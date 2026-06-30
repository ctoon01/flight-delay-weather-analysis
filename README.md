# ✈️ Flight Delay & Weather Impact Analysis

End-to-end analytics project using **real flight and weather data** to build a complete analytics pipeline:

**Real Data → Python ETL → PostgreSQL Star Schema → SQL Analysis → Statistical Inference → Interactive Streamlit Dashboard**

## 🚀 Live Dashboard

**https://flight-delay-weather-analysis-jjzhyugpxwskrndgsgzxyy.streamlit.app/**

---

![Python](https://img.shields.io/badge/Python-3.12-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red)
![SciPy](https://img.shields.io/badge/SciPy-Statistics-654FF0)
![statsmodels](https://img.shields.io/badge/statsmodels-Regression-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B)
![Plotly](https://img.shields.io/badge/Plotly-Visualization-3F4F75)
![GitHub%20Actions](https://img.shields.io/badge/CI-GitHub%20Actions-success)
![License](https://img.shields.io/badge/License-MIT-green)

---

# 📸 Dashboard Preview


![Dashboard](images/dashboard.png)

---

# 📋 At a Glance

| Metric | Value |
|---------|------:|
| Flights Analyzed | **336,776** |
| Airports | **3 (JFK, LGA, EWR)** |
| Weather Observations | **Hourly NOAA Data** |
| Fact Table | **336,776 Rows** |
| Dimension Tables | **5** |
| Database | **PostgreSQL** |
| Dashboard | **Streamlit + Plotly** |

---

## 📄 Findings Memo

The primary analyst deliverable written for a non-technical audience:

➡️ **[reports/findings_memo.md](reports/findings_memo.md)**

---

# Project Overview

This project intentionally uses **real, publicly available data** rather than simulated data.

It analyzes **336,776 real commercial flights** departing New York City airports (JFK, LGA, and EWR) during 2013 and joins them with real hourly weather observations.

The data comes from the **nycflights13** dataset (CC0/Public Domain), originally compiled from:

- US Department of Transportation Bureau of Transportation Statistics
- National Oceanic and Atmospheric Administration (NOAA)

Unlike another project in my portfolio that uses synthetic business data, this project demonstrates handling **real-world data challenges**, including:

- Missing values
- Cancelled flights
- Join-key mismatches
- Statistical inference
- Reproducible ETL pipelines

---

# Executive Summary

Analysis of **336,776 flights** found a statistically significant relationship between precipitation and departure delays.

Flights departing during measurable precipitation experienced delays averaging **19.4 minutes longer** than flights departing under dry conditions.

Multiple linear regression confirmed precipitation as a statistically significant predictor of departure delay even after controlling for airline and airport effects.

Although weather contributes meaningfully to delays, the relatively low model R² demonstrates that operational factors beyond weather explain most of the variation in departure performance.

---

# Skills Demonstrated

- Python
- PostgreSQL
- SQL
- ETL Development
- Star Schema Design
- SQL Window Functions
- Statistical Analysis
- Welch's t-test
- Multiple Linear Regression
- Data Visualization
- Business Intelligence
- GitHub Actions
- CI/CD
- Streamlit
- Plotly

---

# What this project demonstrates

- Star-schema data modeling using one fact table and five dimensions
- Python ETL pipeline with documented cleaning decisions
- SQL joins, CTEs, window functions, and analytical queries
- Statistical inference using Welch's t-test and multiple linear regression
- Reproducible analytics pipeline executed with a single command
- Interactive dashboard built using Streamlit and Plotly
- Portable deployment using SQLite fallback when PostgreSQL is unavailable

---

# Architecture

```text
Raw Data (GitHub-hosted CC0)

        │
        ▼

etl/extract.py

        │
        ▼

Raw CSV Files

        │
        ▼

etl/transform.py

Cleaning
Validation
Foreign Key Checks
Star Schema Preparation

        │
        ▼

tests/test_etl.py

Data Quality Validation

        │
        ▼

etl/load.py

        │
        ▼

PostgreSQL Star Schema

        │
        ▼

analysis/statistical_analysis.py

        │
        ▼

Reports

JSON Results

Executive Memo

        │
        ▼

Streamlit Dashboard
```

---

# Schema

**Fact Table**

- fact_flights

**Dimension Tables**

- dim_date
- dim_airport
- dim_airline
- dim_plane
- dim_weather

Flights join to weather using:

```
(origin, time_hour)
```

Complete schema:

```
sql/schema.sql
```

---

# Business Questions Answered

- Does precipitation significantly increase departure delays?
- Which airports experience the greatest weather-related disruption?
- Can weather predict departure delays?
- How much variation in delays can weather explain?
- Which operational factors appear more influential than weather?

---

# Key Findings

- Flights during measurable precipitation averaged **30.9 minutes** of departure delay.
- Flights during dry conditions averaged **11.4 minutes**.
- Difference: **19.4 minutes** (95% CI 18.6–20.2 minutes, p < 0.001).
- Regression estimated an **85-minute increase** in delay per additional inch of hourly precipitation after controlling for airline and airport.
- Model R² = **0.03**, demonstrating weather has a statistically significant but limited explanatory effect.

Complete analysis:

**reports/findings_memo.md**

---

# Running Locally

```bash
git clone https://github.com/ctoon01/flight-delay-weather-analysis.git

cd flight-delay-weather-analysis

pip install -r requirements.txt

bash run_pipeline.sh

streamlit run dashboard/app.py
```

---

# Running Without PostgreSQL

The dashboard automatically falls back to a bundled SQLite database if PostgreSQL is unavailable.

This allows deployment on Streamlit Community Cloud without requiring a database server.

To connect to PostgreSQL instead:

```bash
export DATABASE_URL="postgresql+psycopg2://user:password@host:5432/flight_delay_analysis"
```

---

# Cloud Migration

The project is warehouse-agnostic and can be migrated to:

- Google BigQuery
- Snowflake
- PostgreSQL Cloud

Only the SQLAlchemy connection string must change.

---

# Project Structure

```text
etl/
analysis/
dashboard/
sql/
reports/
tests/
.github/workflows/

run_pipeline.sh
README.md
requirements.txt
```

---

# Technology Stack

- Python
- PostgreSQL
- SQLAlchemy
- Pandas
- SciPy
- statsmodels
- Plotly
- Streamlit
- GitHub Actions
- Git
- SQL

---

# Resume Highlights

This project demonstrates experience with:

- Building reproducible ETL pipelines
- Designing PostgreSQL star schemas
- Writing analytical SQL with joins, CTEs, and window functions
- Performing statistical inference using SciPy and statsmodels
- Building interactive dashboards with Streamlit and Plotly
- Automating workflows with GitHub Actions
- Communicating findings to non-technical stakeholders

---

# Data Attribution

Flight and weather data:

https://github.com/tidyverse/nycflights13

Compiled from:

- US DOT Bureau of Transportation Statistics
- NOAA

Dataset License: CC0 / Public Domain

Project Code License: MIT

---

# Author

## Christopher Toon

GitHub:

https://github.com/ctoon01
