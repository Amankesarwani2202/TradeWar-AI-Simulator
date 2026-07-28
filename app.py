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

try:
    import yfinance as yf
except Exception:  # pragma: no cover - optional dependency
    yf = None

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


def build_scenario_trade_network(base_graph, country, category, tariff_change_pct, target_partner):
    g = nx.DiGraph()
    for node in base_graph.nodes():
        g.add_node(node)

    alternatives = ALTERNATIVE_SUPPLIERS.get(country, [])
    elasticity = abs(TRADE_ELASTICITY.get(category, -0.7))
    magnitude = min(0.35, 0.12 + elasticity * 0.09)

    if tariff_change_pct > 0:
        exporter_mult = 1 - magnitude
        alternative_mult = 1 + magnitude * 0.65
        partner_mult = 1 + magnitude * 0.35
    elif tariff_change_pct < 0:
        exporter_mult = 1 + magnitude * 0.45
        alternative_mult = 1 - magnitude * 0.35
        partner_mult = 1 - magnitude * 0.2
    else:
        exporter_mult = 1.0
        alternative_mult = 1.0
        partner_mult = 1.0

    for exporter, importer, value in TRADE_FLOWS:
        weight = value
        if exporter == country:
            if importer == target_partner:
                weight *= exporter_mult
            elif importer in alternatives:
                weight *= alternative_mult
        if exporter in alternatives and importer == target_partner:
            weight *= partner_mult
        elif tariff_change_pct != 0:
            weight *= 1 + (tariff_change_pct / 100) * 0.03
        g.add_edge(exporter, importer, weight=max(5.0, round(weight, 2)), label=f"${round(weight, 1)}B")

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


def build_country_scenario(df, country, category, tariff_change_pct, target_partner, projection_horizon=3):
    elasticity = TRADE_ELASTICITY.get(category, -0.7)
    base_export = float(
        df[(df["country"] == country) & (df["category"] == category) & (df["year"] == 2024)]["export_value_bn_usd"].sum()
    )
    trade_change_pct = elasticity * tariff_change_pct
    trade_change_pct = float(np.clip(trade_change_pct, -40.0, 30.0))

    horizon_effect = 1 + (projection_horizon - 1) * 0.08
    horizon_adjustment = 1 + (trade_change_pct / 100) * horizon_effect
    new_export = base_export * horizon_adjustment
    delta = new_export - base_export

    alternatives = ALTERNATIVE_SUPPLIERS.get(country, [])
    impact_rows = []
    for other_country in COUNTRIES:
        baseline = float(
            df[(df["country"] == other_country) & (df["category"] == category) & (df["year"] == 2024)]["export_value_bn_usd"].sum()
        )
        if other_country == country:
            pct = trade_change_pct * horizon_effect
            predicted_export = baseline * (1 + pct / 100)
        elif other_country in alternatives:
            pct = -0.35 * trade_change_pct * horizon_effect
            predicted_export = baseline * (1 + pct / 100)
        elif other_country == target_partner:
            pct = 0.15 * abs(trade_change_pct) * horizon_effect if tariff_change_pct > 0 else -0.05 * abs(trade_change_pct) * horizon_effect
            predicted_export = baseline * (1 + pct / 100)
        else:
            pct = 0.05 * trade_change_pct * horizon_effect
            predicted_export = baseline * (1 + pct / 100)
        impact_rows.append(
            {
                "country": other_country,
                "baseline_export_bn": round(baseline, 2),
                "predicted_export_bn": round(predicted_export, 2),
                "change_pct": round(pct, 2),
                "change_bn": round(predicted_export - baseline, 2),
            }
        )

    impact_df = pd.DataFrame(impact_rows).sort_values("change_bn", ascending=False)

    if tariff_change_pct > 0:
        diversion_values = {alt: round(abs(delta) / max(len(alternatives), 1) * 0.6, 2) for alt in alternatives}
        likely_beneficiaries = [country for country, value in sorted(diversion_values.items(), key=lambda item: item[1], reverse=True)[:3]]
    elif tariff_change_pct < 0:
        gainers = [country, target_partner]
        diversion_values = {name: round(abs(delta) / max(len(gainers), 1) * 0.4, 2) for name in gainers}
        likely_beneficiaries = [name for name, value in sorted(diversion_values.items(), key=lambda item: item[1], reverse=True)[:3]]
    else:
        diversion_values = {}
        likely_beneficiaries = []

    return {
        "country": country,
        "category": category,
        "target_partner": target_partner,
        "baseline_export_bn": round(base_export, 2),
        "predicted_export_bn": round(new_export, 2),
        "trade_change_pct": round(trade_change_pct, 2),
        "trade_delta_bn": round(delta, 2),
        "risk_score": round(min(100.0, abs(trade_change_pct) * 1.6 + 12), 1),
        "trade_diversion": diversion_values,
        "likely_beneficiaries": likely_beneficiaries,
        "impact_df": impact_df,
        "projection_horizon": projection_horizon,
    }


