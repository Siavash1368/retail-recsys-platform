import pandas as pd

from retail_ds.evaluate.metrics import hit_rate_at_k, ndcg_at_k, recall_at_k

RECS = pd.DataFrame({
    "household_key": [1, 1, 1, 2, 2, 2],
    "product_id":    [1, 9, 2, 7, 5, 8],
    "rank":          [1, 2, 3, 1, 2, 3],
})
LABELS = pd.DataFrame({
    "household_key": [1, 1, 1, 2],
    "product_id":    [1, 2, 3, 5],
})


def test_recall_at_k():
    # hh1: hits {1,2} of 3 relevant = 2/3 ; hh2: hits {5} of 1 = 1.0 ; mean = 0.8333
    assert abs(recall_at_k(RECS, LABELS, 3) - 5 / 6) < 1e-9


def test_hit_rate_at_k():
    assert hit_rate_at_k(RECS, LABELS, 3) == 1.0


def test_ndcg_at_k():
    # hh1 DCG = 1/log2(2) + 1/log2(4) = 1.5 ; ideal(3) = 1 + 1/log2(3) + 1/log2(4) = 2.13093
    # hh2 DCG = 1/log2(3) = 0.63093 ; ideal(1) = 1.0
    expected = ((1.5 / 2.130929753) + 0.630929753) / 2
    assert abs(ndcg_at_k(RECS, LABELS, 3) - expected) < 1e-6


def test_k_truncates():
    # at k=1, hh1 hits {1} = 1/3, hh2 hits nothing = 0 -> mean 1/6
    assert abs(recall_at_k(RECS, LABELS, 1) - 1 / 6) < 1e-9