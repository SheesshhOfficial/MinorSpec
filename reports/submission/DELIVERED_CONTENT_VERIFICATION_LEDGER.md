# Delivered Document Content Verification Ledger

Task ID: P003-R2  
Date: 12 October 2026  
Status: ALL 155 DELIVERED-DOCUMENT EXTRACTIONS MATCH ARTIFACT TRUTH  
Verification Engine: `scripts/verify_delivered_documents.py`  
Audited Delivered Deliverables: `reports/submission/RESEARCH_PAPER_DRAFT.docx`, `reports/submission/COLLEGE_PROJECT_REPORT.docx`  

This ledger records the automated, direct inspection of the *actual delivered Microsoft Word DOCX documents*. Every table cell and quantitative prose assertion was parsed out of the final compiled document binaries and checked against ground-truth CSV/JSON research artifacts.

---

## Summary of Extraction Checks

- **Total Delivered-Content Assertions Checked**: 155
- **Passed Checks**: 155
- **Failed Checks**: 0

| Deliverable | Location | Metric / Claim | Extracted Document Value | Artifact Benchmark | Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 1 | RELIANCE.NS Mean AUC | 0.5469 | 0.5468755676862941 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 1 | RELIANCE.NS Min AUC | 0.4415 | 0.4414787798408488 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 1 | RELIANCE.NS Max AUC | 0.6246 | 0.6246199557766722 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 1 | RELIANCE.NS Test Accuracy (%) | 52.01 | 52.006956396022865 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 1 | RELIANCE.NS Base Accuracy (%) | 52.21 | 52.214329667912274 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 1 | RELIANCE.NS Brier Score | 0.2494 | 0.24939537218196053 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 2 | TCS.NS Mean AUC | 0.5304 | 0.5303926473074198 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 2 | TCS.NS Min AUC | 0.4774 | 0.4773587456069206 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 2 | TCS.NS Max AUC | 0.6182 | 0.6181946025580928 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 2 | TCS.NS Test Accuracy (%) | 50.91 | 50.91212475459105 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 2 | TCS.NS Base Accuracy (%) | 50.78 | 50.77937543393733 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 2 | TCS.NS Brier Score | 0.2516 | 0.2516474250709482 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 3 | INFY.NS Mean AUC | 0.5199 | 0.5199212365900918 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 3 | INFY.NS Min AUC | 0.4509 | 0.4509105846912227 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 3 | INFY.NS Max AUC | 0.5766 | 0.5765746934225194 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 3 | INFY.NS Test Accuracy (%) | 55.12 | 55.12460005068643 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 3 | INFY.NS Base Accuracy (%) | 54.99 | 54.98854562891773 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 1 (Page 4) Row 3 | INFY.NS Brier Score | 0.2493 | 0.24928631195692283 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 1 | RELIANCE.NS Mean AUC | 0.5469 | 0.5468755676862941 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 1 | RELIANCE.NS Min AUC | 0.4415 | 0.4414787798408488 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 1 | RELIANCE.NS Max AUC | 0.6246 | 0.6246199557766722 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 1 | RELIANCE.NS Test Accuracy (%) | 52.01 | 52.006956396022865 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 1 | RELIANCE.NS Base Accuracy (%) | 52.21 | 52.214329667912274 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 1 | RELIANCE.NS Brier Score | 0.2494 | 0.24939537218196053 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 2 | TCS.NS Mean AUC | 0.5304 | 0.5303926473074198 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 2 | TCS.NS Min AUC | 0.4774 | 0.4773587456069206 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 2 | TCS.NS Max AUC | 0.6182 | 0.6181946025580928 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 2 | TCS.NS Test Accuracy (%) | 50.91 | 50.91212475459105 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 2 | TCS.NS Base Accuracy (%) | 50.78 | 50.77937543393733 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 2 | TCS.NS Brier Score | 0.2516 | 0.2516474250709482 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 3 | INFY.NS Mean AUC | 0.5199 | 0.5199212365900918 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 3 | INFY.NS Min AUC | 0.4509 | 0.4509105846912227 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 3 | INFY.NS Max AUC | 0.5766 | 0.5765746934225194 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 3 | INFY.NS Test Accuracy (%) | 55.12 | 55.12460005068643 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 3 | INFY.NS Base Accuracy (%) | 54.99 | 54.98854562891773 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.1 (Page 10) Row 3 | INFY.NS Brier Score | 0.2493 | 0.24928631195692283 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 1 | RELIANCE B&H Return (%) | 128.74 | 128.73967932876425 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 1 | RELIANCE B&H CAGR (%) | 15.05 | 15.0527884001913 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 1 | RELIANCE B&H MaxDD (%) | 44.08 | 44.08284239250412 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 1 | RELIANCE B&H Terminal ₹ | 228740.0 | 228739.67932876424 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 2 | RELIANCE Hybrid Median Return (%) | -0.35 | -0.34801721689629 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 2 | RELIANCE Hybrid Median MaxDD (%) | 23.01 | 23.01406915305964 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 2 | RELIANCE Hybrid Median Terminal ₹ | 99652.0 | 99651.98278310373 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 5 | TCS B&H Return (%) | 65.13 | 65.13352980755691 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 5 | TCS B&H CAGR (%) | 8.87 | 8.87201611718979 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 5 | TCS B&H MaxDD (%) | 34.57 | 34.57353915960921 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 5 | TCS B&H Terminal ₹ | 165134.0 | 165133.52980755692 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 6 | TCS Hybrid Median Return (%) | 25.6 | 25.60006380742787 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 6 | TCS Hybrid Median MaxDD (%) | 28.66 | 28.663906222639202 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 6 | TCS Hybrid Median Terminal ₹ | 125600.0 | 125600.06380742788 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 9 | INFY B&H Return (%) | 152.78 | 152.78290071028385 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 9 | INFY B&H CAGR (%) | 17.02 | 17.01812623740868 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 9 | INFY B&H MaxDD (%) | 35.93 | 35.932328016635914 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 9 | INFY B&H Terminal ₹ | 252783.0 | 252782.90071028384 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 10 | INFY Hybrid Median Return (%) | 9.1 | 9.10306690233377 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 10 | INFY Hybrid Median MaxDD (%) | 37.16 | 37.15824633997054 | **PASS** |
| RESEARCH_PAPER_DRAFT | Table 2 (Page 5) Row 10 | INFY Hybrid Median Terminal ₹ | 109103.0 | 109103.06690233375 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 1 | RELIANCE B&H Return (%) | 128.74 | 128.73967932876425 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 1 | RELIANCE B&H CAGR (%) | 15.05 | 15.0527884001913 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 1 | RELIANCE B&H MaxDD (%) | 44.08 | 44.08284239250412 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 1 | RELIANCE B&H Terminal ₹ | 228740.0 | 228739.67932876424 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 2 | RELIANCE Hybrid Median Return (%) | -0.35 | -0.34801721689629 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 2 | RELIANCE Hybrid Median MaxDD (%) | 23.01 | 23.01406915305964 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 2 | RELIANCE Hybrid Median Terminal ₹ | 99652.0 | 99651.98278310373 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 5 | TCS B&H Return (%) | 65.13 | 65.13352980755691 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 5 | TCS B&H CAGR (%) | 8.87 | 8.87201611718979 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 5 | TCS B&H MaxDD (%) | 34.57 | 34.57353915960921 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 5 | TCS B&H Terminal ₹ | 165134.0 | 165133.52980755692 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 6 | TCS Hybrid Median Return (%) | 25.6 | 25.60006380742787 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 6 | TCS Hybrid Median MaxDD (%) | 28.66 | 28.663906222639202 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 6 | TCS Hybrid Median Terminal ₹ | 125600.0 | 125600.06380742788 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 9 | INFY B&H Return (%) | 152.78 | 152.78290071028385 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 9 | INFY B&H CAGR (%) | 17.02 | 17.01812623740868 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 9 | INFY B&H MaxDD (%) | 35.93 | 35.932328016635914 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 9 | INFY B&H Terminal ₹ | 252783.0 | 252782.90071028384 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 10 | INFY Hybrid Median Return (%) | 9.1 | 9.10306690233377 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 10 | INFY Hybrid Median MaxDD (%) | 37.16 | 37.15824633997054 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.2 (Page 10) Row 10 | INFY Hybrid Median Terminal ₹ | 109103.0 | 109103.06690233375 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.4 Row 1 | RELIANCE Seed 42 1x Ret | -6.58 | -6.58 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.4 Row 1 | RELIANCE Seed 42 2x Ret | -25.41 | -25.41 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.4 Row 1 | RELIANCE Seed 42 Diff | -18.83 | -18.83 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.4 Row 2 | TCS Seed 43 1x Ret | 25.6 | 25.6 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.4 Row 2 | TCS Seed 43 2x Ret | 19.61 | 19.61 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.4 Row 2 | TCS Seed 43 Diff | -5.99 | -5.99 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.4 Row 3 | INFY Seed 44 1x Ret | 27.88 | 27.88 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.4 Row 3 | INFY Seed 44 2x Ret | -7.97 | -7.97 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.4 Row 3 | INFY Seed 44 Diff | -35.85 | -35.85 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 1 | RELIANCE.NS 2020 B&H | 32.3 | 32.3 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 1 | RELIANCE.NS 2020 Hyb | 0.0 | 0.0 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 1 | RELIANCE.NS 2020 Diff | -32.3 | -32.3 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 2 | RELIANCE.NS 2022 B&H | 7.84 | 7.84 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 2 | RELIANCE.NS 2022 Hyb | -12.07 | -12.07 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 2 | RELIANCE.NS 2022 Diff | -19.9 | -19.9 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 3 | RELIANCE.NS 2023 B&H | 10.0 | 10.0 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 3 | RELIANCE.NS 2023 Hyb | 12.0 | 12.0 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 3 | RELIANCE.NS 2023 Diff | 2.0 | 2.0 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 4 | TCS.NS 2022 B&H | -12.13 | -12.13 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 4 | TCS.NS 2022 Hyb | 4.41 | 4.41 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 4 | TCS.NS 2022 Diff | 16.55 | 16.55 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 5 | TCS.NS 2023 B&H | 20.24 | 20.24 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 5 | TCS.NS 2023 Hyb | 24.16 | 24.16 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 5 | TCS.NS 2023 Diff | 3.92 | 3.92 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 6 | INFY.NS 2022 B&H | -18.54 | -18.54 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 6 | INFY.NS 2022 Hyb | -7.1 | -7.1 | **PASS** |
| COLLEGE_PROJECT_REPORT | Table 6.3 Row 6 | INFY.NS 2022 Diff | 11.44 | 11.44 | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | GBDT max rounds | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | GBDT max rounds | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Early stopping rounds | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Early stopping rounds | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Learning rate | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Learning rate | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Max tree depth | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Max tree depth | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Num leaves | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Num leaves | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Crossover probability | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Crossover probability | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | SBX distribution index | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | SBX distribution index | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Polynomial mutation per-gene prob | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Polynomial mutation per-gene prob | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Mutation distribution index | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Mutation distribution index | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Inactivity Sharpe penalty | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Inactivity Sharpe penalty | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Inactivity MaxDD floor | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Inactivity MaxDD floor | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Standard friction per side | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Standard friction per side | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Standard friction RT | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Standard friction RT | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Doubled friction per side | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Doubled friction per side | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Doubled friction total per side | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Doubled friction total per side | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Doubled friction RT | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Doubled friction RT | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Drawdown reduction folds | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Drawdown reduction folds | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | B&H outperformance folds | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | B&H outperformance folds | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Positive hybrid folds | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Positive hybrid folds | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Hybrid outperformance folds | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Hybrid outperformance folds | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Diagnostic hybrid wins | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Diagnostic hybrid wins | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Diagnostic exposure B&H wins | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Diagnostic exposure B&H wins | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Diagnostic cash ties | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Diagnostic cash ties | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Prose Body | Diagnostic exposure lower DD | True | True | **PASS** |
| COLLEGE_PROJECT_REPORT | Prose Body | Diagnostic exposure lower DD | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Section 5.2 | Figure 2 reference (not Figure 3) | True | True | **PASS** |
| RESEARCH_PAPER_DRAFT | Figure Cross-Ref | No stray Figures 2 and 3 | True | True | **PASS** |
