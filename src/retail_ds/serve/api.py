"""Serve precomputed recommendations."""
from functools import lru_cache

import pandas as pd
from fastapi import FastAPI, HTTPException

from retail_ds.data.validate import find_root

app = FastAPI(title="Retail Recommender", version="1.0")


@lru_cache(maxsize=1)
def load_recs() -> pd.DataFrame:
    root = find_root()
    files = sorted((root / "outputs" / "recs").glob("recs_day*.parquet"))
    if not files:
        raise FileNotFoundError("no scored recommendations found")
    return pd.read_parquet(files[-1])


@app.get("/health")
def health():
    try:
        recs = load_recs()
        return {"status": "ok", "households": int(recs["household_key"].nunique()),
                "asof_day": int(recs["asof_day"].iloc[0])}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/recommendations/{household_key}")
def recommendations(household_key: int, k: int = 10):
    recs = load_recs()
    rows = recs[recs["household_key"] == household_key].nsmallest(k, "rank")
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"no recommendations for {household_key}")
    return {
        "household_key": household_key,
        "asof_day": int(rows["asof_day"].iloc[0]),
        "model_version": int(rows["model_version"].iloc[0]),
        "items": [{"product_id": int(r.product_id), "rank": int(r.rank), "score": float(r.score)}
                  for r in rows.itertuples()],
    }