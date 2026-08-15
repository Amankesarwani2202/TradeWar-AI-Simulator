import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import ALTERNATIVE_SUPPLIERS, COUNTRIES, TRADE_ELASTICITY, CATEGORY_TRADE_WEIGHTS


def _weighted_metrics(graph):
    pagerank = nx.pagerank(graph, weight="weight")
    bridge = nx.betweenness_centrality(graph, weight="weight", normalized=True)

    rows = []
    for country in COUNTRIES:
        inbound = [(u, float(graph[u][country].get("weight", 0))) for u in graph.predecessors(country)]
        outbound = [(v, float(graph[country][v].get("weight", 0))) for v in graph.successors(country)]
        inbound_total = sum(v for _, v in inbound)
        outbound_total = sum(v for _, v in outbound)
        max_import = max((v for _, v in inbound), default=0.0)
        max_export = max((v for _, v in outbound), default=0.0)
        rows.append(
            {
                "country": country,
                "pagerank": pagerank.get(country, 0.0),
                "import_dependency": max_import / inbound_total if inbound_total else 0.0,
                "export_reach": max_export / outbound_total if outbound_total else 0.0,
                "bridge_score": bridge.get(country, 0.0),
                "total_imports_bn": inbound_total,
                "total_exports_bn": outbound_total,
            }
        )
    return pd.DataFrame(rows)


def build_scenario_network(base_graph, exporter, category, tariff_change, importer):
    """Apply a category-sensitive tariff shock to a weighted trade graph.

    The underlying flows are a reproducible model baseline, not live trade data.
    A tariff increase reduces the affected exporter->importer edge and reallocates
    part of the lost flow to alternative suppliers. A tariff reduction reverses
    that direction. The category elasticity controls the shock magnitude.
    """
    graph = nx.DiGraph()
    graph.add_nodes_from(base_graph.nodes())
    graph.add_edges_from(
        (u, v, {**data, "weight": float(data.get("weight", 0)) * CATEGORY_TRADE_WEIGHTS.get(category, 0.1)})
        for u, v, data in base_graph.edges(data=True)
    )

    elasticity = abs(float(TRADE_ELASTICITY.get(category, -0.7)))
    shock = min(0.45, max(0.04, abs(tariff_change) / 100.0 * elasticity))
    alternatives = [c for c in ALTERNATIVE_SUPPLIERS.get(exporter, []) if graph.has_edge(c, importer)]

    affected_edge = (exporter, importer)
    baseline_affected = float(graph[exporter][importer]["weight"]) if graph.has_edge(*affected_edge) else 0.0

    if baseline_affected and tariff_change != 0:
        if tariff_change > 0:
            graph[exporter][importer]["weight"] = baseline_affected * (1.0 - shock)
            diversion = baseline_affected * shock
            weights = [1.0 / (i + 1) for i in range(len(alternatives))]
            total = sum(weights) or 1.0
            for supplier, weight in zip(alternatives, weights):
                graph[supplier][importer]["weight"] *= 1.0 + (diversion * weight / total) / max(float(graph[supplier][importer]["weight"]), 1.0)
        else:
            graph[exporter][importer]["weight"] = baseline_affected * (1.0 + shock * 0.8)
            for supplier in alternatives:
                graph[supplier][importer]["weight"] *= max(0.5, 1.0 - shock * 0.25)

    metrics = _weighted_metrics(graph)
    baseline_metrics = _weighted_metrics(base_graph)
    merged = metrics.merge(
        baseline_metrics[["country", "pagerank", "import_dependency", "export_reach"]],
        on="country",
        suffixes=("", "_baseline"),
    )
    merged["pagerank_change"] = merged["pagerank"] - merged["pagerank_baseline"]
    merged["import_dependency_change"] = merged["import_dependency"] - merged["import_dependency_baseline"]
    merged["export_reach_change"] = merged["export_reach"] - merged["export_reach_baseline"]

    return graph, merged, {
        "affected_edge": affected_edge,
        "alternatives": alternatives,
        "shock_fraction": shock,
        "baseline_affected": baseline_affected,
    }


def _edge_style(u, v, meta, max_weight):
    if (u, v) == meta["affected_edge"]:
        return "affected", max(3.0, 9.0 * float(meta["shock_fraction"]) + 2.0)
    if v == meta["affected_edge"][1] and u in meta["alternatives"]:
        return "diversion", max(2.0, 7.0 * float(meta["shock_fraction"]) + 1.5)
    return "normal", max(0.8, min(5.0, 1.0 + 4.0 * float(graph_weight_ratio := 0 if max_weight == 0 else 1)))


