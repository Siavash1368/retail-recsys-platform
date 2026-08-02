CREATE OR REPLACE TABLE raw.transaction_data AS
SELECT * FROM read_csv_auto('data/raw/transaction_data.csv');

CREATE OR REPLACE TABLE raw.product AS
SELECT * FROM read_csv_auto('data/raw/product.csv');

CREATE OR REPLACE TABLE raw.hh_demographic AS
SELECT * FROM read_csv_auto('data/raw/hh_demographic.csv');

CREATE OR REPLACE TABLE raw.campaign_desc AS
SELECT * FROM read_csv_auto('data/raw/campaign_desc.csv');

CREATE OR REPLACE TABLE raw.campaign_table AS
SELECT * FROM read_csv_auto('data/raw/campaign_table.csv');

CREATE OR REPLACE TABLE raw.coupon AS
SELECT * FROM read_csv_auto('data/raw/coupon.csv');

CREATE OR REPLACE TABLE raw.coupon_redempt AS
SELECT * FROM read_csv_auto('data/raw/coupon_redempt.csv');

CREATE OR REPLACE TABLE raw.causal_data AS
SELECT * FROM read_csv_auto('data/raw/causal_data.csv');