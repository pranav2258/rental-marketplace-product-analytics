-- stg_supporting.sql
-- Additional staging tables (properties, applications, payments, marketing, experiment)
-- kept together since they're straightforward type/dedup passes.

CREATE TABLE IF NOT EXISTS stg_properties AS
SELECT DISTINCT
    property_id, landlord_id, metro_id, property_type,
    CAST(bedroom_count AS INTEGER) AS bedroom_count,
    CAST(monthly_rent AS REAL)     AS monthly_rent,
    DATE(date_added)               AS date_added,
    DATE(listing_publish_date)     AS listing_publish_date,
    occupancy_status
FROM raw_properties
WHERE property_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS stg_applications AS
SELECT DISTINCT
    application_id, property_id, tenant_id,
    DATE(application_date)  AS application_date,
    application_status,
    CASE WHEN screening_completed IN ('True','1','true') THEN 1 ELSE 0 END AS screening_completed,
    CASE WHEN lease_signed IN ('True','1','true') THEN 1 ELSE 0 END AS lease_signed,
    CAST(decision_time_days AS REAL) AS decision_time_days
FROM raw_applications
WHERE application_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS stg_payments AS
SELECT DISTINCT
    payment_id, lease_id,
    DATE(due_date)      AS due_date,
    DATE(payment_date)  AS payment_date,
    CAST(payment_amount AS REAL) AS payment_amount,
    payment_status, payment_method, failure_reason
FROM raw_payments
WHERE payment_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS stg_marketing_spend AS
SELECT
    DATE(month || '-01') AS month,
    channel, market, campaign,
    CAST(impressions AS INTEGER) AS impressions,
    CAST(clicks AS INTEGER)      AS clicks,
    CAST(spend AS REAL)          AS spend,
    CAST(signups AS INTEGER)     AS signups
FROM raw_marketing_spend;

CREATE TABLE IF NOT EXISTS stg_experiment_exposure AS
SELECT
    user_id, experiment_name, variant,
    DATE(exposure_date) AS exposure_date,
    CASE WHEN activation_7d IN ('True','1','true') THEN 1 ELSE 0 END AS activation_7d,
    CASE WHEN paid_conversion_30d IN ('True','1','true') THEN 1 ELSE 0 END AS paid_conversion_30d
FROM raw_experiment_exposure;
