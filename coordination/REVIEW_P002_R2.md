# Codex review P002-R2 - 12 October 2026

Outcome: CHANGES REQUIRED. Boundary tests and reporting have improved, but the saved campaign no longer matches current source. This is a material evidence mismatch, not a stylistic issue.

## Independent verification
- python -m pytest tests -q: 27 passed, one warning, 9.27s.
- Audit companion and all-seed reporting exist; source handles trailing zero-volume liquidation.
- Independently re-executed run_fold for ALL 18 asset/year folds and ALL 3 seeds against the immutable snapshots (without calling run_all or overwriting saved campaign). Compared each GA variant equity against campaign_raw_results.json with rtol=0, atol=1e-7.
- Found 35 differing variant equity paths. This includes full hybrid, doubled-cost hybrid, diagnostic and no-ML ablation.

## Reproduced examples (current source vs saved)
- INFY.NS 2020 seed44 hybrid return: 27.8341% vs saved 47.8786%.
- INFY.NS 2025 seed42 hybrid return: -16.9165% vs saved -5.8584%.
- TCS.NS 2023 seed43 hybrid return: 24.1582% vs saved 27.1737%.
- TCS.NS 2022 seed42 no-ML ablation return: -8.8583% vs saved +2.2614%.
- Saved RELIANCE.NS 2021 seed43 ablation contains an entry on the final test day, which current source forbids.

## Cause
The new entry gate i < last_tradable_idx affects EVERY simulation's final tradable day, even when the endpoint has positive volume. It changes development fitness and the evolutionary search, not merely terminal zero-volume handling. Therefore checking only endpoint volumes cannot establish unchanged results. New audit records current code hashes against previous-code results and is not proof of provenance for their generating execution.

## Required next action
Keep the now-documented execution convention, perform a complete audited campaign rerun, regenerate ALL dependent CSVs/figures/paired comparisons/RESULTS, then verify all current-source fold paths against the newly saved artifact. Do not alter strategy budgets or tune after observing these differences. Add a regression demonstrating final-day-entry convention and test that a positive-volume endpoint can affect development selection. Save campaign-wide reproducibility evidence rather than relying on the single unaffected TCS2021seed42 case.

## Protocol provenance caution
P002-R1 report recorded original protocol hash 853e34a66d0cffaa61da75c0be362629bca0b68625ae743a60424560b7318357; current audit/reference is 012e66ad55e4eed0c9017ffa84ec160e94697a7266a4064cf0ddfbe4c1c197bb. Without a preserved historical byte snapshot, do not assert those references prove the original file remained untouched. Record current content and correction history honestly, distinguish byte changes from methodological changes, and describe this as a documented retrospective protocol rather than preregistered evidence.
