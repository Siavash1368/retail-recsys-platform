from pathlib import Path

import duckdb
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def con():
    """In-memory DuckDB with synthetic transactions and the real as-of macros."""
    con = duckdb.connect(":memory:")
    con.execute("CREATE SCHEMA staging; CREATE SCHEMA marts;")

    tx = pd.DataFrame({
        "household_key": [1, 1, 1, 2, 2, 3],
        "basket_id":     [10, 11, 12, 20, 21, 30],
        "day_no":        [10, 20, 60, 15, 45, 5],
        "product_id":    [100, 100, 200, 100, 300, 200],
        "sales_value":   [1.0, 1.0, 2.0, 1.0, 3.0, 2.0],
        "quantity":      [1, 1, 1, 1, 1, 1],
    })
    con.register("tx", tx)
    con.execute("CREATE TABLE staging.stg_transactions AS SELECT * FROM tx")
    con.execute("""
        CREATE TABLE marts.mart_product_cycles AS
        SELECT DISTINCT product_id, 10.0 AS median_gap_days, 'global' AS gap_source FROM tx
    """)

    for sql_file in ["sql/30_marts/32_snapshot_macros.sql",
                     "sql/30_marts/34_interaction_macro.sql"]:
        con.execute((ROOT / sql_file).read_text())
    return con