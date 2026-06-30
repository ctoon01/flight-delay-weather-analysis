"""
load.py — Loads cleaned CSVs into PostgreSQL using the star schema
defined in sql/schema.sql.

Connection config is read from environment variables so the same
script works locally and in CI:
  PGHOST (default localhost), PGPORT (5432), PGDATABASE
  (flight_delay_analysis), PGUSER (postgres), PGPASSWORD (postgres)
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

CLEAN_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "clean")
SCHEMA_SQL = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")

PGHOST = os.environ.get("PGHOST", "localhost")
PGPORT = os.environ.get("PGPORT", "5432")
PGDATABASE = os.environ.get("PGDATABASE", "flight_delay_analysis")
PGUSER = os.environ.get("PGUSER", "postgres")
PGPASSWORD = os.environ.get("PGPASSWORD", "postgres")

CONN_STR = f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"

# Order matters: dimensions before fact (FK constraints)
LOAD_ORDER = ["dim_date", "dim_airport", "dim_airline", "dim_plane", "dim_weather", "fact_flights"]


def run_schema(engine):
    with open(SCHEMA_SQL) as f:
        ddl = f.read()
    raw_conn = engine.raw_connection()
    try:
        cur = raw_conn.cursor()
        cur.execute(ddl)
        raw_conn.commit()
        cur.close()
    finally:
        raw_conn.close()
    print("Schema created.")


def load_table(engine, name: str):
    path = os.path.join(CLEAN_DIR, f"{name}.csv")
    df = pd.read_csv(path)
    # Parse date/timestamp columns explicitly so they land as proper SQL types
    for col in df.columns:
        if col in ("date_key", "time_hour"):
            df[col] = pd.to_datetime(df[col])
    df.to_sql(name, engine, if_exists="append", index=False, method="multi", chunksize=5000)
    print(f"  loaded {name}: {len(df):,} rows")


def main():
    engine = create_engine(CONN_STR)
    print(f"Connecting to {PGDATABASE} @ {PGHOST}:{PGPORT} ...")
    run_schema(engine)
    print("Loading tables...")
    for name in LOAD_ORDER:
        load_table(engine, name)
    print("\nLoad complete.")


if __name__ == "__main__":
    main()
