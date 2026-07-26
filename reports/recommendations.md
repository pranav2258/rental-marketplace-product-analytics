# Executive Insights & Recommendations

*Rental Marketplace Product Analytics Platform — synthetic data, see README
for scope and limitations.*

## 1. Fix mobile onboarding before scaling mobile paid-social spend

Mobile-acquired landlords from paid social abandon between "property added"
and "listing published" at a **40.9% rate**, versus 1.5% for
referral-acquired desktop landlords. Paid social is also the highest-CAC
channel. The combination means a meaningful share of paid acquisition spend
is producing signups that never reach a published listing — the point where
the platform actually starts generating marketplace value (applications,
leases, rent collection).

**Action:** Simplify the mobile property-setup flow (fewer required fields,
save-and-resume) before increasing mobile paid-social budget. Re-measure
abandonment by device after the fix ships.

## 2. Make "enable rent collection" the activation goal, not "publish a listing"

Landlords whose first adopted feature is online rent collection retain at
**80.1% by month 6**, versus 72.4% for landlords who only use listing tools
first. This holds even after controlling for portfolio size and channel.

**Action:** Update onboarding messaging and in-product nudges to point new,
activated landlords toward enabling rent collection in their first session,
not just toward publishing a listing.

## 3. Ship the guided onboarding checklist

The Guided Property Onboarding A/B test produced a **+6.29 percentage point
absolute lift** in 7-day activation (18.1% relative), 95% CI [+3.3%, +9.3%],
p<0.0001. The sample-ratio-mismatch check passed, so the randomization can
be trusted. Thirty-day paid conversion also moved directionally positive.

**Action:** Ship to 100% of new landlords. Follow up with a dedicated
mobile-onboarding experiment, since that's where finding #1 shows the
largest remaining opportunity.

## 4. Plan around the Holt-trend MRR forecast, not the optimistic case

A Holt linear-trend model backtested at 2.9% MAPE against the last 6 months
of actuals, dramatically outperforming a seasonal-naive baseline (39.6%
MAPE). The 6-month forward forecast should be the base case for budget and
hiring planning; the guided-onboarding rollout's activation lift is
directional upside on top of that base case, not guaranteed and not yet
reflected in the forecast.

## 5. Prioritize Phoenix, Orlando, Austin, and Atlanta for expansion

These four metros rank in the top 5 by opportunity score under all three
tested weighting schemes (demand-heavy, whitespace-heavy, and the balanced
base case), meaning the recommendation is robust to how much the business
trusts "demand" versus "current whitespace" versus "current platform
performance." Markets that only rank highly under one specific weighting
(e.g. San Antonio under whitespace-heavy) should be treated as lower-
confidence picks pending further market-specific due diligence.

---

*A data-quality note: two real bugs were found and fixed during this
project's build — a generator gap that hid the mobile-abandonment finding,
and a warehouse mart that truncated long-tenured subscribers' MRR. Both are
documented in the README and on the dashboard's Data Quality page. Flagging
this here deliberately: the value of the quality-test layer is catching
exactly this kind of thing before a stakeholder sees a wrong number.*
