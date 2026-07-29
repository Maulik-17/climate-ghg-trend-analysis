"""
Climate Change Trend Analysis and Forecasting — Streamlit Dashboard

Interactive companion to notebook/ghg_analysis.ipynb. Assembles the project's EDA, feature,
model, forecast, and scenario outputs into a single-page dashboard with six sections:
Overview, Historical Trends, Country Profile, Forecasts, Scenario Comparison, About.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from statsmodels.tsa.holtwinters import ExponentialSmoothing

RAW_DATA_PATH = "data/owid-co2-data.csv"
FEATURES_PATH = "data/ghg_features.csv"
SCENARIOS_PATH = "data/scenario_projections.csv"

COUNTRIES = [
    "China", "United States", "India", "Russia", "Japan",
    "Germany", "Brazil", "United Kingdom", "South Africa", "Australia",
]
COUNTRY_COLORS = dict(zip(COUNTRIES, px.colors.qualitative.Bold[: len(COUNTRIES)]))
SCENARIO_COLORS = {"BAU": "#1f77b4", "Moderate Mitigation": "#ff7f0e", "Aggressive Mitigation": "#2ca02c"}
GAS_COLUMNS = {"CO2": "co2", "Methane (CH4)": "methane", "Nitrous Oxide (N2O)": "nitrous_oxide"}
RANDOM_STATE = 42

st.set_page_config(page_title="Climate Change Trend Analysis & Forecasting", layout="wide")


# ---------------------------------------------------------------------------
# Data loading (cached so the ~14MB CSV and ETS fits only run once per session)
# ---------------------------------------------------------------------------
@st.cache_data
def load_base_data():
    raw = pd.read_csv(RAW_DATA_PATH)
    filtered = raw[(raw["year"] >= 1990) & (raw["iso_code"].notna())].copy()
    base = (
        filtered[filtered["country"].isin(COUNTRIES)]
        .sort_values(["country", "year"])
        .reset_index(drop=True)
    )
    return filtered, base


@st.cache_data
def load_features():
    return pd.read_csv(FEATURES_PATH)


@st.cache_data
def load_scenarios():
    return pd.read_csv(SCENARIOS_PATH)


@st.cache_resource
def fit_forecasts(base_df):
    """Fit ETS(A,Ad,N) per country on 1990-2018 and forecast 2019-2043 with a bootstrap 95% CI."""
    forecast_years = list(range(2019, 2044))
    n_steps = len(forecast_years)
    forecasts = {}
    for country in COUNTRIES:
        series = base_df[(base_df["country"] == country) & (base_df["year"] <= 2018)].sort_values("year")
        y = pd.Series(series["co2"].values, index=series["year"].values)
        fit = ExponentialSmoothing(y, trend="add", damped_trend=True, seasonal=None).fit(optimized=True)

        mean_fc = fit.forecast(n_steps)
        mean_fc.index = forecast_years
        sims = fit.simulate(nsimulations=n_steps, repetitions=500, error="add",
                             random_errors="bootstrap", random_state=RANDOM_STATE)
        sims.index = forecast_years

        forecasts[country] = {
            "fitted": fit.fittedvalues,
            "mean": mean_fc,
            "ci_lower": sims.quantile(0.025, axis=1),
            "ci_upper": sims.quantile(0.975, axis=1),
            "params": fit.params,
        }
    return forecasts


filtered_df, base_df = load_base_data()
features_df = load_features()
scenario_df = load_scenarios()
ets_forecasts = fit_forecasts(base_df)

st.title("Climate Change Trend Analysis and Forecasting")
st.caption("IDEAS TIH Summer Internship 2026 — GHG Emissions Dashboard")

tabs = st.tabs([
    "Overview", "Historical Trends", "Country Profile", "Forecasts", "Scenario Comparison", "About",
])

# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
with tabs[0]:
    st.header("Overview")
    st.write(
        "This dashboard summarises an end-to-end analysis of national greenhouse gas emissions: "
        "exploratory trends, engineered time-series features, baseline machine learning models, "
        "an ETS(A,Ad,N) Holt's Damped Trend forecast to 2043, and policy mitigation scenarios, "
        "for 10 focus countries spanning major emitters, economies at different stages of "
        "development, and countries with documented emissions-reduction trajectories."
    )

    latest_year = int(base_df["year"].max())
    global_latest = base_df.loc[base_df["year"] == latest_year, "co2"].sum()
    global_1990 = base_df.loc[base_df["year"] == 1990, "co2"].sum()
    pct_change = (global_latest - global_1990) / global_1990 * 100

    col1, col2, col3 = st.columns(3)
    col1.metric(f"Total CO2, {latest_year} (10 countries)", f"{global_latest:,.0f} Mt")
    col2.metric("% Change since 1990", f"{pct_change:+.1f}%")
    col3.metric("Countries Analysed", f"{len(COUNTRIES)}")

    st.subheader("Focus Countries")
    st.write(", ".join(COUNTRIES))

# ---------------------------------------------------------------------------
# Historical Trends
# ---------------------------------------------------------------------------
with tabs[1]:
    st.header("Historical Trends")

    selected_countries = st.multiselect(
        "Select countries for the trend comparison", options=COUNTRIES, default=COUNTRIES[:5],
    )
    if selected_countries:
        trend_df = base_df[base_df["country"].isin(selected_countries)]
        fig = px.line(
            trend_df, x="year", y="co2", color="country",
            title="CO2 Emissions Over Time", labels={"co2": "CO2 Emissions (Mt)", "year": "Year"},
            color_discrete_map=COUNTRY_COLORS,
        )
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Select at least one country to display the trend chart.")

    st.subheader("GHG Composition by Gas Type")
    selected_gases = st.multiselect(
        "Select gases to include", options=list(GAS_COLUMNS.keys()), default=list(GAS_COLUMNS.keys()),
    )
    if selected_gases:
        gas_cols = [GAS_COLUMNS[g] for g in selected_gases]
        decade_df = base_df.copy()
        decade_df["decade"] = (decade_df["year"] // 10 * 10).astype(str) + "s"
        gas_by_decade = decade_df.groupby("decade")[gas_cols].sum().reset_index()
        gas_long = gas_by_decade.melt(id_vars="decade", var_name="gas_col", value_name="emissions")
        inv_map = {v: k for k, v in GAS_COLUMNS.items()}
        gas_long["Gas"] = gas_long["gas_col"].map(inv_map)

        fig = px.area(
            gas_long, x="decade", y="emissions", color="Gas",
            title="GHG Emissions by Gas Type per Decade (10 Focus Countries)",
            labels={"emissions": "Emissions (Mt CO2-eq)", "decade": "Decade"},
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Select at least one gas to display the composition chart.")

# ---------------------------------------------------------------------------
# Country Profile
# ---------------------------------------------------------------------------
with tabs[2]:
    st.header("Country Profile")
    profile_country = st.selectbox("Select a country", options=COUNTRIES, key="profile_country")

    country_df = base_df[base_df["country"] == profile_country].sort_values("year")

    fig_trend = px.line(
        country_df, x="year", y="co2", title=f"{profile_country}: CO2 Emissions Trend",
        labels={"co2": "CO2 Emissions (Mt)", "year": "Year"},
    )
    fig_trend.update_traces(line_color=COUNTRY_COLORS[profile_country], line_width=3)
    fig_trend.update_layout(template="plotly_white")
    st.plotly_chart(fig_trend, width="stretch")

    col1, col2 = st.columns(2)
    with col1:
        fig_pc = px.line(
            country_df, x="year", y="co2_per_capita", title=f"{profile_country}: CO2 Per Capita",
            labels={"co2_per_capita": "CO2 per Capita (t)", "year": "Year"},
        )
        fig_pc.update_traces(line_color=COUNTRY_COLORS[profile_country], line_width=3)
        fig_pc.update_layout(template="plotly_white")
        st.plotly_chart(fig_pc, width="stretch")
    with col2:
        yoy_df = country_df.copy()
        yoy_df["co2_yoy_pct_change"] = yoy_df["co2"].pct_change() * 100
        fig_yoy = px.bar(
            yoy_df, x="year", y="co2_yoy_pct_change",
            title=f"{profile_country}: Year-on-Year CO2 % Change",
            labels={"co2_yoy_pct_change": "YoY Change (%)", "year": "Year"},
        )
        fig_yoy.update_traces(marker_color=COUNTRY_COLORS[profile_country])
        fig_yoy.update_layout(template="plotly_white")
        st.plotly_chart(fig_yoy, width="stretch")

    st.subheader("Key Stats")
    latest_row = country_df.iloc[-1]
    stats_table = pd.DataFrame({
        "Metric": ["Latest Year", "Latest CO2 (Mt)", "Latest CO2 per Capita (t)",
                   "1990 CO2 (Mt)", "% Change since 1990"],
        "Value": [
            str(int(latest_row["year"])),
            f"{latest_row['co2']:.1f}",
            f"{latest_row['co2_per_capita']:.2f}",
            f"{country_df.iloc[0]['co2']:.1f}",
            f"{(latest_row['co2'] - country_df.iloc[0]['co2']) / country_df.iloc[0]['co2'] * 100:+.1f}%",
        ],
    })
    st.table(stats_table)

# ---------------------------------------------------------------------------
# Forecasts
# ---------------------------------------------------------------------------
with tabs[3]:
    st.header("Forecasts — ETS(A,Ad,N) Holt's Damped Trend")
    forecast_country = st.selectbox("Select a country", options=COUNTRIES, key="forecast_country")

    fc = ets_forecasts[forecast_country]
    hist = base_df[(base_df["country"] == forecast_country) & (base_df["year"] <= 2018)].sort_values("year")
    holdout = base_df[
        (base_df["country"] == forecast_country) & (base_df["year"].between(2019, 2023))
    ].sort_values("year")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist["year"], y=hist["co2"], name="Historical actual (1990-2018)",
                              mode="lines", line=dict(color="black", width=2)))
    fig.add_trace(go.Scatter(x=fc["fitted"].index, y=fc["fitted"].values, name="Fitted values",
                              mode="lines", line=dict(color="gray", dash="dot")))
    fig.add_trace(go.Scatter(x=holdout["year"], y=holdout["co2"], name="Holdout actual (2019-2023)",
                              mode="markers", marker=dict(color="black", size=8, symbol="diamond")))
    fc_to_2040 = fc["mean"].loc[:2040]
    ci_lower_to_2040 = fc["ci_lower"].loc[:2040]
    ci_upper_to_2040 = fc["ci_upper"].loc[:2040]
    fig.add_trace(go.Scatter(x=fc_to_2040.index, y=fc_to_2040.values, name="Forecast to 2040",
                              mode="lines", line=dict(color="crimson", width=2)))
    fig.add_trace(go.Scatter(
        x=list(ci_upper_to_2040.index) + list(ci_lower_to_2040.index[::-1]),
        y=list(ci_upper_to_2040.values) + list(ci_lower_to_2040.values[::-1]),
        fill="toself", fillcolor="rgba(220,20,60,0.15)", line=dict(color="rgba(0,0,0,0)"),
        name="95% CI", hoverinfo="skip",
    ))
    fig.update_layout(title=f"ETS(A,Ad,N) Forecast: {forecast_country}", xaxis_title="Year",
                       yaxis_title="CO2 Emissions (Mt)", template="plotly_white",
                       legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig, width="stretch")

    st.subheader("Forecast Summary")
    actual_2020 = base_df.loc[
        (base_df["country"] == forecast_country) & (base_df["year"] == 2020), "co2"
    ].values[0]
    summary = pd.DataFrame({
        "Metric": ["2030 Forecast (Mt)", "2035 Forecast (Mt)", "2040 Forecast (Mt)",
                   "2020 Actual (Mt)", "% Change 2020->2040", "Damping Parameter (phi)"],
        "Value": [
            f"{fc['mean'].loc[2030]:.1f}",
            f"{fc['mean'].loc[2035]:.1f}",
            f"{fc['mean'].loc[2040]:.1f}",
            f"{actual_2020:.1f}",
            f"{(fc['mean'].loc[2040] - actual_2020) / actual_2020 * 100:+.1f}%",
            f"{fc['params']['damping_trend']:.3f}",
        ],
    })
    st.table(summary)

# ---------------------------------------------------------------------------
# Scenario Comparison
# ---------------------------------------------------------------------------
with tabs[4]:
    st.header("Scenario Comparison")
    st.write(
        "Business as Usual (BAU) uses the ETS(A,Ad,N) baseline forecast; Moderate and Aggressive "
        "Mitigation apply illustrative 2%/year and 5%/year linear reduction rates from 2025."
    )

    view_mode = st.radio("View", options=["Per-Country", "Global Aggregate"], horizontal=True)

    if view_mode == "Per-Country":
        scenario_country = st.selectbox("Select a country", options=COUNTRIES, key="scenario_country")
        hist = base_df[
            (base_df["country"] == scenario_country) & (base_df["year"].between(1990, 2024))
        ].sort_values("year")
        level_1990 = base_df.loc[
            (base_df["country"] == scenario_country) & (base_df["year"] == 1990), "co2"
        ].values[0]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist["year"], y=hist["co2"], name="Historical actual (1990-2024)",
                                  mode="lines", line=dict(color="lightgray", width=3)))
        for scen, color in SCENARIO_COLORS.items():
            s = scenario_df[
                (scenario_df["country"] == scenario_country) & (scenario_df["scenario"] == scen)
            ].sort_values("year")
            fig.add_trace(go.Scatter(x=s["year"], y=s["co2_projected"], name=scen,
                                      mode="lines", line=dict(color=color, width=2.5)))
        fig.add_hline(y=level_1990, line_dash="dash", line_color="black",
                      annotation_text="1990 level", annotation_position="top left")
        fig.update_layout(title=f"Emissions Scenarios: {scenario_country}", xaxis_title="Year",
                           yaxis_title="CO2 Emissions (Mt)", template="plotly_white",
                           legend=dict(orientation="h", y=-0.25))
        fig.update_xaxes(range=[2020, 2040])
        st.plotly_chart(fig, width="stretch")
    else:
        global_scenario = scenario_df.groupby(["scenario", "year"])["co2_projected"].sum().reset_index()
        fig = px.line(
            global_scenario, x="year", y="co2_projected", color="scenario",
            title="Global Aggregate Emissions Scenarios (Sum of 10 Countries)",
            labels={"co2_projected": "CO2 Emissions (Mt)", "year": "Year", "scenario": "Scenario"},
            color_discrete_map=SCENARIO_COLORS,
        )
        fig.update_traces(line_width=3)
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, width="stretch")

    st.subheader("Cumulative Emissions, 2025-2040")
    cumulative_df = (
        scenario_df.groupby(["country", "scenario"])["co2_projected"]
        .sum()
        .reset_index()
        .rename(columns={"co2_projected": "cumulative_co2"})
    )
    fig = px.bar(
        cumulative_df, x="country", y="cumulative_co2", color="scenario", barmode="group",
        title="Cumulative CO2 Emissions by Country and Scenario, 2025-2040",
        labels={"cumulative_co2": "Cumulative CO2 (Mt)", "country": "Country", "scenario": "Scenario"},
        color_discrete_map=SCENARIO_COLORS,
    )
    fig.update_layout(template="plotly_white", xaxis_tickangle=-30)
    st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------------
# About
# ---------------------------------------------------------------------------
with tabs[5]:
    st.header("About")
    st.subheader("Data Sources")
    st.markdown(
        "- **Primary:** Our World in Data CO2 and GHG dataset — "
        "[github.com/owid/co2-data](https://github.com/owid/co2-data)\n"
        "- **Supporting:** Climate Watch Historical Emissions — "
        "[climatewatchdata.org](https://climatewatchdata.org)"
    )
    st.subheader("Methodology Summary")
    st.markdown(
        "1. **EDA** on the full sovereign-country panel, 1990-present.\n"
        "2. **Feature engineering** (lags, rolling means, growth rates, per-capita/intensity) "
        "restricted to the 10 focus countries.\n"
        "3. **Baseline ML:** naive no-change model, per-country Linear Regression, and a pooled "
        "Random Forest, trained on 1990-2018 and evaluated on 2019-2023.\n"
        "4. **Forecasting:** ETS(A,Ad,N) Holt's Damped Trend fit per country, forecast to 2043 "
        "with a bootstrap-simulated 95% confidence interval.\n"
        "5. **Scenario analysis:** BAU, Moderate (-2%/yr), and Aggressive (-5%/yr) mitigation "
        "pathways from 2025-2040."
    )
    st.subheader("Team / Attribution")
    st.markdown(
        "**IDEAS TIH Summer Internship 2026** — Climate Change Trend Analysis and Forecasting "
        "intern project. See `README.md` for full project details and setup instructions."
    )
