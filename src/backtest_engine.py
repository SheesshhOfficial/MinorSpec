"""
Execution Timing, Bracket Resolution, and Simulation Helpers.

Policy:
1. Signal Timing & Queuing:
   - At bar t-1 Close, signal evaluation checks if an entry or exit should be queued for bar t Open.
   - Entry order queued for bar t Open if and only if position was 0.0 at bar t-1 Close AND p_up[t-1] >= p_entry.
   - Exit order queued for bar t Open if and only if position > 0.0 at bar t-1 Close AND (p_up[t-1] < p_exit OR held_bars >= max_hold).
2. Bar t Execution Phasing:
   - Phase 2A: Queued Exit Execution at bar t Open.
     If an exit was queued from bar t-1 Close, it executes strictly at bar t Open * (1 - slippage), paying commission.
     This executes BEFORE any intrabar price movement on bar t.
   - Phase 2B: Opening Gaps for Existing Positions.
     If position > 0 (not queued for exit), check opening gap:
     - gap down below stop: curr_open <= stop_price -> exits at curr_open * (1 - slippage).
     - gap up above target: curr_open >= target_price -> exits at curr_open * (1 - slippage).
     - gap conflict (both touched): conservative policy exits at stop: curr_open * (1 - slippage).
   - Phase 2C: Queued Entry Execution at bar t Open.
     If an entry was queued from bar t-1 Close (and position is 0), it executes at bar t Open * (1 + slippage).
     Brackets (Stop Loss & Take Profit) are ACTIVATED IMMEDIATELY based on bar t-1 ATR and entry execution price.
     Initial highest_price is set to max(entry_price, curr_open).
   - Phase 2D: Intrabar Price Action & Bracket Evaluation.
     If position > 0 (whether entered on earlier bars or entered at bar t Open):
     - Check intrabar touches against stop and target.
     - Ambiguous conflict (low <= stop AND high >= target):
       Conservative policy assumes STOP LOSS was hit first -> exits at stop_price * (1 - slippage).
     - Stop touched (low <= stop): exits at stop_price * (1 - slippage).
     - Target touched (high >= target): exits at target_price * (1 - slippage).
   - Phase 2E: Bar t Close Maintenance.
     If position is still held at bar t Close:
     - highest_price = max(highest_price, curr_high).
     - trail_stop = highest_price * (1.0 - trailing_pct).
     - if trail_stop > stop_price: stop_price = trail_stop.
     - Position marks to market at curr_close.
   - Phase 2F: Final Horizon Liquidation.
     On the last bar (i == n-1), if position > 0, liquidated at bar n-1 Close * (1 - slippage).
3. Non-Funding of Reentry:
   - An intrabar exit on bar t can NEVER fund an entry at bar t Open, because entry orders were strictly queued at bar t-1 Close.
4. Input Contract:
   - If n == 0, returns (0.0, 0.0, 0.0, 0, 0.0).
   - If n < 20, computes actual exact returns, Sharpe, drawdown, trades on the available bars without arbitrary sentinel losses.
5. Detailed Simulation:
   - Computes its own equity curve and trade logs independently.
   - Sharpe, drawdown, return, trades, and turnover are computed from its own equity and trade history, matching fast results.
"""
from typing import Tuple, Dict, Optional
import numpy as np
import pandas as pd
import numba

from src.config import DEFAULT_COMMISSION_PCT, DEFAULT_SLIPPAGE_PCT, INITIAL_CAPITAL


