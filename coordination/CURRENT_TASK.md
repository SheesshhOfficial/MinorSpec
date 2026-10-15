# Task P005 - Simple college presentation

Status: COMPLETE
Owner: Codex (explicit user override)
Reviewer: Codex

## User request and role
User asks: "create me a very simple ppt to present". Create the actual editable PowerPoint now. Codex has planned the content below. Target a beginner-friendly 5-7 minute college presentation, exactly 8 slides, with short speaker notes. Do not ask for cosmetic preferences. Use a simple white background, dark navy text, restrained blue accent, generous whitespace and large text. No decorative stock-market imagery, dense dashboard layouts, animations, or paragraphs on slides.

## Preserve pending work
P004-R1 task and implementation report are copied to coordination/TASK_P004_R1_PRESERVED.md and coordination/IMPLEMENTATION_REPORT_P004_R1_PRESERVED.md. They still await Codex review. Do not claim their approval or change app/code/tests/data/research outputs while making the presentation. Do not overwrite existing submission files.

## Read and source
Read PROJECT.md, AGENTS.md, reports/submission/VIVA_DEFENSE_NOTES.md, RESEARCH_PAPER_DRAFT.pdf, coordination/REVIEW_P002_R3.md and REVIEW_P003_R2.md. Verify numbers against reports/experiments/results/stitched_aggregate_metrics.csv and paired_annual_comparisons.csv. Read available presentation skill for authoring and visual checks. Sources in speaker notes should identify local artifact and relevant metric, not claim a new experiment.

## Deliverables
- reports/submission/SIMPLE_PROJECT_PRESENTATION.pptx (editable text/table)
- reports/submission/SIMPLE_PROJECT_PRESENTATION.pdf (same 8 slides, if export available)
- Speaker notes inside PPTX: approximately 45-70 spoken words per slide, everyday English, explain jargon when first introduced. Include evidence sources after the spoken script where needed.
- Private build scripts, rendered slides and validation evidence under reports/presentation_build/. Do not clutter final submission folder with temporary files.

## Exact slide plan
1. Title: "Hybrid Market Predictor & Strategy Optimizer". Subtitle: "LightGBM and NSGA-II for Indian stocks". Authors exactly: Ashish Ranjan; Khuushi Maheshwari; Satyanarayan H. Institution: Manipal Institute of Technology. Program: B.Tech - Computer Science. No supervisor name, leave it out.
2. "Project purpose". Three short points: Learn patterns in historical stock data. Search for trading rules that balance return and risk. Test those rules on later, unseen data. Plain explanation in notes: a research simulator, not live trading or guaranteed profit.
3. "Data and tools". NSE stocks: Reliance, TCS and Infosys. Daily prices and trading volume via yfinance, saved snapshots. 20 indicators describe trend, momentum and volatility. Python with LightGBM, NSGA-II and Streamlit. Notes distinguish historical data availability from test period 2020-2025. Do not imply only 2020-2025 training history.
4. "How it works". A simple numbered sequence with 5 short lines: 1 Read historical prices. 2 Build technical indicators. 3 LightGBM estimates the chance of a rise over the next 3 trading bars. 4 NSGA-II searches for entry, exit and risk rules. 5 Backtest on later data and show results. Explain probabilities as model estimates, not calibrated certainty.
5. "The two algorithms". Two simple text columns, no boxes needed. LightGBM: learns from past examples and produces a direction probability. NSGA-II: improves candidate trading rules over several rounds, balancing Sharpe ratio and maximum drawdown. One short definition each: Sharpe = return relative to variability; drawdown = largest fall from a previous peak. Explain risk-return tradeoff in notes without claiming optimal future performance.
6. "Research results". Editable 3-row table: Stock / Hybrid return / Buy-and-hold return. Use six-year 2020-2025 compounded returns, median across GA seeds for hybrid: Reliance -0.35% vs 128.74%; TCS 25.60% vs 65.13%; Infosys 9.10% vs 152.78%. Recalculate/confirm against source before delivery. Visible caption must say "2020-2025 cumulative return; hybrid median across 3 seeds". Visible takeaway: "Buy-and-hold earned more on all three stocks." Secondary line: "Hybrid drawdown was lower in 17 of 18 annual stock comparisons." Notes explain annual count uses seed-median comparisons, does not mean lower drawdown for every full-period path. These are archived rolling research results, not current dashboard demo values. Explain buy-and-hold in notes. Keep findings honest.
7. "Using the dashboard". Four steps: Select a stock. Set population 40, generations 15 and seed 42 for a demo. Click Run Experiment. Inspect performance, strategies and trades. Small explanation: "Population = candidate rules; generations = improvement rounds; seed = repeatable randomness." Notes: this demo uses a single chronological split and different optimizer settings from the rolling study (30/10, seeds42/43/44). Do not mix the two sets of results. Use actual app button label if changed. No screenshot necessary for this simple deck.
8. "Conclusion and next steps". Built an end-to-end prediction and strategy research tool. Observed risk-return tradeoffs, with lower returns than buy-and-hold in this study. Next: evaluate more stocks and improve predictive features. End with a small "Thank you / Questions" line. No unsupported novelty or future profitability claims.

## Acceptance and verification
Exactly8 slides; readable at projection size (titles approximately32pt+, body22pt+ where possible, no tiny source clutter). Limit text to supplied concise points, with explanations in speaker notes. Keep editable table values and texts. Check author spelling including Khuushi and Satyanarayan H. Verify all results against approved source artifacts without running a new research campaign. Render every slide, inspect all 8 for clipping, overlap, missing glyphs and table readability, fix before delivery. Verify PPTX opens and contains8slides plus notes. Export PDF if supported, otherwise report that limitation honestly. Record source hashes and render/inspection method. Do not invent verification.

## Report
Replace coordination/IMPLEMENTATION_REPORT.md using REPORT_TEMPLATE.md, Task ID P005, status COMPLETE/PARTIAL/BLOCKED. Include actual deliverable paths, slide count, evidence checks, render QA and any limitations. Continue independent work after non-blocking export failures. Stop for Codex review. Do not edit history or publish externally.

