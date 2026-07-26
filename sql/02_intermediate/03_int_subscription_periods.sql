-- int_subscription_periods.sql
-- One row per paid landlord subscription with start/end and monthly price,
-- used to build MRR, expansion/churned MRR, and paid-plan retention.
CREATE TABLE IF NOT EXISTS int_subscription_periods AS
SELECT
    landlord_id,
    subscription_plan,
    subscription_start_date,
    churn_date AS subscription_end_date,
    CASE subscription_plan
        WHEN 'starter'    THEN 29
        WHEN 'pro'        THEN 79
        WHEN 'enterprise' THEN 199
        ELSE 0
    END AS monthly_price,
    CASE WHEN churn_date IS NULL THEN 1 ELSE 0 END AS is_active_subscription
FROM stg_landlords
WHERE is_paid = 1
  AND subscription_start_date IS NOT NULL;
