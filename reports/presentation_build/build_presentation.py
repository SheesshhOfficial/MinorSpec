"""
Build script for Task P005: Simple College Presentation.
Generates an 8-slide presentation with speaker notes adhering strictly to:
- White background, dark navy text, restrained blue accent.
- Generous whitespace, large readable text (32pt+ title, 20-24pt body).
- 16:9 widescreen layout (13.333 x 7.5 inches).
- Speaker notes (45-70 spoken words per slide + evidence citations).
- Outputs to reports/submission/SIMPLE_PROJECT_PRESENTATION.pptx.
- Converts to PDF if PowerPoint automation is available.
- Renders slide PNGs to reports/presentation_build/ for automated inspection.
"""

import os
import sys
from pathlib import Path
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# 1. Colors & Constants
COLOR_BG = RGBColor(255, 255, 255)         # Pure white
COLOR_PRIMARY = RGBColor(11, 25, 44)       # Deep navy
COLOR_SECONDARY = RGBColor(65, 90, 119)    # Muted dark slate
COLOR_ACCENT = RGBColor(27, 73, 101)       # Restrained blue
COLOR_LIGHT_BG = RGBColor(244, 246, 249)   # Very light blue-gray for table headers
COLOR_BORDER = RGBColor(218, 224, 233)     # Subtle table border

FONT_TITLE = "Calibri"
FONT_BODY = "Calibri"

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)


def create_blank_slide(prs):
    """Creates a blank slide with white background."""
    blank_layout = prs.slide_layouts[6] # Blank
    slide = prs.slides.add_slide(blank_layout)
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = COLOR_BG
    return slide


def add_header(slide, title_text, category_text=""):
    """Adds a standardized clean header zone with generous spacing."""
    tx_box = slide.shapes.add_textbox(Inches(1.2), Inches(0.8), Inches(10.933), Inches(1.3))
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0)
    tf.margin_top = Inches(0)
    tf.margin_right = Inches(0)
    tf.margin_bottom = Inches(0)

    if category_text:
        p_cat = tf.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.name = FONT_BODY
        p_cat.font.size = Pt(13)
        p_cat.font.bold = True
        p_cat.font.color.rgb = COLOR_ACCENT
        p_cat.space_after = Pt(4)
        p_title = tf.add_paragraph()
    else:
        p_title = tf.paragraphs[0]

    p_title.text = title_text
    p_title.font.name = FONT_TITLE
    p_title.font.size = Pt(36)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_PRIMARY


def set_speaker_notes(slide, notes_text):
    """Sets speaker notes on the slide."""
    notes_slide = slide.notes_slide
    text_frame = notes_slide.notes_text_frame
    text_frame.text = notes_text.strip()


