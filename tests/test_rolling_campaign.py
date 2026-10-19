"""
Offline Unit and Regression Tests for Task P002 (Rolling NSE Retrospective Campaign).

Verifies:
1. Input Snapshot Manifest integrity and SHA-256 validity.
2. Temporal isolation and purging across rolling fold partitions.
3. Feature causality: Prefix-based indicator engineering does not leak future data.
4. Zero-volume bar execution policy: No orders execute on volume == 0 bars.
5. Stitched equity curve mathematical accounting (no Sharpe/CAGR averaging across folds).
6. Baseline execution and friction consistency.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.config import INITIAL_CAPITAL, DEFAULT_COMMISSION_PCT, DEFAULT_SLIPPAGE_PCT, PREDICTION_HORIZON_BARS
from src.feature_pipeline import compute_technical_indicators
from src.backtest_engine import (
    run_vectorized_simulation_fast,
    ENGINE_ACCOUNTING_VERSION,
    get_detailed_simulation_results,
)
from src.rolling_runner import (
    compute_sha256,
    verify_manifest,
    simulate_buy_and_hold,
    simulate_cash_baseline,
    simulate_sma_baseline,
    stitch_equity_curves,
    compute_performance_metrics,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUTS_DIR = PROJECT_ROOT / "reports" / "experiments" / "inputs"
MANIFEST_PATH = INPUTS_DIR / "manifest.json"


def test_input_manifest_integrity():
    """Verify that all snapshot parquet files exist and match manifest hashes."""
    assert MANIFEST_PATH.exists(), "Manifest file missing"
    manifest = verify_manifest(INPUTS_DIR, MANIFEST_PATH)
    assert len(manifest) == 3
    for ticker in ["RELIANCE.NS", "TCS.NS", "INFY.NS"]:
        assert ticker in manifest
        parquet_file = INPUTS_DIR / f"{ticker}.parquet"
        assert parquet_file.exists()
        computed_hash = compute_sha256(parquet_file)
        assert computed_hash == manifest[ticker]["sha256"]


def test_prefix_feature_causality():
    """Ensure technical indicators computed up to bar T are identical whether full dataset or truncated dataset is passed."""
    df = pd.read_parquet(INPUTS_DIR / "RELIANCE.NS.parquet")
    df["Date"] = pd.to_datetime(df["Date"])
    df_full = compute_technical_indicators(df)

    cutoff_date = "2020-12-31"
    df_trunc = compute_technical_indicators(df[df["Date"] <= cutoff_date].copy())

    check_cols = ["sma_10", "sma_50", "sma_200", "rsi_14", "atr_14", "volatility_20", "volume_zscore"]
    for col in check_cols:
        diff = (df_full.loc[df_trunc.index, col] - df_trunc[col]).abs().max()
        assert diff == pytest.approx(0.0, abs=1e-10), f"Leakage detected in {col}"


def test_zero_volume_bar_execution_prevention():
    """Verify that equity orders do NOT execute on bars where Volume == 0."""
    n = 100
    open_p = np.full(n, 100.0, dtype=np.float64)
    close_p = np.full(n, 100.0, dtype=np.float64)
    high_p = np.full(n, 100.0, dtype=np.float64)
    low_p = np.full(n, 100.0, dtype=np.float64)
    p_up = np.full(n, 0.70, dtype=np.float64)  # High probability to trigger entry
    atr = np.full(n, 2.0, dtype=np.float64)
    reg_vol = np.zeros(n, dtype=np.int32)
    genes = np.array([0.55, 0.45, 2.0, 3.5, 0.03, 0.5, 15.0], dtype=np.float64)

    # All volume is zero -> Should never trade
    vol_zero = np.zeros(n, dtype=np.float64)
    sh, mdd, ret, trades, to = run_vectorized_simulation_fast(
        open_p, close_p, high_p, low_p, p_up, atr, reg_vol, genes,
        apply_penalty=False, volume=vol_zero
    )
    assert trades == 0, f"Expected 0 trades on zero volume bars, got {trades}"
    assert ret == pytest.approx(0.0, abs=1e-8)

    # Normal volume -> Should trade
    vol_normal = np.full(n, 10000.0, dtype=np.float64)
    sh_norm, mdd_norm, ret_norm, trades_norm, to_norm = run_vectorized_simulation_fast(
        open_p, close_p, high_p, low_p, p_up, atr, reg_vol, genes,
        apply_penalty=False, volume=vol_normal
    )
    assert trades_norm > 0, "Normal volume should execute trades"


def test_buy_and_hold_execution_friction():
    """Verify Buy & Hold accurately applies commission and slippage at bar 0 Open and bar N-1 Close."""
    dates = pd.date_range("2020-01-01", periods=10, freq="D")
    df = pd.DataFrame({
        "Date": dates,
        "Open": np.full(10, 100.0),
        "High": np.full(10, 105.0),
        "Low": np.full(10, 95.0),
        "Close": np.full(10, 100.0),
        "Volume": np.full(10, 1000.0),
    })

    bh_res = simulate_buy_and_hold(df, commission_pct=0.001, slippage_pct=0.001, initial_capital=10000.0)
    # Price is flat 100.0. Round-trip friction is:
    # Entry: 100 * (1 + 0.001) = 100.10
    # Shares: (10000 * 0.999) / 100.10 = 99.8001998
    # Exit: 100 * (1 - 0.001) = 99.90
    # Proceeds: shares * 99.90 * 0.999 = 9960.05
    # Return should be negative due to friction even with flat price
    ret = bh_res["metrics"]["total_return"]
    assert ret < 0.0, "Flat price Buy & Hold must incur round-trip friction"
    assert ret == pytest.approx(-0.00399, rel=1e-2)


def test_stitched_equity_accounting():
    """Verify that stitched equity carries capital forward via compounded returns rather than naive averaging."""
    fold1 = [100.0, 105.0, 110.0]  # +10% return
    fold2 = [100.0, 95.0, 90.0]    # -10% return

    stitched = stitch_equity_curves([fold1, fold2], initial_capital=100.0)
    assert len(stitched) == 6
    # Day 0: 100.0
    assert stitched[0] == 100.0
    # End of fold 1: 100 * (110 / 100) = 110.0
    assert stitched[2] == pytest.approx(110.0)
    # Start of fold 2: carries 110.0 * (100 / 100) = 110.0
    assert stitched[3] == pytest.approx(110.0)
    # End of fold 2: 110.0 * (90 / 100) = 99.0
    assert stitched[5] == pytest.approx(99.0)
    # Compounded total return: 99 / 100 - 1 = -1% (not 0% average)
    assert (stitched[-1] / 100.0 - 1.0) == pytest.approx(-0.01)


def test_rolling_partition_dates_and_purging():
    """Check that fold boundaries do not overlap and 3 bars are purged at label boundaries."""
    df = pd.read_parquet(INPUTS_DIR / "RELIANCE.NS.parquet")
    df["Date"] = pd.to_datetime(df["Date"])
    y = 2020

    tr_raw = df[(df["Date"] >= f"{y-8}-01-01") & (df["Date"] <= f"{y-4}-12-31")].copy()
    vl_raw = df[(df["Date"] >= f"{y-3}-01-01") & (df["Date"] <= f"{y-3}-12-31")].copy()
    dv_df = df[(df["Date"] >= f"{y-2}-01-01") & (df["Date"] <= f"{y-1}-12-31")].copy()
    ts_df = df[(df["Date"] >= f"{y}-01-01") & (df["Date"] <= f"{y}-12-31")].copy()

    tr_purged = tr_raw.iloc[:-PREDICTION_HORIZON_BARS]
    vl_purged = vl_raw.iloc[:-PREDICTION_HORIZON_BARS]

    # Verify chronological sequence
    assert tr_purged["Date"].max() < vl_raw["Date"].min()
    assert vl_purged["Date"].max() < dv_df["Date"].min()
    assert dv_df["Date"].max() < ts_df["Date"].min()


def test_regression_toy_fold_scaling():
    """
    Verify regression case [90, 99] repeated twice across two folds with initial capital 100.
    Fold 1: [90, 99] scaled by 100 -> terminal 99.0
    Fold 2: [90, 99] scaled by 99.0 -> terminal 99.0 * 99 / 100 = 98.01.
    Product of ratios: (99/100) * (99/100) = 0.9801.
    Terminal stitched equity = 100 * 0.9801 = 98.01.
    """
    fold1 = [90.0, 99.0]
    fold2 = [90.0, 99.0]
    stitched = stitch_equity_curves([fold1, fold2], initial_capital=100.0)
    assert len(stitched) == 4
    # Fold 1
    assert stitched[0] == pytest.approx(90.0)
    assert stitched[1] == pytest.approx(99.0)
    # Fold 2
    assert stitched[2] == pytest.approx(89.1)
    assert stitched[3] == pytest.approx(98.01)

    fold_ratios = [(99.0 / 100.0), (99.0 / 100.0)]
    stitched_ratio = stitched[-1] / 100.0
    assert stitched_ratio == pytest.approx(np.prod(fold_ratios), rel=1e-12)
    assert stitched[-1] == pytest.approx(98.01, rel=1e-12)


def test_regression_exposure_matched_bh():
    """
    Verify exposure-matched Buy & Hold diagnostic:
    Daily returns: r_0 = -0.10, r_1 = +0.10 (from [90, 99] relative to pre-trade capital 100).
    Exposure weight w = 0.25.
    Blended r_0 = 0.25 * -0.10 = -0.025 -> E_0 = 100 * (1 - 0.025) = 97.5.
    Blended r_1 = 0.25 * +0.10 = +0.025 -> E_1 = 97.5 * (1 + 0.025) = 99.9375.
    Repeated twice: 99.9375 * (99.9375 / 100) = 99.875039 -> rounds to 99.875.
    """
    from src.rolling_runner import simulate_exposure_matched_bh

    bh_eq = np.array([90.0, 99.0])
    bh_res = simulate_exposure_matched_bh(bh_eq, dev_exposure_fraction=0.25, initial_capital=100.0)
    eq = bh_res["equity"]
    assert eq[0] == pytest.approx(97.5, rel=1e-6)
    assert eq[1] == pytest.approx(99.9375, rel=1e-6)

    # Stitched across 2 identical folds
    stitched = stitch_equity_curves([eq.tolist(), eq.tolist()], initial_capital=100.0)
    assert stitched[-1] == pytest.approx(99.8750390625, rel=1e-6)
    assert round(stitched[-1], 3) == 99.875


def test_stitched_ratio_equals_fold_ratio_product():
    """Verify that for arbitrary non-empty curves, stitched wealth ratio strictly equals product of fold wealth ratios."""
    rng = np.random.RandomState(42)
    curves = []
    for _ in range(5):
        # Generate random equity curve starting from initial 100000
        returns = rng.normal(0.0005, 0.015, size=250)
        curve = 100000.0 * np.cumprod(1 + returns)
        curves.append(curve.tolist())

    stitched = stitch_equity_curves(curves, initial_capital=100000.0)
    fold_ratios = [c[-1] / 100000.0 for c in curves]
    expected_ratio = np.prod(fold_ratios)
    actual_ratio = stitched[-1] / 100000.0
    assert actual_ratio == pytest.approx(expected_ratio, rel=1e-9)


def test_test_label_masking_accounting():
    """Verify that test folds have scored_samples == total_bars - 3 and 3 masked samples."""
    from src.rolling_runner import RollingNSEExperimentRunner

    runner = RollingNSEExperimentRunner(
        inputs_dir=INPUTS_DIR,
        output_dir=PROJECT_ROOT / "reports" / "experiments",
        protocol_path=PROJECT_ROOT / "reports" / "experiments" / "protocol.json",
        test_years=[2020],
        universe=["RELIANCE.NS"],
        ga_seeds=[42],
    )
    df = runner.load_processed_asset("RELIANCE.NS")
    fold_res = runner.run_fold("RELIANCE.NS", df, 2020)

    model_eval = fold_res["model_eval"]
    total_bars = model_eval["test_bars"]
    assert model_eval["scored_test_samples"] == total_bars - 3
    assert model_eval["masked_test_samples"] == 3
    assert total_bars == model_eval["scored_test_samples"] + model_eval["masked_test_samples"]


def test_feasible_test_perturbation_selection_invariance():
    """
    Verify on a feasible fold (TCS.NS 2021, seed 42) that perturbing raw OHLC test partition prices,
    recomputing technical features from raw, and fitting does NOT alter Dev-selected genes,
    Dev Sharpe, or prefix context predictions.
    """
    from src.rolling_runner import RollingNSEExperimentRunner

    raw_df = pd.read_parquet(INPUTS_DIR / "TCS.NS.parquet")
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)

    clean_features = compute_technical_indicators(raw_df.copy())
    runner = RollingNSEExperimentRunner(
        inputs_dir=INPUTS_DIR,
        output_dir=PROJECT_ROOT / "reports" / "experiments",
        protocol_path=PROJECT_ROOT / "reports" / "experiments" / "protocol.json",
        test_years=[2021],
        universe=["TCS.NS"],
        ga_seeds=[42],
    )
    res_clean = runner.run_fold("TCS.NS", clean_features, 2021)

    # Perturb raw test OHLC
    pert_raw = raw_df.copy()
    test_mask = (pert_raw["Date"] >= "2021-01-01") & (pert_raw["Date"] <= "2021-12-31")
    pert_raw.loc[test_mask, "Close"] = pert_raw.loc[test_mask, "Close"] * 1.25
    pert_raw.loc[test_mask, "High"] = pert_raw.loc[test_mask, "High"] * 1.25
    pert_raw.loc[test_mask, "Low"] = pert_raw.loc[test_mask, "Low"] * 1.25
    pert_raw.loc[test_mask, "Open"] = pert_raw.loc[test_mask, "Open"] * 1.25

    pert_features = compute_technical_indicators(pert_raw)
    res_pert = runner.run_fold("TCS.NS", pert_features, 2021)

    # Must both be feasible
    assert res_clean["ga_runs"]["42"]["hybrid"]["is_feasible"] is True
    assert res_pert["ga_runs"]["42"]["hybrid"]["is_feasible"] is True

    # Dev selected genes must be strictly identical
    genes_clean = res_clean["ga_runs"]["42"]["hybrid"]["genes"]
    genes_pert = res_pert["ga_runs"]["42"]["hybrid"]["genes"]
    assert genes_clean is not None and genes_pert is not None
    np.testing.assert_allclose(genes_clean, genes_pert, rtol=1e-12, atol=1e-12)

    # Dev Sharpe must be identical
    dev_sh_clean = res_clean["ga_runs"]["42"]["hybrid"]["dev_selected_sharpe"]
    dev_sh_pert = res_pert["ga_runs"]["42"]["hybrid"]["dev_selected_sharpe"]
    assert dev_sh_clean == pytest.approx(dev_sh_pert, rel=1e-12)

    # Prefix context predictions from Dev end must be identical
    assert res_clean["prefix_context"]["prefix_p_up"] == pytest.approx(res_pert["prefix_context"]["prefix_p_up"], rel=1e-12)


@pytest.mark.skipif(ENGINE_ACCOUNTING_VERSION != 1, reason="Archived campaign equity uses v1 approximate fee sizing; reproduce with the archived v1 source. Current v2 replay is checked separately.")
def test_offline_feasible_fold_rerun_against_saved_artifact(monkeypatch):
    """
    Verify offline execution of a real feasible fold (TCS.NS 2021, seed 42) executes
    strictly from parquet snapshots without downloader calls and matches saved artifact
    full-precision genes and equity curve.
    """
    import yfinance as yf
    from src.rolling_runner import RollingNSEExperimentRunner

    def forbidden_call(*args, **kwargs):
        raise RuntimeError("Network call attempted! Test must be strictly offline.")

    monkeypatch.setattr(yf, "download", forbidden_call)
    monkeypatch.setattr(yf, "Ticker", forbidden_call)

    # Load saved full-precision results
    raw_results_file = PROJECT_ROOT / "reports" / "experiments" / "results" / "campaign_raw_results.json"
    assert raw_results_file.exists(), "Saved campaign results missing"
    with open(raw_results_file, "r") as f:
        saved_all = json.load(f)
    saved_fold = saved_all["TCS.NS"]["2021"]["ga_runs"]["42"]["hybrid"]

    # Re-run fold offline
    runner = RollingNSEExperimentRunner(
        inputs_dir=INPUTS_DIR,
        output_dir=PROJECT_ROOT / "reports" / "experiments",
        protocol_path=PROJECT_ROOT / "reports" / "experiments" / "protocol.json",
        test_years=[2021],
        universe=["TCS.NS"],
        ga_seeds=[42],
    )
    df = runner.load_processed_asset("TCS.NS")
    fresh_res = runner.run_fold("TCS.NS", df, 2021)
    fresh_fold = fresh_res["ga_runs"]["42"]["hybrid"]

    # Genes match saved artifact within absolute 1e-12
    np.testing.assert_allclose(fresh_fold["genes"], saved_fold["genes"], atol=1e-12, rtol=1e-12)
    # Entire equity path matches saved artifact within 1e-7
    np.testing.assert_allclose(fresh_fold["equity"], saved_fold["equity"], atol=1e-7, rtol=1e-7)
    # Metrics match
    assert fresh_fold["metrics"]["total_return"] == pytest.approx(saved_fold["metrics"]["total_return"], rel=1e-9)


def test_trailing_zero_volume_scheduled_fold_end_liquidation():
    """
    Verify that when synthetic test data ends with trailing zero-volume bars:
    1. Positions are liquidated at the last tradable session with positive volume.
    2. No trade executions occur on zero-volume bars.
    3. Terminal holdings are 0.0 without unliquidated open positions carryover.
    """
    from src.rolling_runner import simulate_sma_baseline, simulate_buy_and_hold
    from src.backtest_engine import get_detailed_simulation_results, run_vectorized_simulation_fast

    dates = pd.date_range("2020-01-01", periods=5, freq="D")
    df = pd.DataFrame({
        "Date": dates,
        "Open": [100.0, 105.0, 110.0, 115.0, 120.0],
        "High": [105.0, 110.0, 115.0, 120.0, 125.0],
        "Low": [95.0, 100.0, 105.0, 110.0, 115.0],
        "Close": [104.0, 109.0, 114.0, 119.0, 124.0],
        "Volume": [1000.0, 1000.0, 1000.0, 0.0, 0.0],
        "sma_50": [100.0, 100.0, 100.0, 100.0, 100.0],
        "sma_200": [90.0, 90.0, 90.0, 90.0, 90.0],
        "atr_14": [2.0, 2.0, 2.0, 2.0, 2.0],
        "regime_high_vol": [0, 0, 0, 0, 0],
    })

    # SMA Baseline
    res_sma = simulate_sma_baseline(df, prefix_signal=True)
    assert res_sma["positions"][-1] == 0.0
    assert len(res_sma["trade_log"]) == 1
    assert res_sma["trade_log"][-1]["exit_date"] == "2020-01-03"  # Bar 2 is last positive volume

    # Buy & Hold
    res_bh = simulate_buy_and_hold(df)
    assert res_bh["positions"][-1] == 0.0
    assert len(res_bh["trade_log"]) == 1
    assert res_bh["trade_log"][-1]["exit_date"] == "2020-01-03"

    # Hybrid Detailed: use wide bracket so position is held until final scheduled liquidation at bar 2
    p_up = np.full(5, 0.70)
    genes_wide = np.array([0.55, 0.45, 5.0, 10.0, 0.10, 0.5, 15.0])
    det = get_detailed_simulation_results(df, p_up, genes_wide, prefix_p_up=0.70, prefix_atr=2.0)
    assert det["positions"][-1] == 0.0
    assert len(det["trade_log"]) == 1
    last_exit = det["trade_log"].iloc[-1]["exit_date"]
    last_exit_str = last_exit.strftime("%Y-%m-%d") if hasattr(last_exit, "strftime") else str(last_exit)[:10]
    assert last_exit_str == "2020-01-03"
    assert det["trade_log"].iloc[-1]["exit_reason"] == "Final Horizon Liquidation"

    # Hybrid Fast
    sh, mdd, ret, trades, to = run_vectorized_simulation_fast(
        df["Open"].values, df["Close"].values, df["High"].values, df["Low"].values,
        p_up, df["atr_14"].values, df["regime_high_vol"].values, genes_wide,
        prefix_p_up=0.70, prefix_atr=2.0, volume=df["Volume"].values
    )
    assert trades > 0


def test_final_tradable_day_entry_prohibition():
    """
    Verify CORR-07 protocol convention:
    1. A model signal generated on bar N-2 scheduled for execution on bar N-1 (the final tradable day)
       must NOT open a new position because entry requires i < last_tradable_idx.
    2. A model signal generated on bar N-3 successfully executes on bar N-2, holds across the session,
       and then liquidates at bar N-1 Close upon scheduled horizon liquidation.
    3. Fast simulator and detailed backtest engine agree precisely on trade count and behavior.
    """
    from src.backtest_engine import get_detailed_simulation_results, run_vectorized_simulation_fast

    dates = pd.date_range("2020-01-01", periods=5, freq="D")
    df = pd.DataFrame({
        "Date": dates,
        "Open": [100.0, 102.0, 104.0, 106.0, 108.0],
        "High": [103.0, 105.0, 107.0, 109.0, 111.0],
        "Low": [99.0, 101.0, 103.0, 105.0, 107.0],
        "Close": [101.0, 103.0, 105.0, 107.0, 109.0],
        "Volume": [1000.0, 1000.0, 1000.0, 1000.0, 1000.0],
        "atr_14": [2.0, 2.0, 2.0, 2.0, 2.0],
        "regime_high_vol": [0, 0, 0, 0, 0],
    })
    # last_tradable_idx = 4 (bar 4, the final row)

    genes = np.array([0.55, 0.45, 5.0, 10.0, 0.10, 0.5, 15.0])

    # Case 1: Signal only triggers on bar 3 (N-2, penultimate bar).
    # Next day is bar 4 (last_tradable_idx). Under i < last_tradable_idx, entry MUST NOT trigger.
    p_up_late = np.array([0.40, 0.40, 0.40, 0.90, 0.90])
    det_late = get_detailed_simulation_results(df, p_up_late, genes, prefix_p_up=0.40)
    assert len(det_late["trade_log"]) == 0
    assert np.all(det_late["positions"] == 0.0)

    sh_late, _, ret_late, trades_late, _ = run_vectorized_simulation_fast(
        df["Open"].values, df["Close"].values, df["High"].values, df["Low"].values,
        p_up_late, df["atr_14"].values, df["regime_high_vol"].values, genes,
        prefix_p_up=0.40, volume=df["Volume"].values
    )
    assert trades_late == 0
    assert ret_late == pytest.approx(0.0)

    # Case 2: Signal triggers on bar 2 (N-3).
    # Keep p_up high so ML exit signal does not trigger on bar 4 Open.
    # Next day is bar 3 (i = 3 < 4), so entry triggers on bar 3 Open and holds to bar 4,
    # where it liquidates at bar 4 Close.
    p_up_early = np.array([0.40, 0.40, 0.90, 0.90, 0.90])
    det_early = get_detailed_simulation_results(df, p_up_early, genes, prefix_p_up=0.40)
    assert len(det_early["trade_log"]) == 1
    trade = det_early["trade_log"].iloc[0]
    entry_date = trade["entry_date"].strftime("%Y-%m-%d") if hasattr(trade["entry_date"], "strftime") else str(trade["entry_date"])[:10]
    exit_date = trade["exit_date"].strftime("%Y-%m-%d") if hasattr(trade["exit_date"], "strftime") else str(trade["exit_date"])[:10]
    assert entry_date == "2020-01-04"  # Bar 3
    assert exit_date == "2020-01-05"   # Bar 4 (final bar)
    assert trade["exit_reason"] == "Final Horizon Liquidation"

    sh_early, _, ret_early, trades_early, _ = run_vectorized_simulation_fast(
        df["Open"].values, df["Close"].values, df["High"].values, df["Low"].values,
        p_up_early, df["atr_14"].values, df["regime_high_vol"].values, genes,
        prefix_p_up=0.40, volume=df["Volume"].values
    )
    assert trades_early == 1






def test_repaired_v2_offline_fold_replays_versioned_fixture(monkeypatch, tmp_path):
    """Current code replays a separate repaired fixture, without changing archives."""
    import yfinance as yf
    from src.rolling_runner import RollingNSEExperimentRunner

    def forbidden_call(*args, **kwargs):
        raise AssertionError("Fixture replay must use immutable offline inputs")

    monkeypatch.setattr(yf, "Ticker", forbidden_call)
    monkeypatch.setattr(yf, "download", forbidden_call)
    fixture_path = PROJECT_ROOT / "reports/verification/repaired_tcs_2021_seed42.json"
    with fixture_path.open() as handle:
        fixture = json.load(handle)
    metadata = fixture["metadata"]
    assert metadata["engine_accounting_version"] == ENGINE_ACCOUNTING_VERSION == 2
    assert metadata["input_sha256"] == compute_sha256(INPUTS_DIR / "TCS.NS.parquet")
    assert metadata["protocol_sha256"] == compute_sha256(PROJECT_ROOT / "reports/experiments/protocol.json")
    assert metadata["model_seed"] == 42 and metadata["ga_seeds"] == [42]
    archive_path = PROJECT_ROOT / "reports/experiments/results/campaign_raw_results.json"
    archive_hash_before = compute_sha256(archive_path) if archive_path.exists() else None
    runner = RollingNSEExperimentRunner(
        inputs_dir=INPUTS_DIR, output_dir=tmp_path,
        protocol_path=PROJECT_ROOT / "reports/experiments/protocol.json",
        test_years=[2021], universe=["TCS.NS"], ga_seeds=[42], model_seed=42,
    )
    fold = runner.run_fold("TCS.NS", runner.load_processed_asset("TCS.NS"), 2021)
    actual, saved = fold["ga_runs"]["42"]["hybrid"], fixture["hybrid"]
    assert actual["is_feasible"] is saved["is_feasible"] is True
    np.testing.assert_allclose(actual["genes"], saved["genes"], atol=1e-12, rtol=1e-12)
    np.testing.assert_allclose(actual["equity"], saved["equity"], atol=1e-7, rtol=1e-7)
    for name in ("total_return", "max_drawdown", "sharpe_ratio", "capital_exposure"):
        assert actual["metrics"][name] == pytest.approx(saved["metrics"][name], rel=1e-9, abs=1e-12)
    if archive_hash_before is not None:
        assert compute_sha256(archive_path) == archive_hash_before


def test_archived_v1_campaign_blob_integrity():
    """Archived research evidence is separate from the repaired engine replay."""
    import hashlib
    archive = PROJECT_ROOT / "reports/experiments/results/campaign_raw_results.json"
    if not archive.exists():
        pytest.skip("Full archived v1 campaign JSON is absent from this partial checkout; remote Git blob preservation must be verified separately")
    raw = archive.read_bytes()
    assert len(raw) == 9020452
    git_object = b"blob " + str(len(raw)).encode() + b"\0" + raw
    assert hashlib.sha1(git_object).hexdigest() == "c6646b348649e5c3b145ef052f75944ee379ec5a"
