"""Offline regressions for cache identity, observed labels and model/search isolation."""
import json
import random
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src import data_loader, pipeline
from src.config import PREDICTION_HORIZON_BARS
from src.evolutionary_core import Individual, NSGA2Optimizer
from src.feature_pipeline import compute_technical_indicators, prepare_feature_dataset
from src.predictor import MarketPredictor
from src.rolling_runner import simulate_buy_and_hold, simulate_sma_baseline


def bars(n=400):
    close = 100 + np.arange(n) * 0.1
    return pd.DataFrame({"Date": pd.date_range("2020-01-01", periods=n), "Open": close,
                         "High": close + 1, "Low": close - 1, "Close": close,
                         "Volume": np.full(n, 1000.0)})


def downloader(monkeypatch, tmp_path, data=None):
    monkeypatch.setattr(data_loader, "RAW_DATA_DIR", tmp_path)
    calls = []
    data = bars() if data is None else data

    def history(**kwargs):
        calls.append(kwargs)
        return data.set_index("Date")

    monkeypatch.setattr(data_loader.yf, "Ticker", lambda ticker: SimpleNamespace(history=history))
    return calls


def test_cache_respects_requested_range_and_records_provenance(monkeypatch, tmp_path):
    calls = downloader(monkeypatch, tmp_path)
    first = data_loader.fetch_and_cache_ticker("TEST", "2020-01-01", "2020-06-01")
    again = data_loader.fetch_and_cache_ticker("TEST", "2020-01-01", "2020-06-01")
    assert len(calls) == 1
    pd.testing.assert_frame_equal(first, again)
    assert again.attrs["data_provenance"]["source"] == "cache"
    narrowed = data_loader.fetch_and_cache_ticker("TEST", "2020-03-01", "2020-04-01")
    assert narrowed["Date"].min() == pd.Timestamp("2020-03-01")
    assert narrowed["Date"].max() == pd.Timestamp("2020-03-31")
    assert narrowed.attrs["data_provenance"]["raw_sha256"]


def test_distinct_ticker_keys_do_not_collide_or_escape_directory():
    assert data_loader.ticker_cache_key("^NSEI") != data_loader.ticker_cache_key("NSEI")
    assert "/" not in data_loader.ticker_cache_key("../../TEST")
    assert data_loader.ticker_cache_key(" reliance.ns ") == "RELIANCE.NS"


def test_bad_download_cannot_silently_become_partial_ohlcv(monkeypatch, tmp_path):
    downloader(monkeypatch, tmp_path, bars().drop(columns="Volume"))
    with pytest.raises(ValueError, match="required columns"):
        data_loader.fetch_and_cache_ticker("TEST")


def test_offline_legacy_snapshot_is_explicit_and_never_downloads(monkeypatch, tmp_path):
    calls = downloader(monkeypatch, tmp_path)
    bars().to_parquet(tmp_path / "TEST.parquet", index=False)
    data = data_loader.fetch_and_cache_ticker("TEST", offline=True)
    assert calls == []
    assert data.attrs["data_provenance"]["source"] == "offline_snapshot"
    assert data.attrs["data_provenance"]["stale_cache"] is True
    assert data.attrs["data_provenance"]["first_date"].startswith("2020-01-01")
    with pytest.raises(ValueError, match="cannot both"):
        data_loader.fetch_and_cache_ticker("TEST", offline=True, force_refresh=True)


def test_force_refresh_failure_does_not_report_old_cache_as_new(monkeypatch, tmp_path):
    downloader(monkeypatch, tmp_path)
    data_loader.fetch_and_cache_ticker("TEST", "2020-01-01", "2020-06-01")
    monkeypatch.setattr(data_loader.yf, "Ticker", lambda ticker: SimpleNamespace(history=lambda **kw: pd.DataFrame()))
    with pytest.raises(ValueError, match="No data"):
        data_loader.fetch_and_cache_ticker("TEST", "2020-01-01", "2020-06-01", force_refresh=True)


