"""Regression coverage for causal equity, validated execution, and fee accounting."""
import numpy as np
import pandas as pd
import pytest

from src.backtest_engine import (
    ENGINE_ACCOUNTING_VERSION,
    apply_fitness_penalty,
    get_detailed_simulation_results,
    run_vectorized_simulation_fast,
)


GENES = np.array([0.70, 0.30, 200.0, 200.0, 1.0, 0.50, 100.0])


def _frame(open_prices, close=None, volume=None):
    open_prices = np.asarray(open_prices, dtype=float)
    close = open_prices.copy() if close is None else np.asarray(close, dtype=float)
    n = len(close)
    frame = pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=n),
        "Open": open_prices,
        "High": np.maximum(open_prices, close),
        "Low": np.minimum(open_prices, close),
        "Close": close,
        "atr_14": np.ones(n),
        "regime_high_vol": np.zeros(n),
    })
    if volume is not None:
        frame["Volume"] = volume
    return frame


def _fast(frame, probabilities, genes=GENES, **kwargs):
    volume = frame["Volume"].to_numpy() if "Volume" in frame else None
    return run_vectorized_simulation_fast(
        frame["Open"].to_numpy(), frame["Close"].to_numpy(),
        frame["High"].to_numpy(), frame["Low"].to_numpy(), probabilities,
        frame["atr_14"].to_numpy(), frame["regime_high_vol"].to_numpy(), genes,
        volume=volume, **kwargs,
    )


def _assert_parity(frame, probabilities, genes=GENES, **kwargs):
    detailed = get_detailed_simulation_results(frame, probabilities, genes, **kwargs)
    fast = _fast(frame, probabilities, genes, apply_penalty=False, **kwargs)
    metrics = tuple(detailed[name] for name in (
        "sharpe_ratio", "max_drawdown", "total_return", "total_trades", "turnover",
    ))
    np.testing.assert_allclose(fast, metrics, rtol=1e-10, atol=1e-10)
    if len(frame):
        assert detailed["max_drawdown"] == pytest.approx(-detailed["drawdowns"].min())
        initial = kwargs.get("initial_capital", 100000.0)
        assert detailed["trade_log"]["pnl"].sum() == pytest.approx(
            detailed["equity"][-1] - initial, abs=1e-8,
        )
    return detailed


def test_drawdown_series_uses_each_dates_peak_not_future_peak():
    frame = _frame([100, 100, 110, 105, 120, 115], [100, 110, 105, 120, 115, 130])
    result = _assert_parity(frame, np.full(6, 0.9), commission_pct=0, slippage_pct=0)
    equity = result["equity"]
    peaks = np.maximum.accumulate(np.r_[100000.0, equity])[1:]
    expected = (equity - peaks) / (peaks + 1e-8)
    np.testing.assert_allclose(result["drawdowns"], expected)
    np.testing.assert_allclose(result["drawdowns"][[0, 1, 3, 5]], 0)
    assert result["drawdowns"][2] < 0


def test_initial_capital_is_included_in_first_day_drawdown():
    frame = _frame([100, 90, 90], [90, 90, 90])
    result = _assert_parity(
        frame, np.full(3, 0.9), commission_pct=0, slippage_pct=0,
        prefix_p_up=0.9, prefix_atr=1,
    )
    assert result["drawdowns"][0] == pytest.approx(-0.095)
    assert result["max_drawdown"] == pytest.approx(0.095)


def test_entry_allocation_includes_exact_commission_and_net_pnl():
    frame = _frame([100, 100, 100])
    result = _assert_parity(
        frame, np.full(3, 0.9), commission_pct=0.1, slippage_pct=0,
        initial_capital=1000,
    )
    shares = 950.0 / (100.0 * 1.1)
    expected_terminal = 50.0 + shares * 100.0 * 0.9
    assert result["equity"][1] == pytest.approx(50.0 + shares * 100)
    assert result["equity"][-1] == pytest.approx(expected_terminal)
    assert result["trade_log"]["pnl"].sum() == pytest.approx(expected_terminal - 1000)


@pytest.mark.parametrize("engine", ["fast", "detailed"])
def test_executable_prefix_requires_prior_atr(engine):
    frame = _frame([100, 100, 100])
    with pytest.raises(ValueError, match="prefix_atr"):
        if engine == "fast":
            _fast(frame, np.full(3, 0.9), prefix_p_up=0.9)
        else:
            get_detailed_simulation_results(frame, np.full(3, 0.9), GENES, prefix_p_up=0.9)


def test_first_bar_stop_depends_only_on_prior_atr():
    genes = np.array([0.70, 0.30, 2.0, 4.0, 0.1, 0.5, 10.0])
    for current_atr in [0.001, 100.0]:
        frame = _frame([100, 100, 100])
        frame.loc[0, "Low"] = 95.0
        frame.loc[0, "atr_14"] = current_atr
        result = _assert_parity(
            frame, np.full(3, 0.1), genes, prefix_p_up=0.9,
            prefix_atr=1, commission_pct=0, slippage_pct=0,
        )
        assert result["trade_log"].iloc[0]["exit_price"] == 98.0
        assert result["trade_log"].iloc[0]["holding_bars"] == 0


