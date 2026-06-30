"""
app.py — Flight Delay & Weather Impact Dashboard (Streamlit)

Data: 336,776 real flights departing NYC airports (JFK, LGA, EWR) in 2013,
sourced from the US DOT Bureau of Transportation Statistics, joined with
hourly NOAA weather observations. See README.md for full pipeline details.

Connects to PostgreSQL if DATABASE_URL is set (local/dev use); otherwise
falls back to the bundled SQLite snapshot in data/flight_delay_analysis.db
so the app runs standalone on Streamlit Community Cloud with no DB server.
"""

import os
import json
import sqlite3

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine

st.set_page_config(page_title="Flight Delay & Weather Impact", page_icon="\u2708\ufe0f", layout="wide")

BASE_DIR = os.path.dirname(__file__)
SQLITE_PATH = os.path.join(BASE_DIR, "..", "data", "flight_delay_analysis.db")
FINDINGS_PATH = os.path.join(BASE_DIR, "..", "reports", "statistical_findings.json")


@st.cache_resource
def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        engine = create_engine(database_url)
        return ("sqlalchemy", engine)
    conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
    return ("sqlite", conn)


def run_query(sql: str) -> pd.DataFrame:
    kind, handle = get_connection()
    if kind == "sqlalchemy":
        return pd.read_sql(sql, handle)
    return pd.read_sql(sql, handle)


@st.cache_data
def load_findings():
    if os.path.exists(FINDINGS_PATH):
        with open(FINDINGS_PATH) as f:
            return json.load(f)
    return None


@st.cache_data
def load_filter_options():
    origins = run_query("SELECT DISTINCT origin FROM fact_flights ORDER BY origin")["origin"].tolist()
    carriers = run_query(
        "SELECT a.carrier, a.airline_name FROM dim_airline a "
        "JOIN fact_flights f ON a.carrier = f.carrier "
        "GROUP BY a.carrier, a.airline_name ORDER BY airline_name"
    )
    return origins, carriers