def test_unknown_future_labels_remain_unknown_and_constant_obv_is_finite():
    data = bars()
    data[["Open", "High", "Low", "Close"]] = 100.0
    indicators = compute_technical_indicators(data)
    assert indicators["target_direction"].tail(PREDICTION_HORIZON_BARS).isna().all()
    assert indicators["target_end_date"].tail(PREDICTION_HORIZON_BARS).isna().all()
    prepared, features = prepare_feature_dataset(data, "FLAT", save_processed=False)
    assert np.isfinite(prepared[features].to_numpy()).all()
    assert prepared["target_direction"].eq(0).all()


@pytest.mark.parametrize("kwargs", [
    {"horizon_bars": -1}, {"horizon_bars": 1.5}, {"train_frac": 0},
    {"val_frac": float("nan")}, {"train_frac": 0.8, "val_frac": 0.2},
])
def test_invalid_split_settings_raise_before_slicing(kwargs):
    with pytest.raises(ValueError):
        pipeline.create_purged_splits(bars(), **kwargs)


def test_splits_reject_unsorted_dates_and_insufficient_label_purge():
    processed, _ = prepare_feature_dataset(bars(), "TEST", save_processed=False)
    with pytest.raises(ValueError, match="chronologically"):
        pipeline.create_purged_splits(processed.iloc[::-1])
    with pytest.raises(ValueError, match="Label horizons"):
        pipeline.create_purged_splits(processed, horizon_bars=0)


def test_predictor_rejects_unknown_labels_and_boundary_leakage():
    frame = compute_technical_indicators(bars())
    predictor = MarketPredictor("TEST", ["Close"])
    with pytest.raises(ValueError, match="observed binary"):
        predictor.train(frame)
    with pytest.raises(ValueError, match="overlap validation"):
        predictor.train(frame.iloc[:250], frame.iloc[250:300])
    with pytest.raises(ValueError, match="not trained"):
        predictor.save()


def optimizer(**kwargs):
    arr = np.full(30, 100.0)
    return NSGA2Optimizer(arr, arr, arr + 1, arr - 1, arr / 150, np.ones(30), np.zeros(30), **kwargs)


@pytest.mark.parametrize("kwargs", [{"pop_size": 0}, {"pop_size": 1}, {"pop_size": 2.5}, {"num_generations": -1}, {"bounds": [(1, 1)] * 7}])
def test_optimizer_rejects_invalid_population_and_bounds(kwargs):
    with pytest.raises(ValueError):
        optimizer(**kwargs)


def test_optimizer_seed_is_local_and_rerun_resets_history(monkeypatch):
    opt = optimizer(pop_size=6, num_generations=3, seed=42)

    def evaluate(ind):
        ind.fitness = (float(ind.genes.sum()), float(-ind.genes[0]))
        ind.metrics = {"sharpe_ratio": ind.fitness[0], "max_drawdown": -ind.fitness[1]}

    monkeypatch.setattr(opt, "evaluate_individual", evaluate)
    random.seed(123)
    state = random.getstate()
    result_a = np.array([ind.genes for ind in opt.run(progress_callback=lambda *a: None)])
    assert random.getstate() == state
    result_b = np.array([ind.genes for ind in opt.run(progress_callback=lambda *a: random.random())])
    np.testing.assert_array_equal(result_a, result_b)
    assert len(opt.generation_history) == 3