def build_teaching_explanation(scenario, tariff_change_pct):
    country = scenario["country"]
    category = scenario["category"]
    target_partner = scenario["target_partner"]
    elasticity = abs(scenario["trade_change_pct"]) / max(abs(tariff_change_pct), 1)
    direction = "increase" if tariff_change_pct > 0 else "cut" if tariff_change_pct < 0 else "no change"
    if tariff_change_pct > 0:
        main_text = (
            f"This scenario applies the economic idea of price elasticity of trade. A tariff {direction} on {country}'s {category} exports to {target_partner} raises the effective price of the product, so importers buy less and look for alternative suppliers. "
            f"That is why the model predicts weaker exports for {country}, stronger gains for substitute exporters, and a higher risk score for the trade relationship. "
            f"The size of the effect is guided by an elasticity of about {elasticity:.2f}."
        )
    elif tariff_change_pct < 0:
        main_text = (
            f"This scenario applies the same elasticity logic in reverse. A tariff {direction} lowers the price wedge for {country}'s {category} exports to {target_partner}, making the product more competitive and increasing demand. "
            f"That is why the model predicts export gains for {country} and weaker relative benefits for alternative suppliers, with the size of the effect driven by the elasticity assumption. "
            f"The magnitude is guided by an elasticity of about {elasticity:.2f}."
        )
    else:
        main_text = (
            f"This scenario uses the elasticity of trade as a teaching benchmark. With {direction}, the model expects the market to stay close to its baseline path because prices and quantities are not being pushed by a policy shock."
        )

    takeaway = (
        "Teaching takeaway: higher trade barriers usually reduce competitiveness, while lower barriers typically improve export performance and market access."
    )
    beginner_version = (
        "Beginner version: when a tariff goes up, trade becomes more expensive; when it goes down, trade becomes easier and cheaper."
    )
    return f"{main_text}\n\n{takeaway}\n\n{beginner_version}"


def build_forecast_chart(df, country, category, tariff_change_pct, steps=3):
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
    baseline_forecast_vals = forecast_series(series, steps=steps)
    elasticity = abs(TRADE_ELASTICITY.get(category, -0.7))
    scenario_factor = 1 + (tariff_change_pct / 100) * max(0.45, elasticity * 0.75)
    scenario_forecast_vals = np.maximum(0, baseline_forecast_vals * scenario_factor)
    future_years = list(range(2025, 2025 + steps))
    forecast_df = pd.DataFrame({"year": future_years, "baseline_forecast": baseline_forecast_vals, "scenario_forecast": scenario_forecast_vals})

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist_df["year"], y=hist_df["export_value_bn_usd"], mode="lines+markers", name="Historical", line=dict(color="#00d4ff", width=3)))
    fig.add_trace(go.Scatter(x=forecast_df["year"], y=forecast_df["baseline_forecast"], mode="lines+markers", name="Baseline forecast", line=dict(color="#ff6b35", width=3, dash="dash")))
    fig.add_trace(go.Scatter(x=forecast_df["year"], y=forecast_df["scenario_forecast"], mode="lines+markers", name="Scenario-adjusted forecast", line=dict(color="#ffd166", width=3)))
    fig.add_annotation(
        x=0.02,
        y=0.98,
        xref="paper",
        yref="paper",
        text=f"Tariff shock: {tariff_change_pct:+.0f}%",
        showarrow=False,
        bgcolor="rgba(0,0,0,0.45)",
        borderpad=4,
        font=dict(color="white"),
    )
    fig.update_layout(
        title=f"Historical and Forecasted Exports — {country} | {category}",
        xaxis_title="Year",
        yaxis_title="Export Value (USD Bn)",
        template="plotly_dark",
        height=360,
    )
    return fig


