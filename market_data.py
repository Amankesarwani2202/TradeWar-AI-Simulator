"""Live market data and instrument discovery.

Yahoo Finance is used where it provides the requested instrument. Bangladesh
DSEX uses the DSE-specific stocksurferbd adapter because Yahoo Finance does
not expose a reliable DSEX quote. South Africa uses the Yahoo-listed Satrix
40 ETF as an explicitly labelled FTSE/JSE Top 40 proxy because Yahoo does not
provide the JTOPI index itself.
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
    from stocksurferbd import IndexData
except Exception:
    IndexData = None

MARKETS = {
    "India": [
        ("NIFTY 50", "^NSEI", "Index"),
        ("NIFTY Bank", "^NSEBANK", "Index"),
        ("BSE Sensex", "^BSESN", "Index"),
        ("NIFTY IT", "^CNXIT", "Index"),
        ("NIFTY Midcap 100", "NIFTY_MIDCAP_100.NS", "Index"),
        ("NIFTY Smallcap 100", "^CNXSC", "Index"),
        ("NIFTY Next 50", "^NSMIDCP", "Index"),
    ],
    "China": [
        ("SSE Composite", "000001.SS", "Index"),
        ("CSI 300", "000300.SS", "Index"),
        ("Shenzhen Component", "399001.SZ", "Index"),
    ],
    "Hong Kong": [
        ("Hang Seng", "^HSI", "Index"),
        ("Hang Seng China Enterprises", "^HSCE", "Index"),
        ("Hang Seng Tech", "HSTECH.HK", "Index"),
    ],
    "United States": [
        ("S&P 500", "^GSPC", "Index"),
        ("Nasdaq 100", "^NDX", "Index"),
        ("Dow Jones", "^DJI", "Index"),
        ("Russell 2000", "^RUT", "Index"),
        ("VIX", "^VIX", "Volatility"),
    ],
    "Japan": [
        ("Nikkei 225", "^N225", "Index"),
        # Yahoo Japan exposes TOPIX as the index code 998405.T; ^TOPX is stale.
        ("TOPIX", "998405.T", "Index"),
    ],
    "South Korea": [
        ("KOSPI", "^KS11", "Index"),
        ("KOSDAQ", "^KQ11", "Index"),
    ],
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
    # Yahoo does not expose the JTOPI index consistently. STX40.JO is a
    # Yahoo-listed ETF designed to track the FTSE/JSE Top 40, so we label it
    # explicitly as a proxy rather than pretending it is the index itself.
    "South Africa": [("Satrix 40 ETF (FTSE/JSE Top 40 proxy)", "STX40.JO", "ETF proxy")],
}

COMMON_ASSETS = {
    "India": [
        ("Reliance Industries", "RELIANCE.NS", "Equity"),
        ("TCS", "TCS.NS", "Equity"),
        ("HDFC Bank", "HDFCBANK.NS", "Equity"),
        ("Infosys", "INFY.NS", "Equity"),
    ],
    "United States": [
        ("Apple", "AAPL", "Equity"),
        ("Microsoft", "MSFT", "Equity"),
        ("NVIDIA", "NVDA", "Equity"),
        ("Amazon", "AMZN", "Equity"),
        ("Alphabet", "GOOGL", "Equity"),
    ],
    "China": [
        ("Tencent", "0700.HK", "Equity"),
        ("Alibaba", "BABA", "Equity"),
        ("Baidu", "BIDU", "Equity"),
    ],
    "Japan": [("Toyota", "7203.T", "Equity"), ("Sony", "6758.T", "Equity")],
    "South Korea": [
        ("Samsung Electronics", "005930.KS", "Equity"),
        ("SK Hynix", "000660.KS", "Equity"),
    ],
    "South Africa": [
        ("Naspers", "NPN.JO", "Equity"),
        ("Gold Fields", "GFI.JO", "Equity"),
        ("FirstRand", "FSR.JO", "Equity"),
    ],
    "Bangladesh": [
        ("Grameenphone", "GP", "DSE Equity"),
        ("Square Pharmaceuticals", "SQURPHARMA", "DSE Equity"),
        ("BRAC Bank", "BRACBANK", "DSE Equity"),
    ],
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
    return data.dropna(how="all")


@st.cache_data(ttl=300, show_spinner=False)
def _download_dsex(period: str) -> pd.DataFrame:
    if IndexData is None:
        return _empty_history()
    try:
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=_period_days(period))
        loader = IndexData()
        data = loader.get_index_history_df(
            market="DSE",
            start_date=str(start),
            end_date=str(end),
        )
        if data is None or data.empty or "DSEX" not in data.columns:
            return _empty_history()
        frame = data.copy()
        date_col = next((c for c in frame.columns if str(c).upper() in {"DATE", "DATETIME"}), None)
        if date_col:
            frame.index = pd.to_datetime(frame[date_col], errors="coerce")
        frame["Close"] = pd.to_numeric(frame["DSEX"], errors="coerce")
        frame = frame.dropna(subset=["Close"])
        frame["Open"] = frame["Close"]
        frame["High"] = frame["Close"]
        frame["Low"] = frame["Close"]
        frame["Volume"] = pd.to_numeric(frame.get("TOTAL_VOLUME"), errors="coerce") if "TOTAL_VOLUME" in frame else pd.NA
        return frame[["Open", "High", "Low", "Close", "Volume"]].sort_index()
    except Exception:
        return _empty_history()


@st.cache_data(ttl=300, show_spinner=False)
def download_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    if not ticker:
        return _empty_history()
    if ticker.upper() == "DSEX":
        return _download_dsex(period)
    if yf is None:
        return _empty_history()
    try:
        data = yf.download(
            ticker.strip(),
            period=period,
            progress=False,
            auto_adjust=True,
            threads=False,
        )
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
    latest = float(close.iloc[-1])
    previous = float(close.iloc[-2]) if len(close) > 1 else latest
    first = float(close.iloc[0])
    volume = None
    if "Volume" in data:
        vol = pd.to_numeric(data["Volume"], errors="coerce").dropna()
        volume = int(vol.iloc[-1]) if not vol.empty else None
    return {
        "name": name or ticker,
        "ticker": ticker,
        "latest": latest,
        "daily_pct": (latest / previous - 1) * 100 if previous else 0,
        "period_pct": (latest / first - 1) * 100 if first else 0,
        "volume": volume,
        "history": close,
    }


def search_ticker(query: str, country: str | None = None) -> pd.DataFrame:
    """Search Yahoo Finance symbols by name/ticker when yfinance exposes search."""
    if yf is None or not query.strip():
        return pd.DataFrame(columns=["name", "symbol", "exchange", "type"])
    try:
        result = yf.Search(query.strip()).quotes
    except Exception:
        return pd.DataFrame(columns=["name", "symbol", "exchange", "type"])
    rows = []
    for item in result or []:
        rows.append(
            {
                "name": item.get("shortname") or item.get("longname") or item.get("symbol", ""),
                "symbol": item.get("symbol", ""),
                "exchange": item.get("exchange", ""),
                "type": item.get("quoteType", ""),
            }
        )
    return (
        pd.DataFrame(rows).drop_duplicates(subset=["symbol"])
        if rows
        else pd.DataFrame(columns=["name", "symbol", "exchange", "type"])
    )


def live_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
