"""
Aggregate Analysis and Visualization for Rolling NSE Retrospective Experiments.

Computes:
1. Per-fold metrics comparison tables across assets, seeds, and benchmarks.
2. Stitched equity curves carrying capital forward across 2020-2025.
3. Seed variability summary (median and range across GA seeds 42, 43, 44).
4. Cost sensitivity analysis (doubled friction without reoptimization).
5. Diagnostic exposure-matched Buy & Hold comparisons.
6. Publication-grade static figures:
   - Stitched equity curves vs Buy & Hold.
   - Underwater drawdown profiles.
   - Per-fold risk-return (Sharpe vs Annual Return) scatter.
   - Seed sensitivity / variability boxplots.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from src.config import INITIAL_CAPITAL
from src.rolling_runner import stitch_equity_curves


def load_campaign_results(results_file: Path) -> Dict[str, Any]:
    with open(results_file, "r") as f:
        return json.load(f)


def build_fold_summary_dataframe(raw_results: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for ticker, years_dict in raw_results.items():
        for year, fold_data in years_dict.items():
            mod = fold_data["model_eval"]
            b_bh = fold_data["baselines"]["buy_and_hold"]["metrics"]
            b_cash = fold_data["baselines"]["cash"]["metrics"]
            b_sma = fold_data["baselines"]["sma_50_200"]["metrics"]
            b_fix = fold_data["baselines"]["fixed_gene_hybrid"]["metrics"]

            # Add fixed baselines once per asset/year
            rows.append({
                "ticker": ticker,
                "year": int(year),
                "strategy": "Buy & Hold",
                "ga_seed": "N/A",
                "feasible": True,
                "total_return": b_bh["total_return"],
                "cagr": b_bh["cagr"],
                "sharpe_ratio": b_bh["sharpe_ratio"],
                "max_drawdown": b_bh["max_drawdown"],
                "annualized_volatility": b_bh["annualized_volatility"],
                "total_trades": b_bh["total_trades"],
                "win_rate": b_bh["win_rate"],
                "exposure_fraction": b_bh["exposure_fraction"],
                "capital_exposure": b_bh.get("capital_exposure", b_bh["exposure_fraction"]),
                "terminal_equity": b_bh["terminal_equity"],
                "test_auc": mod["test_auc"],
                "test_accuracy": mod["test_accuracy"],
                "baseline_accuracy": mod["baseline_accuracy"],
                "test_brier": mod["test_brier"],
                "baseline_brier": mod["baseline_brier"],
                "scored_test_samples": mod.get("scored_test_samples", mod["test_bars"]),
                "masked_test_samples": mod.get("masked_test_samples", 0),
            })
            rows.append({
                "ticker": ticker,
                "year": int(year),
                "strategy": "Cash (0%)",
                "ga_seed": "N/A",
                "feasible": True,
                "total_return": b_cash["total_return"],
                "cagr": b_cash["cagr"],
                "sharpe_ratio": b_cash["sharpe_ratio"],
                "max_drawdown": b_cash["max_drawdown"],
                "annualized_volatility": b_cash["annualized_volatility"],
                "total_trades": b_cash["total_trades"],
                "win_rate": b_cash["win_rate"],
                "exposure_fraction": b_cash["exposure_fraction"],
                "capital_exposure": b_cash.get("capital_exposure", 0.0),
                "terminal_equity": b_cash["terminal_equity"],
                "test_auc": mod["test_auc"],
                "test_accuracy": mod["test_accuracy"],
                "baseline_accuracy": mod["baseline_accuracy"],
                "test_brier": mod["test_brier"],
                "baseline_brier": mod["baseline_brier"],
                "scored_test_samples": mod.get("scored_test_samples", mod["test_bars"]),
                "masked_test_samples": mod.get("masked_test_samples", 0),
            })
            rows.append({
                "ticker": ticker,
                "year": int(year),
                "strategy": "SMA 50/200",
                "ga_seed": "N/A",
                "feasible": True,
                "total_return": b_sma["total_return"],
                "cagr": b_sma["cagr"],
                "sharpe_ratio": b_sma["sharpe_ratio"],
                "max_drawdown": b_sma["max_drawdown"],
                "annualized_volatility": b_sma["annualized_volatility"],
                "total_trades": b_sma["total_trades"],
                "win_rate": b_sma["win_rate"],
                "exposure_fraction": b_sma["exposure_fraction"],
                "capital_exposure": b_sma.get("capital_exposure", b_sma["exposure_fraction"]),
                "terminal_equity": b_sma["terminal_equity"],
                "test_auc": mod["test_auc"],
                "test_accuracy": mod["test_accuracy"],
                "baseline_accuracy": mod["baseline_accuracy"],
                "test_brier": mod["test_brier"],
                "baseline_brier": mod["baseline_brier"],
                "scored_test_samples": mod.get("scored_test_samples", mod["test_bars"]),
                "masked_test_samples": mod.get("masked_test_samples", 0),
            })
            rows.append({
                "ticker": ticker,
                "year": int(year),
                "strategy": "Fixed-Gene Hybrid",
                "ga_seed": "N/A",
                "feasible": True,
                "total_return": b_fix["total_return"],
                "cagr": b_fix["cagr"],
                "sharpe_ratio": b_fix["sharpe_ratio"],
                "max_drawdown": b_fix["max_drawdown"],
                "annualized_volatility": b_fix["annualized_volatility"],
                "total_trades": b_fix["total_trades"],
                "win_rate": b_fix["win_rate"],
                "exposure_fraction": b_fix["exposure_fraction"],
                "capital_exposure": b_fix.get("capital_exposure", b_fix["exposure_fraction"]),
                "terminal_equity": b_fix["terminal_equity"],
                "test_auc": mod["test_auc"],
                "test_accuracy": mod["test_accuracy"],
                "baseline_accuracy": mod["baseline_accuracy"],
                "test_brier": mod["test_brier"],
                "baseline_brier": mod["baseline_brier"],
                "scored_test_samples": mod.get("scored_test_samples", mod["test_bars"]),
                "masked_test_samples": mod.get("masked_test_samples", 0),
            })

            # Add GA seed runs
            for seed_str, ga_data in fold_data["ga_runs"].items():
                hyb = ga_data["hybrid"]
                m_hyb = hyb["metrics"]
                rows.append({
                    "ticker": ticker,
                    "year": int(year),
                    "strategy": "Full Hybrid (LightGBM+NSGA-II)",
                    "ga_seed": int(seed_str),
                    "feasible": hyb["is_feasible"],
                    "total_return": m_hyb["total_return"],
                    "cagr": m_hyb["cagr"],
                    "sharpe_ratio": m_hyb["sharpe_ratio"],
                    "max_drawdown": m_hyb["max_drawdown"],
                    "annualized_volatility": m_hyb["annualized_volatility"],
                    "total_trades": m_hyb["total_trades"],
                    "win_rate": m_hyb["win_rate"],
                    "exposure_fraction": m_hyb["exposure_fraction"],
                    "capital_exposure": m_hyb.get("capital_exposure", hyb.get("dev_capital_exposure", 0.0)),
                    "terminal_equity": m_hyb["terminal_equity"],
                    "test_auc": mod["test_auc"],
                    "test_accuracy": mod["test_accuracy"],
                    "baseline_accuracy": mod["baseline_accuracy"],
                    "test_brier": mod["test_brier"],
                    "baseline_brier": mod["baseline_brier"],
                    "scored_test_samples": mod.get("scored_test_samples", mod["test_bars"]),
                    "masked_test_samples": mod.get("masked_test_samples", 0),
                })

                # Cost sensitivity (2x fees)
                c_cost = ga_data["cost_sensitivity_2x"]["metrics"]
                rows.append({
                    "ticker": ticker,
                    "year": int(year),
                    "strategy": "Hybrid (2x Friction Sensitivity)",
                    "ga_seed": int(seed_str),
                    "feasible": hyb["is_feasible"],
                    "total_return": c_cost["total_return"],
                    "cagr": c_cost["cagr"],
                    "sharpe_ratio": c_cost["sharpe_ratio"],
                    "max_drawdown": c_cost["max_drawdown"],
                    "annualized_volatility": c_cost["annualized_volatility"],
                    "total_trades": c_cost["total_trades"],
                    "win_rate": c_cost["win_rate"],
                    "exposure_fraction": c_cost["exposure_fraction"],
                    "capital_exposure": c_cost.get("capital_exposure", hyb.get("dev_capital_exposure", 0.0)),
                    "terminal_equity": c_cost["terminal_equity"],
                    "test_auc": mod["test_auc"],
                    "test_accuracy": mod["test_accuracy"],
                    "baseline_accuracy": mod["baseline_accuracy"],
                    "test_brier": mod["test_brier"],
                    "baseline_brier": mod["baseline_brier"],
                    "scored_test_samples": mod.get("scored_test_samples", mod["test_bars"]),
                    "masked_test_samples": mod.get("masked_test_samples", 0),
                })

                # Exposure-matched Buy & Hold
                exp_bh = ga_data["exposure_matched_bh"]["metrics"]
                rows.append({
                    "ticker": ticker,
                    "year": int(year),
                    "strategy": "Exposure-Matched B&H Diagnostic",
                    "ga_seed": int(seed_str),
                    "feasible": True,
                    "total_return": exp_bh["total_return"],
                    "cagr": exp_bh["cagr"],
                    "sharpe_ratio": exp_bh["sharpe_ratio"],
                    "max_drawdown": exp_bh["max_drawdown"],
                    "annualized_volatility": exp_bh["annualized_volatility"],
                    "total_trades": exp_bh["total_trades"],
                    "win_rate": exp_bh["win_rate"],
                    "exposure_fraction": exp_bh["exposure_fraction"],
                    "capital_exposure": exp_bh.get("capital_exposure", exp_bh["exposure_fraction"]),
                    "terminal_equity": exp_bh["terminal_equity"],
                    "test_auc": mod["test_auc"],
                    "test_accuracy": mod["test_accuracy"],
                    "baseline_accuracy": mod["baseline_accuracy"],
                    "test_brier": mod["test_brier"],
                    "baseline_brier": mod["baseline_brier"],
                    "scored_test_samples": mod.get("scored_test_samples", mod["test_bars"]),
                    "masked_test_samples": mod.get("masked_test_samples", 0),
                })

                # Constant Prob Ablation (No ML)
                abl = ga_data["constant_prob_ablation"]
                m_abl = abl["metrics"]
                rows.append({
                    "ticker": ticker,
                    "year": int(year),
                    "strategy": "Evolved No-ML Ablation (p=0.60)",
                    "ga_seed": int(seed_str),
                    "feasible": abl["is_feasible"],
                    "total_return": m_abl["total_return"],
                    "cagr": m_abl["cagr"],
                    "sharpe_ratio": m_abl["sharpe_ratio"],
                    "max_drawdown": m_abl["max_drawdown"],
                    "annualized_volatility": m_abl["annualized_volatility"],
                    "total_trades": m_abl["total_trades"],
                    "win_rate": m_abl["win_rate"],
                    "exposure_fraction": m_abl["exposure_fraction"],
                    "capital_exposure": m_abl.get("capital_exposure", m_abl["exposure_fraction"]),
                    "terminal_equity": m_abl["terminal_equity"],
                    "test_auc": mod["test_auc"],
                    "test_accuracy": mod["test_accuracy"],
                    "baseline_accuracy": mod["baseline_accuracy"],
                    "test_brier": mod["test_brier"],
                    "baseline_brier": mod["baseline_brier"],
                    "scored_test_samples": mod.get("scored_test_samples", mod["test_bars"]),
                    "masked_test_samples": mod.get("masked_test_samples", 0),
                })

    return pd.DataFrame(rows)


def build_stitched_equity_curves(raw_results: Dict[str, Any]) -> Dict[str, Dict[str, pd.DataFrame]]:
    stitched_curves = {}
    years = [2020, 2021, 2022, 2023, 2024, 2025]

    for ticker, years_dict in raw_results.items():
        stitched_curves[ticker] = {}

        # Collect dates
        all_dates = []
        for y in years:
            all_dates.extend(years_dict[str(y)]["test_dates"])

        # Baselines
        for b_name in ["buy_and_hold", "cash", "sma_50_200", "fixed_gene_hybrid"]:
            daily_eqs = [years_dict[str(y)]["baselines"][b_name]["equity"] for y in years]
            stitched = stitch_equity_curves(daily_eqs, initial_capital=INITIAL_CAPITAL)
            stitched_curves[ticker][b_name] = pd.DataFrame({"Date": all_dates, "equity": stitched})

        # GA runs
        for seed in [42, 43, 44]:
            # Hybrid
            daily_eqs_hyb = [years_dict[str(y)]["ga_runs"][str(seed)]["hybrid"]["equity"] for y in years]
            stitched_hyb = stitch_equity_curves(daily_eqs_hyb, initial_capital=INITIAL_CAPITAL)
            stitched_curves[ticker][f"hybrid_seed_{seed}"] = pd.DataFrame({"Date": all_dates, "equity": stitched_hyb})

            # Cost sensitivity
            daily_eqs_cost = [years_dict[str(y)]["ga_runs"][str(seed)]["cost_sensitivity_2x"]["equity"] for y in years]
            stitched_cost = stitch_equity_curves(daily_eqs_cost, initial_capital=INITIAL_CAPITAL)
            stitched_curves[ticker][f"hybrid_cost2x_seed_{seed}"] = pd.DataFrame({"Date": all_dates, "equity": stitched_cost})

            # Exposure matched BH
            daily_eqs_exp = [years_dict[str(y)]["ga_runs"][str(seed)]["exposure_matched_bh"]["equity"] for y in years]
            stitched_exp = stitch_equity_curves(daily_eqs_exp, initial_capital=INITIAL_CAPITAL)
            stitched_curves[ticker][f"exp_bh_seed_{seed}"] = pd.DataFrame({"Date": all_dates, "equity": stitched_exp})

            # Ablation
            daily_eqs_abl = [years_dict[str(y)]["ga_runs"][str(seed)]["constant_prob_ablation"]["equity"] for y in years]
            stitched_abl = stitch_equity_curves(daily_eqs_abl, initial_capital=INITIAL_CAPITAL)
            stitched_curves[ticker][f"ablation_seed_{seed}"] = pd.DataFrame({"Date": all_dates, "equity": stitched_abl})

    return stitched_curves


def compute_stitched_aggregate_metrics(stitched_curves: Dict[str, Dict[str, pd.DataFrame]]) -> pd.DataFrame:
    rows = []
    for ticker, curves_dict in stitched_curves.items():
        for strat_key, df in curves_dict.items():
            eq = df["equity"].to_numpy(dtype=np.float64)
            n = len(eq)
            tot_ret = (eq[-1] / INITIAL_CAPITAL) - 1.0
            cagr = (eq[-1] / INITIAL_CAPITAL) ** (252.0 / n) - 1.0 if eq[-1] > 0 else -1.0
            
            # Max Drawdown includes pre-trade initial capital peak
            running_max = np.maximum.accumulate(np.insert(eq, 0, INITIAL_CAPITAL))
            dd = (running_max[1:] - eq) / (running_max[1:] + 1e-8)
            mdd = float(np.max(dd))

            # Daily returns include first-day return from pre-trade initial capital
            daily_r = np.empty(n, dtype=np.float64)
            daily_r[0] = (eq[0] - INITIAL_CAPITAL) / (INITIAL_CAPITAL + 1e-8)
            for j in range(1, n):
                daily_r[j] = (eq[j] - eq[j - 1]) / (eq[j - 1] + 1e-8)
            mean_r = float(np.mean(daily_r))
            std_r = float(np.std(daily_r))
            sharpe = (mean_r / std_r) * np.sqrt(252.0) if std_r >= 1e-8 else 0.0
            vol = std_r * np.sqrt(252.0)

            rows.append({
                "ticker": ticker,
                "strategy_key": strat_key,
                "stitched_bars": n,
                "total_return": tot_ret,
                "cagr": cagr,
                "sharpe_ratio": sharpe,
                "max_drawdown": mdd,
                "annualized_volatility": vol,
                "terminal_equity": eq[-1],
            })
    return pd.DataFrame(rows)


def generate_static_figures(
    stitched_curves: Dict[str, Dict[str, pd.DataFrame]],
    fold_df: pd.DataFrame,
    figures_dir: Path,
):
    figures_dir.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # 1. Stitched Equity Curves Comparison
    fig, axes = plt.subplots(3, 1, figsize=(12, 14), sharex=True)
    for idx, ticker in enumerate(["RELIANCE.NS", "TCS.NS", "INFY.NS"]):
        ax = axes[idx]
        dates = pd.to_datetime(stitched_curves[ticker]["buy_and_hold"]["Date"])

        # Buy & Hold
        bh_eq = stitched_curves[ticker]["buy_and_hold"]["equity"]
        ax.plot(dates, bh_eq, label="Buy & Hold (Full Exposure)", color="#1f77b4", linewidth=2.0)

        # SMA 50/200
        sma_eq = stitched_curves[ticker]["sma_50_200"]["equity"]
        ax.plot(dates, sma_eq, label="SMA 50/200 Trend", color="#ff7f0e", linestyle="--", linewidth=1.8)

        # Hybrid Seeds (42, 43, 44)
        for seed, color, ls in [(42, "#2ca02c", "-"), (43, "#27ae60", ":"), (44, "#2ecc71", "-.")]:
            hyb_eq = stitched_curves[ticker][f"hybrid_seed_{seed}"]["equity"]
            ax.plot(dates, hyb_eq, label=f"Full Hybrid (Seed {seed})", color=color, linestyle=ls, linewidth=1.5)

        # Ablation Seed 42
        abl_eq = stitched_curves[ticker]["ablation_seed_42"]["equity"]
        ax.plot(dates, abl_eq, label="Ablation (No ML, Seed 42)", color="#9467bd", linestyle=":", linewidth=1.4)

        ax.set_title(f"{ticker}: Stitched 6-Year Out-of-Sample Equity Curves (2020–2025)", fontsize=13, fontweight="bold")
        ax.set_ylabel("Portfolio Value (₹, Initial: 100,000)", fontsize=10)
        ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
        ax.legend(loc="upper left", framealpha=0.9, fontsize=9)
        ax.grid(True, linestyle="--", alpha=0.6)

    axes[-1].set_xlabel("Date", fontsize=11)
    fig.tight_layout()
    equity_fig_path = figures_dir / "stitched_equity_curves.png"
    fig.savefig(equity_fig_path, dpi=300)
    plt.close(fig)
    print(f"Saved figure -> {equity_fig_path}")

    # 2. Underwater Drawdown Profiles
    fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
    for idx, ticker in enumerate(["RELIANCE.NS", "TCS.NS", "INFY.NS"]):
        ax = axes[idx]
        dates = pd.to_datetime(stitched_curves[ticker]["buy_and_hold"]["Date"])

        # Buy & Hold Drawdown
        bh_eq = stitched_curves[ticker]["buy_and_hold"]["equity"].to_numpy()
        bh_peak = np.maximum.accumulate(bh_eq)
        bh_dd = (bh_eq - bh_peak) / (bh_peak + 1e-8)
        ax.plot(dates, bh_dd * 100.0, label="Buy & Hold Drawdown", color="#d62728", alpha=0.7, linewidth=1.5)
        ax.fill_between(dates, bh_dd * 100.0, 0, color="#d62728", alpha=0.15)

        # Hybrid Seed 42 Drawdown
        hyb_eq = stitched_curves[ticker]["hybrid_seed_42"]["equity"].to_numpy()
        hyb_peak = np.maximum.accumulate(hyb_eq)
        hyb_dd = (hyb_eq - hyb_peak) / (hyb_peak + 1e-8)
        ax.plot(dates, hyb_dd * 100.0, label="Full Hybrid (Seed 42)", color="#2ca02c", linewidth=1.8)
        ax.fill_between(dates, hyb_dd * 100.0, 0, color="#2ca02c", alpha=0.15)

        # SMA 50/200 Drawdown
        sma_eq = stitched_curves[ticker]["sma_50_200"]["equity"].to_numpy()
        sma_peak = np.maximum.accumulate(sma_eq)
        sma_dd = (sma_eq - sma_peak) / (sma_peak + 1e-8)
        ax.plot(dates, sma_dd * 100.0, label="SMA 50/200", color="#ff7f0e", linestyle="--", linewidth=1.4)

        ax.set_title(f"{ticker}: Underwater Drawdown Profile (2020–2025)", fontsize=13, fontweight="bold")
        ax.set_ylabel("Drawdown (%)", fontsize=10)
        ax.set_ylim(-55, 5)
        ax.legend(loc="lower left", framealpha=0.9, fontsize=9)
        ax.grid(True, linestyle="--", alpha=0.6)

    axes[-1].set_xlabel("Date", fontsize=11)
    fig.tight_layout()
    dd_fig_path = figures_dir / "underwater_drawdowns.png"
    fig.savefig(dd_fig_path, dpi=300)
    plt.close(fig)
    print(f"Saved figure -> {dd_fig_path}")

    # 3. Per-Fold Sharpe Ratio & Return Scatter (Risk-Return Tradeoff)
    fig, ax = plt.subplots(figsize=(10, 7))
    styles = {
        "Buy & Hold": ("#1f77b4", "o", "Buy & Hold"),
        "SMA 50/200": ("#ff7f0e", "s", "SMA 50/200"),
        "Full Hybrid (LightGBM+NSGA-II)": ("#2ca02c", "^", "Full Hybrid"),
        "Evolved No-ML Ablation (p=0.60)": ("#9467bd", "v", "No-ML Ablation"),
        "Fixed-Gene Hybrid": ("#8c564b", "x", "Fixed-Gene Hybrid"),
    }
    for strat, (col, marker, label) in styles.items():
        sub = fold_df[fold_df["strategy"] == strat]
        ax.scatter(
            sub["annualized_volatility"] * 100.0,
            sub["total_return"] * 100.0,
            color=col,
            marker=marker,
            s=80,
            alpha=0.85,
            edgecolors="black" if marker != "x" else None,
            label=label,
        )

    ax.axhline(0, color="gray", linestyle="--", alpha=0.5)
    ax.set_title("Per-Fold Risk vs Return Across All NSE Assets & Test Years (2020–2025)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Annualized Volatility (%)", fontsize=11)
    ax.set_ylabel("Annual Total Return (%)", fontsize=11)
    ax.legend(loc="upper left", framealpha=0.9, fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.6)
    fig.tight_layout()
    scatter_fig_path = figures_dir / "risk_return_scatter.png"
    fig.savefig(scatter_fig_path, dpi=300)
    plt.close(fig)
    print(f"Saved figure -> {scatter_fig_path}")

    # 4. Seed Sensitivity Boxplots (Comparing seeds 42, 43, 44 on Hybrid metrics)
    hybrid_folds = fold_df[fold_df["strategy"] == "Full Hybrid (LightGBM+NSGA-II)"].copy()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Sharpe by Seed
    seeds = [42, 43, 44]
    sharpe_data = [hybrid_folds[hybrid_folds["ga_seed"] == s]["sharpe_ratio"].values for s in seeds]
    axes[0].boxplot(sharpe_data, labels=[f"Seed {s}" for s in seeds], patch_artist=True,
                    boxprops=dict(facecolor="#a1d99b", color="#2ca02c"),
                    medianprops=dict(color="black", linewidth=1.5))
    axes[0].set_title("Hybrid Annual Sharpe Distribution by GA Seed", fontsize=12, fontweight="bold")
    axes[0].set_ylabel("Sharpe Ratio", fontsize=10)
    axes[0].grid(True, linestyle="--", alpha=0.6)

    # Return by Seed
    ret_data = [hybrid_folds[hybrid_folds["ga_seed"] == s]["total_return"].values * 100.0 for s in seeds]
    axes[1].boxplot(ret_data, labels=[f"Seed {s}" for s in seeds], patch_artist=True,
                    boxprops=dict(facecolor="#bcbddc", color="#756bb1"),
                    medianprops=dict(color="black", linewidth=1.5))
    axes[1].set_title("Hybrid Annual Return Distribution by GA Seed", fontsize=12, fontweight="bold")
    axes[1].set_ylabel("Total Return (%)", fontsize=10)
    axes[1].grid(True, linestyle="--", alpha=0.6)

    fig.tight_layout()
    seed_fig_path = figures_dir / "seed_variability_boxplots.png"
    fig.savefig(seed_fig_path, dpi=300)
    plt.close(fig)
    print(f"Saved figure -> {seed_fig_path}")


def main():
    project_root = Path(__file__).resolve().parent.parent
    raw_results_file = project_root / "reports" / "experiments" / "results" / "campaign_raw_results.json"
    results_dir = project_root / "reports" / "experiments" / "results"
    figures_dir = project_root / "reports" / "experiments" / "figures"

    print("Loading raw campaign results...")
    raw_results = load_campaign_results(raw_results_file)

    print("Building fold summary dataframe...")
    fold_df = build_fold_summary_dataframe(raw_results)
    fold_csv_path = results_dir / "fold_summary_metrics.csv"
    fold_df.to_csv(fold_csv_path, index=False)
    print(f"Saved fold metrics table -> {fold_csv_path}")

    print("Building stitched equity curves...")
    stitched_curves = build_stitched_equity_curves(raw_results)

    print("Computing stitched aggregate metrics...")
    stitched_metrics_df = compute_stitched_aggregate_metrics(stitched_curves)
    stitched_csv_path = results_dir / "stitched_aggregate_metrics.csv"
    stitched_metrics_df.to_csv(stitched_csv_path, index=False)
    print(f"Saved stitched aggregate metrics -> {stitched_csv_path}")

    print("Generating publication static figures...")
    generate_static_figures(stitched_curves, fold_df, figures_dir)

    print("Analysis and plot generation complete.")


if __name__ == "__main__":
    main()
