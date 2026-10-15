"""
Unit Tests for Data Pipeline and Feature Engineering.
Offline tests use synthetic OHLCV data to guarantee zero network dependence in tests/.
"""
import pandas as pd
import numpy as np
from src.feature_pipeline import compute_technical_indicators, prepare_feature_dataset
from src.pipeline import create_purged_splits


def _create_synthetic_ohlcv(n_bars: int = 600) -> pd.DataFrame:
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", periods=n_bars, freq="D")
    ret = np.random.normal(0.0005, 0.012, n_bars)
    close = 100.0 * np.exp(np.cumsum(ret))
    high = close * (1.0 + np.abs(np.random.normal(0, 0.004, n_bars)))
    low = close * (1.0 - np.abs(np.random.normal(0, 0.004, n_bars)))
    open_prices = (close + np.roll(close, 1)) / 2.0
    open_prices[0] = 100.0
    volume = np.random.uniform(1e6, 5e6, n_bars)

    return pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": volume,
    })


def test_feature_engineering_integrity_offline():
    raw_df = _create_synthetic_ohlcv(600)
    proc_df, feature_cols = prepare_feature_dataset(raw_df, "SYNTH", save_processed=False)

    assert len(feature_cols) == 20
    assert "rsi_14" in proc_df.columns
    assert "macd" in proc_df.columns
    assert "atr_14" in proc_df.columns
    assert "regime_high_vol" in proc_df.columns

    # Assert no NaNs in operational feature columns
    feature_nans = proc_df[feature_cols].isna().sum().sum()
    assert feature_nans == 0, f"Found {feature_nans} NaN values in feature columns"

    # Assert no NaNs in target direction or forward return
    assert proc_df["forward_return"].isna().sum() == 0, "Forward return contains trailing NaNs"
    assert proc_df["target_direction"].isna().sum() == 0, "Target direction contains trailing NaNs"


def test_purged_chronological_splits():
    raw_df = _create_synthetic_ohlcv(600)
    proc_df, _ = prepare_feature_dataset(raw_df, "SYNTH", save_processed=False)

    horizon_bars = 3
    splits = create_purged_splits(proc_df, horizon_bars=horizon_bars, train_frac=0.45, val_frac=0.15, dev_frac=0.15)

    train_df = splits["train"]
    val_df = splits["val"]
    dev_df = splits["dev"]
    test_df = splits["test"]

    # Verify chronological ordering
    assert train_df["Date"].max() < val_df["Date"].min()
    assert val_df["Date"].max() < dev_df["Date"].min()
    assert dev_df["Date"].max() < test_df["Date"].min()

    # Verify purge gap between train and val
    train_last_date = train_df["Date"].iloc[-1]
    val_first_date = val_df["Date"].iloc[0]
    full_dates = proc_df["Date"].tolist()
    train_last_idx = full_dates.index(train_last_date)
    val_first_idx = full_dates.index(val_first_date)
    assert val_first_idx - train_last_idx > horizon_bars, "Purge gap between Train and Val violated"

    # Verify purge gap between dev and test
    dev_last_date = dev_df["Date"].iloc[-1]
    test_first_date = test_df["Date"].iloc[0]
    dev_last_idx = full_dates.index(dev_last_date)
    test_first_idx = full_dates.index(test_first_date)
    assert test_first_idx - dev_last_idx > horizon_bars, "Purge gap between Dev and Test violated"
