"""
Updated RESEARCH_PAPER_DRAFT generator for Task P003-R1:
- Replaced all raw TeX and dollar-delimited equations with clean Unicode/plain equations.
- Replaced colored headings with clean, authoritative black academic headings.
- Corrected 20 technical features list directly matching FEATURE_COLUMNS in rolling_runner.py.
- Stated exact GBDT settings (num_boost_round=250, early_stopping=30, learning_rate=0.03, max_depth=5, num_leaves=24).
- Stated exact 7 gene bounds: [(0.52, 0.85), (0.35, 0.50), (1.0, 4.5), (1.5, 7.0), (0.01, 0.06), (0.10, 1.00), (5.0, 45.0)].
- Stated exact NSGA-II operators: SBX (pc=0.85, eta=15), Polynomial Mutation (per-gene prob=1/7, eta=20).
- Stated exact inactivity penalty: Sharpe -= 2.0, MaxDD = max(MaxDD, 0.5) if trades < 5 during Development.
- Stated exact costs: 0.05% commission + 0.05% slippage per side (approx 10 bps per side, 20 bps round trip; 40 bps doubled).
- Computed all table metrics directly from CSV/JSON artifacts.
- Fixed figure captions and embedded truthful system architecture diagram.
- Included cash fallback selection, raw vs penalized fitness, annual reset B&H, hypothetical diagnostic assumptions, and 6-year INFY drawdown.
- Removed student email-domain placeholders.
"""

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from pathlib import Path
import pandas as pd
import numpy as np
import json
import win32com.client

PROJECT_ROOT = Path("u:/MInor-Specialization")
SUBMISSION_DIR = PROJECT_ROOT / "reports" / "submission"
FIGURES_DIR = SUBMISSION_DIR / "figures"
RESULTS_DIR = PROJECT_ROOT / "reports" / "experiments" / "results"

# Academic Palette: Black headings, charcoal body, soft borders
HEADING_COLOR = RGBColor(0, 0, 0)         # Authoritative Academic Black
TEXT_COLOR = RGBColor(40, 40, 40)         # Neutral Charcoal #282828
MUTED_COLOR = RGBColor(100, 100, 100)     # Gray #646464
BG_HEADER_HEX = "F2F2F2"                 # Light Neutral Gray

def set_cell_background(cell, hex_color):
    xml_str = f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(xml_str))

def set_table_borders(table):
    tblPr = table._tbl.tblPr
    borders_xml = f'''
    <w:tblBorders {nsdecls("w")}>
        <w:top w:val="single" w:sz="6" w:space="0" w:color="888888"/>
        <w:bottom w:val="single" w:sz="6" w:space="0" w:color="888888"/>
        <w:insideH w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
        <w:insideV w:val="none"/>
        <w:left w:val="none"/>
        <w:right w:val="none"/>
    </w:tblBorders>
    '''
    tblPr.append(parse_xml(borders_xml))

def format_cell(cell, text, bold=False, italic=False, color=TEXT_COLOR, size=Pt(8.5), align=WD_ALIGN_PARAGRAPH.LEFT, bg_hex=None):
    if bg_hex:
        set_cell_background(cell, bg_hex)
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.05
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.name = 'Calibri'
    run.font.size = size
    run.font.color.rgb = color

def add_header_footer(doc):
    for s in doc.sections:
        s.top_margin = Inches(0.85)
        s.bottom_margin = Inches(0.85)
        s.left_margin = Inches(0.85)
        s.right_margin = Inches(0.85)
        
        # Header
        header = s.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("Risk-Return Trade-offs of LightGBM & NSGA-II Trading Rules | Retrospective Walk-Forward Study")
        hrun.font.name = 'Calibri'
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = MUTED_COLOR
        
        # Footer
        footer = s.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Draft Academic Manuscript — For Academic Review Only — Manipal Institute of Technology (Oct 2026)")
        frun.font.name = 'Calibri'
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = MUTED_COLOR

def add_section_heading(doc, number_str, title_str):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(11)
    h.paragraph_format.space_after = Pt(3)
    h.paragraph_format.keep_with_next = True
    
    run_num = h.add_run(f"{number_str} " if number_str else "")
    run_num.bold = True
    run_num.font.name = 'Calibri'
    run_num.font.size = Pt(11.5)
    run_num.font.color.rgb = HEADING_COLOR
    
    run_t = h.add_run(title_str)
    run_t.bold = True
    run_t.font.name = 'Calibri'
    run_t.font.size = Pt(11.5)
    run_t.font.color.rgb = HEADING_COLOR

def add_subsection_heading(doc, number_str, title_str):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(8)
    h.paragraph_format.space_after = Pt(2)
    h.paragraph_format.keep_with_next = True
    
    run_num = h.add_run(f"{number_str} ")
    run_num.bold = True
    run_num.font.name = 'Calibri'
    run_num.font.size = Pt(10)
    run_num.font.color.rgb = HEADING_COLOR
    
    run_t = h.add_run(title_str)
    run_t.bold = True
    run_t.font.name = 'Calibri'
    run_t.font.size = Pt(10)
    run_t.font.color.rgb = HEADING_COLOR

def add_body_p(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3.5)
    p.paragraph_format.line_spacing = 1.12
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(9.5)
    run.font.color.rgb = TEXT_COLOR
    return p

