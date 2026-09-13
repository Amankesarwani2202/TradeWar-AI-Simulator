import streamlit as st


def current_theme_type():
    """Return the active Streamlit light/dark theme for the current viewer."""
    try:
        theme_type = st.context.theme.type
        if theme_type in ("dark", "light"):
            return theme_type
    except Exception:
        pass
    # Compatibility fallback for older Streamlit versions.
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
            "background": "#FFFFFF",
            "secondary": "#F0F2F6",
            "text": "#31333F",
            "muted": "#6B7280",
            "border": "#D1D5DB",
            "grid": "#E5E7EB",
        }
    return {
        "background": "#0E1117",
        "secondary": "#262730",
        "text": "#FAFAFA",
        "muted": "#B8C0CC",
        "border": "#3B4252",
        "grid": "#343B4A",
    }


def apply_plotly_theme(fig):
    """Apply explicit light/dark colors directly to a Plotly figure."""
    colors = theme_colors()
    is_dark = current_theme_type() == "dark"

    # Use Plotly's matching native template, then explicitly override every
    # text-bearing component. This is important because several app charts
    # start with plotly_white and Streamlit can otherwise apply its own chart
    # theme again when rendering the figure.
    fig.update_layout(
        template="plotly_dark" if is_dark else "plotly_white",
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
        title_font=dict(color=colors["text"]),
        tickfont=dict(color=colors["text"]),
        color=colors["text"],
        gridcolor=colors["grid"],
        zerolinecolor=colors["grid"],
        linecolor=colors["border"],
    )
    fig.update_yaxes(
        title_font=dict(color=colors["text"]),
        tickfont=dict(color=colors["text"]),
        color=colors["text"],
        gridcolor=colors["grid"],
        zerolinecolor=colors["grid"],
        linecolor=colors["border"],
    )

    for trace in fig.data:
        for attr in ("textfont", "insidetextfont", "outsidetextfont"):
            try:
                setattr(trace, attr, dict(color=colors["text"]))
            except Exception:
                pass

        try:
            cb = getattr(getattr(trace, "marker", None), "colorbar", None)
            if cb is not None:
                title_text = cb.title.text if cb.title and cb.title.text else ""
                cb.title = dict(text=title_text, font=dict(color=colors["text"]))
                cb.tickfont = dict(color=colors["text"])
                cb.outlinecolor = colors["border"]
        except Exception:
            pass

        try:
            cb = getattr(trace, "colorbar", None)
            if cb is not None:
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
    """Apply our figure theme and disable Streamlit's second chart theme layer."""
    if getattr(st, "_trade_war_plotly_theme_patched", False):
        return

    try:
        from streamlit.delta_generator import DeltaGenerator

        original_plotly_chart = DeltaGenerator.plotly_chart

        def themed_plotly_chart(self, figure_or_data, *args, **kwargs):
            try:
                if hasattr(figure_or_data, "update_layout") and hasattr(figure_or_data, "data"):
                    figure_or_data = apply_plotly_theme(figure_or_data)
                    # Streamlit's default theme="streamlit" can apply a second
                    # set of chart defaults after the figure reaches the browser.
                    # Disable that layer so our explicit light/dark text colors win.
                    kwargs["theme"] = None
            except Exception:
                pass
            return original_plotly_chart(self, figure_or_data, *args, **kwargs)

        DeltaGenerator.plotly_chart = themed_plotly_chart
    except Exception:
        original_plotly_chart = st.plotly_chart

        def themed_plotly_chart(figure_or_data, *args, **kwargs):
            try:
                if hasattr(figure_or_data, "update_layout") and hasattr(figure_or_data, "data"):
                    figure_or_data = apply_plotly_theme(figure_or_data)
                    kwargs["theme"] = None
            except Exception:
                pass
            return original_plotly_chart(figure_or_data, *args, **kwargs)

        st.plotly_chart = themed_plotly_chart

    st._trade_war_plotly_theme_patched = True


def inject_css():
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
        [data-testid="stAppViewContainer"],[data-testid="stMainBlockContainer"] { color:var(--app-text); }
        [data-testid="stSidebar"] { background:var(--app-background) !important; }
        [data-testid="stAlert"] { color:var(--app-text) !important; }
        [data-testid="stAlert"] p,[data-testid="stAlert"] span,[data-testid="stAlert"] strong { color:inherit !important; }
        .tw-panel { background:var(--app-secondary) !important; padding:1rem 1.25rem; border-radius:.5rem; border:1px solid var(--app-border); margin-bottom:1.5rem; }
        .tw-panel p,.tw-panel span,.tw-panel strong { color:var(--app-text); }
        .tw-panel .tw-muted,.tw-panel-inner .tw-muted,.tw-muted { color:var(--app-muted) !important; }
        .tw-panel-inner { background:var(--app-background) !important; padding:.8rem; border-radius:.4rem; border:1px solid var(--app-border); }
        .tw-panel-inner p,.tw-panel-inner span { color:var(--app-text); }
        .tw-hint { background:var(--app-secondary) !important; padding:.5rem .75rem; border-radius:.4rem; }
        .tw-hint p { color:inherit; }
        [data-testid="stDataFrame"] { color:var(--app-text) !important; }
        [data-testid="stPlotlyChart"] { margin-bottom:0 !important; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


patch_streamlit_plotly_chart()
