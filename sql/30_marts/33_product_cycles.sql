CREATE OR REPLACE TABLE marts.mart_product_cycles AS
WITH purchases AS (
    SELECT DISTINCT household_key, product_id, day_no
    FROM staging.stg_transactions
    WHERE day_no <= 450          -- leakage guard: clocks estimated before the first snapshot
),,
gaps AS (
    SELECT g.product_id, p.sub_commodity, p.commodity, g.gap_days
    FROM (
        SELECT product_id,
               day_no - LAG(day_no) OVER (
                   PARTITION BY household_key, product_id ORDER BY day_no
               ) AS gap_days
        FROM purchases
    ) g
    LEFT JOIN staging.stg_products p USING (product_id)
    WHERE g.gap_days IS NOT NULL
),
by_product AS (
    SELECT product_id, MEDIAN(gap_days) AS gap_median, COUNT(*) AS n
    FROM gaps GROUP BY product_id
),
by_sub AS (
    SELECT sub_commodity, MEDIAN(gap_days) AS gap_median, COUNT(*) AS n
    FROM gaps GROUP BY sub_commodity
),
by_commodity AS (
    SELECT commodity, MEDIAN(gap_days) AS gap_median, COUNT(*) AS n
    FROM gaps GROUP BY commodity
),
overall AS (SELECT MEDIAN(gap_days) AS gap_median FROM gaps)
SELECT
    p.product_id,
    COALESCE(
        CASE WHEN bp.n >= 30 THEN bp.gap_median END,
        CASE WHEN bs.n >= 30 THEN bs.gap_median END,
        CASE WHEN bc.n >= 30 THEN bc.gap_median END,
        o.gap_median
    ) AS median_gap_days,
    CASE WHEN bp.n >= 30 THEN 'product'
         WHEN bs.n >= 30 THEN 'sub_commodity'
         WHEN bc.n >= 30 THEN 'commodity'
         ELSE 'global' END AS gap_source
FROM staging.stg_products p
LEFT JOIN by_product   bp USING (product_id)
LEFT JOIN by_sub       bs USING (sub_commodity)
LEFT JOIN by_commodity bc USING (commodity)
CROSS JOIN overall o;