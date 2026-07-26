"""
generate_synthetic_data.py
============================
Generates the synthetic "product" side of the Rental Marketplace Product
Analytics Platform: landlords, tenants, properties, applications, product
events, payments, marketing spend, and experiment exposure.

THIS DATA IS 100% SYNTHETIC. It is generated with intentional, documented
probability relationships (e.g. channel -> activation rate, device ->
completion time, first-feature-adopted -> retention) so that downstream
funnel / cohort / experiment analyses uncover *real* (if simulated)
patterns rather than manufactured conclusions.

Usage:
    python generate_synthetic_data.py --scale full   # ~50k landlords / 150k tenants / ~1M events
    python generate_synthetic_data.py --scale demo    # ~5k landlords / 15k tenants / ~100k events (fast, for iteration)

Output: CSV files written to ../data/raw/
"""
import argparse
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
SEED = 42
rng = np.random.default_rng(SEED)

START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2025, 12, 31)
TOTAL_DAYS = (END_DATE - START_DATE).days

CHANNELS = ["organic_search", "paid_social", "paid_search", "referral", "content_seo", "partnerships"]
CHANNEL_WEIGHTS = [0.28, 0.20, 0.18, 0.14, 0.12, 0.08]
# Baseline 7-day activation propensity multiplier by channel (referral/organic convert best)
CHANNEL_ACTIVATION_MULT = {
    "organic_search": 1.10, "paid_social": 0.78, "paid_search": 0.92,
    "referral": 1.30, "content_seo": 1.05, "partnerships": 1.15,
}
CHANNEL_CAC = {  # rough $ cost per signup, used for marketing spend synth
    "organic_search": 8, "paid_social": 42, "paid_search": 55,
    "referral": 12, "content_seo": 15, "partnerships": 20,
}

DEVICE_TYPES = ["mobile", "desktop", "tablet"]
DEVICE_WEIGHTS = [0.52, 0.40, 0.08]
DEVICE_SPEED_MULT = {"mobile": 0.72, "desktop": 1.15, "tablet": 0.95}  # mobile = slower/lower completion

EXPERIENCE_LEVELS = ["first_time", "occasional", "professional"]
EXPERIENCE_WEIGHTS = [0.45, 0.35, 0.20]

PLANS = ["free", "starter", "pro", "enterprise"]
PLAN_PRICE = {"free": 0, "starter": 29, "pro": 79, "enterprise": 199}

PROPERTY_TYPES = ["single_family", "apartment", "condo", "townhouse", "duplex"]

# 25 metros with baseline synthetic "market strength" -> demand_score/supply_score (0-100)
METROS = pd.DataFrame([
    ("Austin, TX",        82, 55, 1.25), ("Dallas, TX",        76, 60, 1.10),
    ("Phoenix, AZ",        79, 52, 1.15), ("Tampa, FL",         84, 48, 1.20),
    ("Charlotte, NC",      77, 58, 1.05), ("Nashville, TN",     81, 50, 1.15),
    ("Raleigh, NC",        78, 54, 1.05), ("Columbus, OH",      68, 62, 0.90),
    ("Indianapolis, IN",   62, 65, 0.80), ("Kansas City, MO",   60, 68, 0.75),
    ("Denver, CO",         73, 57, 1.10), ("Seattle, WA",       75, 45, 1.30),
    ("Portland, OR",       65, 55, 1.00), ("Atlanta, GA",       80, 53, 1.15),
    ("Orlando, FL",        83, 47, 1.15), ("San Antonio, TX",   70, 63, 0.90),
    ("Sacramento, CA",     71, 49, 1.20), ("Las Vegas, NV",     74, 52, 1.10),
    ("Salt Lake City, UT", 72, 56, 1.05), ("Boise, ID",         69, 58, 0.95),
    ("Minneapolis, MN",    58, 66, 0.75), ("Pittsburgh, PA",    52, 70, 0.65),
    ("Cleveland, OH",      50, 72, 0.60), ("Memphis, TN",       55, 69, 0.70),
    ("Jacksonville, FL",   75, 55, 1.05),
], columns=["metro_name", "demand_score", "supply_score", "market_strength"])
METROS["metro_id"] = ["M" + str(i+1).zfill(3) for i in range(len(METROS))]
# weight signup allocation toward stronger markets
METRO_WEIGHTS = (METROS["market_strength"] ** 2).values
METRO_WEIGHTS = METRO_WEIGHTS / METRO_WEIGHTS.sum()

FEATURES = ["listing_tools", "tenant_screening", "online_rent_collection", "maintenance_tracking", "e_signatures"]