def test_single_split_uses_volume_and_selects_without_test_metrics(monkeypatch):
    processed = bars(120)
    processed["atr_14"] = 1.0
    processed["regime_high_vol"] = 0
    processed["target_direction"] = 1
    processed["Volume"] = np.arange(len(processed), dtype=float)
    expected = pipeline.create_purged_splits(processed)
    seen_volumes = []
    candidates = [Individual([x, 0.4, 2, 3, 0.03, 0.5, 15]) for x in (0.55, 0.7)]

    class Predictor:
        model_seed = 42
        def __init__(self, *a, **kw): pass
        def train(self, *a, **kw): pass
        def predict_proba(self, df): return np.full(len(df), 0.75)

    class Optimizer:
        def __init__(self, **kw):
            np.testing.assert_array_equal(kw["volume"], expected["dev"]["Volume"])
        def run(self, **kw): return candidates

    def simulate(*args, **kw):
        seen_volumes.append(kw["volume"])
        genes = args[7]
        # Deliberately invert the ranking on test. Selection must stay development-only.
        sign = 1 if len(args[0]) == len(expected["dev"]) else -1
        return sign * genes[0], 0.1, 0.01, 5, 0.0

    monkeypatch.setattr(pipeline, "fetch_and_cache_ticker", lambda *a, **kw: processed.copy())
    monkeypatch.setattr(pipeline, "prepare_feature_dataset", lambda *a, **kw: (processed.copy(), ["Close"]))
    monkeypatch.setattr(pipeline, "MarketPredictor", Predictor)
    monkeypatch.setattr(pipeline, "NSGA2Optimizer", Optimizer)
    monkeypatch.setattr(pipeline, "run_vectorized_simulation_fast", simulate)
    monkeypatch.setattr(pipeline, "get_detailed_simulation_results", lambda *a, **kw: {"benchmark_return": .123, "benchmark_max_drawdown": .07})
    result = pipeline.run_experiment_pipeline(seed=99)
    assert result["frozen_genes"][0] == .7
    assert result["model_seed"] == 42 and result["seed"] == 99
    assert result["test_benchmark_ret"] == .123
    assert result["test_benchmark_mdd"] == .07
    for volume in seen_volumes[:2]:
        np.testing.assert_array_equal(volume, expected["dev"]["Volume"])
    for volume in seen_volumes[2:]:
        np.testing.assert_array_equal(volume, expected["test"]["Volume"])


def test_baselines_allocate_cash_including_exact_entry_fee():
    data = bars(3)
    data[["Open", "High", "Low", "Close"]] = 100.0
    data["sma_50"] = 90.0
    data["sma_200"] = 80.0
    commission = .1
    expected_terminal = 10000 * (1 - commission) / (1 + commission)
    for result in (simulate_buy_and_hold(data, commission, 0, 10000),
                   simulate_sma_baseline(data, commission, 0, 10000, prefix_signal=True)):
        assert result["equity"][-1] == pytest.approx(expected_terminal)
        assert result["trade_log"][0]["pnl"] == pytest.approx(expected_terminal - 10000)


def test_all_operational_features_are_prefix_causal():
    data = bars()
    full, features = prepare_feature_dataset(data, "TEST", save_processed=False)
    truncated = compute_technical_indicators(data.iloc[:300])
    complete = compute_technical_indicators(data)
    pd.testing.assert_frame_equal(complete.loc[:299, features], truncated[features])


def test_one_class_validation_auc_is_undefined_not_chance(monkeypatch):
    train = pd.DataFrame({"Close": [1, 2, 3, 4], "target_direction": [0, 1, 0, 1]})
    val = pd.DataFrame({"Close": [5, 6], "target_direction": [1, 1]})
    monkeypatch.setattr("src.predictor.lgb.train", lambda *a, **kw: SimpleNamespace(predict=lambda X: np.full(len(X), .7)))
    result = MarketPredictor("TEST", ["Close"]).train(train, val)
    assert np.isnan(result["val_auc"])
    assert result["val_auc_defined"] is False


def test_predictor_default_save_path_escapes_ticker(monkeypatch, tmp_path):
    monkeypatch.setattr("src.predictor.MODELS_DIR", tmp_path)
    predictor = MarketPredictor("../TEST", ["Close"])
    saved = []
    predictor.model = SimpleNamespace(save_model=lambda path: saved.append(path))
    target = predictor.save()
    assert target.parent == tmp_path
    assert "%2F" in target.name


def test_optimizer_keeps_measured_metrics_separate_from_fitness_penalty(monkeypatch):
    opt = optimizer(pop_size=2, num_generations=0)
    ind = Individual([.55, .4, 2, 3, .03, .5, 15])
    monkeypatch.setattr("src.evolutionary_core.run_vectorized_simulation_fast", lambda *a, **kw: (1.2, .12, .02, 2, .1))
    opt.evaluate_individual(ind)
    assert ind.metrics["sharpe_ratio"] == 1.2
    assert ind.metrics["max_drawdown"] == .12
    assert ind.fitness == pytest.approx((-.8, -.5))


