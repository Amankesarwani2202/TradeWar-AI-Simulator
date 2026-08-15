import streamlit as st


def inject_css():
    """Apply shared styling while preserving the existing light-theme appearance."""
    st.markdown(
        '''<style>
        .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        [data-testid="metric-container"] { padding: 1.1rem; border-radius: .5rem; }
        h1 { font-weight: 700; }
        h2 { font-weight: 600; }

        /*
         * Dark-mode readability fixes for the legacy Demographics HTML.
         * These selectors deliberately target only the affected cards.
         * In particular, the dependency-ratio card is NOT selected.
         * No card backgrounds are overridden, so the existing light theme
         * remains visually unchanged.
         */

        /* Demographic profile summary: fix only its dark secondary text. */
        [style*="#f8fafc"][style*="#16a34a"] p[style*="#0f172a"],
        [style*="#f8fafc"][style*="#16a34a"] p[style*="#64748b"],
        [style*="#f8fafc"][style*="#16a34a"] p[style*="#64748B"] {
            color: var(--text-color) !important;
        }

        /* Sector-description cards: uniquely identified by their slate left border. */
        [style*="#f8fafc"][style*="#94a3b8"] p,
        [style*="#f8fafc"][style*="#94A3B8"] p {
            color: var(--text-color) !important;
        }

        /* Demographic phase / vulnerability cards. */
        [style*="#eff6ff"] > p,
        [style*="#dcfce7"] > p,
        [style*="#fef3c7"] > p,
        [style*="#fee2e2"] > p {
            color: var(--text-color) !important;
        }

        /* Legacy headings/subtitles that are genuinely too faint on dark mode. */
        [data-testid="stSidebar"] h2[style*="#1f2937"],
        [style*="#666"] {
            color: var(--text-color) !important;
        }

        /* Preserve the intentional green profile accent. */
        [style*="#16a34a"] p[style*="#16a34a"] {
            color: #16a34a !important;
        }

        [data-testid="stAlert"] { color: var(--text-color); }
        [data-testid="stAlert"] p { color: inherit !important; }
        </style>''',
        unsafe_allow_html=True,
    )
