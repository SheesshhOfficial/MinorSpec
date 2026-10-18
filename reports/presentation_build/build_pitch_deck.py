"""
High-End Institutional Pitch Deck Builder for Computational Intelligence Project.
Deck Title: Two-Tier Machine Learning & Multi-Objective Evolutionary Strategy Engine
Target Audience: Institutional Pitchers, Quantitative Investors, Academic Defense Jury.

Key Aesthetics:
- Deep Navy Dark Theme (#0A1128 / #101F42 / #1B2A4A) with high-contrast Crisp White text.
- Electric Cyan (#00E5FF) and Emerald Green (#00E676) accents.
- Structured Executive Cards, KPI Badges, and Embedded Publication-Grade Charts.
- 10 Comprehensive, High-Impact Slides:
  1. Executive Title & Pedigree
  2. The Quant Paradox (Problem & Inefficiencies in Retail ML)
  3. The Two-Tier Architectural Solution (System Blueprint)
  4. Feature Alpha: 20 Causal Market Microstructure & Volatility Factors
  5. Multi-Objective Genetic Discovery (NSGA-II & Pareto Frontiers)
  6. Institutional Friction Realism (Next-Bar Execution & Zero Lookahead Bias)
  7. 6-Year Empirical Campaign: Stitched Equity & Drawdown Analysis (Figure embed)
  8. Seed Robustness & Statistical Invariance (Figure embed)
  9. Evolutionary Market Lab: Interactive Real-Time Research Cockpit
  10. Institutional Roadmap, Alpha Scalability & Conclusion
"""

import os
from pathlib import Path
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# 1. Institutional Dark Palette
BG_DARK = RGBColor(10, 17, 40)          # #0A1128 Deepest midnight navy
CARD_DARK = RGBColor(18, 30, 60)        # #121E3C Elevated container
CARD_BORDER = RGBColor(35, 55, 95)      # #23375F Subtle divider
TEXT_WHITE = RGBColor(245, 247, 250)    # Crisp high-contrast title text
TEXT_MUTED = RGBColor(160, 178, 205)    # Secondary muted body text
ACCENT_CYAN = RGBColor(0, 229, 255)     # #00E5FF Electric Cyan primary highlight
ACCENT_GREEN = RGBColor(0, 230, 118)    # #00E676 Emerald Green risk/performance highlight
ACCENT_ORANGE = RGBColor(255, 145, 0)   # #FF9100 Warning / benchmark baseline
ACCENT_RED = RGBColor(255, 82, 82)      # #FF5252 Drawdown alert

FONT_MAIN = "Calibri"

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)


def create_base_slide(prs):
    """Creates a 16:9 slide with institutional dark background."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = BG_DARK
    return slide


def add_glass_card(slide, left, top, width, height, border_color=CARD_BORDER, fill_color=CARD_DARK):
    """Creates a sleek modern rounded card for containerizing content."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.color.rgb = border_color
    shape.line.width = Pt(1.2)
    return shape


def add_slide_header(slide, title, category="QUANTITATIVE RESEARCH"):
    """Adds a standardized high-impact header zone."""
    tb = slide.shapes.add_textbox(Inches(0.9), Inches(0.55), Inches(11.533), Inches(1.2))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_cat = tf.paragraphs[0]
    p_cat.text = category.upper()
    p_cat.font.name = FONT_MAIN
    p_cat.font.size = Pt(12)
    p_cat.font.bold = True
    p_cat.font.color.rgb = ACCENT_CYAN
    p_cat.space_after = Pt(4)

    p_title = tf.add_paragraph()
    p_title.text = title
    p_title.font.name = FONT_MAIN
    p_title.font.size = Pt(32)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_WHITE


def set_notes(slide, spoken_script, evidence=""):
    """Adds professional speaker notes with clear separation."""
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    full_text = spoken_script.strip()
    if evidence:
        full_text += f"\n\n[Institutional Evidence & Artifacts: {evidence}]"
    tf.text = full_text


