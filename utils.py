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
except Exception:
    yf = None

COUNTRIES = ["China", "India", "Vietnam", "Bangladesh", "Thailand", "South Korea", "Taiwan", "Japan", "EU", "US"]
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
    ("China", "US", 500), ("China", "EU", 400), ("China", "Japan", 170),
    ("China", "South Korea", 160), ("China", "India", 100), ("China", "Vietnam", 80),
    ("Vietnam", "US", 110), ("Vietnam", "EU", 50), ("Vietnam", "China", 70),
    ("Vietnam", "Japan", 25), ("India", "US", 80), ("India", "EU", 65),
    ("India", "China", 20), ("South Korea", "China", 150), ("South Korea", "US", 80),
    ("Taiwan", "China", 180), ("Taiwan", "US", 100), ("Japan", "US", 150),
    ("Japan", "China", 160), ("Japan", "EU", 80), ("US", "EU", 350),
    ("US", "Japan", 80), ("US", "China", 150), ("Bangladesh", "EU", 20),
    ("Bangladesh", "US", 10), ("Thailand", "US", 45), ("Thailand", "China", 40),
    ("Thailand", "EU", 30),
]

CATEGORY_TRADE_WEIGHTS = {
    "Electronics": 0.30, "Semiconductors": 0.20, "Machinery": 0.18,
    "Chemicals": 0.12, "Textiles": 0.12, "Steel": 0.08,
}

# Category-specific bilateral trade multipliers — makes network metrics change by category
CATEGORY_BILATERAL_MULTIPLIERS = {
    "Electronics": {
        ("China", "US"): 3.5, ("China", "EU"): 2.8, ("China", "Japan"): 2.0,
        ("China", "South Korea"): 1.8, ("Vietnam", "US"): 4.5, ("Vietnam", "EU"): 2.5,
        ("Vietnam", "Japan"): 2.0, ("South Korea", "US"): 2.8, ("Taiwan", "US"): 3.0,
        ("Taiwan", "China"): 2.5, ("Japan", "US"): 2.2, ("India", "US"): 1.8,
    },
    "Textiles": {
        ("Bangladesh", "EU"): 14.0, ("Bangladesh", "US"): 12.0,
        ("Vietnam", "US"): 7.0, ("Vietnam", "EU"): 5.5,
        ("India", "EU"): 4.5, ("India", "US"): 4.0,
        ("China", "US"): 2.0, ("China", "EU"): 2.0,
        ("Thailand", "US"): 2.5, ("Thailand", "EU"): 2.0,
    },
    "Semiconductors": {
        ("Taiwan", "US"): 10.0, ("Taiwan", "China"): 8.0,
        ("South Korea", "China"): 6.0, ("South Korea", "US"): 5.5,
        ("Japan", "US"): 3.5, ("China", "US"): 3.0,
        ("China", "South Korea"): 2.5, ("China", "Japan"): 2.0,
        ("US", "China"): 2.0,
    },
    "Machinery": {
        ("EU", "US"): 4.5, ("EU", "Japan"): 2.5, ("EU", "China"): 3.0,
        ("Japan", "US"): 4.0, ("Japan", "China"): 3.5,
        ("US", "EU"): 3.5, ("US", "Japan"): 2.5,
        ("China", "US"): 2.0, ("South Korea", "US"): 2.0,
    },
    "Chemicals": {
        ("EU", "US"): 4.0, ("EU", "Japan"): 2.5,
        ("US", "EU"): 3.5, ("Japan", "US"): 2.5,
        ("China", "India"): 5.0, ("China", "US"): 2.0,
        ("India", "US"): 3.5, ("India", "EU"): 3.0,
        ("China", "EU"): 2.5,
    },
    "Steel": {
        ("China", "EU"): 3.5, ("China", "India"): 4.5, ("China", "US"): 3.0,
        ("China", "Japan"): 2.5, ("China", "South Korea"): 2.5,
        ("South Korea", "US"): 4.0, ("Japan", "US"): 3.5,
        ("EU", "US"): 2.0, ("Taiwan", "US"): 2.0,
    },
}

