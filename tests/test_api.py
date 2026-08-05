import pandas as pd
import pytest
from fastapi.testclient import TestClient

from retail_ds.serve import api


@pytest.fixture
def client(tmp_path, monkeypatch):
    recs_dir = tmp_path / "outputs" / "recs"
    recs_dir.mkdir(parents=True)
    pd.DataFrame({
        "household_key": [1, 1, 2],
        "product_id":    [10, 20, 30],
        "score":         [0.9, 0.5, 0.7],
        "rank":          [1, 2, 1],
        "asof_day":      [650, 650, 650],
        "model_version": [133, 133, 133],
    }).to_parquet(recs_dir / "recs_day650.parquet")

    monkeypatch.setattr(api, "find_root", lambda: tmp_path)
    api.load_recs.cache_clear()
    yield TestClient(api.app)
    api.load_recs.cache_clear()


def test_health_reports_loaded_recs(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["households"] == 2


def test_recommendations_are_rank_ordered(client):
    r = client.get("/recommendations/1")
    assert r.status_code == 200
    assert [i["product_id"] for i in r.json()["items"]] == [10, 20]


def test_unknown_household_returns_404(client):
    assert client.get("/recommendations/999").status_code == 404