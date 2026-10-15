"""
Unit Tests for Simulator Execution Timing, Bracket Conflicts, Gap Handling,
Entry-Day Brackets, Queued Signal Priority, Reentry Ineligibility,
Raw Reporting vs Optimization Penalties, and Fast/Detailed Consistency.
"""
import numpy as np
import pandas as pd
from src.backtest_engine import (
    run_vectorized_simulation_fast,
    get_detailed_simulation_results,
)


def _build_test_df(open_p, high_p, low_p, close_p, atr_val=1.0):
    n = len(close_p)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "Date": dates,
        "Open": np.array(open_p, dtype=np.float64),
        "High": np.array(high_p, dtype=np.float64),
        "Low": np.array(low_p, dtype=np.float64),
        "Close": np.array(close_p, dtype=np.float64),
        "atr_14": np.full(n, atr_val, dtype=np.float64),
        "regime_high_vol": np.zeros(n, dtype=np.int32),
    })


def test_next_bar_open_execution_timing():
    """
    Test that a signal triggered at bar 1 Close (p_up[1] >= p_entry)
    executes entry at bar 2 OPEN, not bar 1 Close.
    """
    n = 25
    open_p = np.full(n, 100.0)
    high_p = np.full(n, 101.0)
    low_p = np.full(n, 99.0)
    close_p = np.full(n, 100.0)

    # Set distinct Open on bar 2
    open_p[2] = 105.0

    p_up = np.full(n, 0.40)
    p_up[1] = 0.80  # Signal at bar 1

    atr = np.full(n, 2.0)
    regime_vol = np.zeros(n, dtype=np.int32)
    chromosome = np.array([0.70, 0.30, 2.0, 5.0, 0.05, 1.0, 10.0], dtype=np.float64)

    df = _build_test_df(open_p, high_p, low_p, close_p, atr_val=2.0)
    res = get_detailed_simulation_results(df, p_up, chromosome, slippage_pct=0.0, commission_pct=0.0)

    trades = res["trade_log"]
    assert not trades.empty, "Trade should have executed"
    first_trade = trades.iloc[0]
    assert first_trade["entry_price"] == 105.0, f"Expected entry at bar 2 open (105.0), got {first_trade['entry_price']}"


def test_review_defect_1_entry_day_stop_loss():
    """
    Codex Reproduction 1:
    25 bars: Open=Close=100, High=101, Low=99, ATR=2, regime=0, zero friction.
    Genes [0.7, 0.3, 2.0, 3.0, 0.06, 1.0, 20.0].
    p defaults 0.4; p[0]=0.8 enters on bar 1 (Open=100).
    Bar 1 Low=90: expected entry-day stop exit at 96.0 on bar 1.
    """
    n = 25
    open_p = np.full(n, 100.0)
    close_p = np.full(n, 100.0)
    high_p = np.full(n, 101.0)
    low_p = np.full(n, 99.0)
    low_p[1] = 90.0  # Entry day low touches 90 (below stop 96.0)

    p_up = np.full(n, 0.40)
    p_up[0] = 0.80  # Entry signal at bar 0 -> enters bar 1 Open=100.0

    chromosome = np.array([0.7, 0.3, 2.0, 3.0, 0.06, 1.0, 20.0], dtype=np.float64)
    df = _build_test_df(open_p, high_p, low_p, close_p, atr_val=2.0)
    res = get_detailed_simulation_results(df, p_up, chromosome, slippage_pct=0.0, commission_pct=0.0)

    trades = res["trade_log"]
    assert len(trades) >= 1, "Expected entry-day trade execution"
    first_trade = trades.iloc[0]
    assert first_trade["holding_bars"] == 0, f"Expected 0-bar holding on entry day, got {first_trade['holding_bars']}"
    assert first_trade["exit_price"] == 96.0, f"Expected stop loss at 96.0, got {first_trade['exit_price']}"
    assert "Stop" in first_trade["exit_reason"]


