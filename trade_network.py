"""Scenario-aware trade network calculations and visualization.

The base trade-flow graph is synthetic and intentionally reproducible.  This
module applies the selected tariff shock to bilateral flows, recalculates
weighted network metrics, and renders a readable scenario graph.
"""

import networkx as nx
import pandas as pd
import plotly.graph_objects as go

from utils import (
    ALTERNATIVE_SUPPLIERS,
    COUNTRIES,
    TRADE_ELASTICITY,
    TRADE_FLOWS,
)


def _base_graph():
    graph = nx.DiGraph()
    graph.add_nodes_from(COUNTRIES)
    for exporter, importer, value in TRADE_FLOWS:
        graph.add_edge(exporter, importer, weight=float(value))
    return graph


def build_scenario_trade_network(country, category, tariff_change_pct, target_partner):
    """Return a scenario-adjusted graph plus weighted metrics and vulnerability.

    Positive tariffs reduce the targeted exporter -> importer flow and increase
    alternative supplier flows to the same importer. Negative tariffs reverse
    that direction. The magnitude depends on the selected category elasticity
    and tariff size, so changing the custom scenario changes the tables too.
    """
    graph = _base_graph()
    elasticity = abs(float(TRADE_ELASTICITY.get(category, -0.7)))
    shock = min(0.55, abs(float(tariff_change_pct)) / 100.0 * (0.65 + elasticity * 0.35))
    alternatives = ALTERNATIVE_SUPPLIERS.get(country, [])

    if tariff_change_pct:
        for exporter, importer in list(graph.edges()):
            weight = float(graph[exporter][importer]["weight"])
            if exporter == country and importer == target_partner:
                if tariff_change_pct > 0:
                    weight *= 1.0 - shock
                else:
                    weight *= 1.0 + shock * 0.75
            elif exporter in alternatives and importer == target_partner:
                if tariff_change_pct > 0:
                    weight *= 1.0 + shock * 0.70
                else:
                    weight *= 1.0 - shock * 0.35
            graph[exporter][importer]["weight"] = max(1.0, round(weight, 2))

    metrics = _weighted_metrics(graph)
    vulnerability = _vulnerability(graph, metrics)
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
    # NetworkX treats edge weight as distance for betweenness. Convert trade
    # volume into distance so larger trade routes are more important/shorter.
    distance_graph = graph.copy()
    for exporter, importer, data in distance_graph.edges(data=True):
        data["distance"] = 1.0 / max(float(data["weight"]), 1.0)
    bridge = nx.betweenness_centrality(distance_graph, weight="distance", normalized=True)

    rows = []
    for country in COUNTRIES:
        rows.append(
            {
                "country": country,
                "pagerank": round(pagerank[country], 4),
                "import_dependency": round(total_imports[country] / total_trade, 4),
                "export_reach": round(total_exports[country] / total_trade, 4),
                "bridge_score": round(bridge[country], 4),
                "import_value_bn": round(total_imports[country], 2),
                "export_value_bn": round(total_exports[country], 2),
            }
        )
    return pd.DataFrame(rows).sort_values("pagerank", ascending=False).reset_index(drop=True)


def _vulnerability(graph, metrics):
    by_country = metrics.set_index("country")
    values = {}
    for country in COUNTRIES:
        row = by_country.loc[country]
        values[country] = round(
            100
            * (
                0.45 * row["import_dependency"]
                + 0.30 * row["pagerank"]
                + 0.25 * row["bridge_score"]
            ),
            3,
        )
    return dict(sorted(values.items(), key=lambda item: item[1], reverse=True))


def build_network_figure(graph, metrics, title):
    """Create a readable interactive network graph with scenario-sensitive sizing."""
    positions = nx.spring_layout(graph, seed=42, k=1.8, iterations=120, weight="weight")
    metric_map = metrics.set_index("country")
    pageranks = metrics["pagerank"]
    p_min, p_max = float(pageranks.min()), float(pageranks.max())
    span = max(p_max - p_min, 1e-6)

    edge_x, edge_y = [], []
    for exporter, importer, data in graph.edges(data=True):
        x0, y0 = positions[exporter]
        x1, y1 = positions[importer]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(width=1.2, color="rgba(148,163,184,0.45)"),
        hoverinfo="none",
        showlegend=False,
    )

    node_x = [positions[c][0] for c in COUNTRIES]
    node_y = [positions[c][1] for c in COUNTRIES]
    sizes = [
        18 + 34 * ((metric_map.loc[c, "pagerank"] - p_min) / span)
        for c in COUNTRIES
    ]
    hover = [
        f"<b>{c}</b><br>PageRank: {metric_map.loc[c, 'pagerank']:.4f}"
        f"<br>Import dependency: {metric_map.loc[c, 'import_dependency']:.2%}"
        f"<br>Export reach: {metric_map.loc[c, 'export_reach']:.2%}"
        f"<br>Bridge score: {metric_map.loc[c, 'bridge_score']:.4f}"
        for c in COUNTRIES
    ]

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=COUNTRIES,
        textposition="middle center",
        textfont=dict(size=11),
        hovertext=hover,
        hoverinfo="text",
        marker=dict(
            size=sizes,
            color=[metric_map.loc[c, "pagerank"] for c in COUNTRIES],
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="PageRank"),
            line=dict(width=1, color="rgba(255,255,255,0.45)"),
        ),
        showlegend=False,
    )

    fig = go.Figure([edge_trace, node_trace])
    fig.update_layout(
        title=title,
        height=560,
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode="closest",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def render_network_tab(country, category, tariff_change_pct, target_partner):
    graph, metrics, vulnerability = build_scenario_trade_network(
        country, category, tariff_change_pct, target_partner
    )
    fig = build_network_figure(
        graph,
        metrics,
        f"{category} network — {country} ({tariff_change_pct:+.0f}%)",
    )
    st = __import__("streamlit")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Scenario-adjusted trade network metrics")
    st.dataframe(
        metrics[
            [
                "country",
                "pagerank",
                "import_dependency",
                "export_reach",
                "bridge_score",
                "import_value_bn",
                "export_value_bn",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    vulnerability_df = pd.DataFrame(
        list(vulnerability.items()), columns=["Country", "Vulnerability"]
    )
    st.markdown("#### Scenario-adjusted vulnerability")
    st.dataframe(vulnerability_df, use_container_width=True, hide_index=True)
