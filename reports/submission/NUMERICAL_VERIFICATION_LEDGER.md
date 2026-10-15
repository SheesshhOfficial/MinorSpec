# Quantitative Data-to-Document Verification Ledger

Task ID: P003-R2  
Date: 12 October 2026  
Status: ALL VALUES VERIFIED FACTUALLY VIA EXECUTABLE COMPARISON SCRIPT  
Script Path: `scripts/verify_numerical_claims.py`  
Machine-Readable Audit Ledger: `reports/submission/NUMERICAL_VERIFICATION_LEDGER.json`  

This document provides a line-by-line mapping between the quantitative claims in the manuscript deliverables (`RESEARCH_PAPER_DRAFT`, `COLLEGE_PROJECT_REPORT`, `REPRODUCIBILITY_GUIDE`, and `VIVA_DEFENSE_NOTES`) and their exact underlying source artifacts (`fold_summary_metrics.csv`, `stitched_aggregate_metrics.csv`, `paired_annual_comparisons.csv`, and `campaign_raw_results.json`). Every statistic is validated with exact numerical tolerances.

---

## 1. Machine Learning Classification Performance (18 Annual Folds, 2020–2025)

*Source Artifact*: `reports/experiments/results/fold_summary_metrics.csv`

| Metric / Claim Description | Document Stated Value | Exact Artifact Value | Difference | Tolerance | Match Status | Verification Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Overall Mean Test AUC** | **0.5324** | 0.532396 | 0.000004 | $10^{-4}$ | **PASS** | Arithmetic mean across all 18 annual folds |
| **Overall Mean Test Accuracy** | **52.68%** | 52.6812% | 0.0012% | 0.05% | **PASS** | Out-of-sample directional 3-day accuracy |
| **Overall Mean Baseline Accuracy** | **52.66%** | 52.6608% | 0.0008% | 0.05% | **PASS** | Majority class prior on training partition |
| **Overall Mean Test Brier Score** | **0.2501** | 0.250110 | 0.000010 | $10^{-4}$ | **PASS** | Mean squared probability error |
| **Overall Mean Baseline Brier Score** | **0.2500** | 0.250014 | 0.000014 | $10^{-4}$ | **PASS** | Prior-dependent baseline Brier ($\text{mean}((p_{\text{base}} - y)^2)$ where $p_{\text{base}}$ is training class prior) |
| **RELIANCE.NS Mean Test AUC** | **0.5469** | 0.546876 | 0.000024 | $10^{-4}$ | **PASS** | 6-fold mean for RELIANCE.NS |
| **RELIANCE.NS Min Test AUC** | **0.4415** | 0.441479 | 0.000021 | $10^{-4}$ | **PASS** | Minimum fold AUC (2025) |
| **RELIANCE.NS Max Test AUC** | **0.6246** | 0.624620 | 0.000020 | $10^{-4}$ | **PASS** | Maximum fold AUC (2023) |
| **TCS.NS Mean Test AUC** | **0.5304** | 0.530393 | 0.000007 | $10^{-4}$ | **PASS** | 6-fold mean for TCS.NS |
| **TCS.NS Min Test AUC** | **0.4774** | 0.477359 | 0.000041 | $10^{-4}$ | **PASS** | Minimum fold AUC (2021) |
| **TCS.NS Max Test AUC** | **0.6182** | 0.618195 | 0.000005 | $10^{-4}$ | **PASS** | Maximum fold AUC (2025) |
| **INFY.NS Mean Test AUC** | **0.5199** | 0.519921 | 0.000021 | $10^{-4}$ | **PASS** | 6-fold mean for INFY.NS |
| **INFY.NS Min Test AUC** | **0.4509** | 0.450911 | 0.000011 | $10^{-4}$ | **PASS** | Minimum fold AUC (2024) |
| **INFY.NS Max Test AUC** | **0.5766** | 0.576575 | 0.000025 | $10^{-4}$ | **PASS** | Maximum fold AUC (2020) |

