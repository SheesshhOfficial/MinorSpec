"""
Executable Data-to-Document Numerical Verification Script.
Task P003-R1: Maps every claimed table cell, metric, and quantitative statistic
in the submission documents directly to artifact CSV/JSON paths, validating rounding,
tolerances, and assertions.
Exits with code 0 on full pass, or non-zero on mismatch.
"""

import sys
import json
import math
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path("u:/MInor-Specialization")
RESULTS_DIR = PROJECT_ROOT / "reports" / "experiments" / "results"
SUBMISSION_DIR = PROJECT_ROOT / "reports" / "submission"

def run_numerical_verification():
    print("=" * 80)
    print("STARTING EXECUTABLE DATA-TO-DOCUMENT NUMERICAL VERIFICATION")
    print(f"Artifact Directory: {RESULTS_DIR}")
    print("=" * 80)

    # 1. Load Artifacts
    raw_file = RESULTS_DIR / "campaign_raw_results.json"
    fold_file = RESULTS_DIR / "fold_summary_metrics.csv"
    stitched_file = RESULTS_DIR / "stitched_aggregate_metrics.csv"
    paired_file = RESULTS_DIR / "paired_annual_comparisons.csv"
    audit_file = RESULTS_DIR / "campaign_audit.json"

    with open(raw_file, "r") as f:
        raw_data = json.load(f)
    fold_df = pd.read_csv(fold_file)
    stitched_df = pd.read_csv(stitched_file)
    paired_df = pd.read_csv(paired_file)
    with open(audit_file, "r") as f:
        audit_data = json.load(f)

    ledger_records = []
    mismatches = []

    def check_value(claim_name, doc_val, actual_val, tol=1e-4, is_percent=False):
        diff = abs(doc_val - actual_val)
        passed = diff <= tol
        rec = {
            "claim": claim_name,
            "document_value": doc_val,
            "artifact_value": actual_val,
            "difference": diff,
            "tolerance": tol,
            "status": "PASS" if passed else "FAIL"
        }
        ledger_records.append(rec)
        if not passed:
            mismatches.append(f"MISMATCH in '{claim_name}': doc={doc_val}, actual={actual_val}, diff={diff}")
        return passed

    # -------------------------------------------------------------
    # 2. Check LightGBM Classification Metrics
    # -------------------------------------------------------------
    print("\n--- 1. Validating Classification Metrics ---")
    # Per-asset means
    rel_grp = fold_df[fold_df["ticker"] == "RELIANCE.NS"]
    tcs_grp = fold_df[fold_df["ticker"] == "TCS.NS"]
    inf_grp = fold_df[fold_df["ticker"] == "INFY.NS"]

    # Overall means
    mean_auc = float(fold_df["test_auc"].mean())
    mean_acc = float(fold_df["test_accuracy"].mean())
    mean_base_acc = float(fold_df["baseline_accuracy"].mean())
    mean_brier = float(fold_df["test_brier"].mean())
    mean_base_brier = float(fold_df["baseline_brier"].mean())

    check_value("Overall Mean AUC", 0.5324, mean_auc, tol=1e-4)
    check_value("Overall Mean Accuracy (%)", 52.68, mean_acc * 100.0, tol=0.05)
    check_value("Overall Mean Baseline Accuracy (%)", 52.66, mean_base_acc * 100.0, tol=0.05)
    check_value("Overall Mean Brier Score", 0.2501, mean_brier, tol=1e-4)
    check_value("Overall Mean Baseline Brier Score", 0.2500, mean_base_brier, tol=1e-4)

    # Asset specific AUCs
    check_value("RELIANCE.NS Mean AUC", 0.5469, float(rel_grp["test_auc"].mean()), tol=1e-4)
    check_value("RELIANCE.NS Min AUC", 0.4415, float(rel_grp["test_auc"].min()), tol=1e-4)
    check_value("RELIANCE.NS Max AUC", 0.6246, float(rel_grp["test_auc"].max()), tol=1e-4)

    check_value("TCS.NS Mean AUC", 0.5304, float(tcs_grp["test_auc"].mean()), tol=1e-4)
    check_value("TCS.NS Min AUC", 0.4774, float(tcs_grp["test_auc"].min()), tol=1e-4)
    check_value("TCS.NS Max AUC", 0.6182, float(tcs_grp["test_auc"].max()), tol=1e-4)

    check_value("INFY.NS Mean AUC", 0.5199, float(inf_grp["test_auc"].mean()), tol=1e-4)
    check_value("INFY.NS Min AUC", 0.4509, float(inf_grp["test_auc"].min()), tol=1e-4)
    check_value("INFY.NS Max AUC", 0.5766, float(inf_grp["test_auc"].max()), tol=1e-4)

    # -------------------------------------------------------------
    # 3. Check Stitched Multi-Year Performance Metrics
    # -------------------------------------------------------------
    print("\n--- 2. Validating Stitched Multi-Year Compound Metrics ---")
    def get_stitched_row(ticker, strat_key):
        sub = stitched_df[(stitched_df["ticker"] == ticker) & (stitched_df["strategy_key"] == strat_key)]
        if len(sub) == 0:
            raise ValueError(f"Strategy {strat_key} not found for {ticker}")
        return sub.iloc[0]

    # RELIANCE.NS
    r_bh = get_stitched_row("RELIANCE.NS", "buy_and_hold")
    check_value("RELIANCE Buy & Hold Total Return (%)", 128.74, r_bh["total_return"] * 100.0, tol=0.05)
    check_value("RELIANCE Buy & Hold MaxDD (%)", 44.08, r_bh["max_drawdown"] * 100.0, tol=0.05)
    check_value("RELIANCE Buy & Hold Terminal Equity", 228740.16, r_bh["terminal_equity"], tol=1.0)

    # Multi-seed hybrid for RELIANCE
    r_hyb_42 = get_stitched_row("RELIANCE.NS", "hybrid_seed_42")
    r_hyb_43 = get_stitched_row("RELIANCE.NS", "hybrid_seed_43")
    r_hyb_44 = get_stitched_row("RELIANCE.NS", "hybrid_seed_44")
    r_hyb_rets = [r_hyb_42["total_return"], r_hyb_43["total_return"], r_hyb_44["total_return"]]
    r_hyb_dds = [r_hyb_42["max_drawdown"], r_hyb_43["max_drawdown"], r_hyb_44["max_drawdown"]]
    r_hyb_terms = [r_hyb_42["terminal_equity"], r_hyb_43["terminal_equity"], r_hyb_44["terminal_equity"]]

    check_value("RELIANCE Hybrid Seed Median Return (%)", -0.35, np.median(r_hyb_rets) * 100.0, tol=0.05)
    check_value("RELIANCE Hybrid Min Return (%)", -6.58, min(r_hyb_rets) * 100.0, tol=0.05)
    check_value("RELIANCE Hybrid Max Return (%)", 5.18, max(r_hyb_rets) * 100.0, tol=0.05)
    check_value("RELIANCE Hybrid Seed Median MaxDD (%)", 23.01, np.median(r_hyb_dds) * 100.0, tol=0.05)
    check_value("RELIANCE Hybrid Seed Median Terminal Equity", 99652.41, np.median(r_hyb_terms), tol=1.0)

    # TCS.NS
    t_bh = get_stitched_row("TCS.NS", "buy_and_hold")
    check_value("TCS Buy & Hold Total Return (%)", 65.13, t_bh["total_return"] * 100.0, tol=0.05)
    check_value("TCS Buy & Hold MaxDD (%)", 34.57, t_bh["max_drawdown"] * 100.0, tol=0.05)
    check_value("TCS Buy & Hold Terminal Equity", 165134.19, t_bh["terminal_equity"], tol=1.0)

    t_hyb_42 = get_stitched_row("TCS.NS", "hybrid_seed_42")
    t_hyb_43 = get_stitched_row("TCS.NS", "hybrid_seed_43")
    t_hyb_44 = get_stitched_row("TCS.NS", "hybrid_seed_44")
    t_hyb_rets = [t_hyb_42["total_return"], t_hyb_43["total_return"], t_hyb_44["total_return"]]
    t_hyb_dds = [t_hyb_42["max_drawdown"], t_hyb_43["max_drawdown"], t_hyb_44["max_drawdown"]]
    t_hyb_terms = [t_hyb_42["terminal_equity"], t_hyb_43["terminal_equity"], t_hyb_44["terminal_equity"]]

    check_value("TCS Hybrid Seed Median Return (%)", 25.60, np.median(t_hyb_rets) * 100.0, tol=0.05)
    check_value("TCS Hybrid Min Return (%)", 10.60, min(t_hyb_rets) * 100.0, tol=0.05)
    check_value("TCS Hybrid Max Return (%)", 41.86, max(t_hyb_rets) * 100.0, tol=0.05)
    check_value("TCS Hybrid Seed Median MaxDD (%)", 28.66, np.median(t_hyb_dds) * 100.0, tol=0.05)
    check_value("TCS Hybrid Seed Median Terminal Equity", 125600.00, np.median(t_hyb_terms), tol=1.0)

    # INFY.NS
    i_bh = get_stitched_row("INFY.NS", "buy_and_hold")
    check_value("INFY Buy & Hold Total Return (%)", 152.78, i_bh["total_return"] * 100.0, tol=0.05)
    check_value("INFY Buy & Hold MaxDD (%)", 35.93, i_bh["max_drawdown"] * 100.0, tol=0.05)
    check_value("INFY Buy & Hold Terminal Equity", 252783.33, i_bh["terminal_equity"], tol=1.0)

    i_hyb_42 = get_stitched_row("INFY.NS", "hybrid_seed_42")
    i_hyb_43 = get_stitched_row("INFY.NS", "hybrid_seed_43")
    i_hyb_44 = get_stitched_row("INFY.NS", "hybrid_seed_44")
    i_hyb_rets = [i_hyb_42["total_return"], i_hyb_43["total_return"], i_hyb_44["total_return"]]
    i_hyb_dds = [i_hyb_42["max_drawdown"], i_hyb_43["max_drawdown"], i_hyb_44["max_drawdown"]]
    i_hyb_terms = [i_hyb_42["terminal_equity"], i_hyb_43["terminal_equity"], i_hyb_44["terminal_equity"]]

    check_value("INFY Hybrid Seed Median Return (%)", 9.10, np.median(i_hyb_rets) * 100.0, tol=0.05)
    check_value("INFY Hybrid Min Return (%)", 0.47, min(i_hyb_rets) * 100.0, tol=0.05)
    check_value("INFY Hybrid Max Return (%)", 27.88, max(i_hyb_rets) * 100.0, tol=0.05)
    check_value("INFY Hybrid Seed Median MaxDD (%)", 37.16, np.median(i_hyb_dds) * 100.0, tol=0.05)
    check_value("INFY Hybrid Seed Median Terminal Equity", 109103.11, np.median(i_hyb_terms), tol=1.0)

    # -------------------------------------------------------------
    # 4. Check Annual Scorecard Tallies & Exceptions
    # -------------------------------------------------------------
    print("\n--- 3. Validating Annual Scorecard Tallies ---")
    pos_hyb_folds = 0
    hyb_beats_bh = 0
    bh_beats_hyb = 0
    hyb_lower_dd = 0
    dd_nonwin_folds = []

    for ticker in ["RELIANCE.NS", "TCS.NS", "INFY.NS"]:
        for year in range(2020, 2026):
            fold = raw_data[ticker][str(year)]
            b_ret = fold["baselines"]["buy_and_hold"]["metrics"]["total_return"]
            b_dd = fold["baselines"]["buy_and_hold"]["metrics"]["max_drawdown"]
            
            h_rets = [fold["ga_runs"][s]["hybrid"]["metrics"]["total_return"] for s in ["42", "43", "44"]]
            h_dds = [fold["ga_runs"][s]["hybrid"]["metrics"]["max_drawdown"] for s in ["42", "43", "44"]]
            
            h_med_ret = float(np.median(h_rets))
            h_med_dd = float(np.median(h_dds))
            
            if h_med_ret > 0:
                pos_hyb_folds += 1
            if h_med_ret > b_ret:
                hyb_beats_bh += 1
            elif b_ret > h_med_ret:
                bh_beats_hyb += 1
                
            if h_med_dd < b_dd:
                hyb_lower_dd += 1
            else:
                dd_nonwin_folds.append(f"{ticker} {year}")

    check_value("Positive Hybrid Return Folds", 10, pos_hyb_folds, tol=0)
    check_value("Hybrid Beats Buy & Hold Return Folds", 5, hyb_beats_bh, tol=0)
    check_value("Buy & Hold Beats Hybrid Return Folds", 13, bh_beats_hyb, tol=0)
    check_value("Hybrid Lower Annual MaxDD Folds", 17, hyb_lower_dd, tol=0)
    
    # Assert sole non-win is RELIANCE 2022
    assert dd_nonwin_folds == ["RELIANCE.NS 2022"], f"Expected non-win fold ['RELIANCE.NS 2022'], got {dd_nonwin_folds}"
    ledger_records.append({
        "claim": "Sole Median Annual MaxDD Non-Win Fold",
        "document_value": "RELIANCE.NS 2022",
        "artifact_value": dd_nonwin_folds[0],
        "difference": 0,
        "tolerance": 0,
        "status": "PASS"
    })

    # -------------------------------------------------------------
    # 5. Check Exposure-Matched Diagnostic Run Counts
    # -------------------------------------------------------------
    print("\n--- 4. Validating Exposure-Matched Diagnostic Counts ---")
    hyb_ret_wins = 0
    exp_ret_wins = 0
    diag_ties = 0
    exp_dd_lower = 0

    for ticker in ["RELIANCE.NS", "TCS.NS", "INFY.NS"]:
        for year in range(2020, 2026):
            fold = raw_data[ticker][str(year)]
            for s in ["42", "43", "44"]:
                h_r = fold["ga_runs"][s]["hybrid"]["metrics"]["total_return"]
                e_r = fold["ga_runs"][s]["exposure_matched_bh"]["metrics"]["total_return"]
                h_d = fold["ga_runs"][s]["hybrid"]["metrics"]["max_drawdown"]
                e_d = fold["ga_runs"][s]["exposure_matched_bh"]["metrics"]["max_drawdown"]
                
                if h_r > e_r:
                    hyb_ret_wins += 1
                elif e_r > h_r:
                    exp_ret_wins += 1
                else:
                    diag_ties += 1
                    
                if e_d < h_d:
                    exp_dd_lower += 1

    check_value("Hybrid > Exp-Matched B&H Return Runs", 22, hyb_ret_wins, tol=0)
    check_value("Exp-Matched B&H > Hybrid Return Runs", 29, exp_ret_wins, tol=0)
    check_value("Exp-Matched B&H Return Ties", 3, diag_ties, tol=0)
    check_value("Exp-Matched B&H Lower MaxDD Runs", 43, exp_dd_lower, tol=0)

    # -------------------------------------------------------------
    # 6. Save Machine-Readable Ledger Output
    # -------------------------------------------------------------
    out_json = SUBMISSION_DIR / "NUMERICAL_VERIFICATION_LEDGER.json"
    with open(out_json, "w") as f:
        json.dump(ledger_records, f, indent=2)
    print(f"\nSaved machine-readable ledger to {out_json}")

    print("\n" + "=" * 80)
    if len(mismatches) == 0:
        print(f"VERIFICATION SUCCESS: All {len(ledger_records)} quantitative assertions PASSED!")
        print("Zero discrepancies found between approved artifacts and manuscript claims.")
        print("=" * 80)
        return 0
    else:
        print(f"VERIFICATION FAILURE: {len(mismatches)} mismatches detected:")
        for m in mismatches:
            print("  -", m)
        print("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(run_numerical_verification())
