import numpy as np
import plotly.graph_objects as go
import streamlit as st

from theme import apply_plotly_theme
from utils import TRADE_ELASTICITY, forecast_series


def build_clean_forecast_chart(df, country, category, tariff_change_pct, steps=3):
    """Build a forecast chart with separated legend, generous margins and readable axes."""
    hist = df[(df.country == country) & (df.category == category)].sort_values("year")
    base = forecast_series(hist.export_value_bn_usd.values, steps)
    scenario = np.maximum(
        0,
        base * (1 + TRADE_ELASTICITY.get(category, -0.7) * tariff_change_pct / 100),
    )
    years = list(range(2025, 2025 + steps))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=hist.year,
            y=hist.export_value_bn_usd,
            mode="lines+markers",
            name="Historical",
            line=dict(width=2.5),
            marker=dict(size=6),
            hovertemplate="Year: %{x}<br>Exports: $%{y:.1f}B<extra>Historical</extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=base,
            mode="lines+markers",
            name="Baseline",
            line=dict(width=2.5, dash="dash"),
            marker=dict(size=7),
            hovertemplate="Year: %{x}<br>Exports: $%{y:.1f}B<extra>Baseline</extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=scenario,
            mode="lines+markers",
            name="Policy scenario",
            line=dict(width=2.5),
            marker=dict(size=7),
            hovertemplate="Year: %{x}<br>Exports: $%{y:.1f}B<extra>Policy scenario</extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text=f"Export Trajectory — {country} | {category}",
            x=0,
            xanchor="left",
            y=0.98,
            yanchor="top",
        ),
        height=440,
        margin=dict(l=70, r=40, t=105, b=65),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="right",
            x=1,
            traceorder="normal",
            itemwidth=110,
        ),
        hovermode="x unified",
        xaxis=dict(
            title="Year",
            dtick=1,
            tickmode="linear",
            automargin=True,
        ),
        yaxis=dict(
            title="Exports (USD billions)",
            automargin=True,
            separatethousands=True,
        ),
    )
    return apply_plotly_theme(fig), base, scenario


def render_clean_forecast_tab(df, country, category, tariff_change_pct, steps=3):
    fig, _, _ = build_clean_forecast_chart(
        df, country, category, tariff_change_pct, steps
    )
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displaylogo": False, "responsive": True},
    )
