"""
test_etl.py — Basic data-quality tests run in CI after the ETL pipeline.
Not exhaustive; covers the checks that would actually catch a broken
pipeline (row counts, null/FK integrity, no silent data loss).
"""

import os
import sys
import pandas as pd
import pytest

CLEAN_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "clean")


def _load(name):
    return pd.read_csv(os.path.join(CLEAN_DIR, f"{name}.csv"))


def test_fact_flights_row_count():
    df = _load("fact_flights")
    assert len(df) == 336776, f"Expected 336,776 flights, got {len(df)}"


def test_fact_flights_no_exact_duplicates():
    df = _load("fact_flights")
    assert df.duplicated().sum() == 0


def test_cancelled_flights_have_no_delay():
    df = _load("fact_flights")
    cancelled = df[df["is_cancelled"] == True]
    assert cancelled["dep_delay_min"].isna().all(), "Cancelled flights should have null delay, not 0"


def test_origin_values_valid():
    df = _load("fact_flights")
    assert set(df["origin"].unique()) == {"EWR", "JFK", "LGA"}


def test_weather_join_key_is_unique():
    df = _load("dim_weather")
    assert df.duplicated(subset=["origin", "time_hour"]).sum() == 0, \
        "Weather join key must be unique or the flight join will fan out"


def test_dim_date_covers_full_year():
    df = _load("dim_date")
    assert len(df) == 365


def test_no_negative_distances():
    df = _load("fact_flights")
    assert (df["distance_mi"].dropna() > 0).all()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
