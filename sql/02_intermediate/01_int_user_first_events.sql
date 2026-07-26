-- int_user_first_events.sql
-- One row per (user_id, event_name) giving the FIRST time each event happened.
-- This is the building block for funnel step timing and activation windows.
CREATE TABLE IF NOT EXISTS int_user_first_events AS
SELECT
    user_id,
    event_name,
    MIN(event_timestamp) AS first_event_ts,
    MIN(event_date)       AS first_event_date
FROM stg_events
GROUP BY user_id, event_name;
