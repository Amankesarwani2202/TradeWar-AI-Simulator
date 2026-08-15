import streamlit as st


def inject_css():
    """Apply theme-aware shared styling without changing the light theme layout."""
    st.markdown('''<style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    [data-testid="metric-container"] { padding: 1.1rem; border-radius: .5rem; }
    h1 { font-weight: 700; }
    h2 { font-weight: 600; }

    /* Keep the existing card backgrounds and borders exactly as designed. */
    [style*="#f8fafc"], [style*="#F8FAFC"] {
        background: var(--secondary-background-color) !important;
        border-color: var(--st-border-color, var(--border-color)) !important;
    }
    [style*="#eff6ff"], [style*="#EFF6FF"] {
        background: color-mix(in srgb, var(--primary-color) 12%, var(--secondary-background-color)) !important;
    }
    [style*="#dcfce7"], [style*="#DCFCE7"] {
        background: color-mix(in srgb, #22c55e 12%, var(--secondary-background-color)) !important;
    }
    [style*="#fef3c7"], [style*="#FEF3C7"] {
        background: color-mix(in srgb, #f59e0b 14%, var(--secondary-background-color)) !important;
    }
    [style*="#fee2e2"], [style*="#FEE2E2"] {
        background: color-mix(in srgb, #ef4444 12%, var(--secondary-background-color)) !important;
    }

    /* Only fix text inside the legacy Demographics cards that is hard to read
       in dark mode. No layout/background changes are made here. */
    [style*="#f8fafc"] p,
    [style*="#f8fafc"] strong,
    [style*="#f8fafc"] span,
    [style*="#eff6ff"] p,
    [style*="#eff6ff"] strong,
    [style*="#dcfce7"] p,
    [style*="#dcfce7"] strong,
    [style*="#fef3c7"] p,
    [style*="#fef3c7"] strong,
    [style*="#fee2e2"] p,
    [style*="#fee2e2"] strong {
        color: var(--text-color) !important;
    }

    /* Preserve intentional green status/accent text. */
    [style*="#16a34a"] { color: #16a34a !important; }

    /* Existing inline dark text from the light theme. */
    [style*="#0f172a"], [style*="#0F172A"],
    [style*="#1f2937"], [style*="#1F2937"],
    [style*="#475569"], [style*="#64748b"], [style*="#64748B"],
    [style*="#666"] {
        color: var(--text-color) !important;
    }

    [style*="#e2e8f0"], [style*="#E2E8F0"] {
        border-color: var(--st-border-color, var(--border-color)) !important;
    }

    [data-testid="stAlert"] { color: var(--text-color); }
    [data-testid="stAlert"] p { color: inherit !important; }
    </style>''', unsafe_allow_html=True)