def render_scenario_network(base_graph, exporter, category, tariff_change, importer):
    graph, metrics, meta = build_scenario_network(base_graph, exporter, category, tariff_change, importer)

    direction = "increase" if tariff_change > 0 else "reduction" if tariff_change < 0 else "no change"
    st.markdown(f"**Scenario network — {category}: {exporter} → {importer} ({tariff_change:+.0f}%)**")
    st.caption(
        f"Weighted model network after the tariff {direction}. Edge thickness represents modeled trade value; "
        "the highlighted route shows the direct shock and green routes show modeled diversion."
    )

    positions = nx.spring_layout(graph, seed=42, k=1.8, iterations=120, weight="weight")
    max_weight = max((float(d.get("weight", 0)) for _, _, d in graph.edges(data=True)), default=1.0)

    edge_x, edge_y = [], []
    edge_colors, edge_widths = [], []
    for u, v, data in graph.edges(data=True):
        x0, y0 = positions[u]
        x1, y1 = positions[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        if (u, v) == meta["affected_edge"]:
            edge_colors.append("#ef4444")
            edge_widths.append(4.5)
        elif v == importer and u in meta["alternatives"] and tariff_change > 0:
            edge_colors.append("#16a34a")
            edge_widths.append(3.2)
        else:
            edge_colors.append("#94a3b8")
            edge_widths.append(max(0.7, 5.0 * float(data.get("weight", 0)) / max_weight))

    # Plotly uses one width/color per trace, so draw normal edges together and
    # highlighted edges separately for reliable rendering.
    fig = go.Figure()
    normal_x, normal_y = [], []
    normal_widths = []
    for u, v, data in graph.edges(data=True):
        x0, y0 = positions[u]
        x1, y1 = positions[v]
        if (u, v) == meta["affected_edge"] or (v == importer and u in meta["alternatives"] and tariff_change > 0):
            continue
        normal_x += [x0, x1, None]
        normal_y += [y0, y1, None]
        normal_widths.append(max(0.7, 5.0 * float(data.get("weight", 0)) / max_weight))

    fig.add_trace(go.Scatter(x=normal_x, y=normal_y, mode="lines", line=dict(color="#94a3b8", width=1.2), hoverinfo="none", name="Other trade routes"))

    def add_highlight(edge, color, name, width):
        if graph.has_edge(*edge):
            x0, y0 = positions[edge[0]]
            x1, y1 = positions[edge[1]]
            fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines+markers", line=dict(color=color, width=width), marker=dict(size=4), hovertemplate=f"{edge[0]} → {edge[1]}<extra>{name}</extra>", name=name))

    add_highlight(meta["affected_edge"], "#ef4444", "Tariff-affected route", 5)
    if tariff_change > 0:
        for supplier in meta["alternatives"]:
            add_highlight((supplier, importer), "#16a34a", "Diversion route", 3)

    node_x = [positions[c][0] for c in graph.nodes()]
    node_y = [positions[c][1] for c in graph.nodes()]
    node_sizes = []
    for c in graph.nodes():
        score = float(metrics.loc[metrics.country == c, "pagerank"].iloc[0])
        node_sizes.append(18 + 90 * score)

    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=list(graph.nodes()),
            textposition="top center",
            marker=dict(size=node_sizes, color="#2563eb", line=dict(width=1, color="#0f172a")),
            hovertemplate="%{text}<extra>Country</extra>",
            name="Countries",
        )
    )
    fig.update_layout(
        height=560,
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=True,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#64748b"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    display = metrics[["country", "pagerank", "import_dependency", "export_reach", "bridge_score", "total_imports_bn", "total_exports_bn"]].copy()
    display = display.sort_values("pagerank", ascending=False)
    display.columns = ["Country", "PageRank", "Import dependency", "Export reach", "Bridge score", "Modeled imports (B)", "Modeled exports (B)"]
    for col in ["PageRank", "Import dependency", "Export reach", "Bridge score"]:
        display[col] = display[col].round(4)
    display["Modeled imports (B)"] = display["Modeled imports (B)"].round(2)
    display["Modeled exports (B)"] = display["Modeled exports (B)"].round(2)
    st.markdown("**Scenario-sensitive network metrics**")
    st.dataframe(display, use_container_width=True, hide_index=True)

    if tariff_change > 0 and meta["alternatives"]:
        st.info("Green routes represent modeled trade diversion toward alternative suppliers. These are scenario estimates, not live trade-flow observations.")
    elif tariff_change < 0:
        st.info("The affected route expands under the tariff reduction; alternative-supplier routes are reduced modestly in the model.")
    else:
        st.info("No tariff change was applied, so the network remains at its baseline weights.")
