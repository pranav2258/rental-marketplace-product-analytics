-- test_event_sequence.sql
-- Validates funnel logic: a user cannot publish a listing before adding a
-- property, and cannot start a subscription before creating an account.
-- Should return 0 rows.

SELECT landlord_id, ts_property_added, ts_listing_published
FROM int_funnel_steps
WHERE ts_listing_published IS NOT NULL
  AND ts_property_added IS NOT NULL
  AND JULIANDAY(ts_listing_published) < JULIANDAY(ts_property_added);

SELECT landlord_id, ts_account_created, ts_subscription_started
FROM int_funnel_steps
WHERE ts_subscription_started IS NOT NULL
  AND ts_account_created IS NOT NULL
  AND JULIANDAY(ts_subscription_started) < JULIANDAY(ts_account_created);
