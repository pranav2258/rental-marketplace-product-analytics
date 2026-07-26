-- mart_revenue.sql
-- Monthly MRR with new / churned MRR bridge, ARPU, and revenue by market.
CREATE TABLE IF NOT EXISTS mart_revenue AS
WITH RECURSIVE seq(n) AS (
    SELECT 0
    UNION ALL
    SELECT n + 1 FROM seq WHERE n < 59   -- up to 60 months of active-subscription expansion
),
sub_months AS (
    -- expand each subscription into one row per active month
    SELECT
        sp.landlord_id, sp.monthly_price,
        strftime('%Y-%m', DATE(sp.subscription_start_date, '+' || seq.n || ' months')) AS month
    FROM int_subscription_periods sp
    JOIN seq
      ON DATE(sp.subscription_start_date, '+' || seq.n || ' months') <=
         COALESCE(sp.subscription_end_date, DATE('2025-12-31'))
     AND DATE(sp.subscription_start_date, '+' || seq.n || ' months') <= DATE('2025-12-31')
),
monthly_mrr AS (
    SELECT month, COUNT(DISTINCT landlord_id) AS paying_landlords, SUM(monthly_price) AS mrr
    FROM sub_months
    GROUP BY month
),
new_mrr AS (
    SELECT strftime('%Y-%m', subscription_start_date) AS month, SUM(monthly_price) AS new_mrr
    FROM int_subscription_periods GROUP BY 1
),
churned_mrr AS (
    SELECT strftime('%Y-%m', subscription_end_date) AS month, SUM(monthly_price) AS churned_mrr
    FROM int_subscription_periods WHERE subscription_end_date IS NOT NULL GROUP BY 1
)
SELECT
    m.month,
    m.paying_landlords,
    m.mrr,
    ROUND(m.mrr * 1.0 / NULLIF(m.paying_landlords, 0), 2) AS arpu,
    COALESCE(n.new_mrr, 0)     AS new_mrr,
    COALESCE(c.churned_mrr, 0) AS churned_mrr,
    m.mrr - LAG(m.mrr) OVER (ORDER BY m.month) AS mrr_mom_change
FROM monthly_mrr m
LEFT JOIN new_mrr n ON n.month = m.month
LEFT JOIN churned_mrr c ON c.month = m.month
ORDER BY m.month;
