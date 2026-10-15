# Codex review P001-R1 - 12 October 2026

Outcome: APPROVED for the research baseline. This approval verifies implementation and reproducibility, not scientific outperformance.

## Independent checks
- python -m pytest tests -q: 14 passed, one dateutil deprecation warning, 21.97s.
- Source confirms entry-day bracket activation, opening signal exit priority, previous-close entry eligibility and independent detailed metric computation.
- Both baseline JSON input hashes match current raw/processed Parquet files. Saved equity reproduces total return and drawdown; trade counts and summed net P&L match the final portfolio change.
- Two offline cached runs per asset reproduce full-precision selected genes (exact repeated arrays) and saved return/Sharpe/drawdown within absolute 1e-12. The review monkeypatched pipeline.fetch_and_cache_ticker to return a copy of the directly read cached DataFrame, ensuring no network refresh.
- python -m reports.baseline.smoke_apptest: zero initial/drill-down exceptions; 12 actual strategy choices; selection changed #1 to #2. Existing Streamlit width deprecation warnings are non-blocking.

## Measured baseline
RELIANCE.NS: test return 3.6193%, Sharpe 0.1357, max drawdown 14.7411%, 30 trades; same-asset buy-and-hold return 29.7561%, drawdown 27.1758%.
SPY: test return 12.6441%, Sharpe 0.3388, max drawdown 14.9797%, 54 trades; buy-and-hold return 89.1639%, drawdown 24.4964%.
These show lower drawdown alongside substantially lower return; no broad superiority claim is supported.

## Limitations to address in P002
Default CLI still auto-refreshes caches after one day: add an explicit immutable offline snapshot route. NSE probe infers causes of zero-volume bars and equates first TCS data date with IPO without evidence: remove those interpretations or verify with primary sources. Exclude potentially incomplete latest daily bars and audit actual usable history. Seed currently controls GA but model has hard-coded seed 42; expose distinct model/evolution seeds. Existing temporal test results have been inspected; later evaluation of those periods is retrospective research rather than an untouched final holdout.

Next task: P002, fixed rolling protocol across three NSE equities, realistic comparisons and ablations. No expanded hyperparameter search before evidence is reviewed.
