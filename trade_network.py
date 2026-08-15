"""Scenario-aware trade network calculations and visualization."""

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import ALTERNATIVE_SUPPLIERS, COUNTRIES, TRADE_ELASTICITY, TRADE_FLOWS

# Illustrative route weights make the selected product category matter in the
# network. These are teaching-model weights, not observed bilateral statistics.
CATEGORY_ROUTE_MULTIPLIERS = {
    "Electronics": {"China": 1.20, "Taiwan": 1.35, "South Korea": 1.25, "Japan": 1.10, "Vietnam": 1.15, "India": 0.85},
    "Semiconductors": {"Taiwan": 1.45, "South Korea": 1.35, "Japan": 1.20, "China": 1.05, "US": 1.10, "India": 0.75},
    "Machinery": {"Japan": 1.30, "Germany": 1.0, "China": 1.15, "US": 1.20, "South Korea": 1.15, "EU": 1.15},
    "Chemicals": {"US": 1.20, "China": 1.15, "EU": 1.20, "Japan": 1.10, "India": 1.05},
    "Textiles": {"Bangladesh": 1.45, "Vietnam": 1.30, "India": 1.25, "China": 1.05, "Thailand": 1.10},
    "Steel": {"China": 1.30, "India": 1.15, "Japan": 1.15, "South Korea": 1.20, "EU": 1.10},
}


def _base_graph(category):
    graph = nx.DiGraph()
    graph.add_nodes_from(COUNTRIES)
    route_weights = CATEGORY_ROUTE_MULTIPLIERS.get(category, {})
    for exporter, importer, value in TRADE_FLOWS:
        multiplier = route_weights.get(exporter, 1.0)
        graph.add_edge(exporter, importer, weight=round(float(value) * multiplier, 2))
    return graph


def build_scenario_trade_network(country, category, tariff_change_pct, target_partner):
    """Return a category- and tariff-adjusted graph plus weighted metrics."""
    graph = _base_graph(category)
    elasticity = abs(float(TRADE_ELASTICITY.get(category, -0.7)))
    shock = min(0.55, abs(float(tariff_change_pct)) / 100.0 * (0.65 + elasticity * 0.35))
    alternatives = ALTERNATIVE_SUPPLIERS.get(country, [])

    for exporter, importer in list(graph.edges()):
        weight = float(graph[exporter][importer]["weight"])
        if exporter == country and importer == target_partner:
            if tariff_change_pct > 0:
                weight *= 1.0 - shock
            elif tariff_change_pct < 0:
                weight *= 1.0 + shock * 0.75
        elif exporter in alternatives and importer == target_partner:
            if tariff_change_pct > 0:
                weight *= 1.0 + shock * 0.70
            elif tariff_change_pct < 0:
                weight *= 1.0 - shock * 0.35
        graph[exporter][importer]["weight"] = max(1.0, round(weight, 2))

    metrics = _weighted_metrics(graph)
    vulnerability = _vulnerability(metrics)
    return graph, metrics, vulnerability


def _weighted_metrics(graph):
    total_imports = {
        node: sum(data["weight"] for _, _, data in graph.in_edges(node, data=True))
        for node in graph.nodes
    }
    total_exports = {
        node: sum(data["weight"] for _, _, data in graph.out_edges(node, data=True))
        for node in graph.nodes
    }
    total_trade = sum(data["weight"] for _, _, data in graph.edges(data=True)) or 1.0

    pagerank = nx.pagerank(graph, weight="weight")
    distance_graph = graph.copy()
    for _, _, data in distance_graph.edges(data=True):
        data["distance"] = 1.0 / max(float(data["weight"]), 1.0)
    bridge = nx.betweenness_centrality(distance_graph, weight="distance", normalized=True)

    rows = []
    for country in COUNTRIES:
        rows.append({
            "country": country,
            "pagerank": round(pagerank[country], 4),
            "import_dependency": round(total_imports[country] / total_trade, 4),
            "export_reach": round(total_exports[country] / total_trade, 4),
            "bridge_score": round(bridge[country], 4),
            "import_value_bn": round(total_imports[country], 2),
            "export_value_bn": round(total_exports[country], 2),
        })
    return pd.DataFrame(rows).sort_values("pagerank", ascending=False).reset_index(drop=True)


