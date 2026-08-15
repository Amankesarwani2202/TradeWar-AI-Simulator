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
    light_backgrounds = ["#f8fafc", "#ffffff", "#FFFFFF", "#fff", "#FFF", "white", "#eff6ff", "#dcfce7", "#fef3c7", "#fee2e2", "#faf5ff"]
    light_texts = ["#0f172a", "#0F172A", "#111827", "#1f2937", "#1F2937", "#374151", "#475569", "#64748b", "#64748B", "#6b7280", "#6B7280", "#666"]
    bg_selectors = ",\n        ".join(f'[style*="background:{v}"], [style*="background: {v}"]' for v in light_backgrounds)
    text_selectors = ",\n        ".join(f'[style*="color:{v}"], [style*="color: {v}"]' for v in light_texts)
    css = f"""
    <style>
        :root {{ --app-background:{colors['background']}; --app-secondary:{colors['secondary']}; --app-text:{colors['text']}; --app-muted:{colors['muted']}; --app-border:{colors['border']}; }}
        .main .block-container {{ padding-top:2rem; padding-bottom:1.25rem; }}
        [data-testid="metric-container"] {{ padding:1.1rem; border-radius:.5rem; }}
        h1,h2,h3,h4,h5,h6 {{ color:{colors['text']} !important; font-weight:600; }}
        p,li,label {{ color:{colors['text']}; }}
        [data-testid="stCaptionContainer"] {{ color:{colors['muted']} !important; }}
        [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {{ color:{colors['text']}; }}
        [data-testid="stSidebar"] {{ background:{colors['background']} !important; }}
        {bg_selectors} {{ background:{colors['secondary']} !important; color:{colors['text']} !important; border-color:{colors['border']} !important; }}
        {text_selectors} {{ color:{colors['text']} !important; }}
        [style*="border:#e2e8f0"], [style*="border: #e2e8f0"], [style*="border:1px solid #e2e8f0"], [style*="border: 1px solid #e2e8f0"], [style*="border:1px solid #E2E8F0"], [style*="border: 1px solid #E2E8F0"] {{ border-color:{colors['border']} !important; }}
        [data-testid="stAlert"] {{ color:{colors['text']} !important; }}
        [data-testid="stAlert"] p,[data-testid="stAlert"] span,[data-testid="stAlert"] strong {{ color:inherit !important; }}
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
        .js-plotly-plot .plotly .cbaxis text {{ fill:{colors['text']} !important; }}
        .js-plotly-plot .plotly .gridlayer path,
        .js-plotly-plot .plotly .zerolinelayer path,
        .js-plotly-plot .plotly .xaxislayer-above path,
        .js-plotly-plot .plotly .yaxislayer-above path {{ stroke:{colors['border']} !important; }}
        [data-testid="stDataFrame"] {{ color:{colors['text']} !important; }}
        [data-testid="stDataFrame"] iframe {{ color-scheme:{'dark' if dark else 'light'}; }}
        /* Prevent an empty chart wrapper from creating a large visual gap. */
        [data-testid="stPlotlyChart"] {{ margin-bottom:0 !important; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
