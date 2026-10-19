# MinorSpec correctness and dashboard repair

Status: COMPLETE (with explicit verification limits below)
Baseline: c8c400e286178201377b98fabbfb0fefa4f5f097
Engine accounting contract: 2

## Scope

The owner requested fault repairs and publication, then a premium, concise UI
with detailed explanations behind information buttons. This supersedes the old
completed presentation-only task for this repair. No history rewrite or deployment
was requested. Historical datasets, campaigns and submission artifacts are retained.

## Corrections

- Strategy/benchmark drawdown paths use point-in-time peaks including initial capital.
- Fee-inclusive position sizing is exact; first-bar entries require causal prior ATR.
- Zero-volume highs cannot move trailing stops; entry-day already-crossed stops use
  the opening quote. Fast/detailed engines share validation and accounting checks.
- Dashboard buy-and-hold now uses first tradable Open to final tradable Close with
  matching commission/slippage. This is an explicit benchmark methodology change.
- Optimizer and single-split evaluations use volume constraints consistently;
  measured metrics are distinct from low-trade search fitness penalties.
- Date/split/label validation, missing-label handling, flat-volume features and
  one-class AUC reporting are corrected. Search randomness is isolated; classifier
  seed remains 42. Unsafe model/cache filename interpretation is prevented.
- Data caches validate symbol, requested range, file hash and metadata. Explicit
  offline mode records coverage. Stale fallback/source are visible in the dashboard.
- Current-engine output files are versioned and refuse overwrites; CLI provenance
  includes actual data-mode flags. Original archival replay is not silently relaxed.
- Compact controls and tabs replace verbose headings. Information icons support
  hover/title fallback, native click/touch/keyboard disclosure and accessible labels.
  Longer explanations are collapsed. Research/errors/staleness remain visible.
- Fixed dynamic population caption, invalid-ticker fallback, selector reset,
  missing-result preservation, undefined metric formatting, break-even filtering,
  chart currency/capital labels and doubled strategy-ID hover marker.
- README, detailed walkthrough and Windows interpreter-specific installer updated.

## Executed verification

Full final suite: **148 passed, 2 skipped**, 21.29 seconds. All 27 UI tests also
passed separately after the final tooltip-title fallback. Latest results are
recorded in `reports/verification/test_summary_v2.json`.

Commands (with installed dependencies on PYTHONPATH in the cloud validation workspace):

```sh
python -m pytest tests -q -ra
python -m scripts.verify_dashboard_offline
python -m compileall -q src ui app.py scripts
```

For this target-directory Streamlit installation only, tests initialize
`config.get_config_options(options_from_flags={'global.developmentMode': False})`
before pytest/AppTest. This resolves a test-runtime development-mode/port conflict;
the later owner-approved CORS hardening is a separate intentional configuration change.

Real offline AppTest used bundled RELIANCE, population40/generations15/seed42:
zero exceptions; five tabs; alternate-candidate inspection preserves primary;
pending settings preserve completed results; repeated run resets selection.
`scripts/verify_dashboard_offline.py` forbids market downloads during that check.

Independent regression cases cover ledger arithmetic, net-P&L/equity reconciliation,
cost-only drawdown, first-bar ATR causality, zero-volume rules, fast/detailed parity,
feature prefix causality, purges, cache/schema errors, UI failure/state flows and
model/search separation. Existing 5,000-bar performance threshold passes.

Separate v2 fixture: `reports/verification/repaired_tcs_2021_seed42.json`, with
source/input/protocol hashes, dependency versions and exact genes/equity replay.
Regeneration script refuses to overwrite an existing fixture. Fresh dashboard
examples are in `reports/verification/dashboard_examples_v2.json`; they are not
a new full rolling campaign.

Independent source review examined timing, fees, benchmark integration, evidence
preservation, provenance and UI state. Its actionable findings were incorporated.

## Skips and limits

1. Original exact v1 archived-equity replay is retained, explicitly skipped for
   accounting v2; fee/execution changes make v1 equity an invalid exact target.
2. The 9,020,452-byte archived raw campaign JSON could not be materialized through
   the connector in this partial checkout. Its separate local integrity test is
   explicitly skipped. Expected original Git blob:
   `c6646b348649e5c3b145ef052f75944ee379ec5a`. Remote tree preservation is checked
   after publication; no empty placeholder is published.
3. Browser startup is blocked in this cloud execution environment. AppTest verifies
   behavior, not rendered desktop/mobile pixels. Visual layout and real keyboard/
   touch interaction are not claimed as browser-tested.
4. Live Yahoo retrieval was mocked in automated tests; real offline snapshots were
   exercised. Provider availability and live data changes are not verified.
5. Full archived rolling research was not rerun. Old claims/plots are unchanged and
   must not be presented as results from repaired accounting v2. Archived plotting
   and audit tools still target v1 files; see README.
6. The owner explicitly approved enabling Streamlit cross-origin protection.
   `enableCORS=true` and `enableXsrfProtection=true` are now verified by a
   configuration regression test and the real offline AppTest was rerun. No public
   deployment was performed; custom cross-origin embeddings may need a reviewed
   allowed-origin configuration.

No audit establishes that all possible bugs are absent, and no result establishes
future trading profitability.
