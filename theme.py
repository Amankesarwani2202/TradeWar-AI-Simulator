import streamlit as st


def inject_css():
    """Apply theme-aware shared styling without changing the light theme layout."""
    st.markdown('''<style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    [data-testid="metric-container"] { padding: 1.1rem; border-radius: .5rem; }
    h1 { font-weight: 700; }
    h2 { font-weight: 600; }

    /* Legacy cards: preserve their existing light colours, but fix only text/border contrast. */
    [style*="#f8fafc"], [style*="#F8FAFC"] { border-color: var(--border-color) !important; }
    [style*="#e2e8f0"], [style*="#E2E8F0"] { border-color: var(--border-color) !important; }

    /* Existing inline text colours that are too dark for dark mode. */
    [style*="#0f172a"], [style*="#0F172A"],
    [style*="#1f2937"], [style*="#1F2937"],
    [style*="#475569"], [style*="#64748b"], [style*="#64748B"],
    [style*="#666"] {
        color: var(--text-color) !important;
    }

    /* Demographics-only text correction. Backgrounds are intentionally untouched
       so the current light theme remains exactly as designed. */
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

    /* Keep coloured status accents readable in both themes. */
    [style*="#16a34a"] { color: #16a34a !important; }

    [data-testid="stAlert"] { color: var(--text-color); }
    [data-testid="stAlert"] p { color: inherit !important; }
    </style>''', unsafe_allow_html=True)
