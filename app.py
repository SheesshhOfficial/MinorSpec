"""
Evolutionary Market Lab: Interactive Computational Intelligence Research Workspace.

Architecture & Evidence Boundary:
- Tier 1: LightGBM GBDT estimating forward 3-day return direction across 20 technical features.
- Tier 2: NSGA-II multi-objective genetic algorithm evolving continuous trading chromosomes.
- Evaluation Protocol: Single-split chronological partitions (Train -> Val -> Dev -> Test) with 3-bar purging.
- Strategy Selection: Best Sharpe on Development partition is frozen for Out-of-Sample Test.
"""

import html
import io
from pathlib import Path
import streamlit as st
import numpy as np
import pandas as pd

from src.config import DEFAULT_TICKERS, INITIAL_CAPITAL, DEFAULT_COMMISSION_PCT, DEFAULT_SLIPPAGE_PCT
from src.pipeline import run_experiment_pipeline
from src.backtest_engine import get_detailed_simulation_results

from ui.styles import CUSTOM_CSS
from ui.formatting import format_currency, format_pct, format_ratio, get_asset_currency_info
from ui.charts import create_pareto_chart, create_equity_drawdown_chart, create_feature_importance_chart
from ui.metadata import GENE_DEFINITIONS, FEATURE_GLOSSARY


# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Evolutionary Market Lab",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. Cached Pipeline Execution
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def execute_pipeline_cached(ticker_sym: str, population: int, generations: int, rnd_seed: int):
    """
    Executes single-split chronological research pipeline.
    Cached across identical parameter combinations to preserve session responsiveness.
    """
    return run_experiment_pipeline(
        ticker=ticker_sym,
        pop_size=population,
        num_generations=generations,
        seed=rnd_seed,
    )


# -----------------------------------------------------------------------------
# 3. Sidebar Controls & Parameter Helpers
# -----------------------------------------------------------------------------
st.sidebar.markdown("### Experiment Setup")

# Section A: Stock or Asset
st.sidebar.markdown("**Stock or Asset**")
default_idx = DEFAULT_TICKERS.index("RELIANCE.NS") if "RELIANCE.NS" in DEFAULT_TICKERS else 0
selected_ticker = st.sidebar.selectbox(
    "Select Stock or Asset",
    options=DEFAULT_TICKERS,
    index=default_idx,
    key="select_universe_ticker",
    help="Core research evaluated Indian NSE equities (RELIANCE.NS, TCS.NS, INFY.NS); US indices/equities (SPY, AAPL) are exploratory reference tickers.",
)
custom_ticker_raw = st.sidebar.text_input(
    "Or Custom Ticker",
    value="",
    key="input_custom_ticker",
    help="Enter an external symbol (e.g. RELIANCE.NS, TCS.NS, SPY, AAPL). Overrides dropdown when provided.",
).strip()

# Validate and sanitize custom input
clean_custom = "".join(c for c in custom_ticker_raw.upper() if c.isalnum() or c in ".-_^")
custom_is_invalid = bool(custom_ticker_raw and not clean_custom)

if custom_is_invalid:
    st.sidebar.error("Invalid custom ticker format. Please enter letters, numbers, dot, or hyphen.")
    active_ticker = selected_ticker
elif clean_custom:
    active_ticker = clean_custom
    st.sidebar.caption(f"Active Ticker: **{html.escape(active_ticker)}** (Custom Entry)")
else:
    active_ticker = selected_ticker
    st.sidebar.caption(f"Active Ticker: **{html.escape(active_ticker)}**")

# Section B: Evolutionary Search Settings
st.sidebar.markdown("---")
st.sidebar.markdown("**Evolutionary Search Settings**")

pop_size = st.sidebar.slider(
    "Candidate Strategies (Population)",
    min_value=20,
    max_value=100,
    value=40,
    step=10,
    key="slider_pop_size",
    help="Size of the population evolving on Development data.",
)
st.sidebar.caption("40 strategies are maintained in each generation to preserve Pareto frontier diversity.")

