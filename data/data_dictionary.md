# Data Dictionary

All tables in `data/raw/` are **synthetic**, except that `market_monthly.csv`
is generated to exactly match the schema of Realtor.com Economic Research's
real public data files (see disclaimer in `src/ingest_realtor_data.py`).

## landlords.csv
| Column | Type | Description |
|---|---|---|
| landlord_id | string | Primary key |
| signup_date | date | Account creation date |
| acquisition_channel | string | organic_search / paid_social / paid_search / referral / content_seo / partnerships |
| metro_id | string | FK to metros_dim |
| portfolio_size | int | Number of units the landlord manages (declared at signup) |
| experience_level | string | first_time / occasional / professional |
| signup_device | string | mobile / desktop / tablet |
| activated_7d | bool | Did the landlord complete a meaningful action within 7 days |
| time_to_first_property_days | float | Days from signup to first property added (NaN if never) |
| first_feature_adopted | string | First product feature used after activation |
| subscription_plan | string | free / starter / pro / enterprise |
| subscription_start_date | date | Paid subscription start (NaT if never paid) |
| churn_date | date | Date landlord churned (NaT if still active) |
| is_paid | bool | Currently or previously on a paid plan |

## properties.csv
| Column | Type | Description |
|---|---|---|
| property_id | string | Primary key |
| landlord_id | string | FK to landlords |
| metro_id | string | FK to metros_dim |
| property_type | string | single_family / apartment / condo / townhouse / duplex |
| bedroom_count | int | |
| monthly_rent | float | USD |
| date_added | date | |
| listing_publish_date | date | NaT if the property was added but never published |
| occupancy_status | string | occupied / vacant / pending |

## tenants.csv
| Column | Type | Description |
|---|---|---|
| tenant_id | string | Primary key |
| signup_date | date | |
| acquisition_channel | string | |
| metro_id | string | |

## applications.csv
| Column | Type | Description |
|---|---|---|
| application_id | string | Primary key |
| property_id | string | FK |
| tenant_id | string | FK |
| application_date | date | |
| application_status | string | leased / rejected / withdrawn / pending |
| screening_completed | bool | |
| lease_signed | bool | |
| decision_time_days | float | |

## product_events.csv
| Column | Type | Description |
|---|---|---|
| event_id | string | Primary key |
| user_id | string | landlord_id (all events in this build are landlord-side) |
| user_type | string | landlord |
| event_timestamp | datetime | |
| event_name | string | account_created / property_added / listing_published / tenant_invited / application_received / screening_completed / lease_created / rent_collection_enabled / maintenance_request_created / subscription_started / subscription_cancelled |
| property_id | string | nullable |
| session_id | string | |
| device_type | string | |
| traffic_source | string | |

## payments.csv
| Column | Type | Description |
|---|---|---|
| payment_id | string | Primary key |
| lease_id | string | Derived from application_id of a leased application |
| due_date | date | |
| payment_date | date | NaT if payment failed |
| payment_amount | float | |
| payment_status | string | on_time / late / failed |
| payment_method | string | ach / credit_card / debit_card |
| failure_reason | string | nullable |

## marketing_spend.csv
| Column | Type | Description |
|---|---|---|
| month | string (YYYY-MM) | |
| channel | string | |
| market | string | metro_name |
| campaign | string | |
| impressions | int | |
| clicks | int | |
| spend | float | USD |
| signups | int | |

## experiment_exposure.csv
| Column | Type | Description |
|---|---|---|
| user_id | string | landlord_id |
| experiment_name | string | guided_property_onboarding |
| variant | string | control / treatment |
| exposure_date | date | |
| activation_7d | bool | |
| paid_conversion_30d | bool | |

## metros_dim.csv
| Column | Type | Description |
|---|---|---|
| metro_id | string | Primary key |
| metro_name | string | |
| demand_score | float | Baseline synthetic demand strength (0-100) |
| supply_score | float | Baseline synthetic supply strength (0-100) |
| market_strength | float | Composite multiplier used to weight signup allocation and rents |

## market_monthly.csv
**Schema matches Realtor.com Economic Research's public "Monthly Inventory" /
"Market Hotness" files.** Generated synthetically in this offline sandbox
(see `src/ingest_realtor_data.py`); attribute to Realtor.com Economic
Research if you swap in the real files.

| Column | Type | Description |
|---|---|---|
| metro_id, metro_name | string | |
| month | date | First of month |
| median_listing_price | float | USD |
| active_listing_count | int | |
| new_listing_count | int | |
| median_days_on_market | float | |
| demand_score | float | 0-100 |
| supply_score | float | 0-100 |
| hotness_score | float | 0-100 composite |
