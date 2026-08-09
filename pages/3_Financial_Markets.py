import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils import (
    COUNTRIES, YEARS, TRADE_ELASTICITY,
    COUNTRY_PROFILES, inject_css, generate_trade_data,
    forecast_series,
)

try:
    import yfinance as yf
except Exception:
    yf = None

inject_css()

np.random.seed(42)
df = generate_trade_data()

# Map each country to its ticker and display label (shown to user for clarity)
TICKER_GUIDE = {
    "India":       {"ticker": "^NSEI",     "label": "NIFTY 50 (NSE India)", "currency": "INR"},
    "China":       {"ticker": "000001.SS", "label": "SSE Composite (Shanghai)", "currency": "CNY"},
    "US":          {"ticker": "SPY",       "label": "S&P 500 ETF (NYSE)", "currency": "USD"},
    "EU":          {"ticker": "^STOXX50E", "label": "Euro Stoxx 50", "currency": "EUR"},
    "Vietnam":     {"ticker": "^VNINDEX",  "label": "VN-Index (HOSE)", "currency": "VND"},
    "Bangladesh":  {"ticker": "DSEX.BD",   "label": "DSEX (Dhaka Stock Exchange)", "currency": "BDT"},
    "Japan":       {"ticker": "^N225",     "label": "Nikkei 225 (TSE)", "currency": "JPY"},
    "South Korea": {"ticker": "^KS11",     "label": "KOSPI (KRX)", "currency": "KRW"},
    "Taiwan":      {"ticker": "^TWII",     "label": "TAIEX (TWSE)", "currency": "TWD"},
    "Thailand":    {"ticker": "^SET.BK",   "label": "SET Index (SET)", "currency": "THB"},
}


def get_market_data(ticker, profile, currency_label=""):
    """Fetch live market data via yfinance; falls back to synthetic if unavailable."""
    daily_change_pct = round(np.random.uniform(-1.5, 1.5), 2)
    synthetic_base = profile.get("market_cap_bn", 500) * 10
    result = {
        "latest_close": round(synthetic_base * np.random.uniform(0.9, 1.1), 2),
        "yoy_return_pct": round(profile.get("gdp_growth", 3.0) * 2.5 + np.random.uniform(-8, 8), 2),
        "sentiment": "Upward" if daily_change_pct >= 0 else "Cautious",
        "volatility": "High" if abs(daily_change_pct) > 1.0 else "Moderate",
        "daily_change_pct": daily_change_pct,
        "market_cap_bn": profile.get("market_cap_bn", 500),
        "data_source": "synthetic",
        "currency_label": currency_label,
    }
    if yf is not None and ticker:
        try:
            data = yf.download(ticker, period="2y", progress=False, auto_adjust=True)
            if not data.empty:
                result["latest_close"] = round(float(data["Close"].iloc[-1]), 2)
                result["daily_change_pct"] = round(float((data["Close"].iloc[-1] / data["Close"].iloc[-2] - 1) * 100), 2)
                result["sentiment"] = "Upward" if result["daily_change_pct"] >= 0 else "Cautious"
                result["volatility"] = "High" if data["Close"].pct_change().abs().mean() > 0.02 else "Moderate"
                if len(data) > 252:
                    result["yoy_return_pct"] = round(float((data["Close"].iloc[-1] / data["Close"].iloc[-252] - 1) * 100), 2)
                result["data_source"] = "live"
        except Exception:
            pass
    return result


def generate_synthetic_market_series(profile, steps=5):
    gdp = profile.get("gdp_growth", 3.0)
    inf = profile.get("inflation", 3.0)
    base = profile.get("market_cap_bn", 500) * 10
    series = [base]
    for _ in range(len(YEARS) - 1):
        growth = 1 + (gdp / 100) - (inf / 200) + np.random.uniform(-0.05, 0.08)
        series.append(series[-1] * growth)
    return series


