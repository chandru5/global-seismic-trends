# Global Seismic Trends

A Python, SQLite, and Streamlit project for collecting, preparing, and exploring earthquake catalog data. It combines event-level earthquake information with enriched impact estimates and presents 30 SQL analyses in a local Streamlit report.

## Data and database download

The data files and SQLite database are hosted in the shared Google Drive folder:

[Download project data and database](https://drive.google.com/drive/folders/1XWwJK1zgn2L7xpS_KBJdSOKte_4_dkGw?usp=sharing)

Download the required files from that folder and place them in the project using this structure:

```text
global-seismic-trends/
├── data/
│   ├── earthquakes.csv
│   ├── earthquakes_clean.csv
│   └── earthquake_impacts_enriched.csv
├── database/
│   └── earthquakes.db
├── documentation/
├── notebooks/
└── reports/
    └── app.py
```

The Streamlit app expects `database/earthquakes.db` at the project root. The database should contain an `earthquakes` table. Impact analyses also require an `earthquake_impacts` table. The CSV files are used by the notebook workflow; the app reads query results from SQLite.

The CSV and SQLite assets are large and are distributed through Drive rather than included in this repository. Do not rename the files unless you also update notebook or app paths.

## Project workflow

1. `notebooks/01-data_collection.ipynb` requests earthquake event data from the USGS FDSN Event API and writes the raw records to `data/earthquakes.csv`.
2. `notebooks/02-data_preparation.ipynb` cleans and enriches the event data. It derives calendar and geographic fields, classifies magnitude and depth, handles selected missing values, and writes `data/earthquakes_clean.csv`.
3. `notebooks/03-sql_analysis.ipynb` loads the cleaned earthquake records and impact data into SQLite and runs SQL analyses.
4. `reports/app.py` connects to the local SQLite database and displays the numbered SQL questions and their results in Streamlit.

The notebooks were originally developed in Google Colab and still contain Google Drive paths. The Streamlit app uses the local project-relative database path, but the notebook paths may need to be updated before running the notebooks outside Colab.

## Run the Streamlit report

Use Python 3.10 or later. From the project root, create and activate a virtual environment, then install the app dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install pandas SQLAlchemy streamlit
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Then start the app from the project root:

```bash
streamlit run reports/app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`. The database path is resolved from the location of `app.py`, so it does not depend on the terminal's current directory. If the database file is missing, the app reports the missing path and stops.

To run the notebooks, install Jupyter and the notebook dependencies as well:

```bash
python -m pip install jupyter requests pandas SQLAlchemy
```

## Analyses in the app

The report contains 30 numbered analyses covering:

- Strongest, deepest, and shallow high-magnitude earthquakes
- Average depth by continent and average magnitude by magnitude type
- Earthquake counts by year, month, weekday, hour, and reporting network
- Estimated casualties and economic loss by location, continent, and alert level
- Catalog review status, event type, data-product type, RMS, azimuthal gap, and station coverage
- Tsunami flags and alert-level counts
- Country-level magnitude, depth, and shallow-to-deep comparisons
- Year-over-year catalog count growth
- Regional activity scoring and deep-focus earthquake counts
- Proximity of consecutive events

Q23 calculates annual count growth in Python after the SQL query. Q29 (nearby consecutive earthquakes within 50 km and one hour) is currently a placeholder with no query implementation. Other queries are descriptive summaries, not causal models or official hazard estimates.

## Data interpretation notes

- Results depend on the catalog contents and its time coverage. The most recent year may be incomplete.
- Earthquake event counts can reflect reporting and detection coverage as well as seismic activity.
- Impact records are a subset of the full earthquake catalog. Fatality and economic-loss values are estimates and should not be presented as verified official totals without source validation.
- The regional activity score is a project-defined ranking heuristic, not a standardized seismic hazard or risk measure.
- Q28 combines RMS and azimuthal gap as a rough ranking expression. These measures have different meanings and scales, so the resulting score is not a validated reliability metric.
- Geographic results depend on the region, country, and continent assignments in the prepared dataset.

For more detail about each feature, question, interpretation, saved findings, and open work, see [the project documentation](documentation/Global_Seismic_Trends_Project_Documentation.rtf).
