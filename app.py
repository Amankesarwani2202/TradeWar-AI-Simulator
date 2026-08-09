import streamlit as st
from utils import inject_css

st.set_page_config(
    page_title="TradeWar AI Simulator",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded",
)


def home():
    inject_css()

    st.markdown(
        """
        <div style="padding: 2rem 0 1.5rem 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 2rem;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #0f172a; margin-bottom: 0.4rem;">🌏 TradeWar AI Simulator</h1>
            <p style="font-size: 0.95rem; color: #64748b; max-width: 640px; line-height: 1.65; margin: 0;">
                An interactive platform for exploring how trade policies, tariffs, and economic shocks
                reshape supply chains, financial markets, and demographics across 10 major economies.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4, gap="medium")

    _CARD = (
        "background:#fff;padding:1.5rem;border-radius:0.5rem;"
        "border:1px solid #e2e8f0;border-top:3px solid {accent};"
        "box-shadow:0 1px 3px rgba(0,0,0,0.05);min-height:200px;"
    )

    def _card(icon, title, desc, accent):
        return (
            f'<div style="{_CARD.format(accent=accent)}">'
            f'<p style="margin:0 0 0.5rem 0;font-size:1.4rem;">{icon}</p>'
            f'<p style="margin:0 0 0.4rem 0;font-size:0.95rem;font-weight:700;color:#1e293b;">{title}</p>'
            f'<p style="margin:0;font-size:0.82rem;color:#64748b;line-height:1.6;">{desc}</p>'
            f'</div>'
        )

    with col1:
        st.markdown(_card("⚙️", "Custom Scenario",
            "Simulate present-day tariff policies. Choose from 28 presets or build your own, and trace how trade flows shift across supply chains.",
            "#2563eb"), unsafe_allow_html=True)
        st.page_link("pages/1_Scenario.py", label="Open Custom Scenario →", use_container_width=True)

    with col2:
        st.markdown(_card("🔄", "Historical Counterfactual",
            "Explore alternative history — 1991 Indian liberalisation, 2018 trade war de-escalation, COVID trade policy alternatives.",
            "#7c3aed"), unsafe_allow_html=True)
        st.page_link("pages/2_Historical_Counterfactual.py", label="Open Counterfactual →", use_container_width=True)

    with col3:
        st.markdown(_card("💹", "Financial Markets",
            "Track stock indices, currency rates, and market sentiment. Model how tariff shocks ripple into financial markets.",
            "#0891b2"), unsafe_allow_html=True)
        st.page_link("pages/3_Financial_Markets.py", label="Open Financial Markets →", use_container_width=True)

    with col4:
        st.markdown(_card("👥", "Demographics",
            "Explore population pyramids, workforce composition, and sector breakdowns. Forecast demographic shifts and trade vulnerability.",
            "#16a34a"), unsafe_allow_html=True)
        st.page_link("pages/4_Demographics.py", label="Open Demographics →", use_container_width=True)

    st.markdown("<div style='margin-top:2.5rem;'></div>", unsafe_allow_html=True)

    st.markdown(
        "<p style='font-size:0.85rem;font-weight:600;color:#374151;margin-bottom:0.75rem;'>What this simulator teaches</p>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3, gap="medium")
    _INFO = "background:#f8fafc;padding:1.1rem;border-radius:0.4rem;border:1px solid #e2e8f0;border-left:3px solid {c};"

    with c1:
        st.markdown(
            f'<div style="{_INFO.format(c="#2563eb")}">'
            '<p style="margin:0 0 0.3rem 0;font-weight:600;color:#1e40af;font-size:0.85rem;">Tariff Mechanics</p>'
            '<p style="margin:0;font-size:0.82rem;color:#475569;line-height:1.6;">How a tax on imports raises prices, shifts demand to alternatives, and triggers supply chain reorganisation across interconnected economies.</p>'
            '</div>', unsafe_allow_html=True)

    with c2:
        st.markdown(
            f'<div style="{_INFO.format(c="#7c3aed")}">'
            '<p style="margin:0 0 0.3rem 0;font-weight:600;color:#6d28d9;font-size:0.85rem;">Trade Diversion & Comparative Advantage</p>'
            '<p style="margin:0;font-size:0.82rem;color:#475569;line-height:1.6;">When tariffs block one route, trade doesn\'t disappear — it diverts. Explore which countries gain and why the cheapest option wins.</p>'
            '</div>', unsafe_allow_html=True)

    with c3:
        st.markdown(
            f'<div style="{_INFO.format(c="#16a34a")}">'
            '<p style="margin:0 0 0.3rem 0;font-weight:600;color:#166534;font-size:0.85rem;">Supply Chain Fragility</p>'
            '<p style="margin:0;font-size:0.82rem;color:#475569;line-height:1.6;">Network analysis shows which economies are hubs, which are exposed, and how a single policy shock ripples across the global trading system.</p>'
            '</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    st.info(
        "**Data note**: All trade figures are synthetic baselines calibrated to real 2015–2024 patterns. "
        "Financial market data can be augmented with live yfinance tickers. Scenarios are illustrative — designed for education and policy exploration, not investment advice."
    )

    st.markdown(
        '<p style="text-align:center;font-size:0.76rem;color:#9ca3af;border-top:1px solid #e5e7eb;margin-top:2rem;padding-top:1rem;">'
        'TradeWar AI Simulator v2.0 &nbsp;·&nbsp; Built with Streamlit &nbsp;·&nbsp; Data: Synthetic + yfinance'
        '</p>',
        unsafe_allow_html=True,
    )


pg = st.navigation(
    {
        "": [
            st.Page(home, title="Home", icon="🏠", default=True),
        ],
        "Simulator": [
            st.Page("pages/1_Scenario.py", title="Custom Scenario", icon="⚙️"),
            st.Page("pages/2_Historical_Counterfactual.py", title="Historical Counterfactual", icon="🔄"),
            st.Page("pages/3_Financial_Markets.py", title="Financial Markets", icon="💹"),
            st.Page("pages/4_Demographics.py", title="Demographics", icon="👥"),
        ],
    }
)
pg.run()
