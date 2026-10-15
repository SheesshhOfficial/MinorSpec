# Hybrid Market Predictor and Evolutionary Strategy Research

## Goal and constraints
College submission and research paper, requested 12 October 2026 with a two-day deadline. Faculty algorithms and datasets are not specified. Retain LightGBM and custom NSGA-II as the research core. Prefer Indian NSE daily stock data if obtainable and suitable; otherwise use existing US data with an explicit explanation. This is a research simulator, not live trading.

## Architecture
Python; yfinance OHLCV and Parquet cache; pandas technical features; LightGBM three-bar direction classifier; seven-gene NSGA-II optimizing Sharpe and drawdown; Numba simulator; Streamlit and Plotly dashboard.

## Evidence policy
Existing README and report performance claims are unverified. Publish only results reproduced by a recorded command, dataset period, settings, seed, and saved artifacts. Distinguish measured risk metrics from optimizer penalties. Do not claim calibrated probabilities without calibration evidence, deployability, novelty, or guaranteed future performance. Report limitations honestly.

## Planned milestones
P001: reproducible baseline and validation repair, including NSE feasibility.
P002: reviewed experiment protocol, rolling temporal evaluation, benchmarks and ablations, saved results.
P003: paper, submission report, usable demo and reproducibility instructions based on approved evidence.

## Commands
Install with python -m pip install -r requirements.txt. Verify with python -m pytest tests. Launch with python -m streamlit run app.py. Existing experiment entry point: python -m src.walk_forward. Network-dependent checks must be identified separately from offline checks.

## Confirmed authors and affiliation
Authors in order: Ashish Ranjan; Khuushi Maheshwari; Satyanarayan H.
Institution: Manipal Institute of Technology.
Department/program: B.Tech – Computer Science.
Supervisor field must be blank, for user editing later. Other personal details are unspecified and must not be invented.

## Dashboard redesign request - 14 October 2026
User requested a more detailed professional UI. P004 authorizes Antigravity to redesign Streamlit presentation and explanations while preserving all approved research computation/data/artifacts. See coordination/CURRENT_TASK.md for exact scope and validation.
