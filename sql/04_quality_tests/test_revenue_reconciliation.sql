-- test_revenue_reconciliation.sql
-- Confirms total MRR in mart_revenue for the latest month reconciles with a
-- direct count of active paid subscriptions in the source staging table.
-- The two counts should match (returns a diff of 0, or a small variance
-- explainable by month-boundary timing).

WITH mart_total AS (
    SELECT paying_landlords AS mart_count
    FROM mart_revenue
    ORDER BY month DESC LIMIT 1
),
source_total AS (
    SELECT COUNT(*) AS source_count
    FROM stg_landlords
    WHERE is_paid = 1 AND churn_date IS NULL
)
SELECT
    mart_total.mart_count,
    source_total.source_count,
    mart_total.mart_count - source_total.source_count AS diff
FROM mart_total, source_total;