def test_review_defect_2_queued_market_exit_priority():
    """
    Codex Reproduction 2:
    p[0]=0.8 enters on bar 1 Open=100.
    At bar 1 Close: p[1]=0.1 triggers exit signal.
    Bar 2: Open=100, High=110 (touches target 106).
    Expected: queued market exit executes at bar 2 Open=100 BEFORE later high touches 106.
    """
    n = 25
    open_p = np.full(n, 100.0)
    close_p = np.full(n, 100.0)
    high_p = np.full(n, 101.0)
    low_p = np.full(n, 99.0)

    high_p[2] = 110.0  # Bar 2 High reaches target 106

    p_up = np.full(n, 0.40)
    p_up[0] = 0.80  # Enters bar 1 Open
    p_up[1] = 0.10  # Exit signal at bar 1 Close -> queues exit for bar 2 Open

    chromosome = np.array([0.7, 0.3, 2.0, 3.0, 0.06, 1.0, 20.0], dtype=np.float64)
    df = _build_test_df(open_p, high_p, low_p, close_p, atr_val=2.0)
    res = get_detailed_simulation_results(df, p_up, chromosome, slippage_pct=0.0, commission_pct=0.0)

    trades = res["trade_log"]
    assert len(trades) >= 1
    trade = trades.iloc[0]
    assert trade["exit_price"] == 100.0, f"Expected exit at bar 2 Open=100.0, got {trade['exit_price']}"
    assert "ML Exit" in trade["exit_reason"], f"Expected ML Exit Signal, got {trade['exit_reason']}"


def test_review_defect_3_no_intrabar_reentry_funding():
    """
    Codex Reproduction 3:
    p[0]=0.8 enters on bar 1 Open=100.
    Bar 1 Close: p[1]=0.8 (remains bullish, but already in position).
    Bar 2: Low=90 hits stop at 96 intrabar.
    Expected: No replacement entry funded at earlier bar 2 Open=100 using bar 2 intrabar exit proceeds.
    Only 1 trade occurs on bar 2 exit; position is flat at end of bar 2.
    """
    n = 25
    open_p = np.full(n, 100.0)
    close_p = np.full(n, 100.0)
    high_p = np.full(n, 101.0)
    low_p = np.full(n, 99.0)

    low_p[2] = 90.0  # Bar 2 low hits stop loss at 96

    p_up = np.full(n, 0.40)
    p_up[0] = 0.80  # Enters bar 1 Open
    p_up[1] = 0.80  # p_up remains high, but position was open at bar 1 close

    chromosome = np.array([0.7, 0.3, 2.0, 3.0, 0.06, 1.0, 20.0], dtype=np.float64)
    df = _build_test_df(open_p, high_p, low_p, close_p, atr_val=2.0)
    res = get_detailed_simulation_results(df, p_up, chromosome, slippage_pct=0.0, commission_pct=0.0)

    trades = res["trade_log"]
    # Only 1 trade should have executed (entry bar 1, exit bar 2 at stop 96.0)
    assert len(trades) == 1, f"Expected 1 trade, got {len(trades)} (spurious reentry occurred)"
    assert trades.iloc[0]["exit_price"] == 96.0
    assert res["positions"][2] == 0.0, "Position should be 0.0 at bar 2 Close"


def test_entry_day_target_and_conflict():
    """
    Test entry day target and ambiguous conflict:
    If bar 1 Low=90 and High=110 on entry day, conservative policy prioritizes stop at 96.0.
    """
    n = 25
    open_p = np.full(n, 100.0)
    close_p = np.full(n, 100.0)
    high_p = np.full(n, 101.0)
    low_p = np.full(n, 99.0)

    # Bar 1 entry day touches BOTH brackets
    high_p[1] = 110.0
    low_p[1] = 90.0

    p_up = np.full(n, 0.40)
    p_up[0] = 0.80  # Enters bar 1 Open=100.0

    chromosome = np.array([0.7, 0.3, 2.0, 3.0, 0.06, 1.0, 20.0], dtype=np.float64)
    df = _build_test_df(open_p, high_p, low_p, close_p, atr_val=2.0)
    res = get_detailed_simulation_results(df, p_up, chromosome, slippage_pct=0.0, commission_pct=0.0)

    trades = res["trade_log"]
    assert len(trades) >= 1
    assert trades.iloc[0]["exit_price"] == 96.0, f"Expected conservative stop exit at 96.0, got {trades.iloc[0]['exit_price']}"


