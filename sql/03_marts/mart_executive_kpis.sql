-- mart_executive_kpis.sql
-- Monthly executive summary: signups, activation, paid conversion, applications,
-- payment success rate, with month-over-month and year-over-year deltas.
CREATE TABLE IF NOT EXISTS mart_executive_kpis AS
WITH monthly_signups AS (
    SELECT
        strftime('%Y-%m', signup_date) AS month,
        COUNT(*)                        AS new_landlords,
        SUM(activated_7d)               AS activated_landlords,
        SUM(is_paid)                    AS paid_landlords
    FROM stg_landlords
    GROUP BY 1
),
monthly_apps AS (
    SELECT strftime('%Y-%m', application_date) AS month,
           COUNT(*) AS applications,
           SUM(lease_signed) AS leases_signed
    FROM stg_applications
    GROUP BY 1
),
monthly_payments AS (
    SELECT strftime('%Y-%m', due_date) AS month,
           COUNT(*) AS payments_due,
           SUM(CASE WHEN payment_status = 'on_time' THEN 1 ELSE 0 END) AS payments_on_time,
           SUM(CASE WHEN payment_status = 'failed' THEN 1 ELSE 0 END) AS payments_failed
    FROM stg_payments
    GROUP BY 1
),
combined AS (
    SELECT
        s.month,
        s.new_landlords,
        s.activated_landlords,
        ROUND(1.0 * s.activated_landlords / NULLIF(s.new_landlords, 0), 4) AS activation_rate,
        s.paid_landlords,
        ROUND(1.0 * s.paid_landlords / NULLIF(s.activated_landlords, 0), 4) AS free_to_paid_conversion,
        a.applications,
        a.leases_signed,
        ROUND(1.0 * a.leases_signed / NULLIF(a.applications, 0), 4) AS lease_conversion_rate,
        p.payments_due,
        ROUND(1.0 * p.payments_on_time / NULLIF(p.payments_due, 0), 4) AS payment_success_rate,
        ROUND(1.0 * p.payments_failed / NULLIF(p.payments_due, 0), 4) AS payment_failure_rate
    FROM monthly_signups s
    LEFT JOIN monthly_apps a ON a.month = s.month
    LEFT JOIN monthly_payments p ON p.month = s.month
)
SELECT
    *,
    ROUND(new_landlords - LAG(new_landlords) OVER (ORDER BY month), 1) AS new_landlords_mom_change,
    ROUND(new_landlords - LAG(new_landlords, 12) OVER (ORDER BY month), 1) AS new_landlords_yoy_change
FROM combined
ORDER BY month;
