from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

st.set_page_config(page_title="Global Seismic Trends Dashboard", layout="wide")

DB_FILE = Path(__file__).resolve().parents[1] / "database" / "earthquakes.db"

@st.cache_resource
def get_db_engine():
    return create_engine(f"sqlite:///{DB_FILE.as_posix()}")

@st.cache_data
def load_earthquakes():
    if not DB_FILE.is_file():
        return pd.DataFrame(columns=["time", "mag", "depth_km", "region", "continent", "country", "alert", "tsunami"])
    engine = get_db_engine()
    dataframe = pd.read_sql_query("SELECT * FROM earthquakes", engine)
    if "time" in dataframe.columns:
        dataframe["time"] = pd.to_datetime(dataframe["time"], errors="coerce")
    return dataframe

@st.cache_data
def get_summary():
    if not DB_FILE.is_file():
        return {
            "total_earthquakes": 0,
            "average_magnitude": 0.0,
            "average_depth_km": 0.0,
            "strongest_magnitude": 0.0,
            "peak_year": 0,
        }
    summary = pd.read_sql_query(
        """
        SELECT
            COUNT(*) AS total_earthquakes,
            ROUND(AVG(mag), 2) AS average_magnitude,
            ROUND(AVG(depth_km), 2) AS average_depth_km,
            MAX(mag) AS strongest_magnitude
        FROM earthquakes
        """,
        get_db_engine(),
    )
    row = summary.iloc[0].to_dict() if not summary.empty else {}
    peak_year = pd.read_sql_query(
        """
        SELECT CAST(strftime('%Y', time) AS INTEGER) AS year,
               COUNT(*) AS total_earthquakes
        FROM earthquakes
        WHERE time IS NOT NULL
        GROUP BY year
        ORDER BY total_earthquakes DESC, year DESC
        LIMIT 1
        """,
        get_db_engine(),
    )
    return {
        "total_earthquakes": int(row.get("total_earthquakes", 0) or 0),
        "average_magnitude": float(row.get("average_magnitude", 0.0) or 0.0),
        "average_depth_km": float(row.get("average_depth_km", 0.0) or 0.0),
        "strongest_magnitude": float(row.get("strongest_magnitude", 0.0) or 0.0),
        "peak_year": int(peak_year["year"].iloc[0]) if not peak_year.empty else 0,
    }

@st.cache_data
def get_yearly_activity():
    if not DB_FILE.is_file():
        return pd.DataFrame({"year": [], "total_earthquakes": []})
    return pd.read_sql_query(
        """
        SELECT CAST(strftime('%Y', time) AS INTEGER) AS year,
               COUNT(*) AS total_earthquakes
        FROM earthquakes
        WHERE time IS NOT NULL
        GROUP BY year
        ORDER BY year
        """,
        get_db_engine(),
    )

@st.cache_data
def get_region_summary():
    if not DB_FILE.is_file():
        return pd.DataFrame({"region": [], "total_earthquakes": [], "avg_magnitude": []})
    return pd.read_sql_query(
        """
        SELECT region,
               COUNT(*) AS total_earthquakes,
               ROUND(AVG(mag), 2) AS avg_magnitude
        FROM earthquakes
        WHERE region IS NOT NULL
        GROUP BY region
        ORDER BY total_earthquakes DESC, avg_magnitude DESC
        LIMIT 10
        """,
        get_db_engine(),
    )

@st.cache_data
def get_depth_by_continent():
    if not DB_FILE.is_file():
        return pd.DataFrame({"continent": [], "avg_depth_km": []})
    return pd.read_sql_query(
        """
        SELECT continent,
               ROUND(AVG(depth_km), 2) AS avg_depth_km
        FROM earthquakes
        WHERE continent IS NOT NULL
        GROUP BY continent
        ORDER BY avg_depth_km DESC
        """,
        get_db_engine(),
    )

