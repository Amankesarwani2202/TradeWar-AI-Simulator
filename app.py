import streamlit as st
import utils
from beneficiary import build_country_scenario as continuous_build_country_scenario
from utils import inject_css
from live_data import live_timestamp

# Pages import build_country_scenario from utils. Replace that implementation at
# startup so the existing scenario page uses the continuous beneficiary model.
utils.build_country_scenario = continuous_build_country_scenario

st.set_page_config(page_title="TradeWar AI Simulator", page_icon="🌏", layout="wide", initial_sidebar_state="expanded")


def home():
    inject_css()
    st.sidebar.caption("🌗 **Theme:** use ⋮ → Settings → Theme to switch between the configured light and dark themes.")
    st.sidebar.caption(f"🌐 Live data layer: {live_timestamp()}")

    st.markdown("""<div style="padding:2rem 0 1.5rem;border-bottom:1px solid var(--st-border-color);margin-bottom:2rem"><h1>🌏 TradeWar AI Simulator</h1><p style="max-width:720px;line-height:1.65">Explore how tariffs and trade shocks reshape supply chains, financial markets and demographics. Macro, demographic, FX and market inputs are refreshed from live public sources where available.</p></div>""", unsafe_allow_html=True)
    cols = st.columns(5)
    cards = [
        ("⚙️", "Custom Scenario", "Model tariff changes and trade diversion.", "pages/1_Scenario.py"),
        ("🔄", "Historical Counterfactual", "Explore alternative policy histories.", "pages/2_Historical_Counterfactual.py"),
        ("💹", "Financial Markets", "Track live market conditions and tariff scenarios.", "pages/3_Financial_Markets.py"),
        ("🌐", "Global Market Explorer", "Compare global indices, listed assets and any Yahoo Finance ticker.", "pages/5_Global_Market_Explorer.py"),
        ("👥", "Demographics", "Explore refreshed macro and demographic indicators.", "pages/4_Demographics.py"),
    ]
    for col, (icon, title, desc, page) in zip(cols, cards):
        with col:
            st.markdown(f'<div style="padding:1.2rem;border:1px solid var(--st-border-color);border-radius:.6rem;min-height:150px"><div style="font-size:1.4rem">{icon}</div><b>{title}</b><p style="font-size:.82rem;line-height:1.5">{desc}</p></div>', unsafe_allow_html=True)
            st.page_link(page, label="Open →", use_container_width=True)
    st.info("**Data note:** trade-flow baselines remain synthetic for reproducible policy experiments. Macro/demographic data are loaded lazily from public APIs when a country is viewed; market prices use live exchange/provider data. External data can fail temporarily, in which case the affected metric is marked unavailable.")


pg = st.navigation({"": [st.Page(home, title="Home", icon="🏠", default=True)], "Simulator": [
    st.Page("pages/1_Scenario.py", title="Custom Scenario", icon="⚙️"),
    st.Page("pages/2_Historical_Counterfactual.py", title="Historical Counterfactual", icon="🔄"),
    st.Page("pages/3_Financial_Markets.py", title="Financial Markets", icon="💹"),
    st.Page("pages/5_Global_Market_Explorer.py", title="Global Market Explorer", icon="🌐"),
    st.Page("pages/4_Demographics.py", title="Demographics", icon="👥"),
]})
pg.run()
