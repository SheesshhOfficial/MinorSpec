"""Offline regression checks for dashboard controls, state and chart semantics."""
from io import StringIO
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from test_ui_app import APP_PATH, create_deterministic_mock_results
from ui.charts import create_equity_drawdown_chart, create_pareto_chart


@pytest.fixture(autouse=True)
def isolated_cache():
    st.cache_resource.clear()
    yield
    st.cache_resource.clear()


@pytest.fixture
def app_factory(monkeypatch):
    def start(results=None, run=True):
        results = results if results is not None else create_deterministic_mock_results()
        pipeline = Mock(return_value=results)
        monkeypatch.setattr("src.pipeline.run_experiment_pipeline", pipeline)
        monkeypatch.setattr(
            "src.backtest_engine.get_detailed_simulation_results",
            Mock(return_value=results["detailed_test_result"]),
        )
        monkeypatch.setattr("src.data_loader.fetch_and_cache_ticker", Mock(side_effect=AssertionError("No network in UI tests")))
        app = AppTest.from_file(APP_PATH, default_timeout=30).run()
        if run:
            app.button(key="btn_run_experiment").click().run()
        return app, pipeline
    return start


@pytest.mark.parametrize("ticker", ["!!!", "AA PL", "AAPL<script>", "^", "---"])
def test_invalid_ticker_disables_both_execution_buttons(app_factory, ticker):
    app, pipeline = app_factory(run=False)
    app.text_input(key="input_custom_ticker").set_value(ticker).run()
    assert not app.exception
    assert app.button(key="btn_run_experiment").disabled
    assert app.button(key="btn_first_run_inline").disabled
    pipeline.assert_not_called()


def test_population_caption_tracks_control_value(app_factory):
    app, _ = app_factory(run=False)
    app.slider(key="slider_pop_size").set_value(70).run()
    assert any("70 strategies" in c.value for c in app.caption)
    assert not any("40 strategies" in c.value for c in app.caption)


def test_new_successful_run_resets_inspection_to_frozen_strategy(app_factory):
    app, pipeline = app_factory()
    app.selectbox(key="select_candidate_id").set_value(2).run()
    app.selectbox(key="select_trade_outcome").set_value("Profitable Trades Only").run()
    app.slider(key="slider_pop_size").set_value(60).run()
    app.button(key="btn_run_experiment").click().run()
    assert not app.exception
    assert pipeline.call_count == 2
    assert app.selectbox(key="select_candidate_id").value == 1
    assert app.selectbox(key="select_trade_outcome").value == "All Trades"


def test_partial_validation_metrics_render_without_crashing(app_factory):
    results = create_deterministic_mock_results()
    results["predictor"].metrics = {"val_auc": 0.6, "val_acc": None, "val_brier": float("nan")}
    app, _ = app_factory(results)
    assert not app.exception
    metrics = {m.label: m.value for m in app.metric}
    assert metrics["Validation AUC"] == "0.6000"
    assert metrics["Directional Accuracy"] == "N/A"
    assert metrics["Brier Score"] == "N/A"


@pytest.mark.parametrize("defect", ["empty_test", "empty_candidates", "missing_primary"])
def test_invalid_run_results_preserve_prior_successful_run(app_factory, defect):
    app, pipeline = app_factory()
    invalid = create_deterministic_mock_results()
    if defect == "empty_test":
        invalid["splits"]["test"] = invalid["splits"]["test"].iloc[:0]
    elif defect == "empty_candidates":
        invalid["summary_df"] = invalid["summary_df"].iloc[:0]
    else:
        invalid["frozen_strategy_id"] = 999
    pipeline.return_value = invalid
    app.slider(key="slider_pop_size").set_value(60).run()
    app.button(key="btn_run_experiment").click().run()
    assert not app.exception
    assert len(app.tabs) == 5
    assert app.session_state["executed_settings"]["pop_size"] == 40
    assert any("Execution Alert" in m.value for m in app.markdown)


