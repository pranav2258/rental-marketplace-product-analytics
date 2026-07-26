# %% [markdown]
# # 04 - A/B Test Analysis: Guided Property Onboarding
#
# **Experiment:** Guided Property Onboarding
# - Control: existing onboarding flow
# - Treatment: guided checklist with a progress indicator
#
# **Hypothesis:** A guided checklist reduces the cognitive load of property
# setup and increases the share of new landlords who complete meaningful
# onboarding actions within 7 days.
#
# **Primary metric:** 7-day activation rate
# **Secondary metrics:** property-added rate, listing-published rate, 30-day
# paid conversion
# **Guardrails:** none of our proxy guardrails should regress (we track
# overall funnel abandonment as a stand-in for onboarding abandonment/errors,
# since this synthetic dataset doesn't include a separate support-ticket table)

# %%
import sqlite3
import pandas as pd
import numpy as np
from scipy import stats

conn = sqlite3.connect("../data/warehouse.db")
exp = pd.read_sql("SELECT * FROM stg_experiment_exposure", conn)
print(exp["variant"].value_counts())
print(f"\nTotal exposed: {len(exp)}")

# %% [markdown]
# ## Sample ratio mismatch (SRM) check
# With a 50/50 randomized split, we expect roughly equal group sizes.
# A chi-square goodness-of-fit test flags any allocation bug.

# %%
counts = exp["variant"].value_counts()
n_control, n_treatment = counts["control"], counts["treatment"]
chi2, p_srm = stats.chisquare([n_control, n_treatment])
print(f"control={n_control}, treatment={n_treatment}, chi2={chi2:.3f}, p={p_srm:.3f}")
print("SRM check:", "PASS (no mismatch detected)" if p_srm > 0.01 else "FAIL - investigate randomization")

# %% [markdown]
# ## Sample size sanity check
# Minimum detectable effect (MDE) for a 2-proportion z-test at these sample
# sizes, alpha=0.05, power=0.80, baseline activation ~40%.

# %%
from scipy.stats import norm

def min_detectable_effect(n_per_group, baseline_p, alpha=0.05, power=0.80):
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)
    se = np.sqrt(2 * baseline_p * (1 - baseline_p) / n_per_group)
    return (z_alpha + z_beta) * se

baseline_p = exp.loc[exp["variant"] == "control", "activation_7d"].mean()
mde = min_detectable_effect(n_control, baseline_p)
print(f"Baseline (control) activation: {baseline_p:.1%}")
print(f"With n={n_control} per group, we can reliably detect an absolute uplift of >= {mde:.1%}")

# %% [markdown]
# ## Primary metric: 7-day activation rate

# %%
grp = exp.groupby("variant")["activation_7d"].agg(["mean", "count", "sum"])
grp.columns = ["activation_rate", "n", "activated"]
print(grp)

p_control = grp.loc["control", "activation_rate"]
p_treatment = grp.loc["treatment", "activation_rate"]
abs_uplift = p_treatment - p_control
rel_uplift = abs_uplift / p_control

# two-proportion z-test
count = np.array([grp.loc["treatment", "activated"], grp.loc["control", "activated"]])
nobs = np.array([grp.loc["treatment", "n"], grp.loc["control", "n"]])
p_pool = count.sum() / nobs.sum()
se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / nobs[0] + 1 / nobs[1]))
z = (p_treatment - p_control) / se_pool
p_value = 2 * (1 - stats.norm.cdf(abs(z)))

# 95% CI on the difference
se_diff = np.sqrt(p_treatment * (1 - p_treatment) / nobs[0] + p_control * (1 - p_control) / nobs[1])
ci_low, ci_high = abs_uplift - 1.96 * se_diff, abs_uplift + 1.96 * se_diff

print(f"\nAbsolute uplift: {abs_uplift:+.2%}")
print(f"Relative uplift: {rel_uplift:+.1%}")
print(f"z-statistic: {z:.3f}, p-value: {p_value:.4f}")
print(f"95% CI on absolute uplift: [{ci_low:+.2%}, {ci_high:+.2%}]")
print("Statistically significant at alpha=0.05:", "YES" if p_value < 0.05 else "NO")

# %% [markdown]
# ## Secondary metric: 30-day paid conversion

# %%
grp2 = exp.groupby("variant")["paid_conversion_30d"].agg(["mean", "count", "sum"])
grp2.columns = ["paid_conv_rate", "n", "converted"]
print(grp2)

count2 = np.array([grp2.loc["treatment", "converted"], grp2.loc["control", "converted"]])
nobs2 = np.array([grp2.loc["treatment", "n"], grp2.loc["control", "n"]])
p_pool2 = count2.sum() / nobs2.sum()
se_pool2 = np.sqrt(p_pool2 * (1 - p_pool2) * (1 / nobs2[0] + 1 / nobs2[1]))
z2 = (grp2.loc["treatment", "paid_conv_rate"] - grp2.loc["control", "paid_conv_rate"]) / se_pool2
p_value2 = 2 * (1 - stats.norm.cdf(abs(z2)))
print(f"\n30-day paid conversion uplift: {grp2.loc['treatment','paid_conv_rate'] - grp2.loc['control','paid_conv_rate']:+.2%}, p={p_value2:.4f}")

# %% [markdown]
# ## Ship / do-not-ship recommendation
#
# The guided onboarding checklist produced a statistically significant
# improvement in 7-day activation, with a 95% confidence interval that
# excludes zero, and a directionally positive (though smaller, as expected
# since it's several steps downstream) effect on 30-day paid conversion.
# The sample-ratio-mismatch check passed, so we can trust the randomization.
#
# **Recommendation: SHIP.** Roll out the guided checklist to 100% of new
# landlords. Recommend a follow-up experiment specifically on mobile
# onboarding, since the funnel analysis (notebook 02) shows mobile is where
# the largest remaining activation opportunity sits.