def _vulnerability(metrics):
    by_country = metrics.set_index("country")
    values = {}
    for country in COUNTRIES:
        row = by_country.loc[country]
        values[country] = round(100 * (
            0.45 * row["import_dependency"]
            + 0.30 * row["pagerank"]
            + 0.25 * row["bridge_score"]
        ), 3)
    return dict(sorted(values.items(), key=lambda item: item[1], reverse=True))


def _theme_colors():
    try:
        dark = st.context.theme.type == "dark"
    except Exception:
        dark = st.get_option("theme.base") == "dark"
    if dark:
        return "#0b1220", "#e5e7eb", "#334155", "rgba(148,163,184,0.45)"
    return "#ffffff", "#111827", "#e2e8f0", "rgba(100,116,139,0.40)"


def build_network_figure(graph, metrics, title):
    """Create a readable scenario-sensitive network with bounded node sizes."""
    background, text, grid, edge_color = _theme_colors()
    # Ignore edge weights for layout so high-volume hubs do not collapse the graph.
    positions = nx.spring_layout(graph, seed=42, k=2.4, iterations=220, weight=None)
    metric_map = metrics.set_index("country")
    pageranks = metrics["pagerank"]
    p_min, p_max = float(pageranks.min()), float(pageranks.max())
    span = max(p_max - p_min, 1e-6)

    edge_x, edge_y = [], []
    for exporter, importer in graph.edges():
        x0, y0 = positions[exporter]
        x1, y1 = positions[importer]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=1.2, color=edge_color), hoverinfo="none", showlegend=False,
    )

    node_x = [positions[c][0] for c in COUNTRIES]
    node_y = [positions[c][1] for c in COUNTRIES]
    sizes = [20 + 28 * ((metric_map.loc[c, "pagerank"] - p_min) / span) for c in COUNTRIES]
    hover = [
        f"<b>{c}</b><br>PageRank: {metric_map.loc[c, 'pagerank']:.4f}"
        f"<br>Import dependency: {metric_map.loc[c, 'import_dependency']:.2%}"
        f"<br>Export reach: {metric_map.loc[c, 'export_reach']:.2%}"
        f"<br>Bridge score: {metric_map.loc[c, 'bridge_score']:.4f}"
        f"<br>Exports: ${metric_map.loc[c, 'export_value_bn']:.1f}B"
        for c in COUNTRIES
    ]

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text", text=COUNTRIES,
        textposition="middle center", textfont=dict(size=11, color=text),
        hovertext=hover, hoverinfo="text", showlegend=False,
        marker=dict(
            size=sizes,
            color=[metric_map.loc[c, "pagerank"] for c in COUNTRIES],
            colorscale="Viridis", showscale=True,
            colorbar=dict(title="PageRank", tickfont=dict(color=text), titlefont=dict(color=text)),
            line=dict(width=1, color=edge_color),
        ),
    )

    fig = go.Figure([edge_trace, node_trace])
    fig.update_layout(
        title=dict(text=title, font=dict(color=text, size=22)),
        height=560, margin=dict(l=20, r=20, t=70, b=20), hovermode="closest",
        showlegend=False, paper_bgcolor=background, plot_bgcolor=background,
        font=dict(color=text),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, fixedrange=True),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, fixedrange=True),
    )
    return fig


def render_network_tab(country, category, tariff_change_pct, target_partner):
    graph, metrics, vulnerability = build_scenario_trade_network(country, category, tariff_change_pct, target_partner)
    st.caption("Illustrative category-weighted trade network. Tariff shocks alter the targeted route and alternative suppliers; values are model outputs, not observed bilateral trade statistics.")
    st.plotly_chart(build_network_figure(graph, metrics, f"{category} network — {country} ({tariff_change_pct:+.0f}%)"), use_container_width=True)

    st.markdown("#### Scenario-adjusted trade network metrics")
    st.dataframe(metrics[["country", "pagerank", "import_dependency", "export_reach", "bridge_score", "import_value_bn", "export_value_bn"]], use_container_width=True, hide_index=True)

    st.markdown("#### Scenario-adjusted vulnerability")
    vulnerability_df = pd.DataFrame(list(vulnerability.items()), columns=["Country", "Vulnerability"])
    st.dataframe(vulnerability_df, use_container_width=True, hide_index=True)