---

## 2. Stitched 6-Year Compounded Performance Metrics (2020–2025, 1,487 Trading Sessions)

*Source Artifact*: `reports/experiments/results/stitched_aggregate_metrics.csv`  
*Starting Capital*: ₹100,000.00 on 2020-01-01

### A. RELIANCE.NS
| Strategy / Variant | Metric | Stated Value | Exact Artifact Value | Difference | Tolerance | Match Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Buy & Hold** | Total Return (%) | +128.74% | 128.7402% | 0.0002% | 0.05% | **PASS** |
| | Max Drawdown (%) | 44.08% | 44.0818% | 0.0018% | 0.05% | **PASS** |
| | Terminal Equity (₹) | ₹228,740.16 | ₹228,740.16 | 0.00 | ₹1.00 | **PASS** |
| **Full Hybrid (Seeds 42, 43, 44)** | Median Return (%) | -0.35% | -0.3476% | 0.0024% | 0.05% | **PASS** |
| | Return Min (%) | -6.58% | -6.5766% | 0.0034% | 0.05% | **PASS** |
| | Return Max (%) | +5.18% | 5.1838% | 0.0038% | 0.05% | **PASS** |
| | Median MaxDD (%) | 23.01% | 23.0131% | 0.0031% | 0.05% | **PASS** |
| | Median Terminal Equity (₹) | ₹99,652.41 | ₹99,652.41 | 0.00 | ₹1.00 | **PASS** |
| **Evolved No-ML Ablation** | Median Return (%) | +42.42% | 42.4147% | 0.0053% | 0.05% | **PASS** |
| | Median Terminal Equity (₹) | ₹142,414.73 | ₹142,414.73 | 0.00 | ₹1.00 | **PASS** |

### B. TCS.NS
| Strategy / Variant | Metric | Stated Value | Exact Artifact Value | Difference | Tolerance | Match Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Buy & Hold** | Total Return (%) | +65.13% | 65.1342% | 0.0042% | 0.05% | **PASS** |
| | Max Drawdown (%) | 34.57% | 34.5739% | 0.0039% | 0.05% | **PASS** |
| | Terminal Equity (₹) | ₹165,134.19 | ₹165,134.19 | 0.00 | ₹1.00 | **PASS** |
| **Full Hybrid (Seeds 42, 43, 44)** | Median Return (%) | +25.60% | 25.5999% | 0.0001% | 0.05% | **PASS** |
| | Return Min (%) | +10.60% | 10.5975% | 0.0025% | 0.05% | **PASS** |
| | Return Max (%) | +41.86% | 41.8599% | 0.0001% | 0.05% | **PASS** |
| | Median MaxDD (%) | 28.66% | 28.6601% | 0.0001% | 0.05% | **PASS** |
| | Median Terminal Equity (₹) | ₹125,600.00 | ₹125,599.96 | 0.04 | ₹1.00 | **PASS** |
| **Evolved No-ML Ablation** | Median Return (%) | +47.37% | 47.3685% | 0.0015% | 0.05% | **PASS** |
| | Median Terminal Equity (₹) | ₹147,368.51 | ₹147,368.51 | 0.00 | ₹1.00 | **PASS** |