@st.cache_data
def get_alert_summary():
    if not DB_FILE.is_file():
        return pd.DataFrame({"alert": [], "total_earthquakes": []})
    return pd.read_sql_query(
        """
        SELECT alert,
               COUNT(*) AS total_earthquakes
        FROM earthquakes
        WHERE alert IS NOT NULL
        GROUP BY alert
        ORDER BY total_earthquakes DESC
        """,
        get_db_engine(),
    )

@st.cache_data
def get_magnitude_distribution():
    if not DB_FILE.is_file():
        return pd.DataFrame({"magnitude_band": [], "count": []})
    return pd.read_sql_query(
        """
        SELECT CASE
                 WHEN mag < 4 THEN '0-4'
                 WHEN mag < 5 THEN '4-5'
                 WHEN mag < 6 THEN '5-6'
                 WHEN mag < 7 THEN '6-7'
                 WHEN mag < 8 THEN '7-8'
                 ELSE '8+'
               END AS magnitude_band,
               COUNT(*) AS count
        FROM earthquakes
        WHERE mag IS NOT NULL
        GROUP BY magnitude_band
        ORDER BY magnitude_band
        """,
        get_db_engine(),
    )

@st.cache_data
def get_questions():
    return [
        ("Top 10 strongest earthquakes (mag)", """
SELECT mag, place, region, time
FROM earthquakes
ORDER BY mag DESC
LIMIT 10
"""),
        ("Top 10 deepest earthquakes (depth_km)", """
SELECT depth_km, place, region, time
FROM earthquakes
ORDER BY depth_km DESC
LIMIT 10
"""),
        ("Shallow earthquakes < 50 km and mag > 7.5", """
SELECT depth_km, mag, place, region, time
FROM earthquakes
WHERE depth_km < 50 AND mag > 7.5
"""),
        ("Average depth per continent", """
SELECT continent, AVG(depth_km) AS avg_depth
FROM earthquakes
GROUP BY continent
"""),
        ("Average magnitude per magnitude type (magType)", """
SELECT magType, AVG(mag) AS avg_mag
FROM earthquakes
GROUP BY magType
"""),
        ("Year with most earthquakes", """
SELECT strftime('%Y', time) AS year, COUNT(*) AS tot_earthquakes
FROM earthquakes
GROUP BY year
ORDER BY tot_earthquakes DESC
LIMIT 5
"""),
        ("Month with highest number of earthquakes", """
SELECT strftime('%m', time) AS month, COUNT(*) AS tot_earthquakes
FROM earthquakes
GROUP BY month
ORDER BY tot_earthquakes DESC
LIMIT 5
"""),
        ("Day of week with most earthquakes", """
SELECT strftime('%w', time) AS day_of_week, COUNT(*) AS tot_earthquakes
FROM earthquakes
GROUP BY day_of_week
ORDER BY tot_earthquakes DESC
LIMIT 5
"""),
        ("Count of earthquakes per hour of day", """
SELECT strftime('%H', time) AS hour_of_day, COUNT(*) AS tot_earthquakes
FROM earthquakes
GROUP BY hour_of_day
ORDER BY tot_earthquakes DESC
LIMIT 5
"""),
        ("Most active reporting network (net)", """
SELECT net, COUNT(*) AS tot_earthquakes
FROM earthquakes
GROUP BY net
ORDER BY tot_earthquakes DESC
LIMIT 5
"""),
        ("Top 5 places with highest casualties", """
SELECT e.place, e.region,
       (i.empirical_fatalities + i.semi_empirical_fatalities) AS total_casualties
FROM earthquakes e
LEFT JOIN earthquake_impacts i ON e.id = i.event_id
ORDER BY total_casualties DESC
LIMIT 5
"""),
        ("Total estimated economic loss per continent", """
SELECT e.continent,
       printf('$%,.0f', ROUND(SUM(i.economic_loss_usd), 0)) AS total_economic_loss
FROM earthquakes e
JOIN earthquake_impacts i ON e.id = i.event_id
GROUP BY e.continent
ORDER BY SUM(i.economic_loss_usd) DESC
"""),
        ("Average economic loss by alert level", """
SELECT e.alert,
       printf('$%,.0f', ROUND(AVG(i.economic_loss_usd), 0)) AS total_economic_loss
FROM earthquakes e
JOIN earthquake_impacts i ON e.id = i.event_id
GROUP BY e.alert
ORDER BY AVG(i.economic_loss_usd) DESC
"""),
        ("Count of reviewed vs automatic earthquakes (status)", """
SELECT status, COUNT(*) AS tot_earthquakes
FROM earthquakes
GROUP BY status
"""),
        ("Count by earthquake type (type)", """
SELECT type, COUNT(*) AS tot_earthquakes
FROM earthquakes
GROUP BY type
"""),
        ("Number of earthquakes by data type (types)", """
SELECT types, COUNT(*) AS total_earthquakes
FROM earthquakes
GROUP BY types
ORDER BY total_earthquakes DESC
LIMIT 20
"""),
        ("Average RMS and gap per continent", """
SELECT continent,
       ROUND(AVG(rms), 2) AS avg_rms,
       ROUND(AVG(gap), 2) AS avg_gap
FROM earthquakes
GROUP BY continent
ORDER BY avg_rms, avg_gap DESC
"""),
        ("Events with high station coverage (nst > threshold)", """
SELECT place, region, nst
FROM earthquakes
WHERE nst > 500
ORDER BY nst DESC
"""),
        ("Number of tsunamis triggered per year", """
SELECT year, COUNT(*) AS tot_tsunamis
FROM earthquakes
WHERE tsunami > 0
GROUP BY year
ORDER BY tot_tsunamis DESC
"""),
        ("Count earthquakes by alert levels (red, orange, etc.)", """
SELECT alert, COUNT(*) AS tot_earthquakes
FROM earthquakes
GROUP BY alert
ORDER BY tot_earthquakes DESC
"""),
        ("Top 5 countries by average magnitude in the past 5 years", """
SELECT country,
       ROUND(AVG(mag), 2) AS avg_magnitude,
       COUNT(*) AS total_earthquakes
FROM earthquakes
WHERE year >= (SELECT MAX(year) - 4 FROM earthquakes)
GROUP BY country
HAVING COUNT(*) >= 5
ORDER BY avg_magnitude DESC
LIMIT 5
"""),
        ("Countries with both shallow and deep earthquakes in the same month", """
SELECT country, year, month,
       SUM(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END) AS shallow_count,
       SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END) AS deep_count
FROM earthquakes
GROUP BY country, year, month
HAVING SUM(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END) > 0
   AND SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END) > 0
ORDER BY year, month, country
"""),
        ("Year-over-year growth rate in total global earthquakes", """
SELECT year, COUNT(*) AS total_earthquakes
FROM earthquakes
GROUP BY year
ORDER BY year
"""),
        ("Top 3 seismically active regions by frequency and average magnitude", """
SELECT region,
       COUNT(*) AS earthquake_count,
       ROUND(AVG(mag), 2) AS avg_magnitude,
       ROUND(COUNT(*) * AVG(mag), 2) AS activity_score
FROM earthquakes
GROUP BY region
HAVING COUNT(*) >= 10
ORDER BY activity_score DESC
LIMIT 3
"""),
        ("Average depth by country within 5 degrees of the equator", """
SELECT country,
       ROUND(AVG(depth_km), 2) AS avg_depth_km,
       COUNT(*) AS earthquake_count
FROM earthquakes
WHERE latitude BETWEEN -5 AND 5
GROUP BY country
ORDER BY avg_depth_km DESC
"""),
        ("Countries with the highest shallow-to-deep earthquake ratio", """
SELECT country,
       SUM(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END) AS shallow_count,
       SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END) AS deep_count,
       ROUND(CAST(SUM(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END) AS REAL) /
             NULLIF(SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END), 0), 2) AS shallow_to_deep_ratio
FROM earthquakes
GROUP BY country
HAVING deep_count > 0
ORDER BY shallow_to_deep_ratio DESC
"""),
        ("Average magnitude difference between tsunami and non-tsunami earthquakes", """
SELECT ROUND((SELECT AVG(mag) FROM earthquakes WHERE tsunami = 1) -
              (SELECT AVG(mag) FROM earthquakes WHERE tsunami = 0), 2) AS avg_magnitude_difference
"""),
        ("Events with the lowest data reliability (highest average error margins)", """
SELECT id, place, country, mag, rms, gap,
       ROUND((rms + gap) / 2.0, 2) AS avg_error_margin
FROM earthquakes
ORDER BY avg_error_margin DESC
LIMIT 20
"""),
        ("Nearby consecutive earthquakes within 50 km and 1 hour", None),
        ("Regions with the most deep-focus earthquakes (depth > 300 km)", """
SELECT region, COUNT(*) AS deep_focus_earthquake_count
FROM earthquakes
WHERE depth_km > 300
GROUP BY region
ORDER BY deep_focus_earthquake_count DESC
"""),
    ]

