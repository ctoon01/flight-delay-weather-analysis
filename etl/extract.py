"""
extract.py — Pulls real, public flight and weather data.

Source: tidyverse/nycflights13 (CC0 / public domain)
Underlying data originates from the US DOT Bureau of Transportation
Statistics (flight records) and NOAA (weather records), repackaged
by the nycflights13 R package maintainers for reproducible analysis.

Why this dataset: it's the standard, widely-cited real-world dataset
used in data analytics coursework (R for Data Science, etc.) for
exactly this kind of join-and-analyze project — 336K+ real flights
departing NYC airports (JFK, LGA, EWR) in 2013, with hourly weather
observations at each origin airport.
"""

import os
import urllib.request
import pyreadr
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
BASE_URL = "https://raw.githubusercontent.com/tidyverse/nycflights13/main/data"

FILES = ["flights", "weather", "airports", "airlines", "planes"]


def download_rda(name: str) -> str:
    os.makedirs(RAW_DIR, exist_ok=True)
    dest = os.path.join(RAW_DIR, f"{name}.rda")
    url = f"{BASE_URL}/{name}.rda"
    print(f"Downloading {url} ...")
    urllib.request.urlretrieve(url, dest)
    return dest


def rda_to_csv(rda_path: str, name: str) -> pd.DataFrame:
    result = pyreadr.read_r(rda_path)
    key = list(result.keys())[0]
    df = result[key]
    csv_path = os.path.join(RAW_DIR, f"{name}.csv")
    df.to_csv(csv_path, index=False)
    print(f"  -> {csv_path}  ({df.shape[0]:,} rows x {df.shape[1]} cols)")
    return df


def main():
    for name in FILES:
        rda_path = download_rda(name)
        rda_to_csv(rda_path, name)
    print("\nExtract complete. Raw CSVs written to data/raw/")


if __name__ == "__main__":
    main()
