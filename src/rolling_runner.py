"""
Rolling Walk-Forward Experiment Campaign Runner for NSE Equities.

Contract:
- Universe: RELIANCE.NS, TCS.NS, INFY.NS (evaluated strictly individually).
- Input: Immutable Parquet files under reports/experiments/inputs/ verified against manifest SHA-256.
- Folds: 6 test years (2020 through 2025).
  Train: [Y-8, Y-4] (5 calendar years) with 3-bar target horizon purge.
  Val:   [Y-3]     (1 calendar year) with 3-bar target horizon purge.
  Dev:   [Y-2, Y-1] (2 calendar years).
  Test:  [Y]       (1 calendar year).
- Models & Seeds:
  LightGBM classifier: model_seed=42 fixed.
  NSGA-II optimizer: GA seeds 42, 43, 44 evaluated separately.
- Baseline Comparisons:
  1. Full-exposure Buy & Hold (starts at first test bar Open with friction, liquidates at last bar Close).
  2. Cash Baseline (100% cash, 0% interest).
  3. Fixed SMA 50/200 (Long when Close[t-1] > SMA50[t-1] and SMA50[t-1] > SMA200[t-1]; cash otherwise).
  4. Fixed Gene Hybrid (LightGBM with unoptimized chromosome [0.55, 0.45, 2.0, 3.5, 0.03, 0.5, 15.0]).
  5. Constant Probability Ablation (p=0.60 evolved without ML on Dev and Test).
  6. Exposure-Matched Buy & Hold diagnostic (blends B&H daily returns with cash using hybrid DEV exposure fraction).
- Cost Sensitivity:
  Doubled friction (0.10% commission, 0.10% slippage) evaluated for the already-frozen full hybrid chromosome.
"""

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, accuracy_score, brier_score_loss

from src.config import (
    DEFAULT_COMMISSION_PCT,
    DEFAULT_SLIPPAGE_PCT,
    INITIAL_CAPITAL,
    PREDICTION_HORIZON_BARS,
)
from src.feature_pipeline import compute_technical_indicators
from src.predictor import MarketPredictor
from src.evolutionary_core import NSGA2Optimizer
from src.backtest_engine import (
    run_vectorized_simulation_fast,
    get_detailed_simulation_results,
)

FEATURE_COLUMNS = [
    "dist_sma_10", "dist_sma_50", "dist_sma_200",
    "macd_ratio", "macd_hist",
    "rsi_14", "stoch_k", "stoch_d",
    "roc_5", "roc_10", "roc_20",
    "atr_pct", "volatility_20", "volatility_60",
    "bb_pct_b", "bb_width",
    "volume_zscore", "obv_roc_5",
    "regime_high_vol", "regime_trend",
]

FIXED_HYBRID_GENES = np.array([0.55, 0.45, 2.0, 3.5, 0.03, 0.5, 15.0], dtype=np.float64)


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_manifest(inputs_dir: Path, manifest_path: Path) -> Dict[str, Any]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    for ticker, meta in manifest.items():
        parquet_file = inputs_dir / f"{ticker}.parquet"
        if not parquet_file.exists():
            raise FileNotFoundError(f"Snapshot missing for {ticker}: {parquet_file}")
        computed_hash = compute_sha256(parquet_file)
        expected_hash = meta["sha256"]
        if computed_hash != expected_hash:
            raise ValueError(
                f"SHA-256 mismatch for {ticker}! Expected {expected_hash}, got {computed_hash}"
            )
    return manifest


