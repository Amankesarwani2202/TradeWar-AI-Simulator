import streamlit as st
import utils
from beneficiary import build_country_scenario as continuous_build_country_scenario
from theme import inject_css
from utils import COUNTRY_PROFILES
from live_data import refresh_profiles, live_timestamp

utils.build_country_scenario = continuous_build_country_scenario
utils.inject_css = inject_css

st.set_page_config(page_title="TradeWar AI Simulator", page_icon="🌏", layout="wide", initial_sidebar_state="expanded")

try:
    live_profiles, live_years = refresh_profiles(COUNTRY_PROFILES)
    COUNTRY_PROFILES.update(live_profiles)
except Exception:
    live_years = {}


def home():
    inject_css()
    st.sidebar.caption("🌗 **Theme:** use ⋮ → Settings → Theme to switch between the configured light and dark themes.")
    st.sidebar.caption(f"🌐 Macro data refresh: {live_timestamp()}")

    st.markdown("""<div style="padding:2rem 0 1.5rem;border-bottom:1px solid var(--st-border-color);margin-bottom:2rem"><h1>🌏 TradeWar AI Simulator</h1><p style="max-width:720px;line-height:1.65">Explore how tariffs and trade shocks reshape supply chains, financial markets and demographics. Macro, demographic, FX and market inputs are refreshed from live public sources where available.</p></div>""", unsafe_allow_html=True)
    cols = st.columns(5)
    cards = [
        ("⚙️", "Custom Scenario", "Model tariff changes and trade diversion.", "pages/1_Scenario.py"),
        ("🔬", "Historical Data Lab", "Upload real historical data, run statistics, forecasts and counterfactuals.", "pages/6_Historical_Data_Lab.py"),
        ("🔄", "Historical Counterfactual", "Explore alternative policy histories.", "pages/2_Historical_Counterfactual.py"),
        ("💹", "Financial Markets", "Track live market conditions and tariff scenarios.", "pages/3_Financial_Markets.py"),
        ("👥", "Demographics", "Explore refreshed macro and demographic indicators.", "pages/4_Demographics.py"),
    ]
    for col, (icon, title, desc, page) in zip(cols, cards):
        with col:
            st.markdown(f'<div style="padding:1.2rem;border:1px solid var(--st-border-color);border-radius:.6rem;min-height:150px"><div style="font-size:1.4rem">{icon}</div><b>{title}</b><p style="font-size:.82rem;line-height:1.5">{desc}</p></div>', unsafe_allow_html=True)
            st.page_link(page, label="Open →", use_container_width=True)
    st.info("**Data note:** built-in trade-flow data remain synthetic for reproducible policy experiments. The Historical Data Lab lets users replace the synthetic dataset with real observations and clearly separates statistical/economic estimates from illustrative scenarios.")


pg = st.navigation({"": [st.Page(home, title="Home", icon="🏠", default=True)], "Simulator": [
    st.Page("pages/1_Scenario.py", title="Custom Scenario", icon="⚙️"),
    st.Page("pages/6_Historical_Data_Lab.py", title="Historical Data Lab", icon="🔬"),
    st.Page("pages/2_Historical_Counterfactual.py", title="Historical Counterfactual", icon="🔄"),
    st.Page("pages/3_Financial_Markets.py", title="Financial Markets", icon="💹"),
    st.Page("pages/5_Global_Market_Explorer.py", title="Global Market Explorer", icon="🌐"),
    st.Page("pages/4_Demographics.py", title="Demographics", icon="👥"),
]})
pg.run()