def main():
    st.title("\u2708\ufe0f Flight Delay & Weather Impact Analysis")
    st.caption(
        "336,776 real flights departing NYC airports (JFK \u00b7 LGA \u00b7 EWR) in 2013 "
        "\u2014 source: US DOT Bureau of Transportation Statistics + NOAA, via the "
        "public nycflights13 dataset (CC0)."
    )

    origins, carriers_df = load_filter_options()

    with st.sidebar:
        st.header("Filters")
        sel_origins = st.multiselect("Origin airport", origins, default=origins)
        carrier_labels = ["All"] + carriers_df["airline_name"].tolist()
        sel_carrier_label = st.selectbox("Carrier", carrier_labels)
        month_range = st.slider("Month range (2013)", 1, 12, (1, 12))

    origin_filter = "'" + "','".join(sel_origins) + "'" if sel_origins else "''"
    carrier_clause = ""
    if sel_carrier_label != "All":
        carrier_code = carriers_df.loc[carriers_df["airline_name"] == sel_carrier_label, "carrier"].iloc[0]
        carrier_clause = f"AND f.carrier = '{carrier_code}'"

    where_clause = (
        f"WHERE f.origin IN ({origin_filter}) "
        f"AND d.month BETWEEN {month_range[0]} AND {month_range[1]} "
        f"{carrier_clause}"
    )

    kpi_sql = f"""
        SELECT
            COUNT(*) AS total_flights,
            SUM(CASE WHEN f.is_cancelled THEN 1 ELSE 0 END) AS cancelled,
            AVG(CASE WHEN f.is_cancelled = 0 THEN f.dep_delay_min END) AS avg_dep_delay,
            AVG(CASE WHEN f.is_cancelled = 0 AND f.dep_delay_min > 15 THEN 1.0 ELSE 0.0 END) AS pct_delayed_15
        FROM fact_flights f
        JOIN dim_date d ON f.date_key = d.date_key
        {where_clause}
    """
    kpis = run_query(kpi_sql).iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Flights", f"{int(kpis['total_flights']):,}")
    c2.metric("Cancellation Rate", f"{kpis['cancelled'] / kpis['total_flights'] * 100:.1f}%")
    c3.metric("Avg Departure Delay", f"{kpis['avg_dep_delay']:.1f} min")
    c4.metric("% Flights Delayed 15+ min", f"{kpis['pct_delayed_15'] * 100:.1f}%")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Monthly Average Departure Delay")
        monthly_sql = f"""
            SELECT d.month, f.origin,
                   AVG(f.dep_delay_min) AS avg_delay
            FROM fact_flights f
            JOIN dim_date d ON f.date_key = d.date_key
            {where_clause} AND f.is_cancelled = 0
            GROUP BY d.month, f.origin
            ORDER BY d.month
        """
        monthly = run_query(monthly_sql)
        fig = px.line(monthly, x="month", y="avg_delay", color="origin", markers=True,
                       labels={"avg_delay": "Avg Delay (min)", "month": "Month"})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Delay by Weather Condition")
        weather_sql = f"""
            SELECT
                CASE WHEN w.precip_in > 0 THEN 'Precipitation' ELSE 'Clear' END AS condition,
                AVG(f.dep_delay_min) AS avg_delay,
                COUNT(*) AS flights
            FROM fact_flights f
            JOIN dim_weather w ON f.origin = w.origin AND f.time_hour = w.time_hour
            JOIN dim_date d ON f.date_key = d.date_key
            {where_clause} AND f.is_cancelled = 0 AND f.dep_delay_min IS NOT NULL
            GROUP BY condition
        """
        weather = run_query(weather_sql)
        fig2 = px.bar(weather, x="condition", y="avg_delay", color="condition",
                       text_auto=".1f", labels={"avg_delay": "Avg Delay (min)"})
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Top Carriers by Avg Departure Delay")
        carrier_sql = f"""
            SELECT a.airline_name, AVG(f.dep_delay_min) AS avg_delay, COUNT(*) AS flights
            FROM fact_flights f
            JOIN dim_airline a ON f.carrier = a.carrier
            JOIN dim_date d ON f.date_key = d.date_key
            {where_clause} AND f.is_cancelled = 0
            GROUP BY a.airline_name
            HAVING COUNT(*) >= 200
            ORDER BY avg_delay DESC
        """
        carrier_perf = run_query(carrier_sql)
        fig3 = px.bar(carrier_perf, x="avg_delay", y="airline_name", orientation="h",
                       labels={"avg_delay": "Avg Delay (min)", "airline_name": ""})
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("Departure Delay Distribution")
        dist_sql = f"""
            SELECT f.dep_delay_min
            FROM fact_flights f
            JOIN dim_date d ON f.date_key = d.date_key
            {where_clause} AND f.is_cancelled = 0 AND f.dep_delay_min BETWEEN -60 AND 180
        """
        dist = run_query(dist_sql)
        fig4 = px.histogram(dist, x="dep_delay_min", nbins=60,
                             labels={"dep_delay_min": "Departure Delay (min)"})
        fig4.add_vline(x=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig4, use_container_width=True)

    st.divider()
    st.subheader("\U0001F4CA Statistical Findings")

    findings = load_findings()
    if findings:
        t = findings["ttest_precip_vs_clear"]
        r = findings["regression"]

        fc1, fc2 = st.columns(2)
        with fc1:
            st.markdown("**Welch's two-sample t-test \u2014 precipitation vs. clear hours**")
            st.markdown(
                f"- Mean delay on precipitation hours: **{t['mean_delay_precip']} min** "
                f"(n={t['n_precip_days_flights']:,})\n"
                f"- Mean delay on clear hours: **{t['mean_delay_clear']} min** "
                f"(n={t['n_clear_days_flights']:,})\n"
                f"- Difference: **{t['mean_difference_minutes']} min** "
                f"(95% CI: {t['ci_95_low']} to {t['ci_95_high']})\n"
                f"- p-value: **{'< 0.001' if t['p_value'] < 0.001 else round(t['p_value'], 4)}** "
                f"({'statistically significant' if t['significant_at_05'] else 'not significant'} at \u03b1=0.05)"
            )
        with fc2:
            st.markdown("**Multiple regression** \u2014 `delay ~ precip + wind + visibility + carrier + origin`")
            we = r["weather_effects"]
            st.markdown(
                f"- Precipitation (in/hr): **{we['precip_in']['coefficient']:+.1f} min** per unit "
                f"(p={'< 0.001' if we['precip_in']['p_value'] < 0.001 else round(we['precip_in']['p_value'], 4)})\n"
                f"- Wind speed (mph): **{we['wind_speed_mph']['coefficient']:+.2f} min** per mph\n"
                f"- Visibility (mi): **{we['visib_mi']['coefficient']:+.2f} min** per mile\n"
                f"- Model R\u00b2: **{r['r_squared']}** (n={r['n_obs']:,})\n"
                f"- Reference levels: carrier={r['reference_carrier']}, origin={r['reference_origin']}"
            )
        st.caption(
            "Low R\u00b2 is expected and disclosed: individual flight delay has heavy "
            "operational and random variation that weather alone doesn't explain. "
            "The effect of precipitation is real and highly significant, but it is "
            "one factor among many \u2014 see reports/findings_memo.md for full caveats."
        )
    else:
        st.info("Run `python analysis/statistical_analysis.py` to generate findings.")

    st.divider()
    st.caption(
        "Built with Python, PostgreSQL, Streamlit, and Plotly. "
        "Full pipeline, schema, and statistical methodology in the project README."
    )


if __name__ == "__main__":
    main()