def rand_date(start, end, n):
    """Uniform random dates between start/end, with mild YoY growth weighting toward recent."""
    days = (end - start).days
    # growth weighting: skew towards later days (platform growing over time)
    weights = np.linspace(0.5, 1.5, days + 1)
    weights = weights / weights.sum()
    offsets = rng.choice(np.arange(days + 1), size=n, p=weights)
    return [start + timedelta(days=int(d)) for d in offsets]


def make_landlords(n):
    channel = rng.choice(CHANNELS, size=n, p=CHANNEL_WEIGHTS)
    metro_idx = rng.choice(len(METROS), size=n, p=METRO_WEIGHTS)
    metro_id = METROS["metro_id"].values[metro_idx]
    experience = rng.choice(EXPERIENCE_LEVELS, size=n, p=EXPERIENCE_WEIGHTS)
    portfolio_size = np.where(
        experience == "professional", rng.integers(5, 40, n),
        np.where(experience == "occasional", rng.integers(2, 6, n), rng.integers(1, 3, n))
    )
    signup_date = rand_date(START_DATE, END_DATE, n)
    device = rng.choice(DEVICE_TYPES, size=n, p=DEVICE_WEIGHTS)

    df = pd.DataFrame({
        "landlord_id": ["L" + str(i).zfill(6) for i in range(1, n + 1)],
        "signup_date": signup_date,
        "acquisition_channel": channel,
        "metro_id": metro_id,
        "portfolio_size": portfolio_size,
        "experience_level": experience,
        "signup_device": device,
    })
    return df


