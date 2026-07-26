-- mart_cohort_retention.sql
-- Signup-month cohorts x months-since-signup, "retained" = active (not churned)
-- as of that month offset. Powers analysis #2 (cohort retention analysis).
CREATE TABLE IF NOT EXISTS mart_cohort_retention AS
WITH cohorts AS (
    SELECT
        landlord_id,
        strftime('%Y-%m', signup_date) AS cohort_month,
        signup_date,
        churn_date,
        acquisition_channel,
        first_feature_adopted,
        is_paid,
        CASE WHEN portfolio_size >= 10 THEN 'large_10plus'
             WHEN portfolio_size >= 4  THEN 'medium_4to9'
             ELSE 'small_1to3' END AS portfolio_segment
    FROM stg_landlords
    WHERE activated_7d = 1
),
month_offsets AS (
    SELECT 0 AS m_offset UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
    UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6
)
SELECT
    c.cohort_month,
    c.acquisition_channel,
    c.first_feature_adopted,
    c.portfolio_segment,
    CASE WHEN c.is_paid = 1 THEN 'paid' ELSE 'free' END AS plan_type,
    o.m_offset,
    COUNT(*) AS cohort_size,
    SUM(
        CASE WHEN c.churn_date IS NULL
                  OR JULIANDAY(c.churn_date) > JULIANDAY(DATE(c.signup_date, '+' || o.m_offset || ' months'))
             THEN 1 ELSE 0 END
    ) AS retained_landlords,
    ROUND(1.0 * SUM(
        CASE WHEN c.churn_date IS NULL
                  OR JULIANDAY(c.churn_date) > JULIANDAY(DATE(c.signup_date, '+' || o.m_offset || ' months'))
             THEN 1 ELSE 0 END
    ) / COUNT(*), 4) AS retention_rate
FROM cohorts c
CROSS JOIN month_offsets o
GROUP BY c.cohort_month, c.acquisition_channel, c.first_feature_adopted,
         c.portfolio_segment, plan_type, o.m_offset;
