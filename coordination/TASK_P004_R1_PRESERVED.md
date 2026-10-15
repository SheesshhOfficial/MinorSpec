# Task P004-R1 - Finish dashboard visual clarity and deterministic validation

Status: READY
Owner: Antigravity
Reviewer: Codex

## Goal
Complete the redesign by fixing the concrete findings in coordination/REVIEW_P004.md. Read AGENTS.md, PROJECT.md, that review, app.py, ui modules and UI tests. Preserve current design direction and verified research source/data/artifacts. No UI framework migration or expanded research work.

## Scope
1. Fix Pareto heading/legend overlap, right-edge label clipping and long selector options. Short options 'Strategy #ID' with primary tag; selected metrics in a separate caption/card. Make layout readable at desktop1440x900, tablet1024x768 and mobile390x844; wrap legend or put it outside chart data, not on top of title. Readable chart headings and tick labels; keep stable numeric IDs.
2. Persistent plain-language captions for candidate count/improvement rounds and discoverable GA-seed explanation. Rename asset labels to plain 'Stock or asset'; qualify NSE paper universe vs other exploratory tickers. Friendly feature labels with source IDs in hover. No indicator-based profit promises.
3. Replace UI test live-pipeline dependence with deterministic mocked backend fixtures and strict blocked downloader/loader calls. Include >=2 candidates with known unequal metrics, no-trade fixture and failure fixture. Verify initial idle/no pipeline call, explicit run, frozen primary invariance on candidate/filter changes, successful rerun clears pending state, failed rerun preserves exact previous result/settings, metric values/currency, help, zero and filtered-empty journals, and export contents. Save call-count evidence proving no rerun on browsing. Real cached smoke remains separate, clearly identified as potentially cache/network dependent.
4. Prominent identity and primary/exploratory status in Trade Journal and any export context. Filtering changes display only. Export clearly complete vs filtered log; verify exact CSV payload. Use units label for neutral unknown currency. Display holding duration via int(gene) matching simulator truncation. Keep original seed range1..99999.
5. Methodology reflects actual single-split backend: >=3-trade dev filter then highest raw Sharpe, fallback highest raw Sharpe if no eligible; no rolling cash fallback claim. Explain approximate fractions after purge and close-normalized B&H/friction convention. Distinguish18asset-year folds from54fold-seed runs; model seed fixed by backend, displayed seed controls GA. Supervisor blank. Avoid overgeneralizing paper metrics to current run.
6. Unify Run actions: inline CTA uses current sidebar settings or explicitly synchronizes preset controls, never leaves mismatched results/pending state by default. Handle invalid custom ticker input visibly without silent fallback. Persist results on execution failures and make last successful run status distinct from a running job; keep truthful busy indicator.
7. Run full offline suite and one real cached app smoke with numeric comparison to returned backend result. Verify approved code/input hashes unchanged. No full research campaign rerun. Update smoke script/test documentation truthfully.
8. Re-capture final real-browser screenshots after all fixes: overview, explorer, model, journal, methodology, expanded controls help; desktop/tablet/mobile plus failed/empty states. Check all screenshots for exceptions, text overlap, clipping and overflow. Record actual viewport/DPR and source revision/hash, mark old error captures superseded. If real browser unavailable, document limitation and leave visual acceptance incomplete. Update UI_REDESIGN_NOTES.md and README with actual checks and limitations.

## Acceptance
No chart heading/legend overlap or clipped selected label at target widths. Stable intuitive controls; inline Run and sidebar agree. Offline fixture tests cover state/filter/export contracts and never fetch data. All tab contexts distinguish primary/exploratory. Currency and holding duration match backend. Final screenshots contain no exceptions and correspond to current source. Research hashes unchanged and full tests pass.

## Report
Replace IMPLEMENTATION_REPORT.md using REPORT_TEMPLATE.md with COMPLETE/PARTIAL/BLOCKED. Include changed files, actual test outputs, real-run numeric comparison, viewport screenshots, hashes, failures/skips. Continue independent items after non-blocking failures. Stop for Codex review. No history edits, publication or research computation changes.