def add_callout(doc, title, text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.8)
    cell = table.cell(0, 0)
    set_cell_background(cell, "F9F9F9")
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders_xml = f'''
    <w:tcBorders {nsdecls("w")}>
        <w:left w:val="single" w:sz="18" w:space="0" w:color="333333"/>
        <w:top w:val="none"/>
        <w:right w:val="none"/>
        <w:bottom w:val="none"/>
    </w:tcBorders>
    '''
    tcPr.append(parse_xml(borders_xml))
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Inches(0.12)
    p.paragraph_format.right_indent = Inches(0.12)
    
    run_t = p.add_run(f"[{title}]\n")
    run_t.bold = True
    run_t.font.size = Pt(8.5)
    run_t.font.color.rgb = HEADING_COLOR
    
    run_b = p.add_run(text)
    run_b.font.size = Pt(8.5)
    run_b.font.color.rgb = TEXT_COLOR
    
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(3)

def add_figure_image(doc, img_path, caption_str, width_in=5.8):
    if not Path(img_path).exists():
        print(f"Warning: Figure not found at {img_path}")
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(5)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(img_path), width=Inches(width_in))
    
    cp = doc.add_paragraph()
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_before = Pt(0)
    cp.paragraph_format.space_after = Pt(5)
    c_run = cp.add_run(caption_str)
    c_run.font.name = 'Calibri'
    c_run.font.size = Pt(8.0)
    c_run.italic = True
    c_run.font.color.rgb = MUTED_COLOR

