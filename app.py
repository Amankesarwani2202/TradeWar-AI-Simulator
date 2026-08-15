import streamlit as st
from utils import inject_css, COUNTRY_PROFILES
from live_data import refresh_profiles, live_timestamp

st.set_page_config(page_title='TradeWar AI Simulator', page_icon='🌏', layout='wide', initial_sidebar_state='expanded')

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# Refresh macro/demographic inputs from public APIs; keep existing values as fallbacks.
try:
    live_profiles, live_years = refresh_profiles(COUNTRY_PROFILES)
    COUNTRY_PROFILES.update(live_profiles)
except Exception:
    live_years = {}


def home():
    inject_css()
    st.sidebar.toggle('🌙 Dark mode', key='dark_mode', help='Switch the simulator UI between light and dark presentation.')
    st.sidebar.caption(f'Live data refresh: {live_timestamp()}')
    if st.session_state.dark_mode:
        st.markdown('''<style>body,.stApp{background:#0b1220!important;color:#e5e7eb!important}.main .block-container{color:#e5e7eb}.stMarkdown,h1,h2,h3,p,label{color:#e5e7eb!important}.stButton>button,.stSelectbox>div>div,.stTextInput>div>div{background:#111827!important;color:#f9fafb!important;border-color:#374151!important}.stDataFrame{background:#111827!important}.stAlert{background:#172033!important;color:#e5e7eb!important} </style>''', unsafe_allow_html=True)

    st.markdown('''<div style="padding:2rem 0 1.5rem;border-bottom:1px solid #334155;margin-bottom:2rem"><h1>🌏 TradeWar AI Simulator</h1><p style="max-width:720px;line-height:1.65">Explore how tariffs and trade shocks reshape supply chains, financial markets and demographics. Macro and market inputs are refreshed from live public sources where available.</p></div>''', unsafe_allow_html=True)
    cols=st.columns(5)
    cards=[('⚙️','Custom Scenario','Model tariff changes and trade diversion.','pages/1_Scenario.py'),('🔄','Historical Counterfactual','Explore alternative policy histories.','pages/2_Historical_Counterfactual.py'),('💹','Financial Markets','Track live market conditions and tariff scenarios.','pages/3_Financial_Markets.py'),('🌐','Global Market Explorer','Compare multiple indices and any Yahoo Finance ticker.','pages/5_Global_Market_Explorer.py'),('👥','Demographics','Explore live macro and demographic indicators.','pages/4_Demographics.py')]
    for col,(icon,title,desc,page) in zip(cols,cards):
        with col:
            st.markdown(f'<div style="padding:1.2rem;border:1px solid #334155;border-radius:.6rem;min-height:150px"><div style="font-size:1.4rem">{icon}</div><b>{title}</b><p style="font-size:.82rem;line-height:1.5">{desc}</p></div>',unsafe_allow_html=True)
            st.page_link(page,label='Open →',use_container_width=True)
    st.info('**Data note:** trade-flow baselines remain synthetic for reproducible policy experiments. Macro, demographic and FX inputs are refreshed from public APIs; market prices use yfinance. Live sources can fail temporarily, so the app retains safe fallbacks.')

pg=st.navigation({'':[st.Page(home,title='Home',icon='🏠',default=True)],'Simulator':[
    st.Page('pages/1_Scenario.py',title='Custom Scenario',icon='⚙️'),st.Page('pages/2_Historical_Counterfactual.py',title='Historical Counterfactual',icon='🔄'),st.Page('pages/3_Financial_Markets.py',title='Financial Markets',icon='💹'),st.Page('pages/5_Global_Market_Explorer.py',title='Global Market Explorer',icon='🌐'),st.Page('pages/4_Demographics.py',title='Demographics',icon='👥')]})
pg.run()
