# %% [markdown]
# # 01 - Exploratory Data Analysis
# Rental Marketplace Product Analytics Platform
#
# Quick orientation pass over the warehouse: table sizes, date ranges,
# and headline distributions before we move into the five required analyses.

# %%
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

pd.set_option("display.max_columns", 50)
conn = sqlite3.connect("../data/warehouse.db")

tables = ["stg_landlords", "stg_properties", "stg_tenants" if False else "raw_tenants",
          "stg_applications", "stg_payments", "stg_events", "stg_market_monthly"]
for t in tables:
    n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"{t:<20} {n:>10,} rows")

# %% [markdown]
# ## Landlord signups over time

# %%
df = pd.read_sql("SELECT signup_date FROM stg_landlords", conn, parse_dates=["signup_date"])
monthly = df.set_index("signup_date").resample("MS").size()

fig, ax = plt.subplots(figsize=(10, 4))
monthly.plot(ax=ax, color="#2563eb")
ax.set_title("Landlord Signups by Month")
ax.set_ylabel("New landlords")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Portfolio size and experience mix

# %%
landlords = pd.read_sql("SELECT * FROM stg_landlords", conn)
print(landlords["experience_level"].value_counts(normalize=True).round(3))
print()
print(landlords["acquisition_channel"].value_counts(normalize=True).round(3))

# %% [markdown]
# ## Activation and paid-conversion headline rates

# %%
activation_rate = landlords["activated_7d"].mean()
paid_rate = landlords["is_paid"].mean()
free_to_paid = landlords.loc[landlords["activated_7d"] == 1, "is_paid"].mean()
print(f"Overall 7-day activation rate: {activation_rate:.1%}")
print(f"Overall paid conversion rate: {paid_rate:.1%}")
print(f"Free-to-paid conversion (of activated): {free_to_paid:.1%}")

# %% [markdown]
# ## Rent distribution by property type

# %%
props = pd.read_sql("SELECT property_type, monthly_rent FROM stg_properties", conn)
fig, ax = plt.subplots(figsize=(9, 4))
props.boxplot(column="monthly_rent", by="property_type", ax=ax)
ax.set_title("Monthly Rent by Property Type")
plt.suptitle("")
ax.set_ylabel("Monthly rent ($)")
plt.tight_layout()
plt.show()

# %% [markdown]
# Data looks internally consistent: signups grow over time as expected from
# the platform-growth weighting in the generator, activation and paid-conversion
# rates land in plausible SaaS-marketplace ranges, and rent distributions vary
# sensibly by property type. Proceeding to the five required analyses.
