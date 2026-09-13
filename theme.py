import streamlit as st


def current_theme_type():
    """Return Streamlit's active light/dark theme."""
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
    if current_theme_type() == "light":
        return {
            "background": "#FFFFFF", "secondary": "#F0F2F6", "text": "#31333F",
            "muted": "#6B7280", "border": "#D1D5DB", "grid": "#E5E7EB",
        }
    return {
        "background": "#0E1117", "secondary": "#262730", "text": "#FAFAFA",
        "muted": "#B8C0CC", "border": "#3B4252", "grid": "#343B4A",
    }


def apply_plotly_theme(fig):
    """Apply concrete theme colors directly to Plotly figures.

    Plotly charts render their SVG separately from Streamlit's DOM, so relying
    on CSS alone is unreliable. Direct figure styling keeps every chart readable
    in both light and dark mode.
    """
    colors = theme_colors()
    fig.update_layout(
        template="plotly",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=colors["text"]),
        title=dict(font=dict(color=colors["text"])),
        legend=dict(font=dict(color=colors["text"])),
        hoverlabel=dict(
            bgcolor=colors["secondary"],
            font=dict(color=colors["text"]),
            bordercolor=colors["border"],
        ),
    )
    fig.update_xaxes(
        title_font=dict(color=colors["text"]), tickfont=dict(color=colors["text"]),
        gridcolor=colors["grid"], zerolinecolor=colors["grid"],
        linecolor=colors["border"], color=colors["text"],
    )
    fig.update_yaxes(
        title_font=dict(color=colors["text"]), tickfont=dict(color=colors["text"]),
        gridcolor=colors["grid"], zerolinecolor=colors["grid"],
        linecolor=colors["border"], color=colors["text"],
    )

    for trace in fig.data:
        try:
            if getattr(trace, "textfont", None) is not None:
                trace.textfont.color = colors["text"]
        except Exception:
            pass
        try:
            if getattr(trace, "insidetextfont", None) is not None:
                trace.insidetextfont.color = colors["text"]
            if getattr(trace, "outsidetextfont", None) is not None:
                trace.outsidetextfont.color = colors["text"]
        except Exception:
            pass
        try:
            if getattr(trace, "marker", None) is not None and getattr(trace.marker, "colorbar", None) is not None:
                cb = trace.marker.colorbar
                title_text = cb.title.text if cb.title and cb.title.text else ""
                cb.title = dict(text=title_text, font=dict(color=colors["text"]))
                cb.tickfont = dict(color=colors["text"])
                cb.outlinecolor = colors["border"]
        except Exception:
            pass

    for annotation in list(fig.layout.annotations) if fig.layout.annotations else []:
        existing_font = annotation.font.to_plotly_json() if annotation.font else {}
        annotation.font = dict(**existing_font, color=colors["text"])
    return fig


def patch_streamlit_plotly_chart():
    """Theme all Streamlit Plotly charts, including charts with local templates."""
    if getattr(st, "_trade_war_plotly_theme_patched", False):
        return

    # Patch DeltaGenerator.plotly_chart rather than only st.plotly_chart. This is
    # the actual method used by Streamlit's st.plotly_chart API and is reliable
    # across multipage apps and Streamlit reruns.
    try:
        from streamlit.delta_generator import DeltaGenerator
        original_plotly_chart = DeltaGenerator.plotly_chart

        def themed_plotly_chart(self, figure_or_data, *args, **kwargs):
            try:
                if hasattr(figure_or_data, "update_layout") and hasattr(figure_or_data, "data"):
                    figure_or_data = apply_plotly_theme(figure_or_data)
            except Exception:
                pass
            return original_plotly_chart(self, figure_or_data, *args, **kwargs)

        DeltaGenerator.plotly_chart = themed_plotly_chart
    except Exception:
        # Keep the fallback for Streamlit versions exposing the function directly.
        original_plotly_chart = st.plotly_chart

        def themed_plotly_chart(figure_or_data, *args, **kwargs):
            try:
                if hasattr(figure_or_data, "update_layout") and hasattr(figure_or_data, "data"):
                    figure_or_data = apply_plotly_theme(figure_or_data)
            except Exception:
                pass
            return original_plotly_chart(figure_or_data, *args, **kwargs)

        st.plotly_chart = themed_plotly_chart

    st._trade_war_plotly_theme_patched = True


def inject_css():
    """Inject CSS for normal Streamlit UI and Plotly fallbacks."""
    css = """
    <style>
        :root {
            --app-background:var(--st-background-color);
            --app-secondary:var(--st-secondary-background-color);
            --app-text:var(--st-text-color);
            --app-muted:var(--st-gray-text-color);
            --app-border:var(--st-border-color);
        }
        .main .block-container { padding-top:2rem; padding-bottom:1.25rem; }
        [data-testid="metric-container"] { padding:1.1rem; border-radius:.5rem; }
        h1,h2,h3,h4,h5,h6 { color:var(--app-text) !important; font-weight:600; }
        p,li,label { color:var(--app-text); }
        [data-testid="stCaptionContainer"] { color:var(--app-muted) !important; }
        [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] { color:var(--app-text); }
        [data-testid="stSidebar"] { background:var(--app-background) !important; }
        [data-testid="stAlert"] { color:var(--app-text) !important; }
        [data-testid="stAlert"] p,[data-testid="stAlert"] span,[data-testid="stAlert"] strong { color:inherit !important; }
        .tw-panel {
            background:var(--app-secondary) !important;
            padding:1rem 1.25rem;
            border-radius:.5rem;
            border:1px solid var(--app-border);
            margin-bottom:1.5rem;
        }
        .tw-panel p, .tw-panel span, .tw-panel strong { color:var(--app-text); }
        .tw-panel .tw-muted { color:var(--app-muted) !important; }
        .tw-panel-inner {
            background:var(--app-background) !important;
            padding:0.8rem;
            border-radius:.4rem;
            border:1px solid var(--app-border);
        }
        .tw-panel-inner p, .tw-panel-inner span { color:var(--app-text); }
        .tw-panel-inner .tw-muted { color:var(--app-muted) !important; }
        .tw-hint { background:var(--app-secondary) !important; padding:.5rem .75rem; border-radius:.4rem; }
        .tw-hint p { color:inherit; }
        .tw-muted { color:var(--app-muted) !important; }
        .js-plotly-plot .plotly svg text,
        .js-plotly-plot .plotly .gtitle,
        .js-plotly-plot .plotly .xtitle,
        .js-plotly-plot .plotly .ytitle,
        .js-plotly-plot .plotly .xtick text,
        .js-plotly-plot .plotly .ytick text,
        .js-plotly-plot .plotly .legendtext,
        .js-plotly-plot .plotly .cbtitle,
        .js-plotly-plot .plotly .cbaxis text { fill:var(--app-text) !important; }
        .js-plotly-plot .plotly .gridlayer path,
        .js-plotly-plot .plotly .zerolinelayer path,
        .js-plotly-plot .plotly .xaxislayer-above path,
        .js-plotly-plot .plotly .yaxislayer-above path { stroke:var(--app-border) !important; }
        [data-testid="stDataFrame"] { color:var(--app-text) !important; }
        [data-testid="stPlotlyChart"] { margin-bottom:0 !important; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# Install the patch as soon as the module is imported so all pages are covered.
patch_streamlit_plotly_chart()
