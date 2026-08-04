-- Call: SELECT * FROM household_product_snapshot(600) LIMIT 5;
CREATE OR REPLACE MACRO household_product_snapshot(as_of) AS TABLE
WITH purchases AS (
    SELECT DISTINCT household_key, product_id, basket_id, day_no
    FROM staging.stg_transactions
    WHERE day_no <= as_of
)
SELECT
    pu.household_key,
    pu.product_id,
    as_of                       AS asof_day,
    COUNT(DISTINCT pu.basket_id) AS times_bought,
    MAX(pu.day_no)               AS last_bought_day,
    as_of - MAX(pu.day_no)       AS days_since_last,
    (as_of - MAX(pu.day_no)) * 1.0 / NULLIF(pc.median_gap_days, 0) AS due_ness
FROM purchases pu
LEFT JOIN marts.mart_product_cycles pc USING (product_id)
GROUP BY pu.household_key, pu.product_id, pc.median_gap_days;