@numba.njit(fastmath=True)
def run_vectorized_simulation_fast(
    open_prices: np.ndarray,
    close: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    p_up: np.ndarray,
    atr: np.ndarray,
    regime_vol: np.ndarray,
    chromosome: np.ndarray,
    commission_pct: float = DEFAULT_COMMISSION_PCT,
    slippage_pct: float = DEFAULT_SLIPPAGE_PCT,
    initial_capital: float = INITIAL_CAPITAL,
    apply_penalty: bool = True,
    volume: Optional[np.ndarray] = None,
    prefix_p_up: float = -1.0,
    prefix_atr: float = -1.0,
    prefix_regime_vol: int = -1,
) -> Tuple[float, float, float, int, float]:
    """
    High-speed Numba simulation of trading rules dictated by chromosome genes.
    Timing: Decisions at bar t-1 Close execute on bar t Open.
    Intrabar policy: Conservative (Stop prioritized over Target when both touched).
    Returns: (sharpe_ratio, max_drawdown, total_return, total_trades, turnover)
    """
    n = len(close)
    if n == 0:
        return 0.0, 0.0, 0.0, 0, 0.0

    p_entry = chromosome[0]
    p_exit = chromosome[1]
    sl_mult = chromosome[2]
    tp_mult = chromosome[3]
    trailing_pct = chromosome[4]
    vol_discount = chromosome[5]
    max_hold = int(chromosome[6])

    cash = initial_capital
    position = 0.0
    entry_price = 0.0
    highest_price = 0.0
    entry_bar = 0
    stop_price = 0.0
    target_price = 0.0
    total_trades = 0

    # Identify last tradable bar for deterministic scheduled fold-end liquidation
    last_tradable_idx = -1
    for k in range(n - 1, -1, -1):
        if volume is None or volume[k] > 0.0:
            last_tradable_idx = k
            break

    equity_curve = np.empty(n, dtype=np.float64)

    for i in range(n):
        curr_open = open_prices[i]
        curr_high = high[i]
        curr_low = low[i]
        curr_close = close[i]
        has_volume = volume is None or volume[i] > 0.0

        # Phase 1: Determine queued actions from bar i-1 Close
        queue_entry = False
        queue_exit = False
        if i == 0:
            if prefix_p_up >= 0.0:
                if position == 0.0 and prefix_p_up >= p_entry:
                    queue_entry = True
        else:
            prev_p = p_up[i - 1]
            if position == 0.0:
                if prev_p >= p_entry:
                    queue_entry = True
            else:
                prev_held = (i - 1) - entry_bar
                if prev_p < p_exit or prev_held >= max_hold:
                    queue_exit = True

        # Phase 2A: Execute queued signal/timeout exit at bar i Open
        if position > 0.0 and queue_exit and has_volume:
            exec_price = curr_open * (1.0 - slippage_pct)
            proceeds = position * exec_price * (1.0 - commission_pct)
            cash += proceeds
            position = 0.0
            total_trades += 1

        # Phase 2B: Opening Gap Exit for existing positions
        if position > 0.0 and has_volume:
            gap_stop = curr_open <= stop_price
            gap_target = curr_open >= target_price
            if gap_stop and gap_target:
                # Extreme gap: Conservative policy triggers Stop Loss
                exec_price = curr_open * (1.0 - slippage_pct)
                proceeds = position * exec_price * (1.0 - commission_pct)
                cash += proceeds
                position = 0.0
                total_trades += 1
            elif gap_stop:
                exec_price = curr_open * (1.0 - slippage_pct)
                proceeds = position * exec_price * (1.0 - commission_pct)
                cash += proceeds
                position = 0.0
                total_trades += 1
            elif gap_target:
                exec_price = curr_open * (1.0 - slippage_pct)
                proceeds = position * exec_price * (1.0 - commission_pct)
                cash += proceeds
                position = 0.0
                total_trades += 1

        # Phase 2C: Execute queued entry at bar i Open
        if position == 0.0 and queue_entry and (last_tradable_idx == -1 or i < last_tradable_idx) and has_volume:
            if i == 0 and prefix_regime_vol >= 0:
                is_high_vol = prefix_regime_vol == 1
            elif i > 0:
                is_high_vol = regime_vol[i - 1] == 1
            else:
                is_high_vol = False
            alloc_fraction = 0.95 * (vol_discount if is_high_vol else 1.0)
            alloc_cash = cash * alloc_fraction

            exec_price = curr_open * (1.0 + slippage_pct)
            shares = (alloc_cash * (1.0 - commission_pct)) / exec_price

            if shares > 0.0001:
                cost = shares * exec_price * (1.0 + commission_pct)
                cash -= cost
                position = shares
                entry_price = exec_price
                highest_price = max(exec_price, curr_open)
                entry_bar = i

                if i == 0 and prefix_atr > 0.0:
                    prev_atr = prefix_atr
                elif i > 0:
                    prev_atr = atr[i - 1]
                else:
                    prev_atr = atr[0]
                stop_price = entry_price - (sl_mult * prev_atr)
                target_price = entry_price + (tp_mult * prev_atr)

        # Phase 2D: Intrabar range touch (evaluates existing AND newly entered position on bar i)
        if position > 0.0 and has_volume:
            touch_stop = curr_low <= stop_price
            touch_target = curr_high >= target_price

            if touch_stop and touch_target:
                # Ambiguous bracket touch on same bar: Conservative policy assumes STOP touched first
                exec_price = stop_price * (1.0 - slippage_pct)
                proceeds = position * exec_price * (1.0 - commission_pct)
                cash += proceeds
                position = 0.0
                total_trades += 1
            elif touch_stop:
                exec_price = stop_price * (1.0 - slippage_pct)
                proceeds = position * exec_price * (1.0 - commission_pct)
                cash += proceeds
                position = 0.0
                total_trades += 1
            elif touch_target:
                exec_price = target_price * (1.0 - slippage_pct)
                proceeds = position * exec_price * (1.0 - commission_pct)
                cash += proceeds
                position = 0.0
                total_trades += 1

        # Phase 2E: Bar Close Maintenance
        if position > 0.0:
            highest_price = max(highest_price, curr_high)
            trail_stop = highest_price * (1.0 - trailing_pct)
            if trail_stop > stop_price:
                stop_price = trail_stop

        # Phase 2F: Final Horizon Liquidation at last tradable session
        if i == last_tradable_idx and position > 0.0 and has_volume:
            final_exit_price = curr_close * (1.0 - slippage_pct)
            proceeds = position * final_exit_price * (1.0 - commission_pct)
            cash += proceeds
            position = 0.0
            total_trades += 1

        # Mark-to-market equity
        equity_curve[i] = cash + (position * curr_close)

    # Compute Performance Metrics
    total_return = (equity_curve[-1] / initial_capital) - 1.0

    if n <= 1:
        return 0.0, 0.0, total_return, total_trades, 0.0

    # Include first-day return from pre-trade initial capital to bar 0 Close
    daily_returns = np.empty(n, dtype=np.float64)
    daily_returns[0] = (equity_curve[0] - initial_capital) / (initial_capital + 1e-8)
    for j in range(1, n):
        prev = equity_curve[j - 1]
        curr = equity_curve[j]
        daily_returns[j] = (curr - prev) / (prev + 1e-8)

    mean_ret = np.mean(daily_returns)
    std_ret = np.std(daily_returns)
    if std_ret < 1e-8:
        sharpe = 0.0
    else:
        sharpe = (mean_ret / std_ret) * np.sqrt(252.0)

    # Include initial capital in peak tracking
    peak = initial_capital
    max_dd = 0.0
    for k in range(n):
        if equity_curve[k] > peak:
            peak = equity_curve[k]
        dd = (peak - equity_curve[k]) / (peak + 1e-8)
        if dd > max_dd:
            max_dd = dd

    turnover = float(total_trades) / (float(n) / 252.0)

    if apply_penalty and total_trades < 5:
        sharpe -= 2.0
        max_dd = max(max_dd, 0.5)

    return sharpe, max_dd, total_return, total_trades, turnover