@pytest.mark.parametrize("metadata", [[], {"request": None}, {"request": {}, "sha256": "bad"}])
def test_malformed_cache_metadata_is_rejected_cleanly(monkeypatch, tmp_path, metadata):
    calls = downloader(monkeypatch, tmp_path)
    bars().to_parquet(tmp_path / "TEST.parquet", index=False)
    (tmp_path / "TEST.metadata.json").write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="No compatible offline cache"):
        data_loader.fetch_and_cache_ticker("TEST", offline=True)
    data_loader.fetch_and_cache_ticker("TEST")
    assert len(calls) == 1


def test_cli_refuses_existing_versioned_results_before_running(monkeypatch, tmp_path):
    from src import walk_forward
    from src.backtest_engine import ENGINE_ACCOUNTING_VERSION
    output = tmp_path / "baseline" / f"engine_v{ENGINE_ACCOUNTING_VERSION}" / "baseline_TEST_seed42.json"
    output.parent.mkdir(parents=True)
    output.write_text("existing evidence")
    monkeypatch.setattr(walk_forward, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["src.walk_forward", "--ticker", "TEST", "--save-baseline"])
    monkeypatch.setattr(walk_forward, "run_experiment_pipeline", lambda **kw: pytest.fail("must reject before fitting"))
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        walk_forward.main()
    assert output.read_text() == "existing evidence"


def test_rolling_runner_refuses_existing_results_before_campaign(tmp_path):
    from src.rolling_runner import RollingNSEExperimentRunner
    from src.backtest_engine import ENGINE_ACCOUNTING_VERSION
    runner = RollingNSEExperimentRunner.__new__(RollingNSEExperimentRunner)
    runner.results_dir = tmp_path
    output = tmp_path / f"campaign_raw_results_v{ENGINE_ACCOUNTING_VERSION}.json"
    output.write_text("existing evidence")
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        runner.run_all()
    assert output.read_text() == "existing evidence"


@pytest.mark.parametrize("flag", ["--offline", "--force-refresh"])
def test_cli_records_exact_data_mode_and_quoted_command(monkeypatch, tmp_path, flag):
    from src import walk_forward
    from src.backtest_engine import ENGINE_ACCOUNTING_VERSION
    import shlex
    frame = bars(2)
    genes = np.array([.55, .4, 2, 3, .03, .5, 15])
    result = {
        "splits": {**{name: frame for name in ("train", "val", "dev", "test")}, "indices": {"horizon_bars": 3}},
        "dev_summary_df": pd.DataFrame([{"id": 1, "dev_sharpe": 0., "dev_mdd": 0., "dev_ret": 0., "dev_trades": 0, "dev_turnover": 0.}]),
        "frozen_strategy_id": 1, "frozen_genes": genes, "model_seed": 42,
        "feature_cols": ["Close"], "data_provenance": {"source": "offline_snapshot" if flag == "--offline" else "download"},
        "detailed_test_result": {**{name: 0. for name in ("total_return", "sharpe_ratio", "max_drawdown", "total_trades", "win_rate", "benchmark_return", "benchmark_max_drawdown", "turnover")},
                                 "trade_log": pd.DataFrame(), "dates": frame["Date"], "equity": [100000., 100000.], "drawdowns": [0., 0.]},
    }
    monkeypatch.setattr(walk_forward, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(walk_forward, "RAW_DATA_DIR", tmp_path)
    monkeypatch.setattr(walk_forward, "PROCESSED_DATA_DIR", tmp_path)
    monkeypatch.setattr(walk_forward, "_get_package_versions", lambda: {})
    monkeypatch.setattr(walk_forward, "run_experiment_pipeline", lambda **kw: result)
    monkeypatch.setattr("sys.argv", ["src.walk_forward", "--ticker", "TEST SPACE", "--save-baseline", flag])
    walk_forward.main()
    output = tmp_path / "baseline" / f"engine_v{ENGINE_ACCOUNTING_VERSION}" / "baseline_TEST%20SPACE_seed42.json"
    saved = json.loads(output.read_text())
    command = shlex.split(saved["metadata"]["command"])
    assert command[command.index("--ticker") + 1] == "TEST SPACE"
    assert flag in command
    assert saved["metadata"]["engine_accounting_version"] == ENGINE_ACCOUNTING_VERSION