COUNTRY_PROFILES = {
    "India": {
        "population_mn": 1410, "urbanization_pct": 36, "median_age": 28,
        "gdp_growth": 6.5, "inflation": 4.8, "labor_force_mn": 520,
        "primary_sector_pct": 43, "secondary_sector_pct": 25,
        "tertiary_sector_pct": 28, "quaternary_sector_pct": 4,
        "currency": "INR", "currency_vs_usd": 83.5,
        "stock_index": "NIFTY 50", "stock_ticker": "^NSEI", "market_cap_bn": 4200,
        "age_distribution": {"0-14": 26, "15-29": 27, "30-44": 22, "45-59": 15, "60+": 10},
        "news": [
            "India's manufacturing PMI hits 3-month high on export demand",
            "RBI holds interest rates steady amid inflation concerns",
            "India-US trade talks advance; electronics tariffs under review",
        ],
    },
    "China": {
        "population_mn": 1411, "urbanization_pct": 64, "median_age": 39,
        "gdp_growth": 5.2, "inflation": 2.3, "labor_force_mn": 770,
        "primary_sector_pct": 23, "secondary_sector_pct": 39,
        "tertiary_sector_pct": 33, "quaternary_sector_pct": 5,
        "currency": "CNY", "currency_vs_usd": 7.24,
        "stock_index": "SSE Composite", "stock_ticker": "000001.SS", "market_cap_bn": 9800,
        "age_distribution": {"0-14": 17, "15-29": 19, "30-44": 22, "45-59": 22, "60+": 20},
        "news": [
            "China's semiconductor exports face new US restrictions",
            "PBOC cuts reserve requirements to stimulate growth",
            "China's export growth slows amid global trade tensions",
        ],
    },
    "US": {
        "population_mn": 335, "urbanization_pct": 83, "median_age": 38,
        "gdp_growth": 2.5, "inflation": 3.3, "labor_force_mn": 165,
        "primary_sector_pct": 1, "secondary_sector_pct": 19,
        "tertiary_sector_pct": 69, "quaternary_sector_pct": 11,
        "currency": "USD", "currency_vs_usd": 1.0,
        "stock_index": "S&P 500", "stock_ticker": "SPY", "market_cap_bn": 42000,
        "age_distribution": {"0-14": 18, "15-29": 20, "30-44": 20, "45-59": 19, "60+": 23},
        "news": [
            "Fed signals potential rate cuts amid cooling inflation",
            "US-China trade deficit narrows on tariff effects",
            "Congress debates new tariff framework for semiconductor imports",
        ],
    },
    "EU": {
        "population_mn": 447, "urbanization_pct": 75, "median_age": 43,
        "gdp_growth": 1.4, "inflation": 2.9, "labor_force_mn": 230,
        "primary_sector_pct": 4, "secondary_sector_pct": 25,
        "tertiary_sector_pct": 63, "quaternary_sector_pct": 8,
        "currency": "EUR", "currency_vs_usd": 0.92,
        "stock_index": "Euro Stoxx 50", "stock_ticker": "^STOXX50E", "market_cap_bn": 11000,
        "age_distribution": {"0-14": 15, "15-29": 17, "30-44": 21, "45-59": 22, "60+": 25},
        "news": [
            "EU announces new carbon border adjustment mechanism details",
            "ECB maintains cautious stance on rate cuts",
            "EU-India FTA negotiations accelerate on textiles and chemicals",
        ],
    },
    "Vietnam": {
        "population_mn": 99, "urbanization_pct": 37, "median_age": 32,
        "gdp_growth": 7.0, "inflation": 3.5, "labor_force_mn": 56,
        "primary_sector_pct": 38, "secondary_sector_pct": 34,
        "tertiary_sector_pct": 25, "quaternary_sector_pct": 3,
        "currency": "VND", "currency_vs_usd": 24500,
        "stock_index": "VN-Index", "stock_ticker": "^VNINDEX", "market_cap_bn": 260,
        "age_distribution": {"0-14": 23, "15-29": 26, "30-44": 25, "45-59": 17, "60+": 9},
        "news": [
            "Vietnam attracts record FDI in electronics manufacturing",
            "SBV intervenes to stabilize VND amid dollar strength",
            "Vietnam's textile exports surge as China faces US tariffs",
        ],
    },
    "Bangladesh": {
        "population_mn": 170, "urbanization_pct": 29, "median_age": 28,
        "gdp_growth": 6.0, "inflation": 5.2, "labor_force_mn": 67,
        "primary_sector_pct": 42, "secondary_sector_pct": 28,
        "tertiary_sector_pct": 27, "quaternary_sector_pct": 3,
        "currency": "BDT", "currency_vs_usd": 110,
        "stock_index": "DSEX", "stock_ticker": "DSEX.BD", "market_cap_bn": 45,
        "age_distribution": {"0-14": 28, "15-29": 29, "30-44": 22, "45-59": 13, "60+": 8},
        "news": [
            "Bangladesh garment exports hit record high on China supply diversion",
            "Bangladesh Bank raises rates to curb inflation pressures",
            "RMG sector demands infrastructure investment to sustain growth",
        ],
    },
    "Japan": {
        "population_mn": 123, "urbanization_pct": 82, "median_age": 49,
        "gdp_growth": 1.9, "inflation": 2.5, "labor_force_mn": 75,
        "primary_sector_pct": 2, "secondary_sector_pct": 24,
        "tertiary_sector_pct": 67, "quaternary_sector_pct": 7,
        "currency": "JPY", "currency_vs_usd": 149,
        "stock_index": "Nikkei 225", "stock_ticker": "^N225", "market_cap_bn": 6400,
        "age_distribution": {"0-14": 12, "15-29": 14, "30-44": 19, "45-59": 22, "60+": 33},
        "news": [
            "BOJ signals gradual exit from ultra-loose monetary policy",
            "Japan's tech exports face headwinds from China slowdown",
            "Japan and South Korea deepen semiconductor supply chain ties",
        ],
    },
    "South Korea": {
        "population_mn": 52, "urbanization_pct": 82, "median_age": 42,
        "gdp_growth": 2.6, "inflation": 2.9, "labor_force_mn": 28,
        "primary_sector_pct": 4, "secondary_sector_pct": 32,
        "tertiary_sector_pct": 57, "quaternary_sector_pct": 7,
        "currency": "KRW", "currency_vs_usd": 1320,
        "stock_index": "KOSPI", "stock_ticker": "^KS11", "market_cap_bn": 1600,
        "age_distribution": {"0-14": 12, "15-29": 16, "30-44": 22, "45-59": 24, "60+": 26},
        "news": [
            "Samsung expands chip production amid global semiconductor demand",
            "BOK holds rate steady as economy shows signs of recovery",
            "South Korea's exports rebound on semiconductor shipments",
        ],
    },
    "Taiwan": {
        "population_mn": 24, "urbanization_pct": 81, "median_age": 42,
        "gdp_growth": 3.2, "inflation": 2.4, "labor_force_mn": 12,
        "primary_sector_pct": 5, "secondary_sector_pct": 36,
        "tertiary_sector_pct": 53, "quaternary_sector_pct": 6,
        "currency": "TWD", "currency_vs_usd": 31.8,
        "stock_index": "TAIEX", "stock_ticker": "^TWII", "market_cap_bn": 1800,
        "age_distribution": {"0-14": 13, "15-29": 17, "30-44": 22, "45-59": 24, "60+": 24},
        "news": [
            "TSMC announces new fab investment amid US incentives",
            "Taiwan's export orders surge on AI chip demand",
            "CBC maintains forex intervention to curb TWD appreciation",
        ],
    },
    "Thailand": {
        "population_mn": 71, "urbanization_pct": 52, "median_age": 40,
        "gdp_growth": 2.5, "inflation": 3.8, "labor_force_mn": 38,
        "primary_sector_pct": 31, "secondary_sector_pct": 35,
        "tertiary_sector_pct": 30, "quaternary_sector_pct": 4,
        "currency": "THB", "currency_vs_usd": 35.5,
        "stock_index": "SET Index", "stock_ticker": "^SET.BK", "market_cap_bn": 500,
        "age_distribution": {"0-14": 17, "15-29": 19, "30-44": 25, "45-59": 23, "60+": 16},
        "news": [
            "Thailand's auto exports face headwinds from EV transition",
            "BOT cuts rates to boost sluggish economic growth",
            "Tourism recovery drives services sector expansion in Thailand",
        ],
    },
}


