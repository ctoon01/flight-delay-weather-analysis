#!/usr/bin/env bash
# run_pipeline.sh — runs the full pipeline end to end.
# Requires a running PostgreSQL instance reachable with the PG* env vars
# (defaults: localhost:5432, db flight_delay_analysis, user/pass postgres/postgres).
set -euo pipefail

echo "== 1/5 Extract (pulling real flight + weather data) =="
python3 etl/extract.py

echo "== 2/5 Transform (cleaning + star schema reshape) =="
python3 etl/transform.py

echo "== 3/5 Data quality tests =="
pytest tests/ -v

echo "== 4/5 Load (PostgreSQL) =="
python3 etl/load.py

echo "== 5/5 Statistical analysis =="
python3 analysis/statistical_analysis.py

echo
echo "Pipeline complete. Launch the dashboard with:"
echo "  streamlit run dashboard/app.py"
