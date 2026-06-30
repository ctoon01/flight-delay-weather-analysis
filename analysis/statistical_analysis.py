"""
statistical_analysis.py — Runs the core inferential analysis:

  1. Two-sample t-test: does departure delay differ between
     precipitation days and clear days?
  2. Multiple linear regression: delay ~ precipitation + wind + visibility
     + carrier + origin, to isolate weather's effect from carrier/airport
     baseline differences (confounders).

Writes results to reports/statistical_findings.json and prints a
human-readable summary used to build reports/findings_memo.md.
"""

import os
import json
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.formula.api as smf

from sqlalchemy import create_engine

PGHOST = os.environ.get("PGHOST", "localhost")
PGPORT = os.environ.get("PGPORT", "5432")
PGDATABASE = os.environ.get("PGDATABASE", "flight_delay_analysis")
PGUSER = os.environ.get("PGUSER", "postgres")
PGPASSWORD = os.environ.get("PGPASSWORD", "postgres")
CONN_STR = f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")

QUERY = """
SELECT
    f.dep_delay_min,
    f.carrier,
    f.origin,
    f.sched_dep_hour,
    w.precip_in,
    w.wind_speed_mph,
    w.visib_mi,
    w.temp_f
FROM fact_flights f
JOIN dim_weather w
  ON f.origin = w.origin AND f.time_hour = w.time_hour
WHERE f.is_cancelled = false
  AND f.dep_delay_min IS NOT NULL
  AND f.dep_delay_min BETWEEN -60 AND 480   -- drop extreme outliers (data-entry-level delays)
"""


def load_analysis_frame(engine) -> pd.DataFrame:
    df = pd.read_sql(QUERY, engine)
    before = len(df)
    df = df.dropna(subset=["dep_delay_min", "precip_in", "wind_speed_mph", "visib_mi"])
    print(f"Analysis frame: {len(df):,} flights (dropped {before - len(df):,} with missing weather joins)")
    return df


def run_ttest(df: pd.DataFrame) -> dict:
    wet = df.loc[df["precip_in"] > 0, "dep_delay_min"]
    dry = df.loc[df["precip_in"] == 0, "dep_delay_min"]

    t_stat, p_val = stats.ttest_ind(wet, dry, equal_var=False)  # Welch's t-test

    # 95% CI on the mean difference
    diff = wet.mean() - dry.mean()
    se = np.sqrt(wet.var(ddof=1) / len(wet) + dry.var(ddof=1) / len(dry))
    ci_low, ci_high = diff - 1.96 * se, diff + 1.96 * se

    result = {
        "n_precip_days_flights": int(len(wet)),
        "n_clear_days_flights": int(len(dry)),
        "mean_delay_precip": round(float(wet.mean()), 2),
        "mean_delay_clear": round(float(dry.mean()), 2),
        "mean_difference_minutes": round(float(diff), 2),
        "ci_95_low": round(float(ci_low), 2),
        "ci_95_high": round(float(ci_high), 2),
        "t_statistic": round(float(t_stat), 3),
        "p_value": float(p_val),
        "significant_at_05": bool(p_val < 0.05),
    }
    return result


def run_regression(df: pd.DataFrame) -> dict:
    model_df = df.copy()
    # Reference levels: most common carrier and origin, so coefficients
    # read as "vs. the busiest baseline" rather than an arbitrary alphabetical pick
    top_carrier = model_df["carrier"].value_counts().idxmax()
    top_origin = model_df["origin"].value_counts().idxmax()
    model_df["carrier"] = pd.Categorical(
        model_df["carrier"],
        categories=[top_carrier] + [c for c in model_df["carrier"].unique() if c != top_carrier]
    )
    model_df["origin"] = pd.Categorical(
        model_df["origin"],
        categories=[top_origin] + [c for c in model_df["origin"].unique() if c != top_origin]
    )

    formula = "dep_delay_min ~ precip_in + wind_speed_mph + visib_mi + C(carrier) + C(origin)"
    model = smf.ols(formula, data=model_df).fit()

    coef = model.params
    pvals = model.pvalues
    conf = model.conf_int()

    weather_terms = ["precip_in", "wind_speed_mph", "visib_mi"]
    weather_effects = {}
    for term in weather_terms:
        weather_effects[term] = {
            "coefficient": round(float(coef[term]), 3),
            "p_value": float(pvals[term]),
            "ci_95_low": round(float(conf.loc[term, 0]), 3),
            "ci_95_high": round(float(conf.loc[term, 1]), 3),
        }

    return {
        "r_squared": round(float(model.rsquared), 4),
        "n_obs": int(model.nobs),
        "reference_carrier": top_carrier,
        "reference_origin": top_origin,
        "weather_effects": weather_effects,
        "interpretation": (
            f"Holding carrier and origin airport constant, each additional inch of "
            f"hourly precipitation is associated with a "
            f"{coef['precip_in']:.1f}-minute change in average departure delay "
            f"(p={pvals['precip_in']:.4f})."
        ),
        "full_summary": model.summary().as_text(),
    }


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    engine = create_engine(CONN_STR)
    df = load_analysis_frame(engine)

    print("\nRunning Welch's t-test (precipitation vs. clear)...")
    ttest_result = run_ttest(df)
    for k, v in ttest_result.items():
        print(f"  {k}: {v}")

    print("\nRunning multiple linear regression...")
    regression_result = run_regression(df)
    print(f"  R-squared: {regression_result['r_squared']}")
    print(f"  N: {regression_result['n_obs']:,}")
    print(f"  {regression_result['interpretation']}")

    output = {
        "dataset": "nycflights13 (real US DOT + NOAA data, 2013, NYC origin airports)",
        "n_flights_analyzed": len(df),
        "ttest_precip_vs_clear": ttest_result,
        "regression": {k: v for k, v in regression_result.items() if k != "full_summary"},
    }
    out_path = os.path.join(REPORTS_DIR, "statistical_findings.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")

    with open(os.path.join(REPORTS_DIR, "regression_summary.txt"), "w") as f:
        f.write(regression_result["full_summary"])


if __name__ == "__main__":
    main()