def build_network_figure(g, pagerank, title="Trade Dependency Network"):
    fig, ax = plt.subplots(figsize=(10, 7))
    pos = nx.spring_layout(g, seed=42, k=1.4)
    node_sizes = [pagerank[n] * 60000 for n in g.nodes()]
    edge_weights = [g[u][v]["weight"] for u, v in g.edges()]
    max_w = max(edge_weights) if edge_weights else 1
    edge_widths = [w / max_w * 4 for w in edge_weights]

    nx.draw_networkx_nodes(g, pos, node_size=node_sizes, node_color=list(pagerank.values()), cmap=cm.plasma, alpha=0.95, ax=ax)
    nx.draw_networkx_edges(g, pos, width=edge_widths, edge_color="#aaaaaa", alpha=0.6, arrows=True, arrowsize=15, connectionstyle="arc3,rad=0.08", ax=ax)
    nx.draw_networkx_labels(g, pos, font_size=9, font_color="white", ax=ax)
    ax.set_title(title, fontsize=13)
    ax.axis("off")
    plt.tight_layout()
    return fig


def build_financial_summary(country, ticker, event_text=None):
    market_snapshot = {
        "country": country,
        "ticker": ticker or "NIFTY 50",
        "sentiment": "Stable",
        "volatility": "Moderate",
    }

    demographics = {
        "population_mn": 1410 if country == "India" else 1340,
        "urbanization_pct": 36 if country == "India" else 83,
        "median_age": 28 if country == "India" else 39,
    }

    country_profiles = {
        "India": {"population_mn": 1410, "urbanization_pct": 36, "median_age": 28, "gdp_growth": 6.5, "inflation": 4.8},
        "China": {"population_mn": 1411, "urbanization_pct": 64, "median_age": 39, "gdp_growth": 5.2, "inflation": 2.3},
        "US": {"population_mn": 335, "urbanization_pct": 83, "median_age": 38, "gdp_growth": 2.5, "inflation": 3.3},
        "EU": {"population_mn": 447, "urbanization_pct": 75, "median_age": 43, "gdp_growth": 1.4, "inflation": 2.9},
    }
    profile = country_profiles.get(country, {"population_mn": 100, "urbanization_pct": 60, "median_age": 35, "gdp_growth": 3.0, "inflation": 3.0})
    demographics.update(profile)

    if yf is not None and ticker:
        try:
            data = yf.download(ticker, period="2y", progress=False, auto_adjust=True)
            if not data.empty:
                latest = data.iloc[-1]
                market_snapshot["latest_close"] = round(float(latest["Close"]), 2)
                market_snapshot["sentiment"] = "Upward" if data["Close"].iloc[-1] >= data["Close"].iloc[-2] else "Cautious"
                market_snapshot["volatility"] = "High" if data["Close"].pct_change().abs().mean() > 0.02 else "Moderate"
        except Exception:
            market_snapshot["latest_close"] = None

    if event_text:
        market_snapshot["policy_event"] = event_text

    return {
        "country": country,
        "market_snapshot": market_snapshot,
        "demographics": demographics,
    }


def build_policy_shock_summary(event_name, shock_pct):
    if not event_name or event_name == "None":
        return "No historical policy shock selected."
    return (
        f"Historical scenario: {event_name}. A {shock_pct:+.0f}% shock is applied to the selected country's trade and financial outlook, which changes the forecast path and the dependency map."
    )


def apply_policy_shock_to_scenario(scenario, event_name, shock_pct):
    if not event_name or event_name == "None":
        return scenario

    base = float(scenario["predicted_export_bn"])
    if event_name == "Post-9/11 US financial stabilization":
        adjustment = 1 + (shock_pct / 100) * 0.35
    elif event_name == "COVID-19 trade disruption":
        adjustment = 1 - abs(shock_pct / 100) * 0.40
    elif event_name == "India 2016 demonetization shock":
        adjustment = 1 - abs(shock_pct / 100) * 0.25
    else:
        adjustment = 1 + (shock_pct / 100) * 0.15

    scenario["predicted_export_bn"] = round(base * adjustment, 2)
    scenario["trade_delta_bn"] = round(scenario["predicted_export_bn"] - scenario["baseline_export_bn"], 2)
    scenario["risk_score"] = round(min(100.0, scenario["risk_score"] + abs(shock_pct) * 0.7), 1)
    scenario["policy_shock"] = event_name
    scenario["shock_pct"] = shock_pct
    return scenario


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
        "India tariff relief on textiles",
        "India export support for electronics",
        "India semiconductor supply shock",
        "Post-9/11 US financial shock",
    ],
)

