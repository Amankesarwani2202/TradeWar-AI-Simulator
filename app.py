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

st.set_page_config(
    page_title="TradeWar AI Simulator",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://github.com/",
        "Report a bug": "https://github.com/",
        "About": "TradeWar AI Simulator v1.0 — Interactive tariff policy simulator",
    },
)

# Custom CSS for enhanced styling
st.markdown(
    """
    <style>
        /* Main container padding */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* Metric styling */
        [data-testid="metric-container"] {
            background-color: #f0f2f6;
            padding: 1.5rem;
            border-radius: 0.5rem;
            border-left: 4px solid #1f77b4;
        }

        /* Info boxes */
        .stInfo, .stSuccess, .stWarning, .stError {
            border-radius: 0.5rem;
            padding: 1.5rem;
            font-size: 0.95rem;
            line-height: 1.6;
        }

        /* Headers */
        h1 {
            color: #0f1419;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        h2 {
            color: #1f2937;
            font-size: 1.75rem;
            font-weight: 600;
            margin-top: 2rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 0.5rem;
        }

        h3 {
            color: #374151;
            font-size: 1.25rem;
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
        }

        /* Sidebar styling */
        .sidebar .sidebar-content {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }

        /* Expander styling */
        .streamlit-expanderHeader {
            font-weight: 600;
            font-size: 1.05rem;
        }

        /* Dataframe styling */
        .stDataFrame {
            border-radius: 0.5rem;
            overflow: hidden;
        }

        /* Dividers */
        hr {
            margin: 2rem 0;
            border: none;
            height: 1px;
            background: linear-gradient(to right, transparent, #e5e7eb, transparent);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

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
    "Vietnam": ["China", "Thailand", "Bangladesh", "India"],
    "India": ["Vietnam", "Bangladesh", "Thailand"],
    "Bangladesh": ["Vietnam", "India", "Thailand"],
    "Thailand": ["Vietnam", "India", "Bangladesh"],
    "Japan": ["South Korea", "Taiwan"],
    "South Korea": ["Japan", "Taiwan"],
    "Taiwan": ["South Korea", "Japan"],
    "EU": ["US", "Japan"],
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

CATEGORY_TRADE_WEIGHTS = {
    "Electronics": 0.30,
    "Semiconductors": 0.20,
    "Machinery": 0.18,
    "Chemicals": 0.12,
    "Textiles": 0.12,
    "Steel": 0.08,
}


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

    cat_weight = CATEGORY_TRADE_WEIGHTS.get(category, 0.15)
    for exporter, importer, value in TRADE_FLOWS:
        weight = value * cat_weight
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


def build_teaching_explanation(scenario, tariff_change_pct, trade_df=None):
    country = scenario["country"]
    category = scenario["category"]
    target_partner = scenario["target_partner"]
    baseline = scenario["baseline_export_bn"]
    predicted = scenario["predicted_export_bn"]
    trade_change = scenario["trade_change_pct"]
    risk = scenario["risk_score"]

    elasticity = abs(TRADE_ELASTICITY.get(category, -0.7))

    concepts = []
    if tariff_change_pct > 0:
        concepts.append("**Price elasticity of demand**")
        main_text = (
            f"A {abs(tariff_change_pct)}% tariff on {country}'s {category} to {target_partner} raises the effective import price. "
            f"This pushes importers toward cheaper alternatives—a shift governed by elasticity of {elasticity:.2f}. "
            f"Expected outcome: {country}'s exports fall from ${baseline:.1f}B to ${predicted:.1f}B ({trade_change:+.1f}%), "
            f"while substitute suppliers (Vietnam, Bangladesh, India, etc.) capture displaced demand."
        )
        if any(alt in scenario.get("likely_beneficiaries", []) for alt in ["Vietnam", "India", "Bangladesh", "Thailand"]):
            concepts.append("**Trade diversion**")
            main_text += f"\n\nWho gains? **Trade diversion** kicks in—importers switch from {country} to alternatives like {', '.join(scenario.get('likely_beneficiaries', [])[:2])}, not because those suppliers are better, but because tariffs made them cheaper."
    elif tariff_change_pct < 0:
        concepts.append("**Comparative advantage**")
        main_text = (
            f"A {abs(tariff_change_pct)}% tariff cut improves {country}'s {category} competitiveness against {target_partner}. "
            f"Lower prices unlock latent demand, boosting exports from ${baseline:.1f}B to ${predicted:.1f}B ({trade_change:+.1f}%). "
            f"This hardens {country}'s position in the {category} market, assuming the cost advantage sticks."
        )
        concepts.append("**Market access**")
        main_text += f"\n\nEconomic insight: removing tariffs reveals {country}'s underlying **comparative advantage** in {category}—cheaper production or better logistics."
    else:
        main_text = (
            f"No tariff shock applied. {country}'s {category} exports remain at ${baseline:.1f}B—market at baseline equilibrium."
        )
        concepts.append("**Equilibrium analysis**")

    context = f"\n\n**Key concepts**: {', '.join(concepts)}. **Risk to trade relationship**: {risk:.0f}/100."
    beginner = f"\n\n**For beginners**: A tariff is a tax on foreign goods. Raise it → foreign sellers become expensive → buyers look elsewhere. Lower it → foreign sellers become cheap → buyers prefer them."

    return main_text + context + beginner


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
    country_profiles = {
        "India": {"population_mn": 1410, "urbanization_pct": 36, "median_age": 28, "gdp_growth": 6.5, "inflation": 4.8, "labor_force_mn": 520, "primary_sector_pct": 15},
        "China": {"population_mn": 1411, "urbanization_pct": 64, "median_age": 39, "gdp_growth": 5.2, "inflation": 2.3, "labor_force_mn": 770, "primary_sector_pct": 18},
        "US": {"population_mn": 335, "urbanization_pct": 83, "median_age": 38, "gdp_growth": 2.5, "inflation": 3.3, "labor_force_mn": 165, "primary_sector_pct": 1},
        "EU": {"population_mn": 447, "urbanization_pct": 75, "median_age": 43, "gdp_growth": 1.4, "inflation": 2.9, "labor_force_mn": 230, "primary_sector_pct": 3},
        "Vietnam": {"population_mn": 99, "urbanization_pct": 37, "median_age": 32, "gdp_growth": 7.0, "inflation": 3.5, "labor_force_mn": 56, "primary_sector_pct": 38},
        "Bangladesh": {"population_mn": 170, "urbanization_pct": 29, "median_age": 28, "gdp_growth": 6.0, "inflation": 5.2, "labor_force_mn": 67, "primary_sector_pct": 42},
        "Japan": {"population_mn": 123, "urbanization_pct": 82, "median_age": 49, "gdp_growth": 1.9, "inflation": 2.5, "labor_force_mn": 75, "primary_sector_pct": 2},
        "South Korea": {"population_mn": 52, "urbanization_pct": 82, "median_age": 42, "gdp_growth": 2.6, "inflation": 2.9, "labor_force_mn": 28, "primary_sector_pct": 4},
        "Taiwan": {"population_mn": 24, "urbanization_pct": 81, "median_age": 42, "gdp_growth": 3.2, "inflation": 2.4, "labor_force_mn": 12, "primary_sector_pct": 5},
        "Thailand": {"population_mn": 71, "urbanization_pct": 52, "median_age": 40, "gdp_growth": 2.5, "inflation": 3.8, "labor_force_mn": 38, "primary_sector_pct": 31},
    }
    profile = country_profiles.get(country, {"population_mn": 100, "urbanization_pct": 60, "median_age": 35, "gdp_growth": 3.0, "inflation": 3.0, "labor_force_mn": 45, "primary_sector_pct": 20})

    market_snapshot = {
        "country": country,
        "ticker": ticker or "NIFTY 50",
        "sentiment": "Stable",
        "volatility": "Moderate",
    }

    if yf is not None and ticker:
        try:
            data = yf.download(ticker, period="2y", progress=False, auto_adjust=True)
            if not data.empty:
                latest = data.iloc[-1]
                market_snapshot["latest_close"] = round(float(latest["Close"]), 2)
                market_snapshot["sentiment"] = "Upward" if data["Close"].iloc[-1] >= data["Close"].iloc[-2] else "Cautious"
                market_snapshot["volatility"] = "High" if data["Close"].pct_change().abs().mean() > 0.02 else "Moderate"
                market_snapshot["yoy_return_pct"] = round((data["Close"].iloc[-1] / data["Close"].iloc[-252] - 1) * 100, 2) if len(data) > 252 else None
        except Exception:
            market_snapshot["latest_close"] = None

    if event_text:
        market_snapshot["policy_event"] = event_text

    return {
        "country": country,
        "market_snapshot": market_snapshot,
        "demographics": profile,
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
st.sidebar.markdown(
    """
    <h2 style="font-size: 1.5rem; color: #1f2937; margin-bottom: 1rem;">⚙️ Policy Scenario</h2>
    """,
    unsafe_allow_html=True,
)

mode = st.sidebar.radio(
    "**Analysis mode**",
    ["Current policy", "Historical counterfactual"],
    help="Choose between simulating current tariff policies or exploring historical what-if scenarios"
)

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
        "India-China electronics dependency shift",
        "India textile tariffs vs Bangladesh/Vietnam",
        "India PLI semiconductor policy vs US tariffs",
        "India-US tech tariff friction (IT services proxy)",
        "India-EU FTA negotiation (chemicals & pharma)",
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
    "India-China electronics dependency shift": {"country": "India", "category": "Electronics", "target_partner": "China", "tariff_change": -18},
    "India textile tariffs vs Bangladesh/Vietnam": {"country": "India", "category": "Textiles", "target_partner": "EU", "tariff_change": 12},
    "India PLI semiconductor policy vs US tariffs": {"country": "India", "category": "Semiconductors", "target_partner": "US", "tariff_change": -15},
    "India-US tech tariff friction (IT services proxy)": {"country": "India", "category": "Machinery", "target_partner": "US", "tariff_change": 10},
    "India-EU FTA negotiation (chemicals & pharma)": {"country": "India", "category": "Chemicals", "target_partner": "EU", "tariff_change": -20},
}

if mode == "Current policy":
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
    is_counterfactual = False

else:  # Historical counterfactual
    counterfactual_events = {
        "1991 India: Faster liberalization pace": {"country": "India", "category": "Textiles", "target_partner": "US", "tariff_change": -25, "year_context": "1991"},
        "1991 India: Delayed liberalization": {"country": "India", "category": "Electronics", "target_partner": "US", "tariff_change": 15, "year_context": "1991"},
        "2020 COVID: Trade stimulus instead of closures": {"country": "Vietnam", "category": "Electronics", "target_partner": "US", "tariff_change": -18, "year_context": "2020"},
        "2008 Financial Crisis: No Chinese tariffs": {"country": "China", "category": "Machinery", "target_partner": "US", "tariff_change": -12, "year_context": "2008"},
        "2016 India Demonetization: Export boost alternative": {"country": "India", "category": "Textiles", "target_partner": "EU", "tariff_change": -20, "year_context": "2016"},
    }
    selected_counterfactual = st.sidebar.selectbox("Pick historical event & alternative decision", list(counterfactual_events.keys()))
    cf_params = counterfactual_events[selected_counterfactual]

    country = cf_params["country"]
    category = cf_params["category"]
    target_partner = cf_params["target_partner"]
    tariff_change = cf_params["tariff_change"]
    forecast_steps = st.sidebar.slider("Forecast horizon (years)", min_value=1, max_value=5, value=3, step=1)
    historical_event = "None"
    shock_pct = 0
    market_ticker = st.sidebar.text_input("Market ticker", value="SPY")
    is_counterfactual = True
    st.sidebar.info(f"📊 **Counterfactual mode**: Showing {selected_counterfactual} with a {tariff_change:+.0f}% policy alternative from {cf_params['year_context']}. This is illustrative, not historical fact.")

# Main app content
if is_counterfactual:
    st.title("🔄 TradeWar Counterfactual Analyzer")
    st.markdown(
        """
        <p style="font-size: 1.1rem; color: #666; margin-top: -1rem; margin-bottom: 1.5rem;">
        Explore how alternative historical decisions would have shaped trade and growth
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.warning("⚠️ **Disclaimer**: This is illustrative analysis based on economic models. Not a validated historical claim. Use for teaching and scenario exploration only.")
else:
    st.title("🌏 TradeWar AI Simulator")
    st.markdown(
        """
        <p style="font-size: 1.1rem; color: #666; margin-top: -1rem; margin-bottom: 1.5rem;">
        Interactive policy simulation for tariff ripple effects across Asian supply chains
        </p>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 0.5rem; color: white; margin-bottom: 2rem;">
    <p style="margin: 0; font-size: 0.95rem; line-height: 1.6;">
    <strong>📊 What this tool does:</strong> Test trade-policy scenarios and see how tariffs can change exports, shift market share, and reshape supply chains across 10 economies. Understand the economic mechanisms driving outcomes through interactive simulations and historical counterfactuals.
    </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_intro1, col_intro2 = st.columns(2)
with col_intro1:
    st.info(
        "📚 **Economic intuition**: Tariffs act like a tax on trade. When barriers rise, exporters often lose market share, alternative suppliers may gain, and consumers face higher costs."
    )
with col_intro2:
    st.success(
        "✨ **How it works**: This tool combines trade elasticity, supply-chain networks, and demographic context to show how policy shocks ripple through interconnected economies."
    )

scenario = build_country_scenario(df, country, category, tariff_change, target_partner, projection_horizon=forecast_steps)
scenario = apply_policy_shock_to_scenario(scenario, historical_event, shock_pct)
scenario_explanation = build_teaching_explanation(scenario, tariff_change, df)
financial_summary = build_financial_summary(country, market_ticker, build_policy_shock_summary(historical_event, shock_pct))

st.markdown("<h3 style='margin-top: 1rem; margin-bottom: 1rem;'>📈 Scenario Summary</h3>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4, gap="medium")

with col1:
    st.metric(
        label="🏭 Affected Exporter",
        value=scenario["country"],
        help="The country whose exports are being analyzed",
    )

with col2:
    st.metric(
        label="📦 Product Category",
        value=scenario["category"],
        help="The trade category affected by the tariff change",
    )

with col3:
    delta_color = "inverse" if scenario['trade_change_pct'] < 0 else "normal"
    st.metric(
        label="📊 Export Change",
        value=f"{scenario['trade_change_pct']:+.1f}%",
        delta=f"${scenario['trade_delta_bn']:+.1f}B",
        delta_color=delta_color,
        help="Predicted change in export value",
    )

with col4:
    risk_level = "🔴 High" if scenario['risk_score'] > 70 else "🟡 Medium" if scenario['risk_score'] > 40 else "🟢 Low"
    st.metric(
        label="⚠️ Trade Stability Risk",
        value=f"{scenario['risk_score']:.0f}/100",
        help=f"Risk to trade relationship: {risk_level}",
    )

st.markdown("<h3 style='margin-top: 2rem; margin-bottom: 1rem;'>📊 Scenario Outcome</h3>", unsafe_allow_html=True)

if historical_event != "None":
    st.info(f"⚙️ **Historical shock context**: {build_policy_shock_summary(historical_event, shock_pct)}")

if tariff_change > 0:
    scenario_text = f"**Tariff increase scenario**: {abs(tariff_change)}% higher tariffs on {country}'s {category} exports to {target_partner}."
    baseline_text = f"${scenario['baseline_export_bn']:.1f}B"
    predicted_text = f"${scenario['predicted_export_bn']:.1f}B"
    emoji = "📉"
    direction = "decreased"
else:
    scenario_text = f"**Tariff reduction scenario**: {abs(tariff_change)}% lower tariffs on {country}'s {category} exports to {target_partner}."
    baseline_text = f"${scenario['baseline_export_bn']:.1f}B"
    predicted_text = f"${scenario['predicted_export_bn']:.1f}B"
    emoji = "📈"
    direction = "increased"

# Create a card-like outcome box
st.markdown(
    f"""
    <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 1.5rem; border-radius: 0.5rem; border-left: 4px solid #667eea;">
    <p style="margin: 0; font-size: 0.95rem;">
    {scenario_text}
    </p>
    <p style="margin: 1rem 0 0 0; font-size: 1.1rem; font-weight: 600;">
    {emoji} Predicted exports: <span style="color: #667eea;">{baseline_text}</span> → <span style="color: #764ba2;">{predicted_text}</span>
    </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("🎓 Economic concepts and teaching explanation", expanded=True):
    st.markdown(scenario_explanation)

st.markdown("<h3 style='margin-top: 1.5rem; margin-bottom: 1rem;'>🎯 Who benefits?</h3>", unsafe_allow_html=True)

col_ben1, col_ben2 = st.columns(2, gap="medium")

with col_ben1:
    if scenario["likely_beneficiaries"]:
        beneficiary_list = ", ".join(scenario["likely_beneficiaries"])
        if tariff_change > 0:
            emoji_ben = "🚀"
            direction_text = "Higher tariffs benefit alternative suppliers"
        else:
            emoji_ben = "🏆"
            direction_text = "Lower tariffs benefit these countries"

        st.markdown(
            f"""
            <div style="background: #f0f9ff; padding: 1.2rem; border-radius: 0.5rem; border-left: 4px solid #06b6d4;">
            <p style="margin: 0; font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">{emoji_ben} {direction_text}</p>
            <p style="margin: 0; font-size: 1.05rem; font-weight: 600; color: #0369a1;">{beneficiary_list}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background: #f3f4f6; padding: 1.2rem; border-radius: 0.5rem; border-left: 4px solid #9ca3af;">
            <p style="margin: 0; font-size: 0.95rem; color: #666;">📊 <strong>No change</strong> — tariff at baseline equilibrium</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

with col_ben2:
    diversion_pool = sum(scenario["trade_diversion"].values())
    if diversion_pool > 0:
        st.markdown(
            f"""
            <div style="background: #fef3c7; padding: 1.2rem; border-radius: 0.5rem; border-left: 4px solid #f59e0b;">
            <p style="margin: 0; font-size: 0.9rem; color: #92400e; margin-bottom: 0.5rem;">💱 Trade diversion pool</p>
            <p style="margin: 0; font-size: 1.3rem; font-weight: 700; color: #d97706;">${diversion_pool:.1f}B</p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem; color: #b45309;">Exports shifting to alternatives</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background: #f3f4f6; padding: 1.2rem; border-radius: 0.5rem; border-left: 4px solid #9ca3af;">
            <p style="margin: 0; font-size: 0.95rem; color: #666;">No trade diversion detected</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Tabs for deeper analysis
overview_tab, forecast_tab, network_tab = st.tabs(["📈 Overview & Impact", "🔮 Forecast & Scenarios", "🕸️ Trade Network"])

with overview_tab:
    st.markdown("<h3 style='margin-bottom: 1rem;'>📊 Country-by-Country Export Impact</h3>", unsafe_allow_html=True)
    impact_df = scenario["impact_df"].copy()

    col_tab1, col_tab2 = st.columns([1, 1.5], gap="large")

    with col_tab1:
        st.markdown("<p style='font-weight: 600; margin-bottom: 0.5rem;'>Data Table</p>", unsafe_allow_html=True)
        display_df = impact_df[["country", "baseline_export_bn", "predicted_export_bn", "change_pct", "change_bn"]].round(2)
        display_df.columns = ["Country", "Baseline ($B)", "Predicted ($B)", "Change %", "Change ($B)"]
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=320,
        )

    with col_tab2:
        st.markdown("<p style='font-weight: 600; margin-bottom: 0.5rem;'>Change by Country</p>", unsafe_allow_html=True)
        fig_bar = px.bar(
            impact_df,
            x="country",
            y="change_bn",
            color="change_bn",
            color_continuous_scale=["#ef4444", "#f3f4f6", "#10b981"],
            color_continuous_midpoint=0,
            title="",
            labels={"country": "Country", "change_bn": "Change (USD Bn)"},
        )
        fig_bar.update_layout(
            template="plotly_white",
            height=320,
            showlegend=False,
            xaxis_title="",
            yaxis_title="Export Change (USD Bn)",
            font=dict(size=11),
            margin=dict(l=0, r=0, t=0, b=50),
        )
        fig_bar.update_traces(textposition="auto", hovertemplate="<b>%{x}</b><br>Change: %{y:.2f}B<extra></extra>")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("<hr style='margin: 2rem 0;'/>", unsafe_allow_html=True)

    winners = impact_df[impact_df["change_bn"] > 0].nlargest(3, "change_bn")
    losers = impact_df[impact_df["change_bn"] < 0].nsmallest(3, "change_bn")

    col_win, col_loss = st.columns(2, gap="medium")

    with col_win:
        if len(winners) > 0:
            winners_text = ", ".join([f"{w} ({w_val:+.1f}B)" for w, w_val in zip(winners["country"], winners["change_bn"])])
            st.markdown(
                f"""
                <div style="background: #d1fae5; padding: 1.2rem; border-radius: 0.5rem; border-left: 4px solid #10b981;">
                <p style="margin: 0; font-size: 0.9rem; color: #047857; margin-bottom: 0.5rem;">🎯 Winners</p>
                <p style="margin: 0; font-size: 0.95rem; color: #065f46; font-weight: 500;">{winners_text}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("No winners in this scenario")

    with col_loss:
        if len(losers) > 0:
            losers_text = ", ".join([f"{l} ({l_val:+.1f}B)" for l, l_val in zip(losers["country"], losers["change_bn"])])
            st.markdown(
                f"""
                <div style="background: #fee2e2; padding: 1.2rem; border-radius: 0.5rem; border-left: 4px solid #ef4444;">
                <p style="margin: 0; font-size: 0.9rem; color: #991b1b; margin-bottom: 0.5rem;">⚠️ Losers</p>
                <p style="margin: 0; font-size: 0.95rem; color: #7f1d1d; font-weight: 500;">{losers_text}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("No losers in this scenario")

with forecast_tab:
    st.markdown("<h3 style='margin-bottom: 1rem;'>📈 Historical Trend and Forecast</h3>", unsafe_allow_html=True)
    forecast_fig = build_forecast_chart(df, country, category, tariff_change, steps=forecast_steps)
    st.plotly_chart(forecast_fig, use_container_width=True, config={"displayModeBar": True})

    col_info1, col_info2 = st.columns([2, 1])
    with col_info1:
        st.markdown(
            f"""
            <div style="background: #eff6ff; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #3b82f6;">
            <p style="margin: 0; font-size: 0.9rem; color: #1e40af;">✓ Tariff scenario applied: <strong>{tariff_change:+.0f}%</strong></p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem; color: #1e3a8a;">🟠 Baseline (orange) → 🟡 Scenario (yellow)</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_info2:
        years_out = forecast_steps
        st.metric("Forecast horizon", f"{years_out} years", help="Time period for prediction")

    st.divider()
    st.subheader("Scenario comparison: What if tariffs went the opposite way?")
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
    st.markdown("<h3 style='margin-bottom: 0.5rem;'>🕸️ Supply-Chain Dependency Map</h3>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <p style="font-size: 0.9rem; color: #666; margin-top: -0.5rem; margin-bottom: 1rem;">
        Network shows how <strong>{country}'s</strong> tariff shock on <strong>{category}</strong> propagates across trade partners.<br>
        📍 <strong>Node size</strong> = influence (PageRank) | <strong>Edge thickness</strong> = trade flow magnitude
        </p>
        """,
        unsafe_allow_html=True,
    )

    scenario_network, scenario_metrics_df, scenario_vulnerability = build_scenario_trade_network(G, country, category, tariff_change, target_partner)
    pagerank = {node: value for node, value in nx.pagerank(scenario_network, weight="weight").items()}
    network_title = f"Scenario-adjusted trade network — {country} ({category}, tariff {tariff_change:+.0f}%)"
    network_fig = build_network_figure(scenario_network, pagerank, title=network_title)
    st.pyplot(network_fig)

    st.divider()
    col_net1, col_net2 = st.columns([1, 1])

    with col_net1:
        st.write("**Network metrics**")
        st.dataframe(scenario_metrics_df, use_container_width=True, hide_index=True)

    with col_net2:
        st.write("**Vulnerability ranking** (who's most exposed?)")
        vuln_df = pd.DataFrame(list(scenario_vulnerability.items()), columns=["Country", "Vulnerability"]).sort_values("Vulnerability", ascending=False)
        st.dataframe(vuln_df, use_container_width=True, hide_index=True)

    st.caption("📖 **Metrics**: PageRank = influence. Import dependency = exposure to shocks. Bridge score = hub position. Vulnerability = composite risk to trade shocks.")

st.markdown("<hr style='margin: 3rem 0 1rem 0;'/>", unsafe_allow_html=True)
st.markdown("<h3 style='margin-bottom: 0.5rem;'>💰 Financial & Demographic Context</h3>", unsafe_allow_html=True)
st.markdown(
    f"""
    <p style="font-size: 0.9rem; color: #666; margin-top: -0.5rem; margin-bottom: 1.5rem;">
    Understanding <strong>{country}'s</strong> economic fundamentals: workforce composition, market structure, and growth trajectory
    </p>
    """,
    unsafe_allow_html=True,
)

fin_tab1, fin_tab2 = st.tabs(["Market & Macro", "Workforce & Structure"])

with fin_tab1:
    col_m1, col_m2, col_m3 = st.columns(3, gap="medium")

    ticker = financial_summary["market_snapshot"]["ticker"]
    sentiment = financial_summary["market_snapshot"]["sentiment"]
    volatility = financial_summary["market_snapshot"]["volatility"]
    yoy = financial_summary['market_snapshot'].get('yoy_return_pct')

    with col_m1:
        st.metric(
            "🏦 Market Ticker",
            ticker,
            delta=f"{yoy}% YoY" if yoy else None,
            help="Primary equity market index or stock"
        )

    with col_m2:
        sentiment_emoji = "📈" if sentiment == "Upward" else "⚠️"
        st.metric(
            "📊 Market Sentiment",
            f"{sentiment_emoji} {sentiment}",
            help="Market direction indicator"
        )

    with col_m3:
        vol_emoji = "🔴" if volatility == "High" else "🟡"
        st.metric(
            "📉 Volatility",
            f"{vol_emoji} {volatility}",
            help="Price volatility level"
        )

    st.markdown("<hr style='margin: 1rem 0;'/>", unsafe_allow_html=True)

    col_m4, col_m5, col_m6 = st.columns(3, gap="medium")

    gdp = financial_summary['demographics'].get('gdp_growth', 0)
    inf = financial_summary['demographics'].get('inflation', 0)
    latest_close = financial_summary['market_snapshot'].get('latest_close')

    with col_m4:
        gdp_emoji = "🚀" if gdp > 5 else "📊" if gdp > 2 else "⚠️"
        st.metric(
            f"{gdp_emoji} GDP Growth",
            f"{gdp:.1f}%",
            help="Annual GDP growth rate"
        )

    with col_m5:
        inf_emoji = "🔥" if inf > 5 else "⚠️" if inf > 3 else "✓"
        st.metric(
            f"{inf_emoji} Inflation",
            f"{inf:.1f}%",
            help="Consumer price inflation rate"
        )

    with col_m6:
        st.metric(
            "💰 Latest Close",
            f"${latest_close}" if latest_close else "N/A",
            help="Latest closing price"
        )

    st.markdown("<h4 style='margin-top: 1.5rem; margin-bottom: 1rem;'>📌 Economic Narrative</h4>", unsafe_allow_html=True)

    if gdp > 5:
        narrative = f"🚀 <strong>{country} is a high-growth economy</strong> ({gdp:.1f}% GDP growth). Tariff shocks may disproportionately impact labor-intensive sectors as rapid workforce expansion creates job sensitivity."
        color = "#dcfce7"
        border_color = "#22c55e"
    elif gdp < 2:
        narrative = f"⚠️ <strong>{country} is a slow-growth economy</strong> ({gdp:.1f}% GDP growth). Tariff cuts could unlock export-led growth; tariff increases risk recession transmission."
        color = "#fee2e2"
        border_color = "#ef4444"
    else:
        narrative = f"📊 <strong>{country} is a moderate-growth economy</strong> ({gdp:.1f}% GDP growth). Tariff impacts will be muted but material for specific sectors."
        color = "#fef3c7"
        border_color = "#f59e0b"

    st.markdown(
        f"""
        <div style="background: {color}; padding: 1.2rem; border-radius: 0.5rem; border-left: 4px solid {border_color};">
        <p style="margin: 0; font-size: 0.95rem; line-height: 1.6;">{narrative}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with fin_tab2:
    col_w1, col_w2, col_w3 = st.columns(3, gap="medium")

    pop = financial_summary['demographics']['population_mn']
    labor = financial_summary['demographics'].get('labor_force_mn', 0)
    age = financial_summary['demographics']['median_age']

    with col_w1:
        st.metric(
            "👥 Population",
            f"{pop:.0f}M",
            help="Total population in millions"
        )

    with col_w2:
        st.metric(
            "💼 Labor Force",
            f"{labor:.0f}M",
            help="Total labor force in millions"
        )

    with col_w3:
        age_emoji = "👴" if age > 42 else "👨" if age > 32 else "👶"
        st.metric(
            f"{age_emoji} Median Age",
            f"{age} yrs",
            help="Median population age"
        )

    st.markdown("<hr style='margin: 1rem 0;'/>", unsafe_allow_html=True)

    col_w4, col_w5 = st.columns(2, gap="medium")

    urban = financial_summary['demographics']['urbanization_pct']
    agri = financial_summary['demographics'].get('primary_sector_pct', 0)

    with col_w4:
        st.metric(
            "🏙️ Urbanization",
            f"{urban}%",
            help="Percentage of population in urban areas"
        )

    with col_w5:
        st.metric(
            "🌾 Agriculture Sector",
            f"{agri:.0f}%",
            help="Employment in primary (agricultural) sector"
        )

    st.markdown("<h4 style='margin-top: 1.5rem; margin-bottom: 1rem;'>⚖️ Demographic Vulnerability to Trade Shocks</h4>", unsafe_allow_html=True)

    if agri > 30:
        agri_text = f"🌾 <strong>High agricultural sector weight</strong> ({agri:.0f}%). Agricultural tariffs → rural job losses → urban migration pressure."
        agri_color = "#fee2e2"
        agri_border = "#ef4444"
    elif agri < 5:
        agri_text = f"✓ <strong>Low agricultural exposure</strong> ({agri:.0f}%). Manufacturing/service tariffs dominate; less rural vulnerability."
        agri_color = "#dcfce7"
        agri_border = "#22c55e"
    else:
        agri_text = f"⚠️ <strong>Moderate ag dependence</strong> ({agri:.0f}%). Balanced trade shock exposure across sectors."
        agri_color = "#fef3c7"
        agri_border = "#f59e0b"

    st.markdown(
        f"""
        <div style="background: {agri_color}; padding: 1.2rem; border-radius: 0.5rem; border-left: 4px solid {agri_border}; margin-bottom: 1rem;">
        <p style="margin: 0; font-size: 0.95rem; line-height: 1.6;">{agri_text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if age > 42:
        age_emoji = "👴"
        age_text = "🔴 <strong>Aging workforce</strong> — Less adaptive to structural job loss; retraining costly; pension pressure rises."
        age_color = "#fee2e2"
        age_border = "#ef4444"
    elif age < 32:
        age_emoji = "👶"
        age_text = "🟢 <strong>Young workforce</strong> — Higher labor supply, faster retraining capacity; youth unemployment sensitive to tariffs."
        age_color = "#dcfce7"
        age_border = "#22c55e"
    else:
        age_emoji = "👨"
        age_text = "🟡 <strong>Working-age population</strong> — Standard trade adjustment trajectory; moderate retraining feasibility."
        age_color = "#fef3c7"
        age_border = "#f59e0b"

    st.markdown(
        f"""
        <div style="background: {age_color}; padding: 1.2rem; border-radius: 0.5rem; border-left: 4px solid {age_border};">
        <p style="margin: 0; font-size: 0.95rem; line-height: 1.6;">{age_text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<hr style='margin: 3rem 0 1rem 0;'/>", unsafe_allow_html=True)
st.markdown("<h3 style='margin-bottom: 1.5rem;'>📚 About This Tool</h3>", unsafe_allow_html=True)

col_about1, col_about2 = st.columns(2, gap="medium")

with col_about1:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #e0e7ff 0%, #f3e8ff 100%); padding: 1.5rem; border-radius: 0.5rem; border-left: 4px solid #8b5cf6;">
        <p style="margin: 0; font-weight: 600; color: #6d28d9; margin-bottom: 0.5rem;">📊 Data & Calibration</p>
        <p style="margin: 0; font-size: 0.9rem; color: #5b21b6; line-height: 1.6;">
        Synthetic baseline calibrated to real 2015–2024 trade patterns. Can upgrade with World Bank, IMF, OECD, UN Comtrade, WTO data. yfinance integration for live market tickers.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_about2:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #dbeafe 0%, #ddd6fe 100%); padding: 1.5rem; border-radius: 0.5rem; border-left: 4px solid #3b82f6;">
        <p style="margin: 0; font-weight: 600; color: #1e40af; margin-bottom: 0.5rem;">🎓 Teaching Focus</p>
        <p style="margin: 0; font-size: 0.9rem; color: #1e3a8a; line-height: 1.6;">
        Three core concepts: (1) Tariff incidence & elasticity, (2) Trade diversion & comparative advantage, (3) Supply-chain fragility & demographic vulnerability.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<hr style='margin: 1.5rem 0;'/>", unsafe_allow_html=True)

col_footer1, col_footer2 = st.columns(2, gap="medium")

with col_footer1:
    st.markdown(
        """
        <div style="padding: 1rem; text-align: center;">
        <p style="margin: 0; font-size: 0.9rem; color: #666;">
        <strong>🎓 For educators</strong><br/>
        Designed for teaching trade economics, supply-chain analysis, and policy simulation. All scenarios are illustrative.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_footer2:
    st.markdown(
        """
        <div style="padding: 1rem; text-align: center;">
        <p style="margin: 0; font-size: 0.9rem; color: #666;">
        <strong>💡 For learners</strong><br/>
        Adjust the tariff slider to see how policy shocks ripple through interconnected economies.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div style="text-align: center; padding: 2rem 0; border-top: 1px solid #e5e7eb; margin-top: 2rem;">
    <p style="margin: 0; font-size: 0.8rem; color: #9ca3af;">
    <strong>TradeWar AI Simulator v1.0</strong> | Built with Streamlit | Data: Synthetic + yfinance<br/>
    <a href="https://github.com/" style="color: #3b82f6; text-decoration: none;">GitHub</a> ·
    <a href="https://github.com/" style="color: #3b82f6; text-decoration: none;">Docs</a> ·
    <a href="https://github.com/" style="color: #3b82f6; text-decoration: none;">Report Issue</a>
    </p>
    </div>
    """,
    unsafe_allow_html=True,
)
