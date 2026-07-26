-- test_primary_keys.sql
-- Each query should return 0 rows. Any row returned = a duplicate PK violation.

-- landlords
SELECT 'stg_landlords' AS table_name, landlord_id AS pk, COUNT(*) AS n
FROM stg_landlords GROUP BY landlord_id HAVING COUNT(*) > 1;

-- properties
SELECT 'stg_properties', property_id, COUNT(*)
FROM stg_properties GROUP BY property_id HAVING COUNT(*) > 1;

-- applications
SELECT 'stg_applications', application_id, COUNT(*)
FROM stg_applications GROUP BY application_id HAVING COUNT(*) > 1;

-- payments
SELECT 'stg_payments', payment_id, COUNT(*)
FROM stg_payments GROUP BY payment_id HAVING COUNT(*) > 1;

-- events
SELECT 'stg_events', event_id, COUNT(*)
FROM stg_events GROUP BY event_id HAVING COUNT(*) > 1;
