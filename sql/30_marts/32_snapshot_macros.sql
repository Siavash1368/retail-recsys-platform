-- Features: everything known ON OR BEFORE as_of. Call: SELECT * FROM customer_snapshot(600);
CREATE OR REPLACE MACRO customer_snapshot(as_of) AS TABLE
SELECT
    household_key,
    as_of                         AS asof_day,
    as_of - MAX(day_no)           AS days_since_last,
    as_of - MIN(day_no)           AS tenure_days,
    COUNT(DISTINCT basket_id)                                      AS baskets_all,
    COUNT(DISTINCT basket_id) FILTER (WHERE day_no > as_of - 30)   AS baskets_30d,
    COUNT(DISTINCT basket_id) FILTER (WHERE day_no > as_of - 90)   AS baskets_90d,
    COUNT(DISTINCT basket_id) FILTER (WHERE day_no > as_of - 365)  AS baskets_365d,
    SUM(sales_value)          FILTER (WHERE day_no > as_of - 30)   AS spend_30d,
    SUM(sales_value)          FILTER (WHERE day_no > as_of - 90)   AS spend_90d,
    SUM(sales_value)          FILTER (WHERE day_no > as_of - 365)  AS spend_365d,
    COUNT(DISTINCT product_id) FILTER (WHERE day_no > as_of - 90)  AS products_90d,
    SUM(sales_value) / NULLIF(COUNT(DISTINCT basket_id), 0)        AS avg_basket_value
FROM staging.stg_transactions
WHERE day_no <= as_of
GROUP BY household_key;

-- Labels: purchases STRICTLY AFTER as_of, within horizon. Call: SELECT * FROM purchase_labels(600, 30);
CREATE OR REPLACE MACRO purchase_labels(as_of, horizon) AS TABLE
SELECT DISTINCT household_key, product_id, 1 AS bought
FROM staging.stg_transactions
WHERE day_no > as_of AND day_no <= as_of + horizon;