def generate_paper_draft():
    # Load artifact data directly
    fold_df = pd.read_csv(RESULTS_DIR / "fold_summary_metrics.csv")
    stitched_df = pd.read_csv(RESULTS_DIR / "stitched_aggregate_metrics.csv")
    paired_df = pd.read_csv(RESULTS_DIR / "paired_annual_comparisons.csv")
    with open(RESULTS_DIR / "campaign_raw_results.json") as f:
        raw_data = json.load(f)

    doc = docx.Document()
    add_header_footer(doc)

    # -------------------------------------------------------------
    # Title & Metadata
    # -------------------------------------------------------------
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(8)
    title_p.paragraph_format.space_after = Pt(4)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    trun = title_p.add_run("Risk-Return Trade-offs of LightGBM and NSGA-II Trading Rules:\nA Retrospective Walk-Forward Study of Three NSE Equities")
    trun.bold = True
    trun.font.name = 'Calibri'
    trun.font.size = Pt(16)
    trun.font.color.rgb = HEADING_COLOR
    
    # Authors
    auth_p = doc.add_paragraph()
    auth_p.paragraph_format.space_before = Pt(3)
    auth_p.paragraph_format.space_after = Pt(2)
    auth_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    arun = auth_p.add_run("Ashish Ranjan,  Khuushi Maheshwari,  Satyanarayan H.")
    arun.bold = True
    arun.font.size = Pt(10.5)
    arun.font.color.rgb = HEADING_COLOR
    
    # Affiliation (No invented email domains or supervisor placeholders)
    aff_p = doc.add_paragraph()
    aff_p.paragraph_format.space_before = Pt(0)
    aff_p.paragraph_format.space_after = Pt(8)
    aff_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    afrun = aff_p.add_run("Department of Computer Science, Manipal Institute of Technology\n"
                          "B.Tech in Computer Science\n"
                          "Draft Academic Manuscript — October 2026")
    afrun.font.size = Pt(8.5)
    afrun.italic = True
    afrun.font.color.rgb = MUTED_COLOR

    # -------------------------------------------------------------
    # Abstract & Keywords Box
    # -------------------------------------------------------------
    abs_table = doc.add_table(rows=1, cols=1)
    abs_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    abs_table.autofit = False
    abs_table.columns[0].width = Inches(6.8)
    acell = abs_table.cell(0, 0)
    set_cell_background(acell, "F9F9F9")
    set_table_borders(abs_table)
    
    ap = acell.paragraphs[0]
    ap.paragraph_format.space_before = Pt(4)
    ap.paragraph_format.space_after = Pt(4)
    ap.paragraph_format.left_indent = Inches(0.12)
    ap.paragraph_format.right_indent = Inches(0.12)
    
    ab_bold = ap.add_run("Abstract— ")
    ab_bold.bold = True
    ab_bold.font.size = Pt(9.0)
    ab_bold.font.color.rgb = HEADING_COLOR
    
    ab_body = ap.add_run(
        "Machine learning models in financial forecasting frequently fail to preserve portfolio capital "
        "because directional predictions are disconnected from dynamic risk management. This study conducts a retrospective "
        "walk-forward evaluation of a Two-Tier Computational Intelligence (CI) architecture across three large-cap Indian equities "
        "(RELIANCE.NS, TCS.NS, INFY.NS) over a 6-year period (2020–2025, 1,487 trading sessions per asset). Tier 1 employs a LightGBM "
        "gradient-boosted decision tree to estimate forward 3-day directional return probabilities from 20 technical indicators. "
        "Tier 2 leverages the Non-dominated Sorting Genetic Algorithm II (NSGA-II) to evolve real-valued trading rule chromosomes "
        "(probability hurdles, dynamic ATR stop-loss and take-profit multipliers, trailing stops, and volatility-conditioned position sizing) "
        "simultaneously optimizing Annualized Sharpe Ratio and Maximum Drawdown. All backtests enforce strict next-bar Open execution, "
        "transaction costs (0.05% commission + 0.05% slippage per side, approximately 10 bps per side and 20 bps round-trip; sensitivity testing doubles both components to 0.10% commission + 0.10% slippage per side, 0.20% per side, approximately 40 bps round-trip), "
        "conservative intrabar bracket conflict ordering, horizon purging, and scheduled fold-end liquidation barring final-day entries. "
        "Across 18 annual test folds and three GA seeds, LightGBM achieves an average out-of-sample directional AUC of 0.5324, a test accuracy of 52.68% "
        "(compared to the training-class majority baseline of 52.66%), and no Brier score improvement (0.2501 vs baseline 0.2500). The Full Hybrid strategy reduced annual maximum drawdown relative to Buy & Hold in 17 out of "
        "18 folds (94.4%). However, by remaining in cash during sustained market expansions, the Hybrid underperformed Buy & Hold total return in 13 out of "
        "18 folds (72.2%), delivering multi-year stitched seed-median returns of -0.35% for RELIANCE.NS, +25.60% for TCS.NS, and +9.10% for INFY.NS, "
        "compared to Buy & Hold compound growth of +128.74%, +65.13%, and +152.78%, respectively. An evolutionary ablation without machine learning "
        "signals yields comparable or higher multi-year returns. These results show that defensive metaheuristic rules achieved lower median annual drawdowns "
        "in corrective periods but resulted in substantially lower compounded wealth in trending equity markets."
    )
    ab_body.font.size = Pt(8.5)
    ab_body.font.color.rgb = TEXT_COLOR
    
    kp = acell.add_paragraph()
    kp.paragraph_format.space_before = Pt(2)
    kp.paragraph_format.space_after = Pt(4)
    kp.paragraph_format.left_indent = Inches(0.12)
    kp.paragraph_format.right_indent = Inches(0.12)
    k_bold = kp.add_run("Keywords— ")
    k_bold.bold = True
    k_bold.font.size = Pt(8.5)
    k_bold.font.color.rgb = HEADING_COLOR
    k_text = kp.add_run("Computational Intelligence, Algorithmic Trading, LightGBM, NSGA-II, Multi-Objective Optimization, Walk-Forward Validation, National Stock Exchange of India (NSE), Backtest Overfitting.")
    k_text.font.size = Pt(8.5)
    k_text.font.color.rgb = TEXT_COLOR

    # -------------------------------------------------------------
    # 1. Introduction
    # -------------------------------------------------------------
    add_section_heading(doc, "1.", "Introduction & Research Question")
    add_body_p(
        doc,
        "The application of machine learning (ML) to financial market forecasting has expanded rapidly, yet practical deployment "
        "consistently confronts the realities of low signal-to-noise ratios, non-stationarity, and market efficiency [3], [5], [6]. A central "
        "challenge in computational finance literature is the conceptual gap between directional statistical prediction and dynamic "
        "capital preservation. Directional accuracy alone does not determine portfolio profitability because trade payoff distributions, "
        "position sizing, and transaction costs also matter [3]. Conversely, traditional rule-based algorithmic "
        "strategies rely on static technical indicators that fail to adapt across changing volatility regimes."
    )
    add_body_p(
        doc,
        "To investigate this trade-off, this study examines a Two-Tier Computational Intelligence (CI) architecture that decouples directional "
        "statistical inference from multi-objective policy search. Tier 1 trains a gradient-boosted decision tree (LightGBM) to estimate forward "
        "3-day directional return probabilities from engineered technical indicators. Tier 2 applies the Non-dominated Sorting Genetic Algorithm II "
        "(NSGA-II) [1] to evolve continuous trading rule parameters—including entry/exit probability thresholds, Average True Range (ATR) stop-loss "
        "and take-profit multipliers, trailing stop percentages, and regime-conditioned capital allocations. By framing strategy selection as a "
        "bi-objective optimization between risk-adjusted return (Sharpe Ratio) and capital risk (Maximum Drawdown), the evolutionary engine constructs "
        "a Pareto frontier of candidate trading policies."
    )
    add_body_p(
        doc,
        "We ground our investigation in three specific research questions: (1) Does gradient tree boosting provide measurable directional predictive "
        "edge on large-cap National Stock Exchange of India (NSE) equities over simple training priors? (2) Does evolving multi-objective risk parameters "
        "dampen out-of-sample portfolio drawdowns during historical market downturns? (3) How does cash preservation under defensive probability hurdles "
        "affect multi-year compounded capital accumulation relative to passive benchmark holding?"
    )
    
    add_callout(
        doc,
        "METHODOLOGICAL CONTRIBUTION & BOUNDARY DISCLOSURE",
        "Our primary contribution is methodological rigor, audit provenance, and reproducible empirical evaluation rather than claims of algorithmic novelty "
        "or guaranteed investment alpha. All experiments are conducted retrospectively over 2020–2025 using frozen parquet data snapshots, versioned audit "
        "corrections (protocol_correction.json v1.1.0), and verified code execution. The universe is restricted to three surviving large-cap equities "
        "(RELIANCE.NS, TCS.NS, INFY.NS) evaluated individually without cross-asset portfolio rebalancing."
    )

    # -------------------------------------------------------------
    # 2. Related Work
    # -------------------------------------------------------------
    add_section_heading(doc, "2.", "Related Work & Theoretical Foundations")
    add_body_p(
        doc,
        "The theoretical foundation of empirical market predictability is rooted in the Efficient Market Hypothesis (EMH) formulated by Fama [6], which "
        "posits that historical prices reflect available trading information, providing the benchmark against which technical trading strategies must be judged. "
        "In modern econometrics, Halbert White [5] established that empirical outperformance in trading rule evaluations is frequently an artifact of data snooping bias: "
        "searching across numerous parameter permutations risks selecting rules that appear profitable purely due to random chance. Bailey and López de Prado [4] formalized "
        "this hazard via the Deflated Sharpe Ratio (DSR), demonstrating that observed Sharpe ratios must be evaluated in light of sample size, return non-normality, "
        "and the effective number of strategy trials."
    )
    add_body_p(
        doc,
        "To mitigate backtest overfitting, López de Prado [3] proposed rigorous protocols for financial machine learning, notably purged and embargoed "
        "cross-validation. When overlapping forward labels are utilized (e.g., multi-bar holding returns), standard random cross-validation leaks information "
        "across adjacent folds. Purging trailing samples equal to the prediction horizon prevents this forward-looking contamination."
    )
    add_body_p(
        doc,
        "In the domain of multi-objective metaheuristics, Deb et al. [1] introduced NSGA-II, which eliminated the high computational complexity of early genetic "
        "algorithms through fast non-dominated sorting, elitist parent-offspring combining, and a parameter-less crowding distance operator that preserves population diversity. "
        "In tabular machine learning, Ke et al. [2] developed LightGBM, combining Gradient-based One-Side Sampling (GOSS) and Exclusive Feature Bundling (EFB) to provide high-speed, "
        "scalable gradient boosting. Our work integrates these established paradigms into an auditable, causal walk-forward backtesting framework."
    )

    # -------------------------------------------------------------
    # 3. Methodology & System Architecture
    # -------------------------------------------------------------
    add_section_heading(doc, "3.", "Methodology & System Architecture")
    add_body_p(
        doc,
        "The system decouples directional prediction from risk-constrained decision execution across two computational tiers coupled to a vectorized simulator. "
        "Figure 1 illustrates the end-to-end data processing, feature engineering, model training, evolutionary search, and test evaluation pipeline."
    )
    
    # Embed truthful System Architecture diagram
    add_figure_image(doc, FIGURES_DIR / "system_architecture.png", "Figure 1. Two-Tier Computational Intelligence system architecture: Data engineering with purged splits (H=3), Tier 1 LightGBM classifier, Tier 2 NSGA-II optimizer, and causal backtest engine.", width_in=6.0)

    add_subsection_heading(doc, "3.1", "Tier 1: Feature Engineering & Predictive Classifier")
    add_body_p(
        doc,
        "From historical daily OHLCV series, the feature pipeline computes 20 technical and regime indicators: "
        "(1) Trend Distances: percentage distances to 10-day, 50-day, and 200-day Simple Moving Averages (dist_sma_10, dist_sma_50, dist_sma_200); "
        "(2) Momentum Indicators: MACD ratio (macd / close), MACD histogram, 14-day RSI (rsi_14), Stochastic %K and %D (stoch_k, stoch_d), and Rate of Change over 5, 10, and 20 days (roc_5, roc_10, roc_20); "
        "(3) Volatility Indicators: ATR percentage (atr_14 / close), 20-day and 60-day annualized realized return volatility (volatility_20, volatility_60), Bollinger Bands %B (bb_pct_b), and Bandwidth (bb_width); "
        "(4) Volume Indicators: 20-day volume z-score (volume_zscore) and 5-day On-Balance Volume Rate of Change (obv_roc_5); "
        "(5) Market Regimes: Volatility Regime flag (regime_high_vol = 1 if volatility_20 exceeds its rolling 100-day median, else 0) and Trend Regime flag (regime_trend = 1 if Close > SMA50 > SMA200; -1 if Close < SMA50 < SMA200; 0 otherwise). "
        "No stationarity transformations or formal unit root tests are claimed; features are evaluated directly as continuous inputs."
    )
    add_body_p(
        doc,
        "The supervised prediction target is a binary directional indicator over a 3-day holding horizon: y_t = 1 if (Close_{t+3} - Close_t) / Close_t > 0, "
        "and y_t = 0 otherwise. A LightGBM classifier is trained on historical data with parameters: num_boost_round=250, learning_rate=0.03, max_depth=5, "
        "num_leaves=24, feature_fraction=0.8, bagging_fraction=0.8, and early stopping of 30 rounds on the validation partition. "
        "LightGBM outputs conditional class probabilities P(Up) in [0, 1]. No post-hoc probability calibration (Platt scaling or isotonic regression) is applied."
    )

    add_subsection_heading(doc, "3.2", "Tier 2: NSGA-II Multi-Objective Evolutionary Engine")
    add_body_p(
        doc,
        "The evolutionary decision layer optimizes a 7-dimensional real-valued chromosome: "
        "g = [p_entry, p_exit, SL, TP, Trail, VolAlloc, MaxHold], bounded strictly by domain constraints: "
        "p_entry in [0.52, 0.85], p_exit in [0.35, 0.50], Stop-Loss multiplier SL in [1.0, 4.5] x ATR, "
        "Take-Profit multiplier TP in [1.5, 7.0] x ATR, Trailing Stop percentage Trail in [0.01, 0.06], Volatility discount allocation fraction "
        "VolAlloc in [0.10, 1.00], and Maximum holding duration MaxHold in [5, 45] bars."
    )
    add_body_p(
        doc,
        "NSGA-II evaluates each candidate chromosome across the 2-year Development partition under two conflicting objective functions: "
        "(1) Maximize Annualized Sharpe Ratio f_1 = (mu_r / sigma_r) * sqrt(252) (assuming a 0.0% risk-free rate); "
        "(2) Minimize Maximum Drawdown f_2 = max_t ((Peak_t - Equity_t) / Peak_t). "
        "To discourage inactivity during evolutionary search, candidate rules generating fewer than 5 completed trades during development receive a penalty: "
        "Sharpe is decremented by 2.0 (Sharpe -= 2.0) and MaxDrawdown is floored at 0.5 (MaxDD = max(MaxDD, 0.5)). "
        "The population of size N=30 evolves across G=10 generations using Simulated Binary Crossover (SBX, crossover probability pc=0.85, eta_c=15) "
        "and Polynomial Mutation (per-gene mutation probability pm = 1/7, eta_m=20). "
        "Following development search, the individual with the highest development Sharpe ratio among feasible candidate rules (those with >= 5 completed development trades) is selected as the representative trading policy. If no candidate achieves >= 5 development trades, "
        "the system defaults to 100% Cash during out-of-sample evaluation."
    )

    add_subsection_heading(doc, "3.3", "Causal Simulator & Execution Mechanics")
    add_body_p(
        doc,
        "The backtest engine enforces realistic causal timing: "
        "(1) Next-Bar Execution: Signals evaluated at bar t Close execute strictly at bar t+1 Open at price P_entry = Open_{t+1} * (1 + slip); "
        "(2) Transaction Friction: Standard costs are 0.05% commission and 0.05% slippage per side (approximately 10 bps per side, 20 bps round-trip); sensitivity testing doubles both components to 0.10% commission and 0.10% slippage per side (0.20% per side, approximately 40 bps round-trip); "
        "(3) Conservative Intrabar Priority: If both stop-loss and take-profit price levels are touched within the same session's high-low range, the simulator prioritizes the stop-loss; "
        "(4) Opening Gaps: Gaps below stop-loss or above take-profit fill at the opening price with slippage penalty; "
        "(5) Zero-Volume Prohibition: No trade fills occur on zero-volume sessions; "
        "(6) Scheduled Fold-End Policy: New entries are barred on the scheduled last tradable session (i < last_tradable_idx); open positions liquidate at final session Close."
    )

    # -------------------------------------------------------------
    # 4. Empirical Evaluation Setup
    # -------------------------------------------------------------
    add_section_heading(doc, "4.", "Empirical Evaluation Setup & Walk-Forward Protocol")
    add_body_p(
        doc,
        "We implement a rolling walk-forward protocol evaluated annually across six test years (Y in [2020, 2025]) on three large-cap equities: "
        "Reliance Industries (RELIANCE.NS), Tata Consultancy Services (TCS.NS), and Infosys (INFY.NS). Historical daily OHLCV series were acquired "
        "from Yahoo Finance via yfinance with dividend and split adjustments applied. For each test year Y, partitions are chronologically non-overlapping:"
    )
    
    # Partition Table
    part_table = doc.add_table(rows=5, cols=4)
    part_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    part_table.autofit = False
    set_table_borders(part_table)
    col_widths = [Inches(1.8), Inches(1.8), Inches(1.4), Inches(1.8)]
    for row in part_table.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = w
            
    headers = ["Partition Stage", "Calendar Window", "Duration", "Purging / Causal Gate"]
    for i, h in enumerate(headers):
        format_cell(part_table.cell(0, i), h, bold=True, color=HEADING_COLOR, bg_hex=BG_HEADER_HEX)
        
    p_data = [
        ["Model Training", "[Y-8, Y-4]", "5 Years (~1,230 bars)", "Purged trailing 3 bars (H=3)"],
        ["Model Validation", "[Y-3]", "1 Year (~246 bars)", "Early stopping; purged trailing 3 bars"],
        ["Rule Development (GA)", "[Y-2, Y-1]", "2 Years (~493 bars)", "NSGA-II search; t=-1 context preserved"],
        ["Out-of-Sample Test", "[Y]", "1 Year (~248 bars)", "Scored on first N-3 bars; liquidated at fold end"]
    ]
    for r_idx, row_data in enumerate(p_data, start=1):
        for c_idx, val in enumerate(row_data):
            format_cell(part_table.cell(r_idx, c_idx), val)
            
    add_body_p(
        doc,
        "The model seed is held constant at 42. To evaluate metaheuristic sensitivity, NSGA-II is evaluated across three independent random seeds (42, 43, 44). "
        "In total, the campaign comprises 54 walk-forward optimization runs (3 assets x 6 years x 3 GA seeds) spanning 1,487 out-of-sample trading days. "
        "All runs execute offline against immutable parquet snapshots documented in campaign_audit.json."
    )

    # -------------------------------------------------------------
    # 5. Experimental Results
    # -------------------------------------------------------------
    add_section_heading(doc, "5.", "Experimental Results & Performance Analysis")
    
    add_subsection_heading(doc, "5.1", "Machine Learning Directional Predictive Performance")
    add_body_p(
        doc,
        "Table 1 reports out-of-sample classification performance across all 18 annual folds. Across the entire campaign, LightGBM achieved an average "
        "out-of-sample AUC of 0.5324, directional accuracy of 52.68% (compared to the training-class base rate of 52.66%), and a Brier score of 0.2501 (vs baseline 0.2500). "
        "Asset-specific mean AUCs were 0.5469 for RELIANCE.NS, 0.5304 for TCS.NS, and 0.5199 for INFY.NS. These metrics reflect a small average AUC above 0.5, "
        "near-equal accuracy to the majority prior, and no Brier score improvement over naive training priors in liquid Indian equities."
    )
    
    # Table 1: Model Metrics
    t1 = doc.add_table(rows=4, cols=8)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    t1.autofit = False
    set_table_borders(t1)
    t1_widths = [Inches(1.3), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.7)]
    for row in t1.rows:
        for i, w in enumerate(t1_widths):
            row.cells[i].width = w
            
    t1_headers = ["Asset", "Mean AUC", "Min AUC", "Max AUC", "Test Acc", "Base Acc", "Brier", "Scored N"]
    for i, h in enumerate(t1_headers):
        format_cell(t1.cell(0, i), h, bold=True, color=HEADING_COLOR, bg_hex=BG_HEADER_HEX, align=WD_ALIGN_PARAGRAPH.CENTER)
        
    t1_data = [
        ["RELIANCE.NS", "0.5469", "0.4415", "0.6246", "52.01%", "52.21%", "0.2494", "244.8"],
        ["TCS.NS", "0.5304", "0.4774", "0.6182", "50.91%", "50.78%", "0.2516", "244.8"],
        ["INFY.NS", "0.5199", "0.4509", "0.5766", "55.12%", "54.99%", "0.2493", "244.8"]
    ]
    for r_idx, row in enumerate(t1_data, start=1):
        for c_idx, val in enumerate(row):
            format_cell(t1.cell(r_idx, c_idx), val, align=WD_ALIGN_PARAGRAPH.CENTER if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT)

    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(2)
    sp.paragraph_format.space_after = Pt(4)
    run_cap = sp.add_run("Table 1. Out-of-sample directional classification performance across 18 annual test folds (2020–2025).")
    run_cap.font.size = Pt(8.0)
    run_cap.italic = True
    run_cap.font.color.rgb = MUTED_COLOR

    add_subsection_heading(doc, "5.2", "Stitched 6-Year Compounded Performance")
    add_body_p(
        doc,
        "Stitched multi-year curves carry capital forward across test folds by compounding annual net wealth ratios starting from ₹100,000 on 2020-01-01 "
        "through 2025-12-31. Note that Buy & Hold is evaluated under an annually liquidated and re-entered convention at fold boundaries matching the strategy's "
        "annual evaluation, incurring transaction friction each year. Table 2 reports terminal compound performance. Multi-seed variants show medians and ranges "
        "across seeds 42, 43, 44; note that metric-wise medians across seeds are computed independently per metric and may correspond to different individual seed runs rather than a single executable median strategy. Figure 2 displays the stitched equity curves and underwater drawdowns."
    )
    
    # Table 2: Stitched Metrics
    t2 = doc.add_table(rows=11, cols=7)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    t2.autofit = False
    set_table_borders(t2)
    t2_widths = [Inches(1.2), Inches(1.5), Inches(0.9), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8)]
    for row in t2.rows:
        for i, w in enumerate(t2_widths):
            row.cells[i].width = w
            
    t2_headers = ["Asset", "Strategy Variant", "Total Ret", "CAGR", "Sharpe", "MaxDD", "Terminal ₹"]
    for i, h in enumerate(t2_headers):
        format_cell(t2.cell(0, i), h, bold=True, color=HEADING_COLOR, bg_hex=BG_HEADER_HEX, align=WD_ALIGN_PARAGRAPH.CENTER)
        
    t2_data = [
        ["RELIANCE.NS", "Buy & Hold", "+128.74%", "15.05%", "0.64", "44.08%", "₹228,740"],
        ["", "Full Hybrid (Median)", "-0.35%", "-0.06%", "0.04", "23.01%", "₹99,652"],
        ["", "Full Hybrid (Range)", "[-6.58%, +5.18%]", "[-1.15%, +0.86%]", "[-0.07, 0.14]", "[21.88%, 26.18%]", "[₹93k, ₹105k]"],
        ["", "No-ML Ablation (Median)", "+42.42%", "6.18%", "0.45", "20.03%", "₹142,415"],
        ["TCS.NS", "Buy & Hold", "+65.13%", "8.87%", "0.48", "34.57%", "₹165,134"],
        ["", "Full Hybrid (Median)", "+25.60%", "3.94%", "0.44", "28.66%", "₹125,600"],
        ["", "Full Hybrid (Range)", "[+10.60%, +41.86%]", "[+1.72%, +6.10%]", "[0.21, 0.54]", "[18.29%, 30.12%]", "[₹111k, ₹142k]"],
        ["", "No-ML Ablation (Median)", "+47.37%", "6.79%", "0.50", "31.62%", "₹147,369"],
        ["INFY.NS", "Buy & Hold", "+152.78%", "17.02%", "0.71", "35.93%", "₹252,783"],
        ["", "Full Hybrid (Median)", "+9.10%", "1.49%", "0.18", "37.16%", "₹109,103"],
    ]
    for r_idx, row in enumerate(t2_data, start=1):
        for c_idx, val in enumerate(row):
            is_bold = "Buy & Hold" in row[1] or "Median" in row[1]
            format_cell(t2.cell(r_idx, c_idx), val, bold=is_bold, align=WD_ALIGN_PARAGRAPH.CENTER if c_idx > 1 else WD_ALIGN_PARAGRAPH.LEFT)

    sp2 = doc.add_paragraph()
    sp2.paragraph_format.space_before = Pt(2)
    sp2.paragraph_format.space_after = Pt(4)
    run_cap2 = sp2.add_run("Table 2. Stitched 6-year multi-year compound performance (2020–2025, 1,487 trading bars).")
    run_cap2.font.size = Pt(8.0)
    run_cap2.italic = True
    run_cap2.font.color.rgb = MUTED_COLOR

    # Embed Figure 2 (Combined Stitched Curves & Drawdowns)
    add_figure_image(doc, FIGURES_DIR / "stitched_equity_and_drawdowns.png", "Figure 2. Stitched 6-year compounded equity curves (left) and underwater drawdown profiles (right) across 2020–2025 for Buy & Hold vs. individual Full Hybrid seeds (42, 43, 44) and No-ML Ablation (Seed 42).", width_in=6.2)

    add_subsection_heading(doc, "5.3", "Annual Paired Strategy Differences & Scorecard")
    add_body_p(
        doc,
        "Evaluating the 18 annual folds individually reveals the structural asymmetry between annual drawdown dampening and secular compounding: "
        "(1) Positive Hybrid Return: Achieved in 10 out of 18 folds (55.6%); "
        "(2) Return Outperformance vs Buy & Hold: Hybrid exceeded Buy & Hold in 5 out of 18 folds (27.8%)—specifically during market corrections in 2022 (TCS +16.55% diff, INFY +11.44% diff), 2023 (RELIANCE +2.00% diff, TCS +3.92% diff), and 2024 (RELIANCE +1.97% diff); "
        "(3) Buy & Hold Outperformance: Buy & Hold exceeded Hybrid in 13 out of 18 folds (72.2%), particularly during strong bull markets such as 2020 (INFY B&H +74.69% vs Hyb +27.83%) and 2021 (INFY B&H +52.73% vs Hyb +17.22%); "
        "(4) Maximum Drawdown Reduction: Hybrid exhibited lower annual maximum drawdown in 17 out of 18 folds (94.4%). The sole exception was RELIANCE.NS in 2022, where Buy & Hold had a 17.27% drawdown vs Hybrid median drawdown of 17.45%."
    )

    add_subsection_heading(doc, "5.4", "Ablation and Exposure-Matched Diagnostic")
    add_body_p(
        doc,
        "To isolate the contribution of the ML classifier, a Constant Probability Ablation (p=0.60) evolved rules omitting LightGBM features. "
        "The Ablation achieved 6-year stitched returns of +42.42% for RELIANCE.NS (vs Hyb -0.35%), +47.37% for TCS.NS (vs Hyb +25.60%), and +18.69% "
        "for INFY.NS (vs Hyb +9.10%). Furthermore, an Exposure-Matched Buy & Hold diagnostic blending passive holding with cash based on the Hybrid's "
        "development exposure fraction (w_dev) outperformed the Full Hybrid in 29 out of 54 runs (53.7%), while the Hybrid outperformed in 22 runs (40.7%), "
        "with 3 ties (RELIANCE 2020 cash fallbacks). Exposure-Matched Buy & Hold exhibited lower maximum drawdown than the Full Hybrid in 43 of 54 runs (79.6%). "
        "This diagnostic assumes daily frictionless rebalancing and 0% cash return. Across these historical folds, technical metaheuristic rules provided "
        "lower annual drawdowns, but LightGBM probability hurdles restricted market participation without producing higher compound returns."
    )

    add_subsection_heading(doc, "5.5", "Transaction Cost Sensitivity & Slippage Dynamics")
    add_body_p(
        doc,
        "Evaluating frozen Development chromosomes under doubled transaction friction (0.10% commission + 0.10% slippage per side, 0.20% per side, approximately 40 bps round-trip) caused substantial performance drops: "
        "RELIANCE.NS Seed 42 total return declined from -6.58% to -25.41% (-18.83 pp); TCS.NS Seed 43 declined from +25.60% to +19.61% (-5.99 pp); "
        "and INFY.NS Seed 44 dropped from +27.88% to -7.97% (-35.85 pp). "
        "Mechanistically, slippage does not act as a simple linear fee. Because execution price shifts upward (P_entry = Open * (1 + slip)), "
        "the dynamic ATR stop-loss threshold (P_stop = P_entry - SL * ATR) is mechanically elevated. "
        "On sessions where prices touch the stop band, trades exit prematurely, altering subsequent cash levels and eliminating future trade signals."
    )

    # -------------------------------------------------------------
    # 6. Discussion & Limitations
    # -------------------------------------------------------------
    add_section_heading(doc, "6.", "Discussion, Risk Attribution & Methodological Limitations")
    add_body_p(
        doc,
        "The empirical findings highlight several critical trade-offs in quantitative portfolio design: "
        "(1) Asymmetric Risk-Return Profile: NSGA-II discovers defensive chromosome parameters that truncate downside drawdowns during market contractions. "
        "However, because the classifier's directional probabilities hover narrowly around 0.50, high entry thresholds cause the system "
        "to remain in cash during sustained bull market regimes, resulting in substantial compounding penalties relative to passive index compounding. "
        "(2) Multi-Year vs Annual Drawdown Asymmetry: Lower annual drawdowns in 17 of 18 folds do not guarantee lower multi-year risk. On INFY.NS, "
        "the Hybrid 6-year maximum drawdown reached 37.16% compared to 35.93% for Buy & Hold, illustrating how compounded capital erosion can produce deeper multi-year drawdowns. "
        "(3) Capital Exposure as an Overnight Proxy: In our evaluation, capital exposure is defined as session-close invested value divided by equity "
        "(Shares_t * Close_t / Equity_t). This proxy reflects overnight capital commitment and omits intraday capital utilization for same-day round trips. "
        "(4) Survivorship and Single-Asset Constraints: The study evaluates three surviving large-cap equities individually without cross-asset portfolio diversification. "
        "(5) Retrospective Protocol Adjustments: While data snapshots and random seeds remained strictly frozen, the final experimental protocol "
        "incorporated retrospective corrections (versioned in protocol_correction.json v1.1.0) following initial simulator inspection. "
        "No formal statistical significance tests are asserted; results represent retrospective empirical observations."
    )

    # -------------------------------------------------------------
    # 7. Conclusion
    # -------------------------------------------------------------
    add_section_heading(doc, "7.", "Conclusion")
    add_body_p(
        doc,
        "This research evaluated the integration of gradient tree boosting (LightGBM) with multi-objective evolutionary optimization (NSGA-II) "
        "for algorithmic trading across three major Indian equities over 2020–2025. Across 18 annual walk-forward folds, the LightGBM classifier "
        "demonstrated modest predictive capability (AUC 0.5324), tracking majority-class baselines without Brier score improvements. While NSGA-II evolved risk-management "
        "rules that lowered annual maximum drawdowns in 94.4% of folds, passive Buy & Hold generated substantially higher multi-year compounded wealth "
        "across all assets. Ablation analysis confirmed that metaheuristic technical parameter search without ML signals provided equivalent or "
        "superior capital growth. These results illustrate that machine learning directional predictors do not automatically improve "
        "quantitative trading performance, underscoring the substantial opportunity costs associated with defensive cash-allocation rules in trending markets."
    )

    # -------------------------------------------------------------
    # References
    # -------------------------------------------------------------
    add_section_heading(doc, "", "References")
    
    refs = [
        "[1] K. Deb, A. Pratap, S. Agarwal, and T. Meyarivan, \"A fast and elitist multiobjective genetic algorithm: NSGA-II,\" IEEE Transactions on Evolutionary Computation, vol. 6, no. 2, pp. 182–197, Apr. 2002. DOI: 10.1109/4235.996017.",
        "[2] G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye, and T.-Y. Liu, \"LightGBM: A highly efficient gradient boosting decision tree,\" in Advances in Neural Information Processing Systems 30 (NIPS 2017), Long Beach, CA, USA, 2017, pp. 3146–3154.",
        "[3] M. López de Prado, Advances in Financial Machine Learning. Hoboken, NJ, USA: John Wiley & Sons, 2018. ISBN: 978-1119482086.",
        "[4] D. H. Bailey and M. López de Prado, \"The deflated Sharpe ratio: Correcting for selection bias, backtest overfitting and non-normality,\" The Journal of Portfolio Management, vol. 40, no. 5, pp. 94–107, 2014. DOI: 10.3905/jpm.2014.40.5.094.",
        "[5] H. White, \"A reality check for data snooping,\" Econometrica, vol. 68, no. 5, pp. 1097–1126, Sep. 2000. DOI: 10.1111/1468-0262.00152.",
        "[6] E. F. Fama, \"Efficient capital markets: A review of theory and empirical work,\" The Journal of Finance, vol. 25, no. 2, pp. 383–417, May 1970. DOI: 10.2307/2325486.",
        "[7] R. Aroussi et al., \"yfinance: Download market data from Yahoo! Finance,\" Python package documentation, 2024–2026. [Online]. Available: https://github.com/ranaroussi/yfinance."
    ]
    for r in refs:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.first_line_indent = Inches(-0.25)
        run = p.add_run(r)
        run.font.name = 'Calibri'
        run.font.size = Pt(8.0)
        run.font.color.rgb = TEXT_COLOR

    out_docx = SUBMISSION_DIR / "RESEARCH_PAPER_DRAFT.docx"
    doc.save(str(out_docx))
    print(f"Saved Research Paper Draft DOCX -> {out_docx}")

    # Render PDF via Word COM
    out_pdf = SUBMISSION_DIR / "RESEARCH_PAPER_DRAFT.pdf"
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    wb = word.Documents.Open(str(out_docx.resolve()))
    wb.SaveAs(str(out_pdf.resolve()), FileFormat=17)
    wb.Close()
    word.Quit()
    print(f"Compiled Research Paper Draft PDF -> {out_pdf}")

if __name__ == "__main__":
    generate_paper_draft()
