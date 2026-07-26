# %% [markdown]
# # 02 - Funnel Drop-off Analysis
# Uses `mart_landlord_funnel` (built with SQL window functions and conditional
# aggregation) to find WHERE landlords abandon onboarding, and for WHICH
# segments the drop-off is worst -- not just where the biggest average drop is.

# %%
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

conn = sqlite3.connect("../data/warehouse.db")
funnel = pd.read_sql("SELECT * FROM mart_landlord_funnel", conn)
funnel.head()

# %% [markdown]
# ## Step 1: Overall funnel shape

# %%
steps = ["pct_property_added", "pct_listing_published", "pct_tenant_invited",
         "pct_rent_collection_enabled", "pct_paid_conversion"]
overall = (funnel[steps].mul(funnel["landlords"], axis=0).sum() / funnel["landlords"].sum())
print(overall.round(3))

fig, ax = plt.subplots(figsize=(9, 4))
overall.plot(kind="bar", ax=ax, color="#2563eb")
ax.set_title("Overall Landlord Funnel Conversion (of activated landlords)")
ax.set_ylabel("% reaching step")
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.show()

# %% [markdown]
# The naive read is "listing publication has the largest drop." That's true on
# average -- but it hides which *segments* are driving it. Breaking the same
# step down by channel x device below is where the actionable insight is.

# %% [markdown]
# ## Step 2: Which channel x device combos have strong signup volume but weak
# activation-to-publish follow-through?

# %%
by_channel_device = (
    funnel.groupby(["acquisition_channel", "signup_device"])
    .apply(lambda g: pd.Series({
        "landlords": g["landlords"].sum(),
        "pct_listing_published": (g["pct_listing_published"] * g["landlords"]).sum() / g["landlords"].sum(),
        "publish_abandonment_rate": (g["publish_abandonment_rate"] * g["landlords"]).sum() / g["landlords"].sum(),
        "avg_days_to_publish": (g["avg_days_to_publish"].fillna(0) * g["landlords"]).sum() / g["landlords"].sum(),
    }), include_groups=False)
    .reset_index()
    .sort_values("landlords", ascending=False)
)
by_channel_device.round(3).head(15)

# %% [markdown]
# ## Step 3: Isolate the worst combination by volume-weighted abandonment

# %%
sizeable = by_channel_device[by_channel_device["landlords"] >= 200]
worst = sizeable.sort_values("publish_abandonment_rate", ascending=False).head(5)
best = sizeable.sort_values("publish_abandonment_rate", ascending=True).head(5)
print("WORST activation-to-publish segments (min 200 landlords):")
print(worst[["acquisition_channel", "signup_device", "landlords", "publish_abandonment_rate", "avg_days_to_publish"]].to_string(index=False))
print("\nBEST activation-to-publish segments:")
print(best[["acquisition_channel", "signup_device", "landlords", "publish_abandonment_rate", "avg_days_to_publish"]].to_string(index=False))

# %% [markdown]
# ## Step 4: Portfolio-size and metro cuts

# %%
by_portfolio = (
    funnel.groupby("portfolio_segment")
    .apply(lambda g: pd.Series({
        "landlords": g["landlords"].sum(),
        "pct_paid_conversion": (g["pct_paid_conversion"] * g["landlords"]).sum() / g["landlords"].sum(),
    }), include_groups=False)
)
print(by_portfolio.round(3))

top_metros = (
    funnel.groupby("metro_id")
    .apply(lambda g: pd.Series({
        "landlords": g["landlords"].sum(),
        "pct_paid_conversion": (g["pct_paid_conversion"] * g["landlords"]).sum() / g["landlords"].sum(),
    }), include_groups=False)
    .sort_values("landlords", ascending=False)
    .head(8)
)
print("\nHigh-volume metros, paid conversion:")
print(top_metros.round(3))

# %% [markdown]
# ## Finding
#
# Mobile-acquired landlords consistently show a higher listing-publish
# abandonment rate and a longer average time-to-publish than desktop landlords
# across every channel, and the effect compounds for paid-social specifically
# (highest CAC channel, weakest mobile follow-through). Large-portfolio
# landlords (10+ units) convert to paid at a materially higher rate than
# small landlords, consistent with them having more to gain from paid
# features like bulk rent collection.
#
# **Recommendation:** Prioritize a simplified mobile property/listing setup
# flow (fewer required fields, save-and-resume) before spending further on
# mobile paid-social acquisition -- the channel is bringing in volume the
# product isn't currently converting to published listings.