preset_map = {
    "Custom": {"country": "China", "category": "Electronics", "target_partner": "US", "tariff_change": 25},
    "US tariffs on China electronics": {"country": "China", "category": "Electronics", "target_partner": "US", "tariff_change": 25},
    "EU tariffs on Vietnam textiles": {"country": "Vietnam", "category": "Textiles", "target_partner": "EU", "tariff_change": 15},
    "US tariffs on India semiconductors": {"country": "India", "category": "Semiconductors", "target_partner": "US", "tariff_change": 20},
    "India tariff relief on textiles": {"country": "India", "category": "Textiles", "target_partner": "EU", "tariff_change": -12},
    "India export support for electronics": {"country": "India", "category": "Electronics", "target_partner": "US", "tariff_change": -8},
    "India semiconductor supply shock": {"country": "India", "category": "Semiconductors", "target_partner": "US", "tariff_change": 14},
    "Post-9/11 US financial shock": {"country": "US", "category": "Machinery", "target_partner": "EU", "tariff_change": 8},
}

selected = preset_map[preset]
country = st.sidebar.selectbox("Affected exporter", COUNTRIES, index=COUNTRIES.index(selected["country"]))
category = st.sidebar.selectbox("Product category", CATEGORIES, index=CATEGORIES.index(selected["category"]))
target_partner = st.sidebar.selectbox("Policy actor", ["US", "EU", "China", "Japan", "South Korea"], index=["US", "EU", "China", "Japan", "South Korea"].index(selected["target_partner"]))
tariff_change = st.sidebar.slider("Tariff change (%)", min_value=-30, max_value=30, value=selected["tariff_change"], step=1)
forecast_steps = st.sidebar.slider("Forecast horizon (years)", min_value=1, max_value=5, value=3, step=1)
historical_event = st.sidebar.selectbox(
    "Historical policy shock",
    ["None", "Post-9/11 US financial stabilization", "COVID-19 trade disruption", "India 2016 demonetization shock"],
)
shock_pct = st.sidebar.slider("Historical shock intensity (%)", min_value=-20, max_value=20, value=5, step=1)
market_ticker = st.sidebar.text_input("Market ticker for financial view", value="SPY")

# Main app content
st.title("🌏 TradeWar AI Simulator")
st.caption("Interactive policy simulation for tariff ripple effects across Asian supply chains")

st.markdown(
    "This dashboard lets users test trade-policy scenarios and see how tariffs can change exports, shift market share, and reshape supply chains across 10 economies."
)

st.info(
    "Economic intuition: tariffs act like a tax on trade. When barriers rise, exporters often lose market share, alternative suppliers may gain, and downstream consumers usually face higher costs."
)

scenario = build_country_scenario(df, country, category, tariff_change, target_partner, projection_horizon=forecast_steps)
scenario = apply_policy_shock_to_scenario(scenario, historical_event, shock_pct)
scenario_explanation = build_teaching_explanation(scenario, tariff_change)
financial_summary = build_financial_summary(country, market_ticker, build_policy_shock_summary(historical_event, shock_pct))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Affected exporter", scenario["country"])
col2.metric("Category", scenario["category"])
col3.metric("Predicted export change", f"{scenario['trade_change_pct']:+.1f}%")
col4.metric("Risk score", f"{scenario['risk_score']:.0f}/100")

st.subheader("Scenario outcome")
st.caption(build_policy_shock_summary(historical_event, shock_pct))

scenario_text = (
    f"A {abs(tariff_change)}% tariff change on {country}'s {category} trade with {target_partner} is expected to move exports from {scenario['baseline_export_bn']:.1f}B to {scenario['predicted_export_bn']:.1f}B."
    if tariff_change > 0
    else f"A {abs(tariff_change)}% tariff reduction on {country}'s {category} trade with {target_partner} could lift exports from {scenario['baseline_export_bn']:.1f}B to {scenario['predicted_export_bn']:.1f}B."
)
st.write(scenario_text)
st.write("Teaching explanation:")
st.info(scenario_explanation)

