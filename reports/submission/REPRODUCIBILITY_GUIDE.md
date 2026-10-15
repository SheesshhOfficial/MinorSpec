# Submission Package Reproducibility Guide & Environment Specification

Task ID: P003-R1  
Date: 12 October 2026  
Status: VERIFIED REPRODUCIBLE PACKAGE (With Disclosed Network Boundaries)  
Authors: Ashish Ranjan, Khuushi Maheshwari, Satyanarayan H.  
Institution: Manipal Institute of Technology, Department of Computer Science  

This document provides step-by-step instructions for reproducing all empirical results, running offline regression suites, executing the automated numerical verification script, and launching the interactive Streamlit dashboard.

---

## 1. Environment & Pinned Dependencies

The experimental campaign and document generation were executed and verified on the following host system:

- **Host Operating System**: Windows 11 Home / Pro (build 10.0.26300, 64-bit AMD64)
- **Observed Python Runtime**: Python 3.13.14 (tags/v3.13.14:fd17997)
- **Minimum Python Requirement**: Python $\ge 3.10$
- **Observed Core Libraries** (from host environment):
  - `lightgbm == 4.7.0` (Gradient-boosted decision tree classifier)
  - `numba == 0.66.0` (JIT-compiled backtest acceleration)
  - `numpy == 2.3.2` (Array computation)
  - `pandas == 3.0.2` (Time-series dataframes)
  - `scikit-learn == 1.9.0` (ROC-AUC, accuracy, and Brier metrics)
  - `matplotlib == 3.10.0` (Publication figure generation)
  - `streamlit == 1.50+` (Interactive web dashboard)
  - `pytest == 9.1.1` (Automated testing framework)
  - `python-docx == 1.2.0` (DOCX document compilation)
  - `pymupdf / fitz == 1.25.3` (PDF page rendering and visual inspection)
  - `pywin32 / win32com` (Microsoft Word COM automation for PDF compilation)

*Note on Dependency Installation*: Dependencies in `requirements.txt` use flexible lower bounds (e.g., `lightgbm>=4.0.0`, `numba>=0.59.0`). To ensure exact bit-level reproduction of evolutionary numbers, use the observed library versions listed above.

---

## 2. Distinction Between Offline Campaign & Dashboard Network Boundaries

Please note the crucial architectural separation:

1. **The Retrospective Walk-Forward Campaign & Audit (STRICTLY OFFLINE)**:
   All campaign executions (`src.rolling_runner`), plotting (`src.experiment_plots`), and verification scripts (`scripts/audit_campaign_reproducibility.py`, `scripts/verify_numerical_claims.py`) execute **strictly offline** against immutable parquet snapshots stored in `reports/experiments/inputs/`. In the audit script, `yfinance` download functions are monkeypatched to throw runtime exceptions if any network request is attempted.
2. **The Streamlit Interactive Dashboard (`app.py`)**:
   The interactive cockpit is designed for interactive exploration. If cached parquet files exist in `data/raw/` or `data/processed/`, it loads locally; however, its background data loader contains age-refreshing downloader mechanisms that may attempt remote Yahoo Finance updates if cache files are older than 24 hours.

---

## 3. Step-by-Step Reproduction Commands

### Command 1: Execute Automated Regression Test Suite
Runs all 28 automated tests verifying execution timing, intrabar priority, gap mechanics, split purging, and offline artifact equality:
```bash
python -m pytest tests/ -v
```
*Expected Result*: `28 passed in ~16s` (exit code 0).

### Command 2: Execute Campaign-Wide Reproducibility Audit
Re-runs all 18 annual folds across all 3 seeds with active network blockers, asserting bit-level reproduction against saved raw results (`genes` atol $10^{-12}$, `equity` atol $10^{-7}$):
```bash
python scripts/audit_campaign_reproducibility.py
```
*Expected Result*: Evaluates 306 assertions; outputs `SUCCESS: ZERO MISMATCHES DETECTED` (exit code 0).

### Command 3: Execute Executable Data-to-Document Verification Script
Cross-verifies every single metric, table cell, and quantitative claim in the manuscript drafts directly against artifact CSVs and JSONs:
```bash
python scripts/verify_numerical_claims.py
```
*Expected Result*: Evaluates 47 quantitative assertions; outputs `VERIFICATION SUCCESS: All 47 quantitative assertions PASSED!` (exit code 0). Outputs machine-readable ledger to `reports/submission/NUMERICAL_VERIFICATION_LEDGER.json`.

### Command 4: Compile Submission Documents and Render PDFs
Generates `RESEARCH_PAPER_DRAFT.docx`, `COLLEGE_PROJECT_REPORT.docx`, and compiles matching PDFs via Microsoft Word COM automation:
```bash
python scripts/generate_paper_draft.py
python scripts/generate_college_report.py
```
*Expected Result*: Generates 8-page Research Paper PDF and 13-page College Project Report PDF in `reports/submission/`.

### Command 5: Run Streamlit Application Smoke Test
```bash
python -m reports.baseline.smoke_apptest
```
*Expected Result*: Loads in ~8s with 0 exceptions (exit code 0).

---

## 4. Evidence & Deliverable Artifact Map

```
reports/
├── experiments/
│   ├── protocol.json                           # Original experiment protocol
│   ├── protocol_correction.json                # Versioned protocol corrections (v1.1.0, CORR-01 to CORR-07)
│   ├── inputs/
│   │   ├── manifest.json                       # SHA-256 hashes of immutable Parquet snapshots
│   │   ├── RELIANCE.NS.parquet                 # Historical daily OHLCV snapshot (2000-2025)
│   │   ├── TCS.NS.parquet                      # Historical daily OHLCV snapshot (2004-2025)
│   │   └── INFY.NS.parquet                     # Historical daily OHLCV snapshot (2000-2025)
│   ├── results/
│   │   ├── campaign_audit.json                 # Comprehensive provenance & partition accounting
│   │   ├── campaign_raw_results.json           # Raw per-fold JSON results (SHA-256: 255d6c18...)
│   │   ├── fold_summary_metrics.csv            # Annual fold summary metrics (18 rows)
│   │   ├── stitched_aggregate_metrics.csv      # Multi-year compound metrics (48 rows)
│   │   └── paired_annual_comparisons.csv       # Paired annual strategy differences (18 rows)
│   └── figures/                                # Static PNG publication figures
└── submission/
    ├── RESEARCH_PAPER_DRAFT.docx               # Academic paper draft (editable Word document)
    ├── RESEARCH_PAPER_DRAFT.pdf                # Academic paper draft (8-page compiled PDF)
    ├── COLLEGE_PROJECT_REPORT.docx             # College capstone project report (editable Word document)
    ├── COLLEGE_PROJECT_REPORT.pdf              # College capstone project report (13-page compiled PDF)
    ├── REFERENCE_LEDGER.md                     # Verified academic primary sources & bounds ledger
    ├── NUMERICAL_VERIFICATION_LEDGER.md        # Detailed quantitative data-to-document ledger
    ├── NUMERICAL_VERIFICATION_LEDGER.json      # Machine-readable output of executable verification
    ├── SUBMISSION_CHECKLIST.md                 # Student editable placeholder checklist
    ├── REPRODUCIBILITY_GUIDE.md                # This reproduction guide
    ├── VIVA_DEFENSE_NOTES.md                   # 5-minute presentation guide & oral defense Q&A
    ├── SUBMISSION_MANIFEST.json                # Cryptographic SHA-256 manifest of deliverables
    └── figures/                                # Publication-grade high-resolution figures
```
