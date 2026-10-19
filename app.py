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
import re
import streamlit as st
import pandas as pd

from src.config import DEFAULT_TICKERS, INITIAL_CAPITAL, DEFAULT_COMMISSION_PCT, DEFAULT_SLIPPAGE_PCT
from src.pipeline import run_experiment_pipeline
from src.backtest_engine import get_detailed_simulation_results

from ui.styles import CUSTOM_CSS
from ui.formatting import format_currency, format_pct, format_ratio, get_asset_currency_info
from ui.charts import create_pareto_chart, create_equity_drawdown_chart, create_feature_importance_chart
from ui.metadata import GENE_DEFINITIONS, FEATURE_GLOSSARY
from ui.state import validate_results_for_display


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


def info_icon(label: str, explanation: str) -> str:
    """Hover help with native click/Enter/Space expansion for touch and keyboard."""
    return (
        '<details class="eml-info">'
        f'<summary aria-label="About {html.escape(label, quote=True)}" title="{html.escape(explanation, quote=True)}">ⓘ</summary>'
        f'<div class="eml-tooltip" role="note">{html.escape(explanation)}</div>'
        '</details>'
    )


def section_title(label: str, explanation: str) -> None:
    st.markdown(
        f'<div class="eml-section-title">{html.escape(label)} {info_icon(label, explanation)}</div>',
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# 2. Cached Pipeline Execution
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner=False, ttl=3600)
def execute_pipeline_cached(ticker_sym: str, population: int, generations: int, rnd_seed: int, offline_mode: bool = False):
    """
    Executes single-split chronological research pipeline.
    Cached across identical parameter combinations to preserve session responsiveness.
    """
    return run_experiment_pipeline(
        ticker=ticker_sym,
        pop_size=population,
        num_generations=generations,
        seed=rnd_seed,
        offline=offline_mode,
    )


# -----------------------------------------------------------------------------
# 3. Sidebar Controls & Parameter Helpers
# -----------------------------------------------------------------------------
st.sidebar.markdown("### Experiment")

# Section A: Stock or Asset
default_idx = DEFAULT_TICKERS.index("RELIANCE.NS") if "RELIANCE.NS" in DEFAULT_TICKERS else 0
selected_ticker = st.sidebar.selectbox(
    "Asset",
    options=DEFAULT_TICKERS,
    index=default_idx,
    key="select_universe_ticker",
    help="Core research evaluated Indian NSE equities (RELIANCE.NS, TCS.NS, INFY.NS); US indices/equities (SPY, AAPL) are exploratory reference tickers.",
)
custom_ticker_raw = st.sidebar.text_input(
    "Custom symbol",
    value="",
    key="input_custom_ticker",
    help="Enter an external symbol (e.g. RELIANCE.NS, TCS.NS, SPY, AAPL). Overrides dropdown when provided.",
).strip()

# Normalize case only: silently removing characters could run a different asset.
clean_custom = custom_ticker_raw.upper()
custom_is_invalid = bool(clean_custom) and (
    re.fullmatch(r"[A-Z0-9._^-]+", clean_custom) is None
    or not re.search(r"[A-Z0-9]", clean_custom)
)

if custom_is_invalid:
    st.sidebar.error("Invalid custom ticker format. Use letters, numbers, dot, hyphen, underscore, or caret, and include at least one letter or number.")
    active_ticker = clean_custom
elif clean_custom:
    active_ticker = clean_custom
    st.sidebar.caption(f"Using {active_ticker}")
else:
    active_ticker = selected_ticker
    pass

# Section B: Evolutionary Search Settings
st.sidebar.markdown("---")
offline_mode = st.sidebar.checkbox(
    "Use saved historical data (offline)",
    value=False,
    key="checkbox_offline",
    help="Use a compatible saved price snapshot without any network refresh. This is historical data, not live prices; the actual snapshot dates are shown with the results.",
)
st.sidebar.markdown("**Search**")

pop_size = st.sidebar.slider(
    "Population",
    min_value=20,
    max_value=100,
    value=40,
    step=10,
    key="slider_pop_size",
    help="Size of the population evolving on Development data.",
)
st.sidebar.caption(f"{pop_size} strategies per generation")

