import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from statsmodels.tsa.arima.model import ARIMA

st.set_page_config(page_title="TradeWar AI Simulator", page_icon="🌏", layout="wide")

COUNTRIES = [
    "China",
    "India",
    "Vietnam",
    "Bangladesh",
    "Thailand",
    "South Korea",
    "Taiwan",
    "Japan",
    "EU",
    "US",
]

CATEGORIES = ["Electronics", "Textiles", "Semiconductors", "Machinery", "Chemicals", "Steel"]
YEARS = list(range(2015, 2025))

TRADE_ELASTICITY = {
    "Electronics": -0.8,
    "Semiconductors": -0.9,
    "Machinery": -0.7,
    "Chemicals": -0.5,
    "Textiles": -0.6,
    "Steel": -0.7,
}

ALTERNATIVE_SUPPLIERS = {
    "China": ["Vietnam", "India", "Thailand", "Bangladesh"],
    "US": ["EU", "Japan", "South Korea"],
    "Vietnam": ["China", "Thailand", "Bangladesh"],
    "India": ["Vietnam", "Bangladesh", "Thailand"],
}

TRADE_FLOWS = [
    ("China", "US", 500),
    ("China", "EU", 400),
    ("China", "Japan", 170),
    ("China", "South Korea", 160),
    ("China", "India", 100),
    ("China", "Vietnam", 80),
    ("Vietnam", "US", 110),
    ("Vietnam", "EU", 50),
    ("Vietnam", "China", 70),
    ("Vietnam", "Japan", 25),
    ("India", "US", 80),
    ("India", "EU", 65),
    ("India", "China", 20),
    ("South Korea", "China", 150),
    ("South Korea", "US", 80),
    ("Taiwan", "China", 180),
    ("Taiwan", "US", 100),
    ("Japan", "US", 150),
    ("Japan", "China", 160),
    ("Japan", "EU", 80),
    ("US", "EU", 350),
    ("US", "Japan", 80),
    ("US", "China", 150),
    ("Bangladesh", "EU", 20),
    ("Bangladesh", "US", 10),
    ("Thailand", "US", 45),
    ("Thailand", "China", 40),
    ("Thailand", "EU", 30),
]


@st.cache_data(show_spinner=False)
def generate_trade_data():
    """Generate a synthetic but realistic trade dataset for teaching and prototyping."""
    records = []
    base_exports = {
        "China": 2500,
        "India": 450,
        "Vietnam": 280,
        "Bangladesh": 45,
        "Thailand": 250,
        "South Korea": 600,
        "Taiwan": 380,
        "Japan": 700,
        "EU": 2200,
        "US": 1600,
    }
    cat_weight = {
        "Electronics": 0.30,
        "Semiconductors": 0.20,
        "Machinery": 0.18,
        "Chemicals": 0.12,
        "Textiles": 0.12,
        "Steel": 0.08,
    }

    for year in YEARS:
        for exporter in COUNTRIES:
            for category in CATEGORIES:
                base = base_exports[exporter]
                growth = 1.04 ** (year - 2015)
                shock = 1.0
                if year >= 2018:
                    if exporter in ["China", "US"] and category in ["Electronics", "Semiconductors"]:
                        shock = 0.82
                    elif exporter in ["Vietnam", "India"] and category in ["Electronics", "Textiles"]:
                        shock = 1.15
                covid = 0.88 if year == 2020 else 1.0
                export_val = base * cat_weight[category] * growth * shock * covid * np.random.uniform(0.93, 1.07)

                tariff_rate = np.random.uniform(2, 8)
                if year >= 2018 and exporter == "China" and category in ["Electronics", "Semiconductors"]:
                    tariff_rate = np.random.uniform(20, 25)

                records.append(
                    {
                        "year": year,
                        "country": exporter,
                        "category": category,
                        "export_value_bn_usd": round(export_val, 2),
                        "tariff_rate_pct": round(tariff_rate, 2),
                        "gdp_growth_pct": round(np.random.uniform(2, 8), 2),
                        "inflation_pct": round(np.random.uniform(1, 6), 2),
                        "manufacturing_reliance": round(np.random.uniform(0.2, 0.7), 2),
                        "shipping_dependency": round(np.random.uniform(0.3, 0.9), 2),
                    }
                )
    return pd.DataFrame(records)


