import streamlit as st


def inject_css():
    """Apply theme-aware shared styling without changing the light theme layout."""
    st.markdown('''<style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    [data-testid="metric-container"] { padding: 1.1rem; border-radius: .5rem; }
    h1 { font-weight: 700; }
    h2 { font-weight: 600; }

    /* Legacy cards use inline light-theme colours. Map them to Streamlit theme variables. */
    [style*="#f8fafc"], [style*="#F8FAFC"] {
        background: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border-color: var(--border-color) !important;
    }
    [style*="#eff6ff"], [style*="#EFF6FF"] {
        background: color-mix(in srgb, var(--primary-color) 12%, var(--secondary-background-color)) !important;
        color: var(--text-color) !important;
    }
    [style*="#dcfce7"], [style*="#DCFCE7"] {
        background: color-mix(in srgb, #22c55e 12%, var(--secondary-background-color)) !important;
        color: var(--text-color) !important;
    }
    [style*="#fef3c7"], [style*="#FEF3C7"] {
        background: color-mix(in srgb, #f59e0b 14%, var(--secondary-background-color)) !important;
        color: var(--text-color) !important;
    }
    [style*="#fee2e2"], [style*="#FEE2E2"] {
        background: color-mix(in srgb, #ef4444 12%, var(--secondary-background-color)) !important;
        color: var(--text-color) !important;
    }

    /* Inline dark text from the light theme must not become unreadable in dark mode. */
    [style*="#0f172a"], [style*="#0F172A"],
    [style*="#1f2937"], [style*="#1F2937"],
    [style*="#475569"], [style*="#64748b"], [style*="#64748B"],
    [style*="#666"] {
        color: var(--text-color) !important;
    }

    [style*="#e2e8f0"], [style*="#E2E8F0"] {
        border-color: var(--border-color) !important;
    }

    [data-testid="stAlert"] { color: var(--text-color); }
    [data-testid="stAlert"] p { color: inherit !important; }

    /*
       Scoped fix for legacy Demographics HTML blocks whose inline colours can
       become unreadable in dark mode. We deliberately do not change their
       backgrounds, spacing, borders, or the dependency-ratio card, so the
       existing light theme remains visually unchanged.
    */
    .tw-theme-text,
    .tw-theme-text strong {
        color: var(--text-color) !important;
    }
    .tw-theme-muted {
        color: var(--text-color) !important;
        opacity: 0.78;
    }
    </style>''', unsafe_allow_html=True)