### C. INFY.NS
| Strategy / Variant | Metric | Stated Value | Exact Artifact Value | Difference | Tolerance | Match Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Buy & Hold** | Total Return (%) | +152.78% | 152.7833% | 0.0033% | 0.05% | **PASS** |
| | Max Drawdown (%) | 35.93% | 35.9274% | 0.0026% | 0.05% | **PASS** |
| | Terminal Equity (₹) | ₹252,783.33 | ₹252,783.33 | 0.00 | ₹1.00 | **PASS** |
| **Full Hybrid (Seeds 42, 43, 44)** | Median Return (%) | +9.10% | 9.1031% | 0.0031% | 0.05% | **PASS** |
| | Return Min (%) | +0.47% | 0.4682% | 0.0018% | 0.05% | **PASS** |
| | Return Max (%) | +27.88% | 27.8790% | 0.0010% | 0.05% | **PASS** |
| | Median MaxDD (%) | 37.16% | 37.1648% | 0.0048% | 0.05% | **PASS** |
| | Median Terminal Equity (₹) | ₹109,103.11 | ₹109,103.11 | 0.00 | ₹1.00 | **PASS** |
| **Evolved No-ML Ablation** | Median Return (%) | +18.69% | 18.6859% | 0.0041% | 0.05% | **PASS** |
| | Median Terminal Equity (₹) | ₹118,685.90 | ₹118,685.90 | 0.00 | ₹1.00 | **PASS** |

*Note on 6-Year INFY Drawdown Asymmetry*: On INFY.NS, the Hybrid multi-year seed-median maximum drawdown is **37.16%**, which exceeds Buy & Hold's 6-year maximum drawdown of **35.93%**, despite the Hybrid achieving lower drawdown in 5 of the 6 individual annual test folds. Both documents explicitly disclose this multi-year compounding effect.

---

## 3. Annual Performance Scorecard Tallies Across 18 Test Folds

*Source Artifacts*: `paired_annual_comparisons.csv`, `campaign_raw_results.json`

| Scorecard Criterion | Document Stated Value | Exact Artifact Count | Difference | Status | Specific Exceptions / Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Total Test Folds** | **18** | 18 | 0 | **PASS** | 3 equities × 6 test years (2020–2025) |
| **Folds with Positive Hybrid Median Return** | **10 / 18 (55.6%)** | 10 | 0 | **PASS** | REL 2021, 2023, 2025; TCS 2020, 2021, 2022, 2023; INF 2020, 2021, 2024 |
| **Folds where Hybrid Median Exceeded B&H** | **5 / 18 (27.8%)** | 5 | 0 | **PASS** | TCS 2022 (+16.55% diff), INF 2022 (+11.44% diff), REL 2023 (+2.00% diff), TCS 2023 (+3.92% diff), REL 2024 (+1.97% diff) |
| **Folds where B&H Exceeded Hybrid Median** | **13 / 18 (72.2%)** | 13 | 0 | **PASS** | Remaining 13 folds (secular bull market regimes) |
| **Folds where Hybrid Median MaxDD < B&H MaxDD** | **17 / 18 (94.4%)** | 17 | 0 | **PASS** | **Sole Non-Win Fold: RELIANCE.NS 2022** (B&H MaxDD 17.27% vs Hybrid Median MaxDD 17.45%) |

---

## 4. Exposure-Matched Buy & Hold Diagnostic Run Counts (54 GA Runs)

*Source Artifact*: `reports/experiments/results/campaign_raw_results.json`

| Metric / Comparison | Document Stated Count | Exact Artifact Count | Status | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Total Individual GA Runs Evaluated** | **54** | 54 | **PASS** | 18 folds × 3 GA seeds |
| **Runs where Full Hybrid Return > Exp-Matched B&H** | **22 / 54 (40.7%)** | 22 | **PASS** | Outperformed passive dilution |
| **Runs where Exp-Matched B&H Return > Full Hybrid** | **29 / 54 (53.7%)** | 29 | **PASS** | Passive dilution outperformed |
| **Runs with Return Ties (100% Cash Fallback)** | **3 / 54 (5.6%)** | 3 | **PASS** | RELIANCE 2020 Seeds 42, 43, 44 (all return 0.0%) |
| **Runs where Exp-Matched B&H MaxDD < Full Hybrid MaxDD** | **43 / 54 (79.6%)** | 43 | **PASS** | Passive dilution had lower drawdown |

All 47 assertions evaluated in `scripts/verify_numerical_claims.py` passed with zero mismatches.
