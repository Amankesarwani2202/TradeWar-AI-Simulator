"""Live market data and instrument discovery.

Yahoo Finance is used for supported global markets. Bangladesh DSE data uses
bdshare, which provides DSEX and DSE equity quotes without conflicting with
Yahoo Finance dependencies.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import pandas as pd
import streamlit as st

try:
    import yfinance as yf
except Exception:
    yf = None

try:
    from bdshare import get_dsex_data, get_historical_data, get_current_trade_data
except Exception:
    get_dsex_data = None
    get_historical_data = None
    get_current_trade_data = None

MARKETS = {
    "India": [("NIFTY 50", "^NSEI", "Index"), ("NIFTY Bank", "^NSEBANK", "Index"), ("BSE Sensex", "^BSESN", "Index"), ("NIFTY IT", "^CNXIT", "Index"), ("NIFTY Midcap 100", "NIFTY_MIDCAP_100.NS", "Index"), ("NIFTY Smallcap 100", "^CNXSC", "Index"), ("NIFTY Next 50", "^NSMIDCP", "Index")],
    "China": [("SSE Composite", "000001.SS", "Index"), ("CSI 300", "000300.SS", "Index"), ("Shenzhen Component", "399001.SZ", "Index")],
    "Hong Kong": [("Hang Seng", "^HSI", "Index"), ("Hang Seng China Enterprises", "^HSCE", "Index"), ("Hang Seng Tech", "HSTECH.HK", "Index")],
    "United States": [("S&P 500", "^GSPC", "Index"), ("Nasdaq 100", "^NDX", "Index"), ("Dow Jones", "^DJI", "Index"), ("Russell 2000", "^RUT", "Index"), ("VIX", "^VIX", "Volatility")],
    "Japan": [("Nikkei 225", "^N225", "Index"), ("TOPIX", "998405.T", "Index")],
    "South Korea": [("KOSPI", "^KS11", "Index"), ("KOSDAQ", "^KQ11", "Index")],
    "Taiwan": [("TAIEX", "^TWII", "Index")],
    "Vietnam": [("VN-Index", "^VNINDEX.VN", "Index")],
    "Thailand": [("SET Index", "SET.BK", "Index")],
    "Bangladesh": [("DSEX", "DSEX", "Index")],
    "Singapore": [("STI", "^STI", "Index")],
    "Australia": [("ASX 200", "^AXJO", "Index")],
    "United Kingdom": [("FTSE 100", "^FTSE", "Index")],
    "Germany": [("DAX", "^GDAXI", "Index")],
    "France": [("CAC 40", "^FCHI", "Index")],
    "Europe": [("Euro Stoxx 50", "^STOXX50E", "Index")],
    "Canada": [("S&P/TSX Composite", "^GSPTSE", "Index")],
    "Brazil": [("Bovespa", "^BVSP", "Index")],
    "Mexico": [("IPC Mexico", "^MXX", "Index")],
    "South Africa": [("Satrix 40 ETF (FTSE/JSE Top 40 proxy)", "STX40.JO", "ETF proxy")],
}

COMMON_ASSETS = {
    "India": [("Reliance Industries", "RELIANCE.NS", "Equity"), ("TCS", "TCS.NS", "Equity"), ("HDFC Bank", "HDFCBANK.NS", "Equity"), ("Infosys", "INFY.NS", "Equity")],
    "United States": [("Apple", "AAPL", "Equity"), ("Microsoft", "MSFT", "Equity"), ("NVIDIA", "NVDA", "Equity"), ("Amazon", "AMZN", "Equity"), ("Alphabet", "GOOGL", "Equity")],
    "China": [("Tencent", "0700.HK", "Equity"), ("Alibaba", "BABA", "Equity"), ("Baidu", "BIDU", "Equity")],
    "Japan": [("Toyota", "7203.T", "Equity"), ("Sony", "6758.T", "Equity")],
    "South Korea": [("Samsung Electronics", "005930.KS", "Equity"), ("SK Hynix", "000660.KS", "Equity")],
    "South Africa": [("Naspers", "NPN.JO", "Equity"), ("Gold Fields", "GFI.JO", "Equity"), ("FirstRand", "FSR.JO", "Equity")],
    "Bangladesh": [("Grameenphone", "GP", "DSE Equity"), ("Square Pharmaceuticals", "SQURPHARMA", "DSE Equity"), ("BRAC Bank", "BRACBANK", "DSE Equity")],
}


def _empty_history() -> pd.DataFrame:
    return pd.DataFrame()


def _period_days(period: str) -> int:
    return {"1mo": 31, "3mo": 93, "6mo": 186, "1y": 366, "2y": 731, "5y": 1826}.get(period, 366)


def _normalize_history(data: pd.DataFrame) -> pd.DataFrame:
    if data is None or data.empty:
        return _empty_history()
    data = data.copy()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    if "Close" not in data.columns:
        for candidate in ("close", "CLOSE", "ltp", "LTP"):
            if candidate in data.columns:
                data["Close"] = data[candidate]
                break
    if "Close" not in data.columns:
        return _empty_history()
    for col in ("Open", "High", "Low"):
        if col not in data.columns:
            data[col] = data["Close"]
    if "Volume" not in data.columns:
        data["Volume"] = pd.NA
    data["Close"] = pd.to_numeric(data["Close"], errors="coerce")
    return data.dropna(subset=["Close"]).sort_index()


@st.cache_data(ttl=300, show_spinner=False)
def _download_dsex(period: str) -> pd.DataFrame:
    if get_dsex_data is None:
        return _empty_history()
    try:
        raw = get_dsex_data("DSEX")
        if raw is None or raw.empty:
            return _empty_history()
        data = raw.copy()
        # bdshare versions expose the index value under dsex/close/ltp depending on release.
        close_col = next((c for c in data.columns if str(c).lower() in {"dsex", "close", "ltp", "index"}), None)
        if close_col is None:
            numeric = data.select_dtypes(include="number").columns
            close_col = numeric[0] if len(numeric) else None
        if close_col is None:
            return _empty_history()
        data["Close"] = pd.to_numeric(data[close_col], errors="coerce")
        date_col = next((c for c in data.columns if str(c).lower() in {"date", "datetime"}), None)
        if date_col:
            data.index = pd.to_datetime(data[date_col], errors="coerce")
        data["Open"] = data["Close"]; data["High"] = data["Close"]; data["Low"] = data["Close"]
        data["Volume"] = pd.NA
        return data[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"]).sort_index()
    except Exception:
        return _empty_history()


@st.cache_data(ttl=300, show_spinner=False)
def _download_dse_equity(ticker: str, period: str) -> pd.DataFrame:
    if get_historical_data is None:
        return _empty_history()
    try:
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=_period_days(period))
        data = get_historical_data(str(start), str(end), ticker)
        return _normalize_history(data)
    except Exception:
        return _empty_history()


@st.cache_data(ttl=300, show_spinner=False)
def download_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    if not ticker:
        return _empty_history()
    symbol = ticker.strip()
    if symbol.upper() == "DSEX":
        return _download_dsex(period)
    if symbol.upper() in {"GP", "SQURPHARMA", "BRACBANK"}:
        return _download_dse_equity(symbol, period)
    if yf is None:
        return _empty_history()
    try:
        data = yf.download(symbol, period=period, progress=False, auto_adjust=True, threads=False)
        return _normalize_history(data)
    except Exception:
        return _empty_history()


def summarize(ticker: str, name: str = "") -> dict | None:
    data = download_history(ticker, "1y")
    if data.empty or "Close" not in data:
        return None
    close = pd.to_numeric(data["Close"], errors="coerce").dropna()
    if close.empty:
        return None
    latest = float(close.iloc[-1]); previous = float(close.iloc[-2]) if len(close) > 1 else latest; first = float(close.iloc[0])
    volume = None
    if "Volume" in data:
        vol = pd.to_numeric(data["Volume"], errors="coerce").dropna()
        volume = int(vol.iloc[-1]) if not vol.empty else None
    return {"name": name or ticker, "ticker": ticker, "latest": latest, "daily_pct": (latest / previous - 1) * 100 if previous else 0, "period_pct": (latest / first - 1) * 100 if first else 0, "volume": volume, "history": close}


def search_ticker(query: str, country: str | None = None) -> pd.DataFrame:
    if yf is None or not query.strip():
        return pd.DataFrame(columns=["name", "symbol", "exchange", "type"])
    try:
        result = yf.Search(query.strip()).quotes
    except Exception:
        return pd.DataFrame(columns=["name", "symbol", "exchange", "type"])
    rows = [{"name": item.get("shortname") or item.get("longname") or item.get("symbol", ""), "symbol": item.get("symbol", ""), "exchange": item.get("exchange", ""), "type": item.get("quoteType", "")} for item in (result or [])]
    return pd.DataFrame(rows).drop_duplicates(subset=["symbol"]) if rows else pd.DataFrame(columns=["name", "symbol", "exchange", "type"])


def live_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