num_generations = st.sidebar.slider(
    "Improvement Rounds (Generations)",
    min_value=5,
    max_value=40,
    value=15,
    step=5,
    key="slider_generations",
    help="Generations of repeated selection, crossover, and mutation.",
)
st.sidebar.caption("Repeated evolutionary rounds improve Development fitness; higher values do not guarantee better Out-of-Sample Test returns.")

with st.sidebar.expander("Search Randomness (Seed)", expanded=False):
    seed = st.number_input(
        "Random Starting Seed",
        min_value=1,
        max_value=99999,
        value=42,
        step=1,
        key="num_seed",
        help="Controls random number generation for NSGA-II crossover and mutation. Note: The LightGBM classifier seed is fixed by the backend for consistency.",
    )
    st.caption("Controls NSGA-II evolutionary search randomness. Same seed reproduces identical Pareto solutions on the same dataset. 42 is an arbitrary seed, not a performance score.")

st.sidebar.markdown("---")
run_experiment_clicked = st.sidebar.button(
    "Run Experiment",
    type="primary",
    use_container_width=True,
    key="btn_run_experiment",
    help="Executes feature pipeline, LightGBM fitting, NSGA-II search, and frozen test evaluation.",
)
st.sidebar.caption("First run on an asset may take 10-15s to load data and compile Numba simulation kernels.")


# -----------------------------------------------------------------------------
# 4. Session State Management & Execution Lifecycle
# -----------------------------------------------------------------------------
# Keys in session_state:
# - "has_run": bool (True once at least one successful run completed)
# - "pipeline_results": dict (latest successful results)
# - "executed_settings": dict (settings corresponding to pipeline_results)
# - "last_error": Optional[str]

if "has_run" not in st.session_state:
    st.session_state.has_run = False
    st.session_state.pipeline_results = None
    st.session_state.executed_settings = None
    st.session_state.last_error = None

# If user clicked Run Experiment, execute pipeline with error safety
if run_experiment_clicked:
    with st.spinner(f"Running Two-Tier Optimization on {active_ticker} (N={pop_size}, G={num_generations}, Seed={seed})..."):
        try:
            results_candidate = execute_pipeline_cached(active_ticker, pop_size, num_generations, seed)
            st.session_state.pipeline_results = results_candidate
            st.session_state.executed_settings = {
                "ticker": active_ticker,
                "pop_size": pop_size,
                "generations": num_generations,
                "seed": seed,
            }
            st.session_state.has_run = True
            st.session_state.last_error = None
        except Exception as e:
            st.session_state.last_error = f"Execution failed for {active_ticker}: {str(e)}"

# -----------------------------------------------------------------------------
# 5. Header Banner & Execution Context Chips
# -----------------------------------------------------------------------------
st.markdown("""
<div class="eml-header">
    <div class="eml-title">
        <span>Evolutionary Market Lab</span>
        <span class="eml-title-badge">Computational Intelligence</span>
    </div>
    <div class="eml-subtitle">
        Explore how machine learning directional forecasts and multi-objective evolutionary trading rules alter risk and return.
    </div>
</div>
""", unsafe_allow_html=True)

# Display error if execution failed
if st.session_state.last_error:
    st.markdown(f"""
    <div class="eml-banner eml-banner-warning">
        <div><strong>Execution Alert:</strong> {html.escape(st.session_state.last_error)}</div>
    </div>
    """, unsafe_allow_html=True)

