# Retrospective Rolling NSE Research Experiment Results (Task P002-R3)

**Status**: FROZEN PROTOCOL EVALUATED FACTUALLY WITH SYNCHRONIZED SIMULATOR EVIDENCE  
**Universe**: `RELIANCE.NS`, `TCS.NS`, `INFY.NS` (Evaluated Strictly Individually; No Cross-Asset Portfolio Blending Claimed)  
**Evaluation Nature**: Retrospective Historical Research (Exploratory single-split runs were inspected earlier; results presented as empirical retrospective walk-forward evidence without claims of forward untouched out-of-sample deployment)  
**Execution Platform**: Windows 11 (build 10.0.26300), Python 3.13.14, LightGBM 4.7.0, Numba 0.66.0, NumPy 2.3.2, Pandas 3.0.2, Scikit-learn 1.9.0  
**Test Years**: 2020 through 2025 (6 Annual Test Folds per Asset; 1,487 Trading Bars; Nominal Capital in INR)  
**Protocol References**: Retrospective protocol specification in [protocol.json](file:///u:/MInor-Specialization/reports/experiments/protocol.json); formal audit corrections in [protocol_correction.json](file:///u:/MInor-Specialization/reports/experiments/protocol_correction.json) (v1.1.0, SHA-256: `e08d24cbfa641dd13d2f243007ba68e21199a6134bdf8880608fa8faeb0df80b`)  
**Audit & Provenance Companion**: [campaign_audit.json](file:///u:/MInor-Specialization/reports/experiments/results/campaign_audit.json)  
**Input Snapshot Reference**: [manifest.json](file:///u:/MInor-Specialization/reports/experiments/inputs/manifest.json) (All Parquet SHA-256 hashes strictly verified)

---

## 1. Executive Summary

This study evaluates whether combining a gradient-boosted decision tree classifier (LightGBM) with multi-objective evolutionary strategy optimization (NSGA-II) discovers robust trading rules across large-cap Indian equities (`RELIANCE.NS`, `TCS.NS`, `INFY.NS`) over a 6-year walk-forward period (2020–2025).

Following Task P002-R3, all campaign evidence, tables, CSVs, figures, and reproducibility tests have been synchronized from scratch using the unified scheduled fold-end liquidation convention:
- **Scheduled Fold-End Rule**: In all backtests (fast vectorized Numba, detailed simulator, and SMA baseline), no new positions may be entered on the scheduled last tradable session ($i < \text{last\_tradable\_idx}$); any existing position is liquidated at the Close of the last session with positive trading volume.
- **Campaign-Wide Source Verification**: `scripts/audit_campaign_reproducibility.py` evaluated all 18 annual folds across all 3 seeds and confirmed **zero mismatches** between current source code and saved artifacts (`genes` atol $\le 10^{-12}$, `equity` atol $\le 10^{-7}$).
- **Audit Companion**: Provenance hashes, partition boundaries, scored sample dates, and environment versions are documented in [campaign_audit.json](file:///u:/MInor-Specialization/reports/experiments/results/campaign_audit.json).

### Core Findings:
1. **Modest Predictive Improvement Over Base Rates**:
   Across all 18 annual folds (3 assets × 6 years), the LightGBM classifier achieves an average out-of-sample **AUC of 0.5324**, **directional accuracy of 52.68%** (compared to the naive training-class positive baseline of **52.66%**), and a **Brier score of 0.2501** (vs baseline 0.2500). Directional classification improvements over simple base rates remain slight.
2. **Defensive Exposure Tendency**:
   Because classifier probabilities oscillate narrowly around 0.50 (mostly within $[0.49, 0.56]$), NSGA-II discovers parameter sets with high probability hurdles ($p_{\text{entry}} \ge 0.55$) and tight stop-loss / volatility limits. In 2020 for `RELIANCE.NS`, no candidate individual met the feasibility requirement of $\ge 5$ development trades; adhering strictly to protocol, the system defaulted to 100% Cash without forcing trading.
3. **Consistent Drawdown Dampening with Sacrificed Trend Participation**:
   Across the 18 folds, the Full Hybrid strategy (evaluating seed medians) achieved a lower annual maximum drawdown than Buy & Hold in **17 out of 18 folds (94.4%)**. However, by sitting in cash during strong market expansions, the Hybrid underperformed Buy & Hold total return in **13 out of 18 folds (72.2%)**, outperforming in **5 out of 18 folds (27.8%)** (primarily during severe market corrections such as 2022 and 2023).
4. **Stitched Multi-Year Capital Growth**:
   Carrying capital forward across the 6 test years (reinvesting terminal capital with compounding and friction), Buy & Hold achieved higher final wealth than the Hybrid strategy across all three equities:
   - `RELIANCE.NS`: Buy & Hold **+128.74%** (CAGR 15.05%, Sharpe 0.64, MaxDD 44.08%) vs Hybrid Seed Median **-0.35%** (range `[-6.58%, +5.18%]`, CAGR -0.06%, Sharpe 0.04, MaxDD 23.01%).
   - `TCS.NS`: Buy & Hold **+65.13%** (CAGR 8.87%, Sharpe 0.48, MaxDD 34.57%) vs Hybrid Seed Median **+25.60%** (range `[+10.60%, +41.86%]`, CAGR 3.94%, Sharpe 0.44, MaxDD 28.66%).
   - `INFY.NS`: Buy & Hold **+152.78%** (CAGR 17.02%, Sharpe 0.71, MaxDD 35.93%) vs Hybrid Seed Median **+9.10%** (range `[+0.47%, +27.88%]`, CAGR 1.49%, Sharpe 0.18, MaxDD 37.16%).
5. **Non-Linear Bracket Path Shifts Under Doubled Friction**:
   When transaction costs are doubled (0.10% commission + 0.10% slippage per side = 0.40% round-trip), total returns drop noticeably. Doubling slippage alters execution prices ($P_{\text{entry}} = \text{Open} \times (1 + \text{slip})$), which mechanically shifts absolute stop-loss thresholds ($P_{\text{stop}} = P_{\text{entry}} - \text{SL} \times \text{ATR}$), causing bracket stops to trigger on different bars and diverging the subsequent trade sequences.

---

## 2. Experimental Protocol, Partition Structure & Conventions

### Chronological Fold Schedule
Each annual fold $Y \in [2020, 2025]$ is constructed strictly chronologically with no temporal leakage:
- **Model Training**: $[Y-8, Y-4]$ (5 calendar years, ~1,230 bars), purged trailing 3 bars overlapping validation forward targets.
- **Model Validation**: $[Y-3]$ (1 calendar year, ~246 bars), purged trailing 3 bars overlapping development forward targets.
- **Rule Development (NSGA-II)**: $[Y-2, Y-1]$ (2 calendar years, ~493 bars), purged trailing 3 bars for GA training/validation; final completed session ($t=-1$ Close) supplies causal prefix context for bar 0 Open trading.
- **Out-of-Sample Test**: $[Y]$ (1 calendar year, ~248 bars), out-of-sample trading; classification scored strictly on the first $N-3$ bars whose forward targets resolve within the fold.

### Dates and Conventions
- **Observation Dates**: 2020-01-01 through 2025-12-31 (1,487 trading bars per asset). Actual first trading session is 2020-01-01; actual final session is 2025-12-31.
- **Capital Units**: Nominal Indian Rupees (₹), initial capital ₹100,000.
- **Capital Exposure Definition**: End-of-day invested position market value divided by total equity:
  $$\text{Capital Exposure}_t = \frac{\text{Shares}_t \times \text{Close}_t}{\text{Equity}_t}$$
  Because this metric is measured at session close after intraday exits have settled, same-day round trips contribute zero to end-of-day exposure. It represents an overnight capital commitment proxy rather than continuous intraday capital tracking.
- **Scheduled Fold-End Liquidation Policy**: In all backtests and baselines, new entries are barred on the scheduled last tradable session ($i < \text{last\_tradable\_idx}$), and any open position is liquidated at session Close. If trailing sessions have zero volume, liquidation occurs deterministically at the last session with positive trading volume to ensure realistic execution without carrying unliquidated shares across fold boundaries.

---

## 3. Machine Learning Classification Performance

All LightGBM classifiers were fitted with `model_seed=42`, `max_depth=5`, `num_leaves=24`, `learning_rate=0.03`, and early stopping on the validation split. The final 3 bars of each annual test fold are masked from classification scoring because their 3-day forward targets extend beyond the fold.

| Asset | Test Year | Test AUC | Test Accuracy | Baseline Accuracy | Test Brier Score | Baseline Brier Score | Scored Samples | Masked Samples |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **RELIANCE.NS** | 2020 | 0.5729 | 52.02% | 50.40% | 0.2495 | 0.2500 | 248 | 3 |
| **RELIANCE.NS** | 2021 | 0.5635 | 54.69% | 57.55% | 0.2454 | 0.2484 | 245 | 3 |
| **RELIANCE.NS** | 2022 | 0.5368 | 50.61% | 50.61% | 0.2501 | 0.2507 | 245 | 3 |
| **RELIANCE.NS** | 2023 | 0.6246 | 55.37% | 55.37% | 0.2459 | 0.2471 | 242 | 3 |
| **RELIANCE.NS** | 2024 | 0.5419 | 46.50% | 46.50% | 0.2551 | 0.2551 | 243 | 3 |
| **RELIANCE.NS** | 2025 | 0.4415 | 52.85% | 52.85% | 0.2504 | 0.2496 | 246 | 3 |
| **TCS.NS** | 2020 | 0.5263 | 55.65% | 54.44% | 0.2480 | 0.2481 | 248 | 3 |
| **TCS.NS** | 2021 | 0.4774 | 55.92% | 55.92% | 0.2468 | 0.2466 | 245 | 3 |
| **TCS.NS** | 2022 | 0.5343 | 48.98% | 48.57% | 0.2533 | 0.2536 | 245 | 3 |
| **TCS.NS** | 2023 | 0.5445 | 50.83% | 50.41% | 0.2499 | 0.2513 | 242 | 3 |
| **TCS.NS** | 2024 | 0.4816 | 49.79% | 51.03% | 0.2534 | 0.2509 | 243 | 3 |
| **TCS.NS** | 2025 | 0.6182 | 44.31% | 44.31% | 0.2586 | 0.2575 | 246 | 3 |
| **INFY.NS** | 2020 | 0.5766 | 62.90% | 62.90% | 0.2422 | 0.2439 | 248 | 3 |
| **INFY.NS** | 2021 | 0.5726 | 58.78% | 58.78% | 0.2439 | 0.2446 | 245 | 3 |
| **INFY.NS** | 2022 | 0.5079 | 48.98% | 48.16% | 0.2577 | 0.2522 | 245 | 3 |
| **INFY.NS** | 2023 | 0.5057 | 54.13% | 54.13% | 0.2483 | 0.2483 | 242 | 3 |
| **INFY.NS** | 2024 | 0.4509 | 55.14% | 55.14% | 0.2479 | 0.2475 | 243 | 3 |
| **INFY.NS** | 2025 | 0.5058 | 50.81% | 50.81% | 0.2558 | 0.2549 | 246 | 3 |
| **Overall Mean** | — | **0.5324** | **52.68%** | **52.66%** | **0.2501** | **0.2500** | **244.8** | **3.0** |

*Interpretation*: Across the 18 folds, out-of-sample directional AUC averages 0.5324 and test accuracy closely tracks majority-class proportions, indicating limited directional predictive improvement over simple base rates.

---

## 4. Stitched 6-Year Aggregate Performance (2020–2025)

Stitched equity carries capital forward from fold to fold, scaling each fold by its pre-trade initial capital ($100,000$). Starting capital is ₹100,000 on 2020-01-01, evaluated across 1,487 trading bars through 2025-12-31. Multi-seed variants show medians and ranges across all three seeds (42, 43, 44).

| Asset | Strategy Variant | Total Return | CAGR | Sharpe Ratio | Max Drawdown | Volatility | Terminal Equity (₹) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **RELIANCE.NS** | Buy & Hold | **+128.74%** | **15.05%** | **0.64** | 44.08% | 28.25% | ₹228,740 |
| | Cash (0%) | 0.00% | 0.00% | 0.00 | 0.00% | 0.00% | ₹100,000 |
| | SMA 50/200 | +29.31% | 4.45% | 0.36 | 26.66% | 15.69% | ₹129,312 |
| | Fixed-Gene Hybrid | +23.26% | 3.61% | 0.44 | **11.54%** | 8.87% | ₹123,264 |
| | Full Hybrid (Seed Median) | **-0.35%** | **-0.06%** | **0.04** | **23.01%** | **8.50%** | **₹99,652** |
| | Full Hybrid (Seed Range) | `[-6.58%, +5.18%]` | `[-1.15%, +0.86%]` | `[-0.07, 0.14]` | `[21.88%, 26.18%]` | `[8.44%, 9.53%]` | `[₹93,423, ₹105,184]` |
| | No-ML Ablation (Seed Median) | +42.42% | 6.18% | 0.45 | 20.03% | 16.03% | ₹142,415 |
| | No-ML Ablation (Seed Range) | `[+39.60%, +46.95%]` | `[+5.82%, +6.74%]` | `[0.45, 0.48]` | `[16.32%, 20.71%]` | `[14.97%, 16.26%]` | `[₹139,597, ₹146,947]` |
| | Exp-Matched B&H (Seed Median) | +15.54% | 2.48% | 0.51 | 9.27% | 5.14% | ₹115,545 |
| | Exp-Matched B&H (Seed Range) | `[+12.82%, +18.80%]` | `[+2.07%, +2.96%]` | `[0.50, 0.52]` | `[6.00%, 10.07%]` | `[4.13%, 6.11%]` | `[₹112,823, ₹118,799]` |
| **TCS.NS** | Buy & Hold | **+65.13%** | **8.87%** | 0.48 | 34.57% | 23.74% | ₹165,134 |
| | Cash (0%) | 0.00% | 0.00% | 0.00 | 0.00% | 0.00% | ₹100,000 |
| | SMA 50/200 | +27.80% | 4.25% | 0.36 | 30.97% | 14.56% | ₹127,803 |
| | Fixed-Gene Hybrid | -32.38% | -6.42% | -0.44 | 43.80% | 13.02% | ₹67,618 |
| | Full Hybrid (Seed Median) | **+25.60%** | **3.94%** | **0.44** | **28.66%** | **11.56%** | **₹125,600** |
| | Full Hybrid (Seed Range) | `[+10.60%, +41.86%]` | `[+1.72%, +6.10%]` | `[0.21, 0.54]` | `[18.29%, 30.12%]` | `[10.02%, 12.28%]` | `[₹110,597, ₹141,860]` |
| | No-ML Ablation (Seed Median) | +47.37% | 6.79% | 0.50 | 31.62% | 15.43% | ₹147,369 |
| | No-ML Ablation (Seed Range) | `[-4.37%, +55.24%]` | `[-0.75%, +7.74%]` | `[0.01, 0.54]` | `[31.05%, 32.37%]` | `[13.60%, 16.05%]` | `[₹95,631, ₹155,244]` |
| | Exp-Matched B&H (Seed Median) | +8.14% | 1.34% | 0.23 | 13.75% | 6.57% | ₹108,141 |
| | Exp-Matched B&H (Seed Range) | `[+6.36%, +17.87%]` | `[+1.05%, +2.82%]` | `[0.21, 0.43]` | `[12.22%, 16.76%]` | `[5.90%, 7.12%]` | `[₹106,364, ₹117,866]` |
| **INFY.NS** | Buy & Hold | **+152.78%** | **17.02%** | **0.71** | 35.93% | 27.39% | ₹252,783 |
| | Cash (0%) | 0.00% | 0.00% | 0.00 | 0.00% | 0.00% | ₹100,000 |
| | SMA 50/200 | +55.08% | 7.72% | 0.55 | 25.84% | 15.60% | ₹155,078 |
| | Fixed-Gene Hybrid | -18.74% | -3.46% | -0.25 | 34.56% | 11.35% | ₹81,257 |
| | Full Hybrid (Seed Median) | **+9.10%** | **1.49%** | **0.18** | **37.16%** | **14.61%** | **₹109,103** |
| | Full Hybrid (Seed Range) | `[+0.47%, +27.88%]` | `[+0.08%, +4.26%]` | `[0.08, 0.36]` | `[31.70%, 41.41%]` | `[13.43%, 15.49%]` | `[₹100,468, ₹127,879]` |
| | No-ML Ablation (Seed Median) | +18.69% | 2.95% | 0.26 | 41.54% | 15.20% | ₹118,686 |
| | No-ML Ablation (Seed Range) | `[+12.63%, +36.30%]` | `[+2.04%, +5.39%]` | `[0.21, 0.42]` | `[37.94%, 42.62%]` | `[15.20%, 15.85%]` | `[₹112,631, ₹136,305]` |
| | Exp-Matched B&H (Seed Median) | +37.04% | 5.48% | 0.63 | 15.89% | 10.34% | ₹137,038 |
| | Exp-Matched B&H (Seed Range) | `[+29.33%, +42.52%]` | `[+4.46%, +6.19%]` | `[0.43, 0.65]` | `[13.46%, 23.72%]` | `[8.84%, 11.58%]` | `[₹129,333, ₹142,525]` |

---

## 5. Annual Paired Differences (Measured Return Differences vs Buy & Hold)

Comparing annual test fold returns between strategies across all three assets (data recorded in [paired_annual_comparisons.csv](file:///u:/MInor-Specialization/reports/experiments/results/paired_annual_comparisons.csv)):

| Asset | Fold | Buy & Hold Return | Hybrid Median Return | Hybrid Seed Range | Return Difference (Hyb - B&H) | No-ML Ablation Median | Exp-Matched B&H Median |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **RELIANCE.NS** | 2020 | +32.30% | 0.00% *(Cash)* | `[0.00%, 0.00%]` | -32.30% | +9.89% | 0.00% |
| | 2021 | +19.30% | +2.24% | `[+0.24%, +4.17%]` | -17.06% | +27.27% | +0.76% |
| | 2022 | +7.84% | -12.07% | `[-13.27%, -12.01%]` | -19.90% | -7.36% | +3.19% |
| | 2023 | +10.00% | +12.00% | `[+9.56%, +17.02%]` | +2.00% | +7.60% | +3.00% |
| | 2024 | -5.67% | -3.70% | `[-15.12%, -3.49%]` | +1.97% | -1.57% | -0.13% |
| | 2025 | +29.52% | +7.36% | `[+2.82%, +9.32%]` | -22.17% | +9.97% | +5.91% |
| **TCS.NS** | 2020 | +34.31% | +4.75% | `[+3.11%, +13.71%]` | -29.56% | +28.21% | +8.04% |
| | 2021 | +30.96% | +6.21% | `[+4.94%, +21.65%]` | -24.75% | +18.49% | +1.70% |
| | 2022 | -12.13% | +4.41% | `[-2.60%, +11.28%]` | +16.55% | -2.44% | -2.83% |
| | 2023 | +20.24% | +24.16% | `[+21.79%, +28.45%]` | +3.92% | +10.97% | +5.63% |
| | 2024 | +9.89% | -3.82% | `[-7.65%, +6.91%]` | -13.71% | +1.38% | +3.42% |
| | 2025 | -19.13% | -19.78% | `[-22.36%, -8.97%]` | -0.65% | -16.95% | -7.29% |
| **INFY.NS** | 2020 | +74.69% | +27.83% | `[+21.48%, +47.88%]` | -46.86% | +34.21% | +22.43% |
| | 2021 | +52.73% | +17.22% | `[+13.33%, +38.04%]` | -35.51% | +37.19% | +18.52% |
| | 2022 | -18.54% | -7.10% | `[-10.71%, -3.03%]` | +11.44% | -9.69% | -5.70% |
| | 2023 | +4.41% | -8.11% | `[-10.97%, -4.29%]` | -12.52% | -14.19% | +2.37% |
| | 2024 | +25.77% | +0.07% | `[-1.57%, +3.28%]` | -25.70% | -0.97% | +2.73% |
| | 2025 | -11.43% | -15.90% | `[-16.92%, -5.86%]` | -4.48% | -12.42% | -4.37% |

### Scorecard Summary:
- **Total Annual Folds**: 18 test folds across 3 equities.
- **Folds with Positive Hybrid Median Return**: **10 out of 18 (55.6%)**.
- **Folds where Hybrid Median Exceeded Buy & Hold Return**: **5 out of 18 (27.8%)** (2022 for TCS and INFY; 2023 for RELIANCE and TCS; 2024 for RELIANCE).
- **Folds where Buy & Hold Exceeded Hybrid Median Return**: **13 out of 18 (72.2%)**.
- **Folds where Hybrid Median Drawdown was Lower than Buy & Hold**: **17 out of 18 (94.4%)**.

---

## 6. Exposure-Matched Diagnostic & Ablation Analysis

### Exposure-Matched Buy & Hold Diagnostic
To evaluate performance relative to capital commitment, each fold was evaluated against a diagnostic model that blends Buy & Hold daily returns with cash using the Hybrid strategy's **Development end-of-day capital exposure fraction** $w_{\text{dev}}$:
- **Assumptions and Scope**: This diagnostic assumes daily frictionless rebalancing and a 0% cash return. Because it measures exposure at close, intraday activity is not captured. It serves as a benchmark for passive capital dilution rather than a strict causal test of market timing.
- **Measured Outcomes**: Across the 54 individual runs (18 folds × 3 seeds), the Full Hybrid achieved higher returns than Exposure-Matched Buy & Hold in **21 out of 54 runs (38.9%)**, while Exposure-Matched Buy & Hold achieved higher returns in **33 runs (61.1%)**.
- **Drawdown Comparison**: Exposure-Matched Buy & Hold exhibited lower maximum drawdown than the Full Hybrid in **47 out of 54 runs (87.0%)**.

### Constant Probability Ablation ($p=0.60$)
When NSGA-II optimizes rules using a constant probability of $p=0.60$ on Development and Test (omitting LightGBM features):
- On `RELIANCE.NS`, the Evolved Ablation achieved a 6-year stitched return median of **+42.42%** (range `[+39.60%, +46.95%]`) vs Hybrid median **-0.35%**.
- On `TCS.NS`, the Ablation median was **+47.37%** (range `[-4.37%, +55.24%]`) vs Hybrid median **+25.60%**.
- On `INFY.NS`, the Ablation median was **+18.69%** (range `[+12.63%, +36.30%]`) vs Hybrid median **+9.10%**.
- Across all three assets, evolving technical parameters without ML generated comparable or higher multi-year capital growth, indicating that the ML signal provided limited observable benefit within this architecture.

---

## 7. Cost Sensitivity & Slippage Bracket Dynamics

Representative hybrid chromosomes frozen from Development were evaluated under doubled transaction friction (**0.10% commission + 0.10% slippage per side**, totaling 0.40% round-trip) without re-optimizing:

| Asset | GA Seed | 1x Costs Total Return | 2x Costs Total Return | Return Difference (Percentage Points) | 1x Sharpe Ratio | 2x Sharpe Ratio |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **RELIANCE.NS** | 42 | -6.58% | -25.41% | -18.83% | -0.07 | -0.46 |
| | 43 | +5.18% | -10.95% | -16.13% | +0.14 | -0.19 |
| | 44 | -0.35% | -14.37% | -14.02% | +0.04 | -0.26 |
| **TCS.NS** | 42 | +10.60% | +1.04% | -9.55% | +0.21 | +0.07 |
| | 43 | +25.60% | +19.61% | -5.99% | +0.44 | +0.35 |
| | 44 | +41.86% | +30.60% | -11.26% | +0.54 | +0.43 |
| **INFY.NS** | 42 | +0.47% | -23.03% | -23.50% | +0.08 | -0.21 |
| | 43 | +9.10% | -10.23% | -19.33% | +0.18 | -0.07 |
| | 44 | +27.88% | -7.97% | -35.85% | +0.36 | -0.02 |

### Mechanics of Slippage in Bracket Execution:
In volatility-bracket trading, slippage does not act as a simple additive subtraction from final profits. When entry slippage increases from 0.05% to 0.10%, the execution price shifts higher:
$$P_{\text{entry}} = \text{Open} \times (1 + \text{slip})$$
Because bracket thresholds are tied to the fill price:
$$P_{\text{stop}} = P_{\text{entry}} - (\text{SL} \times \text{ATR})$$
a higher entry price establishes an elevated stop price. On sessions where price dips near the stop band, this shift causes intrabar stop-loss exits to trigger on sessions where they would have otherwise remained open under lower slippage assumptions. This prematurely terminates positions and alters subsequent trade sequences.

---

## 8. Seed Variability & Empirical Sensitivity

Across identical Development data, evaluating seeds 42, 43, 44 produced noticeable spread in multi-year outcomes:
- On `TCS.NS`, stitched returns ranged from **+10.60%** (Seed 42) to **+41.86%** (Seed 44).
- On `INFY.NS`, stitched returns spanned **+0.47%** (Seed 42) to **+27.88%** (Seed 44).
- On `RELIANCE.NS`, performance spanned **-6.58%** (Seed 42) to **+5.18%** (Seed 43).

*Interpretation*: With a budget of 30 individuals across 10 generations, NSGA-II exhibits empirical sensitivity to random initialization. The resulting chromosomes vary in entry thresholds and holding durations, illustrating that optimization runs should be reported with seed distributions rather than single isolated outcomes.

---

## 9. Audit Artifacts & Verification

The following verified artifacts document all experimental outputs:
- **Audit Companion**: [campaign_audit.json](file:///u:/MInor-Specialization/reports/experiments/results/campaign_audit.json) (environment, package versions, command lines, code hashes, and partition index ranges).
- **Raw Campaign Results**: [campaign_raw_results.json](file:///u:/MInor-Specialization/reports/experiments/results/campaign_raw_results.json)
- **Per-Fold Summary Metrics CSV**: [fold_summary_metrics.csv](file:///u:/MInor-Specialization/reports/experiments/results/fold_summary_metrics.csv)
- **Stitched Aggregate Metrics CSV**: [stitched_aggregate_metrics.csv](file:///u:/MInor-Specialization/reports/experiments/results/stitched_aggregate_metrics.csv)
- **Paired Annual Comparisons CSV**: [paired_annual_comparisons.csv](file:///u:/MInor-Specialization/reports/experiments/results/paired_annual_comparisons.csv)
- **Publication Figures**:
  - [stitched_equity_curves.png](file:///u:/MInor-Specialization/reports/experiments/figures/stitched_equity_curves.png)
  - [underwater_drawdowns.png](file:///u:/MInor-Specialization/reports/experiments/figures/underwater_drawdowns.png)
  - [risk_return_scatter.png](file:///u:/MInor-Specialization/reports/experiments/figures/risk_return_scatter.png)
  - [seed_variability_boxplots.png](file:///u:/MInor-Specialization/reports/experiments/figures/seed_variability_boxplots.png)

---

## 10. Conclusion & Honest Scientific Assessment

1. **Comparative Capital Growth**:
   Across the 6-year evaluation period, Buy & Hold compounded higher final wealth than the Full Hybrid strategy on all three equities.
2. **Downside Risk Profile**:
   The Full Hybrid strategy demonstrated lower annual maximum drawdowns than Buy & Hold in 94.4% of folds, operating with an average end-of-day capital exposure between 15% and 55%.
3. **Model Contribution**:
   Out-of-sample directional AUC averaged 0.5324. Technical parameter search without ML signals produced comparable or higher total returns across all three equities.
4. **Context of Prior Single-Split Observations**:
   The isolated SPY split inspected during initial development represents a single favorable market partition. It does not reflect walk-forward performance in multi-year Indian equity markets.