def compute_performance_metrics(
    equity: np.ndarray,
    positions: np.ndarray,
    trades_count: int,
    win_rate: float,
    initial_capital: float = INITIAL_CAPITAL,
    trading_days_per_year: float = 252.0,
    capital_exposures: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    n = len(equity)
    if n == 0:
        return {
            "total_return": 0.0,
            "cagr": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "annualized_volatility": 0.0,
            "total_trades": 0,
            "win_rate": 0.0,
            "exposure_fraction": 0.0,
            "capital_exposure": 0.0,
            "terminal_equity": initial_capital,
        }

    terminal_equity = float(equity[-1])
    total_return = float((terminal_equity / initial_capital) - 1.0)

    # CAGR: (terminal / initial) ** (252 / n) - 1
    if terminal_equity > 0.0 and n > 0:
        cagr = float((terminal_equity / initial_capital) ** (trading_days_per_year / float(n)) - 1.0)
    else:
        cagr = -1.0

    # Max Drawdown: includes pre-trade initial capital peak
    running_max = np.maximum.accumulate(np.insert(equity, 0, initial_capital))
    drawdowns = (running_max[1:] - equity) / (running_max[1:] + 1e-8)
    max_dd = float(np.max(drawdowns))

    # Daily returns & Sharpe & Volatility: includes first-day return from pre-trade initial capital
    if n > 0:
        daily_returns = np.empty(n, dtype=np.float64)
        daily_returns[0] = (equity[0] - initial_capital) / (initial_capital + 1e-8)
        for j in range(1, n):
            daily_returns[j] = (equity[j] - equity[j - 1]) / (equity[j - 1] + 1e-8)
        mean_ret = float(np.mean(daily_returns))
        std_ret = float(np.std(daily_returns))
        sharpe = float((mean_ret / std_ret) * np.sqrt(trading_days_per_year)) if std_ret >= 1e-8 else 0.0
        annualized_vol = float(std_ret * np.sqrt(trading_days_per_year))
    else:
        sharpe = 0.0
        annualized_vol = 0.0

    exposure_fraction = float(np.mean(positions > 0.0)) if len(positions) > 0 else 0.0
    cap_exp = float(np.mean(capital_exposures)) if capital_exposures is not None and len(capital_exposures) > 0 else exposure_fraction

    return {
        "total_return": total_return,
        "cagr": cagr,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_dd,
        "annualized_volatility": annualized_vol,
        "total_trades": int(trades_count),
        "win_rate": float(win_rate),
        "exposure_fraction": exposure_fraction,
        "capital_exposure": cap_exp,
        "terminal_equity": terminal_equity,
    }


def simulate_buy_and_hold(
    test_df: pd.DataFrame,
    commission_pct: float = DEFAULT_COMMISSION_PCT,
    slippage_pct: float = DEFAULT_SLIPPAGE_PCT,
    initial_capital: float = INITIAL_CAPITAL,
) -> Dict[str, Any]:
    n = len(test_df)
    if n == 0:
        return {
            "equity": np.array([]),
            "positions": np.array([]),
            "capital_exposures": np.array([]),
            "trade_log": [],
            "entries": [],
            "exits": [],
            "metrics": compute_performance_metrics(np.array([]), np.array([]), 0, 0.0),
        }

    open_p = test_df["Open"].to_numpy(dtype=np.float64)
    close_p = test_df["Close"].to_numpy(dtype=np.float64)
    volumes = test_df["Volume"].to_numpy(dtype=np.float64) if "Volume" in test_df.columns else None
    dates = [pd.to_datetime(d).strftime("%Y-%m-%d") for d in test_df["Date"].values]

    # Find first bar with volume > 0 for entry
    first_trade_idx = -1
    for k in range(n):
        if volumes is None or volumes[k] > 0.0:
            first_trade_idx = k
            break

    # Find last bar with volume > 0 for terminal liquidation
    last_trade_idx = -1
    for k in range(n - 1, -1, -1):
        if volumes is None or volumes[k] > 0.0:
            last_trade_idx = k
            break

    if first_trade_idx == -1 or last_trade_idx == -1 or first_trade_idx > last_trade_idx:
        # No tradable volume in fold
        equity = np.full(n, initial_capital, dtype=np.float64)
        positions = np.zeros(n, dtype=np.float64)
        capital_exposures = np.zeros(n, dtype=np.float64)
        return {
            "equity": equity,
            "positions": positions,
            "capital_exposures": capital_exposures,
            "trade_log": [],
            "entries": [],
            "exits": [],
            "metrics": compute_performance_metrics(equity, positions, 0, 0.0, initial_capital, capital_exposures=capital_exposures),
        }

    entry_exec = open_p[first_trade_idx] * (1.0 + slippage_pct)
    shares = (initial_capital * (1.0 - commission_pct)) / entry_exec
    cash_rem = initial_capital - (shares * entry_exec * (1.0 + commission_pct))
    entry_cost = shares * entry_exec * (1.0 + commission_pct)

    equity = np.empty(n, dtype=np.float64)
    positions = np.zeros(n, dtype=np.float64)
    capital_exposures = np.zeros(n, dtype=np.float64)

    # Before entry
    for i in range(first_trade_idx):
        equity[i] = initial_capital
        positions[i] = 0.0
        capital_exposures[i] = 0.0

    # During holding (up to last tradable bar)
    for i in range(first_trade_idx, last_trade_idx):
        equity[i] = cash_rem + shares * close_p[i]
        positions[i] = 1.0
        capital_exposures[i] = (shares * close_p[i]) / (equity[i] + 1e-8)

    # Liquidate at last tradable bar Close
    exit_exec = close_p[last_trade_idx] * (1.0 - slippage_pct)
    proceeds = shares * exit_exec * (1.0 - commission_pct)
    final_cash = cash_rem + proceeds
    equity[last_trade_idx] = final_cash
    positions[last_trade_idx] = 0.0
    capital_exposures[last_trade_idx] = 0.0

    # After liquidation (if any trailing non-tradable bars)
    for i in range(last_trade_idx + 1, n):
        equity[i] = final_cash
        positions[i] = 0.0
        capital_exposures[i] = 0.0

    pnl = proceeds - entry_cost
    pnl_pct = (proceeds / entry_cost) - 1.0
    trade_log = [{
        "entry_date": dates[first_trade_idx],
        "exit_date": dates[last_trade_idx],
        "entry_price": float(entry_exec),
        "exit_price": float(exit_exec),
        "pnl": float(pnl),
        "pnl_pct": float(pnl_pct),
        "holding_bars": int(last_trade_idx - first_trade_idx),
        "exit_reason": "Final Horizon Liquidation",
    }]
    entries = [{"date": dates[first_trade_idx], "price": float(entry_exec)}]
    exits = [{"date": dates[last_trade_idx], "price": float(exit_exec), "reason": "Final Horizon Liquidation", "pnl": float(pnl)}]

    win = 1.0 if final_cash > initial_capital else 0.0
    metrics = compute_performance_metrics(equity, positions, 1, win, initial_capital, capital_exposures=capital_exposures)
    return {
        "equity": equity,
        "positions": positions,
        "capital_exposures": capital_exposures,
        "trade_log": trade_log,
        "entries": entries,
        "exits": exits,
        "metrics": metrics,
    }


def simulate_cash_baseline(
    test_df: pd.DataFrame,
    initial_capital: float = INITIAL_CAPITAL,
) -> Dict[str, Any]:
    n = len(test_df)
    equity = np.full(n, initial_capital, dtype=np.float64)
    positions = np.zeros(n, dtype=np.float64)
    capital_exposures = np.zeros(n, dtype=np.float64)
    metrics = compute_performance_metrics(equity, positions, 0, 0.0, initial_capital, capital_exposures=capital_exposures)
    return {
        "equity": equity,
        "positions": positions,
        "capital_exposures": capital_exposures,
        "trade_log": [],
        "entries": [],
        "exits": [],
        "metrics": metrics,
    }


def simulate_sma_baseline(
    test_df: pd.DataFrame,
    commission_pct: float = DEFAULT_COMMISSION_PCT,
    slippage_pct: float = DEFAULT_SLIPPAGE_PCT,
    initial_capital: float = INITIAL_CAPITAL,
    prefix_signal: bool = False,
) -> Dict[str, Any]:
    n = len(test_df)
    if n == 0:
        return {
            "equity": np.array([]),
            "positions": np.array([]),
            "capital_exposures": np.array([]),
            "trade_log": [],
            "entries": [],
            "exits": [],
            "metrics": compute_performance_metrics(np.array([]), np.array([]), 0, 0.0),
        }

    open_p = test_df["Open"].to_numpy(dtype=np.float64)
    close_p = test_df["Close"].to_numpy(dtype=np.float64)
    sma50 = test_df["sma_50"].to_numpy(dtype=np.float64)
    sma200 = test_df["sma_200"].to_numpy(dtype=np.float64)
    volumes = test_df["Volume"].to_numpy(dtype=np.float64) if "Volume" in test_df.columns else None
    dates = [pd.to_datetime(d).strftime("%Y-%m-%d") for d in test_df["Date"].values]

    cash = initial_capital
    position = 0.0
    trade_pnls = []
    trade_log = []
    entries = []
    exits = []

    entry_cost_val = 0.0
    entry_price_val = 0.0
    entry_idx = 0

    equity = np.empty(n, dtype=np.float64)
    positions = np.zeros(n, dtype=np.float64)
    capital_exposures = np.zeros(n, dtype=np.float64)

    # Identify last tradable bar for deterministic scheduled fold-end liquidation
    last_tradable_idx = -1
    for k in range(n - 1, -1, -1):
        if volumes is None or volumes[k] > 0.0:
            last_tradable_idx = k
            break

    for i in range(n):
        has_volume = volumes is None or volumes[i] > 0.0
        queue_entry = False
        queue_exit = False

        if i == 0:
            if prefix_signal and position == 0.0:
                queue_entry = True
        else:
            signal = (close_p[i - 1] > sma50[i - 1]) and (sma50[i - 1] > sma200[i - 1])
            if signal and position == 0.0:
                queue_entry = True
            elif not signal and position > 0.0:
                queue_exit = True

        # Phase 2A: Queued Exit at Open
        if position > 0.0 and queue_exit and has_volume:
            exec_p = open_p[i] * (1.0 - slippage_pct)
            proceeds = position * exec_p * (1.0 - commission_pct)
            cash += proceeds
            pnl = proceeds - entry_cost_val
            pnl_pct = (proceeds / entry_cost_val) - 1.0
            trade_pnls.append(pnl)
            trade_log.append({
                "entry_date": dates[entry_idx],
                "exit_date": dates[i],
                "entry_price": float(entry_price_val),
                "exit_price": float(exec_p),
                "pnl": float(pnl),
                "pnl_pct": float(pnl_pct),
                "holding_bars": int(i - entry_idx),
                "exit_reason": "SMA Trend Exit",
            })
            exits.append({"date": dates[i], "price": float(exec_p), "reason": "SMA Trend Exit", "pnl": float(pnl)})
            position = 0.0

        # Phase 2C: Queued Entry at Open (full cash allocation, only if before last tradable bar)
        if position == 0.0 and queue_entry and has_volume and (last_tradable_idx == -1 or i < last_tradable_idx):
            exec_p = open_p[i] * (1.0 + slippage_pct)
            shares = (cash * (1.0 - commission_pct)) / exec_p
            if shares > 0.0001:
                cost = shares * exec_p * (1.0 + commission_pct)
                cash -= cost
                position = shares
                entry_cost_val = cost
                entry_price_val = exec_p
                entry_idx = i
                entries.append({"date": dates[i], "price": float(exec_p)})

        # Phase 2F: Final Bar Liquidation at last tradable session
        if i == last_tradable_idx and position > 0.0 and has_volume:
            exec_p = close_p[i] * (1.0 - slippage_pct)
            proceeds = position * exec_p * (1.0 - commission_pct)
            cash += proceeds
            pnl = proceeds - entry_cost_val
            pnl_pct = (proceeds / entry_cost_val) - 1.0
            trade_pnls.append(pnl)
            trade_log.append({
                "entry_date": dates[entry_idx],
                "exit_date": dates[i],
                "entry_price": float(entry_price_val),
                "exit_price": float(exec_p),
                "pnl": float(pnl),
                "pnl_pct": float(pnl_pct),
                "holding_bars": int(i - entry_idx),
                "exit_reason": "Final Horizon Liquidation",
            })
            exits.append({"date": dates[i], "price": float(exec_p), "reason": "Final Horizon Liquidation", "pnl": float(pnl)})
            position = 0.0

        equity[i] = cash + position * close_p[i]
        positions[i] = 1.0 if position > 0.0 else 0.0
        capital_exposures[i] = (position * close_p[i]) / (equity[i] + 1e-8)

    round_trips_count = len(trade_log)
    win_rate = float(np.mean([p > 0.0 for p in trade_pnls])) if len(trade_pnls) > 0 else 0.0
    metrics = compute_performance_metrics(equity, positions, round_trips_count, win_rate, initial_capital, capital_exposures=capital_exposures)
    return {
        "equity": equity,
        "positions": positions,
        "capital_exposures": capital_exposures,
        "trade_log": trade_log,
        "entries": entries,
        "exits": exits,
        "metrics": metrics,
    }


def simulate_exposure_matched_bh(
    bh_equity: np.ndarray,
    dev_exposure_fraction: float,
    initial_capital: float = INITIAL_CAPITAL,
) -> Dict[str, Any]:
    """
    Hypothetical exposure-matched Buy & Hold diagnostic:
    Blends all Buy & Hold daily returns (including day 0 relative to pre-trade initial capital)
    with cash (earning 0%) using the hybrid strategy's DEVELOPMENT-only capital exposure weight.
    Assumptions: frictionless cash rebalancing and 0% risk-free rate; not an unmanaged static stock holding.
    """
    n = len(bh_equity)
    if n == 0:
        equity = np.array([])
        positions = np.array([])
        capital_exposures = np.array([])
        return {
            "equity": equity,
            "positions": positions,
            "capital_exposures": capital_exposures,
            "trade_log": [],
            "entries": [],
            "exits": [],
            "metrics": compute_performance_metrics(equity, positions, 0, 0.0, initial_capital),
        }

    # Daily returns of B&H including day 0
    bh_daily_ret = np.empty(n, dtype=np.float64)
    bh_daily_ret[0] = (bh_equity[0] - initial_capital) / (initial_capital + 1e-8)
    for t in range(1, n):
        bh_daily_ret[t] = (bh_equity[t] - bh_equity[t - 1]) / (bh_equity[t - 1] + 1e-8)

    blended_daily_ret = dev_exposure_fraction * bh_daily_ret

    equity = np.empty(n, dtype=np.float64)
    equity[0] = initial_capital * (1.0 + blended_daily_ret[0])
    for t in range(1, n):
        equity[t] = equity[t - 1] * (1.0 + blended_daily_ret[t])

    positions = np.full(n, 1.0 if dev_exposure_fraction > 0 else 0.0, dtype=np.float64)
    capital_exposures = np.full(n, dev_exposure_fraction, dtype=np.float64)
    metrics = compute_performance_metrics(
        equity, positions, 1 if dev_exposure_fraction > 0 else 0,
        1.0 if equity[-1] > initial_capital else 0.0, initial_capital,
        capital_exposures=capital_exposures
    )
    return {
        "equity": equity,
        "positions": positions,
        "capital_exposures": capital_exposures,
        "trade_log": [],
        "entries": [],
        "exits": [],
        "metrics": metrics,
    }


def stitch_equity_curves(
    daily_equities: List[List[float]],
    initial_capital: float = INITIAL_CAPITAL,
) -> np.ndarray:
    """
    Stitches non-overlapping annual test equity curves by carrying capital forward.
    Each fold k scales by fold_scale[t] = eq_k[t] / initial_capital (100,000 for standard runs).
    This strictly preserves day 0 returns and entry friction, guaranteeing that
    stitched terminal / initial capital == prod_k (fold_terminal_k / fold_initial_k).
    """
    total_bars = sum(len(eq) for eq in daily_equities)
    stitched = np.empty(total_bars, dtype=np.float64)

    curr_capital = initial_capital
    idx = 0
    for eq_list in daily_equities:
        eq_arr = np.array(eq_list, dtype=np.float64)
        n = len(eq_arr)
        if n == 0:
            continue
        fold_scale = eq_arr / initial_capital
        stitched[idx : idx + n] = curr_capital * fold_scale
        curr_capital = stitched[idx + n - 1]
        idx += n

    return stitched


class RollingNSEExperimentRunner:
    """
    Executes the frozen retrospective rolling experiment protocol.
    """

    def __init__(
        self,
        inputs_dir: Path,
        output_dir: Path,
        protocol_path: Path,
        test_years: Optional[List[int]] = None,
        universe: Optional[List[str]] = None,
        ga_seeds: Optional[List[int]] = None,
        model_seed: int = 42,
    ):
        self.inputs_dir = inputs_dir
        self.output_dir = output_dir
        self.protocol_path = protocol_path
        self.manifest_path = inputs_dir / "manifest.json"
        self.correction_path = output_dir / "protocol_correction.json"

        with open(protocol_path, "r") as f:
            self.protocol = json.load(f)

        self.test_years = test_years or self.protocol["test_years"]
        self.universe = universe or self.protocol["universe"]
        self.ga_seeds = ga_seeds or self.protocol["evolutionary_specification"]["evolution_seeds"]
        self.model_seed = model_seed

        # Results directory
        self.results_dir = self.output_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Verify input manifest
        self.manifest = verify_manifest(self.inputs_dir, self.manifest_path)

    def load_processed_asset(self, ticker: str) -> pd.DataFrame:
        parquet_file = self.inputs_dir / f"{ticker}.parquet"
        df = pd.read_parquet(parquet_file)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        # Compute indicators causally from the complete historical prefix
        processed = compute_technical_indicators(df)
        return processed

    def run_fold(
        self,
        ticker: str,
        df_full: pd.DataFrame,
        test_year: int,
    ) -> Dict[str, Any]:
        """
        Runs one annual fold for an asset:
        - Train: [Y-8, Y-4] (purged trailing 3 bars)
        - Val:   [Y-3]     (purged trailing 3 bars)
        - Dev:   [Y-2, Y-1] (purged trailing 3 bars for GA training/validation)
        - Preceding bar: Final completed bar of Dev partition supplies causal prefix context
        - Test:  [Y]       (out-of-sample trading; classification scored on valid non-boundary bars)
        """
        y = test_year
        train_raw = df_full[(df_full["Date"] >= f"{y-8}-01-01") & (df_full["Date"] <= f"{y-4}-12-31")].copy()
        val_raw = df_full[(df_full["Date"] >= f"{y-3}-01-01") & (df_full["Date"] <= f"{y-3}-12-31")].copy()
        dev_raw = df_full[(df_full["Date"] >= f"{y-2}-01-01") & (df_full["Date"] <= f"{y-1}-12-31")].copy()
        test_df = df_full[(df_full["Date"] >= f"{y}-01-01") & (df_full["Date"] <= f"{y}-12-31")].copy().reset_index(drop=True)

        # Drop 3 trailing bars from train, val, and dev to purge overlapping forward targets
        train_df = train_raw.iloc[:-PREDICTION_HORIZON_BARS].copy().reset_index(drop=True)
        val_df = val_raw.iloc[:-PREDICTION_HORIZON_BARS].copy().reset_index(drop=True)
        dev_df = dev_raw.iloc[:-PREDICTION_HORIZON_BARS].copy().reset_index(drop=True)

        # 1. Fit LightGBM Model (model_seed = 42)
        predictor = MarketPredictor(ticker, FEATURE_COLUMNS, model_seed=self.model_seed)
        train_metrics = predictor.train(train_df, val_df)

        # Generate probabilities
        p_up_dev = predictor.predict_proba(dev_df)
        p_up_dev_raw = predictor.predict_proba(dev_raw.reset_index(drop=True))
        p_up_test = predictor.predict_proba(test_df)

        # Causal Preceding Completed Bar Prefix Context for Bar 0 Open Trading
        prefix_p_up = float(p_up_dev_raw[-1])
        prefix_atr = float(dev_raw.iloc[-1]["atr_14"])
        prefix_regime_vol = int(dev_raw.iloc[-1]["regime_high_vol"])
        prefix_sma_signal = bool(
            (dev_raw.iloc[-1]["Close"] > dev_raw.iloc[-1]["sma_50"])
            and (dev_raw.iloc[-1]["sma_50"] > dev_raw.iloc[-1]["sma_200"])
        )

        # Mask classification outcomes extending outside annual fold or into NaNs
        test_valid_mask = test_df["forward_return"].notna() & (test_df.index < (len(test_df) - PREDICTION_HORIZON_BARS))
        y_test_scored = test_df.loc[test_valid_mask, "target_direction"].values
        p_up_test_scored = p_up_test[test_valid_mask.values]

        scored_count = int(test_valid_mask.sum())
        first_scored_date = str(test_df.loc[test_valid_mask, "Date"].iloc[0].strftime("%Y-%m-%d")) if scored_count > 0 else ""
        last_scored_date = str(test_df.loc[test_valid_mask, "Date"].iloc[-1].strftime("%Y-%m-%d")) if scored_count > 0 else ""

        test_auc = float(roc_auc_score(y_test_scored, p_up_test_scored)) if len(np.unique(y_test_scored)) > 1 else 0.5
        test_acc = float(accuracy_score(y_test_scored, (p_up_test_scored > 0.5).astype(int))) if scored_count > 0 else 0.0
        test_brier = float(brier_score_loss(y_test_scored, p_up_test_scored)) if scored_count > 0 else 0.25

        train_p_pos = float(train_df["target_direction"].mean())
        base_probs = np.full(len(y_test_scored), train_p_pos)
        base_acc = float(accuracy_score(y_test_scored, (base_probs > 0.5).astype(int))) if scored_count > 0 else 0.0
        base_brier = float(brier_score_loss(y_test_scored, base_probs)) if scored_count > 0 else 0.25

        model_eval = {
            "val_auc": float(train_metrics.get("val_auc", 0.5)),
            "val_accuracy": float(train_metrics.get("val_acc", 0.5)),
            "val_brier": float(train_metrics.get("val_brier", 0.25)),
            "test_auc": test_auc,
            "test_accuracy": test_acc,
            "test_brier": test_brier,
            "train_positive_fraction": train_p_pos,
            "baseline_accuracy": base_acc,
            "baseline_brier": base_brier,
            "train_bars": len(train_df),
            "val_bars": len(val_df),
            "dev_bars": len(dev_df),
            "dev_raw_bars": len(dev_raw),
            "test_bars": len(test_df),
            "scored_test_samples": scored_count,
            "masked_test_samples": len(test_df) - scored_count,
            "first_scored_date": first_scored_date,
            "last_scored_date": last_scored_date,
            "purged_bars_per_boundary": PREDICTION_HORIZON_BARS,
        }

        # Arrays for Dev and Test simulation
        open_dev = dev_df["Open"].to_numpy(dtype=np.float64)
        close_dev = dev_df["Close"].to_numpy(dtype=np.float64)
        high_dev = dev_df["High"].to_numpy(dtype=np.float64)
        low_dev = dev_df["Low"].to_numpy(dtype=np.float64)
        atr_dev = dev_df["atr_14"].to_numpy(dtype=np.float64)
        reg_vol_dev = dev_df["regime_high_vol"].to_numpy(dtype=np.int32)
        vol_dev = dev_df["Volume"].to_numpy(dtype=np.float64) if "Volume" in dev_df.columns else None

        # Fixed baselines (evaluated once per fold)
        bh_res = simulate_buy_and_hold(test_df)
        cash_res = simulate_cash_baseline(test_df)
        sma_res = simulate_sma_baseline(test_df, prefix_signal=prefix_sma_signal)

        # Fixed-gene hybrid test evaluation
        fixed_hybrid_res = get_detailed_simulation_results(
            test_df, p_up_test, FIXED_HYBRID_GENES,
            prefix_p_up=prefix_p_up, prefix_atr=prefix_atr, prefix_regime_vol=prefix_regime_vol
        )
        fixed_hybrid_metrics = compute_performance_metrics(
            fixed_hybrid_res["equity"],
            fixed_hybrid_res["positions"],
            fixed_hybrid_res["total_trades"],
            fixed_hybrid_res["win_rate"],
            capital_exposures=fixed_hybrid_res["capital_exposures"],
        )
        fixed_tl = fixed_hybrid_res["trade_log"].to_dict(orient="records")
        fixed_trade_log = [
            {
                "entry_date": pd.to_datetime(t["entry_date"]).strftime("%Y-%m-%d"),
                "exit_date": pd.to_datetime(t["exit_date"]).strftime("%Y-%m-%d"),
                "entry_price": float(t["entry_price"]),
                "exit_price": float(t["exit_price"]),
                "pnl": float(t["pnl"]),
                "pnl_pct": float(t["pnl_pct"]),
                "holding_bars": int(t["holding_bars"]),
                "exit_reason": str(t["exit_reason"]),
            }
            for t in fixed_tl
        ]
        fixed_entries = [{"date": t["entry_date"], "price": t["entry_price"]} for t in fixed_trade_log]
        fixed_exits = [{"date": t["exit_date"], "price": t["exit_price"], "reason": t["exit_reason"], "pnl": t["pnl"]} for t in fixed_trade_log]

        fold_results = {
            "ticker": ticker,
            "test_year": test_year,
            "model_eval": model_eval,
            "prefix_context": {
                "prefix_p_up": prefix_p_up,
                "prefix_atr": prefix_atr,
                "prefix_regime_vol": prefix_regime_vol,
                "prefix_sma_signal": prefix_sma_signal,
            },
            "baselines": {
                "buy_and_hold": {
                    "metrics": bh_res["metrics"],
                    "equity": bh_res["equity"].tolist(),
                    "positions": bh_res["positions"].tolist(),
                    "capital_exposures": bh_res["capital_exposures"].tolist(),
                    "trade_log": bh_res["trade_log"],
                    "entries": bh_res["entries"],
                    "exits": bh_res["exits"],
                },
                "cash": {
                    "metrics": cash_res["metrics"],
                    "equity": cash_res["equity"].tolist(),
                    "positions": cash_res["positions"].tolist(),
                    "capital_exposures": cash_res["capital_exposures"].tolist(),
                    "trade_log": cash_res["trade_log"],
                    "entries": cash_res["entries"],
                    "exits": cash_res["exits"],
                },
                "sma_50_200": {
                    "metrics": sma_res["metrics"],
                    "equity": sma_res["equity"].tolist(),
                    "positions": sma_res["positions"].tolist(),
                    "capital_exposures": sma_res["capital_exposures"].tolist(),
                    "trade_log": sma_res["trade_log"],
                    "entries": sma_res["entries"],
                    "exits": sma_res["exits"],
                },
                "fixed_gene_hybrid": {
                    "metrics": fixed_hybrid_metrics,
                    "equity": fixed_hybrid_res["equity"].tolist(),
                    "positions": fixed_hybrid_res["positions"].tolist(),
                    "capital_exposures": fixed_hybrid_res["capital_exposures"].tolist(),
                    "trade_log": fixed_trade_log,
                    "entries": fixed_entries,
                    "exits": fixed_exits,
                },
            },
            "ga_runs": {},
            "test_dates": [pd.to_datetime(d).strftime("%Y-%m-%d") for d in test_df["Date"]],
            "p_up_test": p_up_test.tolist(),
        }

        # 2. Run GA for each seed
        for seed in self.ga_seeds:
            # A. Full Hybrid Optimization
            opt = NSGA2Optimizer(
                open_prices=open_dev,
                close=close_dev,
                high=high_dev,
                low=low_dev,
                p_up=p_up_dev,
                atr=atr_dev,
                regime_vol=reg_vol_dev,
                pop_size=self.protocol["evolutionary_specification"]["population_size"],
                num_generations=self.protocol["evolutionary_specification"]["generations"],
                seed=seed,
                volume=vol_dev,
            )
            pareto_front = opt.run()

            # Representative strategy selection on Dev:
            dev_evals = []
            for ind in pareto_front:
                sh, mdd, ret, trades, to = run_vectorized_simulation_fast(
                    open_dev, close_dev, high_dev, low_dev, p_up_dev, atr_dev, reg_vol_dev,
                    ind.genes, apply_penalty=False, volume=vol_dev
                )
                dev_evals.append({
                    "dev_sharpe": sh,
                    "dev_mdd": mdd,
                    "dev_return": ret,
                    "dev_trades": trades,
                    "genes": ind.genes,
                })

            valid_dev = [e for e in dev_evals if e["dev_trades"] >= 5]
            if len(valid_dev) > 0:
                best_dev = max(valid_dev, key=lambda x: x["dev_sharpe"])
                is_feasible = True
                chosen_genes = best_dev["genes"]
                # Obtain exact dev capital exposure by running detailed simulation on dev
                dev_det = get_detailed_simulation_results(dev_df, p_up_dev, chosen_genes)
                dev_capital_exposure = float(dev_det["capital_exposure"])
                dev_time_in_market = float(dev_det["time_in_market"])
            else:
                is_feasible = False
                chosen_genes = None
                dev_capital_exposure = 0.0
                dev_time_in_market = 0.0
                best_dev = {
                    "dev_sharpe": 0.0,
                    "dev_mdd": 0.0,
                    "dev_return": 0.0,
                    "dev_trades": 0,
                    "genes": None,
                }

            # Evaluate chosen strategy on Test
            if is_feasible:
                test_det = get_detailed_simulation_results(
                    test_df, p_up_test, chosen_genes,
                    prefix_p_up=prefix_p_up, prefix_atr=prefix_atr, prefix_regime_vol=prefix_regime_vol
                )
                hybrid_metrics = compute_performance_metrics(
                    test_det["equity"],
                    test_det["positions"],
                    test_det["total_trades"],
                    test_det["win_rate"],
                    capital_exposures=test_det["capital_exposures"],
                )
                hybrid_equity = test_det["equity"]
                hybrid_positions = test_det["positions"]
                hybrid_capital_exposures = test_det["capital_exposures"]

                tl_hyb = test_det["trade_log"].to_dict(orient="records")
                hybrid_trade_log = [
                    {
                        "entry_date": pd.to_datetime(t["entry_date"]).strftime("%Y-%m-%d"),
                        "exit_date": pd.to_datetime(t["exit_date"]).strftime("%Y-%m-%d"),
                        "entry_price": float(t["entry_price"]),
                        "exit_price": float(t["exit_price"]),
                        "pnl": float(t["pnl"]),
                        "pnl_pct": float(t["pnl_pct"]),
                        "holding_bars": int(t["holding_bars"]),
                        "exit_reason": str(t["exit_reason"]),
                    }
                    for t in tl_hyb
                ]
                hybrid_entries = [{"date": t["entry_date"], "price": t["entry_price"]} for t in hybrid_trade_log]
                hybrid_exits = [{"date": t["exit_date"], "price": t["exit_price"], "reason": t["exit_reason"], "pnl": t["pnl"]} for t in hybrid_trade_log]

                # Cost sensitivity at 2x costs without re-optimizing
                cost_det = get_detailed_simulation_results(
                    test_df,
                    p_up_test,
                    chosen_genes,
                    commission_pct=DEFAULT_COMMISSION_PCT * 2.0,
                    slippage_pct=DEFAULT_SLIPPAGE_PCT * 2.0,
                    prefix_p_up=prefix_p_up,
                    prefix_atr=prefix_atr,
                    prefix_regime_vol=prefix_regime_vol,
                )
                cost_metrics = compute_performance_metrics(
                    cost_det["equity"],
                    cost_det["positions"],
                    cost_det["total_trades"],
                    cost_det["win_rate"],
                    capital_exposures=cost_det["capital_exposures"],
                )
                cost_equity = cost_det["equity"]
                cost_capital_exposures = cost_det["capital_exposures"]
                tl_cost = cost_det["trade_log"].to_dict(orient="records")
                cost_trade_log = [
                    {
                        "entry_date": pd.to_datetime(t["entry_date"]).strftime("%Y-%m-%d"),
                        "exit_date": pd.to_datetime(t["exit_date"]).strftime("%Y-%m-%d"),
                        "entry_price": float(t["entry_price"]),
                        "exit_price": float(t["exit_price"]),
                        "pnl": float(t["pnl"]),
                        "pnl_pct": float(t["pnl_pct"]),
                        "holding_bars": int(t["holding_bars"]),
                        "exit_reason": str(t["exit_reason"]),
                    }
                    for t in tl_cost
                ]
                cost_entries = [{"date": t["entry_date"], "price": t["entry_price"]} for t in cost_trade_log]
                cost_exits = [{"date": t["exit_date"], "price": t["exit_price"], "reason": t["exit_reason"], "pnl": t["pnl"]} for t in cost_trade_log]
            else:
                # Infeasible -> Default to 100% Cash
                hybrid_equity = np.full(len(test_df), INITIAL_CAPITAL, dtype=np.float64)
                hybrid_positions = np.zeros(len(test_df), dtype=np.float64)
                hybrid_capital_exposures = np.zeros(len(test_df), dtype=np.float64)
                hybrid_metrics = compute_performance_metrics(
                    hybrid_equity, hybrid_positions, 0, 0.0, capital_exposures=hybrid_capital_exposures
                )
                hybrid_trade_log = []
                hybrid_entries = []
                hybrid_exits = []

                cost_equity = hybrid_equity.copy()
                cost_capital_exposures = hybrid_capital_exposures.copy()
                cost_metrics = hybrid_metrics.copy()
                cost_trade_log = []
                cost_entries = []
                cost_exits = []

            # Exposure-matched Buy & Hold diagnostic using DEVELOPMENT-only capital exposure
            exp_bh_res = simulate_exposure_matched_bh(bh_res["equity"], dev_capital_exposure)

            # B. Constant Probability Ablation (p=0.60)
            p_const_dev = np.full(len(dev_df), 0.60, dtype=np.float64)
            p_const_test = np.full(len(test_df), 0.60, dtype=np.float64)
            opt_abl = NSGA2Optimizer(
                open_prices=open_dev,
                close=close_dev,
                high=high_dev,
                low=low_dev,
                p_up=p_const_dev,
                atr=atr_dev,
                regime_vol=reg_vol_dev,
                pop_size=self.protocol["evolutionary_specification"]["population_size"],
                num_generations=self.protocol["evolutionary_specification"]["generations"],
                seed=seed,
                volume=vol_dev,
            )
            pareto_abl = opt_abl.run()

            abl_evals = []
            for ind in pareto_abl:
                sh, mdd, ret, trades, to = run_vectorized_simulation_fast(
                    open_dev, close_dev, high_dev, low_dev, p_const_dev, atr_dev, reg_vol_dev,
                    ind.genes, apply_penalty=False, volume=vol_dev
                )
                abl_evals.append({
                    "dev_sharpe": sh,
                    "dev_mdd": mdd,
                    "dev_return": ret,
                    "dev_trades": trades,
                    "genes": ind.genes,
                })

            valid_abl = [e for e in abl_evals if e["dev_trades"] >= 5]
            if len(valid_abl) > 0:
                best_abl = max(valid_abl, key=lambda x: x["dev_sharpe"])
                abl_feasible = True
                abl_genes = best_abl["genes"]
                abl_det = get_detailed_simulation_results(
                    test_df, p_const_test, abl_genes,
                    prefix_p_up=0.60, prefix_atr=prefix_atr, prefix_regime_vol=prefix_regime_vol
                )
                abl_metrics = compute_performance_metrics(
                    abl_det["equity"],
                    abl_det["positions"],
                    abl_det["total_trades"],
                    abl_det["win_rate"],
                    capital_exposures=abl_det["capital_exposures"],
                )
                abl_equity = abl_det["equity"]
                abl_positions = abl_det["positions"]
                abl_capital_exposures = abl_det["capital_exposures"]
                tl_abl = abl_det["trade_log"].to_dict(orient="records")
                abl_trade_log = [
                    {
                        "entry_date": pd.to_datetime(t["entry_date"]).strftime("%Y-%m-%d"),
                        "exit_date": pd.to_datetime(t["exit_date"]).strftime("%Y-%m-%d"),
                        "entry_price": float(t["entry_price"]),
                        "exit_price": float(t["exit_price"]),
                        "pnl": float(t["pnl"]),
                        "pnl_pct": float(t["pnl_pct"]),
                        "holding_bars": int(t["holding_bars"]),
                        "exit_reason": str(t["exit_reason"]),
                    }
                    for t in tl_abl
                ]
                abl_entries = [{"date": t["entry_date"], "price": t["entry_price"]} for t in abl_trade_log]
                abl_exits = [{"date": t["exit_date"], "price": t["exit_price"], "reason": t["exit_reason"], "pnl": t["pnl"]} for t in abl_trade_log]
            else:
                abl_feasible = False
                abl_genes = None
                abl_equity = np.full(len(test_df), INITIAL_CAPITAL, dtype=np.float64)
                abl_positions = np.zeros(len(test_df), dtype=np.float64)
                abl_capital_exposures = np.zeros(len(test_df), dtype=np.float64)
                abl_metrics = compute_performance_metrics(
                    abl_equity, abl_positions, 0, 0.0, capital_exposures=abl_capital_exposures
                )
                abl_trade_log = []
                abl_entries = []
                abl_exits = []

            fold_results["ga_runs"][str(seed)] = {
                "hybrid": {
                    "is_feasible": is_feasible,
                    "dev_selected_sharpe": float(best_dev["dev_sharpe"]),
                    "dev_trades": int(best_dev["dev_trades"]),
                    "dev_capital_exposure": float(dev_capital_exposure),
                    "dev_time_in_market": float(dev_time_in_market),
                    "genes": chosen_genes.tolist() if chosen_genes is not None else None,
                    "metrics": hybrid_metrics,
                    "equity": hybrid_equity.tolist(),
                    "positions": hybrid_positions.tolist(),
                    "capital_exposures": hybrid_capital_exposures.tolist(),
                    "trade_log": hybrid_trade_log,
                    "entries": hybrid_entries,
                    "exits": hybrid_exits,
                },
                "cost_sensitivity_2x": {
                    "metrics": cost_metrics,
                    "equity": cost_equity.tolist(),
                    "capital_exposures": cost_capital_exposures.tolist(),
                    "trade_log": cost_trade_log,
                    "entries": cost_entries,
                    "exits": cost_exits,
                },
                "exposure_matched_bh": {
                    "diagnostic_type": "hypothetical_frictionless_blend",
                    "dev_capital_exposure_used": float(dev_capital_exposure),
                    "metrics": exp_bh_res["metrics"],
                    "equity": exp_bh_res["equity"].tolist(),
                    "positions": exp_bh_res["positions"].tolist(),
                    "capital_exposures": exp_bh_res["capital_exposures"].tolist(),
                },
                "constant_prob_ablation": {
                    "is_feasible": abl_feasible,
                    "genes": abl_genes.tolist() if abl_genes is not None else None,
                    "metrics": abl_metrics,
                    "equity": abl_equity.tolist(),
                    "positions": abl_positions.tolist(),
                    "capital_exposures": abl_capital_exposures.tolist(),
                    "trade_log": abl_trade_log,
                    "entries": abl_entries,
                    "exits": abl_exits,
                },
            }

        return fold_results

    def run_all(self) -> Dict[str, Any]:
        campaign_start = time.time()
        print("=" * 70)
        print("STARTING FROZEN RETROSPECTIVE ROLLING NSE EXPERIMENT CAMPAIGN")
        print(f"Assets: {self.universe} | Years: {self.test_years} | GA Seeds: {self.ga_seeds}")
        print("=" * 70)

        all_results = {}
        for ticker in self.universe:
            ticker_start = time.time()
            print(f"\n>>> Processing {ticker}...")
            df_full = self.load_processed_asset(ticker)
            all_results[ticker] = {}

            for year in self.test_years:
                fold_start = time.time()
                print(f"  [Fold {year}] Running Train/Val/Dev/Test partitions...")
                fold_res = self.run_fold(ticker, df_full, year)
                all_results[ticker][str(year)] = fold_res
                elapsed = time.time() - fold_start
                print(f"  [Fold {year}] Completed in {elapsed:.1f}s.")

            elapsed_ticker = time.time() - ticker_start
            print(f">>> {ticker} completed in {elapsed_ticker:.1f}s.")

        campaign_elapsed = time.time() - campaign_start
        print("\n" + "=" * 70)
        print(f"CAMPAIGN EXECUTION COMPLETE in {campaign_elapsed:.1f}s.")
        print("Saving raw fold results...")

        # Save machine-readable raw fold results
        raw_results_file = self.results_dir / "campaign_raw_results.json"
        with open(raw_results_file, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"Raw results saved -> {raw_results_file}")

        return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run rolling NSE research campaign.")
    parser.add_argument("--test-years", nargs="+", type=int, default=[2020, 2021, 2022, 2023, 2024, 2025])
    parser.add_argument("--universe", nargs="+", type=str, default=["RELIANCE.NS", "TCS.NS", "INFY.NS"])
    parser.add_argument("--ga-seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument("--model-seed", type=int, default=42)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    inputs_path = project_root / "reports" / "experiments" / "inputs"
    outputs_path = project_root / "reports" / "experiments"
    protocol_file = project_root / "reports" / "experiments" / "protocol.json"

    runner = RollingNSEExperimentRunner(
        inputs_dir=inputs_path,
        output_dir=outputs_path,
        protocol_path=protocol_file,
        test_years=args.test_years,
        universe=args.universe,
        ga_seeds=args.ga_seeds,
        model_seed=args.model_seed,
    )
    runner.run_all()
