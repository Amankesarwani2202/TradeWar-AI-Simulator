import streamlit as st


def inject_css():
    """Apply shared, theme-aware styling across every page."""
    st.markdown(
        '''<style>
        .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        [data-testid="metric-container"] { padding: 1.1rem; border-radius: .5rem; }
        h1 { font-weight: 700; }
        h2 { font-weight: 600; }

        /*
         * Theme rule: custom HTML cards are used throughout the app and many
         * of them were authored with legacy light-mode colors. Streamlit can
         * normalize inline CSS values in the rendered DOM (for example,
         * #f8fafc -> rgb(...)), so matching one exact color string is not
         * reliable. Any custom markdown card that explicitly sets a
         * background therefore follows the active Streamlit theme instead.
         * Native Streamlit alerts/widgets are intentionally not included.
         */
        [data-testid="stMarkdownContainer"] div[style*="background"],
        [data-testid="stMarkdownContainer"] div[style*="background-color"] {
            background: var(--st-secondary-background-color) !important;
            color: var(--st-text-color) !important;
        }

        /* Make text inside legacy cards follow the active theme too. This is
           needed because many cards set text colors directly on <p>/<span>. */
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
            color: var(--st-text-color) !important;
        }

        /* Preserve semantic accent borders while making neutral borders theme-aware. */
        [data-testid="stMarkdownContainer"] div[style*="background"] {
            border-top-color: var(--st-border-color) !important;
            border-right-color: var(--st-border-color) !important;
            border-bottom-color: var(--st-border-color) !important;
        }

        /* Legacy light text used outside cards. */
        [style*="color:#0f172a"],
        [style*="color: #0f172a"],
        [style*="color:#0F172A"],
        [style*="color: #0F172A"],
        [style*="color:#111827"],
        [style*="color: #111827"],
        [style*="color:#1f2937"],
        [style*="color: #1f2937"],
        [style*="color:#1F2937"],
        [style*="color: #1F2937"],
        [style*="color:#374151"],
        [style*="color: #374151"],
        [style*="color:#475569"],
        [style*="color: #475569"] {
            color: var(--st-text-color) !important;
        }

        [style*="color:#64748b"],
        [style*="color: #64748b"],
        [style*="color:#64748B"],
        [style*="color: #64748B"],
        [style*="color:#6b7280"],
        [style*="color: #6b7280"],
        [style*="color:#6B7280"],
        [style*="color: #6B7280"],
        [style*="color:#666"],
        [style*="color: #666"] {
            color: var(--st-gray-text-color) !important;
        }

        /* Neutral inline surfaces -> active theme surfaces even when the
           browser normalizes the inline color value. */
        [style*="background:#f8fafc"],
        [style*="background: #f8fafc"],
        [style*="background:#F8FAFC"],
        [style*="background: #F8FAFC"],
        [style*="background:#ffffff"],
        [style*="background: #ffffff"],
        [style*="background:#FFFFFF"],
        [style*="background: #FFFFFF"],
        [style*="background:white"],
        [style*="background: white"] {
            background: var(--st-secondary-background-color) !important;
        }

        [style*="border:#e2e8f0"],
        [style*="border: #e2e8f0"],
        [style*="border:1px solid #e2e8f0"],
        [style*="border: 1px solid #e2e8f0"],
        [style*="border:1px solid #E2E8F0"],
        [style*="border: 1px solid #E2E8F0"] {
            border-color: var(--st-border-color) !important;
        }

        [data-testid="stAlert"] { color: var(--st-text-color); }
        [data-testid="stAlert"] p { color: inherit !important; }

        /* Plotly charts: keep canvas, grid, and labels aligned with the
           currently selected Streamlit theme. */
        .js-plotly-plot .plotly,
        .js-plotly-plot .plotly .main-svg,
        .js-plotly-plot .plotly .bg {
            background: var(--st-background-color) !important;
            fill: var(--st-background-color) !important;
        }
        .js-plotly-plot .plotly .gridlayer path,
        .js-plotly-plot .plotly .zerolinelayer path {
            stroke: var(--st-border-color) !important;
        }
        .js-plotly-plot .plotly .xtick text,
        .js-plotly-plot .plotly .ytick text,
        .js-plotly-plot .plotly .gtitle,
        .js-plotly-plot .plotly .xtitle,
        .js-plotly-plot .plotly .ytitle {
            fill: var(--st-text-color) !important;
        }
        </style>''',
        unsafe_allow_html=True,
    )