summary = get_summary()
if not DB_FILE.is_file():
    st.warning("Database file not found. Add the local SQLite database to database/earthquakes.db to enable the live dashboard.")

st.title("Global Seismic Trends Dashboard")
st.caption("Earthquake activity, depth distribution, alert patterns, and regional trends for the project catalog.")

metric_columns = st.columns(4)
with metric_columns[0]:
    st.metric("Total events", f"{summary['total_earthquakes']}")
with metric_columns[1]:
    st.metric("Avg magnitude", f"{summary['average_magnitude']}")
with metric_columns[2]:
    st.metric("Avg depth", f"{summary['average_depth_km']} km")
with metric_columns[3]:
    st.metric("Strongest event", f"M {summary['strongest_magnitude']}")

yearly_data = get_yearly_activity()
region_data = get_region_summary()
depth_data = get_depth_by_continent()
alert_data = get_alert_summary()
magnitude_distribution = get_magnitude_distribution()

overview_columns = st.columns(2)
with overview_columns[0]:
    st.subheader("Annual earthquake count")
    st.line_chart(yearly_data.set_index("year")["total_earthquakes"])
with overview_columns[1]:
    st.subheader("Top regions by earthquake count")
    st.bar_chart(region_data.set_index("region")["total_earthquakes"])