num_generations = st.sidebar.slider(
    "Generations",
    min_value=5,
    max_value=40,
    value=15,
    step=5,
    key="slider_generations",
    help="Generations of repeated selection, crossover, and mutation.",
)


with st.sidebar.expander("Advanced", expanded=False):
    seed = st.number_input(
        "Seed",
        min_value=1,
        max_value=99999,
        value=42,
        step=1,
        key="num_seed",
        help="Controls random number generation for NSGA-II crossover and mutation. Note: The LightGBM classifier seed is fixed by the backend for consistency.",
    )


st.sidebar.markdown("---")
run_experiment_clicked = st.sidebar.button(
    "Run Experiment",
    type="primary",
    use_container_width=True,
    key="btn_run_experiment",
    disabled=custom_is_invalid,
    help="Run feature preparation, model fitting, strategy search and frozen test evaluation. Identical settings may reuse a result for up to one hour. Editing controls does not change displayed results until you run again.",
)
st.sidebar.caption("First runs may take longer while data and simulation kernels load.")


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

def store_successful_run(results_candidate):
    """Commit a complete run atomically and reset inspection-only controls."""
    validate_results_for_display(results_candidate)
    st.session_state.pipeline_results = results_candidate
    st.session_state.executed_settings = {
        "ticker": active_ticker,
        "pop_size": pop_size,
        "generations": num_generations,
        "seed": seed,
        "offline": offline_mode,
    }
    st.session_state.has_run = True
    st.session_state.last_error = None
    for key in ("select_candidate_id", "select_trade_outcome", "select_trade_reason"):
        st.session_state.pop(key, None)


# If user clicked Run Experiment, execute pipeline with error safety
if run_experiment_clicked and not custom_is_invalid:
    with st.spinner(f"Running Two-Tier Optimization on {active_ticker} (N={pop_size}, G={num_generations}, Seed={seed})..."):
        try:
            results_candidate = execute_pipeline_cached(active_ticker, pop_size, num_generations, seed, offline_mode)
            store_successful_run(results_candidate)
        except Exception as e:
            st.session_state.last_error = f"Execution failed for {active_ticker}: {str(e)}"

