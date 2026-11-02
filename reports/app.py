from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
import streamlit as st

st.set_page_config(page_title="SQL Results & Reports", layout="wide")

DB_FILE = Path(__file__).resolve().parents[1] / "database" / "earthquakes.db"

@st.cache_resource
def get_db_engine():
    return create_engine(f"sqlite:///{DB_FILE.as_posix()}")

if not DB_FILE.is_file():
    st.error(f"Database file not found: {DB_FILE}")
    st.stop()

engine = get_db_engine()

st.title("SQL Queries & Static Analysis Results")
st.markdown("SQL queries and results from the 03.SQL-analysis notebook.")

questions = [
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
    SELECT continent, AVG(depth_km) as avg_depth
FROM earthquakes
GROUP BY continent
"""),
    ("Average magnitude per magnitude type (magType)", """
SELECT magType, AVG(mag) as avg_mag
FROM earthquakes
GROUP BY magType
"""),
    ("Year with most earthquakes", """
SELECT strftime('%Y', time) as year, COUNT(*) as tot_earthquakes
FROM earthquakes
GROUP BY year
ORDER BY tot_earthquakes DESC
LIMIT 5
"""),
    ("Month with highest number of earthquakes", """
SELECT strftime('%m', time) as month, COUNT(*) as tot_earthquakes
FROM earthquakes
GROUP BY month
ORDER BY tot_earthquakes DESC
LIMIT 5
"""),
    ("Day of week with most earthquakes", """
SELECT strftime('%w', time) as day_of_week, COUNT(*) as tot_earthquakes
FROM earthquakes
GROUP BY day_of_week
ORDER BY tot_earthquakes DESC
LIMIT 5
"""),
    ("Count of earthquakes per hour of day", """
SELECT strftime('%H', time) as hour_of_day, COUNT(*) as tot_earthquakes
FROM earthquakes
GROUP BY hour_of_day
ORDER BY tot_earthquakes DESC
LIMIT 5
"""),
    ("Most active reporting network (net)", """
SELECT net, COUNT(*) as tot_earthquakes
FROM earthquakes
GROUP BY net
ORDER BY tot_earthquakes DESC
LIMIT 5
"""),
    ("Top 5 places with highest casualties", """
SELECT
  e.place, e.region,
  (i.empirical_fatalities+i.semi_empirical_fatalities) as total_casualties
FROM earthquakes e
LEFT JOIN earthquake_impacts i
  ON e.id = i.event_id ORDER BY total_casualties DESC LIMIT 5
"""),
    ("Total estimated economic loss per continent", """
SELECT
    e.continent,
    printf('$%,.0f', ROUND(SUM(i.economic_loss_usd), 0)) AS total_economic_loss
FROM earthquakes e
JOIN earthquake_impacts i
    ON e.id = i.event_id
GROUP BY e.continent
ORDER BY SUM(i.economic_loss_usd) DESC
"""),
    ("Average economic loss by alert level", """
SELECT
    e.alert,
    printf('$%,.0f', ROUND(AVG(i.economic_loss_usd), 0)) AS total_economic_loss
FROM earthquakes e
JOIN earthquake_impacts i
    ON e.id = i.event_id
GROUP BY e.alert
ORDER BY AVG(i.economic_loss_usd) DESC
"""),
    ("Count of reviewed vs automatic earthquakes (status)", """
SELECT status, COUNT(*) as tot_earthquakes
FROM earthquakes
GROUP BY status
"""),
    ("Count by earthquake type (type)", """
SELECT type, COUNT(*) as tot_earthquakes
FROM earthquakes
GROUP BY type
"""),
    ("Number of earthquakes by data type (types)", """
SELECT
    types,
    COUNT(*) AS total_earthquakes
FROM earthquakes
GROUP BY types
ORDER BY total_earthquakes DESC
LIMIT 20
"""),
    ("Average RMS and gap per continent", """
SELECT
    continent,
    ROUND(AVG(rms), 2) AS avg_rms,
    ROUND(AVG(gap), 2) AS avg_gap
FROM earthquakes
GROUP BY continent
ORDER BY avg_rms, avg_gap DESC
"""),
    ("Events with high station coverage (nst > threshold)", """
SELECT
    place,
    region,
    nst
FROM earthquakes
WHERE nst > 500
ORDER BY nst DESC;
"""),
    ("Number of tsunamis triggered per year", """
SELECT
    year,
    COUNT(*) as tot_tsunamis
FROM earthquakes
WHERE tsunami > 0
GROUP BY year
ORDER BY tot_tsunamis DESC
"""),
    ("Count earthquakes by alert levels (red, orange, etc.)", """
SELECT
    alert,
    COUNT(*) as tot_earthquakes
FROM earthquakes
GROUP BY alert
ORDER BY tot_earthquakes DESC
"""),
    ("Top 5 countries by average magnitude in the past 5 years", """
SELECT
    country,
    ROUND(AVG(mag), 2) AS avg_magnitude,
    COUNT(*) AS total_earthquakes
FROM earthquakes
WHERE year >= (
    SELECT MAX(year) - 4
    FROM earthquakes
)
GROUP BY country
HAVING COUNT(*) >= 5
ORDER BY avg_magnitude DESC
LIMIT 5
"""),
    ("Countries with both shallow and deep earthquakes in the same month", """
SELECT
    country,
    year,
    month,
    SUM(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END) AS shallow_count,
    SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END) AS deep_count