def build_pitch_deck():
    prs = pptx.Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    # =========================================================================
    # SLIDE 1: Pitch Title & Pedigree
    # =========================================================================
    s1 = create_base_slide(prs)

    # Ambient Accent Glow card
    add_glass_card(s1, Inches(0.9), Inches(1.1), Inches(11.533), Inches(5.3), border_color=RGBColor(0, 180, 216))

    tb1 = s1.shapes.add_textbox(Inches(1.4), Inches(1.5), Inches(10.533), Inches(4.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = 0

    p_badge = tf1.paragraphs[0]
    p_badge.text = "COMPUTATIONAL INTELLIGENCE & QUANTITATIVE ASSET MANAGEMENT"
    p_badge.font.name = FONT_MAIN
    p_badge.font.size = Pt(13)
    p_badge.font.bold = True
    p_badge.font.color.rgb = ACCENT_CYAN
    p_badge.space_after = Pt(16)

    p_t1 = tf1.add_paragraph()
    p_t1.text = "Autonomous Two-Tier Market Predictor\n& Evolutionary Strategy Engine"
    p_t1.font.name = FONT_MAIN
    p_t1.font.size = Pt(38)
    p_t1.font.bold = True
    p_t1.font.color.rgb = TEXT_WHITE
    p_t1.space_after = Pt(14)

    p_sub = tf1.add_paragraph()
    p_sub.text = "High-Fidelity LightGBM Directional Forecasting & Multi-Objective NSGA-II Chromosome Discovery Under Realistic Frictions"
    p_sub.font.name = FONT_MAIN
    p_sub.font.size = Pt(18)
    p_sub.font.color.rgb = TEXT_MUTED
    p_sub.space_after = Pt(36)

    p_auth = tf1.add_paragraph()
    p_auth.text = "Principal Investigators: Ashish Ranjan   •   Khuushi Maheshwari   •   Satyanarayan H."
    p_auth.font.name = FONT_MAIN
    p_auth.font.size = Pt(18)
    p_auth.font.bold = True
    p_auth.font.color.rgb = TEXT_WHITE
    p_auth.space_after = Pt(6)

    p_inst = tf1.add_paragraph()
    p_inst.text = "Manipal Institute of Technology  |  Department of Computer Science  |  B.Tech Minor Specialization"
    p_inst.font.name = FONT_MAIN
    p_inst.font.size = Pt(15)
    p_inst.font.color.rgb = RGBColor(0, 200, 255)

    set_notes(s1, (
        "Welcome everyone. Today we present our institutional computational intelligence framework: a decoupled two-tier machine learning and evolutionary decision engine engineered specifically for systematic trading in volatile equity markets. "
        "Our work addresses the fundamental structural flaws of naive algorithmic models by separating signal probability estimation from multi-objective risk execution. "
        "I am presenting on behalf of my research partners Ashish Ranjan, Khuushi Maheshwari, and Satyanarayan H. from the Department of Computer Science at Manipal Institute of Technology."
    ), "PROJECT.md; reports/submission/VIVA_DEFENSE_NOTES.md; reports/submission/RESEARCH_PAPER_DRAFT.pdf")

    # =========================================================================
    # SLIDE 2: The Quantitative Paradox (The Problem)
    # =========================================================================
    s2 = create_base_slide(prs)
    add_slide_header(s2, "The Quantitative Paradox: Why Naive ML Trading Fails", "Market Inefficiencies & Problem Statement")

    col_w = Inches(3.6)
    col_h = Inches(4.7)
    gap = Inches(0.36)

    cards_s2 = [
        ("The Directional Trap", "High Accuracy != Profitability", 
         "Standard retail models optimize for classification accuracy. A model can boast 55% accuracy and still induce ruin if the 45% incorrect trades result in catastrophic tail-risk drawdowns.", 
         ACCENT_RED),
        ("Friction Blindness", "Zero-Cost Fantasy vs Reality", 
         "Academic backtests routinely ignore real-world execution drag. In high-turnover setups, 10–20 basis points of round-trip brokerage, spread, and adverse slippage erode gross alpha to zero.", 
         ACCENT_ORANGE),
        ("Lookahead Contamination", "Data Snooping & Overfitting", 
         "Random K-fold validation leaks future price dynamics into past training sets. Overfitted systems collapse instantly when transitioning to unseen out-of-sample live regimes.", 
         ACCENT_CYAN),
    ]

    for i, (title, sub, body, color) in enumerate(cards_s2):
        c_left = Inches(0.9) + i * (col_w + gap)
        add_glass_card(s2, c_left, Inches(1.9), col_w, col_h, border_color=color)

        tb = s2.shapes.add_textbox(c_left + Inches(0.25), Inches(2.1), col_w - Inches(0.5), col_h - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = 0

        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.name = FONT_MAIN
        p1.font.size = Pt(22)
        p1.font.bold = True
        p1.font.color.rgb = color
        p1.space_after = Pt(4)

        p2 = tf.add_paragraph()
        p2.text = sub
        p2.font.name = FONT_MAIN
        p2.font.size = Pt(14)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_WHITE
        p2.space_after = Pt(18)

        p3 = tf.add_paragraph()
        p3.text = body
        p3.font.name = FONT_MAIN
        p3.font.size = Pt(16)
        p3.font.color.rgb = TEXT_MUTED

    set_notes(s2, (
        "In algorithmic finance, naive machine learning setups face three fatal flaws. "
        "First is the directional trap: classification accuracy does not guarantee capital survival. If losses are unhedged, an accurate model blows up during flash crashes. "
        "Second is friction blindness: real trading costs twenty basis points round-trip in commissions, spreads, and slippage. Ignoring this creates phantom paper profits. "
        "Third is lookahead bias: naive cross-validation leaks tomorrow's prices into yesterday's model. "
        "Our mission was to build an institutional-grade architecture immune to all three vulnerabilities."
    ), "RESEARCH_PAPER_DRAFT.pdf Section 1; VIVA_DEFENSE_NOTES.md")

    # =========================================================================
    # SLIDE 3: The Two-Tier Architectural Solution
    # =========================================================================
    s3 = create_base_slide(prs)
    add_slide_header(s3, "Decoupled Architecture: Prediction vs. Evolutionary Control", "System Engineering")

    # Tier 1 Box
    add_glass_card(s3, Inches(0.9), Inches(1.9), Inches(5.6), Inches(4.7), border_color=ACCENT_CYAN)
    tb_t1 = s3.shapes.add_textbox(Inches(1.2), Inches(2.1), Inches(5.0), Inches(4.3))
    tf_t1 = tb_t1.text_frame
    tf_t1.word_wrap = True
    tf_t1.margin_left = tf_t1.margin_top = 0

    p = tf_t1.paragraphs[0]
    p.text = "TIER 1: PREDICTIVE INTELLIGENCE"
    p.font.name = FONT_MAIN
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p.space_after = Pt(6)

    p = tf_t1.add_paragraph()
    p.text = "LightGBM Gradient Boosted Decision Trees"
    p.font.name = FONT_MAIN
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_after = Pt(14)

    t1_bullets = [
        ("Causal Factor Engine:", " Computes 20 technical momentum, trend, and volatility features."),
        ("Directional Horizon:", " Predicts forward 3-day directional movement with strict purging."),
        ("Probabilistic Output:", " Generates continuous probability P_up in [0, 1] without rigid binary entry triggers."),
        ("Validation Tuning:", " Early-stopped on dedicated validation splits to guarantee generalization."),
    ]
    for lead, rest in t1_bullets:
        p = tf_t1.add_paragraph()
        r1 = p.add_run()
        r1.text = "• " + lead
        r1.font.bold = True
        r1.font.color.rgb = ACCENT_CYAN
        r1.font.size = Pt(15)
        r2 = p.add_run()
        r2.text = rest
        r2.font.color.rgb = TEXT_MUTED
        r2.font.size = Pt(15)
        p.space_after = Pt(8)

    # Tier 2 Box
    add_glass_card(s3, Inches(6.8), Inches(1.9), Inches(5.6), Inches(4.7), border_color=ACCENT_GREEN)
    tb_t2 = s3.shapes.add_textbox(Inches(7.1), Inches(2.1), Inches(5.0), Inches(4.3))
    tf_t2 = tb_t2.text_frame
    tf_t2.word_wrap = True
    tf_t2.margin_left = tf_t2.margin_top = 0

    p = tf_t2.paragraphs[0]
    p.text = "TIER 2: EVOLUTIONARY DECISION ENGINE"
    p.font.name = FONT_MAIN
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p.space_after = Pt(6)

    p = tf_t2.add_paragraph()
    p.text = "NSGA-II Multi-Objective Optimization"
    p.font.name = FONT_MAIN
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_after = Pt(14)

    t2_bullets = [
        ("7-Gene Chromosomes:", " Dynamically optimizes entry, exit, stop-loss, profit target, and holding bounds."),
        ("Multi-Objective Frontier:", " Simultaneously maximizes Sharpe Ratio while minimizing Maximum Drawdown."),
        ("Survival of the Fittest:", " Fast non-dominated sorting and crowding distance preserve frontier diversity."),
        ("Frozen Primary Selection:", " Best candidate on Development partition is frozen before Out-of-Sample testing."),
    ]
    for lead, rest in t2_bullets:
        p = tf_t2.add_paragraph()
        r1 = p.add_run()
        r1.text = "• " + lead
        r1.font.bold = True
        r1.font.color.rgb = ACCENT_GREEN
        r1.font.size = Pt(15)
        r2 = p.add_run()
        r2.text = rest
        r2.font.color.rgb = TEXT_MUTED
        r2.font.size = Pt(15)
        p.space_after = Pt(8)

    set_notes(s3, (
        "Our core architectural breakthrough is decoupling forecasting from trading rules. "
        "In Tier One, LightGBM is trained solely to estimate conditional upward probability over a three-day forward horizon. It never decides when to buy or sell. "
        "In Tier Two, NSGA-II takes this probability surface and evolves a seven-gene trading chromosome. "
        "It searches simultaneously for two conflicting goals: maximizing risk-adjusted return through Sharpe ratio, and minimizing peak capital impairment through Maximum Drawdown. "
        "This separation guarantees that trading rules adapt directly to market risk regimes."
    ), "src/pipeline.py; src/evolutionary_core.py; src/predictor.py")

    # =========================================================================
    # SLIDE 4: Feature Alpha: 20 Causal Quantitative Factors
    # =========================================================================
    s4 = create_base_slide(prs)
    add_slide_header(s4, "Feature Engineering: 20 Microstructure & Volatility Factors", "Quantitative Alpha Signals")

    f_groups = [
        ("Trend & Moving Distances", ACCENT_CYAN, [
            "dist_sma_10: Normalized distance to 10-day SMA",
            "dist_sma_50: Distance to medium-term 50-day SMA",
            "dist_ema_20: Exponential smoothing trend anchor",
            "sma_ratio: Ratio between SMA_10 and SMA_50",
        ]),
        ("Momentum & Oscillators", ACCENT_GREEN, [
            "rsi_14: 14-period Relative Strength Index",
            "roc_5 / roc_20: Short & medium Rate of Change",
            "macd / macd_signal / macd_hist: Moving convergence",
            "stoch_k / stoch_d: Stochastic momentum bounds",
        ]),
        ("Volatility & Dispersion", ACCENT_ORANGE, [
            "atr_pct: 14-day Average True Range / Close price",
            "bb_width / bb_pct: Bollinger band volatility spread",
            "historical_vol_20: 20-day annualized log-return sigma",
            "Dynamic Volatility Stops: Calibrated intraday risk",
        ]),
        ("Volume & Regime Filters", RGBColor(180, 136, 255), [
            "volume_ratio_20: Current volume / 20-day volume SMA",
            "obv_slope_10: 10-day slope of On-Balance Volume",
            "regime_high_vol: Binary regime switch (60-day median)",
            "Liquidity Validation: Zero-volume trade prohibition",
        ]),
    ]

    c_w = Inches(2.7)
    c_h = Inches(4.7)
    c_gap = Inches(0.24)

    for i, (g_title, g_color, g_items) in enumerate(f_groups):
        g_left = Inches(0.9) + i * (c_w + c_gap)
        add_glass_card(s4, g_left, Inches(1.9), c_w, c_h, border_color=g_color)

        tb = s4.shapes.add_textbox(g_left + Inches(0.18), Inches(2.1), c_w - Inches(0.36), c_h - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = 0

        p = tf.paragraphs[0]
        p.text = g_title
        p.font.name = FONT_MAIN
        p.font.size = Pt(17)
        p.font.bold = True
        p.font.color.rgb = g_color
        p.space_after = Pt(14)

        for item in g_items:
            p = tf.add_paragraph()
            p.text = "• " + item
            p.font.name = FONT_MAIN
            p.font.size = Pt(13)
            p.font.color.rgb = TEXT_MUTED
            p.space_after = Pt(8)

    set_notes(s4, (
        "Raw price data is transformed through a causal pipeline computing twenty non-linear technical features grouped into four financial families. "
        "Trend features normalize moving average distances to capture mean-reversion. "
        "Momentum oscillators quantify rate-of-change and overbought exhaustion. "
        "Volatility dispersion metrics, especially Average True Range percentage, feed directly into both the machine learning model and the evolutionary stop-loss multipliers. "
        "Finally, volume ratios and regime filters prevent trades during illiquid market dislocations. All features strictly evaluate at bar close without forward leakage."
    ), "src/feature_pipeline.py; reports/ui/UI_REDESIGN_NOTES.md")

    # =========================================================================
    # SLIDE 5: Multi-Objective Genetic Discovery (The 7-Gene Chromosome)
    # =========================================================================
    s5 = create_base_slide(prs)
    add_slide_header(s5, "Multi-Objective Evolutionary Search: The 7-Gene Chromosome", "Genetic Decision Engine (NSGA-II)")

    # Left: The Chromosome Spec Table
    t_shape = s5.shapes.add_table(8, 3, Inches(0.9), Inches(1.9), Inches(6.8), Inches(4.7))
    tbl = t_shape.table
    tbl.columns[0].width = Inches(2.2)
    tbl.columns[1].width = Inches(1.4)
    tbl.columns[2].width = Inches(3.2)

    gene_data = [
        ["Gene Parameter", "Range", "Institutional Purpose"],
        ["g0: entry_prob_threshold", "[0.50, 0.80]", "Min ML probability required to buy"],
        ["g1: exit_prob_threshold", "[0.20, 0.50]", "Probability floor triggering early exit"],
        ["g2: atr_stop_loss_mult", "[1.0, 4.0]", "Volatility-adaptive stop loss multiplier"],
        ["g3: atr_take_profit_mult", "[2.0, 8.0]", "Reward-to-risk profit target barrier"],
        ["g4: trailing_stop_pct", "[1.0%, 10.0%]", "Peak unrealized gain lock-in threshold"],
        ["g5: capital_allocation", "[10%, 100%]", "Portfolio equity fraction committed"],
        ["g6: max_holding_period", "[5, 60] bars", "Calendar bar liquidation timeout"],
    ]

    for r_idx, row in enumerate(gene_data):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.font.name = FONT_MAIN
            if r_idx == 0:
                p.font.size = Pt(14)
                p.font.bold = True
                p.font.color.rgb = ACCENT_CYAN
                cell.fill.solid()
                cell.fill.fore_color.rgb = CARD_DARK
            else:
                p.font.size = Pt(13)
                p.font.color.rgb = TEXT_WHITE if c_idx == 0 else TEXT_MUTED
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(14, 24, 48)

    # Right: Pareto Mechanics Card
    add_glass_card(s5, Inches(8.0), Inches(1.9), Inches(4.433), Inches(4.7), border_color=ACCENT_CYAN)
    tb_pm = s5.shapes.add_textbox(Inches(8.3), Inches(2.1), Inches(3.833), Inches(4.3))
    tf_pm = tb_pm.text_frame
    tf_pm.word_wrap = True
    tf_pm.margin_left = tf_pm.margin_top = 0

    p = tf_pm.paragraphs[0]
    p.text = "PARETO OPTIMIZATION MECHANICS"
    p.font.name = FONT_MAIN
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p.space_after = Pt(10)

    p_body = [
        "Simulated Binary Crossover (SBX, eta=15) and Polynomial Mutation (eta=20) evolve bounded continuous chromosomes.",
        "Crowding Distance sorting ensures broad coverage across both aggressive high-Sharpe and conservative low-drawdown profiles.",
        "Selection Governance: Primary candidate is selected on the Development partition (highest Sharpe with >= 3 trades) and strictly FROZEN prior to Out-of-Sample Test evaluation.",
        "Eliminates cherry-picking: Test evaluation is single-pass and unalterable.",
    ]
    for b in p_body:
        p = tf_pm.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_MAIN
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_MUTED
        p.space_after = Pt(10)

    set_notes(s5, (
        "Each trading rule is encoded as a continuous seven-gene chromosome. "
        "The first two genes control entry and exit probability gates. "
        "The next three govern adaptive risk: Average True Range stop losses, profit targets, and trailing stops. "
        "The final two manage capital sizing and duration limits. "
        "Using Simulated Binary Crossover and Polynomial Mutation, NSGA-II sorts non-dominated solutions across multiple generations. "
        "Crucially, our selection governance freezes the primary strategy on the development partition before testing. We never cherry-pick test results."
    ), "src/evolutionary_core.py; ui/metadata.py")

    # =========================================================================
    # SLIDE 6: Institutional Realism & Purged Protocol
    # =========================================================================
    s6 = create_base_slide(prs)
    add_slide_header(s6, "Institutional Realism: Eliminating Frictions & Lookahead Bias", "Execution Mechanics")

    pillars = [
        ("Next-Bar Open Execution", ACCENT_CYAN, 
         "Signals calculated at bar t-1 Close are executed strictly at bar t Open. Intraday execution delay is fully modeled, preventing zero-latency execution fallacies."),
        ("20 bps Friction Drag", ACCENT_ORANGE, 
         "Every trade incurs 10 bps broker commission and 10 bps adverse slippage (20 bps round-trip). High-frequency over-trading is systematically penalized."),
        ("Intrabar Conflict Priority", ACCENT_RED, 
         "If bar t Low breaches the stop-loss while High breaches the profit target, the simulator conservatively assumes the stop loss hit first, preventing optimistic fill bias."),
        ("4-Way Chronological Purging", ACCENT_GREEN, 
         "Data is split into Train (~50%), Validation (~15%), Development (~15%), and Test (~20%) with 3-bar purged buffers between partitions to prevent label overlap."),
    ]

    for i, (p_title, p_col, p_desc) in enumerate(pillars):
        r_top = Inches(1.9) + (i // 2) * Inches(2.4)
        r_left = Inches(0.9) + (i % 2) * Inches(5.9)
        add_glass_card(s6, r_left, r_top, Inches(5.6), Inches(2.15), border_color=p_col)

        tb = s6.shapes.add_textbox(r_left + Inches(0.25), r_top + Inches(0.2), Inches(5.1), Inches(1.75))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = 0

        p = tf.paragraphs[0]
        p.text = p_title
        p.font.name = FONT_MAIN
        p.font.size = Pt(20)
        p.font.bold = True
        p.font.color.rgb = p_col
        p.space_after = Pt(6)

        p = tf.add_paragraph()
        p.text = p_desc
        p.font.name = FONT_MAIN
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_MUTED

    set_notes(s6, (
        "To satisfy institutional standards, our backtest engine implements four uncompromising principles. "
        "First, next-bar open execution: signals generated at close fill strictly at the next open. "
        "Second, real transaction friction: twenty basis points deducted per round trip. "
        "Third, conservative intrabar conflict handling: if price hits both stop-loss and profit target in the same bar, we assume the loss triggered first. "
        "Fourth, four-way chronological partitioning with three-bar purging buffers, eliminating label leakage between training, validation, development, and testing."
    ), "src/backtest_engine.py; tests/test_execution_mechanics.py")

    # =========================================================================
    # SLIDE 7: 6-Year Empirical Campaign (Stitched Equity Curves)
    # =========================================================================
    s7 = create_base_slide(prs)
    add_slide_header(s7, "6-Year Retrospective Campaign: Capital Preservation Over Beta", "Empirical Findings (2020–2025)")

    # Left: Embedded Stitched Equity Chart
    fig_equity = Path("reports/experiments/figures/stitched_equity_curves.png")
    if fig_equity.exists():
        s7.shapes.add_picture(str(fig_equity), Inches(0.9), Inches(1.8), Inches(6.5), Inches(5.0))

    # Right: Institutional Takeaways Card
    add_glass_card(s7, Inches(7.7), Inches(1.8), Inches(4.733), Inches(5.0), border_color=ACCENT_GREEN)
    tb_res = s7.shapes.add_textbox(Inches(8.0), Inches(2.0), Inches(4.133), Inches(4.6))
    tf_res = tb_res.text_frame
    tf_res.word_wrap = True
    tf_res.margin_left = tf_res.margin_top = 0

    p = tf_res.paragraphs[0]
    p.text = "EMPIRICAL PERFORMANCE SUMMARY"
    p.font.name = FONT_MAIN
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p.space_after = Pt(12)

    findings = [
        ("The Return Reality:", " Passive Buy & Hold generated higher raw returns (Reliance +128.7%, TCS +65.1%, Infosys +152.8%) due to a multi-year secular bull market."),
        ("The Drawdown Victory:", " Hybrid strategies demonstrated superior capital preservation, slashing maximum drawdown in 17 out of 18 annual test comparisons."),
        ("Downside Decoupling:", " During major equity downturns (2020 COVID shock and 2022 tech sector corrections), the system automatically rotated to cash."),
        ("Risk-Adjusted Alpha:", " Lower portfolio volatility and controlled exposure provide institutions with asymmetric downside protection without naked market risk."),
    ]
    for lead, body in findings:
        p = tf_res.add_paragraph()
        r1 = p.add_run()
        r1.text = "• " + lead
        r1.font.bold = True
        r1.font.color.rgb = TEXT_WHITE
        r1.font.size = Pt(14)
        r2 = p.add_run()
        r2.text = body
        r2.font.color.rgb = TEXT_MUTED
        r2.font.size = Pt(13)
        p.space_after = Pt(8)

    set_notes(s7, (
        "Here are the empirical results from our six-year retrospective study across eighteen annual folds from 2020 through 2025. "
        "We maintain total intellectual honesty: passive buy-and-hold achieved higher cumulative returns because Indian equities experienced a powerful secular bull market. "
        "However, our evolutionary hybrid system accomplished its core mission: superior capital preservation. "
        "Across seventeen out of eighteen annual evaluations, our strategy delivered lower peak drawdowns by rotating to cash during downturns like the 2020 crash and 2022 bear market."
    ), "reports/experiments/results/stitched_aggregate_metrics.csv; paired_annual_comparisons.csv")

    # =========================================================================
    # SLIDE 8: Underwater Drawdowns & Seed Invariance
    # =========================================================================
    s8 = create_base_slide(prs)
    add_slide_header(s8, "Drawdown Profiles & Seed Invariance: Proof of Resilience", "Risk Analytics & Robustness")

    fig_dd = Path("reports/experiments/figures/underwater_drawdowns.png")
    if fig_dd.exists():
        s8.shapes.add_picture(str(fig_dd), Inches(0.9), Inches(1.8), Inches(6.5), Inches(5.0))

    # Right: Statistical Rigor
    add_glass_card(s8, Inches(7.7), Inches(1.8), Inches(4.733), Inches(5.0), border_color=ACCENT_CYAN)
    tb_st = s8.shapes.add_textbox(Inches(8.0), Inches(2.0), Inches(4.133), Inches(4.6))
    tf_st = tb_st.text_frame
    tf_st.word_wrap = True
    tf_st.margin_left = tf_st.margin_top = 0

    p = tf_st.paragraphs[0]
    p.text = "STATISTICAL STABILITY EVIDENCE"
    p.font.name = FONT_MAIN
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p.space_after = Pt(12)

    stats = [
        ("Underwater Drawdown Profiles:", " As shown in the chart, buy-and-hold suffered devastating drawdowns exceeding 30% to 44%. The hybrid curve remained flat and protected during crises."),
        ("54 Independent Runs:", " Evaluated across 3 distinct random seeds (42, 43, 44) over 18 folds. Verified that performance is structural, not a random seed anomaly."),
        ("Ablation Benchmark:", " Ablation tests without ML directional probabilities show higher turnover and severe cost degradation, proving LightGBM's filtering value."),
        ("Cost Sensitivity (2x Friction):", " Tested under aggressive 40 bps round-trip drag; strategy maintains positive Sharpe ratios, proving institutional execution viability."),
    ]
    for lead, body in stats:
        p = tf_st.add_paragraph()
        r1 = p.add_run()
        r1.text = "• " + lead
        r1.font.bold = True
        r1.font.color.rgb = TEXT_WHITE
        r1.font.size = Pt(14)
        r2 = p.add_run()
        r2.text = body
        r2.font.color.rgb = TEXT_MUTED
        r2.font.size = Pt(13)
        p.space_after = Pt(8)

    set_notes(s8, (
        "The underwater drawdown curves on the left visually prove the asymmetric defense of our model. "
        "While passive buy-and-hold plunged forty-four percent in Reliance and thirty-four percent in Infosys, our hybrid strategy remained shielded. "
        "Furthermore, we validated fifty-four independent runs across three random seeds to confirm statistical stability. "
        "Ablation studies without machine learning collapsed under transaction costs, confirming that Tier One directional forecasting is essential for filtering unprofitable trades."
    ), "reports/experiments/figures/underwater_drawdowns.png; reports/experiments/results/campaign_raw_results.json")

    # =========================================================================
    # SLIDE 9: Evolutionary Market Lab (Interactive Cockpit)
    # =========================================================================
    s9 = create_base_slide(prs)
    add_slide_header(s9, "Evolutionary Market Lab: Interactive Quant Cockpit", "Product Demonstration & Tooling")

    fig_ui = Path("reports/ui/strategy_explorer_final.png")
    if fig_ui.exists():
        s9.shapes.add_picture(str(fig_ui), Inches(0.9), Inches(1.8), Inches(6.5), Inches(5.0))

    # Right: Dashboard Architecture Card
    add_glass_card(s9, Inches(7.7), Inches(1.8), Inches(4.733), Inches(5.0), border_color=ACCENT_GREEN)
    tb_ui = s9.shapes.add_textbox(Inches(8.0), Inches(2.0), Inches(4.133), Inches(4.6))
    tf_ui = tb_ui.text_frame
    tf_ui.word_wrap = True
    tf_ui.margin_left = tf_ui.margin_top = 0

    p = tf_ui.paragraphs[0]
    p.text = "LIVE RESEARCH WORKSPACE"
    p.font.name = FONT_MAIN
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p.space_after = Pt(12)

    ui_points = [
        ("Real-Time Execution:", " Single-split interactive backtesting engine powered by Streamlit and Numba-accelerated simulation kernels."),
        ("5 Specialized Tabs:", " Overview KPIs, Strategy Explorer (Pareto trade-offs), Model Insights (feature gains), Trade Journal, and Methodology."),
        ("One-Click Native Launcher:", " Packaged with run_app.bat for direct double-click desktop execution on Windows."),
        ("Deterministic Testing:", " Verified with 35 automated offline unit and integration tests (zero external network reliance during audits)."),
    ]
    for lead, body in ui_points:
        p = tf_ui.add_paragraph()
        r1 = p.add_run()
        r1.text = "• " + lead
        r1.font.bold = True
        r1.font.color.rgb = TEXT_WHITE
        r1.font.size = Pt(14)
        r2 = p.add_run()
        r2.text = body
        r2.font.color.rgb = TEXT_MUTED
        r2.font.size = Pt(13)
        p.space_after = Pt(8)

    set_notes(s9, (
        "To operationalize this research, we engineered Evolutionary Market Lab, a responsive quantitative web cockpit built on Streamlit. "
        "It features five structured modules: an overview KPI deck, a strategy explorer mapping real-time Pareto frontiers, model diagnostics, a detailed trade audit journal with CSV exports, and full methodology documentation. "
        "The platform launches instantly via run_app.bat and is fortified by thirty-five automated offline unit and integration tests, ensuring flawless operational stability."
    ), "app.py; run_app.bat; tests/test_ui_app.py")

    # =========================================================================
    # SLIDE 10: Institutional Roadmap, Scalability & Conclusion
    # =========================================================================
    s10 = create_base_slide(prs)
    add_slide_header(s10, "Institutional Roadmap: Alpha Scaling & Commercialization", "Summary & Next Steps")

    next_steps = [
        ("Universe Expansion", ACCENT_CYAN, 
         "Scale from 3 single-stock universes to the full NIFTY 50 and S&P 500 constituents with cross-sectional rank portfolio rebalancing."),
        ("Macroeconomic Overlays", ACCENT_GREEN, 
         "Incorporate yield curve spreads, RBI interest rate decisions, and crude oil volatility indices into Tier 1 feature space."),
        ("Execution Microstructure", ACCENT_ORANGE, 
         "Integrate intraday tick data and TWAP/VWAP execution algorithms for institutional large-block order routing."),
        ("Commercial Thesis", RGBColor(180, 136, 255), 
         "Delivers asymmetric wealth preservation for conservative capital seeking high Sharpe downside protection in volatile emerging markets."),
    ]

    for i, (p_title, p_col, p_desc) in enumerate(next_steps):
        r_top = Inches(1.9) + (i // 2) * Inches(2.1)
        r_left = Inches(0.9) + (i % 2) * Inches(5.9)
        add_glass_card(s10, r_left, r_top, Inches(5.6), Inches(1.9), border_color=p_col)

        tb = s10.shapes.add_textbox(r_left + Inches(0.25), r_top + Inches(0.18), Inches(5.1), Inches(1.5))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = 0

        p = tf.paragraphs[0]
        p.text = p_title
        p.font.name = FONT_MAIN
        p.font.size = Pt(19)
        p.font.bold = True
        p.font.color.rgb = p_col
        p.space_after = Pt(4)

        p = tf.add_paragraph()
        p.text = p_desc
        p.font.name = FONT_MAIN
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_MUTED

    # Bottom closing line
    add_glass_card(s10, Inches(0.9), Inches(6.15), Inches(11.533), Inches(0.85), border_color=ACCENT_CYAN, fill_color=RGBColor(12, 22, 48))
    tb_c = s10.shapes.add_textbox(Inches(1.2), Inches(6.25), Inches(10.933), Inches(0.65))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True
    p = tf_c.paragraphs[0]
    p.text = "Thank you for your consideration  —  We welcome your questions & quantitative due diligence."
    p.font.name = FONT_MAIN
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.alignment = PP_ALIGN.CENTER

    set_notes(s10, (
        "In conclusion, we have built a rigorous, verified, and institutional-ready computational intelligence framework. "
        "Our roadmap focuses on expanding to multi-asset portfolios across the NIFTY 50 and incorporating macroeconomic regime signals. "
        "This system offers a powerful commercial proposition for institutions: superior downside risk control and consistent capital preservation in turbulent markets. "
        "Thank you for your time and quantitative due diligence. We are now open for your questions."
    ), "reports/submission/RESEARCH_PAPER_DRAFT.pdf Section 6; reports/submission/COLLEGE_PROJECT_REPORT.pdf")

    # Output save
    out_dir = Path("reports/submission")
    out_dir.mkdir(parents=True, exist_ok=True)
    pptx_path = out_dir / "PROFESSIONAL_PITCH_DECK.pptx"
    prs.save(str(pptx_path))
    print(f"Professional pitch deck generated successfully -> {pptx_path}")
    return pptx_path


if __name__ == "__main__":
    build_pitch_deck()
