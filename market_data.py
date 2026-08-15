"""Live market data and instrument discovery backed by Yahoo Finance."""
from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd
import streamlit as st

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None

# Curated entry points cover major exchanges/indices. Users can also search by
# company/instrument name or enter any Yahoo Finance ticker below.
MARKETS = {
    "India": [("NIFTY 50