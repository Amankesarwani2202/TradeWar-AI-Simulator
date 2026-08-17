import streamlit as st


def current_theme_type():
    """Return the actual active Streamlit theme, including user menu switches."""
    try:
        theme_type = st.context.theme.type
        if theme_type in ("dark", "light"):
            return theme_type
    except Exception:
        pass
    try:
        configured = st.get_option("theme.base")
        if configured in ("dark", "light"):
            return configured
    except Exception:
        pass
    return "dark"


def theme_colors():
    if current_theme_type() == "dark":
        return {"background": "#0b1220", "secondary": "#111827", "text": "#e5e7eb", "muted": "#94a3b8", "border": "#334155", "grid": "#334155"}
    return {"background": "#ffffff", "secondary": "#f8fafc", "text": "#111827", "muted": "#64748b", "border": "#e2e8f0", "grid": "#e2e8f0"}


def apply_plotly_theme(fig):
    colors = theme_colors()
    dark = current_theme_type() == "dark"
    fig.update_layout(
        template="plotly_dark" if dark else "plotly_white",
        paper_bgcolor=colors["background"], plot_bgcolor=colors["background"],
        font=dict(color=colors["text"]), title=dict(font=dict(color=colors["text"])),
        legend=dict(font=dict(color=colors["text"])),
        hoverlabel=dict(bgcolor=colors["secondary"], font=dict(color=colors["text"]), bordercolor=colors["border"]),
    )
    fig.update_xaxes(title_font=dict(color=colors["text"]), tickfont=dict(color=colors["text"]), gridcolor=colors["grid"], zerolinecolor=colors["grid"], linecolor=colors["border"], color=colors["text"])
    fig.update_yaxes(title_font=dict(color=colors["text"]), tickfont=dict(color=colors["text"]), gridcolor=colors["grid"], zerolinecolor=colors["grid"], linecolor=colors["border"], color=colors["text"])
    for trace in fig.data:
        try:
            if getattr(trace, "marker", None) is not None and getattr(trace.marker, "colorbar", None) is not None:
                cb = trace.marker.colorbar
                title_text = cb.title.text if cb.title and cb.title.text else ""
                cb.title = dict(text=title_text, font=dict(color=colors["text"]))
                cb.tickfont = dict(color=colors["text"])
                cb.outlinecolor = colors["border"]
        except Exception:
            pass
    return fig


def inject_css():
    colors = theme_colors()
    dark = current_theme_type() == "dark"
    css = f"""
    <style>
        :root {{
            --app-background:{colors['background']};
            --app-secondary:{colors['secondary']};
            --app-text:{colors['text']};
            --app-muted:{colors['muted']};
            --app-border:{colors['border']};
        }}
        .main .block-container {{ padding-top:2rem; padding-bottom:1.25rem; }}
        [data-testid="metric-container"] {{ padding:1.1rem; border-radius:.5rem; }}
        h1,h2,h3,h4,h5,h6 {{ color:var(--app-text) !important; font-weight:600; }}
        p,li,label {{ color:var(--app-text); }}
        [data-testid="stCaptionContainer"] {{ color:var(--app-muted) !important; }}
        [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {{ color:var(--app-text); }}
        [data-testid="stSidebar"] {{ background:var(--app-background) !important; }}
        [data-testid="stAlert"] {{ color:var(--app-text) !important; }}
        [data-testid="stAlert"] p,[data-testid="stAlert"] span,[data-testid="stAlert"] strong {{ color:inherit !important; }}
        .tw-panel {{
            background:var(--app-secondary) !important;
            padding:1rem 1.25rem;
            border-radius:.5rem;
            border:1px solid var(--app-border);
            margin-bottom:1.5rem;
        }}
        .tw-panel p, .tw-panel span, .tw-panel strong {{ color:var(--app-text); }}
        .tw-panel .tw-muted {{ color:var(--app-muted) !important; }}
        .tw-panel-inner {{
            background:var(--app-background) !important;
            padding:0.8rem;
            border-radius:.4rem;
            border:1px solid var(--app-border);
        }}
        .tw-panel-inner p, .tw-panel-inner span {{ color:var(--app-text); }}
        .tw-panel-inner .tw-muted {{ color:var(--app-muted) !important; }}
        .tw-hint {{
            background:var(--app-secondary) !important;
            padding:.5rem .75rem;
            border-radius:.4rem;
        }}
        .tw-hint p {{ color:inherit; }}
        .tw-muted {{ color:var(--app-muted) !important; }}
        /* Do not set SVG fill/background here: Plotly uses child SVG paths for
           node markers and edges, and forcing fill on the parent can hide them. */
        .js-plotly-plot .plotly svg text,
        .js-plotly-plot .plotly .gtitle,
        .js-plotly-plot .plotly .xtitle,
        .js-plotly-plot .plotly .ytitle,
        .js-plotly-plot .plotly .xtick text,
        .js-plotly-plot .plotly .ytick text,
        .js-plotly-plot .plotly .legendtext,
        .js-plotly-plot .plotly .cbtitle,
        .js-plotly-plot .plotly .cbaxis text {{ fill:var(--app-text) !important; }}
        .js-plotly-plot .plotly .gridlayer path,
        .js-plotly-plot .plotly .zerolinelayer path,
        .js-plotly-plot .plotly .xaxislayer-above path,
        .js-plotly-plot .plotly .yaxislayer-above path {{ stroke:var(--app-border) !important; }}
        [data-testid="stDataFrame"] {{ color:var(--app-text) !important; }}
        [data-testid="stDataFrame"] iframe {{ color-scheme:{'dark' if dark else 'light'}; }}
        [data-testid="stPlotlyChart"] {{ margin-bottom:0 !important; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