def test_zero_prefix_atr_is_valid_and_not_replaced_with_current_atr():
    frame = _frame([100, 100, 100])
    result = _assert_parity(
        frame, np.full(3, 0.1), prefix_p_up=0.9, prefix_atr=0,
        commission_pct=0, slippage_pct=0,
    )
    assert result["trade_log"].iloc[0]["exit_price"] == 100.0
    assert result["trade_log"].iloc[0]["holding_bars"] == 0


def test_zero_volume_high_does_not_ratchet_trailing_stop():
    frame = _frame([100] * 5, volume=[1000, 1000, 0, 1000, 1000])
    frame.loc[2, ["High", "Low"]] = [1000.0, 1.0]
    genes = np.array([0.70, 0.30, 20.0, 200.0, 0.1, 0.5, 100.0])
    result = _assert_parity(frame, np.full(5, 0.9), genes, commission_pct=0, slippage_pct=0)
    assert len(result["trade_log"]) == 1
    assert result["trade_log"].iloc[0]["exit_reason"] == "Final Horizon Liquidation"
    assert result["trade_log"].iloc[0]["exit_date"] == frame["Date"].iloc[-1]


def test_benchmark_uses_open_entry_costs_and_tradable_terminal_close():
    frame = _frame([80, 100, 110, 999], [80, 105, 120, 999], volume=[0, 1000, 1000, 0])
    result = _assert_parity(
        frame, np.full(4, 0.1), commission_pct=0.01, slippage_pct=0.02,
        initial_capital=1000,
    )
    shares = 1000 / (100 * 1.02 * 1.01)
    terminal = shares * 120 * 0.98 * 0.99
    np.testing.assert_allclose(result["benchmark_equity"], [1000, shares * 105, terminal, terminal])
    assert result["benchmark_return"] == pytest.approx(terminal / 1000 - 1)


def test_benchmark_includes_cost_only_drawdown_from_initial_capital():
    frame = _frame([100, 100])
    result = _assert_parity(frame, np.full(2, 0.1), commission_pct=0.01, slippage_pct=0.01)
    assert result["benchmark_return"] < 0
    assert result["benchmark_max_drawdown"] == pytest.approx(-result["benchmark_drawdowns"].min())
    assert result["benchmark_drawdowns"][0] < 0
    assert result["benchmark_max_drawdown"] == pytest.approx(-result["benchmark_return"])


def test_all_zero_volume_is_cash_for_strategy_and_benchmark():
    frame = _frame([100, 200, 300], volume=[0, 0, 0])
    result = _assert_parity(frame, np.full(3, 0.9))
    np.testing.assert_array_equal(result["benchmark_equity"], [100000] * 3)
    assert result["benchmark_return"] == result["total_return"] == 0
    assert result["total_trades"] == 0


@pytest.mark.parametrize("n", [0, 1, 2, 3, 10, 50])
def test_short_horizons_and_empty_trade_schema(n):
    frame = _frame(np.full(n, 100.0))
    result = _assert_parity(frame, np.full(n, 0.1))
    assert result["total_trades"] == 0
    assert result["engine_accounting_version"] == ENGINE_ACCOUNTING_VERSION == 2
    assert result["initial_capital"] == 100000
    assert len(result["benchmark_drawdowns"]) == n
    assert "pnl" in result["trade_log"]
    if n:
        penalized = _fast(frame, np.full(n, 0.1), apply_penalty=True)
        assert penalized[0] == -2
        assert penalized[1] == 0.5


@pytest.mark.parametrize("column,value", [
    ("Open", 0.0), ("Close", -1.0), ("High", np.inf), ("Low", np.nan),
    ("atr_14", -1.0), ("regime_high_vol", 0.5), ("Volume", -1.0),
    ("Volume", np.nan),
])
def test_invalid_market_inputs_fail_in_both_engines(column, value):
    frame = _frame([100, 100, 100], volume=[1000, 1000, 1000])
    frame.loc[1, column] = value
    with pytest.raises(ValueError):
        _fast(frame, np.full(3, 0.9))
    with pytest.raises(ValueError):
        get_detailed_simulation_results(frame, np.full(3, 0.9), GENES)


@pytest.mark.parametrize("probabilities", [
    np.array([0.9, 0.9]), np.array([0.9, 0.9, np.nan]),
    np.array([0.9, 0.9, 1.1]), np.array([[0.9], [0.9], [0.9]]),
])
def test_invalid_signal_inputs_fail_before_simulation(probabilities):
    frame = _frame([100, 100, 100])
    with pytest.raises(ValueError):
        _fast(frame, probabilities)
    with pytest.raises(ValueError):
        get_detailed_simulation_results(frame, probabilities, GENES)


