-- schema.sql — Star schema for flight delay + weather analysis
-- Fact table: fact_flights (one row per real flight, NYC origin airports, 2013)
-- Dimensions: dim_date, dim_airport, dim_airline, dim_plane, dim_weather

DROP TABLE IF EXISTS fact_flights CASCADE;
DROP TABLE IF EXISTS dim_weather CASCADE;
DROP TABLE IF EXISTS dim_plane CASCADE;
DROP TABLE IF EXISTS dim_airline CASCADE;
DROP TABLE IF EXISTS dim_airport CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

CREATE TABLE dim_date (
    date_key        DATE PRIMARY KEY,
    year            INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    day             INTEGER NOT NULL,
    day_of_week     INTEGER NOT NULL,      -- 0=Monday .. 6=Sunday
    day_name        TEXT NOT NULL,
    is_weekend      BOOLEAN NOT NULL
);

CREATE TABLE dim_airport (
    faa             TEXT PRIMARY KEY,
    name            TEXT,
    lat             DOUBLE PRECISION,
    lon             DOUBLE PRECISION,
    alt             INTEGER,
    tz_offset       INTEGER,
    dst             TEXT,
    tzone           TEXT
);

CREATE TABLE dim_airline (
    carrier         TEXT PRIMARY KEY,
    airline_name    TEXT
);

CREATE TABLE dim_plane (
    tailnum         TEXT PRIMARY KEY,
    manufacture_year INTEGER,
    plane_type      TEXT,
    manufacturer    TEXT,
    model           TEXT,
    engines         INTEGER,
    seats           INTEGER,
    speed           DOUBLE PRECISION,
    engine          TEXT
);

CREATE TABLE dim_weather (
    weather_id      BIGSERIAL PRIMARY KEY,
    origin          TEXT NOT NULL REFERENCES dim_airport(faa),
    date_key        DATE NOT NULL,
    hour            INTEGER NOT NULL,
    temp_f          DOUBLE PRECISION,
    dewp_f          DOUBLE PRECISION,
    humid_pct       DOUBLE PRECISION,
    wind_dir        DOUBLE PRECISION,
    wind_speed_mph  DOUBLE PRECISION,
    precip_in       DOUBLE PRECISION,
    pressure_mb     DOUBLE PRECISION,
    visib_mi        DOUBLE PRECISION,
    time_hour       TIMESTAMP NOT NULL,
    UNIQUE (origin, time_hour)
);
CREATE INDEX idx_weather_origin_time ON dim_weather(origin, time_hour);

CREATE TABLE fact_flights (
    flight_id           BIGSERIAL PRIMARY KEY,
    date_key            DATE NOT NULL REFERENCES dim_date(date_key),
    carrier             TEXT NOT NULL REFERENCES dim_airline(carrier),
    flight_num          INTEGER NOT NULL,
    tailnum             TEXT REFERENCES dim_plane(tailnum),
    origin              TEXT NOT NULL REFERENCES dim_airport(faa),
    dest                TEXT NOT NULL,
    sched_dep_time      INTEGER NOT NULL,    -- HHMM local
    dep_time            INTEGER,             -- NULL if cancelled
    dep_delay_min       DOUBLE PRECISION,
    sched_arr_time      INTEGER NOT NULL,
    arr_time            INTEGER,
    arr_delay_min       DOUBLE PRECISION,
    air_time_min        DOUBLE PRECISION,
    distance_mi         DOUBLE PRECISION,
    sched_dep_hour      INTEGER NOT NULL,
    time_hour           TIMESTAMP NOT NULL,  -- scheduled departure hour, joins to dim_weather
    is_cancelled        BOOLEAN NOT NULL
);
CREATE INDEX idx_flights_origin_time ON fact_flights(origin, time_hour);
CREATE INDEX idx_flights_carrier ON fact_flights(carrier);
CREATE INDEX idx_flights_date ON fact_flights(date_key);