def build_market_prediction(profile, event_type, intensity_pct):
    gdp = profile.get("gdp_growth", 3.0)
    inf = profile.get("inflation", 3.0)
    base_series = generate_synthetic_market_series(profile)
    baseline_forecast = forecast_series(np.array(base_series), steps=5)

    shocks = {
        "Tariff increase (trade partner)": -0.4,
        "Tariff reduction (market access)": 0.3,
        "Currency devaluation": -0.25,
        "Foreign direct investment surge": 0.45,
        "Interest rate hike": -0.35,
        "Interest rate cut": 0.3,
        "Supply chain shock": -0.5,
        "Commodity price spike": -0.2 if gdp < 3 else 0.1,
    }
    multiplier = 1 + (intensity_pct / 100) * shocks.get(event_type, 0)
    scenario_forecast = np.maximum(0, baseline_forecast * multiplier)
    return base_series, baseline_forecast, scenario_forecast


# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown("<h2 style='font-size:1.3rem;color:#1f2937;margin-bottom:0.75rem;'>💹 Market Settings</h2>", unsafe_allow_html=True)

country = st.sidebar.selectbox("Select country", COUNTRIES)
profile = COUNTRY_PROFILES.get(country, {})
ticker_info = TICKER_GUIDE.get(country, {"ticker": "SPY", "label": "S&P 500 ETF", "currency": "USD"})

st.sidebar.markdown(
    f"**Market index for {country}:**\n\n"
    f"📈 **{ticker_info['label']}**\n\n"
    f"Ticker symbol: `{ticker_info['ticker']}` (Yahoo Finance)\n\n"
    f"Currency: **{ticker_info['currency']}** — prices shown are in {ticker_info['currency']}, not USD.",
)
custom_ticker = st.sidebar.text_input(
    "Override ticker symbol",
    value=ticker_info["ticker"],
    help=f"Default is {ticker_info['ticker']} ({ticker_info['label']}). Enter any valid Yahoo Finance ticker to override.",
)

st.sidebar.divider()
st.sidebar.markdown("**Market scenario prediction**")
st.sidebar.caption("Choose an economic event and see how it shifts the market forecast.")
prediction_event = st.sidebar.selectbox(
    "Economic / policy event",
    [
        "Tariff increase (trade partner)",
        "Tariff reduction (market access)",
        "Currency devaluation",
        "Foreign direct investment surge",
        "Interest rate hike",
        "Interest rate cut",
        "Supply chain shock",
        "Commodity price spike",
    ],
)
prediction_intensity = st.sidebar.slider(
    "Event intensity (%)",
    min_value=5, max_value=50, value=20, step=5,
    help="How large is the event? 5% = minor, 50% = major shock.",
)
compare_country = st.sidebar.selectbox("Compare with", [c for c in COUNTRIES if c != country])

# ── Main content ─────────────────────────────────────────────────────────────
st.title("💹 Financial Markets")
st.markdown(
    '<p style="font-size:1.05rem;color:#6b7280;margin-top:-0.75rem;margin-bottom:1.5rem;">'
    "Current market status, currency context, key news, and how economic events shift market forecasts"
    "</p>",
    unsafe_allow_html=True,
)

market_data = get_market_data(custom_ticker, profile, currency_label=ticker_info["currency"])

# Current market status banner
gdp = profile.get("gdp_growth", 0)
inf = profile.get("inflation", 0)
currency = ticker_info["currency"]
fx = profile.get("currency_vs_usd", 1.0)
stock_index = ticker_info["label"]
data_badge = "🟢 Live data (yfinance)" if market_data["data_source"] == "live" else "🟡 Synthetic data (yfinance unavailable)"