def simulate_landlord_lifecycle(landlords):
    """Simulate activation, feature adoption, subscription, churn for each landlord."""
    n = len(landlords)
    channel_mult = landlords["acquisition_channel"].map(CHANNEL_ACTIVATION_MULT).values
    device_mult = landlords["signup_device"].map(DEVICE_SPEED_MULT).values
    exp_mult = landlords["experience_level"].map({"first_time": 0.85, "occasional": 1.05, "professional": 1.25}).values
    metro_mult = landlords["metro_id"].map(METROS.set_index("metro_id")["market_strength"]).values

    base_activation_p = 0.42
    activation_p = np.clip(base_activation_p * channel_mult * device_mult * exp_mult * (0.6 + 0.4 * metro_mult), 0.03, 0.92)
    activated = rng.random(n) < activation_p

    # time to first property (days), faster for higher propensity
    time_to_property = np.where(
        activated,
        np.clip(rng.gamma(shape=2.0, scale=1.0 / activation_p.clip(0.05), size=n), 0.1, 30),
        np.nan
    )

    # first feature adopted (only if activated) -- listing_tools most common first step
    first_feature = np.where(
        activated,
        rng.choice(FEATURES, size=n, p=[0.55, 0.15, 0.15, 0.08, 0.07]),
        None
    )

    # Retention boost if first feature was online_rent_collection (per spec hypothesis)
    retention_boost = np.where(first_feature == "online_rent_collection", 1.35,
                       np.where(first_feature == "tenant_screening", 1.15, 1.0))

    # subscription: only activated landlords convert to paid, with channel/experience effects
    paid_p = np.where(activated, np.clip(0.22 * channel_mult * exp_mult * retention_boost, 0.02, 0.85), 0.01)
    is_paid = rng.random(n) < paid_p
    plan = np.where(
        is_paid,
        rng.choice(["starter", "pro", "enterprise"], size=n, p=[0.55, 0.35, 0.10]),
        "free"
    )

    sub_start = []
    for i in range(n):
        if is_paid[i]:
            offset = int(np.clip(rng.gamma(2, 5), 1, 90))
            sub_start.append(landlords["signup_date"].iloc[i] + timedelta(days=offset))
        else:
            sub_start.append(pd.NaT)

    # monthly churn hazard, reduced by retention_boost, increased for free/low-portfolio
    months_active = np.array([(END_DATE - d).days // 30 for d in landlords["signup_date"]])
    base_monthly_churn = np.where(is_paid, 0.035, 0.09) / retention_boost
    churned = rng.random(n) < np.clip(base_monthly_churn * months_active * 0.3, 0, 0.9)
    churn_date = []
    for i in range(n):
        if churned[i] and (is_paid[i] or activated[i]):
            ref_date = sub_start[i] if is_paid[i] and pd.notna(sub_start[i]) else landlords["signup_date"].iloc[i]
            offset_days = int(np.clip(rng.exponential(180), 15, max(16, (END_DATE - ref_date).days)))
            cd = ref_date + timedelta(days=offset_days)
            churn_date.append(cd if cd <= END_DATE else pd.NaT)
        else:
            churn_date.append(pd.NaT)

    out = landlords.copy()
    out["activated_7d"] = activated
    out["time_to_first_property_days"] = time_to_property
    out["first_feature_adopted"] = first_feature
    out["subscription_plan"] = plan
    out["subscription_start_date"] = sub_start
    out["churn_date"] = churn_date
    out["is_paid"] = is_paid
    return out


def make_properties(landlords):
    rows = []
    pid = 1
    for _, l in landlords.iterrows():
        if not l["activated_7d"]:
            continue
        n_props = max(1, int(rng.poisson(max(1, l["portfolio_size"] * 0.5))))
        n_props = min(n_props, max(1, l["portfolio_size"]))
        # publish propensity: mobile users and lower-intent channels abandon more
        # between "property added" and "listing published"
        device_publish_mult = {"mobile": 0.68, "tablet": 0.85, "desktop": 1.05}[l["signup_device"]]
        channel_publish_mult = CHANNEL_ACTIVATION_MULT.get(l["acquisition_channel"], 1.0)
        publish_p = np.clip(0.80 * device_publish_mult * channel_publish_mult, 0.20, 0.97)
        for _ in range(n_props):
            date_added = l["signup_date"] + timedelta(days=int(np.clip(rng.gamma(2, 3), 0, 120)))
            if date_added > END_DATE:
                continue
            will_publish = rng.random() < publish_p
            if will_publish:
                # mobile users who DO publish also take longer to do so
                publish_lag_scale = 2 * (1.4 if l["signup_device"] == "mobile" else 1.0)
                publish_lag = int(np.clip(rng.gamma(1.5, publish_lag_scale), 0, 45))
                listing_publish = date_added + timedelta(days=publish_lag)
                listing_publish = listing_publish if listing_publish <= END_DATE else pd.NaT
            else:
                listing_publish = pd.NaT
            rows.append({
                "property_id": "P" + str(pid).zfill(7),
                "landlord_id": l["landlord_id"],
                "metro_id": l["metro_id"],
                "property_type": rng.choice(PROPERTY_TYPES, p=[0.35, 0.30, 0.15, 0.12, 0.08]),
                "bedroom_count": int(rng.integers(1, 6)),
                "monthly_rent": int(rng.normal(1650, 500) * METROS.set_index("metro_id").loc[l["metro_id"], "market_strength"]),
                "date_added": date_added,
                "listing_publish_date": listing_publish,
                "occupancy_status": rng.choice(["occupied", "vacant", "pending"], p=[0.72, 0.20, 0.08]),
            })
            pid += 1
    df = pd.DataFrame(rows)
    df["monthly_rent"] = df["monthly_rent"].clip(600, 6000)
    return df


def make_tenants(n):
    channel = rng.choice(CHANNELS, size=n, p=CHANNEL_WEIGHTS)
    metro_idx = rng.choice(len(METROS), size=n, p=METRO_WEIGHTS)
    df = pd.DataFrame({
        "tenant_id": ["T" + str(i).zfill(7) for i in range(1, n + 1)],
        "signup_date": rand_date(START_DATE, END_DATE, n),
        "acquisition_channel": channel,
        "metro_id": METROS["metro_id"].values[metro_idx],
    })
    return df


def make_applications(properties, tenants):
    rows = []
    aid = 1
    tenants_by_metro = tenants.groupby("metro_id")["tenant_id"].apply(list).to_dict()
    published = properties.dropna(subset=["listing_publish_date"])
    for _, p in published.iterrows():
        pool = tenants_by_metro.get(p["metro_id"], [])
        if not pool:
            continue
        n_apps = rng.poisson(1.8)
        for _ in range(n_apps):
            tenant_id = pool[rng.integers(0, len(pool))]
            app_date = p["listing_publish_date"] + timedelta(days=int(rng.exponential(10)))
            if app_date > END_DATE:
                continue
            screening = rng.random() < 0.68
            decision_days = float(np.clip(rng.gamma(2, 1.5), 0.5, 21))
            lease_signed = rng.random() < (0.32 if screening else 0.15)
            status = "leased" if lease_signed else rng.choice(["rejected", "withdrawn", "pending"], p=[0.45, 0.25, 0.30])
            rows.append({
                "application_id": "A" + str(aid).zfill(8),
                "property_id": p["property_id"],
                "tenant_id": tenant_id,
                "application_date": app_date,
                "application_status": status,
                "screening_completed": screening,
                "lease_signed": lease_signed,
                "decision_time_days": decision_days,
            })
            aid += 1
    return pd.DataFrame(rows)


EVENT_SEQUENCE = ["account_created", "property_added", "listing_published", "tenant_invited",
                   "application_received", "screening_completed", "lease_created",
                   "rent_collection_enabled", "maintenance_request_created",
                   "subscription_started", "subscription_cancelled"]


def make_product_events(landlords, properties, target_total_events):
    rows = []
    eid = 1
    props_by_landlord = properties.groupby("landlord_id")
    for _, l in landlords.iterrows():
        session_id = "S" + str(rng.integers(1, 10**8))
        device = l["signup_device"]
        traffic_source = l["acquisition_channel"]
        rows.append([eid, l["landlord_id"], "landlord", l["signup_date"], "account_created", None, session_id, device, traffic_source]); eid += 1
        if not l["activated_7d"]:
            continue
        try:
            lprops = props_by_landlord.get_group(l["landlord_id"])
        except KeyError:
            continue
        for _, p in lprops.iterrows():
            rows.append([eid, l["landlord_id"], "landlord", p["date_added"], "property_added", p["property_id"], session_id, device, traffic_source]); eid += 1
            if pd.notna(p["listing_publish_date"]):
                rows.append([eid, l["landlord_id"], "landlord", p["listing_publish_date"], "listing_published", p["property_id"], session_id, device, traffic_source]); eid += 1
                if rng.random() < 0.6:
                    ev_date = p["listing_publish_date"] + timedelta(days=int(rng.exponential(5)))
                    if ev_date <= END_DATE:
                        rows.append([eid, l["landlord_id"], "landlord", ev_date, "tenant_invited", p["property_id"], session_id, device, traffic_source]); eid += 1
        if l["first_feature_adopted"] == "online_rent_collection" and rng.random() < 0.8:
            ev_date = l["signup_date"] + timedelta(days=int(rng.integers(1, 20)))
            if ev_date <= END_DATE:
                rows.append([eid, l["landlord_id"], "landlord", ev_date, "rent_collection_enabled", None, session_id, device, traffic_source]); eid += 1
        if l["is_paid"] and pd.notna(l["subscription_start_date"]):
            rows.append([eid, l["landlord_id"], "landlord", l["subscription_start_date"], "subscription_started", None, session_id, device, traffic_source]); eid += 1
        if pd.notna(l["churn_date"]) and l["is_paid"]:
            rows.append([eid, l["landlord_id"], "landlord", l["churn_date"], "subscription_cancelled", None, session_id, device, traffic_source]); eid += 1
        if len(rows) >= target_total_events:
            break

    df = pd.DataFrame(rows, columns=["event_id", "user_id", "user_type", "event_timestamp", "event_name",
                                       "property_id", "session_id", "device_type", "traffic_source"])
    return df


def make_payments(applications, properties):
    rows = []
    pid = 1
    leased = applications[applications["lease_signed"] == True].merge(
        properties[["property_id", "monthly_rent"]], on="property_id", how="left")
    for _, a in leased.iterrows():
        lease_id = "LS" + a["application_id"][1:]
        n_months = int(rng.integers(3, 24))
        due = a["application_date"] + timedelta(days=15)
        for m in range(n_months):
            due_date = due + timedelta(days=30 * m)
            if due_date > END_DATE:
                break
            on_time = rng.random() < 0.90
            status = "on_time" if on_time else rng.choice(["late", "failed"], p=[0.7, 0.3])
            pay_date = due_date if status == "on_time" else due_date + timedelta(days=int(rng.integers(1, 15)))
            failure_reason = None if status != "failed" else rng.choice(
                ["insufficient_funds", "card_declined", "bank_error", "account_closed"])
            rows.append({
                "payment_id": "PY" + str(pid).zfill(8),
                "lease_id": lease_id,
                "due_date": due_date,
                "payment_date": pay_date if status != "failed" else pd.NaT,
                "payment_amount": a["monthly_rent"],
                "payment_status": status,
                "payment_method": rng.choice(["ach", "credit_card", "debit_card"], p=[0.6, 0.25, 0.15]),
                "failure_reason": failure_reason,
            })
            pid += 1
    return pd.DataFrame(rows)


def make_marketing_spend(landlords):
    landlords = landlords.copy()
    landlords["month"] = pd.to_datetime(landlords["signup_date"]).dt.to_period("M").astype(str)
    landlords["metro_name"] = landlords["metro_id"].map(METROS.set_index("metro_id")["metro_name"])
    grp = landlords.groupby(["month", "acquisition_channel", "metro_name"]).size().reset_index(name="signups")
    grp["cac"] = grp["acquisition_channel"].map(CHANNEL_CAC)
    grp["spend"] = (grp["signups"] * grp["cac"] * rng.uniform(0.9, 1.3, len(grp))).round(2)
    grp["clicks"] = (grp["signups"] * rng.uniform(8, 20, len(grp))).round(0).astype(int)
    grp["impressions"] = (grp["clicks"] * rng.uniform(15, 40, len(grp))).round(0).astype(int)
    grp["campaign"] = grp["acquisition_channel"] + "_" + grp["month"]
    return grp[["month", "acquisition_channel", "metro_name", "campaign", "impressions", "clicks", "spend", "signups"]].rename(
        columns={"acquisition_channel": "channel", "metro_name": "market"})


def make_experiment(landlords):
    """Guided Property Onboarding A/B test: only landlords who signed up in a 90-day experiment window."""
    exp_start = datetime(2025, 3, 1)
    exp_end = datetime(2025, 5, 30)
    mask = (pd.to_datetime(landlords["signup_date"]) >= exp_start) & (pd.to_datetime(landlords["signup_date"]) <= exp_end)
    exp_landlords = landlords[mask].copy()
    n = len(exp_landlords)
    variant = rng.choice(["control", "treatment"], size=n, p=[0.5, 0.5])
    # true uplift: guided checklist improves activation by ~6.5pp absolute
    true_lift = np.where(variant == "treatment", 0.065, 0.0)
    activation_base = exp_landlords["activated_7d"].astype(float).values
    # Re-simulate activation with the lift baked in (keep original as base propensity)
    activation_p = np.clip(activation_base * 0.85 + true_lift + rng.normal(0, 0.03, n), 0.02, 0.97)
    activation_7d = rng.random(n) < activation_p
    paid_conv_30d = np.where(activation_7d, rng.random(n) < (0.18 + true_lift * 0.5), False)

    df = pd.DataFrame({
        "user_id": exp_landlords["landlord_id"].values,
        "experiment_name": "guided_property_onboarding",
        "variant": variant,
        "exposure_date": exp_landlords["signup_date"].values,
        "activation_7d": activation_7d,
        "paid_conversion_30d": paid_conv_30d,
    })
    return df


def main(scale):
    if scale == "full":
        n_landlords, n_tenants, n_events_target = 50_000, 150_000, 1_000_000
    else:
        n_landlords, n_tenants, n_events_target = 5_000, 15_000, 120_000

    print(f"Generating scale='{scale}': {n_landlords} landlords, {n_tenants} tenants, target ~{n_events_target} events")

    landlords = make_landlords(n_landlords)
    landlords = simulate_landlord_lifecycle(landlords)
    print("landlords done:", len(landlords))

    properties = make_properties(landlords)
    print("properties done:", len(properties))

    tenants = make_tenants(n_tenants)
    print("tenants done:", len(tenants))

    applications = make_applications(properties, tenants)
    print("applications done:", len(applications))

    events = make_product_events(landlords, properties, n_events_target)
    print("events done:", len(events))

    payments = make_payments(applications, properties)
    print("payments done:", len(payments))

    marketing = make_marketing_spend(landlords)
    print("marketing done:", len(marketing))

    experiment = make_experiment(landlords)
    print("experiment done:", len(experiment))

    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    os.makedirs(out_dir, exist_ok=True)

    landlords_out = landlords.drop(columns=["signup_device"]).rename(columns={"signup_device": None}, errors="ignore")
    # keep signup_device as its own useful column instead of dropping
    landlords_out = landlords.copy()

    landlords_out.to_csv(os.path.join(out_dir, "landlords.csv"), index=False)
    properties.to_csv(os.path.join(out_dir, "properties.csv"), index=False)
    tenants.to_csv(os.path.join(out_dir, "tenants.csv"), index=False)
    applications.to_csv(os.path.join(out_dir, "applications.csv"), index=False)
    events.to_csv(os.path.join(out_dir, "product_events.csv"), index=False)
    payments.to_csv(os.path.join(out_dir, "payments.csv"), index=False)
    marketing.to_csv(os.path.join(out_dir, "marketing_spend.csv"), index=False)
    experiment.to_csv(os.path.join(out_dir, "experiment_exposure.csv"), index=False)
    METROS.to_csv(os.path.join(out_dir, "metros_dim.csv"), index=False)

    print("\nAll files written to", os.path.abspath(out_dir))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=["full", "demo"], default="demo")
    args = parser.parse_args()
    main(args.scale)
