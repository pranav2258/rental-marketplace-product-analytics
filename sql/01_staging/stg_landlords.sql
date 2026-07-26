-- stg_landlords.sql
-- Cleans and types the raw landlords extract. One row per landlord_id (deduplicated).
CREATE TABLE IF NOT EXISTS stg_landlords AS
WITH deduped AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY landlord_id ORDER BY signup_date DESC) AS rn
    FROM raw_landlords
)
SELECT
    landlord_id,
    DATE(signup_date)                              AS signup_date,
    LOWER(TRIM(acquisition_channel))                AS acquisition_channel,
    metro_id,
    CAST(portfolio_size AS INTEGER)                 AS portfolio_size,
    experience_level,
    signup_device,
    CASE WHEN activated_7d IN ('True','1','true') THEN 1 ELSE 0 END AS activated_7d,
    time_to_first_property_days,
    first_feature_adopted,
    subscription_plan,
    DATE(subscription_start_date)                   AS subscription_start_date,
    DATE(churn_date)                                 AS churn_date,
    CASE WHEN is_paid IN ('True','1','true') THEN 1 ELSE 0 END AS is_paid
FROM deduped
WHERE rn = 1
  AND signup_date IS NOT NULL;
