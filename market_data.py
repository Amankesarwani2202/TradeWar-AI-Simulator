"""Live market data helpers backed by Yahoo Finance via yfinance."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

import pandas as pd
import streamlit as st

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None

# A broad, curated directory of major indices/exchanges. The custom ticker input
# remains available so the explorer is not limited to this directory.
MARKETS = {
    "India": [
        ("NIFTY 50", "^NSEI", "Index"), ("NIFTY Bank", "^NSEBANK", "Index"),
        ("BSE Sensex", "^BSESN", "Index"), ("NIFTY IT", "^CNXIT", "Index"),
        ("NIFTY Midcap 100", "^CNXMC", "Index"), ("NIFTY Smallcap 100", "^CNXSC", "Index"),
        ("NIFTY Next 50", "^NSMIDCP", "Index"),
    ],
    "China": [("SSE Composite", "000001.SS", "Index"), ("CSI 300", "000300.SS", "Index"), ("Shenzhen Component", "399001.SZ", "Index")],
    "Hong Kong": [("Hang Seng", "^HSI", "Index"), ("Hang Seng China Enterprises", "^HSCE", "Index"), ("Hang Seng Tech", "^HSTECH", "Index")],
    "United States": [("S&P 500", "^GSPC", "Index"), ("Nasdaq 100", "^NDX", "Index"), ("Dow Jones", "^DJI", "Index"), ("Russell 2000", "^RUT", "Index"), ("VIX", "^VIX", "Volatility")],
    "Japan": [("Nikkei 225", "^N225", "Index"), ("TOPIX", "^TOPX", "Index")],
    "South Korea": [("KOSPI", "^KS11", "Index"), ("KOSDAQ", "^KQ11", "Index")],
    "Taiwan": [("TAIEX", "^TWII", "Index")],
    "Vietnam": [("VN-Index", "^VNINDEX", "Index")],
    "Thailand": [("SET Index", "^SET.BK", "Index")],
    "Bangladesh": [("DSEX", "DSEX.BD", "Index")],
    "Singapore": [("STI", "^STI", "Index")],
    "Australia": [("ASX 200", "^AXJO", "Index")],
    "United Kingdom": [("FTSE 100", "^FTSE", "Index")],
    "Germany": [("DAX", "^GDAXI", "Index")],
    "France": [("CAC 40", "^FCHI", "Index")],
    "Europe": [("Euro Stoxx 50", "^STOXX50E", "Index")],
    "Canada": [("S&P/TSX Composite", "^GSPTSE", "Index")],
    "Brazil": [("Bovespa", "^BVSP", "Index")],
    "Mexico": [("IPC Mexico", "^MXX", "Index")],
    "South Africa": [("FTSE/JSE Top 40", "^JTOPI", "Index")],
}

COMMON_ASSETS = {
    "India": [("Reliance Industries", "RELIANCE.NS", "Equity"), ("TCS", "TCS.NS", "Equity"), ("HDFC Bank", "HDFCBANK.NS", "Equity"), ("Infosys", "INFY.NS", "Equity")],
    "United States": [("Apple", "AAPL", "Equity"), ("Microsoft", "MSFT", "Equity"), ("NVIDIA", "NVDA", "Equity"), ("Amazon", "AMZN", "Equity"), ("Alphabet", "GOOGL", "Equity")],
    "China": [("Tencent", "0700.HK", "Equity"), ("Alibaba", "BABA", "Equity"), ("Baidu", "BIDU", "Equity")],
    "Japan": [("Toyota", "7203.T", "Equity"), ("Sony", "6758.T", "Equity")],
    "South Korea": [("Samsung Electronics", "005930.KS", "Equity"), ("SK Hynix", "000660.KS", "Equity")],
}

@st.cache_data(ttl=300, show_spinner=False)
def download_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    if yf is None or not ticker:
        return pd.DataFrame()
    try:
        data = yf.download(ticker.strip(), period=period, progress=False, auto_adjust=True, threads=False)
        if data.empty:
            return pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data.dropna(how="all")
    except Exception:
        return pd.DataFrame()


def summarize(ticker: str, name: str = "") -> dict | None:
    data = download_history(ticker, "1y")
    if data.empty or "Close" not in data:
        return None
    close = pd.to_numeric(data["Close"], errors="coerce").dropna()
    if close.empty:
        return None
    latest = float(close.iloc[-1]); previous = float(close.iloc[-2]) if len(close) > 1 else latest
    year_ago = float(close.iloc[0])
    volume = None
    if "Volume" in data:
        vol = pd.to_numeric(data["Volume"], errors="coerce").dropna()
        volume = int(vol.iloc[-1]) if not vol.empty else None
    return {
        "name": name or ticker, "ticker": ticker, "latest": latest,
        "daily_pct": (latest / previous - 1) * 100 if previous else 0,
        "period_pct": (latest / year_ago - 1) * 100 if year_ago else 0,
        "volume": volume, "history": close,
    }


def live_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