if scenario["likely_beneficiaries"]:
    if tariff_change > 0:
        st.write(f"Likely beneficiaries: {', '.join(scenario['likely_beneficiaries'])}")
    elif tariff_change < 0:
        st.write(f"Likely beneficiaries: {', '.join(scenario['likely_beneficiaries'])}")

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
    forecast_fig = build_forecast_chart(df, country, category, tariff_change, steps=forecast_steps)
    st.plotly_chart(forecast_fig, use_container_width=True)

    st.subheader("Tariff-up vs tariff-down comparison")
    comparison_df = pd.DataFrame({
        "year": list(range(2025, 2025 + forecast_steps)),
        "baseline": forecast_fig.data[1].y if len(forecast_fig.data) > 1 else [None] * forecast_steps,
        "current_scenario": forecast_fig.data[2].y if len(forecast_fig.data) > 2 else [None] * forecast_steps,
    })
    if tariff_change > 0:
        alt_tariff = -abs(tariff_change)
    else:
        alt_tariff = abs(tariff_change)
    alt_factor = 1 + (alt_tariff / 100) * max(0.45, abs(TRADE_ELASTICITY.get(category, -0.7)) * 0.75)
    base_series = forecast_fig.data[1].y if len(forecast_fig.data) > 1 else [None] * forecast_steps
    alt_series = [max(0.0, value * alt_factor) for value in base_series]
    comparison_df["alternate_scenario"] = alt_series
    comparison_fig = go.Figure()
    comparison_fig.add_trace(go.Scatter(x=comparison_df["year"], y=comparison_df["baseline"], mode="lines+markers", name="Baseline", line=dict(color="#ff6b35", width=3)))
    comparison_fig.add_trace(go.Scatter(x=comparison_df["year"], y=comparison_df["current_scenario"], mode="lines+markers", name="Current tariff", line=dict(color="#ffd166", width=3)))
    comparison_fig.add_trace(go.Scatter(x=comparison_df["year"], y=comparison_df["alternate_scenario"], mode="lines+markers", name="Opposite tariff", line=dict(color="#00d4ff", width=3, dash="dash")))
    comparison_fig.update_layout(
        title=f"Forecast comparison for {country} | {category}",
        xaxis_title="Year",
        yaxis_title="Export Value (USD Bn)",
        template="plotly_dark",
        height=360,
    )
    st.plotly_chart(comparison_fig, use_container_width=True)

    st.subheader("How the scenario changes the story")
    st.write(
        "The chart above shows how the selected exporter has moved historically and where a simple statistical forecast suggests the next few years may head. The scenario adds a policy shock that changes the path for the exporter, its competitors, and the importer."
    )

with network_tab:
    st.subheader("Supply-chain dependency map")
    scenario_network, scenario_metrics_df, scenario_vulnerability = build_scenario_trade_network(G, country, category, tariff_change, target_partner)
    pagerank = {node: value for node, value in nx.pagerank(scenario_network, weight="weight").items()}
    network_title = f"Scenario-adjusted dependency map — {country} | {category} | tariff {tariff_change:+.0f}%"
    network_fig = build_network_figure(scenario_network, pagerank, title=network_title)
    st.pyplot(network_fig)

    st.subheader("Dependency ranking")
    st.dataframe(scenario_metrics_df, use_container_width=True, hide_index=True)
    st.caption("PageRank highlights the most influential nodes in the trade network, while the vulnerability ranking captures how exposed countries are to shocks transmitted through trade links.")

st.markdown("---")
st.subheader("Financial and demographic snapshot")
col_fin1, col_fin2, col_fin3 = st.columns(3)
col_fin1.metric("Country", financial_summary["country"])
col_fin2.metric("Market ticker", financial_summary["market_snapshot"]["ticker"])
col_fin3.metric("Market sentiment", financial_summary["market_snapshot"]["sentiment"])
st.write(f"Latest market close: {financial_summary['market_snapshot'].get('latest_close', 'N/A')}")
st.write(f"Population (mn): {financial_summary['demographics']['population_mn']}")
st.write(f"Urbanization (%): {financial_summary['demographics']['urbanization_pct']}")
st.write(f"Median age: {financial_summary['demographics']['median_age']}")

st.markdown("---")
st.subheader("Data sources and teaching notes")
st.write(
    "The simulator uses a synthetic baseline calibrated to plausible trade patterns and can be upgraded with real data from World Bank Open Data, FRED, IMF, OECD, UN Comtrade, and WTO sources."
)
st.write(
    "For teaching purposes, the app focuses on three macro concepts: tariff incidence, trade diversion, and supply-chain fragility."
)
