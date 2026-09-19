# Climate Change Trend Analysis and Forecasting

**IDEAS TIH Summer Internship 2026** — an end-to-end analysis of national greenhouse gas emissions:
exploratory data analysis, feature engineering, baseline machine learning models, ETS(A,Ad,N) Holt's
Damped Trend forecasting to 2043, and policy mitigation scenario analysis, for 10 focus countries.

## Project Description

This project ingests open GHG emissions data, explores historical trends, engineers time-series
features, trains and compares regression models to predict next-year CO2 emissions, forecasts
long-range emissions with a damped-trend exponential smoothing model, and simulates the impact of
mitigation policy scenarios. The full analysis lives in `notebook/ghg_analysis.ipynb`; an optional
interactive dashboard (`app.py`) presents the same findings via Streamlit.

**Focus countries:** China, United States, India, Russia, Japan, Germany, Brazil, United Kingdom,
South Africa, Australia — a mix of major emitters, economies at different stages of development, and
countries with documented emissions-reduction trajectories.

## Data Sources

- **Primary:** [Our World in Data CO2 and GHG dataset](https://github.com/owid/co2-data) — annual
  CO2/GHG emissions by country (total, per capita, per GDP, production vs. consumption-based), plus
  energy mix and related indicators.
- **Supporting:** [Climate Watch Historical Emissions](https://climatewatchdata.org)

The primary dataset is downloaded as `data/owid-co2-data.csv`. Running the notebook also produces
`data/ghg_features.csv` (engineered modelling features) and `data/scenario_projections.csv`
(mitigation scenario projections), which `app.py` reads directly.

## Project Structure

```
.
├── notebook/
│   └── ghg_analysis.ipynb   # Complete, documented Jupyter Notebook (Weeks 1-6)
├── app.py                   # Streamlit dashboard (stretch goal)
├── data/
│   ├── owid-co2-data.csv        # Downloaded raw dataset
│   ├── ghg_features.csv         # Engineered feature set (Week 2 output)
│   └── scenario_projections.csv # Mitigation scenario projections (Week 5 output)
├── requirements.txt
└── README.md
```

## How to Run

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Notebook

```bash
jupyter lab notebook/ghg_analysis.ipynb
```

Run all cells top to bottom. The notebook downloads/reads `../data/owid-co2-data.csv` and writes
`../data/ghg_features.csv` and `../data/scenario_projections.csv` as it runs.

If `data/owid-co2-data.csv` is not already present, download it first:

```bash
curl -sL -o data/owid-co2-data.csv https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv
```

### Streamlit Dashboard (stretch goal)

Run the notebook at least once first, so `data/ghg_features.csv` and `data/scenario_projections.csv`
exist, then from the project root:

```bash
streamlit run app.py
```

## Methodology Summary

1. **Week 1 — EDA:** load and profile the full sovereign-country panel (1990–present), filter out
   aggregates, and chart global/top-emitter/gas-mix trends.
2. **Week 2 — Feature Engineering:** decade/time-index, 5-year rolling mean, 1–3 year lags, per-capita
   and GHG-intensity checks, and year-on-year growth rates, restricted to the 10 focus countries.
3. **Week 3 — Baseline ML:** a naive no-change baseline, a per-country Linear Regression, and a single
   pooled Random Forest (with a `country_encoded` feature), evaluated on a 2019–2023 temporal holdout.
4. **Week 4 — Forecasting:** ETS(A,Ad,N) Holt's Damped Trend fit per country on 1990–2018, forecast to
   2043 with a bootstrap-simulated 95% confidence interval, validated against the 2019–2023 holdout.
5. **Week 5 — Scenario Analysis:** Business-as-Usual (ETS baseline), Moderate Mitigation (-2%/year),
   and Aggressive Mitigation (-5%/year) emissions pathways from 2025–2040, with cumulative impact
   comparisons.
6. **Week 6 — Finalisation:** consolidated notebook with a table of contents, consistent chart styling,
   and a written conclusions/limitations section.

## Team

IDEAS TIH Summer Internship 2026 — Climate Change Trend Analysis and Forecasting intern project.

## Container image (deployment)

`Dockerfile` packages only the Streamlit app (`app.py` plus the three CSVs it reads) using the pinned
runtime set in `requirements-app.txt`. The image listens on port 8501 and is meant to run behind a
reverse proxy; `compose.yml` reads an immutable `IMAGE_REF` and publishes no host ports. Pushing a
version tag that is on `main` (for example `v1.0.0`) builds the image to GHCR and deploys it.

```bash
docker build -t climate-app .
docker run --rm -p 127.0.0.1:8501:8501 climate-app   # http://127.0.0.1:8501
```
