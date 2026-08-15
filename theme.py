import streamlit as st


def current_theme_type():
    """Return the active Streamlit theme type."""
    try:
        configured = st.get_option("theme.base")
        if configured in ("dark", "light"):
            return configured
    except Exception:
        pass
    try:
        theme_type = st.context.theme.type
        if theme_type in ("dark", "light"):
            return theme_type
    except Exception:
        pass
    return "dark"


def theme_colors():
    """Return concrete colors for the active theme.

    Use concrete values rather than undocumented CSS custom-property names so
    injected HTML and Plotly SVGs behave consistently across Streamlit versions.
    """
    if current_theme_type() == "dark":
        return {
            "background": "#0b1220",
            "secondary": "#111827",
            "text": "#e5e7eb",
            "muted": "#94a3b8",
            "border": "#334155",
            "grid": "#334155",
        }
    return {
        "background": "#ffffff",
        "secondary": "#f8fafc",
        "text": "#111827",
        "muted": "#64748b",
        "border": "#e2e8f0",
        "grid": "#e2e8f0",
    }


def apply_plotly_theme(fig):
    """Apply the active theme to every Plotly figure."""
    colors = theme_colors()
    fig.update_layout(
        template="plotly_dark" if current_theme_type() == "dark" else "plotly_white",
        paper_bgcolor=colors["background"],
        plot_bgcolor=colors["background"],
        font=dict(color=colors["text"]),
        title=dict(font=dict(color=colors["text"])),
        legend=dict(font=dict(color=colors["text"])),
    )
    fig.update_xaxes(
        title_font=dict(color=colors["text"]),
        tickfont=dict(color=colors["text"]),
        gridcolor=colors["grid"],
        zerolinecolor=colors["grid"],
        linecolor=colors["border"],
    )
    fig.update_yaxes(
        title_font=dict(color=colors["text"]),
        tickfont=dict(color=colors["text"]),
        gridcolor=colors["grid"],
        zerolinecolor=colors["grid"],
        linecolor=colors["border"],
    )
    return fig


def inject_css():
    """Apply shared theme-aware styling across the entire application."""
    colors = theme_colors()
    css = f"""
    <style>
        :root {{
            --app-background: {colors['background']};
            --app-secondary: {colors['secondary']};
            --app-text: {colors['text']};
            --app-muted: {colors['muted']};
            --app-border: {colors['border']};
        }}

        .main .block-container {{ padding-top: 2rem; padding-bottom: 2rem; }}
        [data-testid="metric-container"] {{ padding: 1.1rem; border-radius: .5rem; }}
        h1, h2, h3, h4, h5, h6 {{ font-weight: 600; color: {colors['text']} !important; }}
        p, li, label, [data-testid="stCaptionContainer"] {{ color: {colors['text']}; }}
        [data-testid="stCaptionContainer"] {{ color: {colors['muted']} !important; }}

        /* Convert hard-coded light cards/panels to the active theme. */
        [style*="background:#f8fafc"], [style*="background: #f8fafc"],
        [style*="background:#F8FAFC"], [style*="background: #F8FAFC"],
        [style*="background:#ffffff"], [style*="background: #ffffff"],
        [style*="background:#FFFFFF"], [style*="background: #FFFFFF"],
        [style*="background:white"], [style*="background: white"],
        [style*="background:#fff"], [style*="background: #fff"],
        [style*="background:#FFF"] {{
            background: {colors['secondary']} !important;
            color: {colors['text']} !important;
        }}

        [style*="color:#0f172a"], [style*="color: #0f172a"],
        [style*="color:#0F172A"], [style*="color: #0F172A"],
        [style*="color:#111827"], [style*="color: #111827"],
        [style*="color:#1f2937"], [style*="color: #1f2937"],
        [style*="color:#1F2937"], [style*="color: #1F2937"],
        [style*="color:#374151"], [style*="color: #374151"],
        [style*="color:#475569"], [style*="color: #475569"],
        [style*="color:#64748b"], [style*="color: #64748b"],
        [style*="color:#64748B"], [style*="color: #64748B"],
        [style*="color:#6b7280"], [style*="color: #6b7280"],
        [style*="color:#6B7280"], [style*="color: #6B7280"],
        [style*="color:#666"], [style*="color: #666"] {{
            color: {colors['text']} !important;
        }}

        [style*="border:#e2e8f0"], [style*="border: #e2e8f0"],
        [style*="border:1px solid #e2e8f0"], [style*="border: 1px solid #e2e8f0"],
        [style*="border:1px solid #E2E8F0"], [style*="border: 1px solid #E2E8F0"] {{
            border-color: {colors['border']} !important;
        }}

        /* Alert/callout text must remain readable on dark backgrounds. */
        [data-testid="stAlert"] {{ color: {colors['text']} !important; }}
        [data-testid="stAlert"] p, [data-testid="stAlert"] span {{ color: {colors['text']} !important; }}

        /* Plotly renders text as SVG attributes, so target the SVG directly. */
        .js-plotly-plot .plotly,
        .js-plotly-plot .plotly .main-svg,
        .js-plotly-plot .plotly .bg,
        .js-plotly-plot .plotly .plotbg,
        .js-plotly-plot .plotly .paperbg {{
            background: {colors['background']} !important;
            fill: {colors['background']} !important;
        }}
        .js-plotly-plot .plotly svg text,
        .js-plotly-plot .plotly .gtitle,
        .js-plotly-plot .plotly .xtitle,
        .js-plotly-plot .plotly .ytitle,
        .js-plotly-plot .plotly .xtick text,
        .js-plotly-plot .plotly .ytick text,
        .js-plotly-plot .plotly .legendtext,
        .js-plotly-plot .plotly .cbtitle,
        .js-plotly-plot .plotly .cbaxis text {{
            fill: {colors['text']} !important;
        }}
        .js-plotly-plot .plotly .gridlayer path,
        .js-plotly-plot .plotly .zerolinelayer path,
        .js-plotly-plot .plotly .xaxislayer-above path,
        .js-plotly-plot .plotly .yaxislayer-above path {{
            stroke: {colors['border']} !important;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
