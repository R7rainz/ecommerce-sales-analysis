"""Step 3b - Are the rankings real, or is this noise?

Every breakdown in this project produces a "winner". This script asks whether
those winners are distinguishable from random variation, so the written summary
can state its confidence instead of implying a pattern that is not there.

Two tests per dimension:

  1. Permutation test. Shuffle the group labels many times while holding the
     sales values fixed. If the real gap between best and worst group is no
     bigger than the gap a shuffle produces, the ranking carries no signal.

  2. Bootstrap CI on the leader's margin. Resample orders with replacement and
     re-rank. If the leader's margin over the runner-up crosses zero, the top
     spot is not stable.

Run:  python src/03_significance_tests.py
"""

import json

import numpy as np
import pandas as pd

from config import CLEAN_CSV, OUTPUT_DIR, TABLE_DIR, ensure_dirs

N_PERMUTATIONS = 2000
N_BOOTSTRAP = 2000
SEED = 42
ALPHA = 0.05

DIMENSIONS = ["State", "Product_Category", "Payment_Mode", "City", "Product_Name"]


def permutation_test(
    df: pd.DataFrame, group_col: str, value_col: str, rng: np.random.Generator
) -> dict:
    """Compare the real between-group spread against shuffled labels."""
    values = df[value_col].to_numpy()
    labels = df[group_col].to_numpy()

    def spread(lab: np.ndarray) -> float:
        totals = pd.Series(values).groupby(lab).sum()
        return float((totals.max() - totals.min()) / totals.mean())

    observed = spread(labels)
    null = np.array([spread(rng.permutation(labels)) for _ in range(N_PERMUTATIONS)])
    p_value = float((null >= observed).mean())

    return {
        "observed_spread": round(observed, 5),
        "null_median_spread": round(float(np.median(null)), 5),
        "null_p95_spread": round(float(np.percentile(null, 95)), 5),
        "p_value": round(p_value, 4),
        "significant": bool(p_value < ALPHA),
    }


def bootstrap_leader_margin(
    df: pd.DataFrame, group_col: str, value_col: str, rng: np.random.Generator
) -> dict:
    """Resample orders and ask how often the leader stays the leader."""
    totals = df.groupby(group_col)[value_col].sum().sort_values(ascending=False)
    leader, runner_up = totals.index[0], totals.index[1]
    observed_margin = float(totals.iloc[0] - totals.iloc[1])

    values = df[value_col].to_numpy()
    codes, uniques = pd.factorize(df[group_col])
    n = len(df)
    leader_idx = list(uniques).index(leader)

    margins = np.empty(N_BOOTSTRAP)
    wins = 0
    for i in range(N_BOOTSTRAP):
        pick = rng.integers(0, n, n)
        sums = np.bincount(codes[pick], weights=values[pick], minlength=len(uniques))
        order = np.argsort(sums)[::-1]
        margins[i] = sums[order[0]] - sums[order[1]]
        if order[0] == leader_idx:
            wins += 1

    # CI on the leader's own margin, signed: negative means it lost the top spot.
    signed = np.empty(N_BOOTSTRAP)
    for i in range(N_BOOTSTRAP):
        pick = rng.integers(0, n, n)
        sums = np.bincount(codes[pick], weights=values[pick], minlength=len(uniques))
        best_other = np.max(np.delete(sums, leader_idx))
        signed[i] = sums[leader_idx] - best_other

    lo, hi = np.percentile(signed, [2.5, 97.5])
    return {
        "leader": str(leader),
        "runner_up": str(runner_up),
        "observed_margin": round(observed_margin, 2),
        "margin_ci_low": round(float(lo), 2),
        "margin_ci_high": round(float(hi), 2),
        "margin_ci_excludes_zero": bool(lo > 0),
        "leader_retention_rate": round(wins / N_BOOTSTRAP, 4),
    }


