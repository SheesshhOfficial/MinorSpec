"""
Single-Split Chronological Experiment CLI Runner.

NOTE: This is a single chronological train/val/dev/test split with horizon purging.
It is NOT rolling walk-forward validation.
"""
import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path
import numpy as np
import pandas as pd

from src.config import (
    REPORTS_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    DEFAULT_COMMISSION_PCT,
    DEFAULT_SLIPPAGE_PCT,
    INITIAL_CAPITAL,
)
from src.pipeline import run_experiment_pipeline


def _compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def _get_package_versions() -> dict:
    import numpy, pandas, polars, pyarrow, scipy, sklearn, numba, yfinance, lightgbm, streamlit, pytest
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "polars": polars.__version__,
        "pyarrow": pyarrow.__version__,
        "scipy": scipy.__version__,
        "scikit-learn": sklearn.__version__,
        "numba": numba.__version__,
        "yfinance": yfinance.__version__,
        "lightgbm": lightgbm.__version__,
        "streamlit": streamlit.__version__,
        "pytest": pytest.__version__,
    }


def main():
    parser = argparse.ArgumentParser(description="Run single-split chronological research experiment.")
    parser.add_argument("--ticker", type=str, default="SPY", help="Asset ticker symbol (e.g. SPY, RELIANCE.NS)")
    parser.add_argument("--pop-size", type=int, default=40, help="Population size for NSGA-II")
    parser.add_argument("--generations", type=int, default=15, help="Generations for NSGA-II")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--save-baseline", action="store_true", help="Save machine-readable results to reports/baseline/")
    parser.add_argument("--force-refresh", action="store_true", help="Force re-download of raw market data")
    args = parser.parse_args()

    clean_ticker = args.ticker.upper().replace("^", "")
    raw_file = RAW_DATA_DIR / f"{clean_ticker}.parquet"

    print("=" * 65)
    print(f"RUNNING SINGLE-SPLIT CHRONOLOGICAL EXPERIMENT FOR {args.ticker}")
    print(f"Settings: Seed={args.seed}, PopSize={args.pop_size}, Gens={args.generations}")
    print("=" * 65)

    results = run_experiment_pipeline(
        ticker=args.ticker,
        pop_size=args.pop_size,
        num_generations=args.generations,
        seed=args.seed,
        force_refresh=args.force_refresh,
    )

    splits = results["splits"]
    train_df = splits["train"]
    val_df = splits["val"]
    dev_df = splits["dev"]
    test_df = splits["test"]
    indices = splits["indices"]

    print("\n--- Chronological Partitions with Horizon Purging ---")
    print(f"Train      : {train_df['Date'].min().strftime('%Y-%m-%d')} to {train_df['Date'].max().strftime('%Y-%m-%d')} ({len(train_df)} bars)")
    print(f"  [Purged {indices['horizon_bars']} bars]")
    print(f"Val        : {val_df['Date'].min().strftime('%Y-%m-%d')} to {val_df['Date'].max().strftime('%Y-%m-%d')} ({len(val_df)} bars)")
    print(f"  [Purged {indices['horizon_bars']} bars]")
    print(f"Dev (GA)   : {dev_df['Date'].min().strftime('%Y-%m-%d')} to {dev_df['Date'].max().strftime('%Y-%m-%d')} ({len(dev_df)} bars)")
    print(f"  [Purged {indices['horizon_bars']} bars]")
    print(f"Test (OOS) : {test_df['Date'].min().strftime('%Y-%m-%d')} to {test_df['Date'].max().strftime('%Y-%m-%d')} ({len(test_df)} bars)")

    print("\n--- Strategy Selection (Frozen on Development Partition) ---")
    strat_id = results["frozen_strategy_id"]
    dev_row = results["dev_summary_df"][results["dev_summary_df"]["id"] == strat_id].iloc[0]
    print(f"Selected Frozen Strategy ID: #{strat_id}")
    print(f"Dev Sharpe: {dev_row['dev_sharpe']:.2f} | Dev MaxDD: {dev_row['dev_mdd']*100:.2f}% | Dev Return: {dev_row['dev_ret']*100:.2f}% | Dev Trades: {dev_row['dev_trades']}")
    print(f"Genes (Full Precision): {[float(g) for g in results['frozen_genes']]}")

    print("\n--- Out-of-Sample Test Evaluation (Frozen Strategy) ---")
    detailed = results["detailed_test_result"]
    print(f"Strategy Test Return   : {detailed['total_return']*100:.2f}%")
    print(f"Strategy Test Sharpe   : {detailed['sharpe_ratio']:.2f}")
    print(f"Strategy Test Max DD   : {detailed['max_drawdown']*100:.2f}%")
    print(f"Strategy Test Trades   : {detailed['total_trades']} (Win Rate: {detailed['win_rate']*100:.1f}%)")
    print(f"Benchmark Test Return  : {detailed['benchmark_return']*100:.2f}%")
    print(f"Benchmark Test Max DD  : {detailed['benchmark_max_drawdown']*100:.2f}%")

    if args.save_baseline:
        baseline_dir = REPORTS_DIR / "baseline"
        baseline_dir.mkdir(parents=True, exist_ok=True)
        out_file = baseline_dir / f"baseline_{clean_ticker}_seed{args.seed}.json"

        # Compute dataset hashes
        raw_sha256 = _compute_sha256(raw_file) if raw_file.exists() else "not_found"
        proc_file = PROCESSED_DATA_DIR / f"{clean_ticker}_features.parquet"
        proc_sha256 = _compute_sha256(proc_file) if proc_file.exists() else "not_found"

        # Prepare serializable trade log
        trades_df = detailed["trade_log"]
        serializable_trades = []
        if not trades_df.empty:
            for _, tr in trades_df.iterrows():
                serializable_trades.append({
                    "entry_date": str(tr["entry_date"])[:10],
                    "exit_date": str(tr["exit_date"])[:10],
                    "entry_price": float(tr["entry_price"]),
                    "exit_price": float(tr["exit_price"]),
                    "pnl": float(tr["pnl"]),
                    "pnl_pct": float(tr["pnl_pct"]),
                    "holding_bars": int(tr["holding_bars"]),
                    "exit_reason": str(tr["exit_reason"]),
                })

        # Prepare serializable daily equity series
        equity_series = [
            {"date": str(d)[:10], "equity": float(eq), "drawdown": float(dd)}
            for d, eq, dd in zip(detailed["dates"], detailed["equity"], detailed["drawdowns"])
        ]

        artifact = {
            "metadata": {
                "ticker": args.ticker,
                "command": f"python -m src.walk_forward --ticker {args.ticker} --pop-size {args.pop_size} --generations {args.generations} --seed {args.seed} --save-baseline",
                "seed": args.seed,
                "provider": "yfinance",
                "adjustment": "auto_adjust=True (splits & dividends adjusted)",
                "costs": {
                    "commission_pct": DEFAULT_COMMISSION_PCT,
                    "slippage_pct": DEFAULT_SLIPPAGE_PCT,
                    "initial_capital": INITIAL_CAPITAL,
                },
                "dataset_provenance": {
                    "raw_parquet_path": str(raw_file),
                    "raw_parquet_sha256": raw_sha256,
                    "processed_parquet_path": str(proc_file),
                    "processed_parquet_sha256": proc_sha256,
                },
                "environment": _get_package_versions(),
            },
            "parameters": {
                "pop_size": args.pop_size,
                "generations": args.generations,
                "features_count": len(results["feature_cols"]),
                "feature_names": results["feature_cols"],
            },
            "splits": {
                "train_bars": len(train_df),
                "val_bars": len(val_df),
                "dev_bars": len(dev_df),
                "test_bars": len(test_df),
                "horizon_bars": indices["horizon_bars"],
                "train_dates": [train_df["Date"].min().strftime("%Y-%m-%d"), train_df["Date"].max().strftime("%Y-%m-%d")],
                "val_dates": [val_df["Date"].min().strftime("%Y-%m-%d"), val_df["Date"].max().strftime("%Y-%m-%d")],
                "dev_dates": [dev_df["Date"].min().strftime("%Y-%m-%d"), dev_df["Date"].max().strftime("%Y-%m-%d")],
                "test_dates": [test_df["Date"].min().strftime("%Y-%m-%d"), test_df["Date"].max().strftime("%Y-%m-%d")],
            },
            "selected_strategy": {
                "id": strat_id,
                "genes": [float(g) for g in results["frozen_genes"]],
                "gene_names": [
                    "p_entry_threshold",
                    "p_exit_threshold",
                    "stop_loss_atr_mult",
                    "take_profit_atr_mult",
                    "trailing_stop_pct",
                    "regime_vol_discount",
                    "max_holding_period",
                ],
                "dev_metrics": {
                    "sharpe": float(dev_row["dev_sharpe"]),
                    "max_drawdown": float(dev_row["dev_mdd"]),
                    "return": float(dev_row["dev_ret"]),
                    "trades": int(dev_row["dev_trades"]),
                    "turnover": float(dev_row["dev_turnover"]),
                },
                "test_metrics": {
                    "return": float(detailed["total_return"]),
                    "sharpe": float(detailed["sharpe_ratio"]),
                    "max_drawdown": float(detailed["max_drawdown"]),
                    "trades": int(detailed["total_trades"]),
                    "win_rate": float(detailed["win_rate"]),
                    "turnover": float(detailed["turnover"]),
                },
            },
            "benchmark_test_metrics": {
                "return": float(detailed["benchmark_return"]),
                "max_drawdown": float(detailed["benchmark_max_drawdown"]),
            },
            "trades": serializable_trades,
            "equity_curve": equity_series,
        }

        with open(out_file, "w") as f:
            json.dump(artifact, f, indent=2)
        print(f"\n[Saved Baseline Artifact with SHA-256 and Full Provenance] -> {out_file}")

    return results


if __name__ == "__main__":
    main()
