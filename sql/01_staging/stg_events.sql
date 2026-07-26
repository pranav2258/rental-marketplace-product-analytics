-- stg_events.sql
-- Cleans product events, removes duplicate event_ids, standardizes timestamps.
CREATE TABLE IF NOT EXISTS stg_events AS
WITH deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY event_timestamp) AS rn
    FROM raw_product_events
)
SELECT
    event_id,
    user_id,
    user_type,
    DATETIME(event_timestamp)   AS event_timestamp,
    DATE(event_timestamp)       AS event_date,
    LOWER(event_name)           AS event_name,
    property_id,
    session_id,
    device_type,
    traffic_source
FROM deduped
WHERE rn = 1
  AND event_timestamp IS NOT NULL;
