# Flight Delay & Weather Impact Analysis

End-to-end analytics project: real flight and weather data → PostgreSQL
star schema → statistical inference (t-test + regression) → interactive
Streamlit dashboard.

**[Findings memo](reports/findings_memo.md)** — the actual analyst deliverable, written for a non-technical reader.

## Why this project, and what's real

This project intentionally uses **real, publicly sourced data** —
336,776 actual flights departing NYC airports (JFK, LGA, EWR) in 2013,
joined with real hourly weather observations at each airport. The
data comes from the [`nycflights13`](https://github.com/tidyverse/nycflights13)
dataset (CC0 / public domain), originally compiled from the **US DOT
Bureau of Transportation Statistics** (flight records) and **NOAA**
(weather records).

I'm explicit about this because [another project in my portfolio](https://github.com/ctoon01/cannabis-retail-intelligence-platform)
uses simulated business data — that project showcases schema design
and ETL on a clean synthetic dataset; this one showcases handling
real-world data (real nulls, real cancellations, real join-key
mismatches) and real statistical inference.

## What this project demonstrates

- **Star-schema data modeling** — one fact table, five dimension tables, proper FK constraints.
- **ETL with documented, defensible cleaning decisions** — not just `dropna()`. See `etl/transform.py` docstring for the full list (cancelled flights flagged not dropped, no silent zero-fills, FK integrity checks, etc).
- **SQL depth** — multi-table joins, CTEs, and window functions (`RANK()`, rolling-average frames) — see `sql/analysis_queries.sql`.
- **Real statistical inference** — Welch's t-test and multiple linear regression with confounder controls, confidence intervals, and disclosed model limitations (R²) — not just descriptive averages.
- **Reproducible pipeline** — `run_pipeline.sh` runs extract → transform → test → load → analyze in one command, and the same steps run in CI on every push.
- **Deployable dashboard** — Streamlit + Plotly, with a portable SQLite fallback so it runs standalone with no database server required.

## Architecture

```
 raw data (GitHub-hosted CC0 source)
        │  etl/extract.py
        ▼
 data/raw/*.rda  →  data/raw/*.csv
        │  etl/transform.py  (cleaning, FK checks, reshaping)
        ▼
 data/clean/*.csv  →  tests/test_etl.py  (data quality gate)
        │  etl/load.py
        ▼
 PostgreSQL star schema (sql/schema.sql)
        │  analysis/statistical_analysis.py
        ▼
 reports/statistical_findings.json + findings_memo.md
        │
        ▼
 dashboard/app.py  (Streamlit + Plotly)
```

## Schema

**Fact table:** `fact_flights` — one row per real flight (336,776 rows)
**Dimensions:** `dim_date`, `dim_airport`, `dim_airline`, `dim_plane`, `dim_weather`

Flights join to weather on `(origin, time_hour)`. Full DDL in [`sql/schema.sql`](sql/schema.sql).

## Key findings

- Flights during hours with measurable precipitation were delayed an
  average of **30.9 minutes**, vs. **11.4 minutes** on clear hours — a
  **19.4-minute difference** (95% CI: 18.6–20.2 min, p < 0.001, n=326,848).
- In a regression controlling for carrier and origin airport, each
  additional inch of hourly precipitation is associated with an
  **85-minute increase** in average departure delay (p < 0.001).
- Model R² is low (0.03) — disclosed deliberately. Weather has a real,
  statistically robust effect, but individual flight delay has far
  more variance than weather alone explains.

Full writeup, caveats, and methodology: [`reports/findings_memo.md`](reports/findings_memo.md).

## Running it locally

```bash
# 1. Clone and install
git clone https://github.com/<your-username>/flight-delay-weather-analysis.git
cd flight-delay-weather-analysis
pip install -r requirements.txt

# 2. Start PostgreSQL (or point PG* env vars at an existing instance)
#    Defaults: localhost:5432, db=flight_delay_analysis, user/pass=postgres/postgres

# 3. Run the full pipeline
bash run_pipeline.sh

# 4. Launch the dashboard
streamlit run dashboard/app.py
```

## Running the dashboard without PostgreSQL

The dashboard falls back to a bundled SQLite snapshot
(`data/flight_delay_analysis.db`, built from the same pipeline) if no
`DATABASE_URL` environment variable is set. This is what makes it
deployable on Streamlit Community Cloud with zero database setup:

```bash
streamlit run dashboard/app.py    # uses bundled SQLite automatically
```

To point it at a live Postgres instance instead, set:
```bash
export DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/flight_delay_analysis"
```

## Migrating to a cloud warehouse (BigQuery / Snowflake)

The schema and load step are warehouse-agnostic SQL — to move off
local Postgres onto a free-tier cloud warehouse:
1. Create a free BigQuery sandbox or Snowflake trial account.
2. Adjust `etl/load.py`'s connection string to the warehouse's
   SQLAlchemy dialect (`bigquery://` or `snowflake://`).
3. Re-run `python etl/load.py` — the schema DDL and load logic are
   otherwise unchanged.

This step needs your own cloud account credentials, so it's left as
a configuration change rather than baked into the pipeline.

## Project structure

```
etl/extract.py          Pulls real source data (GitHub-hosted CC0)
etl/transform.py         Cleans and reshapes into star schema
etl/load.py               Loads into PostgreSQL
sql/schema.sql             Star schema DDL
sql/analysis_queries.sql    Reference SQL: joins, CTEs, window functions
analysis/statistical_analysis.py   t-test + regression
dashboard/app.py            Streamlit dashboard
reports/findings_memo.md     Analyst writeup
reports/statistical_findings.json  Machine-readable results
tests/test_etl.py             Data quality tests (run in CI)
run_pipeline.sh                 One-command pipeline runner
.github/workflows/ci.yml         CI: runs the full pipeline + tests on every push
```

## Tech stack

Python · PostgreSQL · SQLAlchemy · Pandas · SciPy · statsmodels · Streamlit · Plotly · GitHub Actions

## Data attribution

Flight and weather data: [`nycflights13`](https://github.com/tidyverse/nycflights13)
(CC0), compiled from the US DOT Bureau of Transportation Statistics
and NOAA. This project's code is MIT licensed — see [`LICENSE`](LICENSE).

## Author

Christopher Toon — [github.com/ctoon01](https://github.com/ctoon01)