@st.cache_data(show_spinner=False)
def build_trade_network():
    g = nx.DiGraph()
    for country in COUNTRIES:
        g.add_node(country)
    for exporter, importer, value in TRADE_FLOWS:
        g.add_edge(exporter, importer, weight=value, label=f"${value}B")

    pagerank = nx.pagerank(g, weight="weight")
    in_centrality = nx.in_degree_centrality(g)
    out_centrality = nx.out_degree_centrality(g)
    betweenness = nx.betweenness_centrality(g, weight="weight")

    metrics_df = pd.DataFrame(
        {
            "country": COUNTRIES,
            "pagerank": [round(pagerank.get(c, 0), 4) for c in COUNTRIES],
            "import_dependency": [round(in_centrality.get(c, 0), 4) for c in COUNTRIES],
            "export_reach": [round(out_centrality.get(c, 0), 4) for c in COUNTRIES],
            "bridge_score": [round(betweenness.get(c, 0), 4) for c in COUNTRIES],
        }
    ).sort_values("pagerank", ascending=False)

    vulnerability = {}
    for node in g.nodes():
        import_dep = sum(g[u][node]["weight"] for u in g.predecessors(node) if g.has_edge(u, node))
        vulnerability[node] = round((import_dep / 1000) * 0.5 + betweenness.get(node, 0) * 100 * 0.3 + pagerank.get(node, 0) * 10 * 0.2, 3)
    vulnerability = dict(sorted(vulnerability.items(), key=lambda item: -item[1]))
    return g, metrics_df, vulnerability


@st.cache_data(show_spinner=False)
def forecast_series(series, steps=3):
    if len(series) < 5:
        return np.array([series[-1]] * steps)
    try:
        model = ARIMA(series, order=(1, 1, 1))
        fit = model.fit()
        return fit.forecast(steps=steps)
    except Exception:
        x = np.arange(len(series))
        slope = np.polyfit(x, series, 1)[0]
        intercept = np.polyfit(x, series, 1)[1]
        future = np.array([intercept + slope * (len(series) + i) for i in range(steps)])
        return future


def build_country_scenario(df, country, category, tariff_change_pct, target_partner):
    elasticity = TRADE_ELASTICITY.get(category, -0.7)
    base_export = float(
        df[(df["country"] == country) & (df["category"] == category) & (df["year"] == 2024)]["export_value_bn_usd"].sum()
    )
    trade_change_pct = elasticity * tariff_change_pct
    trade_change_pct = float(np.clip(trade_change_pct, -40.0, 30.0))
    new_export = base_export * (1 + trade_change_pct / 100)
    delta = new_export - base_export

    alternatives = ALTERNATIVE_SUPPLIERS.get(country, [])
    diversion_per_alt = abs(delta) / max(len(alternatives), 1) if alternatives else 0.0

    impact_rows = []
    for other_country in COUNTRIES:
        if other_country == country:
            pct = trade_change_pct
            predicted_export = new_export
        elif other_country in alternatives:
            pct = -0.35 * trade_change_pct
            predicted_export = float(
                df[(df["country"] == other_country) & (df["category"] == category) & (df["year"] == 2024)]["export_value_bn_usd"].sum()
                * (1 + pct / 100)
            )
        elif other_country == target_partner:
            pct = 0.15 * abs(trade_change_pct) if tariff_change_pct > 0 else -0.05 * abs(trade_change_pct)
            predicted_export = float(
                df[(df["country"] == other_country) & (df["category"] == category) & (df["year"] == 2024)]["export_value_bn_usd"].sum()
                * (1 + pct / 100)
            )
        else:
            pct = 0.05 * trade_change_pct
            predicted_export = float(
                df[(df["country"] == other_country) & (df["category"] == category) & (df["year"] == 2024)]["export_value_bn_usd"].sum()
                * (1 + pct / 100)
            )
        impact_rows.append(
            {
                "country": other_country,
                "baseline_export_bn": float(
                    df[(df["country"] == other_country) & (df["category"] == category) & (df["year"] == 2024)]["export_value_bn_usd"].sum()
                ),
                "predicted_export_bn": round(predicted_export, 2),
                "change_pct": round(pct, 2),
                "change_bn": round(predicted_export - float(df[(df["country"] == other_country) & (df["category"] == category) & (df["year"] == 2024)]["export_value_bn_usd"].sum()), 2),
            }
        )

    impact_df = pd.DataFrame(impact_rows).sort_values("change_bn", ascending=False)
    return {
        "country": country,
        "category": category,
        "target_partner": target_partner,
        "baseline_export_bn": round(base_export, 2),
        "predicted_export_bn": round(new_export, 2),
        "trade_change_pct": round(trade_change_pct, 2),
        "trade_delta_bn": round(delta, 2),
        "risk_score": round(min(100.0, abs(trade_change_pct) * 1.6 + 12), 1),
        "trade_diversion": {alt: round(diversion_per_alt, 2) for alt in alternatives},
        "impact_df": impact_df,
    }


