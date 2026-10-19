"""
High-Performance Financial Data Loader & Parquet Cache Manager.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from urllib.parse import quote
from pathlib import Path
from typing import Dict, List, Optional
import yfinance as yf
import pandas as pd
import numpy as np

from src.config import RAW_DATA_DIR, START_DATE, DEFAULT_TICKERS


def ticker_cache_key(ticker: str) -> str:
    """Keep distinct symbols distinct, and never interpret symbols as file paths."""
    if not isinstance(ticker, str) or not ticker.strip():
        raise ValueError("ticker must be a nonempty string")
    return quote(ticker.strip().upper(), safe=".-_")


def normalize_history(df: pd.DataFrame) -> pd.DataFrame:
    required = ["Date", "Open", "High", "Low", "Close", "Volume"]
    if "Date" not in df.columns:
        df = df.reset_index().rename(columns={"Datetime": "Date"})
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Market data is missing required columns: {sorted(missing)}")
    data = df[required].copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="raise").dt.tz_localize(None)
    for column in required[1:]:
        data[column] = pd.to_numeric(data[column], errors="raise")
    if data["Date"].isna().any() or data["Date"].duplicated().any():
        raise ValueError("Market data dates must be present and unique")
    values = data[required[1:]].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values[:, :4] <= 0).any() or (values[:, 4] < 0).any():
        raise ValueError("Market data requires finite positive prices and nonnegative volume")
    if (data["High"] < data["Low"]).any():
        raise ValueError("Market data High must not be below Low")
    return data.sort_values("Date").reset_index(drop=True)


def fetch_and_cache_ticker(
    ticker: str,
    start_date: str = START_DATE,
    end_date: Optional[str] = None,
    force_refresh: bool = False,
    offline: bool = False,
) -> pd.DataFrame:
    """Download adjusted OHLCV, honoring the requested [start, end) interval.

    Cache identity includes ticker and requested coverage, recorded in a sidecar.
    Legacy caches may only supply intervals demonstrably inside their date span.
    Stale fallback is explicitly reported in dataframe provenance and a warning.
    """
    if offline and force_refresh:
        raise ValueError("offline and force_refresh cannot both be True")
    symbol = ticker.strip().upper() if isinstance(ticker, str) else ticker
    clean_ticker = ticker_cache_key(ticker)
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date) if end_date is not None else None
    if pd.isna(start) or (end is not None and (pd.isna(end) or end <= start)):
        raise ValueError("end_date must be later than start_date")
    if start.tzinfo is not None or (end is not None and end.tzinfo is not None):
        raise ValueError("Use timezone-naive dates for daily history")
    request = {"ticker": symbol, "start": start.isoformat(), "end": end.isoformat() if end is not None else None,
               "provider": "yfinance", "auto_adjust": True}
    parquet_path = RAW_DATA_DIR / f"{clean_ticker}.parquet"
    metadata_path = parquet_path.with_suffix(".metadata.json")
    cached = None
    cache_meta = None
    digest = None
    if parquet_path.exists():
        try:
            cached = normalize_history(pd.read_parquet(parquet_path))
            digest = hashlib.sha256(parquet_path.read_bytes()).hexdigest()
            if metadata_path.exists():
                cache_meta = json.loads(metadata_path.read_text())
                if not isinstance(cache_meta, dict) or not isinstance(cache_meta.get("request"), dict):
                    raise ValueError("Invalid cache metadata schema")
                cache_request = cache_meta["request"]
                if not set(request).issubset(cache_request) or not isinstance(cache_meta.get("sha256"), str):
                    raise ValueError("Incomplete cache metadata schema")
            if cache_meta is not None:
                covered = (cache_meta.get("request") == request and cache_meta.get("sha256") == digest)
            else:
                # An unannotated file cannot establish inception coverage or a current open-ended request.
                covered = (not cached.empty and end is not None and start >= cached["Date"].min()
                           and end <= cached["Date"].max() + pd.Timedelta(days=1))
            offline_identity_valid = offline and (cache_meta is None or (cache_meta.get("request", {}).get("ticker") == symbol and cache_meta.get("sha256") == digest))
            if not covered and not offline_identity_valid:
                cached = None
        except (ValueError, OSError, KeyError):
            cached = None

    def finish(data, source, stale=False):
        selected = data.loc[(data["Date"] >= start) & ((data["Date"] < end) if end is not None else True)].copy().reset_index(drop=True)
        if selected.empty:
            raise ValueError(f"No data for {symbol} in the requested date range")
        selected.attrs["data_provenance"] = {
            **request, "source": source, "stale_cache": stale,
            "raw_path": str(parquet_path), "raw_sha256": digest,
            "retrieved_at": cache_meta.get("retrieved_at") if cache_meta else None,
            "first_date": selected["Date"].iloc[0].isoformat(),
            "last_date": selected["Date"].iloc[-1].isoformat(), "rows": len(selected),
        }
        return selected

    if offline:
        if cached is None:
            raise ValueError(f"No compatible offline cache exists for {symbol}")
        print(f"[DataLoader] Offline snapshot for {symbol}; actual dates are recorded in data_provenance.")
        return finish(cached, "offline_snapshot", stale=True)

    if cached is not None and not force_refresh:
        age = datetime.now(timezone.utc).timestamp() - parquet_path.stat().st_mtime
        if 0 <= age < timedelta(days=1).total_seconds():
            return finish(cached, "cache")

    print(f"[DataLoader] Downloading historical data for {symbol} from {start_date}...")
    try:
        downloaded = yf.Ticker(symbol).history(start=start_date, end=end_date, auto_adjust=True)
        if downloaded.empty:
            raise ValueError(f"No data returned for ticker: {symbol}")
        data = normalize_history(downloaded)
        data = data.loc[(data["Date"] >= start) & ((data["Date"] < end) if end is not None else True)].reset_index(drop=True)
        if data.empty:
            raise ValueError(f"No data for {symbol} in the requested date range")
    except Exception as exc:
        if cached is None or force_refresh:
            raise
        print(f"[DataLoader] Refresh failed for {symbol}; using stale matching cache: {exc}")
        return finish(cached, "cache_fallback", stale=True)

    data.to_parquet(parquet_path, index=False, compression="zstd")
    digest = hashlib.sha256(parquet_path.read_bytes()).hexdigest()
    cache_meta = {"request": request, "sha256": digest, "retrieved_at": datetime.now(timezone.utc).isoformat()}
    metadata_path.write_text(json.dumps(cache_meta, indent=2) + "\n")
    print(f"[DataLoader] Successfully saved {len(data)} records for {symbol} -> {parquet_path}")
    return finish(data, "download")


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