def trend_test(df: pd.DataFrame) -> dict:
    """Is there a real time trend, once unequal month lengths are removed?"""
    monthly = df.groupby("Order_Month").agg(
        sales=("Sales_Amount", "sum"), orders=("Order_ID", "count")
    )
    days = pd.PeriodIndex(monthly.index, freq="M").days_in_month
    per_day = monthly["sales"] / days

    x = np.arange(len(per_day))
    y = per_day.to_numpy()
    slope, intercept = np.polyfit(x, y, 1)
    fit = slope * x + intercept
    ss_res = float(((y - fit) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r_squared = 1 - ss_res / ss_tot if ss_tot else 0.0

    return {
        "months": int(len(per_day)),
        "raw_monthly_cv": round(float(monthly["sales"].std() / monthly["sales"].mean()), 4),
        "per_day_cv": round(float(per_day.std() / per_day.mean()), 4),
        "per_day_slope": round(float(slope), 2),
        "trend_r_squared": round(float(r_squared), 4),
        "peak_month": str(per_day.idxmax()),
        "trough_month": str(per_day.idxmin()),
        "peak_vs_trough_ratio": round(float(per_day.max() / per_day.min()), 4),
    }


def verdict(perm: dict, boot: dict) -> str:
    if perm["significant"] and boot["margin_ci_excludes_zero"]:
        return "REAL - ranking is statistically distinguishable from noise"
    if boot["leader_retention_rate"] >= 0.90:
        return "WEAK - leader is stable but group differences are not significant"
    return "NOISE - ranking is not distinguishable from random variation"


def main() -> None:
    ensure_dirs()
    print("=" * 72)
    print("STEP 3b - SIGNIFICANCE TESTING")
    print("=" * 72 + "\n")

    df = pd.read_csv(CLEAN_CSV, parse_dates=["Order_Date"])
    rng = np.random.default_rng(SEED)
    print(f"{len(df):,} orders | {N_PERMUTATIONS:,} permutations | "
          f"{N_BOOTSTRAP:,} bootstrap resamples\n")

    results, rows = {}, []
    for dim in DIMENSIONS:
        perm = permutation_test(df, dim, "Sales_Amount", rng)
        boot = bootstrap_leader_margin(df, dim, "Sales_Amount", rng)
        v = verdict(perm, boot)
        results[dim] = {"permutation": perm, "bootstrap": boot, "verdict": v}

        print(f"{dim}")
        print(f"  leader              {boot['leader']} over {boot['runner_up']}")
        print(f"  permutation p       {perm['p_value']:.4f}"
              f"   (observed spread {perm['observed_spread']:.4f} vs "
              f"null median {perm['null_median_spread']:.4f})")
        print(f"  margin 95% CI       [{boot['margin_ci_low']:,.0f}, "
              f"{boot['margin_ci_high']:,.0f}]")
        print(f"  leader holds top    {boot['leader_retention_rate']:.1%} of resamples")
        print(f"  verdict             {v}\n")

        rows.append(
            {
                "Dimension": dim,
                "Leader": boot["leader"],
                "Runner_Up": boot["runner_up"],
                "Observed_Margin": boot["observed_margin"],
                "Margin_CI_Low": boot["margin_ci_low"],
                "Margin_CI_High": boot["margin_ci_high"],
                "Leader_Retention_Rate": boot["leader_retention_rate"],
                "Permutation_P_Value": perm["p_value"],
                "Significant_At_5pct": perm["significant"],
                "Verdict": v.split(" - ")[0],
            }
        )

    trend = trend_test(df)
    results["Monthly_Trend"] = trend
    print("Monthly trend")
    print(f"  raw monthly CV      {trend['raw_monthly_cv']:.2%}")
    print(f"  per-day CV          {trend['per_day_cv']:.2%} "
          f"(after removing unequal month lengths)")
    print(f"  linear fit R^2      {trend['trend_r_squared']:.4f}")
    print(f"  peak vs trough      {trend['peak_vs_trough_ratio']:.2f}x")
    print()

    pd.DataFrame(rows).to_csv(TABLE_DIR / "significance_tests.csv", index=False)
    (OUTPUT_DIR / "significance_tests.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )

    n_real = sum(1 for r in rows if r["Verdict"] == "REAL")
    print("=" * 72)
    print(f"CONCLUSION: {n_real} of {len(rows)} dimensions show a statistically "
          f"real ranking.")
    if n_real == 0:
        print("Every headline ranking in this dataset is within random variation.")
        print("Report the winners as required, but do not build a story on them.")
    print("=" * 72)
    print("\nWrote tables/significance_tests.csv and outputs/significance_tests.json")


if __name__ == "__main__":
    main()
