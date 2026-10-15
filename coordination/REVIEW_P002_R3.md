# Codex review P002-R3 - 12 October 2026

Outcome: APPROVED as reproducible retrospective research evidence. P002 is complete; P003 may proceed. Approval does not imply profitability, scientific novelty, publication acceptance or live execution realism.

## Independent evidence
- python -m pytest tests -q: 28 passed, one non-blocking dateutil warning, 9.20s.
- Ran the campaign verification with additional independent checks of ALL metrics and ALL available trade logs: 18 folds, 288 variant metric sets and 234 trade-log sets; zero mismatches. Selected hybrid/ablation genes and all equity paths pass the original campaign gate, tolerances genes 1e-12 and equity 1e-7.
- Current protocol/correction/raw-result/source file SHA-256 values match campaign_audit.json. Saved machine-readable review evidence in coordination/VERIFICATION_P002_R3.json.
- Independently reconciled terminal return and net trade P&L for all executable variants and retallied median annual scorecard: 10 positive-return folds, 5 return wins against B&H, 17 lower-drawdown folds, out of 18.
- Viewed stitched_equity_curves.png: three assets, readable labels, consistent equity trajectories and nominal INR units. Other figures not independently visually inspected in this review; P003 must render/inspect all figures used in documents.

## Approved core findings
Six-year hybrid seed-median returns: RELIANCE -0.35%, TCS +25.60%, INFY +9.10%. Same-asset annually liquidated/reentered B&H: +128.74%, +65.13%, +152.78%. This benchmark differs from an uninterrupted six-year holding due to annual liquidation/reentry costs and gap treatment; paper must state the convention explicitly.
Classifier mean fold AUC .5324; accuracy 52.68% versus training-prior baseline 52.66%; Brier .2501 versus .2500. Evidence supports small discrimination and minimal average classification improvement, not broad predictive superiority.
Lower median ANNUAL drawdown in 17/18 folds does not guarantee lower six-year drawdown on every asset (INFY hybrid median ~37.16% vs B&H ~35.93%). Report both.

## Non-blocking reporting corrections to carry into P003
Implementation report mistakenly says test years 2019-2024 and seeds 42/123/999 in one paragraph. Actual runner/artifacts use 2020-2025 and 42/43/44; correct that paragraph. Audit script header claims trade-log comparisons it does not itself execute; independent Codex review performed those comparisons, but strengthen script or correct its claim and save review evidence.
RESULTS headings retain 'frozen' language despite documented retrospective corrections; use documented protocol rather than preregistered wording. Baselines and seeds remained fixed during correction, but the protocol was revised after results were inspected. Daily volume-known endpoint and overnight exposure proxy are disclosed retrospective assumptions. TCS early snapshot history is not asserted to be IPO data.

## Next
P003: evidence-based paper draft, college report, reproducible demo and viva notes. Do not modify approved simulator/models/data or launch new tuning. Source changes would invalidate stored source hashes and require explicit rerun/audit.
