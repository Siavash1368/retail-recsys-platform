"""Batch scoring: write top-K recommendations for one snapshot day."""
import argparse
import json
import logging
from pathlib import Path

import duckdb
import xgboost as xgb
import yaml

from retail_ds.data.validate import find_root
from retail_ds.features.design_matrix import build_plane

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("score")


def main() -> None:
    parser = argparse.ArgumentParser(description="Score households and write top-K recommendations.")
    parser.add_argument("--as-of", type=int, required=True, help="snapshot day index")
    parser.add_argument("--root", type=Path, default=None, help="repo root (default: auto-detect)")
    parser.add_argument("--top-k", type=int, default=None, help="override configs/base.yaml")
    args = parser.parse_args()

    root = args.root or find_root()
    cfg = yaml.safe_load((root / "configs" / "base.yaml").read_text())
    top_k = args.top_k or cfg["top_k"]
    budgets = {k: (10**9 if v == -1 else v) for k, v in cfg["candidates"].items()}

    meta = json.loads((root / "models" / "registry" / "model_meta.json").read_text())
    model = xgb.XGBClassifier()
    model.load_model(root / "models" / "registry" / "ranker.ubj")
    log.info("model loaded: trained on planes %s", meta["trained_on_planes"])

    con = duckdb.connect((root / "db" / "retail.duckdb").as_posix(), read_only=True)
    log.info("building candidate plane for day %s ...", args.as_of)
    plane = build_plane(con, args.as_of, budgets, with_label=False)
    log.info("plane built: %s rows", f"{len(plane):,}")

    plane["score"] = model.predict_proba(plane[meta["features"]])[:, 1]
    plane["rank"] = (plane.groupby("household_key")["score"]
                     .rank(method="first", ascending=False).astype(int))
    recs = (plane.loc[plane["rank"] <= top_k,
                      ["household_key", "product_id", "score", "rank"]]
            .sort_values(["household_key", "rank"]))
    recs["asof_day"] = args.as_of
    recs["model_version"] = meta.get("best_iteration", "unknown")

    out_dir = root / "outputs" / "recs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"recs_day{args.as_of}.parquet"
    recs.to_parquet(out_path, index=False)

    log.info("wrote %s rows for %s households -> %s",
             f"{len(recs):,}", f"{recs['household_key'].nunique():,}", out_path)


if __name__ == "__main__":
    main()