def test_loss_and_breakeven_filters_and_csv_payloads(app_factory, monkeypatch):
    results = create_deterministic_mock_results()
    trades = results["detailed_test_result"]["trade_log"]
    flat = trades.iloc[0].copy()
    flat["pnl"] = 0.0
    flat["pnl_pct"] = 0.0
    results["detailed_test_result"]["trade_log"] = pd.concat([trades, flat.to_frame().T], ignore_index=True)
    downloads = {}
    actual_download = st.download_button

    def capture_download(*args, **kwargs):
        downloads[kwargs["key"]] = kwargs["data"]
        return actual_download(*args, **kwargs)

    monkeypatch.setattr(st, "download_button", capture_download)
    app, pipeline = app_factory(results)
    assert not app.exception
    app.selectbox(key="select_trade_outcome").set_value("Loss Trades Only").run()
    filtered = pd.read_csv(StringIO(downloads["btn_download_filtered_trades"]))
    complete = pd.read_csv(StringIO(downloads["btn_download_complete_trades"]))
    assert len(complete) == 3
    assert len(filtered) == 1
    assert (filtered["pnl"] < 0).all()
    app.selectbox(key="select_trade_outcome").set_value("Break-even Trades Only").run()
    filtered = pd.read_csv(StringIO(downloads["btn_download_filtered_trades"]))
    assert len(filtered) == 1
    assert (filtered["pnl"] == 0).all()
    assert pipeline.call_count == 1
    assert not app.exception


def test_unknown_currency_chart_labels_actual_capital_and_units():
    results = create_deterministic_mock_results()
    sim = results["detailed_test_result"]
    sim["initial_capital"] = 50000.0
    sim["equity"] = sim["equity"] / 2
    sim["benchmark_equity"] = sim["benchmark_equity"] / 2
    fig = create_equity_drawdown_chart(sim, "BTC-EUR", results["splits"]["test"])
    assert "units" in fig.layout.yaxis.title.text
    assert "50,000" in fig.layout.annotations[0].text
    assert "units" in fig.data[0].hovertemplate


def test_primary_hover_does_not_duplicate_hash_and_raw_metrics_are_labelled():
    results = create_deterministic_mock_results()
    fig = create_pareto_chart(results["summary_df"], 1, 1)
    primary = next(t for t in fig.data if "Frozen Primary" in t.name)
    assert "#%{text}" not in primary.hovertemplate
    assert "raw" in fig.data[0].name.lower()


def test_offline_toggle_is_applied_only_on_run_and_in_cache_key(app_factory):
    app, pipeline = app_factory(run=False)
    app.checkbox(key="checkbox_offline").set_value(True).run()
    pipeline.assert_not_called()
    app.button(key="btn_run_experiment").click().run()
    assert not app.exception
    assert pipeline.call_args.kwargs["offline"] is True
    assert app.session_state["executed_settings"]["offline"] is True
    app.checkbox(key="checkbox_offline").set_value(False).run()
    assert pipeline.call_count == 1
    assert any("Pending Settings Modified" in m.value for m in app.markdown)
    app.button(key="btn_run_experiment").click().run()
    assert pipeline.call_count == 2
    assert pipeline.call_args.kwargs["offline"] is False
    assert app.session_state["executed_settings"]["offline"] is False
    assert not app.exception


def test_snapshot_source_and_actual_raw_dates_are_visible(app_factory):
    results = create_deterministic_mock_results()
    results["data_provenance"] = {
        "source": "offline_snapshot", "stale_cache": True, "first_date": "2000-01-03T00:00:00",
        "last_date": "2026-10-12T00:00:00", "rows": 6789, "raw_sha256": "ab" * 32,
        "retrieved_at": None,
    }
    app, _ = app_factory(results)
    assert not app.exception
    assert any("2000-01-03 to 2026-10-12" in c.value and "6,789" in c.value for c in app.caption)
    assert any("no live refresh" in m.value for m in app.info)
    assert any(e.label == "Data provenance" for e in app.expander)


