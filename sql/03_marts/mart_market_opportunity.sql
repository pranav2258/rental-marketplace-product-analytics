-- mart_market_opportunity.sql
-- Combines latest Realtor.com-style market indicators with platform performance
-- per metro into a transparent, weighted opportunity score. Powers analysis #5.
CREATE TABLE IF NOT EXISTS mart_market_opportunity AS
WITH latest_market AS (
    SELECT metro_id, metro_name, demand_score, supply_score, hotness_score,
           median_days_on_market, active_listing_count, new_listing_count,
           ROW_NUMBER() OVER (PARTITION BY metro_id ORDER BY month DESC) AS rn
    FROM stg_market_monthly
),
market_latest AS (
    SELECT * FROM latest_market WHERE rn = 1
),
platform_by_metro AS (
    SELECT
        metro_id,
        COUNT(*)                                    AS platform_landlords,
        ROUND(AVG(activated_7d), 4)                 AS activation_rate,
        ROUND(AVG(is_paid), 4)                       AS paid_conversion_rate
    FROM stg_landlords
    GROUP BY metro_id
),
scored AS (
    SELECT
        m.metro_id, m.metro_name,
        m.demand_score, m.supply_score, m.hotness_score, m.median_days_on_market,
        m.active_listing_count, m.new_listing_count,
        COALESCE(p.platform_landlords, 0)     AS platform_landlords,
        COALESCE(p.activation_rate, 0)        AS activation_rate,
        COALESCE(p.paid_conversion_rate, 0)   AS paid_conversion_rate,
        -- min-max normalize demand & inverse of platform penetration (proxy: landlords per 1000 active listings)
        (m.demand_score - MIN(m.demand_score) OVER ()) * 1.0 /
            NULLIF(MAX(m.demand_score) OVER () - MIN(m.demand_score) OVER (), 0)  AS demand_norm,
        1.0 - (COALESCE(p.platform_landlords, 0) * 1000.0 / NULLIF(m.active_listing_count, 0)
               - MIN(COALESCE(p.platform_landlords, 0) * 1000.0 / NULLIF(m.active_listing_count, 0)) OVER ())
            / NULLIF(MAX(COALESCE(p.platform_landlords, 0) * 1000.0 / NULLIF(m.active_listing_count, 0)) OVER ()
                    - MIN(COALESCE(p.platform_landlords, 0) * 1000.0 / NULLIF(m.active_listing_count, 0)) OVER (), 0) AS low_penetration_norm
    FROM market_latest m
    LEFT JOIN platform_by_metro p ON p.metro_id = m.metro_id
)
SELECT
    metro_id, metro_name, demand_score, supply_score, hotness_score,
    median_days_on_market, active_listing_count, new_listing_count,
    platform_landlords, activation_rate, paid_conversion_rate,
    ROUND(demand_norm, 4)          AS demand_norm,
    ROUND(low_penetration_norm, 4) AS low_penetration_norm,
    -- transparent weighted score: 40% demand, 30% low penetration (whitespace), 30% platform performance
    ROUND(0.40 * demand_norm + 0.30 * low_penetration_norm + 0.30 * (activation_rate + paid_conversion_rate) / 2, 4)
        AS opportunity_score,
    CASE
        WHEN demand_norm >= 0.5 AND low_penetration_norm >= 0.5 THEN 'high_demand_low_penetration'
        WHEN demand_norm >= 0.5 AND low_penetration_norm <  0.5 THEN 'high_demand_high_penetration'
        WHEN demand_norm <  0.5 AND (activation_rate + paid_conversion_rate) / 2 >= 0.15 THEN 'low_demand_high_performance'
        ELSE 'low_priority'
    END AS market_classification
FROM scored
ORDER BY opportunity_score DESC;
