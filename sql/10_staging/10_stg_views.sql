-- Staging: typed, renamed, decoded views. 1:1 with raw tables.

CREATE OR REPLACE VIEW staging.stg_transactions AS
SELECT
    household_key,
    BASKET_ID          AS basket_id,
    DAY                AS day_no,
    WEEK_NO            AS week_no,
    TRANS_TIME         AS trans_time,
    CAST(substr(lpad(TRANS_TIME, 4, '0'), 1, 2) AS INTEGER) AS trans_hour,
    STORE_ID           AS store_id,
    PRODUCT_ID         AS product_id,
    QUANTITY           AS quantity,
    SALES_VALUE        AS sales_value,
    RETAIL_DISC        AS retail_disc,
    COUPON_DISC        AS coupon_disc,
    COUPON_MATCH_DISC  AS coupon_match_disc
FROM raw.transaction_data;

CREATE OR REPLACE VIEW staging.stg_products AS
SELECT
    PRODUCT_ID           AS product_id,
    MANUFACTURER         AS manufacturer,
    DEPARTMENT           AS department,
    BRAND                AS brand,
    COMMODITY_DESC       AS commodity,
    SUB_COMMODITY_DESC   AS sub_commodity,
    CURR_SIZE_OF_PRODUCT AS pack_size
FROM raw.product;

CREATE OR REPLACE VIEW staging.stg_demographics AS
SELECT
    household_key,
    classification_1  AS age_band,       -- Age Group1-6, ordinal
    classification_2  AS marital_code,   -- X/Y/Z, nominal (mapping unrecoverable)
    classification_3  AS income_band,    -- Level1-12
    CAST(regexp_extract(classification_3, '[0-9]+') AS INTEGER) AS income_level,  -- fixes string-sort trap
    classification_4  AS hh_size,        -- 1..5+, ordinal
    classification_5  AS hh_comp,        -- Group1-6, nominal
    HOMEOWNER_DESC    AS homeowner_desc,
    KID_CATEGORY_DESC AS kid_category
FROM raw.hh_demographic;

CREATE OR REPLACE VIEW staging.stg_campaign_desc AS
SELECT CAMPAIGN AS campaign_id, DESCRIPTION AS campaign_type,
       START_DAY AS start_day, END_DAY AS end_day
FROM raw.campaign_desc;

CREATE OR REPLACE VIEW staging.stg_campaign_exposures AS
SELECT household_key, CAMPAIGN AS campaign_id, DESCRIPTION AS campaign_type
FROM raw.campaign_table;

CREATE OR REPLACE VIEW staging.stg_coupons AS
SELECT COUPON_UPC AS coupon_upc, PRODUCT_ID AS product_id, CAMPAIGN AS campaign_id
FROM raw.coupon;

CREATE OR REPLACE VIEW staging.stg_coupon_redemptions AS
SELECT household_key, DAY AS day_no, COUPON_UPC AS coupon_upc, CAMPAIGN AS campaign_id
FROM raw.coupon_redempt;

CREATE OR REPLACE VIEW staging.stg_causal AS
SELECT PRODUCT_ID AS product_id, STORE_ID AS store_id, WEEK_NO AS week_no,
       display, mailer
FROM raw.causal_data;