def build_forecast_chart(df, country, category, steps=3):
    series = (
        df[(df["country"] == country) & (df["category"] == category)]
        .sort_values("year")["export_value_bn_usd"]
        .values
    )
    hist_df = (
        df[(df["country"] == country) & (df["category"] == category)]
        .sort_values("year")[["year", "export_value_bn_usd"]]
        .copy()
    )
    forecast_vals = forecast_series(series, steps=steps)
    future_years = list(range(2025, 2025 + steps))
    forecast_df = pd.DataFrame({"year": future_years, "forecast_value_bn_usd": forecast_vals})

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist_df["year"], y=hist_df["export_value_bn_usd"], mode="lines+markers", name="Historical", line=dict(color="#00d4ff", width=3)))
    fig.add_trace(go.Scatter(x=forecast_df["year"], y=forecast_df["forecast_value_bn_usd"], mode="lines+markers", name="Forecast", line=dict(color="#ff6b35", width=3, dash="dash")))
    fig.update_layout(
        title=f"Historical and Forecasted Exports — {country} | {category}",
        xaxis_title="Year",
        yaxis_title="Export Value (USD Bn)",
        template="plotly_dark",
        height=360,
    )
    return fig


def build_network_figure(g, pagerank):
    fig, ax = plt.subplots(figsize=(10, 7))
    pos = nx.spring_layout(g, seed=42, k=1.4)
    node_sizes = [pagerank[n] * 60000 for n in g.nodes()]
    edge_weights = [g[u][v]["weight"] for u, v in g.edges()]
    max_w = max(edge_weights) if edge_weights else 1
    edge_widths = [w / max_w * 4 for w in edge_weights]

    nx.draw_networkx_nodes(g, pos, node_size=node_sizes, node_color=list(pagerank.values()), cmap=cm.plasma, alpha=0.95, ax=ax)
    nx.draw_networkx_edges(g, pos, width=edge_widths, edge_color="#aaaaaa", alpha=0.6, arrows=True, arrowsize=15, connectionstyle="arc3,rad=0.08", ax=ax)
    nx.draw_networkx_labels(g, pos, font_size=9, font_color="white", ax=ax)
    ax.set_title("Trade Dependency Network", fontsize=13)
    ax.axis("off")
    plt.tight_layout()
    return fig


# Load data once
np.random.seed(42)
df = generate_trade_data()
G, metrics_df, vulnerability = build_trade_network()

# Sidebar controls
st.sidebar.header("Policy Scenario")
preset = st.sidebar.selectbox(
    "Scenario preset",
    [
        "Custom",
        "US tariffs on China electronics",
        "EU tariffs on Vietnam textiles",
        "US tariffs on India semiconductors",
    ],
)

preset_map = {
    "Custom": {"country": "China", "category": "Electronics", "target_partner": "US", "tariff_change": 25},
    "US tariffs on China electronics": {"country": "China", "category": "Electronics", "target_partner": "US", "tariff_change": 25},
    "EU tariffs on Vietnam textiles": {"country": "Vietnam", "category": "Textiles", "target_partner": "EU", "tariff_change": 15},
    "US tariffs on India semiconductors": {"country": "India", "category": "Semiconductors", "target_partner": "US", "tariff_change": 20},
}

selected = preset_map[preset]
country = st.sidebar.selectbox("Affected exporter", COUNTRIES, index=COUNTRIES.index(selected["country"]))
category = st.sidebar.selectbox("Product category", CATEGORIES, index=CATEGORIES.index(selected["category"]))
target_partner = st.sidebar.selectbox("Policy actor", ["US", "EU", "China", "Japan", "South Korea"], index=["US", "EU", "China", "Japan", "South Korea"].index(selected["target_partner"]))
tariff_change = st.sidebar.slider("Tariff change (%)", min_value=-30, max_value=30, value=selected["tariff_change"], step=1)
forecast_steps = st.sidebar.slider("Forecast horizon (years)", min_value=1, max_value=5, value=3, step=1)