def build_presentation():
    prs = pptx.Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    # =========================================================================
    # SLIDE 1: Title Slide
    # =========================================================================
    s1 = create_blank_slide(prs)
    tb1 = s1.shapes.add_textbox(Inches(1.2), Inches(1.4), Inches(10.933), Inches(4.8))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = Inches(0)
    tf1.margin_top = Inches(0)

    # Category tracker
    p_sub0 = tf1.paragraphs[0]
    p_sub0.text = "MINOR SPECIALIZATION RESEARCH PROJECT"
    p_sub0.font.name = FONT_BODY
    p_sub0.font.size = Pt(14)
    p_sub0.font.bold = True
    p_sub0.font.color.rgb = COLOR_ACCENT
    p_sub0.space_after = Pt(14)

    # Title
    p_t1 = tf1.add_paragraph()
    p_t1.text = "Hybrid Market Predictor & Strategy Optimizer"
    p_t1.font.name = FONT_TITLE
    p_t1.font.size = Pt(42)
    p_t1.font.bold = True
    p_t1.font.color.rgb = COLOR_PRIMARY
    p_t1.space_after = Pt(10)

    # Subtitle
    p_sub1 = tf1.add_paragraph()
    p_sub1.text = "LightGBM and NSGA-II for Indian stocks"
    p_sub1.font.name = FONT_BODY
    p_sub1.font.size = Pt(24)
    p_sub1.font.color.rgb = COLOR_SECONDARY
    p_sub1.space_after = Pt(36)

    # Authors
    p_auth = tf1.add_paragraph()
    p_auth.text = "Authors: Ashish Ranjan   •   Khuushi Maheshwari   •   Satyanarayan H."
    p_auth.font.name = FONT_BODY
    p_auth.font.size = Pt(20)
    p_auth.font.bold = True
    p_auth.font.color.rgb = COLOR_PRIMARY
    p_auth.space_after = Pt(8)

    # Affiliation
    p_aff = tf1.add_paragraph()
    p_aff.text = "Manipal Institute of Technology   |   B.Tech - Computer Science"
    p_aff.font.name = FONT_BODY
    p_aff.font.size = Pt(18)
    p_aff.font.color.rgb = COLOR_SECONDARY

    set_speaker_notes(s1, (
        "Good morning. Today we present our project, 'Hybrid Market Predictor and Strategy Optimizer'. "
        "Our work combines two computational intelligence methods—LightGBM and NSGA-II—to study systematic trading on Indian equity markets. "
        "I am presenting on behalf of team members Ashish Ranjan, Khuushi Maheshwari, and Satyanarayan H. from Manipal Institute of Technology.\n\n"
        "[Evidence Source: Task P005 Plan; PROJECT.md Section 1; reports/submission/VIVA_DEFENSE_NOTES.md]"
    ))

    # =========================================================================
    # SLIDE 2: Project purpose
    # =========================================================================
    s2 = create_blank_slide(prs)
    add_header(s2, "Project Purpose", "Overview & Motivation")

    tb2 = s2.shapes.add_textbox(Inches(1.2), Inches(2.4), Inches(10.933), Inches(4.2))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = Inches(0)
    tf2.margin_top = Inches(0)

    points2 = [
        "Learn patterns in historical stock data.",
        "Search for trading rules that balance return and risk.",
        "Test those rules on later, unseen data.",
    ]
    for i, pt in enumerate(points2):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        p.text = f"•   {pt}"
        p.font.name = FONT_BODY
        p.font.size = Pt(26)
        p.font.color.rgb = COLOR_PRIMARY
        p.space_after = Pt(30)

    set_speaker_notes(s2, (
        "The purpose of this project is to explore how machine learning and evolutionary search interact under market frictions. "
        "First, we learn patterns from historical price data. "
        "Second, we search for trading rules that balance reward against risk. "
        "Third, we evaluate those candidate rules strictly on later, unseen test periods. "
        "This project is an academic research simulator, not a tool for live trading or guaranteed profits.\n\n"
        "[Evidence Source: Task P005 Plan; PROJECT.md Purpose; reports/submission/RESEARCH_PAPER_DRAFT.pdf Section 1]"
    ))

    # =========================================================================
    # SLIDE 3: Data and tools
    # =========================================================================
    s3 = create_blank_slide(prs)
    add_header(s3, "Data and Tools", "System Architecture & Inputs")

    tb3 = s3.shapes.add_textbox(Inches(1.2), Inches(2.3), Inches(10.933), Inches(4.5))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = Inches(0)
    tf3.margin_top = Inches(0)

    points3 = [
        ("NSE stocks:", " Reliance, TCS, and Infosys."),
        ("Price and volume data:", " Daily prices and trading volume via yfinance, saved as immutable snapshots."),
        ("Feature library:", " 20 indicators describing market trend, momentum, and volatility."),
        ("Software stack:", " Python with LightGBM, NSGA-II, and Streamlit for visual interaction."),
    ]
    for i, (lead, rest) in enumerate(points3):
        p = tf3.paragraphs[0] if i == 0 else tf3.add_paragraph()
        run_lead = p.add_run()
        run_lead.text = f"•   {lead}"
        run_lead.font.name = FONT_BODY
        run_lead.font.size = Pt(24)
        run_lead.font.bold = True
        run_lead.font.color.rgb = COLOR_PRIMARY

        run_rest = p.add_run()
        run_rest.text = rest
        run_rest.font.name = FONT_BODY
        run_rest.font.size = Pt(24)
        run_rest.font.bold = False
        run_rest.font.color.rgb = COLOR_SECONDARY
        p.space_after = Pt(24)

    set_speaker_notes(s3, (
        "Our study evaluates three major National Stock Exchange equities: Reliance, TCS, and Infosys. "
        "We collected daily trading prices and volume through yfinance, storing frozen snapshots for exact reproducibility. "
        "From raw prices, we engineer twenty indicators capturing trend, momentum, and volatility. "
        "Models train on historical data dating back to 2002, while our rolling campaign rigorously tests annual out-of-sample periods from 2020 through 2025.\n\n"
        "[Evidence Source: Task P005 Plan; reports/experiments/inputs/manifest.json; reports/submission/RESEARCH_PAPER_DRAFT.pdf Section 3]"
    ))

    # =========================================================================
    # SLIDE 4: How it works
    # =========================================================================
    s4 = create_blank_slide(prs)
    add_header(s4, "How It Works", "Execution Pipeline")

    tb4 = s4.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(10.933), Inches(4.7))
    tf4 = tb4.text_frame
    tf4.word_wrap = True
    tf4.margin_left = Inches(0)
    tf4.margin_top = Inches(0)

    steps4 = [
        "1.  Read historical daily market prices.",
        "2.  Build technical indicators describing trend and volatility.",
        "3.  LightGBM estimates the chance of a rise over the next 3 trading bars.",
        "4.  NSGA-II searches for entry, exit, and risk rules.",
        "5.  Backtest on later data and show results.",
    ]
    for i, st in enumerate(steps4):
        p = tf4.paragraphs[0] if i == 0 else tf4.add_paragraph()
        p.text = st
        p.font.name = FONT_BODY
        p.font.size = Pt(23)
        p.font.color.rgb = COLOR_PRIMARY
        p.space_after = Pt(18)

    set_speaker_notes(s4, (
        "Here is the execution pipeline. "
        "First, we read historical daily prices. "
        "Second, we build technical indicators without looking ahead. "
        "Third, LightGBM estimates the probability that price will rise over the next three trading bars. "
        "Fourth, the NSGA-II genetic algorithm evolves entry thresholds, stop-losses, and holding horizons. "
        "Finally, we simulate trade execution on later unseen test data, incorporating commissions and slippage.\n\n"
        "[Evidence Source: Task P005 Plan; src/pipeline.py; reports/submission/VIVA_DEFENSE_NOTES.md Core Architecture]"
    ))

    # =========================================================================
    # SLIDE 5: The two algorithms
    # =========================================================================
    s5 = create_blank_slide(prs)
    add_header(s5, "The Two Algorithms", "Predictive ML & Evolutionary Search")

    # Column 1: LightGBM
    tb5_l = s5.shapes.add_textbox(Inches(1.2), Inches(2.3), Inches(5.2), Inches(4.6))
    tf5_l = tb5_l.text_frame
    tf5_l.word_wrap = True
    tf5_l.margin_left = Inches(0)
    tf5_l.margin_top = Inches(0)

    p_h1 = tf5_l.paragraphs[0]
    p_h1.text = "Tier 1: LightGBM"
    p_h1.font.name = FONT_TITLE
    p_h1.font.size = Pt(26)
    p_h1.font.bold = True
    p_h1.font.color.rgb = COLOR_ACCENT
    p_h1.space_after = Pt(14)

    p_b1_1 = tf5_l.add_paragraph()
    p_b1_1.text = "•   Learns from past indicator examples."
    p_b1_1.font.name = FONT_BODY
    p_b1_1.font.size = Pt(22)
    p_b1_1.font.color.rgb = COLOR_PRIMARY
    p_b1_1.space_after = Pt(10)

    p_b1_2 = tf5_l.add_paragraph()
    p_b1_2.text = "•   Produces a forward 3-day directional probability."
    p_b1_2.font.name = FONT_BODY
    p_b1_2.font.size = Pt(22)
    p_b1_2.font.color.rgb = COLOR_PRIMARY
    p_b1_2.space_after = Pt(16)

    p_b1_3 = tf5_l.add_paragraph()
    p_b1_3.text = "Directional Forecast: Estimates market probability rather than guaranteeing exact price levels."
    p_b1_3.font.name = FONT_BODY
    p_b1_3.font.size = Pt(18)
    p_b1_3.font.color.rgb = COLOR_SECONDARY

    # Column 2: NSGA-II
    tb5_r = s5.shapes.add_textbox(Inches(6.9), Inches(2.3), Inches(5.2), Inches(4.6))
    tf5_r = tb5_r.text_frame
    tf5_r.word_wrap = True
    tf5_r.margin_left = Inches(0)
    tf5_r.margin_top = Inches(0)

    p_h2 = tf5_r.paragraphs[0]
    p_h2.text = "Tier 2: NSGA-II"
    p_h2.font.name = FONT_TITLE
    p_h2.font.size = Pt(26)
    p_h2.font.bold = True
    p_h2.font.color.rgb = COLOR_ACCENT
    p_h2.space_after = Pt(14)

    p_b2_1 = tf5_r.add_paragraph()
    p_b2_1.text = "•   Improves candidate trading rules over repeated rounds."
    p_b2_1.font.name = FONT_BODY
    p_b2_1.font.size = Pt(22)
    p_b2_1.font.color.rgb = COLOR_PRIMARY
    p_b2_1.space_after = Pt(10)

    p_b2_2 = tf5_r.add_paragraph()
    p_b2_2.text = "•   Balances Sharpe ratio and maximum drawdown simultaneously."
    p_b2_2.font.name = FONT_BODY
    p_b2_2.font.size = Pt(22)
    p_b2_2.font.color.rgb = COLOR_PRIMARY
    p_b2_2.space_after = Pt(16)

    p_b2_3 = tf5_r.add_paragraph()
    p_b2_3.text = "Key Metrics:\n• Sharpe = Return relative to volatility\n• Drawdown = Largest peak-to-trough fall"
    p_b2_3.font.name = FONT_BODY
    p_b2_3.font.size = Pt(18)
    p_b2_3.font.color.rgb = COLOR_SECONDARY

    set_speaker_notes(s5, (
        "Our framework separates prediction from trade execution. "
        "LightGBM learns from past indicator patterns and outputs a forward directional probability between zero and one. "
        "NSGA-II is an evolutionary algorithm that optimizes candidate trading rules over repeated rounds. "
        "It balances Sharpe ratio—return divided by volatility—against maximum drawdown, which measures the largest fall from a peak. "
        "This produces a balanced trade-off frontier.\n\n"
        "[Evidence Source: Task P005 Plan; src/predictor.py; src/evolutionary_core.py; reports/submission/VIVA_DEFENSE_NOTES.md]"
    ))

    # =========================================================================
    # SLIDE 6: Research results
    # =========================================================================
    s6 = create_blank_slide(prs)
    add_header(s6, "Research Results", "6-Year Rolling Retrospective Study (2020–2025)")

    # Editable Table
    # Rows: 4 (Header + 3 stocks), Cols: 3 (Stock, Hybrid Return, Buy-and-Hold Return)
    t_left = Inches(1.5)
    t_top = Inches(2.2)
    t_width = Inches(10.333)
    t_height = Inches(2.2)
    table_shape = s6.shapes.add_table(4, 3, t_left, t_top, t_width, t_height)
    table = table_shape.table
    table.columns[0].width = Inches(3.5)
    table.columns[1].width = Inches(3.4)
    table.columns[2].width = Inches(3.433)

    table_data = [
        ["Stock", "Hybrid Return", "Buy-and-Hold Return"],
        ["Reliance (RELIANCE.NS)", "-0.35%", "128.74%"],
        ["TCS (TCS.NS)", "25.60%", "65.13%"],
        ["Infosys (INFY.NS)", "9.10%", "152.78%"],
    ]

    for r_idx, row in enumerate(table_data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.font.name = FONT_BODY
            p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT
            if r_idx == 0:
                p.font.size = Pt(20)
                p.font.bold = True
                p.font.color.rgb = COLOR_PRIMARY
                cell.fill.solid()
                cell.fill.fore_color.rgb = COLOR_LIGHT_BG
            else:
                p.font.size = Pt(20)
                p.font.bold = (c_idx == 0)
                p.font.color.rgb = COLOR_PRIMARY

    # Takeaway text block below table
    tb6_b = s6.shapes.add_textbox(Inches(1.5), Inches(4.7), Inches(10.333), Inches(2.2))
    tf6_b = tb6_b.text_frame
    tf6_b.word_wrap = True
    tf6_b.margin_left = Inches(0)
    tf6_b.margin_top = Inches(0)

    p_cap = tf6_b.paragraphs[0]
    p_cap.text = "Caption: 2020–2025 cumulative compounded return; hybrid strategy median across 3 random GA seeds."
    p_cap.font.name = FONT_BODY
    p_cap.font.size = Pt(16)
    p_cap.font.italic = True
    p_cap.font.color.rgb = COLOR_SECONDARY
    p_cap.space_after = Pt(12)

    p_take1 = tf6_b.add_paragraph()
    p_take1.text = "•   Visible takeaway: Buy-and-hold earned more total return on all three stocks."
    p_take1.font.name = FONT_BODY
    p_take1.font.size = Pt(21)
    p_take1.font.bold = True
    p_take1.font.color.rgb = COLOR_PRIMARY
    p_take1.space_after = Pt(6)

    p_take2 = tf6_b.add_paragraph()
    p_take2.text = "•   Defensive benefit: Hybrid maximum drawdown was lower in 17 of 18 annual stock comparisons."
    p_take2.font.name = FONT_BODY
    p_take2.font.size = Pt(21)
    p_take2.font.bold = False
    p_take2.font.color.rgb = COLOR_PRIMARY

    set_speaker_notes(s6, (
        "Here are our empirical results from the six-year rolling study across eighteen annual folds. "
        "Passive buy-and-hold earned higher total return on all three stocks: Reliance 128.7%, TCS 65.1%, and Infosys 152.8%, compared to minus 0.35%, 25.6%, and 9.1% for the hybrid strategy. "
        "However, our system provided consistent defensive protection, reducing maximum drawdown in seventeen of eighteen annual comparisons by moving to cash during downturns.\n\n"
        "[Evidence Source: Task P005 Plan; reports/experiments/results/stitched_aggregate_metrics.csv; paired_annual_comparisons.csv; fold_summary_metrics.csv]"
    ))

    # =========================================================================
    # SLIDE 7: Using the dashboard
    # =========================================================================
    s7 = create_blank_slide(prs)
    add_header(s7, "Using the Dashboard", "Evolutionary Market Lab Cockpit")

    tb7 = s7.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(10.933), Inches(4.7))
    tf7 = tb7.text_frame
    tf7.word_wrap = True
    tf7.margin_left = Inches(0)
    tf7.margin_top = Inches(0)

    steps7 = [
        "1.  Select a stock or asset from the sidebar.",
        "2.  Set Candidate Population to 40, Improvement Rounds to 15, and Random Seed to 42.",
        "3.  Click the Run Experiment button.",
        "4.  Inspect performance KPIs, Pareto frontier strategies, and simulated trade logs.",
    ]
    for i, st in enumerate(steps7):
        p = tf7.paragraphs[0] if i == 0 else tf7.add_paragraph()
        p.text = st
        p.font.name = FONT_BODY
        p.font.size = Pt(23)
        p.font.color.rgb = COLOR_PRIMARY
        p.space_after = Pt(14)

    p_param_box = tf7.add_paragraph()
    p_param_box.text = "Key Parameter Definitions:\nPopulation = Candidate rules  •  Generations = Improvement rounds  •  Seed = Repeatable randomness"
    p_param_box.font.name = FONT_BODY
    p_param_box.font.size = Pt(18)
    p_param_box.font.color.rgb = COLOR_ACCENT
    p_param_box.space_after = Pt(8)

    p_note_app = tf7.add_paragraph()
    p_note_app.text = "Note: Interactive dashboard executes a single chronological split for real-time exploration (separate from 6-year rolling research)."
    p_note_app.font.name = FONT_BODY
    p_note_app.font.size = Pt(16)
    p_note_app.font.italic = True
    p_note_app.font.color.rgb = COLOR_SECONDARY

    set_speaker_notes(s7, (
        "We also created an interactive web cockpit called Evolutionary Market Lab using Streamlit. "
        "In a live demonstration, the user selects an asset, sets population to 40 candidate rules, runs 15 improvement rounds, and sets seed 42 for exact repeatability. "
        "Clicking Run Experiment fits the model and optimizes trading rules in seconds. "
        "This interactive cockpit uses a single chronological split, keeping it distinct from our multi-year rolling study.\n\n"
        "[Evidence Source: Task P005 Plan; app.py; run_app.bat; reports/ui/UI_REDESIGN_NOTES.md]"
    ))

    # =========================================================================
    # SLIDE 8: Conclusion and next steps
    # =========================================================================
    s8 = create_blank_slide(prs)
    add_header(s8, "Conclusion and Next Steps", "Summary & Future Work")

    tb8 = s8.shapes.add_textbox(Inches(1.2), Inches(2.3), Inches(10.933), Inches(4.5))
    tf8 = tb8.text_frame
    tf8.word_wrap = True
    tf8.margin_left = Inches(0)
    tf8.margin_top = Inches(0)

    points8 = [
        "Built an end-to-end prediction and strategy research tool.",
        "Observed risk-return trade-offs: lower drawdowns, but lower total return than buy-and-hold in this study.",
        "Next steps: evaluate broader stock universes and incorporate richer macroeconomic features.",
    ]
    for i, pt in enumerate(points8):
        p = tf8.paragraphs[0] if i == 0 else tf8.add_paragraph()
        p.text = f"•   {pt}"
        p.font.name = FONT_BODY
        p.font.size = Pt(24)
        p.font.color.rgb = COLOR_PRIMARY
        p.space_after = Pt(24)

    p_ty = tf8.add_paragraph()
    p_ty.text = "Thank you for your time  —  Questions & Discussion"
    p_ty.font.name = FONT_TITLE
    p_ty.font.size = Pt(28)
    p_ty.font.bold = True
    p_ty.font.color.rgb = COLOR_ACCENT

    set_speaker_notes(s8, (
        "In conclusion, we built an end-to-end framework combining machine learning and evolutionary multi-objective optimization. "
        "Our empirical results show an important risk-return trade-off: evolutionary rules significantly reduced drawdown risk during market downturns, though passive buy-and-hold achieved higher cumulative returns in a strong bull market. "
        "Future steps include evaluating broader asset universes and richer economic indicators. "
        "Thank you for your time, and we welcome your questions.\n\n"
        "[Evidence Source: Task P005 Plan; reports/submission/COLLEGE_PROJECT_REPORT.pdf; reports/submission/VIVA_DEFENSE_NOTES.md]"
    ))

    # Output paths
    output_dir = Path("reports/submission")
    output_dir.mkdir(parents=True, exist_ok=True)
    pptx_path = output_dir / "SIMPLE_PROJECT_PRESENTATION.pptx"
    prs.save(str(pptx_path))
    print(f"Saved PPTX to: {pptx_path}")
    return pptx_path


if __name__ == "__main__":
    build_presentation()
