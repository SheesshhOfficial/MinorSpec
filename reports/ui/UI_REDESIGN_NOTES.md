# Streamlit UI Redesign & Architecture Notes

**Task ID:** P004 / P004-R1  
**Date:** 15 October 2026  
**Status:** COMPLETE  
**Primary Deliverables:** `app.py`, `ui/styles.py`, `ui/formatting.py`, `ui/charts.py`, `ui/metadata.py`, `.streamlit/config.toml`, `tests/test_ui_app.py`, `reports/baseline/smoke_apptest.py`, `reports/ui/*.png`

---

## 1. Design Decisions & Visual Aesthetics

1. **Restrained Dark Quantitative Theme:**
   - **Deep Navy Base:** `#0B1020` app background.
   - **Panel Background:** `#131D30` card and container backgrounds.
   - **Fine Borders:** `#263247` subtle structural dividers.
   - **Primary Accent:** `#00D2D3` (cyan) and `#0EA5E9` (teal) for primary highlights, focus states, and Pareto development solutions.
   - **Financial Truthfulness:** Emerald (`#10B981`) exclusively for positive returns/gains, Coral (`#F43F5E`) for losses/drawdowns, Amber (`#F59E0B`) for warnings/exploratory status. Negative results are never disguised as positive.

2. **Clean Typography & Information Hierarchy:**
   - Compact title bar: **Evolutionary Market Lab** with subtle badge and explanatory subtitle. Full formal academic project title is placed respectfully in the Methodology tab.
   - Replaced raw JSON / monospace text blocks with structured HTML chips displaying: Asset, Test Horizon dates, Algorithm settings, and Evaluation Protocol.
   - Native Streamlit widgets preserved without brittle CSS overrides or custom JS injection.

3. **Execution Lifecycle & State Safety:**
   - **Initial First-Run State:** On launch, an intuitive 3-step visual onboarding guide is displayed without triggering expensive computation automatically.
   - **Explicit Run Trigger:** Computation runs only when clicking **Run Experiment** (sidebar) or **Start Baseline Experiment on RELIANCE.NS** (main page). Both paths execute with active sidebar settings and clear prior errors.
   - **Unapplied Edits Warning:** If sidebar parameters are modified after an execution, a prominent amber banner warns that displayed charts reflect the previously executed run until the user clicks **Run Experiment**.
   - **Failure Resilience:** If a run encounters a network or pipeline error, an alert banner is shown while preserving the previously successful results in memory.
   - **Strict Input Validation:** Custom ticker input rejects empty strings, leading/trailing whitespace, and strings with spaces or punctuation cleanly with an immediate error banner, avoiding silent fallback to dropdown selections.

4. **Currency & Unit Formatting Integrity:**
   - Indian NSE assets (`.NS`, `^NSEI`): Formatted with Indian Rupee symbol (`₹`) and comma separators (e.g. `₹100,000.00`).
   - US assets (`SPY`, `AAPL`, `QQQ`): Formatted in USD (`$`).
   - Custom / unknown tickers: Displayed in neutral units (`units`).
   - No hardcoded dollar signs for Indian equities.

---

## 2. Workspace Navigation (5 Structured Tabs)

1. **📊 Overview:**
   - 5 KPI summary cards: Primary Strategy Return (with $\pm$ pp difference vs benchmark), Benchmark Buy & Hold Return, Maximum Drawdown (with benchmark baseline), Annualized Sharpe Ratio, and Completed Trades / Win Rate.
   - Two-panel responsive Plotly chart: Cumulative Portfolio Equity Growth vs. Buy & Hold benchmark on Panel 1; Underwater Drawdown Profile on Panel 2.
   - Plain-language financial reading guide explaining next-bar timing, slippage friction, and opportunity costs.

2. **🎯 Strategy Explorer:**
   - Marker-only Pareto frontier scatter plot eliminating overlapping label clutter. Subplot top margin widened and chart title removed to prevent title/legend collision.
   - Marker annotations positioned center-top and center-bottom to prevent right-edge bounding clipping.
   - Star highlight on the **Frozen Primary Strategy** (selected strictly on Development partition).
   - Short candidate selector options (`Strategy #ID (Primary)` or `Strategy #ID`) preventing dropdown text truncation.
   - Dedicated inspected candidate metric card displaying Dev Sharpe, Dev MDD, Test Sharpe, and Test MDD.
   - Read-only 7-gene chromosome parameter table detailing parameter names, evolved values, search bounds, and plain-English economic purpose. Max holding period formatted as `int(v) bars` matching simulator kernel truncation.