# Main app content
st.title("🌏 TradeWar AI Simulator")
st.caption("Interactive policy simulation for tariff ripple effects across Asian supply chains")

st.markdown(
    "This dashboard lets users test trade-policy scenarios and see how tariffs can change exports, shift market share, and reshape supply chains across 10 economies."
)

st.info(
    "Economic intuition: tariffs act like a tax on trade. When barriers rise, exporters often lose market share, alternative suppliers may gain, and downstream consumers usually face higher costs."
)

scenario = build_country_scenario(df, country, category, tariff_change, target_partner)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Affected exporter", scenario["country"])
col2.metric("Category", scenario["category"])
col3.metric("Predicted export change", f"{scenario['trade_change_pct']:+.1f}%")
col4.metric("Risk score", f"{scenario['risk_score']:.0f}/100")

st.subheader("Scenario outcome")

scenario_text = (
    f"A {abs(tariff_change)}% tariff change on {country}'s {category} trade with {target_partner} is expected to move exports from {scenario['baseline_export_bn']:.1f}B to {scenario['predicted_export_bn']:.1f}B."
    if tariff_change > 0
    else f"A {abs(tariff_change)}% tariff reduction on {country}'s {category} trade with {target_partner} could lift exports from {scenario['baseline_export_bn']:.1f}B to {scenario['predicted_export_bn']:.1f}B."
)
st.write(scenario_text)

if scenario["trade_diversion"]:
    winners = ", ".join([k for k in scenario["trade_diversion"].keys() if scenario["trade_diversion"][k] > 0][:3])
    st.write(f"Likely beneficiaries: {winners}")

# Tabs for deeper analysis
overview_tab, forecast_tab, network_tab = st.tabs(["Overview", "Forecast & impact", "Trade network"])

with overview_tab:
    st.subheader("Country-by-country impact")
    impact_df = scenario["impact_df"].copy()
    impact_df["impact_label"] = impact_df["change_bn"].apply(lambda value: "+" if value >= 0 else "") + impact_df["change_bn"].round(2).astype(str)
    st.dataframe(
        impact_df[["country", "baseline_export_bn", "predicted_export_bn", "change_pct", "change_bn"]].round(2),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Impact by country")
    fig_bar = px.bar(
        impact_df,
        x="country",
        y="change_bn",
        color="change_bn",
        color_continuous_scale="RdBu",
        title="Predicted export change by country",
        labels={"country": "Country", "change_bn": "Change (USD Bn)"},
    )
    fig_bar.update_layout(template="plotly_dark", height=360)
    st.plotly_chart(fig_bar, use_container_width=True)

with forecast_tab:
    st.subheader("Historical trend and forecast")
    forecast_fig = build_forecast_chart(df, country, category, steps=forecast_steps)
    st.plotly_chart(forecast_fig, use_container_width=True)

    st.subheader("How the scenario changes the story")
    st.write(
        "The chart above shows how the selected exporter has moved historically and where a simple statistical forecast suggests the next few years may head. The scenario adds a policy shock that changes the path for the exporter, its competitors, and the importer."
    )

with network_tab:
    st.subheader("Supply-chain dependency map")
    pagerank = {node: value for node, value in nx.pagerank(G, weight="weight").items()}
    network_fig = build_network_figure(G, pagerank)
    st.pyplot(network_fig)

    st.subheader("Dependency ranking")
    st.dataframe(metrics_df, use_container_width=True, hide_index=True)
    st.caption("PageRank highlights the most influential nodes in the trade network, while the vulnerability ranking captures how exposed countries are to shocks transmitted through trade links.")

st.markdown("---")
st.subheader("Data sources and teaching notes")
st.write(
    "The simulator uses a synthetic baseline calibrated to plausible trade patterns and can be upgraded with real data from World Bank Open Data, FRED, IMF, OECD, UN Comtrade, and WTO sources."
)
st.write(
    "For teaching purposes, the app focuses on three macro concepts: tariff incidence, trade diversion, and supply-chain fragility."
)
