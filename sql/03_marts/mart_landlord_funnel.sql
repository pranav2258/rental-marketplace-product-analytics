-- mart_landlord_funnel.sql
-- Step conversion, median time between stages, and abandonment, sliced by
-- channel / portfolio-size segment / metro / device. Answers analysis #1
-- (funnel drop-off analysis).
CREATE TABLE IF NOT EXISTS mart_landlord_funnel AS
WITH steps AS (
    SELECT
        landlord_id, acquisition_channel, metro_id, signup_device, is_paid,
        CASE WHEN portfolio_size >= 10 THEN 'large_10plus'
             WHEN portfolio_size >= 4  THEN 'medium_4to9'
             ELSE 'small_1to3' END AS portfolio_segment,
        ts_account_created, ts_property_added, ts_listing_published,
        ts_tenant_invited, ts_rent_collection_enabled, ts_subscription_started,
        CASE WHEN ts_property_added IS NOT NULL THEN 1 ELSE 0 END AS reached_property_added,
        CASE WHEN ts_listing_published IS NOT NULL THEN 1 ELSE 0 END AS reached_listing_published,
        CASE WHEN ts_tenant_invited IS NOT NULL THEN 1 ELSE 0 END AS reached_tenant_invited,
        CASE WHEN ts_rent_collection_enabled IS NOT NULL THEN 1 ELSE 0 END AS reached_rent_collection,
        CASE WHEN ts_subscription_started IS NOT NULL THEN 1 ELSE 0 END AS reached_paid,
        (JULIANDAY(ts_property_added) - JULIANDAY(ts_account_created))    AS days_to_property,
        (JULIANDAY(ts_listing_published) - JULIANDAY(ts_property_added)) AS days_to_publish
    FROM int_funnel_steps
)
SELECT
    acquisition_channel,
    portfolio_segment,
    metro_id,
    signup_device,
    COUNT(*)                                                     AS landlords,
    ROUND(AVG(reached_property_added), 4)                        AS pct_property_added,
    ROUND(AVG(reached_listing_published), 4)                     AS pct_listing_published,
    ROUND(AVG(reached_tenant_invited), 4)                        AS pct_tenant_invited,
    ROUND(AVG(reached_rent_collection), 4)                       AS pct_rent_collection_enabled,
    ROUND(AVG(reached_paid), 4)                                  AS pct_paid_conversion,
    ROUND(AVG(days_to_property), 2)                              AS avg_days_to_property,
    ROUND(AVG(days_to_publish), 2)                                AS avg_days_to_publish,
    -- abandonment = reached property_added but never published listing
    ROUND(1.0 * SUM(CASE WHEN reached_property_added = 1 AND reached_listing_published = 0 THEN 1 ELSE 0 END)
          / NULLIF(SUM(reached_property_added), 0), 4)           AS publish_abandonment_rate
FROM steps
GROUP BY acquisition_channel, portfolio_segment, metro_id, signup_device;
