# 5-Minute Demonstration Sequence & Oral Defense (Viva Voce) Guide

Task ID: P003-R1  
Date: 12 October 2026  
Status: DEFENSE PREPARATION GUIDE (With Bounded Scientific Claims)  
Authors: Ashish Ranjan, Khuushi Maheshwari, Satyanarayan H.  
Institution: Manipal Institute of Technology, Department of Computer Science  

This guide prepares the student team for their capstone presentation, live software demonstration, and oral defense before the departmental evaluation committee.

---

## Part 1: Five-Minute Live Demonstration Walkthrough

When presenting before faculty examiners, execute this structured sequence:

### Minute 0:00 – 1:00: Problem Context & Architectural Overview
- **Opening Statement**: *"Respected committee members, our project addresses a fundamental challenge in financial artificial intelligence: while machine learning models can be trained to predict stock price movements, directional predictions alone do not protect portfolio capital without dynamic risk management. We engineered a Two-Tier Computational Intelligence architecture combining a LightGBM gradient-boosted directional classifier with an NSGA-II multi-objective evolutionary strategy optimizer."*
- **Show Architecture Diagram**: Open `reports/submission/figures/system_architecture.png` and explain the 4 blocks: Data & 20 Stationary Technical Indicators $\to$ Tier 1 LightGBM Predictor $\to$ Tier 2 NSGA-II 7-Gene Optimizer $\to$ Causal Execution Simulator.

### Minute 1:00 – 2:00: Offline Test Verification & Causal Simulator Mechanics
- **Run the Pytest Suite**:
  ```bash
  python -m pytest tests/ -v
  ```
- **Narrate**: *"Notice our comprehensive test suite passing in under 16 seconds. We rigorously enforce execution reality: trading signals generated at bar $t$ Close execute at bar $t+1$ Open with slippage; intrabar stop-loss conflicts are resolved conservatively; opening gaps are penalized; and label horizons are purged across split boundaries ($H=3$) to prevent temporal leakage."*

### Minute 2:00 – 3:30: Interactive Dashboard Demonstration
- **Launch Streamlit Cockpit**:
  ```bash
  python -m streamlit run app.py
  ```
- **Interact with Cockpit**:
  1. Show the **Pareto Frontier Plot**: Explain the non-dominated trade-off between maximizing Annualized Sharpe Ratio ($f_1$) and minimizing Maximum Drawdown ($f_2$).
  2. Select an aggressive strategy vs a conservative strategy from the Pareto front and demonstrate how the equity curve shifts.
  3. Show the **Trade Audit Log**: Point out entry prices adjusted for slippage, ATR dynamic stop-losses, and regime-conditional capital allocations.

### Minute 3:30 – 5:00: Honest Scientific Findings & Multi-Year Walk-Forward Campaign
- **Open Figures in `reports/submission/figures/`**:
  1. Show `stitched_equity_curves.png` and `underwater_drawdowns.png`.
  2. **Deliver the Core Scientific Takeaway**: *"Unlike typical academic projects claiming 99% accuracy or unrealistic market-beating returns, our retrospective 6-year walk-forward evaluation on NSE large-caps (`RELIANCE.NS`, `TCS.NS`, `INFY.NS`) produced nuanced, honest findings. LightGBM achieves an average AUC of 0.5324. While the hybrid strategy significantly reduced annual drawdowns in 17 of 18 folds (94.4%), Buy & Hold compounded higher final wealth across all three equities because sitting in cash during major expansions sacrificed upside participation. Our contribution is scientific rigor, causal simulation integrity, and total reproducibility."*

---

## Part 2: Comprehensive Viva Voce Questions & Model Answers

### Q1: What is the core rationale for combining LightGBM with NSGA-II rather than using a single end-to-end Reinforcement Learning (RL) agent?
**Answer**:
Deep Reinforcement Learning agents in financial markets suffer from extreme sample inefficiency, non-stationary policy degradation, and black-box reward hacking where agents learn brittle timing patterns that collapse out-of-sample. Our two-tier CI architecture decouples the problem into two specialized domains:
1. **Statistical Inference**: LightGBM is trained solely to estimate conditional forward probabilities $\hat{P}(\text{Up})$ from stationary tabular indicators, where tree boosting excels.
2. **Metaheuristic Policy Search**: NSGA-II searches non-convex risk parameters (stop-loss, take-profit multipliers, position sizing) directly on the portfolio equity curve. Decoupling ensures transparent, auditable rules where every trade exit is attributable to a specific dynamic threshold.

