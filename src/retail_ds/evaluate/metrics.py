"""Ranking metrics. recs: household_key, product_id, rank (1 = best).
labels: household_key, product_id (the ground truth purchases)."""
import numpy as np
import pandas as pd


def recall_at_k(recs: pd.DataFrame, labels: pd.DataFrame, k: int = 10) -> float:
    top_k = recs[recs["rank"] <= k]
    hits = top_k.merge(labels, on=["household_key", "product_id"])
    n_relevant = labels.groupby("household_key").size()
    n_hits = hits.groupby("household_key").size()
    per_household = (n_hits / n_relevant).reindex(n_relevant.index).fillna(0)
    return float(per_household.mean())


def hit_rate_at_k(recs: pd.DataFrame, labels: pd.DataFrame, k: int = 10) -> float:
    top_k = recs[recs["rank"] <= k]
    hits = top_k.merge(labels, on=["household_key", "product_id"])
    households_with_labels = labels["household_key"].nunique()
    households_with_hit = hits["household_key"].nunique()
    return households_with_hit / households_with_labels


def ndcg_at_k(recs: pd.DataFrame, labels: pd.DataFrame, k: int = 10) -> float:
    top_k = recs[recs["rank"] <= k].copy()
    top_k["gain"] = 1 / np.log2(top_k["rank"] + 1)
    hits = top_k.merge(labels, on=["household_key", "product_id"])
    dcg = hits.groupby("household_key")["gain"].sum()

    n_relevant = labels.groupby("household_key").size().clip(upper=k)
    ideal = n_relevant.map(lambda n: sum(1 / np.log2(r + 1) for r in range(1, n + 1)))
    per_household = (dcg / ideal).reindex(ideal.index).fillna(0)
    return float(per_household.mean())