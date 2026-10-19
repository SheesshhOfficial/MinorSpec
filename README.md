# Evolutionary Market Lab

A college research simulator combining a LightGBM three-bar direction classifier
with a seven-parameter NSGA-II trading-rule search and a Streamlit dashboard.
It evaluates historical strategies; it does not place orders or guarantee profit.

## Install and launch

Use Python 3.10 or later in a virtual environment. From the repository root:

```sh
python -m venv .venv
# Activate .venv using the command for your operating system.
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit. Windows users may also run `run_app.bat`
with the intended Python environment active. Package installation and fresh Yahoo
Finance data retrieval require internet access. A historical dataset is not a live
quote. Data-source outages and delisted/unsupported symbols can prevent a run.

## First demonstration

1. Select `RELIANCE.NS` (Reliance Industries). Other presets include TCS, Infosys,
   Nifty 50, SPY, QQQ, Apple, Microsoft and NVIDIA.
2. Set **Population** to 40 and **Generations** to 15. Population counts candidate rule sets, not shares.
3. Leave **Advanced → Seed** at 42. It controls the evolutionary search;
   the classifier's separate model seed stays fixed at 42.
4. For the bundled-data example, enable **Use saved historical data (offline)**.
   Click **Run Experiment**. Changing controls alone does not replace an existing
   successful run; run again to apply pending settings.
5. Read **Overview** for the frozen primary strategy, **Strategies** for
   candidate rules and development/test comparisons, **Model** for
   validation classification metrics, **Trades** for simulated executions
   and CSV downloads, and **Method** for assumptions.

The primary strategy is selected on development data. Browsing other candidates'
test results is exploratory and must not be represented as a fresh unbiased test.
Changing a search seed can change results; selecting the best test seed is itself
test-set tuning. The repaired dashboard benchmark is cost-adjusted buy-and-hold
from the first tradable Open to the last tradable Close, including commission and
slippage. This replaces the older dashboard's frictionless close-normalized line.

## Research protocols and evidence

The dashboard uses a single chronological train/validation/development/test split
with three-bar purge gaps. `python -m src.walk_forward --help` describes the same
single-split CLI; its historical filename does not mean rolling validation.

The separate rolling NSE campaign uses immutable inputs under
`reports/experiments/inputs/`, a checked SHA-256 manifest, and its recorded protocol.
See `reports/experiments/RESULTS.md` and
`reports/submission/REPRODUCIBILITY_GUIDE.md`. Archived figures and submissions are
historical evidence, not newly measured results after a software repair. They are
retained unchanged; do not relabel them as validation of current code.

Signals use immediately preceding-bar information and are checked at each next
bar open. Zero-volume bars do not execute orders; signals are reevaluated rather
than carried forward indefinitely. Daily-bar bracket assumptions apply. Costs include
commission and slippage. Daily OHLC bars cannot determine every intraday ordering
or real-world fill; the simulator uses conservative conflict rules. Model AUC,
directional accuracy and Brier score are validation measures, not trading win rate
or evidence of calibrated probabilities.

The archived plotting/audit entry points `python -m src.experiment_plots` and
`scripts/audit_campaign_reproducibility.py` read the original
`campaign_raw_results.json` (accounting v1). They are archival workflows, not
validation or plotting of new v2 runs. The repaired rolling runner writes
`campaign_raw_results_v2.json` and refuses to overwrite it; use `--output-dir`
for a new run. A full rolling research campaign must be rerun and its downstream
analysis explicitly adapted before publishing revised research conclusions.

## Verification

```sh
python -m pytest tests
```

The suite uses synthetic data, mocked UI runs and immutable research snapshots.
It should not need market-data downloads. Keep the complete repository's research
inputs and `campaign_raw_results.json` available: tests check historical evidence
integrity and repaired-run reproducibility. Corrected fee accounting can change
fresh equity, so old research equity is not an exact target for repaired runs.
A partial source-only copy cannot
run all archival tests. Numba speed checks depend on execution hardware.

Review `coordination/REPAIR_AUDIT_2026_10_19.md` for repair scope, executed checks
and remaining limitations. No test suite proves the absence of all defects or
future investment performance.
