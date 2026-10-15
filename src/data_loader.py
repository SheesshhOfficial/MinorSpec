"""
High-Performance Financial Data Loader & Parquet Cache Manager.
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import yfinance as yf
import pandas as pd
import polars as pl

from src.config import RAW_DATA_DIR, START_DATE, DEFAULT_TICKERS


def fetch_and_cache_ticker(
    ticker: str,
    start_date: str = START_DATE,
    end_date: Optional[str] = None,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Downloads historical OHLCV data for a ticker and caches it as Parquet.
    Returns cleaned pandas DataFrame.
    """
    clean_ticker = ticker.upper().replace("^", "")
    parquet_path = RAW_DATA_DIR / f"{clean_ticker}.parquet"

    # Check cache freshness (refresh if older than 1 day or force_refresh is True)
    if parquet_path.exists() and not force_refresh:
        file_mod_time = datetime.fromtimestamp(parquet_path.stat().st_mtime)
        if datetime.now() - file_mod_time < timedelta(days=1):
            df = pd.read_parquet(parquet_path)
            if not df.empty and len(df) > 100:
                return df

    print(f"[DataLoader] Downloading historical data for {ticker} from {start_date}...")
    yf_ticker = yf.Ticker(ticker)
    df = yf_ticker.history(start=start_date, end=end_date, auto_adjust=True)

    if df.empty:
        if parquet_path.exists():
            print(f"[DataLoader] Download returned empty for {ticker}, falling back to cache.")
            return pd.read_parquet(parquet_path)
        raise ValueError(f"No data returned for ticker: {ticker}")

    # Standardize index and columns
    df.reset_index(inplace=True)
    if "Date" in df.columns:
        # Convert timezone-aware datetimes to UTC or naive datetime
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    elif "Datetime" in df.columns:
        df.rename(columns={"Datetime": "Date"}, inplace=True)
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)

    # Filter required OHLCV columns
    required_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
    cols_present = [c for c in required_cols if c in df.columns]
    df = df[cols_present].dropna().sort_values("Date").reset_index(drop=True)

    # Save to parquet
    df.to_parquet(parquet_path, index=False, compression="zstd")
    print(f"[DataLoader] Successfully saved {len(df)} records for {ticker} -> {parquet_path}")
    return df


def load_universe(
    tickers: Optional[List[str]] = None,
    force_refresh: bool = False,
) -> Dict[str, pd.DataFrame]:
    """
    Loads historical market data for all specified universe tickers.
    """
    if tickers is None:
        tickers = DEFAULT_TICKERS

    universe = {}
    for ticker in tickers:
        try:
            df = fetch_and_cache_ticker(ticker, force_refresh=force_refresh)
            universe[ticker] = df
        except Exception as e:
            print(f"[DataLoader] Warning: Failed to load {ticker}: {e}")

    return universe


if __name__ == "__main__":
    print("Testing data loader with default tickers...")
    data = load_universe(["SPY", "AAPL"])
    for sym, df in data.items():
        print(f"{sym}: {len(df)} bars, Range: {df['Date'].min()} to {df['Date'].max()}")