@pytest.mark.parametrize("option,value", [
    ("initial_capital", 0), ("initial_capital", np.inf),
    ("commission_pct", -0.01), ("commission_pct", 1),
    ("slippage_pct", np.nan), ("slippage_pct", 1),
    ("prefix_p_up", 1.1), ("prefix_atr", -2), ("prefix_regime_vol", 0.5),
])
def test_invalid_scalar_inputs_fail_in_both_engines(option, value):
    frame = _frame([100, 100, 100])
    kwargs = {option: value}
    with pytest.raises(ValueError):
        _fast(frame, np.full(3, 0.9), **kwargs)
    with pytest.raises(ValueError):
        get_detailed_simulation_results(frame, np.full(3, 0.9), GENES, **kwargs)


@pytest.mark.parametrize("genes", [
    GENES[:6], np.r_[GENES, 1], np.full(7, np.nan),
    np.array([0.7, 0.3, 2, 4, 0.1, 1.1, 20]),
    np.array([0.7, 0.3, 2, 4, 0.1, 1, 0]),
])
def test_invalid_chromosomes_fail_in_both_engines(genes):
    frame = _frame([100, 100, 100])
    with pytest.raises(ValueError):
        _fast(frame, np.full(3, 0.9), genes)
    with pytest.raises(ValueError):
        get_detailed_simulation_results(frame, np.full(3, 0.9), genes)


@pytest.mark.parametrize("bad_dates", [
    ["2024-01-01", "2024-01-03", "2024-01-02"],
    ["2024-01-01", "2024-01-01", "2024-01-02"],
    ["2024-01-01", None, "2024-01-03"],
])
def test_detailed_simulation_rejects_invalid_chronology(bad_dates):
    frame = _frame([100, 100, 100])
    frame["Date"] = bad_dates
    with pytest.raises(ValueError, match="Date"):
        get_detailed_simulation_results(frame, np.full(3, 0.9), GENES)


@pytest.mark.parametrize("seed", range(10))
def test_randomized_fast_detailed_parity_with_gaps_costs_and_zero_volume(seed):
    rng = np.random.default_rng(seed)
    n = 80
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.04, n)))
    opens = close * np.exp(rng.normal(0, 0.02, n))
    volume = rng.choice([0.0, 1000.0], n, p=[0.2, 0.8])
    frame = _frame(opens, close, volume)
    frame["High"] *= 1 + rng.uniform(0, 0.04, n)
    frame["Low"] *= 1 - rng.uniform(0, 0.04, n)
    frame["atr_14"] = rng.uniform(0.5, 3, n)
    frame["regime_high_vol"] = rng.integers(0, 2, n)
    genes = np.array([0.60, 0.40, 2.0, 3.5, 0.03, 0.5, 7.0])
    _assert_parity(
        frame, rng.uniform(0.1, 0.9, n), genes, commission_pct=0.001,
        slippage_pct=0.002, prefix_p_up=0.9, prefix_atr=2,
        prefix_regime_vol=seed % 2,
    )


def test_missing_prefix_regime_is_causal_normal_allocation():
    equities = []
    for first_regime in (0, 1):
        frame = _frame([100, 100, 100], [110, 100, 100])
        frame.loc[0, "regime_high_vol"] = first_regime
        result = _assert_parity(
            frame, np.full(3, 0.1), prefix_p_up=0.9, prefix_atr=1,
            commission_pct=0, slippage_pct=0,
        )
        equities.append(result["equity"][0])
    assert equities == pytest.approx([109500, 109500])


def test_explicit_high_vol_prefix_applies_discount_at_first_open():
    frame = _frame([100, 100, 100], [110, 100, 100])
    result = _assert_parity(
        frame, np.full(3, 0.1), prefix_p_up=0.9, prefix_atr=1,
        prefix_regime_vol=1, commission_pct=0, slippage_pct=0,
    )
    assert result["equity"][0] == pytest.approx(104750)


def test_new_stop_already_crossed_at_open_cannot_fill_above_entire_bar():
    frame = _frame([100, 100, 100])
    frame["atr_14"] = 0.1
    genes = np.array([0.7, 0.3, 1.0, 4.0, 0.1, 1.0, 20])
    result = _assert_parity(
        frame, np.array([0.9, 0.1, 0.1]), genes,
        commission_pct=0, slippage_pct=0.01,
    )
    trade = result["trade_log"].iloc[0]
    assert trade["entry_price"] == pytest.approx(101)
    assert trade["exit_price"] == pytest.approx(99)
    assert trade["holding_bars"] == 0


def test_fitness_penalty_is_separate_from_measured_metrics():
    assert apply_fitness_penalty(1.25, 0.08, 4) == pytest.approx((-0.75, 0.5))
    assert apply_fitness_penalty(1.25, 0.08, 5) == pytest.approx((1.25, 0.08))
    assert apply_fitness_penalty(1.25, 0.70, 4) == pytest.approx((-0.75, 0.70))
