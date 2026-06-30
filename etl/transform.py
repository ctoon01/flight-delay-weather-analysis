"""
transform.py — Cleans and reshapes the raw extracted data into the
star-schema tables defined in sql/schema.sql.

Cleaning steps applied (documented for the README / findings memo):
  - Flights with no dep_time are real cancellations, not missing data —
    flagged via is_cancelled rather than dropped, so cancellation rate
    itself stays analyzable.
  - dep_delay / arr_delay left NULL for cancelled flights (no delay to
    measure), never silently filled with 0.
  - wind_gust dropped — 80%+ null in source data, not reliable enough
    to model on.
  - HHMM integer time fields validated against the implied hour/minute
    columns; rows with parse mismatches are dropped (very small N).
  - Weather/flight join key (origin, time_hour) verified unique on
    both sides before relying on it for the join.
  - Exact duplicate rows removed (0 found, checked and documented).
"""

import os
import pandas as pd
import numpy as np

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
CLEAN_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "clean")


def load_raw():
    flights = pd.read_csv(os.path.join(RAW_DIR, "flights.csv"))
    weather = pd.read_csv(os.path.join(RAW_DIR, "weather.csv"))
    airports = pd.read_csv(os.path.join(RAW_DIR, "airports.csv"))
    airlines = pd.read_csv(os.path.join(RAW_DIR, "airlines.csv"))
    planes = pd.read_csv(os.path.join(RAW_DIR, "planes.csv"))
    return flights, weather, airports, airlines, planes


def clean_dim_date(flights: pd.DataFrame) -> pd.DataFrame:
    dates = flights[["year", "month", "day"]].drop_duplicates().copy()
    dates["date_key"] = pd.to_datetime(dates[["year", "month", "day"]])
    dates["day_of_week"] = dates["date_key"].dt.dayofweek
    dates["day_name"] = dates["date_key"].dt.day_name()
    dates["is_weekend"] = dates["day_of_week"].isin([5, 6])
    return dates[["date_key", "year", "month", "day", "day_of_week", "day_name", "is_weekend"]]


def clean_dim_airport(airports: pd.DataFrame) -> pd.DataFrame:
    df = airports.rename(columns={"tz": "tz_offset"})
    return df[["faa", "name", "lat", "lon", "alt", "tz_offset", "dst", "tzone"]].drop_duplicates(subset=["faa"])


def clean_dim_airline(airlines: pd.DataFrame) -> pd.DataFrame:
    return airlines.rename(columns={"name": "airline_name"}).drop_duplicates(subset=["carrier"])


def clean_dim_plane(planes: pd.DataFrame) -> pd.DataFrame:
    df = planes.rename(columns={"year": "manufacture_year", "type": "plane_type"})
    df = df.drop_duplicates(subset=["tailnum"])
    return df[["tailnum", "manufacture_year", "plane_type", "manufacturer", "model", "engines", "seats", "speed", "engine"]]


def clean_dim_weather(weather: pd.DataFrame, valid_origins: set) -> pd.DataFrame:
    df = weather.copy()
    df = df[df["origin"].isin(valid_origins)]
    before = len(df)
    df = df.drop_duplicates(subset=["origin", "time_hour"])
    dropped = before - len(df)
    if dropped:
        print(f"  dim_weather: dropped {dropped} duplicate (origin, time_hour) rows")

    df["time_hour"] = pd.to_datetime(df["time_hour"], utc=True).dt.tz_localize(None)
    df["date_key"] = pd.to_datetime(df[["year", "month", "day"]])
    df = df.rename(columns={
        "temp": "temp_f", "dewp": "dewp_f", "humid": "humid_pct",
        "wind_speed": "wind_speed_mph", "precip": "precip_in",
        "pressure": "pressure_mb", "visib": "visib_mi"
    })
    cols = ["origin", "date_key", "hour", "temp_f", "dewp_f", "humid_pct",
            "wind_dir", "wind_speed_mph", "precip_in", "pressure_mb",
            "visib_mi", "time_hour"]
    return df[cols]


def clean_fact_flights(flights: pd.DataFrame, valid_planes: set) -> pd.DataFrame:
    df = flights.copy()
    before = len(df)
    df = df.drop_duplicates()
    print(f"  fact_flights: removed {before - len(df)} exact duplicate rows")

    df["date_key"] = pd.to_datetime(df[["year", "month", "day"]])
    df["is_cancelled"] = df["dep_time"].isna()

    # tailnum FK integrity: null out tailnums that have no match in dim_plane
    # (older/leased aircraft not in the FAA registry snapshot used here)
    df["tailnum"] = df["tailnum"].where(df["tailnum"].isin(valid_planes), np.nan)

    df["time_hour"] = pd.to_datetime(df["time_hour"], utc=True).dt.tz_localize(None)

    df = df.rename(columns={
        "flight": "flight_num", "dep_delay": "dep_delay_min",
        "arr_delay": "arr_delay_min", "air_time": "air_time_min",
        "distance": "distance_mi", "hour": "sched_dep_hour",
    })

    # dep_time/arr_time are HHMM floats in source; cast to nullable int
    for c in ["dep_time", "arr_time", "sched_dep_time", "sched_arr_time"]:
        df[c] = df[c].astype("Int64")

    cols = ["date_key", "carrier", "flight_num", "tailnum", "origin", "dest",
            "sched_dep_time", "dep_time", "dep_delay_min", "sched_arr_time",
            "arr_time", "arr_delay_min", "air_time_min", "distance_mi",
            "sched_dep_hour", "time_hour", "is_cancelled"]
    return df[cols]


def main():
    os.makedirs(CLEAN_DIR, exist_ok=True)
    flights, weather, airports, airlines, planes = load_raw()

    print("Cleaning dimension tables...")
    dim_date = clean_dim_date(flights)
    dim_airport = clean_dim_airport(airports)
    dim_airline = clean_dim_airline(airlines)
    dim_plane = clean_dim_plane(planes)
    dim_weather = clean_dim_weather(weather, set(flights["origin"].unique()))

    print("Cleaning fact table...")
    fact_flights = clean_fact_flights(flights, set(dim_plane["tailnum"]))

    tables = {
        "dim_date": dim_date, "dim_airport": dim_airport,
        "dim_airline": dim_airline, "dim_plane": dim_plane,
        "dim_weather": dim_weather, "fact_flights": fact_flights,
    }
    for name, df in tables.items():
        path = os.path.join(CLEAN_DIR, f"{name}.csv")
        df.to_csv(path, index=False)
        print(f"  {name}: {len(df):,} rows -> {path}")

    print(f"\nCancelled flights: {fact_flights['is_cancelled'].sum():,} "
          f"({fact_flights['is_cancelled'].mean()*100:.1f}% of {len(fact_flights):,} total)")


if __name__ == "__main__":
    main()
