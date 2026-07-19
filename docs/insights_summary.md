# E-Commerce Sales Analysis — Insights Summary

**Dataset:** 15,000 order records, 1 Jan 2023 – 31 Dec 2024
**Deliverables:** cleaned dataset, Excel workbook, SQL database and queries, interactive dashboard

---

## Headline numbers

| Metric | Value |
| --- | --- |
| Total Sales | Rs 4,93,84,840 (Rs 4.94 Cr) |
| Total Profit | Rs 73,77,771 (Rs 73.78 L) |
| Total Orders | 15,000 |
| Total Quantity Sold | 45,191 units |
| Average Discount | 15.01% |
| Overall Profit Margin | 14.94% |
| Unique Customers | 7,294 |
| Average Order Value | Rs 3,292.32 |

These aggregate figures are exact. They were computed independently in pandas and
in SQL and cross-checked to the rupee — see `src/05_build_database.py`.

---

## The five business questions

| # | Question | Answer | Does it hold up? |
| --- | --- | --- | --- |
| 1 | Highest-sales state | **Rajasthan** — Rs 72.30 L (14.6%) | **No.** Holds top in 39% of resamples |
| 2 | Most profitable category | **Electronics** — Rs 15.51 L profit | **No.** Holds top in 78% of resamples |
| 3 | Highest-revenue product | **Tablet** — Rs 22.05 L | **No.** Holds top in 42% of resamples |
| 4 | Most-used payment method | **Cash on Delivery** — 20.4% of orders | **No.** An even split is 20.0% |
| 5 | Monthly sales trend | **Flat** — H2 vs H1: −0.2% | Genuinely flat; R² = 0.008 |

Every answer above is the literal top of its ranking, as the brief asks. The
right-hand column is the part that matters.

---

## The main finding: these rankings are noise

This is the most important result in the project, and it is easy to miss if you
only read the bar charts.

Each dimension was tested two ways (`src/03_significance_tests.py`):

1. **Permutation test** — shuffle the group labels 2,000 times while holding the
   sales values fixed. If the real gap between best and worst group is no larger
   than a shuffle produces, the ranking carries no information.
2. **Bootstrap** — resample the 15,000 orders with replacement 2,000 times and
   re-rank. If the leader keeps changing, the leaderboard is not stable.

| Dimension | Leader | Permutation p | Leader holds top in | Verdict |
| --- | --- | --- | --- | --- |
| State | Rajasthan | 0.710 | 38.7% | Noise |
| Product Category | Electronics | 0.582 | 78.0% | Noise |
| Payment Mode | Cash on Delivery | 0.149 | 86.5% | Noise |
| City | Lucknow | 0.525 | 42.9% | Noise |
| Product Name | Tablet | 0.049 | 42.1% | Noise |

**Not one dimension clears the bar.** Every leader's 95% confidence interval for
its margin over the runner-up crosses zero. The observed spread between groups is
*smaller than the median spread produced by randomly shuffled labels* for State,
Category and City — the groups are, if anything, more uniform than chance.

Product Name shows p = 0.049, nominally under 0.05. It should not be treated as a
discovery: it is one marginal result out of five tests (with five tests, the
chance of at least one p < 0.05 under pure noise is about 23%), and its bootstrap
interval still crosses zero, with "Tablet" holding first place in only 42% of
resamples. The two tests disagree, and the weaker conclusion is the honest one.

**What this means in practice:** "Rajasthan is our strongest state" is a coin
flip. Re-run the same report next quarter on fresh data from the same process and
a different state would likely top the chart, with no change in the business.
Acting on these rankings — shifting budget to Rajasthan, promoting Tablets,
building a Cash-on-Delivery strategy — would be responding to random variation.

---

## What the data actually shows

**1. The business is remarkably uniform.**
Seven states each take 14.3–14.6% of revenue (an exact even split is 14.29%).
Five payment modes each take ~20%. Five categories each take ~20%. Orders per
state range only from 2,105 to 2,161. This is the signature of a generated
dataset, not of a real market — real e-commerce revenue is famously concentrated,
typically with a handful of SKUs and one or two regions dominating.

