"""Build the featured, labeled design matrix for one time plane."""
import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np
import pandas as pd
import scipy.sparse as sp
from implicit.als import AlternatingLeastSquares

ALS_PARAMS = {"factors": 64, "regularization": 0.05, "alpha": 20.0,
              "iterations": 20, "random_state": 42}
ZERO_FILL = ["times_bought", "spend_30d", "spend_365d",
             "item_baskets_365d", "item_households_365d"]


def fit_als(con, as_of):
    """ALS on interactions up to as_of. Returns (model, households, products, matrix)."""
    counts = con.sql(f"""
        SELECT household_key, product_id, COUNT(DISTINCT basket_id) AS times_bought
        FROM staging.stg_transactions WHERE day_no <= {as_of}
        GROUP BY household_key, product_id
    """).df()
    households = np.sort(counts["household_key"].unique())
    products = np.sort(counts["product_id"].unique())
    hh_pos = {h: i for i, h in enumerate(households)}
    pr_pos = {p: i for i, p in enumerate(products)}
    matrix = sp.csr_matrix(
        (np.log1p(counts["times_bought"]).astype(np.float32),
         (counts["household_key"].map(hh_pos), counts["product_id"].map(pr_pos))),
        shape=(len(households), len(products)))
    als = AlternatingLeastSquares(**ALS_PARAMS)
    als.fit(matrix)
    return als, households, products, hh_pos, pr_pos, matrix


def build_plane(con, as_of, budgets, horizon=30, with_label=True):
    """One time plane: pooled candidates x features (+ label)."""
    als, households, products, hh_pos, pr_pos, matrix = fit_als(con, as_of)

    buy_again = con.sql(
        f"SELECT household_key, product_id FROM household_product_snapshot({as_of})"
    ).df().assign(source="buy_again")

    popularity = con.sql(f"""
        WITH top_products AS (
            SELECT product_id FROM staging.stg_transactions
            WHERE day_no <= {as_of} AND day_no > {as_of} - 365
            GROUP BY product_id ORDER BY COUNT(*) DESC LIMIT {budgets['popularity']}
        )
        SELECT h.household_key, t.product_id
        FROM (SELECT DISTINCT household_key FROM customer_snapshot({as_of})) h
        CROSS JOIN top_products t
    """).df().assign(source="popularity")

    n_als = budgets["als_new"]
    ids, _ = als.recommend(np.arange(len(households)), matrix,
                           N=n_als, filter_already_liked_items=True)
    als_new = pd.DataFrame({"household_key": np.repeat(households, n_als),
                            "product_id": products[ids.ravel()],
                            "source": "als_new"})

    pool = pd.concat([buy_again, popularity, als_new], ignore_index=True)
    cand = (pool.pivot_table(index=["household_key", "product_id"],
                             columns="source", aggfunc="size", fill_value=0)
            .astype(bool).reset_index())
    for col in ["buy_again", "popularity", "als_new"]:
        if col not in cand:
            cand[col] = False
    cand = cand.rename(columns={"buy_again": "in_buy_again",
                                "popularity": "in_popularity",
                                "als_new": "in_als_new"})

    inter = con.sql(f"""
        SELECT household_key, product_id, times_bought, days_since_last, due_ness
        FROM household_product_snapshot({as_of})
    """).df()
    cust = con.sql(f"""
        SELECT household_key, days_since_last AS hh_days_since_last, tenure_days,
               baskets_30d, baskets_90d, baskets_365d, spend_30d, spend_365d,
               products_90d, avg_basket_value
        FROM customer_snapshot({as_of})
    """).df()
    item = con.sql(f"""
        SELECT product_id,
               COUNT(DISTINCT basket_id) AS item_baskets_365d,
               COUNT(DISTINCT household_key) AS item_households_365d,
               SUM(sales_value) / NULLIF(SUM(quantity), 0) AS item_avg_price
        FROM staging.stg_transactions
        WHERE day_no <= {as_of} AND day_no > {as_of} - 365
        GROUP BY product_id
    """).df()
    cycles = con.sql(
        "SELECT product_id, median_gap_days, gap_source FROM marts.mart_product_cycles"
    ).df()

    df = (cand
          .merge(inter, on=["household_key", "product_id"], how="left")
          .merge(cust, on="household_key", how="left")
          .merge(item, on="product_id", how="left")
          .merge(cycles, on="product_id", how="left"))
    df[ZERO_FILL] = df[ZERO_FILL].fillna(0)

    u = df["household_key"].map(hh_pos).to_numpy()
    i = df["product_id"].map(pr_pos).to_numpy()
    ok = ~(pd.isna(u) | pd.isna(i))
    affinity = np.full(len(df), np.nan, dtype=np.float32)
    affinity[ok] = np.einsum("ij,ij->i",
                             als.user_factors[u[ok].astype(int)],
                             als.item_factors[i[ok].astype(int)])
    df["als_affinity"] = affinity

    quality = {"product": 3, "sub_commodity": 2, "commodity": 1, "global": 0}
    df["gap_quality"] = df["gap_source"].map(quality).fillna(0).astype(np.int8)

    if with_label:
        labels = con.sql(
            f"SELECT household_key, product_id, 1 AS label FROM purchase_labels({as_of}, {horizon})"
        ).df()
        df = df.merge(labels, on=["household_key", "product_id"], how="left")
        df["label"] = df["label"].fillna(0).astype(np.int8)

    df["asof_day"] = as_of
    return df