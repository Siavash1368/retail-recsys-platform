-- Leakage-safe covisitation. Call: SELECT * FROM covisitation_pairs(600) LIMIT 5;
-- Returns BOTH directions (source -> neighbor), min support 5 baskets.
CREATE OR REPLACE MACRO covisitation_pairs(as_of) AS TABLE
WITH lines AS (
    SELECT DISTINCT basket_id, product_id
    FROM staging.stg_transactions
    WHERE day_no <= as_of
),
totals AS (SELECT COUNT(DISTINCT basket_id) AS n_baskets FROM lines),
pairs AS (
    SELECT a.product_id AS product_a, b.product_id AS product_b,
           COUNT(*) AS pair_baskets
    FROM lines a
    JOIN lines b ON a.basket_id = b.basket_id AND a.product_id < b.product_id
    GROUP BY 1, 2
    HAVING COUNT(*) >= 5
),
scored AS (
    SELECT pr.product_a, pr.product_b, pr.pair_baskets,
           pr.pair_baskets::DOUBLE * t.n_baskets
               / (ia.n_baskets * ib.n_baskets) AS lift
    FROM pairs pr
    CROSS JOIN totals t
    JOIN marts.mart_item_stats ia ON ia.product_id = pr.product_a
    JOIN marts.mart_item_stats ib ON ib.product_id = pr.product_b
)
SELECT product_a AS source, product_b AS neighbor, pair_baskets, lift FROM scored
UNION ALL
SELECT product_b AS source, product_a AS neighbor, pair_baskets, lift FROM scored;