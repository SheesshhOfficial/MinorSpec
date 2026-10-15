"""
High-Speed Technical Feature Engineering and Market Regime Labeling Pipeline.
"""
from pathlib import Path
from typing import Tuple, List
import numpy as np
import pandas as pd
import polars as pl

from src.config import PROCESSED_DATA_DIR, PREDICTION_HORIZON_BARS, VOLATILITY_LOOKBACK


def compute_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes comprehensive trend, momentum, volatility, and volume indicators.
    Input DataFrame must have: Date, Open, High, Low, Close, Volume.
    """
    data = df.copy().sort_values("Date").reset_index(drop=True)
    
    close = data["Close"]
    high = data["High"]
    low = data["Low"]
    volume = data["Volume"]
    
    # 1. Trend Indicators
    data["sma_10"] = close.rolling(10).mean()
    data["sma_50"] = close.rolling(50).mean()
    data["sma_200"] = close.rolling(200).mean()
    
    data["dist_sma_10"] = (close / data["sma_10"]) - 1.0
    data["dist_sma_50"] = (close / data["sma_50"]) - 1.0
    data["dist_sma_200"] = (close / data["sma_200"]) - 1.0
    
    # Exponential Moving Averages & MACD
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    data["macd"] = ema_12 - ema_26
    data["macd_signal"] = data["macd"].ewm(span=9, adjust=False).mean()
    data["macd_hist"] = data["macd"] - data["macd_signal"]
    data["macd_ratio"] = data["macd"] / (close + 1e-8)
    
    # 2. Momentum Indicators
    # RSI (14-day)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / (avg_loss + 1e-8)
    data["rsi_14"] = 100.0 - (100.0 / (1.0 + rs))
    
    # Stochastic Oscillator
    low_14 = low.rolling(14).min()
    high_14 = high.rolling(14).max()
    data["stoch_k"] = 100.0 * (close - low_14) / ((high_14 - low_14) + 1e-8)
    data["stoch_d"] = data["stoch_k"].rolling(3).mean()
    
    # Rate of Change (Momentum)
    data["roc_5"] = close.pct_change(5)
    data["roc_10"] = close.pct_change(10)
    data["roc_20"] = close.pct_change(20)
    
    # 3. Volatility Indicators
    # Average True Range (ATR 14)
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    data["atr_14"] = tr.rolling(14).mean()
    data["atr_pct"] = data["atr_14"] / (close + 1e-8)
    
    # Realized Volatility (Annualized)
    log_ret = np.log(close / close.shift(1))
    data["volatility_20"] = log_ret.rolling(VOLATILITY_LOOKBACK).std() * np.sqrt(252)
    data["volatility_60"] = log_ret.rolling(60).std() * np.sqrt(252)
    
    # Bollinger Bands
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    data["bb_upper"] = bb_mid + 2.0 * bb_std
    data["bb_lower"] = bb_mid - 2.0 * bb_std
    data["bb_pct_b"] = (close - data["bb_lower"]) / ((data["bb_upper"] - data["bb_lower"]) + 1e-8)
    data["bb_width"] = (data["bb_upper"] - data["bb_lower"]) / (bb_mid + 1e-8)
    
    # 4. Volume Indicators
    vol_mean_20 = volume.rolling(20).mean()
    vol_std_20 = volume.rolling(20).std()
    data["volume_zscore"] = (volume - vol_mean_20) / (vol_std_20 + 1e-8)
    
    # On-Balance Volume (OBV)
    obv_direction = np.sign(delta).fillna(0)
    data["obv"] = (obv_direction * volume).cumsum()
    data["obv_roc_5"] = data["obv"].pct_change(5).replace([np.inf, -np.inf], 0)
    
    # 5. Market Regime Detection
    # Volatility Regime: 1 if volatility > 100-day rolling median, else 0
    vol_median_100 = data["volatility_20"].rolling(100).median()
    data["regime_high_vol"] = (data["volatility_20"] > vol_median_100).astype(int)
    
    # Trend Regime: 1 (Bull) if close > SMA50 and SMA50 > SMA200; -1 (Bear) if close < SMA50 and SMA50 < SMA200; 0 otherwise
    bull_condition = (close > data["sma_50"]) & (data["sma_50"] > data["sma_200"])
    bear_condition = (close < data["sma_50"]) & (data["sma_50"] < data["sma_200"])
    data["regime_trend"] = np.where(bull_condition, 1, np.where(bear_condition, -1, 0))
    
    # 6. Targets for Supervised Prediction (Strictly forward-looking for training)
    data["forward_return"] = close.shift(-PREDICTION_HORIZON_BARS) / close - 1.0
    data["target_direction"] = (data["forward_return"] > 0).astype(int)
    
    return data


def prepare_feature_dataset(
    df: pd.DataFrame,
    ticker: str,
    save_processed: bool = True,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Computes indicators, drops NA warm-up period, and returns (processed_df, feature_names).
    """
    processed = compute_technical_indicators(df)
    
    # Drop warm-up rows (200 rows needed for SMA 200) and future target nulls at the tail
    processed = processed.iloc[200:].copy()
    # Explicitly drop rows with unobserved forward targets to ensure supervised integrity
    processed = processed.dropna(subset=["forward_return"]).reset_index(drop=True)
    
    feature_columns = [
        "dist_sma_10", "dist_sma_50", "dist_sma_200",
        "macd_ratio", "macd_hist",
        "rsi_14", "stoch_k", "stoch_d",
        "roc_5", "roc_10", "roc_20",
        "atr_pct", "volatility_20", "volatility_60",
        "bb_pct_b", "bb_width",
        "volume_zscore", "obv_roc_5",
        "regime_high_vol", "regime_trend",
    ]
    
    if save_processed:
        clean_ticker = ticker.upper().replace("^", "")
        out_path = PROCESSED_DATA_DIR / f"{clean_ticker}_features.parquet"
        processed.to_parquet(out_path, index=False, compression="zstd")
        print(f"[FeaturePipeline] Saved feature matrix for {ticker} ({len(processed)} rows) -> {out_path}")
        
    return processed, feature_columns


if __name__ == "__main__":
    from src.data_loader import fetch_and_cache_ticker
    raw_df = fetch_and_cache_ticker("SPY")
    proc_df, features = prepare_feature_dataset(raw_df, "SPY")
    print(f"Features engineered ({len(features)} total): {features[:6]}...")
    print(f"Dataset shape: {proc_df.shape}")