# -----------------------------------------------------------------------------
# 5. Header Banner & Execution Context Chips
# -----------------------------------------------------------------------------
st.markdown("""
<div class="eml-header">
    <div class="eml-title">
        <span>Evolutionary Market Lab</span>
        <span class="eml-title-badge">Research</span>
    </div>
    <div class="eml-subtitle">
        LightGBM + NSGA-II · Single-split simulation · No live trading
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
        or offline_mode != exec_cfg.get("offline", False)
    )

    if is_stale:
        st.markdown(f"""
        <div class="eml-banner eml-banner-warning">
            <div>
                <strong>Pending Settings Modified:</strong> Results still show {html.escape(exec_cfg['ticker'])}, N={exec_cfg['pop_size']}, G={exec_cfg['generations']}, seed {exec_cfg['seed']}, {'offline' if exec_cfg.get('offline') else 'online/cache'} mode.
                Click <strong>Run Experiment</strong> to apply your changes.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="eml-chip-bar">
        <div class="eml-chip eml-chip-status">
            <strong>Completed</strong>
        </div>
        <div class="eml-chip">
            <span>Asset:</span> <strong>{html.escape(exec_cfg['ticker'])}</strong>
        </div>
        <div class="eml-chip">
            <span>Test:</span> <strong>{t_start} to {t_end} ({len(test_split)} bars)</strong>
        </div>
        <div class="eml-chip">
            <strong>N {exec_cfg['pop_size']} · G {exec_cfg['generations']} · Seed {exec_cfg['seed']}</strong>
        </div>

    </div>
    """, unsafe_allow_html=True)


if st.session_state.has_run and st.session_state.pipeline_results is not None:
    provenance = st.session_state.pipeline_results.get("data_provenance", {})
    source_labels = {
        "download": "Downloaded prices", "cache": "Saved cache",
        "cache_fallback": "Saved cache · refresh failed", "offline_snapshot": "Offline snapshot",
    }
    if provenance:
        source_label = source_labels.get(provenance.get("source"), "Historical data")
        raw_rows = provenance.get("rows")
        row_label = f"{raw_rows:,}" if isinstance(raw_rows, int) else str(raw_rows or "?")
        st.caption(f"{source_label} · {str(provenance.get('first_date', ''))[:10]} to {str(provenance.get('last_date', ''))[:10]} · {row_label} price bars")
        if provenance.get("source") == "cache_fallback":
            st.warning("Live refresh failed. These results use a saved, potentially stale price snapshot.")
        elif provenance.get("source") == "offline_snapshot":
            st.info("Offline snapshot · historical data only; no live refresh.")


# -----------------------------------------------------------------------------
# 6. First-Run State (Clean guidance when no experiment executed yet)
# -----------------------------------------------------------------------------
if not st.session_state.has_run or st.session_state.pipeline_results is None:
    st.markdown("""
    <div class="eml-empty-card">
        <div class="eml-empty-title">Test a strategy. Understand the trade-offs.</div>
        <div class="eml-empty-desc">
            Pick an asset, evolve trading rules, then inspect unseen test results.
        </div>
        <div class="eml-steps-grid">
            <div class="eml-step-item">
                <div class="eml-step-num">Step 1</div>
                <div class="eml-step-title">Choose an asset</div>
                <div class="eml-step-desc">Set population, generations and seed in the sidebar.</div>
            </div>
            <div class="eml-step-item">
                <div class="eml-step-num">Step 2</div>
                <div class="eml-step-title">Run the experiment</div>
                <div class="eml-step-desc">Train the model and search for trading rules.</div>
            </div>
            <div class="eml-step-item">
                <div class="eml-step-num">Step 3</div>
                <div class="eml-step-title">Explore the results</div>
                <div class="eml-step-desc">Compare risk and return. Inspect every trade.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Offer inline button for immediate execution using active sidebar settings
    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    with col_c2:
        if st.button(f"Run Experiment on {active_ticker}", type="primary", use_container_width=True, key="btn_first_run_inline", disabled=custom_is_invalid):
            with st.spinner(f"Running Two-Tier Optimization on {active_ticker} (N={pop_size}, G={num_generations}, Seed={seed})..."):
                try:
                    res = execute_pipeline_cached(active_ticker, pop_size, num_generations, seed, offline_mode)
                    store_successful_run(res)
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
    "Overview",
    "Strategies",
    "Model",
    "Trades",
    "Method",
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
            <div class="eml-kpi-label">Primary Strategy Return {info_icon('Primary Strategy Return', 'Cumulative test return of the frozen primary strategy, selected by the development-only eligibility and Sharpe rule. Includes commission and slippage.')}</div>
            <div class="eml-kpi-value">{format_pct(strat_ret, include_sign=True)}</div>
            <div class="eml-kpi-delta {diff_class}">{diff_sign}{diff_pp:.2f} pp vs Benchmark</div>
            <div class="eml-kpi-subtext">Frozen Strategy #{frozen_id}</div>
        </div>
        <div class="eml-kpi-card">
            <div class="eml-kpi-label">Benchmark Buy & Hold {info_icon('Benchmark Buy & Hold', 'Cost-matched buy-and-hold invests at the first tradable Open and liquidates at the last tradable Close, using the same commission, slippage and volume rules. Scheduled historical endpoint; 100% capital allocation.')}</div>
            <div class="eml-kpi-value">{format_pct(bench_ret, include_sign=True)}</div>
            <div class="eml-kpi-delta {bench_ret_class}">Cost-matched buy & hold</div>
            <div class="eml-kpi-subtext">100% Capital Invested</div>
        </div>
        <div class="eml-kpi-card">
            <div class="eml-kpi-label">Max Drawdown {info_icon('Max Drawdown', 'Largest decline from a running portfolio peak, including initial capital. Shown as a positive loss magnitude; the underwater chart uses negative values.')}</div>
            <div class="eml-kpi-value">{format_pct(strat_mdd)}</div>
            <div class="eml-kpi-delta eml-delta-neutral">Benchmark MDD: {format_pct(bench_mdd)}</div>
            <div class="eml-kpi-subtext">Peak-to-trough decline</div>
        </div>
        <div class="eml-kpi-card">
            <div class="eml-kpi-label">Annualized Sharpe {info_icon('Annualized Sharpe', 'Mean daily return divided by daily-return population standard deviation, multiplied by square root of 252. Risk-free rate is zero. Higher is better; no guarantee of future return.')}</div>
            <div class="eml-kpi-value">{format_ratio(sharpe)}</div>
            <div class="eml-kpi-delta eml-delta-neutral">Risk-free rate: 0.0%</div>
            <div class="eml-kpi-subtext">Daily returns · √252</div>
        </div>
        <div class="eml-kpi-card">
            <div class="eml-kpi-label">Trades & Win Rate {info_icon('Trades & Win Rate', 'Completed round trips on test data, including the final liquidation. Win rate is the fraction with net profit above zero; break-even is not a win.')}</div>
            <div class="eml-kpi-value">{trades_count} trades</div>
            <div class="eml-kpi-delta eml-delta-neutral">Win Rate: {format_pct(win_rate) if trades_count > 0 else 'N/A'}</div>
            <div class="eml-kpi-subtext">Next-bar execution timing</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Equity and Underwater Drawdown Charts
    section_title("Equity & drawdown", "Test-period equity and peak-to-trough drawdown for the frozen primary strategy and cost-matched buy-and-hold. Hover a date to compare both paths; use the legend to hide a series.")
    fig_overview_equity = create_equity_drawdown_chart(sim_primary, ticker, test_df)
    st.plotly_chart(fig_overview_equity, use_container_width=True)

    # Plain-language Reading Guide
    with st.expander("How to read these results", expanded=False):
        st.markdown(f"""
        - **Primary Strategy Status:** Strategy `#{frozen_id}` was selected using the trade-count eligibility and raw Sharpe rule on the **Development partition** (before test data was inspected).
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
        section_title("Inspect a strategy", "Browse candidates retained by the search. Only the frozen primary was selected before test evaluation; inspecting other test results is exploratory.")

        # Short option text preventing UI truncation
        strategy_ids = [int(r["id"]) for _, r in summary_df.iterrows()]
        default_sel_idx = strategy_ids.index(frozen_id) if frozen_id in strategy_ids else 0

        def format_strategy_option(sid: int) -> str:
            if sid == frozen_id:
                return f"Strategy #{sid} (Primary)"
            return f"Strategy #{sid}"

        selected_id = st.selectbox(
            "Candidate",
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
                <strong>Frozen primary</strong> · selected on development data.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="eml-strat-status eml-strat-exploratory">
                <strong>Exploratory only</strong> · primary remains #{frozen_id}.
            </div>
            """, unsafe_allow_html=True)

        # Comparative Metrics Table (Dev vs Test)
        section_title("Performance", "Raw measured metrics without search penalties. Development data selects the primary; inspecting other candidates on test data is exploratory.")
        perf_data = [
            ("Annualized Sharpe Ratio", f"{chosen_row['dev_sharpe']:.2f}", f"{chosen_row['exploratory_test_sharpe']:.2f}"),
            ("Maximum Drawdown", f"{chosen_row['dev_mdd']*100:.2f}%", f"{chosen_row['exploratory_test_mdd']*100:.2f}%"),
            ("Cumulative Return", f"{chosen_row['dev_ret']*100:+.2f}%", f"{chosen_row['exploratory_test_ret']*100:+.2f}%"),
            ("Completed Trades", f"{int(chosen_row['dev_trades'])}", f"{int(chosen_row['exploratory_test_trades'])}"),
        ]
        perf_df = pd.DataFrame(perf_data, columns=["Metric", "Development", "Frozen Test" if is_primary else "Exploratory Test"])
        st.dataframe(perf_df, hide_index=True, use_container_width=True)

    with col_exp_left:
        section_title("Risk & return", "GA fitness uses low-trade penalties. These points show raw measured Sharpe and drawdown, so they need not be a Pareto frontier in these coordinates. Test points are exploratory and never select the primary.")
        fig_pareto = create_pareto_chart(summary_df, selected_id, frozen_id)
        st.plotly_chart(fig_pareto, use_container_width=True)
        st.caption("Raw metrics · development-selected candidates · test points are exploratory")

    # Evolved Chromosome Parameter Cards
    st.markdown("---")
    section_title("Trading rules", "Seven evolved genes control model-probability entry and exit thresholds, ATR brackets, trailing stops, volatility-adjusted position sizing and maximum holding time. Open the parameter guide for individual definitions.")

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
    st.dataframe(gene_df.drop(columns=["Purpose / Role"]), hide_index=True, use_container_width=True)
    with st.expander("Parameter guide", expanded=False):
        for definition in GENE_DEFINITIONS:
            st.markdown(f"**{definition['label']}** · {definition['purpose']}")


# =============================================================================
# TAB 3: MODEL INSIGHTS
# =============================================================================
with tab_model:
    predictor = results["predictor"]
    feat_cols = results["feature_cols"]

    col_m1, col_m2 = st.columns([1, 1])

    with col_m1:
        section_title("Validation scores", "LightGBM estimates whether the close will be higher three trading bars later. These are validation scores used during model development, not untouched test scores.")

        # Validation metrics if available
        metrics = getattr(predictor, "metrics", {})
        v_auc = metrics.get("val_auc", None)
        v_acc = metrics.get("val_acc", None)
        v_brier = metrics.get("val_brier", None)

        if any(value is not None for value in (v_auc, v_acc, v_brier)):
            c1, c2, c3 = st.columns(3)
            c1.metric("Validation AUC", format_ratio(v_auc, decimal_places=4), help="Area Under ROC Curve on the purged validation partition.")
            c2.metric("Directional Accuracy", format_pct(v_acc), help="Correct classifications on the validation partition using P(Up) > 0.5.")
            c3.metric("Brier Score", format_ratio(v_brier, decimal_places=4), help="Mean squared probability error on the validation partition; lower is better. This does not establish calibration.")
        else:
            st.info("Validation diagnostics are unavailable for this run.")
        st.caption("Validation data · probability calibration not established")

        st.markdown("---")
        section_title("Feature importance", "Total LightGBM gain from splits using each feature. This describes fitted-model use, not causal evidence or a guarantee of future predictive value.")
        imp_df = predictor.get_feature_importances()
        fig_imp = create_feature_importance_chart(imp_df, len(feat_cols))
        st.plotly_chart(fig_imp, use_container_width=True)


    with col_m2:
        section_title("Feature guide", "Twenty technical indicators describe historical trend, momentum, volatility, volume and market regime. Expand a group for definitions.")

        for category, cat_feats in FEATURE_GLOSSARY.items():
            with st.expander(category, expanded=False):
                for fname, fdesc in cat_feats.items():
                    st.markdown(f"- **`{fname}`**: {fdesc}")


# =============================================================================
# TAB 4: TRADE JOURNAL
# =============================================================================
with tab_journal:
    section_title("Trade journal", "Completed simulated trades for the inspected candidate. Net P&L includes commission and slippage. Filters only change displayed and filtered-export rows; the complete export and performance metrics retain all trades.")
    
    # Prominent Strategy Identity Chip
    if selected_id == frozen_id:
        st.markdown(f"""
        <div class="eml-strat-status eml-strat-primary" style="margin-bottom: 12px;">
            <strong>Strategy #{selected_id}</strong> · frozen primary · test trades
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="eml-strat-status eml-strat-exploratory" style="margin-bottom: 12px;">
            <strong>Strategy #{selected_id}</strong> · exploratory · primary remains #{frozen_id}
        </div>
        """, unsafe_allow_html=True)

    sim_selected = sim_primary if selected_id == frozen_id else get_detailed_simulation_results(test_df, p_up_test, chosen_genes)
    trades_df = sim_selected["trade_log"]

    if trades_df.empty:
        st.info(f"No trades were executed on the test partition for Strategy #{selected_id}.")
    else:
        # Filters bar
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            outcome_filter = st.selectbox(
                "Outcome",
                options=["All Trades", "Profitable Trades Only", "Loss Trades Only", "Break-even Trades Only"],
                index=0,
                key="select_trade_outcome",
                help="Filter by net P&L after costs: profitable > 0, loss < 0, or break-even = 0. Performance metrics are unchanged.",
            )
        with col_f2:
            reasons = ["All Reasons"] + sorted(list(trades_df["exit_reason"].unique()))
            reason_filter = st.selectbox(
                "Exit reason",
                options=reasons,
                index=0,
                key="select_trade_reason",
                help="Show trades closed by a particular exit rule. The complete CSV still includes every trade.",
            )

        # Apply display filters without modifying underlying backtest metrics
        filtered_trades = trades_df.copy()
        if outcome_filter == "Profitable Trades Only":
            filtered_trades = filtered_trades[filtered_trades["pnl"] > 0]
        elif outcome_filter == "Loss Trades Only":
            filtered_trades = filtered_trades[filtered_trades["pnl"] < 0]
        elif outcome_filter == "Break-even Trades Only":
            filtered_trades = filtered_trades[filtered_trades["pnl"] == 0]

        if reason_filter != "All Reasons":
            filtered_trades = filtered_trades[filtered_trades["exit_reason"] == reason_filter]

        st.caption(f"Showing {len(filtered_trades)} of {len(trades_df)} trades · performance metrics unchanged")

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
    section_title("Method & evidence", "This interactive single-split experiment is separate from the archived 2020–2025 rolling research campaign. Historical simulated returns do not guarantee future performance.")

    splits = results["splits"]
    split_labels = {"train": "Train", "val": "Validation", "dev": "Development", "test": "Test"}
    roles = {"train": "Fit model", "val": "Early stopping", "dev": "Search & select strategy", "test": "Evaluate frozen primary"}
    timeline = []
    for key, label in split_labels.items():
        partition = splits[key]
        timeline.append({"Partition": label, "From": str(partition["Date"].iloc[0])[:10], "To": str(partition["Date"].iloc[-1])[:10], "Bars": len(partition), "Purpose": roles[key]})
    st.dataframe(pd.DataFrame(timeline), hide_index=True, use_container_width=True)
    st.caption("Chronological partitions · 3-bar purged gaps · no live trading")

    with st.expander("Selection & execution", expanded=False):
        st.markdown(f"""
        - Primary #{frozen_id}: highest raw development Sharpe among candidates with at least three completed development trades. If none qualify, highest raw development Sharpe overall.
        - Signals at the previous close execute at the next open. Commission: {format_pct(DEFAULT_COMMISSION_PCT)} per side; slippage: {format_pct(DEFAULT_SLIPPAGE_PCT)} per side.
        - Benchmark: cost-matched buy-and-hold from the first tradable open to the last tradable close. The historical endpoint is scheduled retrospectively. Benchmark allocates 100%; the hybrid allocates up to 95%, with a volatility discount.
        - Starting capital: {format_currency(INITIAL_CAPITAL, ticker)}. Search seed: {exec_cfg['seed']}; model seed: {results.get('model_seed', 42)}.
        - GA low-trade fitness penalties guide search; displayed performance metrics are raw measurements.
        """)

    with st.expander("Data provenance", expanded=False):
        provenance = results.get("data_provenance", {})
        if provenance:
            st.json({key: provenance.get(key) for key in ("ticker", "provider", "source", "first_date", "last_date", "rows", "retrieved_at", "stale_cache", "raw_sha256")})
        else:
            st.info("Detailed data provenance is unavailable for this run.")

    with st.expander("Research boundaries", expanded=False):
        st.markdown("""
        - This dashboard runs one chronological split for exploration. The archived study uses 2020–2025 rolling evaluation: 18 asset-year folds and 54 fold-seed runs. These are separate results.
        - No broker connection or real orders. Historical simulated performance does not guarantee future returns.
        - Model probabilities are estimates; calibration has not been established. Feature importance is not causal evidence.
        - Repeated test inspection can introduce selection bias. Exploratory candidates never replace the development-selected primary automatically.
        """)
    st.caption("Ashish Ranjan · Khuushi Maheshwari · Satyanarayan H. | B.Tech Computer Science · Manipal Institute of Technology")
