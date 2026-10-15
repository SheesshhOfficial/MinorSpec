# Verified Academic References & Primary Source Ledger

Task ID: P003-R1  
Date: 12 October 2026  
Status: VERIFIED PRIMARY SOURCES (Accessible Repositories & Documented Access Bounds)  
Authors: Ashish Ranjan, Khuushi Maheshwari, Satyanarayan H.  
Institution: Manipal Institute of Technology, Department of Computer Science  

This ledger records the verified academic citations, official repositories, DOIs/URLs, access observations, and exact claims supported in the research paper draft and college project report. In accordance with Task P003-R1 guidelines, citations are mapped strictly to claims supported by their respective texts, bounded without asserting unsupported guarantees, and publisher access boundaries are disclosed honestly.

---

### Reference 1: Multi-Objective Evolutionary Optimization (NSGA-II)
- **Full Citation**: Kalyanmoy Deb, Amrit Pratap, Sameer Agarwal, and T. Meyarivan. "A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II." *IEEE Transactions on Evolutionary Computation*, vol. 6, no. 2, pp. 182–197, April 2002.
- **Identifier / DOI**: [10.1109/4235.996017](https://doi.org/10.1109/4235.996017)
- **URL**: https://ieeexplore.ieee.org/document/996017 (Direct publisher landing page; programmatic HTTP automated crawl encountered access barriers, verified via official institutional metadata).
- **Access / Verification Date**: 12 October 2026
- **Claims Supported in This Work**:
  1. Introduction of the fast non-dominated sorting algorithm with $O(M N^2)$ computational complexity, improving over previous $O(M N^3)$ multi-objective approaches.
  2. Elitist selection architecture combining parent and offspring populations ($R_t = P_t \cup Q_t$) of size $2N$ to preserve elite Pareto individuals across generations.
  3. Crowding-distance metric and crowded-comparison operator ($\prec_n$) promoting population diversity along the Pareto front without requiring a subjective sharing parameter $\sigma_{\text{share}}$.
  4. Real-coded Simulated Binary Crossover (SBX) and polynomial mutation concepts for continuous optimization problems.
- **Explicit Boundary**: Deb et al. formulate general multi-objective optimization algorithms; they do not prescribe the financial trading rules, 7-gene bounds, or market volatility filters implemented in this project.

---

### Reference 2: Gradient-Boosted Decision Trees (LightGBM)
- **Full Citation**: Guolin Ke, Qi Meng, Thomas Finley, Taifeng Wang, Wei Chen, Weidong Ma, Qiwei Ye, and Tie-Yan Liu. "LightGBM: A Highly Efficient Gradient Boosting Decision Tree." In *Advances in Neural Information Processing Systems 30 (NIPS 2017)*, Long Beach, CA, USA, pp. 3146–3154, 2017.
- **URL**: https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html (Freely accessible open-access proceedings verified).
- **Access / Verification Date**: 12 October 2026
- **Claims Supported in This Work**:
  1. Histogram-based feature binning and leaf-wise (best-first) tree growth with depth limits to achieve computational efficiency on large tabular datasets.
  2. Gradient-based One-Side Sampling (GOSS) retaining instances with large gradients while downsampling instances with small gradients to maintain information gain estimation accuracy.
  3. Exclusive Feature Bundling (EFB) safely bundling mutually exclusive sparse features to reduce dimensionality.
- **Explicit Boundary**: The paper describes general GBDT acceleration methods; the specific tabular technical indicator features, 3-day return classification target, validation early stopping, and hyperparameter configuration used here are project-specific empirical implementations.

---

### Reference 3: Financial Machine Learning & Purging Mechanics
- **Full Citation**: Marcos López de Prado. *Advances in Financial Machine Learning*. John Wiley & Sons, Hoboken, New Jersey, February 2018. ISBN: 978-1119482086.
- **URL**: https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086 (Official publisher catalog verified).
- **Access / Verification Date**: 12 October 2026
- **Claims Supported in This Work**:
  1. Conceptual risks of non-stationarity, low signal-to-noise ratios, and severe backtest overfitting inherent to financial time series.
  2. Multi-day forward labeling mechanics causing overlapping label dependencies across adjacent temporal observations.
  3. The methodological necessity of chronological train/validation/test partitions with horizon purging to drop samples spanning partition boundaries and prevent forward-looking information leakage.
- **Explicit Boundary**: López de Prado provides the theoretical rationale for horizon purging; the specific fixed 3-bar forward purging rule ($H=3$) implemented across annual calendar splits is our project's operational realization.

---

### Reference 4: Backtest Overfitting & Deflated Sharpe Ratio
- **Full Citation**: David H. Bailey and Marcos López de Prado. "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality." *The Journal of Portfolio Management*, vol. 40, no. 5 (Special 40th Anniversary Issue), pp. 94–107, 2014.
- **Identifier / DOI**: [10.3905/jpm.2014.40.5.094](https://doi.org/10.3905/jpm.2014.40.5.094)
- **URL**: https://www.pm-research.com/content/iijpormgmt/40/5/94 (Publisher landing page; automated programmatic requests returned HTTP 403, metadata verified via cross-reference index).
- **Access / Verification Date**: 12 October 2026
- **Claims Supported in This Work**:
  1. Performance inflation and selection bias in multiple backtesting trials: when an optimization process selects the maximum Sharpe ratio across numerous candidate trials, it risks selecting statistical noise.
  2. The mathematical principle that observed Sharpe ratios must be evaluated in light of sample size, return skewness, excess kurtosis, and the number of evaluated strategy trials.
- **Explicit Boundary**: Cited as foundational theoretical motivation for multi-seed reporting and cautious interpretation; our study presents empirical multi-seed medians and min-max ranges rather than a formal closed-form DSR statistical test.

---

### Reference 5: Data Snooping Bias & Reality Checks
- **Full Citation**: Halbert White. "A Reality Check for Data Snooping." *Econometrica*, vol. 68, no. 5, pp. 1097–1126, September 2000.
- **Identifier / DOI**: [10.1111/1468-0262.00152](https://doi.org/10.1111/1468-0262.00152)
- **URL**: https://www.jstor.org/stable/2999444
- **Access / Verification Date**: 12 October 2026
- **Claims Supported in This Work**:
  1. Formal econometric framing of data snooping bias when historical data is reused for strategy search and model selection.
  2. The principle that testing many rule permutations inflates apparent outperformance, requiring severe penalties or reality-check corrections before asserting superior predictive ability.
- **Explicit Boundary**: White's work warns against unpenalized search; our work reports retrospective multi-seed results without asserting that evolutionary parameter search guarantees profitable rules or formal statistical significance.

---

### Reference 6: Market Efficiency & Benchmark Standards
- **Full Citation**: Eugene F. Fama. "Efficient Capital Markets: A Review of Theory and Empirical Work." *The Journal of Finance*, vol. 25, no. 2, pp. 383–417, May 1970.
- **Identifier / DOI**: [10.2307/2325486](https://doi.org/10.2307/2325486)
- **URL**: https://www.jstor.org/stable/2325486
- **Access / Verification Date**: 12 October 2026
- **Claims Supported in This Work**:
  1. Weak-form Efficient Market Hypothesis (EMH) stating that past price and volume data is reflected in current prices, providing the classical theoretical benchmark against which technical trading strategies are evaluated.
  2. Justification for using passive Buy & Hold as a rigorous primary benchmark for long-only equity strategies.
- **Explicit Boundary**: Fama's paper establishes the theoretical framework; it is cited to contextualize why technical signals often yield small predictive advantages, not as proof that technical anomalies never exist.

---

### Reference 7: Historical Market Data & Corporate Action Adjustment Semantics
- **Full Citation**: Ran Aroussi et al. "yfinance: Download Market Data from Yahoo! Finance." Python Package Documentation, Version 0.2+, 2024–2026.
- **URL**: https://github.com/ranaroussi/yfinance (Open source project repository verified).
- **Access / Verification Date**: 12 October 2026
- **Claims Supported in This Work**:
  1. Data provider adjustment semantics: default `auto_adjust=True` retroactively adjusts historical `Open`, `High`, `Low`, and `Close` prices for stock splits and cash dividends.
  2. Historical prices represent adjusted backward series rather than point-in-time nominal transaction prices on historical trading sessions.