st.markdown(
    f"""
    <div style="background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);padding:1.5rem;border-radius:0.75rem;color:white;margin-bottom:1.5rem;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
                <p style="margin:0;font-size:0.7rem;opacity:0.75;text-transform:uppercase;letter-spacing:0.08em;">Market Overview</p>
                <h3 style="color:white;margin:0.2rem 0 0.5rem 0;font-size:1.15rem;">📊 {country} · {stock_index}</h3>
                <p style="margin:0;font-size:0.88rem;opacity:0.9;">
                    Ticker: <strong>{custom_ticker}</strong> &nbsp;|&nbsp;
                    Currency: <strong>{currency}</strong> ({fx:,.2f} per USD) &nbsp;|&nbsp;
                    GDP: {gdp:.1f}% &nbsp;|&nbsp; Inflation: {inf:.1f}%
                </p>
            </div>
            <div style="background:rgba(255,255,255,0.15);padding:0.4rem 0.8rem;border-radius:0.4rem;font-size:0.75rem;">
                {data_badge}
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if market_data["data_source"] == "synthetic":
    st.info(
        f"📡 **Live data unavailable** for ticker `{custom_ticker}`. "
        "The prices shown below are synthetic (model-generated from macro data). "
        "To get live data, install `yfinance` and ensure the ticker symbol is valid on Yahoo Finance."
    )

# Key metrics row — clearly labelled with currency context
col1, col2, col3, col4, col5 = st.columns(5, gap="small")
with col1:
    close = market_data["latest_close"]
    close_label = f"{currency} {close:,.2f}" if close is not None else "N/A (synthetic)"
    st.metric(
        f"💰 Latest Close ({currency})",
        close_label,
        help=f"Latest closing price of {custom_ticker} in {currency}. "
             f"Note: index prices are in local currency — NOT in USD.",
    )
with col2:
    daily = market_data["daily_change_pct"]
    st.metric(
        "📊 Daily Change",
        f"{daily:+.2f}%",
        delta=f"{daily:+.2f}%",
        delta_color="normal" if daily >= 0 else "inverse",
        help="Change from previous closing price as a percentage.",
    )
with col3:
    yoy = market_data.get("yoy_return_pct")
    st.metric(
        "📅 Year-on-Year Return",
        f"{yoy:+.1f}%" if yoy is not None else "N/A",
        help="Return over the past 252 trading days (~1 year). Positive = market grew.",
    )
with col4:
    sentiment_emoji = "📈" if market_data["sentiment"] == "Upward" else "📉" if market_data["sentiment"] == "Cautious" else "➡️"
    st.metric("🎯 Market Sentiment", f"{sentiment_emoji} {market_data['sentiment']}", help="Based on last daily price movement direction.")
with col5:
    vol_emoji = "🔴" if market_data["volatility"] == "High" else "🟡"
    st.metric(
        "📉 Volatility",
        f"{vol_emoji} {market_data['volatility']}",
        help="High = avg daily move >2%. Moderate = less than 2%. Higher volatility = more uncertain market.",
    )

st.markdown("<hr style='margin:1.5rem 0;'/>", unsafe_allow_html=True)

# Overview & Impact / Forecast tabs
overview_tab, forecast_tab, news_tab = st.tabs(["📊 Overview & Impact", "🔮 Market Forecast & Scenarios", "📰 News & Macro Context"])

with overview_tab:
    st.markdown("<h3 style='margin-bottom:1rem;'>📊 Market Overview & Trade Impact</h3>", unsafe_allow_html=True)

    col_a, col_b = st.columns([1, 1.2], gap="large")

    with col_a:
        st.markdown("**Key economic indicators**")
        indicators = {
            "GDP Growth (%)": gdp,
            "Inflation (%)": inf,
            "Labor Force (M)": profile.get("labor_force_mn", 0),
            "Market Cap ($B)": profile.get("market_cap_bn", 0),
            "FX Rate (per USD)": fx,
        }
        ind_df = pd.DataFrame(list(indicators.items()), columns=["Indicator", "Value"])
        st.dataframe(ind_df, use_container_width=True, hide_index=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown("**Sector exposure to trade shocks**")
        sector_data = {
            "Sector": ["Primary", "Secondary", "Tertiary", "Quaternary"],
            "Share (%)": [
                profile.get("primary_sector_pct", 20),
                profile.get("secondary_sector_pct", 30),
                profile.get("tertiary_sector_pct", 45),
                profile.get("quaternary_sector_pct", 5),
            ],
            "Trade exposure": ["High", "High", "Medium", "Low"],
        }
        st.dataframe(pd.DataFrame(sector_data), use_container_width=True, hide_index=True)

    with col_b:
        st.markdown("**Country comparison — macro snapshot**")
        compare_profile = COUNTRY_PROFILES.get(compare_country, {})
        compare_metrics = {
            "Metric": ["GDP Growth (%)", "Inflation (%)", "Median Age", "Urbanization (%)", "Market Cap ($B)"],
            country: [
                profile.get("gdp_growth", 0),
                profile.get("inflation", 0),
                profile.get("median_age", 0),
                profile.get("urbanization_pct", 0),
                profile.get("market_cap_bn", 0),
            ],
            compare_country: [
                compare_profile.get("gdp_growth", 0),
                compare_profile.get("inflation", 0),
                compare_profile.get("median_age", 0),
                compare_profile.get("urbanization_pct", 0),
                compare_profile.get("market_cap_bn", 0),
            ],
        }
        comp_df = pd.DataFrame(compare_metrics)
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        gdp_diff = profile.get("gdp_growth", 0) - compare_profile.get("gdp_growth", 0)
        if gdp_diff > 1.5:
            narrative = f"🚀 **{country} significantly outgrows {compare_country}** (+{gdp_diff:.1f}pp). Higher tariff sensitivity as trade-dependent growth creates vulnerability."
            color, border = "#dcfce7", "#22c55e"
        elif gdp_diff < -1.5:
            narrative = f"⚠️ **{compare_country} outgrows {country}** by {abs(gdp_diff):.1f}pp. {country} may be more susceptible to demand-side trade shocks."
            color, border = "#fee2e2", "#ef4444"
        else:
            narrative = f"📊 **{country} and {compare_country} are broadly in the same growth tier** (gap: {gdp_diff:+.1f}pp). Similar trade shock resilience profiles."
            color, border = "#fef3c7", "#f59e0b"
        st.markdown(f'<div style="background:{color};padding:1rem;border-radius:0.5rem;border-left:4px solid {border};"><p style="margin:0;font-size:0.9rem;line-height:1.6;">{narrative}</p></div>', unsafe_allow_html=True)

    st.markdown("<hr style='margin:1.5rem 0;'/>", unsafe_allow_html=True)

    st.markdown("**Market cap relative size — selected economies**")
    cap_data = [(c, COUNTRY_PROFILES[c].get("market_cap_bn", 0)) for c in COUNTRIES if c in COUNTRY_PROFILES]
    cap_df = pd.DataFrame(cap_data, columns=["Country", "Market Cap ($B)"]).sort_values("Market Cap ($B)", ascending=False)
    fig_cap = px.bar(cap_df, x="Country", y="Market Cap ($B)", color="Market Cap ($B)", color_continuous_scale="Blues",
                     title="Stock Market Capitalisation by Economy (USD Billions)")
    fig_cap.update_layout(template="plotly_white", height=320, showlegend=False, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_cap, use_container_width=True)

    with st.expander("🎓 Teaching note: Why does market cap matter for trade?", expanded=False):
        st.markdown(
            """
            **Market capitalisation** is the total value of all publicly listed companies in an economy. It reflects:
            - **Investor confidence** in that country's economic outlook
            - **Financial depth** — larger markets can absorb shocks better
            - **Corporate internationalism** — bigger markets tend to have more export-oriented multinationals

            When tariffs hit a key sector (e.g. electronics in South Korea or semiconductors in Taiwan), listed companies
            in that sector lose value, pulling down the index. This is the financial markets channel of trade policy:
            the tariff doesn't just affect trade volumes — it signals future earnings risk, which markets price immediately.

            **Currency link**: Tariff-driven trade deficits put downward pressure on a currency. A weaker currency makes
            exports cheaper (helpful) but raises the cost of imported inputs (inflationary). This feedback loop is why
            central banks watch trade policy closely.
            """
        )

with forecast_tab:
    st.markdown("<h3 style='margin-bottom:1rem;'>🔮 Market Forecast & Scenario Analysis</h3>", unsafe_allow_html=True)

    base_series, baseline_forecast, scenario_forecast = build_market_prediction(profile, prediction_event, prediction_intensity)

    future_years = list(range(2025, 2030))
    hist_years = list(YEARS)

    fig_market = go.Figure()
    fig_market.add_trace(go.Scatter(
        x=hist_years, y=base_series, mode="lines+markers", name="Historical (synthetic index)",
        line=dict(color="#00d4ff", width=3)
    ))
    fig_market.add_trace(go.Scatter(
        x=future_years, y=baseline_forecast, mode="lines+markers", name="Baseline forecast",
        line=dict(color="#ff6b35", width=3, dash="dash")
    ))
    fig_market.add_trace(go.Scatter(
        x=future_years, y=scenario_forecast, mode="lines+markers", name=f"Scenario: {prediction_event}",
        line=dict(color="#ffd166", width=3)
    ))
    fig_market.add_annotation(
        x=0.02, y=0.98, xref="paper", yref="paper",
        text=f"Event: {prediction_event} ({prediction_intensity:+.0f}%)", showarrow=False,
        bgcolor="rgba(0,0,0,0.45)", borderpad=4, font=dict(color="white"),
    )
    fig_market.update_layout(
        title=f"Market Index Forecast — {country} ({profile.get('stock_index', 'Index')})",
        xaxis_title="Year", yaxis_title="Synthetic Index Value",
        template="plotly_dark", height=380,
    )
    st.plotly_chart(fig_market, use_container_width=True)

    col_f1, col_f2, col_f3 = st.columns(3, gap="medium")
    impact_pct = ((scenario_forecast[-1] / baseline_forecast[-1]) - 1) * 100
    with col_f1:
        st.metric("📊 Scenario event", prediction_event[:30] + "..." if len(prediction_event) > 30 else prediction_event)
    with col_f2:
        st.metric("💥 Intensity", f"{prediction_intensity}%")
    with col_f3:
        st.metric("📉 5-yr forecast impact", f"{impact_pct:+.1f}% vs baseline", delta=f"{impact_pct:+.1f}%", delta_color="normal" if impact_pct >= 0 else "inverse")

    st.divider()
    st.subheader("Multi-country market scenario comparison")
    st.markdown(f"*How the same {prediction_event} event affects different markets*")
    comparison_data = []
    for c in [country, compare_country]:
        p = COUNTRY_PROFILES.get(c, {})
        _, bl, sc = build_market_prediction(p, prediction_event, prediction_intensity)
        impact = ((sc[-1] / bl[-1]) - 1) * 100
        comparison_data.append({"Country": c, "Baseline 5yr ($B equivalent)": round(bl[-1] / 10, 1), "Scenario 5yr ($B equivalent)": round(sc[-1] / 10, 1), "Impact (%)": round(impact, 2)})
    comp_tab = pd.DataFrame(comparison_data)
    st.dataframe(comp_tab, use_container_width=True, hide_index=True)

    with st.expander("🎓 Teaching note: How trade policy transmits to financial markets", expanded=False):
        st.markdown(
            """
            **The transmission mechanism** from trade policy to financial markets has three main channels:

            1. **Earnings channel**: Tariffs raise costs or reduce revenues for companies that trade internationally.
               Markets reprice those companies immediately, even before a tariff takes legal effect.

            2. **Uncertainty channel**: Policy unpredictability raises the risk premium investors demand.
               This lifts discount rates → lower asset valuations, even for companies not directly exposed to trade.

            3. **Currency channel**: Trade deficits and capital flow shifts alter exchange rates.
               A weaker currency boosts export competitiveness but raises the cost of imported inputs —
               creating an inflationary-competitive trade-off.

            **Interest rate link**: Central banks respond to trade-driven inflation by adjusting rates,
            which affects the cost of capital across the entire economy. This is why a US-China tariff
            can eventually reach mortgage rates in Australia.
            """
        )

with news_tab:
    st.markdown("<h3 style='margin-bottom:1rem;'>📰 Market News & Macro Context</h3>", unsafe_allow_html=True)

    news_items = profile.get("news", [])
    st.markdown(f"**Latest headlines — {country}** *(synthetic, illustrative)*")
    for i, headline in enumerate(news_items):
        sentiment_color = "#dcfce7" if i == 0 else "#fef3c7" if i == 1 else "#fee2e2"
        sentiment_border = "#22c55e" if i == 0 else "#f59e0b" if i == 1 else "#ef4444"
        sentiment_icon = "📈" if i == 0 else "⚠️" if i == 1 else "📉"
        st.markdown(
            f'<div style="background:{sentiment_color};padding:1rem 1.2rem;border-radius:0.5rem;border-left:4px solid {sentiment_border};margin-bottom:0.75rem;">'
            f'<p style="margin:0;font-size:0.95rem;">{sentiment_icon} {headline}</p>'
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("**Currency exchange rates** *(approximate, illustrative)*")
    fx_data = [(c, COUNTRY_PROFILES[c]["currency"], COUNTRY_PROFILES[c]["currency_vs_usd"]) for c in COUNTRIES if c in COUNTRY_PROFILES]
    fx_df = pd.DataFrame(fx_data, columns=["Country", "Currency", "Per USD"])
    highlight_idx = [i for i, row in fx_df.iterrows() if row["Country"] == country]
    st.dataframe(fx_df, use_container_width=True, hide_index=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="background:#f8fafc;padding:1.2rem;border-radius:0.5rem;border:1px solid #e2e8f0;">
        <p style="margin:0 0 0.5rem 0;font-weight:600;color:#1e293b;">📌 Macro snapshot: {country}</p>
        <p style="margin:0;font-size:0.9rem;color:#475569;line-height:1.7;">
        GDP Growth: <strong>{gdp:.1f}%</strong> &nbsp;|&nbsp;
        Inflation: <strong>{inf:.1f}%</strong> &nbsp;|&nbsp;
        Currency: <strong>{currency} ({fx:,.2f}/USD)</strong> &nbsp;|&nbsp;
        Market Index: <strong>{stock_index}</strong> &nbsp;|&nbsp;
        Market Cap: <strong>${profile.get('market_cap_bn', 0):,}B</strong>
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("🎓 Teaching note: Reading market news through an economic lens", expanded=False):
        st.markdown(
            """
            **How to interpret financial news for trade analysis**:

            - **Central bank decisions** (rate hikes/cuts) directly affect currency values and therefore export competitiveness.
              A rate hike typically strengthens a currency → makes exports more expensive → trade volumes may fall.

            - **FDI announcements** signal where global capital expects future trade growth. A factory opening in Vietnam
              tells you investors expect Vietnam to be a significant exporter in that sector within 3–5 years.

            - **Index moves** often lag real economy changes by 6–12 months. A stock market rally does not always mean
              trade conditions are improving — it may reflect global liquidity conditions (e.g. low US interest rates) more
              than local trade fundamentals.

            - **Currency interventions** by central banks (e.g. Japan, Taiwan, South Korea) are attempts to prevent
              exchange rate appreciation that would erode export competitiveness. These interventions create friction
              in the automatic adjustment mechanism that trade theory assumes.
            """
        )

st.markdown("<hr style='margin:3rem 0 1rem 0;'/>", unsafe_allow_html=True)
with st.expander("📚 About this page", expanded=False):
    st.markdown(
        """
        **Financial Markets** tracks the economic and market context for each of the 10 economies in the simulator.

        - **Market data**: Where available, live data is pulled via yfinance using the country's primary stock index ticker.
          Synthetic data is used as a fallback.
        - **Scenario predictions**: A synthetic index series is generated from macroeconomic fundamentals, then a policy
          event multiplier is applied based on the event type and intensity. This is a simplified illustrative model.
        - **Currency data**: Exchange rates shown are approximate reference values for illustrative purposes.
        - **News**: Headlines are illustrative examples of the kinds of news relevant to each economy's trade position.

        All data is for educational use. Nothing here constitutes investment advice.
        """
    )
