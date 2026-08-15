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
         * The app supports both Streamlit light and dark themes. A number of
         * pages still contain inline colors from the original light design.
         * Streamlit exposes the active theme through --st-* CSS variables, so
         * normalize those legacy inline colors here instead of maintaining
         * separate dark-mode hacks on individual pages.
         */

        /* Light neutral surfaces -> active theme surfaces. */
        [style*="background:#f8fafc"],
        [style*="background: #f8fafc"],
        [style*="background:#F8FAFC"],
        [style*="background: #F8FAFC"] {
            background: var(--st-secondary-background-color) !important;
        }

        [style*="background:#ffffff"],
        [style*="background: #ffffff"],
        [style*="background:#FFFFFF"],
        [style*="background: #FFFFFF"],
        [style*="background:white"],
        [style*="background: white"] {
            background: var(--st-background-color) !important;
        }

        /* Semantic status cards keep their meaning in both themes. */
        [style*="background:#dcfce7"],
        [style*="background: #dcfce7"],
        [style*="background:#DCFCE7"],
        [style*="background: #DCFCE7"] {
            background: var(--st-green-background-color) !important;
        }

        [style*="background:#fef3c7"],
        [style*="background: #fef3c7"],
        [style*="background:#FEF3C7"],
        [style*="background: #FEF3C7"] {
            background: var(--st-yellow-background-color) !important;
        }

        [style*="background:#fee2e2"],
        [style*="background: #fee2e2"],
        [style*="background:#FEE2E2"],
        [style*="background: #FEE2E2"] {
            background: var(--st-red-background-color) !important;
        }

        [style*="background:#eff6ff"],
        [style*="background: #eff6ff"],
        [style*="background:#EFF6FF"],
        [style*="background: #EFF6FF"] {
            background: var(--st-blue-background-color) !important;
        }

        /* Legacy neutral text -> active theme text hierarchy. */
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

        /* Legacy borders -> active theme borders. */
        [style*="border:#e2e8f0"],
        [style*="border: #e2e8f0"],
        [style*="border:1px solid #e2e8f0"],
        [style*="border: 1px solid #e2e8f0"],
        [style*="border:1px solid #E2E8F0"],
        [style*="border: 1px solid #E2E8F0"] {
            border-color: var(--st-border-color) !important;
        }

        [style*="border-left:3px solid #94a3b8"],
        [style*="border-left: 3px solid #94a3b8"],
        [style*="border-left:3px solid #94A3B8"],
        [style*="border-left: 3px solid #94A3B8"] {
            border-left-color: var(--st-gray-color) !important;
        }

        /* Sidebar headings that were explicitly forced to dark text. */
        [data-testid="stSidebar"] h2[style*="#1f2937"],
        [data-testid="stSidebar"] h2[style*="#1F2937"] {
            color: var(--st-text-color) !important;
        }

        /* Alerts should always inherit the active theme's readable text. */
        [data-testid="stAlert"] { color: var(--st-text-color); }
        [data-testid="stAlert"] p { color: inherit !important; }

        /* Keep intentional semantic accent text intact. */
        [style*="color:#16a34a"],
        [style*="color: #16a34a"],
        [style*="color:#16A34A"],
        [style*="color: #16A34A"],
        [style*="color:#22c55e"],
        [style*="color: #22c55e"],
        [style*="color:#ef4444"],
        [style*="color: #ef4444"],
        [style*="color:#f59e0b"],
        [style*="color: #f59e0b"] {
            /* The declaration is intentionally not replaced; these selectors
               exist so the semantic accent rules remain explicit and easy to
               extend without changing the neutral text normalization above. */
        }
        </style>''',
        unsafe_allow_html=True,
    )
