"""Build db/retail.duckdb by running the sql/ stages in order."""
import os

import duckdb

from retail_ds.data.validate import find_root

STAGES = ["00_load", "10_staging", "20_intermediate", "30_marts", "99_checks"]


def main() -> None:
    root = find_root()
    os.chdir(root)  # so relative paths inside the SQL resolve
    con = duckdb.connect("db/retail.duckdb")
    for stage in STAGES:
        for f in sorted((root / "sql" / stage).glob("*.sql")):
            print(f"running {stage}/{f.name}")
            con.execute(f.read_text())
    con.close()
    print("done -> db/retail.duckdb")


if __name__ == "__main__":
    main()