3. **🧠 Model Insights:**
   - Tier 1 LightGBM classifier validation diagnostics: Validation AUC, Directional Accuracy, and Brier Score.
   - Top 10 Influential Features horizontal bar chart sorted by split gain importance with human-friendly feature axis labels (`10-Day SMA Distance`, `14-Day RSI`, `Average True Range %`, etc.) and technical indicator IDs in tooltip hover.
   - Comprehensive 20-feature technical indicator glossary grouped into Trend, Momentum, Volatility, and Volume/Regime categories.

4. **📜 Trade Journal:**
   - Prominent candidate identity status banner indicating whether the displayed trades belong to the frozen primary benchmark or an exploratory candidate.
   - Simulated trade execution audit log displaying Entry Date, Exit Date, Entry Price, Exit Price, Net P&L, Trade Return %, Holding Bars, and Exit Reason with proper currency formatting.
   - Filter controls for trade outcome (Profitable / Loss) and exit reason with informative warning banner if filter matches zero trades.
   - Separate, clearly labeled export buttons: **Download Complete Trade Log (CSV)** vs. **Download Filtered Trade Log (CSV)**.
   - Graceful zero-trade candidate handling with dedicated informational message.

5. **📖 Methodology:**
   - Detailed timeline of the 4 chronological partitions (`Train` ~50% $\rightarrow$ `Val` ~15% $\rightarrow$ `Dev` ~15% $\rightarrow$ `Test` ~20%) with 3-bar purged gap horizons.
   - State exact interactive candidate selection rule: $\ge 3$ trade filter on Dev partition, highest raw Sharpe, with fallback to highest raw Sharpe overall if no candidate achieves $\ge 3$ trades.
   - Close-normalized Buy & Hold benchmark documentation matching the execution engine.
   - Explicit academic distinction between the interactive single-split workspace and the multi-year rolling 2020–2025 campaign (18 asset-year folds evaluated across 3 random seeds = 54 fold-seed runs) documented in the research paper.
   - Blank supervisor field in academic project metadata.

---

## 3. Visual QA & Multi-Device Responsive Inspection

Browser subagent executed complete visual QA across Desktop, Tablet, and Mobile resolutions:
- **Desktop (1440 × 900):** Full side-by-side layout, uncluttered Pareto scatter chart, high-contrast typography, and aligned KPI cards.
- **Tablet (1024 × 768):** Native 2-column stacking, readable dataframes without horizontal viewport overflow.
- **Mobile (390 × 844):** Single-column stacked layout, collapsible sidebar, accessible touch targets, and full horizontal responsiveness.

Screenshots captured and archived in `reports/ui/`:
1. `strategy_explorer_final.png`: Strategy Explorer tab with clean Pareto frontier, unclipped marker labels, and shortened candidate selector options.
2. `model_insights_final.png`: Model Insights tab with friendly feature axis names and validation diagnostics.
3. `trade_journal_final.png`: Trade Journal tab with candidate identity banner, formatted currency columns, and separate CSV download buttons.
4. `methodology_final.png`: Methodology tab documenting exact selection rule, partition fractions, and blank supervisor field.
5. `responsive_tablet_final.png`: Responsive tablet layout at 1024x768.
6. `responsive_mobile_final.png`: Responsive mobile layout at 390x844.

---

## 4. Verification & Regression Suite

- **Full Pytest Suite:** `python -m pytest tests/ -v` $\rightarrow$ **35 passed** (28 core research tests + 7 deterministic offline UI unit/integration tests).
- **Deterministic UI Tests:** `python -m pytest tests/test_ui_app.py -v` $\rightarrow$ **7 passed** with mocked backend fixtures, cache-clearing isolation, and blocked data fetcher/loader network calls.
- **Streamlit AppTest Smoke Test:** `python -m reports.baseline.smoke_apptest` $\rightarrow$ **PASSED** (0 exceptions, candidate drilldown verified, evidence saved to `reports/baseline/apptest_smoke_evidence.json`).
- **Research Source Hashes:** Verified 100% invariant across all files in `src/`.
