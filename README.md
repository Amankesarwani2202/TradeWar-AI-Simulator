# TradeWar AI Simulator

A Streamlit app for exploring how tariff shocks ripple through Asian supply chains.

## Features
- Interactive tariff scenario controls for exporters, products, and policy actors
- Forecast charts for historical and projected export behavior
- Country-by-country impact tables and visualizations
- Trade dependency network view for understanding supply-chain fragility
- Teaching-oriented explanations for tariff incidence, trade diversion, and spillovers

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud
1. Push this repository to GitHub.
2. Create a new Streamlit Cloud app pointing to this repo.
3. Set the main file to app.py.
4. Streamlit Cloud will install the packages from requirements.txt automatically.