# Display status chips if results exist
if st.session_state.has_run and st.session_state.pipeline_results is not None:
    exec_cfg = st.session_state.executed_settings
    results = st.session_state.pipeline_results
    test_split = results["splits"]["test"]
    t_start = str(test_split["Date"].iloc[0])[:10]
    t_end = str(test_split["Date"].iloc[-1])[:10]

    # Check for unapplied pending edits in sidebar
    is_stale = (
        active_ticker != exec_cfg["ticker"]
        or pop_size != exec_cfg["pop_size"]
        or num_generations != exec_cfg["generations"]
        or seed != exec_cfg["seed"]
    )

    if is_stale:
        st.markdown(f"""
        <div class="eml-banner eml-banner-warning">
            <div>
                <strong>Pending Settings Modified:</strong> Sidebar settings were changed (Ticker: <code>{html.escape(active_ticker)}</code>, N={pop_size}, G={num_generations}, Seed={seed}).
                The display below reflects previous executed run: <strong>{html.escape(exec_cfg['ticker'])}</strong> (N={exec_cfg['pop_size']}, G={exec_cfg['generations']}, Seed={exec_cfg['seed']}).
                Click <strong>Run Experiment</strong> in the sidebar to re-execute with current settings.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="eml-chip-bar">
        <div class="eml-chip eml-chip-status">
            <span>Status:</span> <strong>Active Run</strong>
        </div>
        <div class="eml-chip">
            <span>Asset:</span> <strong>{html.escape(exec_cfg['ticker'])}</strong>
        </div>
        <div class="eml-chip">
            <span>Test Horizon:</span> <strong>{t_start} to {t_end} ({len(test_split)} bars)</strong>
        </div>
        <div class="eml-chip">
            <span>Algorithm:</span> <strong>NSGA-II (N={exec_cfg['pop_size']}, G={exec_cfg['generations']}, Seed={exec_cfg['seed']})</strong>
        </div>
        <div class="eml-chip">
            <span>Protocol:</span> <strong>Single-Split Chronological (Purged H=3)</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 6. First-Run State (Clean guidance when no experiment executed yet)
# -----------------------------------------------------------------------------
if not st.session_state.has_run or st.session_state.pipeline_results is None:
    st.markdown("""
    <div class="eml-empty-card">
        <div class="eml-empty-title">Ready to Explore Computational Intelligence Trading Policies</div>
        <div class="eml-empty-desc">
            This workspace evaluates a Two-Tier hybrid model: Tier 1 predicts 3-day directional returns using LightGBM,
            and Tier 2 evolves dynamic ATR risk-management rules with NSGA-II across multi-objective trade-offs.
        </div>
        <div class="eml-steps-grid">
            <div class="eml-step-item">
                <div class="eml-step-num">Step 1</div>
                <div class="eml-step-title">Choose Asset & Settings</div>
                <div class="eml-step-desc">Select an NSE equity (e.g. RELIANCE.NS) or US index (SPY), and configure population size and search generations.</div>
            </div>
            <div class="eml-step-item">
                <div class="eml-step-num">Step 2</div>
                <div class="eml-step-title">Run Evolutionary Search</div>
                <div class="eml-step-desc">Click <strong>Run Experiment</strong> in the sidebar to fit the classifier on Training data and discover Pareto strategies on Development data.</div>
            </div>
            <div class="eml-step-item">
                <div class="eml-step-num">Step 3</div>
                <div class="eml-step-title">Inspect Performance & Risks</div>
                <div class="eml-step-desc">Analyze the frozen representative strategy on Out-of-Sample Test data, explore Pareto trade-offs, and inspect the trade audit log.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Offer inline button for immediate execution using active sidebar settings
    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    with col_c2:
        if st.button(f"Run Experiment on {active_ticker}", type="primary", use_container_width=True, key="btn_first_run_inline"):
            with st.spinner(f"Running Two-Tier Optimization on {active_ticker} (N={pop_size}, G={num_generations}, Seed={seed})..."):
                try:
                    res = execute_pipeline_cached(active_ticker, pop_size, num_generations, seed)
                    st.session_state.pipeline_results = res
                    st.session_state.executed_settings = {
                        "ticker": active_ticker,
                        "pop_size": pop_size,
                        "generations": num_generations,
                        "seed": seed,
                    }
                    st.session_state.has_run = True
                    st.session_state.last_error = None
                    st.rerun()
                except Exception as e:
                    st.session_state.last_error = f"Execution failed for {active_ticker}: {str(e)}"
                    st.error(f"Error starting run: {e}")
    st.stop()


# -----------------------------------------------------------------------------
# 7. Render Executed Results in Structured Tabs
# -----------------------------------------------------------------------------
results = st.session_state.pipeline_results
exec_cfg = st.session_state.executed_settings

if results is not None and exec_cfg is not None:
    ticker = exec_cfg["ticker"]
    summary_df = results["summary_df"]
    test_df = results["splits"]["test"]
    p_up_test = results["predictor"].predict_proba(test_df)
    frozen_id = results["frozen_strategy_id"]
else:
    st.stop()

tab_overview, tab_explorer, tab_model, tab_journal, tab_methodology = st.tabs([
    "📊 Overview",
    "🎯 Strategy Explorer",
    "🧠 Model Insights",
    "📜 Trade Journal",
    "📖 Methodology",
])


# =============================================================================
# TAB 1: OVERVIEW
# =============================================================================
with tab_overview:
    # Always compute metrics for frozen primary strategy for the top KPI row
    frozen_row = summary_df[summary_df["id"] == frozen_id].iloc[0]
    frozen_genes = frozen_row["genes"]
    sim_primary = get_detailed_simulation_results(test_df, p_up_test, frozen_genes)

    strat_ret = sim_primary["total_return"]
    bench_ret = sim_primary["benchmark_return"]
    diff_pp = (strat_ret - bench_ret) * 100.0
    strat_mdd = sim_primary["max_drawdown"]
    bench_mdd = sim_primary["benchmark_max_drawdown"]
    sharpe = sim_primary["sharpe_ratio"]
    trades_count = sim_primary["total_trades"]
    win_rate = sim_primary["win_rate"]

    diff_sign = "+" if diff_pp > 0 else ""
    diff_class = "eml-delta-gain" if diff_pp >= 0 else "eml-delta-loss"
    strat_ret_class = "eml-delta-gain" if strat_ret >= 0 else "eml-delta-loss"
    bench_ret_class = "eml-delta-gain" if bench_ret >= 0 else "eml-delta-loss"

    st.markdown(f"""
    <div class="eml-kpi-grid">
        <div class="eml-kpi-card">
            <div class="eml-kpi-label">Primary Strategy Return</div>
            <div class="eml-kpi-value">{format_pct(strat_ret, include_sign=True)}</div>
            <div class="eml-kpi-delta {diff_class}">{diff_sign}{diff_pp:.2f} pp vs Benchmark</div>
            <div class="eml-kpi-subtext">Frozen Strategy #{frozen_id}</div>
        </div>
        <div class="eml-kpi-card">
            <div class="eml-kpi-label">Benchmark Buy & Hold</div>
            <div class="eml-kpi-value">{format_pct(bench_ret, include_sign=True)}</div>
            <div class="eml-kpi-delta {bench_ret_class}">Passive Buy & Hold</div>
            <div class="eml-kpi-subtext">100% Capital Invested</div>
        </div>
        <div class="eml-kpi-card">
            <div class="eml-kpi-label">Max Drawdown</div>
            <div class="eml-kpi-value">{format_pct(strat_mdd)}</div>
            <div class="eml-kpi-delta eml-delta-neutral">Benchmark MDD: {format_pct(bench_mdd)}</div>
            <div class="eml-kpi-subtext">Peak-to-trough decline</div>
        </div>
        <div class="eml-kpi-card">
            <div class="eml-kpi-label">Annualized Sharpe</div>
            <div class="eml-kpi-value">{format_ratio(sharpe)}</div>
            <div class="eml-kpi-delta eml-delta-neutral">Risk-free rate: 0.0%</div>
            <div class="eml-kpi-subtext">Mean daily / Std daily * √252</div>
        </div>
        <div class="eml-kpi-card">
            <div class="eml-kpi-label">Trades & Win Rate</div>
            <div class="eml-kpi-value">{trades_count} trades</div>
            <div class="eml-kpi-delta eml-delta-neutral">Win Rate: {format_pct(win_rate) if trades_count > 0 else 'N/A'}</div>
            <div class="eml-kpi-subtext">Next-bar execution timing</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Equity and Underwater Drawdown Charts
    fig_overview_equity = create_equity_drawdown_chart(sim_primary, ticker, test_df)
    st.plotly_chart(fig_overview_equity, use_container_width=True)

    # Plain-language Reading Guide
    with st.expander("Reading Guide & Financial Interpretation", expanded=False):
        st.markdown(f"""
        - **Primary Strategy Status:** Strategy `#{frozen_id}` was selected based on the highest Sharpe ratio on the **Development partition** (before test data was inspected).
        - **Realistic Timing:** Signals evaluated at bar $t-1$ Close execute strictly at bar $t$ Open with slippage and commission friction (approximately 20 bps round-trip).
        - **Drawdown Reduction vs. Opportunity Cost:** Defensive rules frequently reduce maximum drawdown during market downturns, but cash-preservation rules incur opportunity costs during strong bull runs.
        - **Units:** All nominal values are formatted in **{get_asset_currency_info(ticker)[1]}** based on the asset exchange.
        """)


# =============================================================================
# TAB 2: STRATEGY EXPLORER
# =============================================================================
with tab_explorer:
    col_exp_left, col_exp_right = st.columns([1.5, 1])

    with col_exp_right:
        st.markdown("#### Candidate Strategy Selector")

        # Short option text preventing UI truncation
        strategy_ids = [int(r["id"]) for _, r in summary_df.iterrows()]
        default_sel_idx = strategy_ids.index(frozen_id) if frozen_id in strategy_ids else 0

        def format_strategy_option(sid: int) -> str:
            if sid == frozen_id:
                return f"Strategy #{sid} (Primary)"
            return f"Strategy #{sid}"

        selected_id = st.selectbox(
            "Select Candidate to Inspect",
            options=strategy_ids,
            index=default_sel_idx,
            format_func=format_strategy_option,
            key="select_candidate_id",
            help="Choose a chromosome from the Pareto frontier to inspect its evolved parameters and test performance.",
        )

        chosen_row = summary_df[summary_df["id"] == selected_id].iloc[0]
        chosen_genes = chosen_row["genes"]
        is_primary = (selected_id == frozen_id)

        # Selected Candidate Metrics Highlight Box
        st.markdown(f"""
        <div class="eml-chip-bar" style="margin-bottom: 12px;">
            <div class="eml-chip">
                <span>Dev Sharpe:</span> <strong>{chosen_row['dev_sharpe']:.2f}</strong>
            </div>
            <div class="eml-chip">
                <span>Dev MaxDD:</span> <strong>{chosen_row['dev_mdd']*100:.1f}%</strong>
            </div>
            <div class="eml-chip">
                <span>Dev Return:</span> <strong>{chosen_row['dev_ret']*100:+.1f}%</strong>
            </div>
            <div class="eml-chip">
                <span>Trades:</span> <strong>{int(chosen_row['dev_trades'])}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if is_primary:
            st.markdown(f"""
            <div class="eml-strat-status eml-strat-primary">
                <strong>Primary Strategy Pick (Frozen Best)</strong><br>
                Selected by highest development Sharpe ratio before evaluating test data. This represents the authentic out-of-sample experiment benchmark.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="eml-strat-status eml-strat-exploratory">
                <strong>Exploratory Inspection Only</strong><br>
                Candidate #{selected_id} is inspected for comparative analysis. Browsing other candidates does not replace Strategy #{frozen_id} as the frozen primary rule.
            </div>
            """, unsafe_allow_html=True)

        # Comparative Metrics Table (Dev vs Test)
        st.markdown("**Performance Comparison (Dev vs. Test)**")
        perf_data = [
            ("Annualized Sharpe Ratio", f"{chosen_row['dev_sharpe']:.2f}", f"{chosen_row['exploratory_test_sharpe']:.2f}"),
            ("Maximum Drawdown", f"{chosen_row['dev_mdd']*100:.2f}%", f"{chosen_row['exploratory_test_mdd']*100:.2f}%"),
            ("Cumulative Return", f"{chosen_row['dev_ret']*100:+.2f}%", f"{chosen_row['exploratory_test_ret']*100:+.2f}%"),
            ("Completed Trades", f"{int(chosen_row['dev_trades'])}", f"{int(chosen_row['exploratory_test_trades'])}"),
        ]
        perf_df = pd.DataFrame(perf_data, columns=["Metric", "Development Partition", "Out-of-Sample Test"])
        st.dataframe(perf_df, hide_index=True, use_container_width=True)

    with col_exp_left:
        fig_pareto = create_pareto_chart(summary_df, selected_id, frozen_id)
        st.plotly_chart(fig_pareto, use_container_width=True)
        st.caption("Pareto frontier visualizes optimal trade-offs discovered during evolutionary search on Development data. Higher Sharpe ratios balance against lower Maximum Drawdown risk.")

    # Evolved Chromosome Parameter Cards
    st.markdown("---")
    st.markdown("#### Evolved Decision Parameters (7-Gene Chromosome)")
    st.caption("These continuous values dictate how Tier 2 translates Tier 1 directional probabilities into market entries, position sizing, and dynamic bracket exits.")

    gene_cards = []
    for idx, gdef in enumerate(GENE_DEFINITIONS):
        val = chosen_genes[idx]
        gene_cards.append({
            "Parameter": gdef["label"],
            "Evolved Value": gdef["fmt"](val),
            "Search Bounds": gdef["bounds"],
            "Purpose / Role": gdef["purpose"],
        })
    gene_df = pd.DataFrame(gene_cards)
    st.dataframe(gene_df, hide_index=True, use_container_width=True)


# =============================================================================
# TAB 3: MODEL INSIGHTS
# =============================================================================
with tab_model:
    predictor = results["predictor"]
    feat_cols = results["feature_cols"]

    col_m1, col_m2 = st.columns([1, 1])

    with col_m1:
        st.markdown("#### Tier 1 Classifier Diagnostics")
        st.markdown(
            "LightGBM Gradient Boosted Decision Trees predict whether 3-day forward return is positive: "
            "$y_t = 1$ if $(Close_{t+3} - Close_t) / Close_t > 0$."
        )

        # Validation metrics if available
        metrics = getattr(predictor, "metrics", {})
        v_auc = metrics.get("val_auc", None)
        v_acc = metrics.get("val_acc", None)
        v_brier = metrics.get("val_brier", None)

        if v_auc is not None:
            c1, c2, c3 = st.columns(3)
            c1.metric("Validation AUC", f"{v_auc:.4f}", help="Area Under ROC Curve on purged validation partition.")
            c2.metric("Directional Accuracy", f"{v_acc*100:.2f}%", help="Percentage of correct directional classifications.")
            c3.metric("Brier Score", f"{v_brier:.4f}", help="Mean squared error of conditional probability forecasts (lower is better).")
        else:
            st.info("Validation diagnostics recorded during model training.")

        st.markdown("---")
        st.markdown("#### Predictive Feature Importance (Split Gain)")
        imp_df = predictor.get_feature_importances()
        fig_imp = create_feature_importance_chart(imp_df, len(feat_cols))
        st.plotly_chart(fig_imp, use_container_width=True)
        st.caption("Gain importance measures total gain brought by feature splits across tree branches. It indicates predictive model utility, not causal economic proof.")

    with col_m2:
        st.markdown("#### Technical Feature Indicator Glossary (20 Features)")
        st.markdown("All 20 indicators are engineered strictly from causal historical OHLCV data without future leakage:")

        for category, cat_feats in FEATURE_GLOSSARY.items():
            with st.expander(category, expanded=(category == "Trend Indicators")):
                for fname, fdesc in cat_feats.items():
                    st.markdown(f"- **`{fname}`**: {fdesc}")


# =============================================================================
# TAB 4: TRADE JOURNAL
# =============================================================================
with tab_journal:
    st.markdown("#### Simulated Execution Audit Log")
    
    # Prominent Strategy Identity Chip
    if selected_id == frozen_id:
        st.markdown(f"""
        <div class="eml-strat-status eml-strat-primary" style="margin-bottom: 12px;">
            <strong>Inspecting Strategy #{selected_id} (Primary Frozen Best)</strong> — Synchronized with Strategy Explorer selection.
            Metrics reflect out-of-sample execution on the Test partition.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="eml-strat-status eml-strat-exploratory" style="margin-bottom: 12px;">
            <strong>Inspecting Strategy #{selected_id} (Exploratory Candidate)</strong> — Synchronized with Strategy Explorer selection.
            Viewing exploratory candidate trades does not alter the frozen primary benchmark.
        </div>
        """, unsafe_allow_html=True)

    sim_selected = get_detailed_simulation_results(test_df, p_up_test, chosen_genes)
    trades_df = sim_selected["trade_log"]

    if trades_df.empty:
        st.info(f"No trades were executed on the test partition for Strategy #{selected_id}. Thresholds remained uncrossed or trades did not trigger.")
    else:
        # Filters bar
        col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
        with col_f1:
            outcome_filter = st.selectbox(
                "Filter by Outcome",
                options=["All Trades", "Profitable Trades Only", "Loss Trades Only"],
                index=0,
                key="select_trade_outcome",
            )
        with col_f2:
            reasons = ["All Reasons"] + sorted(list(trades_df["exit_reason"].unique()))
            reason_filter = st.selectbox(
                "Filter by Exit Reason",
                options=reasons,
                index=0,
                key="select_trade_reason",
            )

        # Apply display filters without modifying underlying backtest metrics
        filtered_trades = trades_df.copy()
        if outcome_filter == "Profitable Trades Only":
            filtered_trades = filtered_trades[filtered_trades["pnl"] > 0]
        elif outcome_filter == "Loss Trades Only":
            filtered_trades = filtered_trades[filtered_trades["pnl"] <= 0]

        if reason_filter != "All Reasons":
            filtered_trades = filtered_trades[filtered_trades["exit_reason"] == reason_filter]

        st.caption(f"Showing **{len(filtered_trades)}** of **{len(trades_df)}** executed trades (Filters modify display rows only; backtest KPIs remain invariant).")

        if filtered_trades.empty:
            st.warning("No trades match the current filter criteria. Adjust the outcome or exit reason filter above.")
        else:
            sym, code = get_asset_currency_info(ticker)
            curr_prefix = sym if sym else ""
            curr_suffix = f" {code}" if not sym else ""

            display_df = filtered_trades.copy()
            display_df["pnl_formatted"] = display_df["pnl"].apply(lambda v: f"{curr_prefix}{v:,.2f}{curr_suffix}")
            display_df["return_pct"] = (display_df["pnl_pct"] * 100.0).apply(lambda v: f"{v:+.2f}%")
            display_df["entry_price_fmt"] = display_df["entry_price"].apply(lambda v: f"{curr_prefix}{v:,.2f}{curr_suffix}")
            display_df["exit_price_fmt"] = display_df["exit_price"].apply(lambda v: f"{curr_prefix}{v:,.2f}{curr_suffix}")

            table_cols = {
                "entry_date": "Entry Date",
                "exit_date": "Exit Date",
                "entry_price_fmt": "Entry Price",
                "exit_price_fmt": "Exit Price",
                "pnl_formatted": "Net P&L",
                "return_pct": "Trade Return",
                "holding_bars": "Duration (Bars)",
                "exit_reason": "Exit Reason",
            }
            st.dataframe(
                display_df[list(table_cols.keys())].rename(columns=table_cols),
                hide_index=True,
                use_container_width=True,
                height=340,
            )

        # Export Buttons Row (Clearly distinguishing Complete vs Filtered)
        col_exp1, col_exp2 = st.columns([1, 1])
        with col_exp1:
            csv_complete = io.StringIO()
            trades_df.to_csv(csv_complete, index=False)
            st.download_button(
                label=f"Download Complete Log ({len(trades_df)} trades, CSV)",
                data=csv_complete.getvalue(),
                file_name=f"{ticker}_strategy_{selected_id}_complete_trades.csv",
                mime="text/csv",
                key="btn_download_complete_trades",
            )
        with col_exp2:
            if not filtered_trades.empty and len(filtered_trades) < len(trades_df):
                csv_filtered = io.StringIO()
                filtered_trades.to_csv(csv_filtered, index=False)
                st.download_button(
                    label=f"Download Filtered Log ({len(filtered_trades)} trades, CSV)",
                    data=csv_filtered.getvalue(),
                    file_name=f"{ticker}_strategy_{selected_id}_filtered_trades.csv",
                    mime="text/csv",
                    key="btn_download_filtered_trades",
                )


# =============================================================================
# TAB 5: METHODOLOGY & LIMITATIONS
# =============================================================================
with tab_methodology:
    st.markdown("#### Computational Intelligence Architecture & Research Boundaries")

    splits = results["splits"]
    train_df = splits["train"]
    val_df = splits["val"]
    dev_df = splits["dev"]
    test_df = splits["test"]
    n_total = len(train_df) + len(val_df) + len(dev_df) + len(test_df) + 9  # 9 bars purged across 3 gaps

    st.markdown(f"""
    ##### 1. Chronological Partitioning Timeline (Single-Split Interactive Experiment)
    To guard strictly against lookahead bias, all data is partitioned chronologically with **3-bar purged gap horizons**:
    - **Training Partition (~50%):** `{str(train_df['Date'].iloc[0])[:10]}` to `{str(train_df['Date'].iloc[-1])[:10]}` ({len(train_df)} bars, {len(train_df)/n_total*100:.1f}%). Fits LightGBM decision trees.
    - *[Purged Gap: 3 bars]*
    - **Validation Partition (~15%):** `{str(val_df['Date'].iloc[0])[:10]}` to `{str(val_df['Date'].iloc[-1])[:10]}` ({len(val_df)} bars, {len(val_df)/n_total*100:.1f}%). Used for early stopping (30 rounds).
    - *[Purged Gap: 3 bars]*
    - **Development Partition (~15%):** `{str(dev_df['Date'].iloc[0])[:10]}` to `{str(dev_df['Date'].iloc[-1])[:10]}` ({len(dev_df)} bars, {len(dev_df)/n_total*100:.1f}%). NSGA-II discovers Pareto-optimal rules.
    - *[Purged Gap: 3 bars]*
    - **Out-of-Sample Test Partition (Remainder, ~20%):** `{str(test_df['Date'].iloc[0])[:10]}` to `{str(test_df['Date'].iloc[-1])[:10]}` ({len(test_df)} bars, {len(test_df)/n_total*100:.1f}%). Evaluates frozen strategy #{frozen_id}.
    """)

    st.markdown(f"""
    ##### 2. Strategy Selection Rule on Development Partition
    - **Selection Rule:** Among candidate strategies with **at least 3 completed development trades** (`dev_trades >= 3`), the strategy with the **highest raw Development Sharpe Ratio** is frozen as the representative strategy.
    - **Fallback:** If no candidate achieves $\\ge 3$ development trades, the system falls back to the candidate with the highest raw Development Sharpe Ratio overall.
    - **Execution Timing:** Signals evaluated at bar $t-1$ Close execute strictly at bar $t$ Open price ($P_{{entry}} = Open_t \\times (1 + slip)$).
    - **Standard Friction:** 0.05% commission and 0.05% slippage per side (approx 10 bps per side, 20 bps round-trip).
    - **Benchmark Convention:** The dashboard benchmark is close-normalized Buy & Hold without transaction costs; strategy returns fully reflect slippage and commission friction.
    - **Starting Capital:** {format_currency(INITIAL_CAPITAL, ticker)} base capital.
    """)

    st.markdown("""
    ##### 3. Academic Research Distinction: Single-Split vs. Rolling 6-Year Campaign
    - **This Interactive Workspace:** Runs a **single-split chronological evaluation** on the selected equity for rapid parameter exploration and visual auditing.
    - **Reviewed Research Paper & College Report:** Based on the **multi-year rolling walk-forward campaign (2020–2025)** across **18 asset-year folds** and **54 fold-seed runs** (3 assets × 6 test years × 3 random seeds). Rolling results carry capital forward and are documented in `reports/submission/`.
    """)

    st.markdown("""
    ##### 4. Research Scope & Honest Evidence Policy
    - **No Live Trading / Broker Connection:** This software is an academic simulation engine; it does not connect to live broker APIs or execute real financial orders.
    - **No Guaranteed Future Alpha:** Past simulated performance does not guarantee future financial returns. Machine learning directional signals in liquid markets provide modest predictability (historical test AUC ~0.53).
    """)

    # Project Authors & Credits
    st.markdown("---")
    st.markdown("""
    **Project Details:**
    - **Authors:** Ashish Ranjan, Khuushi Maheshwari, Satyanarayan H.
    - **Affiliation:** Department of Computer Science, Manipal Institute of Technology (B.Tech Computer Science).
    - **Supervisor:** 
    """)