def test_browsing_preserves_primary_kpis_and_help_has_keyboard_fallback(app_factory):
    app, pipeline = app_factory()
    kpis_before = next(m.value for m in app.markdown if "Primary Strategy Return" in m.value)
    assert '<details class="eml-info">' in kpis_before
    assert '<summary aria-label="About Primary Strategy Return" title="Cumulative test return' in kpis_before
    app.selectbox(key="select_candidate_id").set_value(2).run()
    kpis_after = next(m.value for m in app.markdown if "Primary Strategy Return" in m.value)
    assert kpis_after == kpis_before
    assert pipeline.call_count == 1
    assert [tab.label for tab in app.tabs] == ["Overview", "Strategies", "Model", "Trades", "Method"]
    assert not app.exception


def test_initial_bar_benchmark_fees_are_visible_in_drawdown():
    results = create_deterministic_mock_results()
    sim = results["detailed_test_result"]
    sim["initial_capital"] = 100000.0
    sim["benchmark_equity"] = np.full(len(sim["dates"]), 99900.0)
    fig = create_equity_drawdown_chart(sim, "RELIANCE.NS", results["splits"]["test"])
    benchmark_dd = next(t for t in fig.data if t.name == "Benchmark Drawdown")
    np.testing.assert_allclose(benchmark_dd.y, -0.1)
    assert "100,000" in fig.layout.annotations[0].text


def test_inline_run_and_failure_recovery(app_factory):
    app, pipeline = app_factory(run=False)
    pipeline.side_effect = RuntimeError("Synthetic fetch failure")
    app.button(key="btn_first_run_inline").click().run()
    assert not app.exception
    assert not app.session_state["has_run"]
    assert any("Synthetic fetch failure" in e.value for e in app.error)
    pipeline.side_effect = None
    app.button(key="btn_first_run_inline").click().run()
    assert not app.exception
    assert len(app.tabs) == 5
    assert app.session_state["last_error"] is None


def test_empty_filtered_journal_keeps_complete_download(app_factory):
    app, _ = app_factory()
    app.selectbox(key="select_trade_outcome").set_value("Profitable Trades Only").run()
    app.selectbox(key="select_trade_reason").set_value("Stop Loss / Trailing Stop").run()
    assert not app.exception
    assert any("No trades match" in w.value for w in app.warning)
    labels = [element.proto.label for element in app.get("download_button")]
    assert any("Complete Log (2 trades" in label for label in labels)
    assert not any("Filtered Log" in label for label in labels)


@pytest.mark.parametrize("viewport_width", [360, 1280])
def test_equity_chart_reserves_separate_title_and_wrapping_legend_bands(viewport_width):
    """Layout contract at mobile/desktop widths; this is not a rendered-pixel test."""
    results = create_deterministic_mock_results()
    sim = results["detailed_test_result"]
    fig = create_equity_drawdown_chart(sim, "RELIANCE.NS", results["splits"]["test"])
    assert fig.layout.width is None  # Streamlit controls the responsive container width.
    fig.update_layout(width=viewport_width)

    title = fig.layout.annotations[0]
    assert "<br>" in title.text
    assert title.y >= 1
    assert title.yanchor == "bottom"
    assert title.xanchor == "left"
    assert title.font.size <= 13
    assert fig.layout.legend.orientation == "h"
    assert fig.layout.legend.yanchor == "top"
    assert fig.layout.legend.y < 0
    assert fig.layout.margin.t >= 70
    assert fig.layout.margin.b >= 140  # Space for four wrapped entries plus date ticks.
    assert fig.layout.height - fig.layout.margin.t - fig.layout.margin.b >= 380
    # Layout changes must not alter either return/equity path.
    np.testing.assert_array_equal(fig.data[0].y, sim["equity"])
    np.testing.assert_array_equal(fig.data[1].y, sim["benchmark_equity"])
