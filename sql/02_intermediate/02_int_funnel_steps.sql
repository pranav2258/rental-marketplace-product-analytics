-- int_funnel_steps.sql
-- Pivots int_user_first_events into one row per landlord with a column per funnel
-- step timestamp, using conditional aggregation (MAX(CASE WHEN ...)).
CREATE TABLE IF NOT EXISTS int_funnel_steps AS
SELECT
    l.landlord_id,
    l.signup_date,
    l.acquisition_channel,
    l.metro_id,
    l.portfolio_size,
    l.experience_level,
    l.signup_device,
    l.is_paid,
    l.subscription_plan,
    MAX(CASE WHEN e.event_name = 'account_created'          THEN e.first_event_ts END) AS ts_account_created,
    MAX(CASE WHEN e.event_name = 'property_added'           THEN e.first_event_ts END) AS ts_property_added,
    MAX(CASE WHEN e.event_name = 'listing_published'        THEN e.first_event_ts END) AS ts_listing_published,
    MAX(CASE WHEN e.event_name = 'tenant_invited'            THEN e.first_event_ts END) AS ts_tenant_invited,
    MAX(CASE WHEN e.event_name = 'rent_collection_enabled'  THEN e.first_event_ts END) AS ts_rent_collection_enabled,
    MAX(CASE WHEN e.event_name = 'subscription_started'     THEN e.first_event_ts END) AS ts_subscription_started
FROM stg_landlords l
LEFT JOIN int_user_first_events e ON e.user_id = l.landlord_id
GROUP BY l.landlord_id, l.signup_date, l.acquisition_channel, l.metro_id,
         l.portfolio_size, l.experience_level, l.signup_device, l.is_paid, l.subscription_plan;
