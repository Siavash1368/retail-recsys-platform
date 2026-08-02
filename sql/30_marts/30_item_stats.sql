CREATE OR REPLACE TABLE marts.mart_item_stats AS
SELECT
    t.product_id,
    any_value(p.department)    AS department,
    any_value(p.commodity)     AS commodity,
    any_value(p.sub_commodity) AS sub_commodity,
    any_value(p.brand)         AS brand,
    COUNT(*)                          AS line_count,
    COUNT(DISTINCT t.basket_id)       AS n_baskets,
    COUNT(DISTINCT t.household_key)   AS n_households,
    SUM(t.sales_value)                AS revenue,
    SUM(t.sales_value) / NULLIF(SUM(t.quantity), 0) AS avg_unit_price,
    MIN(t.week_no) AS first_week,
    MAX(t.week_no) AS last_week
FROM staging.stg_transactions t
LEFT JOIN staging.stg_products p USING (product_id)
GROUP BY t.product_id;