FROM earthquakes
GROUP BY country, year, month
HAVING
    SUM(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END) > 0
    AND
    SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END) > 0
ORDER BY year, month, country
"""),
    ("Year-over-year growth rate in total global earthquakes", """
SELECT
    year,
    COUNT(*) AS total_earthquakes
FROM earthquakes
GROUP BY year
ORDER BY year
"""),
    ("Top 3 seismically active regions by frequency and average magnitude", """
SELECT
    region,
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
SELECT
    country,
    ROUND(AVG(depth_km), 2) AS avg_depth_km,
    COUNT(*) AS earthquake_count
FROM earthquakes
WHERE latitude BETWEEN -5 AND 5
GROUP BY country
ORDER BY avg_depth_km DESC
"""),
    ("Countries with the highest shallow-to-deep earthquake ratio", """
SELECT
    country,
    SUM(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END) AS shallow_count,
    SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END) AS deep_count,
    ROUND(
        CAST(
            SUM(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END)
            AS REAL
        ) /
        NULLIF(
            SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END),
            0
        ),
        2
    ) AS shallow_to_deep_ratio
FROM earthquakes
GROUP BY country
HAVING deep_count > 0
ORDER BY shallow_to_deep_ratio DESC
"""),
    ("Average magnitude difference between tsunami and non-tsunami earthquakes", """
SELECT
    ROUND(
        (
            SELECT AVG(mag)
            FROM earthquakes
            WHERE tsunami = 1
        )
        -
        (
            SELECT AVG(mag)
            FROM earthquakes
            WHERE tsunami = 0
        ),
        2
    ) AS avg_magnitude_difference
"""),
    ("Events with the lowest data reliability (highest average error margins)", """
SELECT
    id,
    place,
    country,
    mag,
    rms,
    gap,
    ROUND((rms + gap) / 2.0, 2) AS avg_error_margin
FROM earthquakes
ORDER BY avg_error_margin DESC
LIMIT 20
"""),
    ("Nearby consecutive earthquakes within 50 km and 1 hour", None),
    ("Regions with the most deep-focus earthquakes (depth > 300 km)", """
SELECT
    region,
    COUNT(*) AS deep_focus_earthquake_count
FROM earthquakes
WHERE depth_km > 300
GROUP BY region
ORDER BY deep_focus_earthquake_count DESC
"""),
]

for question_number, (title, query) in enumerate(questions, start=1):
    with st.expander(f"Q{question_number}: {title}", expanded=question_number == 1):
        if query is None:
            st.info("Todo: continent column value update needed.")
            continue

        sql_column, results_column = st.columns(2)
        with sql_column:
            st.markdown("**SQL Query:**")
            st.code(query.strip(), language="sql")

        with results_column:
            st.markdown("**Results:**")
            try:
                result = pd.read_sql_query(query, engine)
                if question_number == 23:
                    result["growth_rate_percent"] = (
                        result["total_earthquakes"].pct_change() * 100
                    ).round(2)
                st.dataframe(result, width="stretch")
            except Exception as error:
                st.error(f"Error executing query: {error}")
