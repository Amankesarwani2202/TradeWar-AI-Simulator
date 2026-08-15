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


def apply_plotly_theme(fig):
    """Apply consistent Streamlit-aware styling to every Plotly figure."""
    dark = current_theme_type() == "dark"
    background = "#0b1220" if dark else "#ffffff"
    text = "#e5e7eb" if dark else "#111827"
    grid = "#334155" if dark else "#e2e8f0"

    fig.update_layout(
        template="plotly_dark" if dark else "plotly_white",
        paper_bgcolor=background,
        plot_bgcolor=background,
        font=dict(color=text),
        title=dict(font=dict(color=text)),
        legend=dict(font=dict(color=text)),
        hoverlabel=dict(
            bgcolor="#111827" if dark else "#ffffff",
            font=dict(color=text),
            bordercolor=grid,
        ),
    )
    fig.update_xaxes(
        title_font=dict(color=text),
        tickfont=dict(color=text),
        gridcolor=grid,
        zerolinecolor=grid,
        linecolor=grid,
        color=text,
    )
    fig.update_yaxes(
        title_font=dict(color=text),
        tickfont=dict(color=text),
        gridcolor=grid,
        zerolinecolor=grid,
        linecolor=grid,
        color=text,
    )

    # Colorbars need their own font settings; figure-level font does not
    # reliably propagate to their title/ticks in Plotly.
    for trace in fig.data:
        try:
            colorbar = trace.marker.colorbar if trace.marker is not None else None
            if colorbar is not None:
                colorbar.title = dict(text=colorbar.title.text if colorbar.title else "", font=dict(color=text))
                colorbar.tickfont = dict(color=text)
                colorbar.outlinecolor = grid
        except Exception:
            pass
        try:
            colorbar = trace.colorbar
            if colorbar is not None:
                colorbar.title = dict(text=colorbar.title.text if colorbar.title else "", font=dict(color=text))
                colorbar.tickfont = dict(color=text)
                colorbar.outlinecolor = grid
        except Exception:
            pass

    return fig


def inject_css():
    """Apply shared theme-aware styling across every page."""
    st.markdown(
        '''<style>
        .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        [data-testid="metric-container"] { padding: 1.1rem; border-radius: .5rem; }
        h1, h2, h3, h4, h5, h6 { font-weight: 600; }

        [data-testid="stMarkdownContainer"] div[style*="background"],
        [data-testid="stMarkdownContainer"] div[style*="background-color"] {
            background: var(--secondary-background-color) !important;
            color: var(--text-color) !important;
        }
        [data-testid="stMarkdownContainer"] div[style*="background"] p,
        [data-testid="stMarkdownContainer"] div[style*="background"] span,
        [data-testid="stMarkdownContainer"] div[style*="background"] strong,
        [data-testid="stMarkdownContainer"] div[style*="background"] b,
        [data-testid="stMarkdownContainer"] div[style*="background"] em,
        [data-testid="stMarkdownContainer"] div[style*="background-color"] p,
        [data-testid="stMarkdownContainer"] div[style*="background-color"] span,
        [data-testid="stMarkdownContainer"] div[style*="background-color"] strong,
        [data-testid="stMarkdownContainer"] div[style*="background-color"] b,
        [data-testid="stMarkdownContainer"] div[style*="background-color"] em {
            color: var(--text-color) !important;
        }

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
        [style*="color:#666"], [style*="color: #666"] {
            color: var(--text-color) !important;
        }

        [style*="background:#f8fafc"], [style*="background: #f8fafc"],
        [style*="background:#F8FAFC"], [style*="background: #F8FAFC"],
        [style*="background:#ffffff"], [style*="background: #ffffff"],
        [style*="background:#FFFFFF"], [style*="background: #FFFFFF"],
        [style*="background:white"], [style*="background: white"] {
            background: var(--secondary-background-color) !important;
        }

        [style*="border:#e2e8f0"], [style*="border: #e2e8f0"],
        [style*="border:1px solid #e2e8f0"], [style*="border: 1px solid #e2e8f0"],
        [style*="border:1px solid #E2E8F0"], [style*="border: 1px solid #E2E8F0"] {
            border-color: var(--border-color) !important;
        }

        [data-testid="stAlert"] { color: var(--text-color); }
        [data-testid="stAlert"] p { color: inherit !important; }

        /* Plotly SVGs do not inherit Streamlit text color consistently.
           Use the actual Streamlit CSS variables instead of hard-coded black. */
        .js-plotly-plot .plotly svg text,
        .js-plotly-plot .plotly .gtitle,
        .js-plotly-plot .plotly .xtitle,
        .js-plotly-plot .plotly .ytitle,
        .js-plotly-plot .plotly .xtick text,
        .js-plotly-plot .plotly .ytick text,
        .js-plotly-plot .plotly .legendtext,
        .js-plotly-plot .plotly .cbtitle,
        .js-plotly-plot .plotly .cbaxis text {
            fill: var(--text-color) !important;
        }
        .js-plotly-plot .plotly .gridlayer path,
        .js-plotly-plot .plotly .zerolinelayer path,
        .js-plotly-plot .plotly .xaxislayer-above path,
        .js-plotly-plot .plotly .yaxislayer-above path {
            stroke: var(--border-color) !important;
        }
        </style>''',
        unsafe_allow_html=True,
    )