def get_detailed_simulation_results(
    df: pd.DataFrame,
    p_up: np.ndarray,
    chromosome: np.ndarray,
    commission_pct: float = DEFAULT_COMMISSION_PCT,
    slippage_pct: float = DEFAULT_SLIPPAGE_PCT,
    initial_capital: float = INITIAL_CAPITAL,
    prefix_p_up: float = -1.0,
    prefix_atr: float = -1.0,
    prefix_regime_vol: int = -1,
) -> Dict:
    """
    Executes full tracking run with trade log, equity curve, and raw performance metrics.
    Independently derives metrics from trade logs and equity curve.
    """
    open_prices = df["Open"].to_numpy(dtype=np.float64)
    close = df["Close"].to_numpy(dtype=np.float64)
    high = df["High"].to_numpy(dtype=np.float64)
    low = df["Low"].to_numpy(dtype=np.float64)
    atr = df["atr_14"].to_numpy(dtype=np.float64)
    regime_vol = df["regime_high_vol"].to_numpy(dtype=np.int32)
    dates = df["Date"].values
    volumes = df["Volume"].to_numpy(dtype=np.float64) if "Volume" in df.columns else None

    n = len(close)
    if n == 0:
        return {
            "dates": np.array([]),
            "equity": np.array([]),
            "drawdowns": np.array([]),
            "positions": np.array([]),
            "capital_exposures": np.array([]),
            "benchmark_equity": np.array([]),
            "benchmark_max_drawdown": 0.0,
            "trade_log": pd.DataFrame(),
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "total_return": 0.0,
            "benchmark_return": 0.0,
            "total_trades": 0,
            "win_rate": 0.0,
            "turnover": 0.0,
            "capital_exposure": 0.0,
            "time_in_market": 0.0,
        }

    p_entry = chromosome[0]
    p_exit = chromosome[1]
    sl_mult = chromosome[2]
    tp_mult = chromosome[3]
    trailing_pct = chromosome[4]
    vol_discount = chromosome[5]
    max_hold = int(chromosome[6])

    cash = initial_capital
    position = 0.0
    entry_price = 0.0
    highest_price = 0.0
    entry_bar = 0
    stop_price = 0.0
    target_price = 0.0

    # Identify last tradable bar for deterministic scheduled fold-end liquidation
    last_tradable_idx = -1
    for k in range(n - 1, -1, -1):
        if volumes is None or volumes[k] > 0.0:
            last_tradable_idx = k
            break

    equity = np.empty(n, dtype=np.float64)
    positions_series = np.zeros(n, dtype=np.float64)
    capital_exposures = np.zeros(n, dtype=np.float64)
    trade_log = []

    for i in range(n):
        curr_open = open_prices[i]
        curr_high = high[i]
        curr_low = low[i]
        curr_close = close[i]
        has_volume = volumes is None or volumes[i] > 0.0

        # Phase 1: Determine queued actions from bar i-1 Close
        queue_entry = False
        queue_exit = False
        if i == 0:
            if prefix_p_up >= 0.0:
                if position == 0.0 and prefix_p_up >= p_entry:
                    queue_entry = True
        else:
            prev_p = p_up[i - 1]
            if position == 0.0:
                if prev_p >= p_entry:
                    queue_entry = True
            else:
                prev_held = (i - 1) - entry_bar
                if prev_p < p_exit or prev_held >= max_hold:
                    queue_exit = True

        # Phase 2A: Queued Exit at Open
        if position > 0.0 and queue_exit and has_volume:
            exec_price = curr_open * (1.0 - slippage_pct)
            proceeds = position * exec_price * (1.0 - commission_pct)
            entry_cost = position * entry_price * (1.0 + commission_pct)
            pnl = proceeds - entry_cost
            pnl_pct = (proceeds / entry_cost) - 1.0
            cash += proceeds

            trade_log.append({
                "entry_date": dates[entry_bar],
                "exit_date": dates[i],
                "entry_price": entry_price,
                "exit_price": exec_price,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "holding_bars": i - entry_bar,
                "exit_reason": "ML Exit Signal / Timeout",
            })
            position = 0.0

        # Phase 2B: Opening Gaps
        if position > 0.0 and has_volume:
            gap_stop = curr_open <= stop_price
            gap_target = curr_open >= target_price
            exit_trade = False
            exec_price = curr_open * (1.0 - slippage_pct)
            exit_reason = ""

            if gap_stop and gap_target:
                exit_trade = True
                exit_reason = "Gap Conflict (Prioritized Stop)"
            elif gap_stop:
                exit_trade = True
                exit_reason = "Gap Down Stop Loss"
            elif gap_target:
                exit_trade = True
                exit_reason = "Gap Up Take Profit"

            if exit_trade:
                proceeds = position * exec_price * (1.0 - commission_pct)
                entry_cost = position * entry_price * (1.0 + commission_pct)
                pnl = proceeds - entry_cost
                pnl_pct = (proceeds / entry_cost) - 1.0
                cash += proceeds

                trade_log.append({
                    "entry_date": dates[entry_bar],
                    "exit_date": dates[i],
                    "entry_price": entry_price,
                    "exit_price": exec_price,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "holding_bars": i - entry_bar,
                    "exit_reason": exit_reason,
                })
                position = 0.0

        # Phase 2C: Queued Entry at Open
        if position == 0.0 and queue_entry and (last_tradable_idx == -1 or i < last_tradable_idx) and has_volume:
            if i == 0 and prefix_regime_vol >= 0:
                is_high_vol = prefix_regime_vol == 1
            elif i > 0:
                is_high_vol = regime_vol[i - 1] == 1
            else:
                is_high_vol = False
            alloc_fraction = 0.95 * (vol_discount if is_high_vol else 1.0)
            alloc_cash = cash * alloc_fraction

            exec_price = curr_open * (1.0 + slippage_pct)
            shares = (alloc_cash * (1.0 - commission_pct)) / exec_price

            if shares > 0.0001:
                cost = shares * exec_price * (1.0 + commission_pct)
                cash -= cost
                position = shares
                entry_price = exec_price
                highest_price = max(exec_price, curr_open)
                entry_bar = i

                if i == 0 and prefix_atr > 0.0:
                    prev_atr = prefix_atr
                elif i > 0:
                    prev_atr = atr[i - 1]
                else:
                    prev_atr = atr[0]
                stop_price = entry_price - (sl_mult * prev_atr)
                target_price = entry_price + (tp_mult * prev_atr)

        # Phase 2D: Intrabar Range Touch (evaluated for existing AND new positions)
        if position > 0.0 and has_volume:
            touch_stop = curr_low <= stop_price
            touch_target = curr_high >= target_price
            exit_trade = False
            exec_price = curr_close
            exit_reason = ""

            if touch_stop and touch_target:
                exit_trade = True
                exec_price = stop_price * (1.0 - slippage_pct)
                exit_reason = "Bracket Conflict (Prioritized Stop)"
            elif touch_stop:
                exit_trade = True
                exec_price = stop_price * (1.0 - slippage_pct)
                exit_reason = "Stop Loss / Trailing Stop"
            elif touch_target:
                exit_trade = True
                exec_price = target_price * (1.0 - slippage_pct)
                exit_reason = "Take Profit (ATR Target)"

            if exit_trade:
                proceeds = position * exec_price * (1.0 - commission_pct)
                entry_cost = position * entry_price * (1.0 + commission_pct)
                pnl = proceeds - entry_cost
                pnl_pct = (proceeds / entry_cost) - 1.0
                cash += proceeds

                trade_log.append({
                    "entry_date": dates[entry_bar],
                    "exit_date": dates[i],
                    "entry_price": entry_price,
                    "exit_price": exec_price,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "holding_bars": i - entry_bar,
                    "exit_reason": exit_reason,
                })
                position = 0.0

        # Phase 2E: Bar Close Maintenance
        if position > 0.0:
            highest_price = max(highest_price, curr_high)
            trail_stop = highest_price * (1.0 - trailing_pct)
            if trail_stop > stop_price:
                stop_price = trail_stop

        # Phase 2F: Final Bar Liquidation at last tradable session
        if i == last_tradable_idx and position > 0.0 and has_volume:
            final_exit_price = curr_close * (1.0 - slippage_pct)
            proceeds = position * final_exit_price * (1.0 - commission_pct)
            entry_cost = position * entry_price * (1.0 + commission_pct)
            pnl = proceeds - entry_cost
            pnl_pct = (proceeds / entry_cost) - 1.0
            cash += proceeds

            trade_log.append({
                "entry_date": dates[entry_bar],
                "exit_date": dates[i],
                "entry_price": entry_price,
                "exit_price": final_exit_price,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "holding_bars": i - entry_bar,
                "exit_reason": "Final Horizon Liquidation",
            })
            position = 0.0

        equity[i] = cash + (position * curr_close)
        positions_series[i] = 1.0 if position > 0.0 else 0.0
        capital_exposures[i] = (position * curr_close) / (equity[i] + 1e-8)

    # Compute Benchmark Buy-and-Hold
    benchmark_equity = initial_capital * (close / close[0])
    b_peak = np.maximum.accumulate(close)
    benchmark_mdd = float(np.max((b_peak - close) / (b_peak + 1e-8)))

    # Compute Detailed Metrics independently
    running_max = initial_capital
    max_dd = 0.0
    for k in range(n):
        if equity[k] > running_max:
            running_max = equity[k]
        dd = (running_max - equity[k]) / (running_max + 1e-8)
        if dd > max_dd:
            max_dd = dd

    drawdowns = (equity - running_max) / (running_max + 1e-8)
    total_ret = float((equity[-1] / initial_capital) - 1.0)

    if n > 0:
        daily_returns = np.empty(n, dtype=np.float64)
        daily_returns[0] = (equity[0] - initial_capital) / (initial_capital + 1e-8)
        for j in range(1, n):
            daily_returns[j] = (equity[j] - equity[j - 1]) / (equity[j - 1] + 1e-8)
        mean_ret = float(np.mean(daily_returns))
        std_ret = float(np.std(daily_returns))
        sharpe = float((mean_ret / std_ret) * np.sqrt(252.0)) if std_ret >= 1e-8 else 0.0
    else:
        sharpe = 0.0

    trades_df = pd.DataFrame(trade_log)
    total_trades = len(trades_df)
    win_rate = float((trades_df["pnl"] > 0).mean()) if total_trades > 0 else 0.0
    turnover = float(total_trades) / (float(n) / 252.0)
    time_in_market = float(np.mean(positions_series > 0.0))
    capital_exposure = float(np.mean(capital_exposures))

    return {
        "dates": dates,
        "equity": equity,
        "drawdowns": drawdowns,
        "positions": positions_series,
        "capital_exposures": capital_exposures,
        "benchmark_equity": benchmark_equity,
        "benchmark_max_drawdown": benchmark_mdd,
        "trade_log": trades_df,
        "sharpe_ratio": sharpe,
        "max_drawdown": float(max_dd),
        "total_return": total_ret,
        "benchmark_return": float((benchmark_equity[-1] / initial_capital) - 1.0),
        "total_trades": total_trades,
        "win_rate": win_rate,
        "turnover": turnover,
        "time_in_market": time_in_market,
        "capital_exposure": capital_exposure,
    }
