# Superseded Prototype Documentation Notice

> [!WARNING]
> **HISTORICAL NOTICE: SUPERSEDED INITIAL PROTOTYPE SPECIFICATION**
>
> This document (`reports/PROJECT_REPORT.md`) represents an early exploratory prototype report written during the initial conception phase of the project.
>
> The claims, speed metrics, deep learning references (e.g., PyTorch LSTMs, 35+ features, single-split US SPY runs, and unverified alpha assertions) contained in this legacy file have been **SUPERSEDED** by:
> 1. The formal retrospective walk-forward campaign evidence on Indian equities (`RELIANCE.NS`, `TCS.NS`, `INFY.NS`) in [`reports/experiments/RESULTS.md`](file:///u:/MInor-Specialization/reports/experiments/RESULTS.md).
> 2. The finalized comprehensive academic submission deliverables:
>    - **Research Paper Draft**: [`reports/submission/RESEARCH_PAPER_DRAFT.docx`](file:///u:/MInor-Specialization/reports/submission/RESEARCH_PAPER_DRAFT.docx) & [`.pdf`](file:///u:/MInor-Specialization/reports/submission/RESEARCH_PAPER_DRAFT.pdf)
>    - **College Project Report**: [`reports/submission/COLLEGE_PROJECT_REPORT.docx`](file:///u:/MInor-Specialization/reports/submission/COLLEGE_PROJECT_REPORT.docx) & [`.pdf`](file:///u:/MInor-Specialization/reports/submission/COLLEGE_PROJECT_REPORT.pdf)
>    - **Reproducibility Guide**: [`reports/submission/REPRODUCIBILITY_GUIDE.md`](file:///u:/MInor-Specialization/reports/submission/REPRODUCIBILITY_GUIDE.md)
>
> All evaluators and readers should refer to `reports/submission/` for verified facts, exact empirical metrics, and primary citations.

---

# A Multi-Objective Evolutionary and Machine Learning Hybrid Framework for Risk-Constrained Algorithmic Trading (Superseded Draft)

**Specialization**: Computational Intelligence  
**Authors**: Ashish Ranjan, Khuushi Maheshwari, Satyanarayan H.  
**Institution**: Manipal Institute of Technology, Department of Computer Science  
**Status**: Archived Historical Companion  

[... Original prototype design text retained below for audit provenance ...]

## Executive Abstract (Prototype Concept)

Classical machine learning approaches to financial market forecasting frequently fail in real-world deployment due to non-stationarity, low signal-to-noise ratios, and the disconnect between point-in-time directional predictions and dynamic risk management. This capstone project introduces a **Two-Tier Hybrid Computational Intelligence (CI) System** that marries statistical pattern recognition with multi-objective metaheuristic optimization:

1. **Tier 1 (Predictive Intelligence Layer)**: A gradient-boosted temporal classifier engineered over technical trend, momentum, volatility, and volume features that estimates calibrated forward return probabilities $\hat{P}(\text{Up})$ and identifies market volatility regimes.
2. **Tier 2 (Multi-Objective Evolutionary Decision Engine)**: A **Non-dominated Sorting Genetic Algorithm II (NSGA-II)** that evolves real-valued trading rule chromosomes (dynamic ATR stop-loss, take-profit multipliers, trailing stops, regime-conditional capital allocation) to simultaneously maximize risk-adjusted return (**Sharpe Ratio**) and minimize capital risk (**Maximum Drawdown**).

By coupling the evolutionary optimizer with a vectorized simulator, the system evaluates strategy permutations across historical market data. In rigorous out-of-sample walk-forward validation across Indian equities (2020–2025), the evolved strategies demonstrated robust capital preservation, dampening annual drawdowns while documenting the empirical trade-offs of market timing.
