-- analysis_queries.sql
-- Reference queries used by the dashboard and findings memo.
-- Demonstrates multi-table joins, CTEs, and window functions against
-- the star schema in schema.sql.

-- 1. Monthly average delay by origin airport
SELECT
    d.year, d.month,
    f.origin,
    COUNT(*) AS flights,
    ROUND(AVG(f.dep_delay_min)::numeric, 1) AS avg_dep_delay
FROM fact_flights f
JOIN dim_date d ON f.date_key = d.date_key
WHERE f.is_cancelled = false
GROUP BY d.year, d.month, f.origin
ORDER BY d.month, f.origin;

-- 2. Carrier performance ranked by average delay, with a CTE filtering
--    out low-volume carriers so the ranking isn't skewed by small N
WITH carrier_volume AS (
    SELECT carrier, COUNT(*) AS n_flights
    FROM fact_flights
    WHERE is_cancelled = false
    GROUP BY carrier
    HAVING COUNT(*) >= 1000
)
SELECT
    a.airline_name,
    cv.n_flights,
    ROUND(AVG(f.dep_delay_min)::numeric, 1) AS avg_dep_delay,
    ROUND(AVG(f.arr_delay_min)::numeric, 1) AS avg_arr_delay
FROM fact_flights f
JOIN carrier_volume cv ON f.carrier = cv.carrier
JOIN dim_airline a ON f.carrier = a.carrier
WHERE f.is_cancelled = false
GROUP BY a.airline_name, cv.n_flights
ORDER BY avg_dep_delay DESC;

-- 3. Weather-joined delay comparison: precipitation vs. clear hours
SELECT
    CASE WHEN w.precip_in > 0 THEN 'Precipitation' ELSE 'Clear' END AS condition,
    COUNT(*) AS flights,
    ROUND(AVG(f.dep_delay_min)::numeric, 1) AS avg_dep_delay,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.dep_delay_min)::numeric, 1) AS median_dep_delay
FROM fact_flights f
JOIN dim_weather w ON f.origin = w.origin AND f.time_hour = w.time_hour
WHERE f.is_cancelled = false AND f.dep_delay_min IS NOT NULL
GROUP BY condition;

-- 4. Window function: each flight's delay rank within its own route
--    (origin -> dest), to surface the worst-delay outlier per route
SELECT *
FROM (
    SELECT
        f.flight_id, f.origin, f.dest, f.carrier, f.date_key,
        f.dep_delay_min,
        RANK() OVER (
            PARTITION BY f.origin, f.dest
            ORDER BY f.dep_delay_min DESC
        ) AS delay_rank_in_route
    FROM fact_flights f
    WHERE f.is_cancelled = false AND f.dep_delay_min IS NOT NULL
) ranked
WHERE delay_rank_in_route = 1
ORDER BY dep_delay_min DESC
LIMIT 20;

-- 5. Running 7-day average departure delay per origin (window function,
--    frame-based) — smooths daily noise for the dashboard trend line
WITH daily AS (
    SELECT
        f.origin, f.date_key,
        AVG(f.dep_delay_min) AS avg_delay
    FROM fact_flights f
    WHERE f.is_cancelled = false AND f.dep_delay_min IS NOT NULL
    GROUP BY f.origin, f.date_key
)
SELECT
    origin, date_key, avg_delay,
    AVG(avg_delay) OVER (
        PARTITION BY origin
        ORDER BY date_key
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_7day_avg_delay
FROM daily
ORDER BY origin, date_key;
