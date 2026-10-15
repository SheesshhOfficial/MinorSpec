"""
Automated Campaign-Wide Source Comparison and Reproducibility Verification Script.

Task P002-R3 / P003 Acceptance Gate:
1. Prohibits all network downloader calls (yfinance.download, yfinance.Ticker).
2. Re-executes run_fold for ALL 18 asset/year folds and ALL 3 GA seeds from snapshot parquets.
3. Compares fresh in-memory results against saved reports/experiments/results/campaign_raw_results.json.
4. Evaluates 306 distinct assertions across all 54 fold runs:
   - Feasibility agreement across all runs.
   - Model evaluation metrics (test_auc, test_accuracy, test_brier, scored_samples, masked_samples).
   - Fixed baselines (buy_and_hold, cash, sma_50_200, fixed_gene_hybrid) equity curves and total returns.
   - Selected genes match saved within absolute tolerance 1e-12.
   - Equity paths match saved within absolute tolerance 1e-7 across all variants (hybrid, cost2x, exposure-matched B&H, ablation).
   - Summary metrics (total_return, feasibility) match.
5. Exits with code 0 on complete pass, or non-zero with detailed mismatch logs on failure.
"""

import sys
import json
from pathlib import Path
import numpy as np
import yfinance as yf

# Prohibit downloader calls
def forbidden_call(*args, **kwargs):
    raise RuntimeError("Downloader call attempted! Campaign verification must run strictly offline from snapshots.")

yf.download = forbidden_call
yf.Ticker = forbidden_call

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUTS_DIR = PROJECT_ROOT / "reports" / "experiments" / "inputs"
RESULTS_DIR = PROJECT_ROOT / "reports" / "experiments" / "results"
PROTOCOL_FILE = PROJECT_ROOT / "reports" / "experiments" / "protocol.json"
SAVED_RAW_FILE = RESULTS_DIR / "campaign_raw_results.json"

sys.path.insert(0, str(PROJECT_ROOT))

from src.rolling_runner import RollingNSEExperimentRunner