### Q2: How does your experimental framework prevent temporal leakage (look-ahead bias)?
**Answer**:
We enforce four strict safeguards:
1. **Chronological Splitting**: We use non-overlapping chronological partitions (Train $\to$ Validation $\to$ Development $\to$ Test) with zero random shuffling.
2. **Label Horizon Purging**: Because our target is a 3-day forward return ($H=3$), we purge the final 3 bars of the training and validation sets so that labels never overlap into subsequent partitions.
3. **Execution Timing**: Signals generated at bar $t$ Close execute strictly at bar $t+1$ Open with bid-ask slippage. Same-bar fill prices are prohibited.
4. **Causal Prefix Context**: The first trade on test bar 0 uses probability and indicator signals computed on the final bar of the development partition ($t=-1$), ensuring unbroken causal continuity.

### Q3: What exact transaction costs did you apply in your simulator?
**Answer**:
We applied standard transaction friction of 0.05% commission plus 0.05% slippage **per side** (approximately 10 basis points per side, or 20 basis points round-trip). In our sensitivity analysis, we evaluated doubled friction of 0.10% commission plus 0.10% slippage per side (approximately 20 basis points per side, or 40 basis points round-trip).

### Q4: Your LightGBM model achieves an average test AUC of 0.5324. How should we interpret this?
**Answer**:
In liquid equity markets operating under Weak-form Market Efficiency, daily return series have extremely low signal-to-noise ratios. An AUC of 0.5324 represents a modest statistical edge (accuracy of 52.68% vs training prior 52.66%). Rather than fabricating high accuracy through data snooping or look-ahead leakage, our study documents that machine learning classifiers face significant out-of-sample degradation, and that trading rule success depends far more on risk-containment mechanics than directional forecasting.

### Q5: Why did Buy & Hold achieve higher 6-year compound returns than your Hybrid strategy on all three assets?
**Answer**:
Because our hybrid strategy prioritizes capital preservation:
1. When LightGBM probability is below the evolved entry hurdle ($p_{\text{entry}} \in [0.52, 0.85]$), the portfolio remains in cash.
2. In strong bull markets (e.g., post-COVID recovery in 2020-2021), sitting in cash incurs severe opportunity cost.
3. However, during market corrections (such as 2022 and 2023), the hybrid strategy outperformed Buy & Hold on multiple assets by avoiding drawdowns. Over 6 years, the compound cost of missing bull runs outweighed the drawdown protection, resulting in lower cumulative wealth.

### Q6: Why did INFY.NS have a higher 6-year maximum drawdown for the Hybrid strategy than Buy & Hold, despite lower drawdown in 5 of the 6 individual years?
**Answer**:
This highlights the mathematical difference between annual drawdowns and multi-year compounded underwater curves. In 2022, INFY suffered a tech sector downturn; while the Hybrid lost less than Buy & Hold that year (-7.10% vs -18.54%), the Hybrid subsequently entered the 2024–2025 period with lower accumulated capital. The compounded multi-year peak-to-trough drop from its historical peak reached 37.16% for the Hybrid vs 35.93% for Buy & Hold. This demonstrates that annual drawdown dampening does not guarantee lower multi-year peak-to-trough portfolio risk.

### Q7: What are the main limitations of this research?
**Answer**:
Our study is bound by four key limitations:
1. **Asset Universe**: We evaluated three large-cap surviving equities (`RELIANCE.NS`, `TCS.NS`, `INFY.NS`) individually; we did not model cross-asset portfolio allocation or survivorship adjustments.
2. **Adjusted Price Data**: We used split- and dividend-adjusted OHLC data from Yahoo Finance rather than point-in-time exchange tick books.
3. **Overnight Capital Exposure**: Capital exposure is measured as session-close invested value divided by equity, which acts as an overnight commitment proxy and omits intraday capital utilization.
4. **Retrospective Evaluation**: The walk-forward protocol was refined through retrospective audit corrections (versioned in `protocol_correction.json`), rather than pre-registered live forward trading.
