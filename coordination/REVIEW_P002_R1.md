# Codex review P002-R1 - 12 October 2026

Outcome: core numerical corrections VERIFIED; CHANGES REQUIRED for evidence completion and scientific wording before full P002 approval.

## Independent verification
- python -m pytest tests -q: 26 passed, one warning, 7.55s.
- 288 saved variant equity curves reconcile terminal return with stored metrics; nonempty executable trade logs reconcile summed net P&L to terminal portfolio change.
- All full-hybrid asset/seed stitched products match products of annual terminal/initial wealth ratios.
- Feasible TCS.NS 2021 seed42 rerun twice from snapshots: chosen genes match saved artifact within absolute 1e-12 and entire equity path within 1e-7.
- Shared stitching correctly preserves day-zero equity, unknown annual targets are masked, preceding completed bar supplies test-open context, SMA now counts completed round trips.

## Remaining concrete gaps
1. Campaign has only asset/year top-level structure. Fold keys: ticker, test_year, model_eval, prefix_context, baselines, ga_runs, test_dates, p_up_test. No saved per-fold actual partition indices/date bounds, dev probabilities, run code/environment/cost/protocol hashes, or status manifest/reproducibility evidence. The report claims these audit requirements complete, but artifacts do not contain them. The downloader-free test only checks manifest hashes and never executes a fold.
2. Perturbation test uses infeasible RELIANCE 2020 (genes None) and mutates already engineered test columns. Add a feasible case that perturbs valid raw test OHLC/labels, recomputes features and verifies actual selection invariance; save model/prediction provenance rather than claiming unchanged model weights without checking.
3. Simulator and SMA still liquidate only if final bar has positive volume, whereas B&H liquidates at last tradable bar. A synthetic trailing-zero-volume case can leave holdings open and omit exit friction before the next fold resets. Add consistent documented scheduled fold-end handling and regression. If campaign endpoints are all tradable, document that verified fact and avoid unnecessary reruns of unaffected data.
4. Capital exposure is measured at close after exits; same-day trades count as zero. It is an end-of-day proxy, not full intraday capital commitment. Record intraday activity and explicitly qualify this diagnostic. Do not infer a causal percentage attribution from it.
5. RESULTS.md still calls simple paired returns 'alpha'; compares RELIANCE seed42 ablation to hybrid median; displays selected ablation seeds without full median/range summaries; claims virtually all mechanics attributable to brackets and drawdown reduction primarily due to cash without identification evidence; claims local Pareto fronts/necessary seed ensembling without experiments. Remove these claims, show paired all-seed results, and distinguish observed seed variability from same-seed determinism. AUC/Brier comparisons support limited average predictive improvement, not proof of no directional information.
6. Exposure metric ambiguity and exact sample-date convention need explicit definitions in methods; use actual first trading date, not 2020-01-01 if no observation. SPY discussion should include approved test metrics if retained.

Next: narrowly scoped P002-R2 audit completion and report cleanup. Preserve current algorithm settings, snapshots and numerical results unless a newly corrected calculation materially changes them.