def run_campaign_reproducibility_audit():
    print("=" * 80)
    print("STARTING CAMPAIGN-WIDE CURRENT-SOURCE REPRODUCIBILITY AUDIT")
    print(f"Inputs: {INPUTS_DIR}")
    print(f"Artifact under test: {SAVED_RAW_FILE}")
    print("=" * 80)

    if not SAVED_RAW_FILE.exists():
        print(f"ERROR: Saved raw results artifact not found at {SAVED_RAW_FILE}")
        sys.exit(1)

    with open(SAVED_RAW_FILE, "r") as f:
        saved_all = json.load(f)

    runner = RollingNSEExperimentRunner(
        inputs_dir=INPUTS_DIR,
        output_dir=PROJECT_ROOT / "reports" / "experiments",
        protocol_path=PROTOCOL_FILE,
        test_years=[2020, 2021, 2022, 2023, 2024, 2025],
        universe=["RELIANCE.NS", "TCS.NS", "INFY.NS"],
        ga_seeds=[42, 43, 44],
        model_seed=42,
    )

    mismatches = []
    total_checks = 0

    for ticker in runner.universe:
        print(f"\nAuditing asset: {ticker}...")
        df_full = runner.load_processed_asset(ticker)

        for year in runner.test_years:
            y_str = str(year)
            fresh_fold = runner.run_fold(ticker, df_full, year)
            saved_fold = saved_all[ticker][y_str]

            # 1. Model Eval & Label Masking
            total_checks += 1
            for k in ["test_auc", "test_accuracy", "test_brier", "scored_test_samples", "masked_test_samples"]:
                diff = abs(fresh_fold["model_eval"][k] - saved_fold["model_eval"][k])
                if diff > 1e-7:
                    mismatches.append(f"{ticker} {year} model_eval.{k}: fresh={fresh_fold['model_eval'][k]} saved={saved_fold['model_eval'][k]}")

            # 2. Fixed Baselines (B&H, Cash, SMA, Fixed Hybrid)
            for b_name in ["buy_and_hold", "cash", "sma_50_200", "fixed_gene_hybrid"]:
                total_checks += 1
                fresh_b = fresh_fold["baselines"][b_name]
                saved_b = saved_fold["baselines"][b_name]

                eq_diff = np.max(np.abs(np.array(fresh_b["equity"]) - np.array(saved_b["equity"])))
                if eq_diff > 1e-7:
                    mismatches.append(f"{ticker} {year} baselines.{b_name}.equity max_diff={eq_diff}")

                ret_diff = abs(fresh_b["metrics"]["total_return"] - saved_b["metrics"]["total_return"])
                if ret_diff > 1e-7:
                    mismatches.append(f"{ticker} {year} baselines.{b_name}.total_return diff={ret_diff}")

            # 3. GA Runs across all seeds (Hybrid, Cost2x, Exp-Matched B&H, Ablation)
            for seed in runner.ga_seeds:
                s_str = str(seed)
                fresh_ga = fresh_fold["ga_runs"][s_str]
                saved_ga = saved_fold["ga_runs"][s_str]

                # A. Full Hybrid
                total_checks += 1
                fresh_hyb = fresh_ga["hybrid"]
                saved_hyb = saved_ga["hybrid"]

                if fresh_hyb["is_feasible"] != saved_hyb["is_feasible"]:
                    mismatches.append(f"{ticker} {year} seed {seed} hybrid.is_feasible: fresh={fresh_hyb['is_feasible']} saved={saved_hyb['is_feasible']}")

                if fresh_hyb["is_feasible"]:
                    genes_diff = np.max(np.abs(np.array(fresh_hyb["genes"]) - np.array(saved_hyb["genes"])))
                    if genes_diff > 1e-12:
                        mismatches.append(f"{ticker} {year} seed {seed} hybrid.genes max_diff={genes_diff}")

                eq_diff = np.max(np.abs(np.array(fresh_hyb["equity"]) - np.array(saved_hyb["equity"])))
                if eq_diff > 1e-7:
                    mismatches.append(f"{ticker} {year} seed {seed} hybrid.equity max_diff={eq_diff}")

                ret_diff = abs(fresh_hyb["metrics"]["total_return"] - saved_hyb["metrics"]["total_return"])
                if ret_diff > 1e-7:
                    mismatches.append(f"{ticker} {year} seed {seed} hybrid.total_return diff={ret_diff}")

                # B. Cost Sensitivity 2x
                total_checks += 1
                fresh_c2 = fresh_ga["cost_sensitivity_2x"]
                saved_c2 = saved_ga["cost_sensitivity_2x"]
                eq_diff_c2 = np.max(np.abs(np.array(fresh_c2["equity"]) - np.array(saved_c2["equity"])))
                if eq_diff_c2 > 1e-7:
                    mismatches.append(f"{ticker} {year} seed {seed} cost2x.equity max_diff={eq_diff_c2}")

                # C. Exposure-Matched Buy & Hold Diagnostic
                total_checks += 1
                fresh_exp = fresh_ga["exposure_matched_bh"]
                saved_exp = saved_ga["exposure_matched_bh"]
                eq_diff_exp = np.max(np.abs(np.array(fresh_exp["equity"]) - np.array(saved_exp["equity"])))
                if eq_diff_exp > 1e-7:
                    mismatches.append(f"{ticker} {year} seed {seed} exp_bh.equity max_diff={eq_diff_exp}")

                # D. Constant Prob Ablation
                total_checks += 1
                fresh_abl = fresh_ga["constant_prob_ablation"]
                saved_abl = saved_ga["constant_prob_ablation"]
                if fresh_abl["is_feasible"] != saved_abl["is_feasible"]:
                    mismatches.append(f"{ticker} {year} seed {seed} ablation.is_feasible: fresh={fresh_abl['is_feasible']} saved={saved_abl['is_feasible']}")

                if fresh_abl["is_feasible"]:
                    genes_diff_abl = np.max(np.abs(np.array(fresh_abl["genes"]) - np.array(saved_abl["genes"])))
                    if genes_diff_abl > 1e-12:
                        mismatches.append(f"{ticker} {year} seed {seed} ablation.genes max_diff={genes_diff_abl}")

                eq_diff_abl = np.max(np.abs(np.array(fresh_abl["equity"]) - np.array(saved_abl["equity"])))
                if eq_diff_abl > 1e-7:
                    mismatches.append(f"{ticker} {year} seed {seed} ablation.equity max_diff={eq_diff_abl}")

    print("\n" + "=" * 80)
    print(f"AUDIT COMPLETE. Total checks evaluated: {total_checks}")
    if len(mismatches) == 0:
        print("SUCCESS: ZERO MISMATCHES DETECTED. Current source code strictly reproduces saved campaign artifact!")
        print("All genes match within 1e-12 atol; all equity paths match within 1e-7 atol.")
        print("=" * 80)
        return 0
    else:
        print(f"FAILURE: {len(mismatches)} MISMATCHES FOUND:")
        for m in mismatches[:20]:
            print("  -", m)
        if len(mismatches) > 20:
            print(f"  ... and {len(mismatches) - 20} more.")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    exit_code = run_campaign_reproducibility_audit()
    sys.exit(exit_code)