def test_net_pnl_sums_to_portfolio_change():
    """
    Verifies that sum of net trade P&L exactly matches total portfolio equity change
    after final liquidation.
    """
    n = 50
    np.random.seed(42)
    ret = np.random.normal(0.0005, 0.015, n)
    close = 100.0 * np.exp(np.cumsum(ret))
    open_p = (close + np.roll(close, 1)) / 2.0
    open_p[0] = 100.0
    high = np.maximum(open_p, close) * 1.01
    low = np.minimum(open_p, close) * 0.99
    p_up = np.random.uniform(0.3, 0.8, n)

    df = pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=n, freq="D"),
        "Open": open_p,
        "High": high,
        "Low": low,
        "Close": close,
        "atr_14": close * 0.02,
        "regime_high_vol": np.zeros(n, dtype=np.int32),
    })

    chromosome = np.array([0.60, 0.40, 2.0, 4.0, 0.03, 0.8, 15.0], dtype=np.float64)
    res = get_detailed_simulation_results(df, p_up, chromosome, commission_pct=0.0005, slippage_pct=0.0005)

    initial_capital = 100000.0
    final_equity = res["equity"][-1]
    expected_delta = final_equity - initial_capital

    trades = res["trade_log"]
    total_pnl = float(trades["pnl"].sum()) if not trades.empty else 0.0

    np.testing.assert_allclose(total_pnl, expected_delta, rtol=1e-5, atol=1e-5)


def test_n_less_than_20_contract():
    """
    Verifies that when n < 20, the simulator computes honest raw metrics on available bars
    rather than returning sentinel losses (-10.0, 1.0, -1.0).
    """
    n = 10
    close = np.full(n, 100.0)
    open_p = np.full(n, 100.0)
    high = np.full(n, 101.0)
    low = np.full(n, 99.0)
    p_up = np.full(n, 0.5)
    atr = np.full(n, 2.0)
    regime_vol = np.zeros(n, dtype=np.int32)
    chromosome = np.array([0.7, 0.3, 2.0, 3.0, 0.06, 1.0, 20.0], dtype=np.float64)

    # Without penalty
    sh, mdd, ret, trades, to = run_vectorized_simulation_fast(
        open_p, close, high, low, p_up, atr, regime_vol, chromosome, apply_penalty=False
    )
    np.testing.assert_allclose(sh, 0.0, atol=1e-7)
    np.testing.assert_allclose(mdd, 0.0, atol=1e-7)
    np.testing.assert_allclose(ret, 0.0, atol=1e-7)
    assert trades == 0


def test_fast_and_detailed_simulators_agree_comprehensive():
    """
    Verifies that fast Numba simulator and detailed simulation produce identical results.
    """
    n = 200
    np.random.seed(123)
    ret = np.random.normal(0.0005, 0.015, n)
    close = 100.0 * np.exp(np.cumsum(ret))
    high = close * (1.0 + np.abs(np.random.normal(0, 0.005, n)))
    low = close * (1.0 - np.abs(np.random.normal(0, 0.005, n)))
    open_p = (close + np.roll(close, 1)) / 2.0
    open_p[0] = 100.0
    p_up = np.random.uniform(0.35, 0.85, n)
    atr = close * 0.018
    regime_vol = np.random.choice([0, 1], n)
    chromosome = np.array([0.60, 0.40, 1.8, 3.5, 0.03, 0.8, 15.0], dtype=np.float64)

    sh_f, dd_f, ret_f, trades_f, to_f = run_vectorized_simulation_fast(
        open_p, close, high, low, p_up, atr, regime_vol, chromosome, apply_penalty=False
    )

    df = pd.DataFrame({
        "Date": pd.date_range("2023-01-01", periods=n, freq="D"),
        "Open": open_p,
        "High": high,
        "Low": low,
        "Close": close,
        "atr_14": atr,
        "regime_high_vol": regime_vol,
    })
    res = get_detailed_simulation_results(df, p_up, chromosome)

    np.testing.assert_allclose(res["sharpe_ratio"], sh_f, rtol=1e-5, atol=1e-5)
    np.testing.assert_allclose(res["max_drawdown"], dd_f, rtol=1e-5, atol=1e-5)
    np.testing.assert_allclose(res["total_return"], ret_f, rtol=1e-5, atol=1e-5)
    assert res["total_trades"] == trades_f
