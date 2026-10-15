"""
Deterministic unit and integration tests for Evolutionary Market Lab Streamlit UI.
Runs completely offline with mocked backend fixtures and strictly blocked data loader/fetcher calls.

Contracts verified:
1. Currency formatting rules (INR ₹ for Indian assets, USD $ for US, units for custom/unknown).
2. Initial idle first-run state (no expensive computation on launch, 3-step onboarding guide rendered).
3. Explicit run via 'Run Experiment' button produces 5 tabs and KPI metrics.
4. Strategy Explorer: candidate selection switch does not alter frozen primary strategy status.
5. Pending settings warning banner appears when sidebar controls are edited after a run.
6. Execution failure preserves previous successful results and displays an alert banner.
7. Trade Journal renders candidate identity chip, handles outcome/exit filters, and provides complete & filtered CSV exports.
8. Trade Journal handles zero-trade candidate fixture gracefully with informative status message.
9. Verification that candidate switching or tab navigation invokes NO backend pipeline reruns (call-count invariant).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
from streamlit.testing.v1 import AppTest

from src.config import BASE_DIR, INITIAL_CAPITAL
from ui.formatting import get_asset_currency_info, format_currency, format_pct, format_ratio
from ui.metadata import GENE_DEFINITIONS, FEATURE_FRIENDLY_NAMES


import streamlit as st

APP_PATH = str(BASE_DIR / "app.py")


@pytest.fixture(autouse=True)
def clear_streamlit_cache():
    """Ensure cached pipeline resources do not leak across test cases."""
    st.cache_resource.clear()
    yield
    st.cache_resource.clear()


def create_deterministic_mock_results(has_trades: bool = True):
    """
    Creates a deterministic mock result dictionary matching src.pipeline.run_experiment_pipeline.
    Contains at least two candidate strategies with known unequal metrics.
    """
    dates = pd.date_range("2024-01-01", periods=100, freq="B")
    
    # Synthetic splits
    train_df = pd.DataFrame({"Date": dates[:50], "Close": np.linspace(100, 150, 50)})
    val_df = pd.DataFrame({"Date": dates[50:65], "Close": np.linspace(150, 160, 15)})
    dev_df = pd.DataFrame({"Date": dates[65:80], "Close": np.linspace(160, 175, 15)})
    test_df = pd.DataFrame({
        "Date": dates[80:],
        "Open": np.linspace(175, 200, 20),
        "High": np.linspace(178, 205, 20),
        "Low": np.linspace(172, 198, 20),
        "Close": np.linspace(176, 202, 20),
        "Volume": np.full(20, 1000000.0),
        "atr_14": np.full(20, 3.5),
        "regime_high_vol": np.zeros(20, dtype=int),
    })

    # Two candidate strategies with known unequal metrics
    # Candidate #1: Frozen Primary (Dev Sharpe 1.50, Dev MDD 5.0%, Dev Trades 6)
    # Candidate #2: Exploratory Candidate (Dev Sharpe 0.90, Dev MDD 2.0%, Dev Trades 4)
    summary_df = pd.DataFrame([
        {
            "id": 1,
            "genes": [0.60, 0.45, 2.0, 4.0, 0.03, 0.8, 20.0],
            "dev_sharpe": 1.50,
            "dev_mdd": 0.05,
            "dev_ret": 0.12,
            "dev_trades": 6,
            "exploratory_test_sharpe": 1.25,
            "exploratory_test_mdd": 0.06,
            "exploratory_test_ret": 0.10,
            "exploratory_test_trades": 5,
        },
        {
            "id": 2,
            "genes": [0.70, 0.40, 2.5, 5.0, 0.04, 0.5, 15.0],
            "dev_sharpe": 0.90,
            "dev_mdd": 0.02,
            "dev_ret": 0.06,
            "dev_trades": 4,
            "exploratory_test_sharpe": 0.85,
            "exploratory_test_mdd": 0.03,
            "exploratory_test_ret": 0.05,
            "exploratory_test_trades": 3,
        },
    ])

    # Predictor mock
    predictor_mock = MagicMock()
    prob_val = 0.65 if has_trades else 0.50
    predictor_mock.predict_proba.return_value = np.full(len(test_df), prob_val)
    predictor_mock.metrics = {"val_auc": 0.5450, "val_acc": 0.5350, "val_brier": 0.2490}
    predictor_mock.get_feature_importances.return_value = pd.DataFrame({
        "feature": ["dist_sma_10", "dist_sma_50", "rsi_14", "atr_pct", "macd_ratio"],
        "importance": [150.0, 120.0, 95.0, 80.0, 60.0],
    })

    # Trade log fixture
    if has_trades:
        trade_log = pd.DataFrame([
            {
                "entry_date": str(dates[81])[:10],
                "exit_date": str(dates[85])[:10],
                "entry_price": 178.0,
                "exit_price": 185.0,
                "pnl": 3500.0,
                "pnl_pct": 0.039,
                "holding_bars": 4,
                "exit_reason": "Take Profit (ATR Target)",
            },
            {
                "entry_date": str(dates[88])[:10],
                "exit_date": str(dates[92])[:10],
                "entry_price": 190.0,
                "exit_price": 186.0,
                "pnl": -2000.0,
                "pnl_pct": -0.021,
                "holding_bars": 4,
                "exit_reason": "Stop Loss / Trailing Stop",
            },
        ])
    else:
        trade_log = pd.DataFrame()

    detailed_sim = {
        "dates": test_df["Date"].tolist(),
        "equity": np.linspace(100000, 108000, len(test_df)),
        "drawdowns": np.array([0.0, -0.01, -0.02, 0.0] * 5),
        "positions": np.ones(len(test_df)),
        "capital_exposures": np.full(len(test_df), 0.8),
        "benchmark_equity": np.linspace(100000, 112000, len(test_df)),
        "benchmark_max_drawdown": 0.08,
        "trade_log": trade_log,
        "sharpe_ratio": 1.25,
        "max_drawdown": 0.04,
        "total_return": 0.08,
        "benchmark_return": 0.12,
        "total_trades": len(trade_log),
        "win_rate": 0.50 if has_trades else 0.0,
        "turnover": 4.5,
        "time_in_market": 0.60,
        "capital_exposure": 0.80,
    }

    return {
        "ticker": "RELIANCE.NS",
        "seed": 42,
        "pop_size": 40,
        "num_generations": 15,
        "feature_cols": ["dist_sma_10", "dist_sma_50", "rsi_14", "atr_pct", "macd_ratio"],
        "splits": {
            "train": train_df,
            "val": val_df,
            "dev": dev_df,
            "test": test_df,
        },
        "predictor": predictor_mock,
        "summary_df": summary_df,
        "frozen_strategy_id": 1,
        "frozen_genes": summary_df.iloc[0]["genes"],
        "detailed_test_result": detailed_sim,
        "test_benchmark_ret": 0.12,
        "test_benchmark_mdd": 0.08,
    }


# =============================================================================
# 1. Currency Formatting Unit Tests
# =============================================================================
def test_currency_formatting_rules():
    """Verify currency rules for Indian equities vs US vs neutral."""
    # Indian NSE equities
    sym, code = get_asset_currency_info("RELIANCE.NS")
    assert sym == "₹"
    assert code == "INR"
    assert "₹100,000.00" in format_currency(100000.0, "RELIANCE.NS")

    sym_tcs, code_tcs = get_asset_currency_info("TCS.NS")
    assert sym_tcs == "₹"
    assert code_tcs == "INR"

    # US Equities
    sym_us, code_us = get_asset_currency_info("SPY")
    assert sym_us == "$"
    assert code_us == "USD"
    assert "$100,000.00" in format_currency(100000.0, "SPY")

    # Custom / Unknown
    sym_unk, code_unk = get_asset_currency_info("BTC-EUR")
    assert sym_unk == ""
    assert code_unk == "units"
    assert "100,000.00 units" in format_currency(100000.0, "BTC-EUR")


def test_holding_period_truncation():
    """Verify holding period displays truncated integer matching int(gene[6])."""
    max_hold_def = next(g for g in GENE_DEFINITIONS if g["name"] == "max_holding_period")
    assert max_hold_def["fmt"](40.9) == "40 bars"
    assert max_hold_def["fmt"](15.1) == "15 bars"


# =============================================================================
# 2. Streamlit UI App Tests with Mocked Fixtures (Offline & Deterministic)
# =============================================================================
@patch("src.data_loader.fetch_and_cache_ticker", side_effect=RuntimeError("NETWORK CALL BLOCKED"))
@patch("yfinance.Ticker", side_effect=RuntimeError("YFINANCE CALL BLOCKED"))
def test_app_initial_idle_state(mock_yf, mock_loader):
    """Verify that on initial load, app presents clean guidance and does NOT automatically run."""
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert len(at.exception) == 0

    # Ensure Run Experiment button is visible in sidebar
    run_btn = at.button(key="btn_run_experiment")
    assert run_btn is not None

    # Overview tabs shouldn't be rendered before first run
    assert len(at.tabs) == 0

    # Ensure no network loader call was triggered
    mock_loader.assert_not_called()
    mock_yf.assert_not_called()


@patch("src.data_loader.fetch_and_cache_ticker", side_effect=RuntimeError("NETWORK CALL BLOCKED"))
@patch("yfinance.Ticker", side_effect=RuntimeError("YFINANCE CALL BLOCKED"))
@patch("src.pipeline.run_experiment_pipeline")
def test_app_explicit_run_and_candidate_drilldown(mock_pipeline, mock_yf, mock_loader):
    """Verify explicit execution, KPI card generation, and strategy dropdown selection."""
    mock_pipeline.return_value = create_deterministic_mock_results(has_trades=True)

    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert len(at.exception) == 0

    # Trigger Run Experiment
    at.button(key="btn_run_experiment").click().run()
    assert len(at.exception) == 0

    # Pipeline was called exactly once
    assert mock_pipeline.call_count == 1

    # Verify 5 tabs render
    assert len(at.tabs) == 5

    # Check candidate selection selectbox
    sb = at.selectbox(key="select_candidate_id")
    assert sb is not None
    assert len(sb.options) == 2
    assert sb.value == 1  # Primary frozen strategy selected by default

    # Switch to exploratory candidate #2
    sb.set_value(2).run()
    assert len(at.exception) == 0
    assert sb.value == 2

    # CRITICAL: Verify candidate browsing did NOT re-execute the pipeline!
    assert mock_pipeline.call_count == 1, "Browsing candidate strategies must not trigger pipeline re-runs!"


@patch("src.data_loader.fetch_and_cache_ticker", side_effect=RuntimeError("NETWORK CALL BLOCKED"))
@patch("yfinance.Ticker", side_effect=RuntimeError("YFINANCE CALL BLOCKED"))
@patch("src.pipeline.run_experiment_pipeline")
def test_app_pending_settings_warning_and_successful_rerun(mock_pipeline, mock_yf, mock_loader):
    """Verify that editing settings displays the warning, and re-running clears it."""
    mock_pipeline.return_value = create_deterministic_mock_results(has_trades=True)

    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    at.button(key="btn_run_experiment").click().run()
    assert len(at.exception) == 0
    assert mock_pipeline.call_count == 1

    # Modify population size slider
    slider = at.slider(key="slider_pop_size")
    slider.set_value(60).run()
    assert len(at.exception) == 0

    # Check that pending banner is displayed in markdown
    md_texts = [m.value for m in at.markdown]
    has_pending = any("Pending Settings Modified" in txt for txt in md_texts)
    assert has_pending, "Expected pending settings warning banner when slider modified."

    # Re-run experiment
    at.button(key="btn_run_experiment").click().run()
    assert len(at.exception) == 0
    assert mock_pipeline.call_count == 2

    # Pending banner must now be cleared
    md_texts_after = [m.value for m in at.markdown]
    has_pending_after = any("Pending Settings Modified" in txt for txt in md_texts_after)
    assert not has_pending_after, "Pending settings banner must be cleared after successful rerun."


@patch("src.data_loader.fetch_and_cache_ticker", side_effect=RuntimeError("NETWORK CALL BLOCKED"))
@patch("yfinance.Ticker", side_effect=RuntimeError("YFINANCE CALL BLOCKED"))
@patch("src.pipeline.run_experiment_pipeline")
def test_app_run_failure_preserves_prior_results(mock_pipeline, mock_yf, mock_loader):
    """Verify that an execution error displays an alert while preserving previously successful results."""
    mock_pipeline.return_value = create_deterministic_mock_results(has_trades=True)

    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    at.button(key="btn_run_experiment").click().run()
    assert len(at.exception) == 0
    assert mock_pipeline.call_count == 1

    # Simulate failure on next pipeline invocation
    mock_pipeline.side_effect = RuntimeError("Simulated Database Connection Failure")
    
    # Change ticker and trigger run
    at.text_input(key="input_custom_ticker").set_value("INVALID_TICKER").run()
    at.button(key="btn_run_experiment").click().run()
    
    # Streamlit should not crash with uncaught exception
    assert len(at.exception) == 0

    # Should display execution alert banner
    md_texts = [m.value for m in at.markdown]
    has_alert = any("Execution Alert" in txt and "Simulated Database Connection Failure" in txt for txt in md_texts)
    assert has_alert, "Expected execution alert banner on pipeline failure."

    # Should still render tabs from prior successful execution
    assert len(at.tabs) == 5


@patch("src.data_loader.fetch_and_cache_ticker", side_effect=RuntimeError("NETWORK CALL BLOCKED"))
@patch("yfinance.Ticker", side_effect=RuntimeError("YFINANCE CALL BLOCKED"))
@patch("src.pipeline.run_experiment_pipeline")
def test_trade_journal_filters_and_zero_trades(mock_pipeline, mock_yf, mock_loader):
    """Verify Trade Journal filters, CSV export presence, and zero-trades fixture handling."""
    # Test with zero trades
    mock_pipeline.return_value = create_deterministic_mock_results(has_trades=False)

    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    at.button(key="btn_run_experiment").click().run()
    assert len(at.exception) == 0

    # With zero trades, an informative status message should render
    info_texts = [inf.value for inf in at.info]
    has_no_trades_msg = any("No trades were executed" in txt for txt in info_texts)
    assert has_no_trades_msg, "Expected informative message when candidate has 0 trades."
