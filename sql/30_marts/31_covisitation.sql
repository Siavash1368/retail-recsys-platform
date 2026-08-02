CREATE OR REPLACE TABLE marts.mart_covisitation AS
WITH lines AS (
    SELECT DISTINCT basket_id, product_id FROM staging.stg_transactions
),
totals AS (
    SELECT COUNT(DISTINCT basket_id) AS n_baskets FROM lines
),
pairs AS (
    SELECT a.product_id AS product_a, b.product_id AS product_b,
           COUNT(*) AS pair_baskets
    FROM lines a
    JOIN lines b ON a.basket_id = b.basket_id AND a.product_id < b.product_id
    GROUP BY 1, 2
    HAVING COUNT(*) >= 5                      -- min support; drop noise pairs
)
SELECT
    pr.product_a, pr.product_b, pr.pair_baskets,
    pr.pair_baskets::DOUBLE * t.n_baskets
        / (ia.n_baskets * ib.n_baskets)       AS lift
FROM pairs pr
CROSS JOIN totals t
JOIN marts.mart_item_stats ia ON ia.product_id = pr.product_a
JOIN marts.mart_item_stats ib ON ib.product_id = pr.product_b;