**2. Margins are flat everywhere.**
Every product category returns a ~15% margin, matching the 14.94% overall figure.
In a real catalogue, electronics and apparel have very different margin profiles.
Here, profit is essentially a fixed fraction of revenue, so **no product-mix
decision can be justified from this data** — there is no high-margin category to
shift toward.

**3. There is no time trend and no seasonality.**
Across 24 months, a linear fit gives R² = 0.008 — the trend line explains under 1%
of the variation. Once unequal month lengths are removed, per-day sales vary with
a coefficient of variation of just 3.9%, and peak month is only 1.18× the trough.
There is no festive-season lift, no year-over-year growth, no weekday effect worth
reporting. **The apparent "peak" in March 2023 and "trough" in February 2023 are
noise**, and February is partly an artifact of having 28 days.

**4. Discounts do not appear to drive anything.**
Discount averages 15.0% and is distributed evenly from 0–30% across every
category, state and payment mode. There is no discount-elasticity story to tell.

---

## Data quality

The source file arrived in unusually good condition. The cleaning pipeline
(`src/01_data_cleaning.py`) ran every check the brief requires and found:

- **0** missing values across all 12 columns
- **0** duplicate rows and **0** repeated Order_IDs
- **0** malformed dates; all 15,000 parse cleanly and fall inside the stated range
- **0** non-numeric values in Quantity, Sales_Amount, Discount or Profit
- **0** out-of-range values (no negative quantities, no discounts outside 0–30%)
- **0** products assigned to more than one category

All 15,000 rows survived cleaning. The pipeline still runs every check so the
result is *verified* rather than assumed, and so it stays correct if the source is
refreshed with messier data.

### One real defect: State and City are not related

Every one of the 7 states is paired with all 7 cities — all 49 combinations occur.
The data contains records such as *Uttar Pradesh / Chennai* and *Karnataka /
Mumbai*, which are geographically impossible.

This was **not silently corrected**, because there is no way to repair it without
inventing facts about where each order was placed.

**Consequence:** state-level and city-level figures are each internally consistent
and safe to report on their own, but the two must never be combined. A
State → City drill-down in any dashboard built on this data would be meaningless,
and no conclusion should be drawn about which city drives a given state.

---

## Recommendations

**On this dataset:**

1. **Do not make business decisions from these rankings.** Report the totals — they
   are correct and useful. Treat every "top state / top product / top category"
   claim as provisional, and quote the confidence alongside it.
2. **Never build a State → City hierarchy** in any report or dashboard sourced from
   this file.
3. Use this dataset for what it is well suited to: practising cleaning, SQL,
   aggregation and dashboard construction. The pipeline here is genuinely
   reusable; the conclusions are not.

**If this were a real business:**

The right next step would be to get data with enough variation to analyse —
covering a period with a known event (a sale, a launch, a stockout) so that
technique can be validated against a real effect. A flat, uniform dataset cannot
distinguish a good analysis from a bad one, because every method returns "no
difference."

**The transferable lesson:** a bar chart will always render a tallest bar, and a
dashboard will always name a winner. Neither is evidence that the winner is real.
The check that separates a finding from an artifact takes about twenty lines of
code — `src/03_significance_tests.py` — and it should be run before any ranking is
presented as an insight.

---

## Reproducing this analysis

```bash
pip install -r requirements.txt
python run_all.py
```

| Output | Path |
| --- | --- |
| Cleaned dataset | `data/processed/ecommerce_sales_cleaned.csv` / `.xlsx` |
| Excel workbook (10 sheets, 7 native charts) | `outputs/ecommerce_analysis.xlsx` |
| SQLite database | `outputs/ecommerce.db` |
| SQL schema and queries | `sql/01_schema.sql`, `sql/02_analysis_queries.sql` |
| Interactive dashboard | `dashboard/index.html` |
| Chart images | `outputs/charts/*.png` |
| Insight tables | `outputs/tables/*.csv` |
| Data quality report | `outputs/data_quality_report.md` |
