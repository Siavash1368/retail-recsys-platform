"""Validate raw data files against the expectations in configs/schema.yaml."""
import sys
from pathlib import Path

import duckdb
import yaml


def find_root(start: Path | None = None) -> Path:
    """Walk upward from cwd until we find the repo root (has configs/schema.yaml)."""
    p = (start or Path.cwd()).resolve()
    while not (p / "configs" / "schema.yaml").exists():
        if p == p.parent:
            raise FileNotFoundError("configs/schema.yaml not found — run from inside the repo")
        p = p.parent
    return p


def validate_raw(root: Path | None = None) -> bool:
    root = root or find_root()
    schema = yaml.safe_load((root / "configs" / "schema.yaml").read_text())
    all_ok = True

    for name, spec in schema["tables"].items():
        f = (root / spec["file"]).as_posix()

        n = duckdb.sql(f"SELECT COUNT(*) FROM read_csv_auto('{f}')").fetchone()[0]
        ok = n == spec["expected_rows"]
        all_ok &= ok
        print(f"{'OK  ' if ok else 'FAIL'} {name}: {n:,} rows (expected {spec['expected_rows']:,})")

        if "expect_unique" in spec:
            cols = ", ".join(spec["expect_unique"])
            dups = duckdb.sql(
                f"SELECT COUNT(*) FROM (SELECT {cols}, COUNT(*) AS c "
                f"FROM read_csv_auto('{f}') GROUP BY {cols} HAVING c > 1)"
            ).fetchone()[0]
            all_ok &= dups == 0
            print(f"     unique({cols}): {dups} duplicate keys")

    return all_ok


if __name__ == "__main__":
    sys.exit(0 if validate_raw() else 1)