def inject_css():
    st.markdown(
        """
        <style>
            .main .block-container { padding-top: 2rem; padding-bottom: 2rem; padding-left: 2rem; padding-right: 2rem; }
            [data-testid="metric-container"] { background-color: #f0f2f6; padding: 1.5rem; border-radius: 0.5rem; border-left: 4px solid #1f77b4; }
            .stInfo, .stSuccess, .stWarning, .stError { border-radius: 0.5rem; padding: 1.5rem; font-size: 0.95rem; line-height: 1.6; }
            h1 { color: #0f1419; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem; }
            h2 { color: #1f2937; font-size: 1.75rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem; }
            h3 { color: #374151; font-size: 1.25rem; font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.75rem; }
            .streamlit-expanderHeader { font-weight: 600; font-size: 1.05rem; }
            .stDataFrame { border-radius: 0.5rem; overflow: hidden; }
            hr { margin: 2rem 0; border: none; height: 1px; background: linear-gradient(to right, transparent, #e5e7eb, transparent); }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def generate_trade_data():
    records = []
    base_exports = {
        "China": 2500, "India": 450, "Vietnam": 280, "Bangladesh": 45,
        "Thailand": 250, "South Korea": 600, "Taiwan": 380, "Japan": 700,
        "EU": 2200, "US": 1600,
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
                export_val = base * CATEGORY_TRADE_WEIGHTS[category] * growth * shock * covid * np.random.uniform(0.93, 1.07)
                tariff_rate = np.random.uniform(2, 8)
                if year >= 2018 and exporter == "China" and category in ["Electronics", "Semiconductors"]:
                    tariff_rate = np.random.uniform(20, 25)
                records.append({
                    "year": year, "country": exporter, "category": category,
                    "export_value_bn_usd": round(export_val, 2),
                    "tariff_rate_pct": round(tariff_rate, 2),
                    "gdp_growth_pct": round(np.random.uniform(2, 8), 2),
                    "inflation_pct": round(np.random.uniform(1, 6), 2),
                    "manufacturing_reliance": round(np.random.uniform(0.2, 0.7), 2),
                    "shipping_dependency": round(np.random.uniform(0.3, 0.9), 2),
                })
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
    metrics_df = pd.DataFrame({
        "country": COUNTRIES,
        "pagerank": [round(pagerank.get(c, 0), 4) for c in COUNTRIES],
        "import_dependency": [round(in_centrality.get(c, 0), 4) for c in COUNTRIES],
        "export_reach": [round(out_centrality.get(c, 0), 4) for c in COUNTRIES],
        "bridge_score": [round(betweenness.get(c, 0), 4) for c in COUNTRIES],
    }).sort_values("pagerank", ascending=False)
    vulnerability = {}
    for node in g.nodes():
        import_dep = sum(g[u][node]["weight"] for u in g.predecessors(node) if g.has_edge(u, node))
        vulnerability[node] = round(
            (import_dep / 1000) * 0.5 + betweenness.get(node, 0) * 100 * 0.3 + pagerank.get(node, 0) * 10 * 0.2, 3
        )
    vulnerability = dict(sorted(vulnerability.items(), key=lambda item: -item[1]))
    return g, metrics_df, vulnerability


def build_scenario_trade_network(base_graph, country, category, tariff_change_pct, target_partner):
    """
    Build a scenario-adjusted trade network.
    Uses category-specific bilateral multipliers so that network metrics
    (import_dependency, export_reach, bridge_score) change meaningfully
    when switching categories.
    """
    g = nx.DiGraph()
    for node in base_graph.nodes():
        g.add_node(node)

    alternatives = ALTERNATIVE_SUPPLIERS.get(country, [])
    elasticity = abs(TRADE_ELASTICITY.get(category, -0.7))
    magnitude = min(0.40, 0.10 + elasticity * 0.12)

    # Tariff increase: exporter loses, alternatives gain at target partner
    # Tariff decrease: exporter gains, alternatives lose at target partner
    if tariff_change_pct > 0:
        exporter_mult = 1 - magnitude
        alt_at_target_mult = 1 + magnitude * 0.70   # alternatives grab share at target_partner
        ripple_mult = 0.98
    elif tariff_change_pct < 0:
        exporter_mult = 1 + magnitude * 0.50
        alt_at_target_mult = 1 - magnitude * 0.30   # alternatives lose some share
        ripple_mult = 1.01
    else:
        exporter_mult = alt_at_target_mult = ripple_mult = 1.0

    bilateral_mults = CATEGORY_BILATERAL_MULTIPLIERS.get(category, {})
    cat_weight = CATEGORY_TRADE_WEIGHTS.get(category, 0.15)

    for exporter, importer, base_value in TRADE_FLOWS:
        bilateral_key = (exporter, importer)
        bilateral_mult = bilateral_mults.get(bilateral_key, 1.0)
        weight = base_value * cat_weight * bilateral_mult

        if exporter == country and importer == target_partner:
            # The directly affected trade route
            weight *= exporter_mult
        elif exporter in alternatives and importer == target_partner:
            # Alternatives gaining/losing share at target_partner
            weight *= alt_at_target_mult
        else:
            # Everything else: small global ripple
            weight *= ripple_mult

        g.add_edge(exporter, importer, weight=max(1.0, round(weight, 2)))

    pagerank = nx.pagerank(g, weight="weight")
    in_centrality = nx.in_degree_centrality(g)
    out_centrality = nx.out_degree_centrality(g)
    betweenness = nx.betweenness_centrality(g, weight="weight")

    metrics_df = pd.DataFrame({
        "country": COUNTRIES,
        "pagerank": [round(pagerank.get(c, 0), 4) for c in COUNTRIES],
        "import_dependency": [round(in_centrality.get(c, 0), 4) for c in COUNTRIES],
        "export_reach": [round(out_centrality.get(c, 0), 4) for c in COUNTRIES],
        "bridge_score": [round(betweenness.get(c, 0), 4) for c in COUNTRIES],
    }).sort_values("pagerank", ascending=False)

    vulnerability = {}
    for node in g.nodes():
        import_dep = sum(g[u][node]["weight"] for u in g.predecessors(node) if g.has_edge(u, node))
        vulnerability[node] = round(
            (import_dep / 1000) * 0.5 + betweenness.get(node, 0) * 100 * 0.3 + pagerank.get(node, 0) * 10 * 0.2, 3
        )
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
        coeffs = np.polyfit(x, series, 1)
        return np.array([coeffs[1] + coeffs[0] * (len(series) + i) for i in range(steps)])


def build_country_scenario(df, country, category, tariff_change_pct, target_partner, projection_horizon=3):
    elasticity = TRADE_ELASTICITY.get(category, -0.7)  # negative value
    base_export = float(
        df[(df["country"] == country) & (df["category"] == category) & (df["year"] == 2024)]["export_value_bn_usd"].sum()
    )
    # trade_change_pct: negative elasticity × positive tariff = negative export change ✓
    trade_change_pct = float(np.clip(elasticity * tariff_change_pct, -45.0, 35.0))
    horizon_effect = 1 + (projection_horizon - 1) * 0.08
    new_export = base_export * (1 + (trade_change_pct / 100) * horizon_effect)
    delta = new_export - base_export
    alternatives = ALTERNATIVE_SUPPLIERS.get(country, [])
    impact_rows = []
    for other_country in COUNTRIES:
        baseline = float(
            df[(df["country"] == other_country) & (df["category"] == category) & (df["year"] == 2024)]["export_value_bn_usd"].sum()
        )
        if other_country == country:
            pct = trade_change_pct * horizon_effect
        elif other_country in alternatives:
            # Alternatives gain when country loses (tariff increase), lose when country gains
            pct = -0.40 * trade_change_pct * horizon_effect
        elif other_country == target_partner:
            pct = (0.12 * abs(trade_change_pct) * horizon_effect if tariff_change_pct > 0
                   else -0.05 * abs(trade_change_pct) * horizon_effect)
        else:
            pct = 0.04 * trade_change_pct * horizon_effect
        predicted_export = baseline * (1 + pct / 100)
        impact_rows.append({
            "country": other_country,
            "baseline_export_bn": round(baseline, 2),
            "predicted_export_bn": round(predicted_export, 2),
            "change_pct": round(pct, 2),
            "change_bn": round(predicted_export - baseline, 2),
        })
    impact_df = pd.DataFrame(impact_rows).sort_values("change_bn", ascending=False)

    # Beneficiary logic: only show if diversion is economically significant (> $0.5B)
    DIVERSION_THRESHOLD = 0.5
    if tariff_change_pct > 0:
        # Tariff increase: alternative suppliers divert trade away from country
        diversion_per_alt = abs(delta) / max(len(alternatives), 1) * 0.65
        diversion_values = {
            alt: round(diversion_per_alt, 2) for alt in alternatives
            if diversion_per_alt > DIVERSION_THRESHOLD
        }
        likely_beneficiaries = sorted(diversion_values, key=diversion_values.get, reverse=True)[:3]
        beneficiary_type = "diversion"  # who captures the diverted trade
    elif tariff_change_pct < 0:
        # Tariff decrease: exporter gains, and target_partner's consumers benefit
        gain_per = abs(delta) / 2 * 0.45
        gainers = {}
        if gain_per > DIVERSION_THRESHOLD:
            gainers[country] = round(gain_per, 2)
        if target_partner != country and gain_per * 0.4 > DIVERSION_THRESHOLD:
            gainers[target_partner] = round(gain_per * 0.4, 2)
        diversion_values = gainers
        likely_beneficiaries = sorted(gainers, key=gainers.get, reverse=True)[:3]
        beneficiary_type = "gain"  # who gains from lower tariffs
    else:
        diversion_values, likely_beneficiaries = {}, []
        beneficiary_type = "none"

    return {
        "country": country, "category": category, "target_partner": target_partner,
        "baseline_export_bn": round(base_export, 2), "predicted_export_bn": round(new_export, 2),
        "trade_change_pct": round(trade_change_pct, 2), "trade_delta_bn": round(delta, 2),
        "risk_score": round(min(100.0, abs(trade_change_pct) * 1.6 + 12), 1),
        "trade_diversion": diversion_values, "likely_beneficiaries": likely_beneficiaries,
        "beneficiary_type": beneficiary_type,
        "impact_df": impact_df, "projection_horizon": projection_horizon,
    }


def build_teaching_explanation(scenario, tariff_change_pct):
    """
    Returns a structured dict with clear educational sections.
    Renders as a rich multi-section teaching panel.
    """
    country = scenario["country"]
    category = scenario["category"]
    target_partner = scenario["target_partner"]
    baseline = scenario["baseline_export_bn"]
    predicted = scenario["predicted_export_bn"]
    trade_change = scenario["trade_change_pct"]
    risk = scenario["risk_score"]
    elasticity_val = TRADE_ELASTICITY.get(category, -0.7)
    abs_e = abs(elasticity_val)
    beneficiaries = scenario.get("likely_beneficiaries", [])
    b_type = scenario.get("beneficiary_type", "none")

    if tariff_change_pct > 0:
        concept = "Price Elasticity of Demand + Trade Diversion"
        concept_def = (
            "**Price elasticity of demand** measures how much demand falls when price rises. "
            "**Trade diversion** occurs when buyers switch from a now-expensive supplier to a cheaper alternative — "
            "the trade is diverted, not destroyed."
        )
        mechanism = (
            f"**Step 1 — The tariff acts as a price increase:**\n"
            f"{target_partner} imposes a **+{abs(tariff_change_pct):.0f}% tariff** on {country}'s {category} imports. "
            f"This makes {country}'s {category} **{abs(tariff_change_pct):.0f}% more expensive** in {target_partner}'s market.\n\n"
            f"**Step 2 — Buyers respond to the price signal:**\n"
            f"The price elasticity for {category} is **{abs_e:.1f}**. "
            f"This means: for every 1% price increase, demand falls by {abs_e:.1f}%. "
            f"Result: a {abs(tariff_change_pct):.0f}% price rise → **{abs(trade_change):.1f}% drop** in {country}'s exports.\n\n"
            f"**Step 3 — Trade diversion begins:**\n"
            f"{target_partner}'s importers still need {category}. "
            f"They switch to the next-cheapest supplier{f': **{chr(44).join(beneficiaries[:2])}**' if beneficiaries else ''}. "
            f"This is **trade diversion** — same volume of trade, different supplier."
        )
        numbers = (
            f"- {country}'s {category} exports: **${baseline:.1f}B → ${predicted:.1f}B** ({trade_change:+.1f}%)\n"
            f"- Estimated displaced trade: **${abs(scenario['trade_delta_bn']):.1f}B**\n"
            f"- Elasticity applied: **{abs_e:.1f}** (sensitivity of demand to the price shock)\n"
            f"- Risk to trade relationship: **{risk:.0f}/100**"
        )
        wider = (
            f"- **{country}** loses export revenue — jobs in the {category} sector face pressure\n"
            f"- **{target_partner}** consumers and firms pay higher prices (tariff cost is passed on)\n"
            f"- **{', '.join(beneficiaries) if beneficiaries else 'Alternative suppliers'}** may capture diverted market share\n"
            f"- **Global trade efficiency falls** — trade routes through more expensive alternatives are less optimal"
        )
        beginner = (
            f"**The coffee shop analogy:**\n"
            f"Imagine you always buy coffee from your favourite café (= {country}). "
            f"Your government adds a {abs(tariff_change_pct)}% 'café tax'. "
            f"Now the café is too expensive, so you switch to a supermarket chain (= {beneficiaries[0] if beneficiaries else 'an alternative'}). "
            f"The café loses your business. The supermarket gains it. Your government collects the tax — "
            f"but *you* pay it through higher prices. **The targeted country is not always the biggest loser — sometimes it's the consumer at home.**"
        )
        key_terms = {
            "Tariff": "A tax imposed on imported goods, raising their price in the domestic market.",
            "Price elasticity": f"How much demand changes per 1% price change. {category} elasticity = {abs_e:.1f}.",
            "Trade diversion": "Trade shifting from one supplier to another because of relative price changes caused by tariffs.",
            "Deadweight loss": "The economic efficiency lost when tariffs prevent mutually beneficial trade from occurring.",
        }

    elif tariff_change_pct < 0:
        concept = "Comparative Advantage + Market Access"
        concept_def = (
            "**Comparative advantage** means producing something at lower relative cost than others. "
            "**Market access** determines whether that advantage can be translated into actual export revenue."
        )
        mechanism = (
            f"**Step 1 — The tariff reduction opens the door:**\n"
            f"{target_partner} cuts tariffs on {country}'s {category} by **{abs(tariff_change_pct):.0f}%**. "
            f"This makes {country}'s {category} cheaper in {target_partner}'s market by the same amount.\n\n"
            f"**Step 2 — {country}'s comparative advantage is revealed:**\n"
            f"At the lower effective price, {country} can now compete. "
            f"With elasticity **{abs_e:.1f}**, a {abs(tariff_change_pct):.0f}% price cut → approximately **{abs(trade_change):.1f}% more exports**.\n\n"
            f"**Step 3 — Competing suppliers adjust:**\n"
            f"As {country} captures more of {target_partner}'s market, "
            f"existing suppliers lose some share. This is the **competitive adjustment** from improved market access."
        )
        numbers = (
            f"- {country}'s {category} exports: **${baseline:.1f}B → ${predicted:.1f}B** ({trade_change:+.1f}%)\n"
            f"- Additional export revenue: **${abs(scenario['trade_delta_bn']):.1f}B**\n"
            f"- Elasticity applied: **{abs_e:.1f}** (how demand responds to the cheaper price)\n"
            f"- Risk to trade relationship: **{risk:.0f}/100** (lower = healthier relationship)"
        )
        wider = (
            f"- **{country}** gains export revenue and may see job creation in {category}\n"
            f"- **{target_partner}** consumers pay less for {category} — real income effect\n"
            f"- **Alternative suppliers** of {category} lose some {target_partner} market share\n"
            f"- **Global trade efficiency improves** — more trade flows through the most competitive supplier"
        )
        beginner = (
            f"**The talented tailor analogy:**\n"
            f"Imagine a skilled tailor in {country} who was kept out of your market by high entry fees (= tariffs). "
            f"By removing the fee, they can now compete — and their quality/price wins customers. "
            f"The other tailors (existing suppliers) lose some business. Your consumers pay less. "
            f"**Lower tariffs usually benefit importing countries** through cheaper goods — even if domestic producers face more competition."
        )
        key_terms = {
            "Comparative advantage": f"{country}'s ability to produce {category} at lower relative cost than others.",
            "Market access": "The degree to which exporters can enter foreign markets without prohibitive barriers.",
            "Trade creation": "New trade that emerges when a tariff barrier is removed, allowing the most efficient supplier to serve the market.",
            "Terms of trade": "The ratio of a country's export prices to import prices — tariff reductions can improve this for importers.",
        }

    else:
        concept = "Baseline Equilibrium"
        concept_def = "**Market equilibrium** is the state where supply and demand balance with no external shocks. At zero tariff change, the current trade pattern persists unchanged."
        mechanism = (
            f"No tariff shock applied. {country}'s {category} exports remain on their current trajectory of **${baseline:.1f}B**. "
            f"The elasticity of **{abs_e:.1f}** is not triggered — no price signal for buyers to respond to."
        )
        numbers = (
            f"- {country}'s exports: **${baseline:.1f}B** (unchanged)\n"
            f"- No trade diversion expected\n"
            f"- Risk level: **{risk:.0f}/100** (baseline)"
        )
        wider = "No significant change expected. The market continues on its current trend."
        beginner = "**No tariff change means no trade shock.** The market continues as before. Use the tariff slider in the sidebar to see what happens when policy changes."
        key_terms = {
            "Equilibrium": "The state where the quantity supplied equals the quantity demanded at the current price — no incentive to change.",
            "Baseline forecast": "The projected export path assuming no new policy interventions.",
        }

    return {
        "concept": concept,
        "concept_def": concept_def,
        "mechanism": mechanism,
        "numbers": numbers,
        "wider": wider,
        "beginner": beginner,
        "key_terms": key_terms,
    }


def render_teaching_panel(teaching):
    """Renders the structured teaching explanation as a multi-section panel."""
    st.markdown(
        f'<div style="background:#eff6ff;padding:1rem 1.25rem;border-radius:0.5rem;border-left:4px solid #2563eb;margin-bottom:1rem;">'
        f'<p style="margin:0;color:#1e40af;font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;">Economics Teaching Corner</p>'
        f'<p style="margin:0.2rem 0 0 0;color:#1e3a8a;font-size:0.98rem;font-weight:700;">{teaching["concept"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(teaching["concept_def"])

    col_mech, col_nums = st.columns([3, 2], gap="large")
    with col_mech:
        st.markdown("**🔍 Why is this happening? (Step-by-step mechanism)**")
        st.markdown(teaching["mechanism"])
    with col_nums:
        st.markdown("**📊 What the numbers mean**")
        st.markdown(teaching["numbers"])
        st.markdown("**🌍 Wider trade impact**")
        st.markdown(teaching["wider"])

    with st.expander("💡 Simple explanation (no economics background needed)", expanded=False):
        st.markdown(teaching["beginner"])

    with st.expander("📖 Key terms glossary", expanded=False):
        for term, definition in teaching["key_terms"].items():
            st.markdown(f"**{term}**: {definition}")


def build_forecast_chart(df, country, category, tariff_change_pct, steps=3):
    """
    FIX: Use signed elasticity so tariff increase → forecast below baseline,
    tariff decrease → forecast above baseline.
    """
    series = (
        df[(df["country"] == country) & (df["category"] == category)]
        .sort_values("year")["export_value_bn_usd"].values
    )
    hist_df = (
        df[(df["country"] == country) & (df["category"] == category)]
        .sort_values("year")[["year", "export_value_bn_usd"]].copy()
    )
    baseline_forecast_vals = forecast_series(series, steps=steps)

    # Correct sign: negative elasticity × positive tariff = negative trade response
    elasticity = TRADE_ELASTICITY.get(category, -0.7)  # keep negative
    trade_response_pct = elasticity * tariff_change_pct  # e.g., -0.8 × 25 = -20%
    scenario_factor = max(0.05, 1 + trade_response_pct / 100)
    scenario_forecast_vals = np.maximum(0, baseline_forecast_vals * scenario_factor)

    future_years = list(range(2025, 2025 + steps))
    forecast_df = pd.DataFrame({
        "year": future_years,
        "baseline_forecast": baseline_forecast_vals,
        "scenario_forecast": scenario_forecast_vals,
    })

    direction_label = "↓ Tariff raises price → exports fall" if tariff_change_pct > 0 else "↑ Tariff cut → exports rise" if tariff_change_pct < 0 else "No change"
    annotation_text = f"Tariff: {tariff_change_pct:+.0f}% | {direction_label}"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist_df["year"], y=hist_df["export_value_bn_usd"],
        mode="lines+markers", name="Historical",
        line=dict(color="#00d4ff", width=3),
        hovertemplate="<b>%{x}</b><br>Actual: $%{y:.2f}B<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=forecast_df["year"], y=forecast_df["baseline_forecast"],
        mode="lines+markers", name="Baseline forecast (no policy change)",
        line=dict(color="#ff6b35", width=3, dash="dash"),
        hovertemplate="<b>%{x}</b><br>Baseline: $%{y:.2f}B<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=forecast_df["year"], y=forecast_df["scenario_forecast"],
        mode="lines+markers", name=f"Policy scenario ({tariff_change_pct:+.0f}% tariff)",
        line=dict(color="#ffd166", width=3),
        hovertemplate="<b>%{x}</b><br>Scenario: $%{y:.2f}B<extra></extra>",
    ))
    fig.add_vline(x=2024.5, line_dash="dot", line_color="rgba(255,255,255,0.3)", annotation_text="Forecast starts")
    fig.add_annotation(
        x=0.02, y=0.96, xref="paper", yref="paper",
        text=annotation_text, showarrow=False,
        bgcolor="rgba(30,27,75,0.85)", borderpad=6, bordercolor="#818cf8",
        font=dict(color="white", size=11),
    )
    fig.update_layout(
        title=f"Export Trajectory — {country} | {category}",
        xaxis_title="Year", yaxis_title="Export Value (USD Billion)",
        template="plotly_dark", height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig, baseline_forecast_vals, scenario_forecast_vals


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


def build_policy_shock_summary(event_name, shock_pct):
    if not event_name or event_name == "None":
        return "No historical policy shock selected."
    return f"Historical scenario: {event_name}. A {shock_pct:+.0f}% shock is applied to the trade outlook."


def render_scenario_summary_metrics(scenario):
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    with col1:
        st.metric(
            "🏭 Exporter (affected)",
            scenario["country"],
            help="The country whose exports are modelled. This is who the tariff is imposed ON.",
        )
    with col2:
        st.metric(
            "📦 Product category",
            scenario["category"],
            help="The type of goods being taxed by the tariff.",
        )
    with col3:
        delta_color = "inverse" if scenario["trade_change_pct"] < 0 else "normal"
        st.metric(
            "📊 Predicted export change",
            f"{scenario['trade_change_pct']:+.1f}%",
            delta=f"${scenario['trade_delta_bn']:+.1f}B",
            delta_color=delta_color,
            help="Estimated change in the exporter's annual exports due to this tariff policy.",
        )
    with col4:
        risk_level = "🔴 High" if scenario["risk_score"] > 70 else "🟡 Medium" if scenario["risk_score"] > 40 else "🟢 Low"
        st.metric(
            "⚠️ Trade disruption risk",
            f"{scenario['risk_score']:.0f}/100",
            help=f"Composite risk to the bilateral trade relationship. {risk_level}",
        )


def render_overview_tab(scenario, impact_df):
    st.markdown("<h3 style='margin-bottom:0.5rem;'>📊 How each economy is affected</h3>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#6b7280;font-size:0.9rem;margin-bottom:1rem;'>"
        "Green bars = economies that gain exports in this scenario. Red bars = economies that lose. "
        "Magnitudes reflect elasticity, market share, and supply-chain proximity."
        "</p>",
        unsafe_allow_html=True,
    )
    col_tab1, col_tab2 = st.columns([1, 1.5], gap="large")
    with col_tab1:
        display_df = impact_df[["country", "baseline_export_bn", "predicted_export_bn", "change_pct", "change_bn"]].round(2).copy()
        display_df.columns = ["Country", "Baseline ($B)", "Predicted ($B)", "Change (%)", "Change ($B)"]
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=340)
    with col_tab2:
        fig_bar = px.bar(
            impact_df, x="country", y="change_bn", color="change_bn",
            color_continuous_scale=["#ef4444", "#f3f4f6", "#10b981"], color_continuous_midpoint=0,
            labels={"country": "Country", "change_bn": "Change (USD Bn)"},
        )
        fig_bar.update_layout(
            template="plotly_white", height=340, showlegend=False,
            xaxis_title="", yaxis_title="Export Change (USD Billion)",
            font=dict(size=11), margin=dict(l=0, r=0, t=10, b=50),
        )
        fig_bar.update_traces(hovertemplate="<b>%{x}</b><br>Change: $%{y:.2f}B<extra></extra>")
        st.plotly_chart(fig_bar, use_container_width=True, key="overview_impact_bar")

    st.markdown("<hr style='margin:1.5rem 0;'/>", unsafe_allow_html=True)
    winners = impact_df[impact_df["change_bn"] > 0].nlargest(3, "change_bn")
    losers = impact_df[impact_df["change_bn"] < 0].nsmallest(3, "change_bn")
    col_win, col_loss = st.columns(2, gap="medium")
    with col_win:
        if len(winners) > 0:
            winners_text = " · ".join([f"{w} ({v:+.1f}B)" for w, v in zip(winners["country"], winners["change_bn"])])
            st.markdown(
                f'<div style="background:#d1fae5;padding:1.2rem;border-radius:0.5rem;border-left:4px solid #10b981;">'
                f'<p style="margin:0;font-size:0.85rem;color:#047857;margin-bottom:0.3rem;font-weight:600;">🎯 Net gainers in this scenario</p>'
                f'<p style="margin:0;font-size:0.9rem;color:#065f46;">{winners_text}</p>'
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("No net gainers in this scenario")
    with col_loss:
        if len(losers) > 0:
            losers_text = " · ".join([f"{l} ({v:+.1f}B)" for l, v in zip(losers["country"], losers["change_bn"])])
            st.markdown(
                f'<div style="background:#fee2e2;padding:1.2rem;border-radius:0.5rem;border-left:4px solid #ef4444;">'
                f'<p style="margin:0;font-size:0.85rem;color:#991b1b;margin-bottom:0.3rem;font-weight:600;">⚠️ Net losers in this scenario</p>'
                f'<p style="margin:0;font-size:0.9rem;color:#7f1d1d;">{losers_text}</p>'
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("No net losers in this scenario")


def render_forecast_tab(df, country, category, tariff_change, forecast_steps):
    st.markdown("<h3 style='margin-bottom:0.5rem;'>📈 Export Trajectory: Historical + Forecast</h3>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#6b7280;font-size:0.9rem;margin-bottom:1rem;'>"
        "Blue = actual historical exports. Orange dashed = where exports go with no new policy. "
        "Yellow = where exports go under the tariff scenario you set."
        "</p>",
        unsafe_allow_html=True,
    )
    forecast_fig, baseline_vals, scenario_vals = build_forecast_chart(df, country, category, tariff_change, steps=forecast_steps)
    st.plotly_chart(forecast_fig, use_container_width=True, config={"displayModeBar": True}, key="forecast_main_chart")

    col_info1, col_info2, col_info3 = st.columns(3, gap="medium")
    direction = "↓ Tariff increase suppresses exports" if tariff_change > 0 else "↑ Tariff cut boosts exports" if tariff_change < 0 else "No change from baseline"
    color = "#fee2e2" if tariff_change > 0 else "#d1fae5" if tariff_change < 0 else "#f3f4f6"
    border = "#ef4444" if tariff_change > 0 else "#10b981" if tariff_change < 0 else "#9ca3af"
    with col_info1:
        st.markdown(
            f'<div style="background:{color};padding:1rem;border-radius:0.5rem;border-left:4px solid {border};">'
            f'<p style="margin:0;font-size:0.85rem;font-weight:600;">{direction}</p>'
            f'<p style="margin:0.25rem 0 0 0;font-size:0.8rem;color:#6b7280;">Tariff applied: {tariff_change:+.0f}%</p>'
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_info2:
        if len(baseline_vals) > 0 and len(scenario_vals) > 0:
            gap = scenario_vals[-1] - baseline_vals[-1]
            st.metric(f"Gap vs baseline in yr {forecast_steps}", f"${gap:+.2f}B", delta=f"${gap:+.2f}B", delta_color="normal" if gap >= 0 else "inverse")
    with col_info3:
        st.metric("Forecast horizon", f"{forecast_steps} year{'s' if forecast_steps > 1 else ''}")

    st.divider()
    st.subheader("What if the tariff went the other direction?")
    st.markdown("*Comparison showing the counterfactual: what if the opposite policy had been chosen.*")
    alt_tariff = -abs(tariff_change) if tariff_change > 0 else abs(tariff_change)
    _, alt_baseline_vals, alt_scenario_vals = build_forecast_chart(df, country, category, alt_tariff, steps=forecast_steps)
    future_years = list(range(2025, 2025 + forecast_steps))
    comparison_fig = go.Figure()
    comparison_fig.add_trace(go.Scatter(x=future_years, y=baseline_vals, mode="lines+markers", name="Baseline (no change)", line=dict(color="#ff6b35", width=3, dash="dash")))
    comparison_fig.add_trace(go.Scatter(x=future_years, y=scenario_vals, mode="lines+markers", name=f"Current scenario ({tariff_change:+.0f}%)", line=dict(color="#ffd166", width=3)))
    comparison_fig.add_trace(go.Scatter(x=future_years, y=alt_scenario_vals, mode="lines+markers", name=f"Opposite scenario ({alt_tariff:+.0f}%)", line=dict(color="#00d4ff", width=3, dash="dot")))
    comparison_fig.update_layout(title=f"Policy direction comparison — {country} | {category}", xaxis_title="Year", yaxis_title="Export Value (USD Billion)", template="plotly_dark", height=380, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(comparison_fig, use_container_width=True, key="forecast_comparison_chart")


def render_network_tab(G, country, category, tariff_change, target_partner):
    st.markdown("<h3 style='margin-bottom:0.5rem;'>🕸️ Supply-Chain Dependency Map</h3>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='font-size:0.9rem;color:#6b7280;margin-bottom:1rem;'>"
        f"This network is recalculated for the <strong>{category}</strong> category specifically — "
        f"node sizes and edge thickness reflect <strong>{category}</strong> trade flows, not overall trade. "
        f"Metrics change as you switch categories or adjust the tariff."
        f"</p>",
        unsafe_allow_html=True,
    )

    scenario_network, scenario_metrics_df, scenario_vulnerability = build_scenario_trade_network(
        G, country, category, tariff_change, target_partner
    )
    pagerank = nx.pagerank(scenario_network, weight="weight")
    network_fig = build_network_figure(
        scenario_network, pagerank,
        title=f"{category} trade network — {country} ({tariff_change:+.0f}% tariff to {target_partner})",
    )
    st.pyplot(network_fig)
    plt.close()

    st.divider()
    col_net1, col_net2 = st.columns(2)
    with col_net1:
        st.markdown("**Network metrics** *(category-specific)*")
        st.caption("PageRank = influence hub | Import dependency = exposure | Export reach = seller spread | Bridge score = bottleneck risk")
        st.dataframe(scenario_metrics_df, use_container_width=True, hide_index=True)
    with col_net2:
        st.markdown("**Vulnerability ranking** — who is most exposed to shocks?")
        st.caption("Higher score = more exposed to supply chain disruptions in this category")
        vuln_df = pd.DataFrame(
            list(scenario_vulnerability.items()), columns=["Country", "Vulnerability"]
        ).sort_values("Vulnerability", ascending=False)
        st.dataframe(vuln_df, use_container_width=True, hide_index=True)

    with st.expander("🎓 How to read this network", expanded=False):
        st.markdown(
            """
            **PageRank** (node size): Borrowed from Google. In trade, high PageRank = a country that receives imports from many other important economies. These are demand hubs — disrupting them has outsized effects.

            **Import dependency**: How many inbound trade routes does this country have? High = relies on many sources; Low = relies on few (concentrated risk).

            **Export reach**: How many markets does this country supply? High = diversified export base; Low = concentrated in few destinations.

            **Bridge score (betweenness centrality)**: Does this country sit on many shortest paths between other countries? High bridge score = a bottleneck. Disrupting a high-bridge country breaks supply routes across the entire network.

            **Why does this change by category?** Because different products have completely different supply chains:
            - **Semiconductors**: Taiwan and South Korea dominate — very concentrated network.
            - **Textiles**: Bangladesh and Vietnam are central — different structure entirely.
            - **Machinery**: EU and Japan are the hubs — another distinct topology.

            Switching categories essentially shows you a different trade network for the same economies.
            """
        )
