# Codex review P001 - 12 October 2026

Outcome: CHANGES REQUIRED. Baseline results are provisional until simulator fixes and regeneration.

Independently ran python -m pytest tests -q: 11 passed, 1 warning in 11.44s. Source confirms horizon gaps, removal of unknown targets and development-only evolution/strategy selection. Baseline JSON exists. No Git repository was present initially, so review compares inspected source rather than claiming a Git diff.

## Three independently reproduced execution defects
Use 25 bars: Open=Close=100, High=101, Low=99, ATR=2, regime=0, zero fees/slippage. Genes [0.7,0.3,2,3,0.06,1,20]. p defaults 0.4; p[0]=0.8 enters on bar 1.
1. Set bar 1 Low=90: expected entry-day stop at 96. Actual position remains open until bar 21 and exits at 100 due to timeout. Exit checks occur before entry and miss entry-day brackets.
2. Set p[1]=0.1 and bar 2 High=110: expected queued market exit at bar 2 Open=100. Actual target exit at 106. Later intrabar events override the scheduled opening exit.
3. Set p[1]=0.8 and bar 2 Low=90: first position exits intrabar at 96, then replacement enters at that day's earlier Open=100 using later proceeds. Previous-close position was already holding; no opening entry was eligible.

## Additional evidence gaps
The detailed wrapper gets metrics from the fast simulator; current agreement test does not independently validate detailed equity/logs. n<20 returns fabricated raw sentinel losses even without penalty. Baseline JSON omits dataset hashes, saved equity/trades and cost/environment provenance. No saved NSE probe/AppTest script found under reports/baseline. Dependencies use lower bounds, despite report wording that they are pinned.

RELIANCE baseline has only four test trades (three wins); its 75% win rate cannot support a strong generalization claim. Do not publish these metrics before regeneration.

Next: P001-R1, then a small NSE basket with rolling evaluation and fixed model settings before broader tuning. Check usable data periods and TCS early-history provenance.
