"""Every feature must be measurable at the as-of date; labels must lie strictly after it."""


def test_interaction_features_never_see_the_future(con):
    as_of = 30
    df = con.sql(f"SELECT * FROM household_product_snapshot({as_of})").df()
    assert (df["last_bought_day"] <= as_of).all()
    assert (df["days_since_last"] >= 0).all()


def test_customer_snapshot_excludes_later_purchases(con):
    """Household 2 buys on days 15 and 45; at as_of=30 only the first is visible."""
    df = con.sql("SELECT * FROM customer_snapshot(30)").df().set_index("household_key")
    assert df.loc[2, "baskets_all"] == 1
    assert df.loc[2, "spend_365d"] == 1.0


def test_labels_lie_strictly_after_as_of(con):
    """Window (30, 60]: household 1 / product 200 on day 60 is in; day-5 purchases are not."""
    labels = con.sql("SELECT * FROM purchase_labels(30, 30)").df()
    pairs = set(zip(labels["household_key"], labels["product_id"]))
    assert (1, 200) in pairs
    assert (3, 200) not in pairs


def test_no_household_appears_before_its_first_purchase(con):
    """Household 1 first buys on day 10; it must be absent from a day-5 snapshot."""
    df = con.sql("SELECT * FROM customer_snapshot(5)").df()
    assert 1 not in set(df["household_key"])