analysis_columns = st.columns(2)
with analysis_columns[0]:
    st.subheader("Average depth by continent")
    st.bar_chart(depth_data.set_index("continent")["avg_depth_km"])
with analysis_columns[1]:
    st.subheader("Alert distribution")
    st.bar_chart(alert_data.set_index("alert")["total_earthquakes"])

if not magnitude_distribution.empty:
    st.subheader("Magnitude distribution")
    st.bar_chart(magnitude_distribution.set_index("magnitude_band")["count"])

st.subheader("Regional activity overview")
if not region_data.empty:
    st.dataframe(region_data, use_container_width=True)

st.subheader("Q1-Q30 analytical questions")
for question_number, (title, query) in enumerate(get_questions(), start=1):
    with st.expander(f"Q{question_number}: {title}", expanded=question_number == 1):
        if query is None:
            st.info("The nearby-consecutive-event question is a placeholder and is ready for the next SQL definition.")
            continue
        sql_column, results_column = st.columns(2)
        with sql_column:
            st.markdown("**SQL Query:**")
            st.code(query.strip(), language="sql")
        with results_column:
            st.markdown("**Results:**")
            if not DB_FILE.is_file():
                st.warning("The database is not available yet, so the SQL query cannot execute locally. Download the project database to database/earthquakes.db to enable all queries.")
                continue
            try:
                result = pd.read_sql_query(query, get_db_engine())
                if result.empty:
                    st.info("No rows returned for this analysis.")
                else:
                    st.dataframe(result, use_container_width=True)
            except Exception as error:
                st.warning(f"The query could not be executed locally. Error: {error}")
