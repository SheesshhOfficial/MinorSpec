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
       Conservative policy assumes STOP LOSS was hit first -> exits at min(stop_price, curr_open) * (1 - slippage).
     - Stop touched (low <= stop): exits at min(stop_price, curr_open) * (1 - slippage).
       For a new position whose slipped entry puts the stop above the raw Open,
       the already-crossed stop executes from the opening quote, not an untraded higher price.
     - Target touched (high >= target): exits at target_price * (1 - slippage).
   - Phase 2E: Bar t Close Maintenance.
     If position is still held at bar t Close:
     - highest_price = max(highest_price, curr_high).
     - trail_stop = highest_price * (1.0 - trailing_pct).
     - if trail_stop > stop_price: stop_price = trail_stop.
     - Trailing stops update only on positive-volume bars; position still marks to market at curr_close.
   - Phase 2F: Final Horizon Liquidation.
     On the last positive-volume bar, liquidate at Close * (1 - slippage).
     This is the scheduled retrospective fold-end convention; no final-session entries.
3. Non-Funding of Reentry:
   - An intrabar exit on bar t can NEVER fund an entry at bar t Open, because entry orders were strictly queued at bar t-1 Close.
4. Input Contract:
   - Invalid shapes, nonfinite values, nonpositive prices, or invalid parameter ranges raise ValueError.
   - If n == 0, valid inputs return (0.0, 0.0, 0.0, 0, 0.0).
   - An executable first-bar prefix signal requires the preceding bar ATR.
     Missing prefix regime defaults to normal allocation without reading current-bar regime.
   - If n < 20, computes actual exact returns, Sharpe, drawdown, trades on the available bars without arbitrary sentinel losses.
5. Detailed Simulation:
   - Computes its own equity curve and trade logs independently.
   - Sharpe, drawdown, return, trades, and turnover are computed from its own equity and trade history, matching fast raw results.
   - Entry sizing reserves commission exactly within the cash allocation.
   - Benchmark buy-and-hold uses first tradable Open, last tradable Close, and the same costs.
   - Positions/exposure are measured at each Close; turnover means annualized completed round trips.
"""
from typing import Tuple, Dict, Optional
import numpy as np
import pandas as pd
import numba

from src.config import DEFAULT_COMMISSION_PCT, DEFAULT_SLIPPAGE_PCT, INITIAL_CAPITAL


ENGINE_ACCOUNTING_VERSION = 2


@numba.njit
def apply_fitness_penalty(sharpe: float, max_drawdown: float, total_trades: int):
    """Return optimizer objectives without relabeling them as measured risk metrics."""
    if total_trades < 5:
        return sharpe - 2.0, max(max_drawdown, 0.5)
    return sharpe, max_drawdown


_TRADE_COLUMNS = [
    "entry_date", "exit_date", "entry_price", "exit_price", "pnl", "pnl_pct",
    "holding_bars", "exit_reason",
]


def _validate_simulation_inputs(
    open_prices, close, high, low, p_up, atr, regime_vol, chromosome,
    commission_pct, slippage_pct, initial_capital, volume,
    prefix_p_up, prefix_atr, prefix_regime_vol,
):
    """Validate once at the public boundary, before unchecked compiled indexing."""
    arrays = []
    for name, value in (
        ("open_prices", open_prices), ("close", close), ("high", high),
        ("low", low), ("p_up", p_up), ("atr", atr),
        ("regime_vol", regime_vol), ("chromosome", chromosome),
    ):
        array = np.asarray(value, dtype=np.float64)
        if array.ndim != 1 or not np.all(np.isfinite(array)):
            raise ValueError(f"{name} must be a finite one-dimensional array")
        arrays.append(np.ascontiguousarray(array))
    open_prices, close, high, low, p_up, atr, regime_vol, chromosome = arrays
    n = len(close)
    if any(len(array) != n for array in arrays[:7]):
        raise ValueError("All market and signal arrays must have the same length")
    if len(chromosome) != 7:
        raise ValueError("chromosome must contain exactly seven genes")
    if any(np.any(array <= 0.0) for array in arrays[:4]):
        raise ValueError("OHLC prices must be strictly positive")
    if np.any(high < low):
        raise ValueError("high prices must be at least low prices")
    if np.any((p_up < 0.0) | (p_up > 1.0)):
        raise ValueError("p_up probabilities must be between zero and one")
    if np.any(atr < 0.0):
        raise ValueError("atr must be nonnegative")
    if np.any((regime_vol != 0.0) & (regime_vol != 1.0)):
        raise ValueError("regime_vol must contain only zero or one")
    if (np.any(chromosome[:2] < 0.0) or np.any(chromosome[:2] > 1.0)
            or np.any(chromosome[2:4] <= 0.0)
            or np.any(chromosome[4:6] < 0.0) or np.any(chromosome[4:6] > 1.0)
            or not 1.0 <= chromosome[6] <= 2147483647.0):
        raise ValueError("chromosome contains invalid threshold, risk, allocation, or holding-period genes")
    for name, value in (("commission_pct", commission_pct), ("slippage_pct", slippage_pct)):
        if not np.isfinite(value) or not 0.0 <= value < 1.0:
            raise ValueError(f"{name} must be finite and in [0, 1)")
    if not np.isfinite(initial_capital) or initial_capital <= 0.0:
        raise ValueError("initial_capital must be finite and strictly positive")
    if not np.isfinite(prefix_p_up) or not (prefix_p_up == -1.0 or 0.0 <= prefix_p_up <= 1.0):
        raise ValueError("prefix_p_up must be -1 (unavailable) or a probability in [0, 1]")
    if not np.isfinite(prefix_atr) or not (prefix_atr == -1.0 or prefix_atr >= 0.0):
        raise ValueError("prefix_atr must be -1 (unavailable) or a nonnegative ATR")
    if prefix_regime_vol not in (-1, 0, 1):
        raise ValueError("prefix_regime_vol must be -1, zero, or one")
    if volume is not None:
        volume = np.asarray(volume, dtype=np.float64)
        if (volume.ndim != 1 or len(volume) != n
                or not np.all(np.isfinite(volume)) or np.any(volume < 0.0)):
            raise ValueError("volume must be a finite, nonnegative array matching the market data")
        volume = np.ascontiguousarray(volume)
    first_bar_can_enter = n > 1 and (
        volume is None or (volume[0] > 0.0 and np.any(volume[1:] > 0.0))
    )
    if first_bar_can_enter and prefix_p_up >= chromosome[0] and prefix_atr < 0.0:
        raise ValueError("A first-bar prefix entry requires prefix_atr from the preceding bar")
    return (*arrays, volume)


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
    """Validated entry point for the compiled next-open simulator.

    A prefix entry requires the previous bar's ATR; the current bar's ATR
    must never be substituted for information unavailable at its open.
    """
    inputs = _validate_simulation_inputs(
        open_prices, close, high, low, p_up, atr, regime_vol, chromosome,
        commission_pct, slippage_pct, initial_capital, volume,
        prefix_p_up, prefix_atr, prefix_regime_vol,
    )
    return _run_vectorized_simulation_fast(
        *inputs[:8], commission_pct, slippage_pct, initial_capital,
        apply_penalty, inputs[8], prefix_p_up, prefix_atr, prefix_regime_vol,
    )


@numba.njit(fastmath=True)
def _run_vectorized_simulation_fast(
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
            shares = alloc_cash / (exec_price * (1.0 + commission_pct))

            if shares > 0.0001:
                cost = shares * exec_price * (1.0 + commission_pct)
                cash -= cost
                position = shares
                entry_price = exec_price
                highest_price = max(exec_price, curr_open)
                entry_bar = i

                if i == 0:
                    prev_atr = prefix_atr
                else:
                    prev_atr = atr[i - 1]
                stop_price = entry_price - (sl_mult * prev_atr)
                target_price = entry_price + (tp_mult * prev_atr)

        # Phase 2D: Intrabar range touch (evaluates existing AND newly entered position on bar i)
        if position > 0.0 and has_volume:
            touch_stop = curr_low <= stop_price
            touch_target = curr_high >= target_price

            if touch_stop and touch_target:
                # Ambiguous bracket touch on same bar: Conservative policy assumes STOP touched first
                exec_price = min(stop_price, curr_open) * (1.0 - slippage_pct)
                proceeds = position * exec_price * (1.0 - commission_pct)
                cash += proceeds
                position = 0.0
                total_trades += 1
            elif touch_stop:
                exec_price = min(stop_price, curr_open) * (1.0 - slippage_pct)
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
        if position > 0.0 and has_volume:
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

    if apply_penalty:
        sharpe, max_dd = apply_fitness_penalty(sharpe, max_dd, total_trades)

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
    required = {"Date", "Open", "Close", "High", "Low", "atr_14", "regime_high_vol"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing simulation columns: {', '.join(sorted(missing))}")
    dates_index = pd.DatetimeIndex(pd.to_datetime(df["Date"], errors="raise"))
    if dates_index.hasnans or not dates_index.is_monotonic_increasing or dates_index.has_duplicates:
        raise ValueError("Date values must be valid, strictly increasing, and unique")
    open_prices = df["Open"].to_numpy(dtype=np.float64)
    close = df["Close"].to_numpy(dtype=np.float64)
    high = df["High"].to_numpy(dtype=np.float64)
    low = df["Low"].to_numpy(dtype=np.float64)
    atr = df["atr_14"].to_numpy(dtype=np.float64)
    regime_vol = df["regime_high_vol"].to_numpy(dtype=np.float64)
    dates = df["Date"].values
    volumes = df["Volume"].to_numpy(dtype=np.float64) if "Volume" in df.columns else None

    open_prices, close, high, low, p_up, atr, regime_vol, chromosome, volumes = _validate_simulation_inputs(
        open_prices, close, high, low, p_up, atr, regime_vol, chromosome,
        commission_pct, slippage_pct, initial_capital, volumes,
        prefix_p_up, prefix_atr, prefix_regime_vol,
    )
    n = len(close)
    if n == 0:
        return {
            "engine_accounting_version": ENGINE_ACCOUNTING_VERSION,
            "initial_capital": float(initial_capital),
            "dates": np.array([]),
            "equity": np.array([]),
            "drawdowns": np.array([]),
            "positions": np.array([]),
            "capital_exposures": np.array([]),
            "benchmark_equity": np.array([]),
            "benchmark_drawdowns": np.array([]),
            "benchmark_max_drawdown": 0.0,
            "trade_log": pd.DataFrame(columns=_TRADE_COLUMNS),
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
            shares = alloc_cash / (exec_price * (1.0 + commission_pct))

            if shares > 0.0001:
                cost = shares * exec_price * (1.0 + commission_pct)
                cash -= cost
                position = shares
                entry_price = exec_price
                highest_price = max(exec_price, curr_open)
                entry_bar = i

                if i == 0:
                    prev_atr = prefix_atr
                else:
                    prev_atr = atr[i - 1]
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
                exec_price = min(stop_price, curr_open) * (1.0 - slippage_pct)
                exit_reason = "Bracket Conflict (Prioritized Stop)"
            elif touch_stop:
                exit_trade = True
                exec_price = min(stop_price, curr_open) * (1.0 - slippage_pct)
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
        if position > 0.0 and has_volume:
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

    # Buy-and-hold uses the same fees, slippage, and tradability as the strategy.
    # The benchmark may enter on its final tradable bar, as a passive baseline.
    benchmark_equity = np.full(n, initial_capital, dtype=np.float64)
    tradable = np.ones(n, dtype=bool) if volumes is None else volumes > 0.0
    tradable_indices = np.flatnonzero(tradable)
    if len(tradable_indices):
        first, last = int(tradable_indices[0]), int(tradable_indices[-1])
        benchmark_entry = open_prices[first] * (1.0 + slippage_pct)
        benchmark_shares = initial_capital / (benchmark_entry * (1.0 + commission_pct))
        benchmark_equity[first:last] = benchmark_shares * close[first:last]
        benchmark_equity[last:] = (
            benchmark_shares * close[last] * (1.0 - slippage_pct) * (1.0 - commission_pct)
        )
    b_peak = np.maximum.accumulate(np.maximum(benchmark_equity, initial_capital))
    benchmark_drawdowns = (benchmark_equity - b_peak) / (b_peak + 1e-8)
    benchmark_mdd = float(-np.min(benchmark_drawdowns))

    # Compute Detailed Metrics independently
    running_max = initial_capital
    max_dd = 0.0
    for k in range(n):
        if equity[k] > running_max:
            running_max = equity[k]
        dd = (running_max - equity[k]) / (running_max + 1e-8)
        if dd > max_dd:
            max_dd = dd

    # Every point is relative to the peak available at that point in time.
    # A later peak must not manufacture drawdown on an earlier date.
    running_peaks = np.maximum.accumulate(np.maximum(equity, initial_capital))
    drawdowns = (equity - running_peaks) / (running_peaks + 1e-8)
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

    trades_df = pd.DataFrame(trade_log, columns=_TRADE_COLUMNS)
    total_trades = len(trades_df)
    win_rate = float((trades_df["pnl"] > 0).mean()) if total_trades > 0 else 0.0
    turnover = float(total_trades) / (float(n) / 252.0)
    time_in_market = float(np.mean(positions_series > 0.0))
    capital_exposure = float(np.mean(capital_exposures))

    return {
        "engine_accounting_version": ENGINE_ACCOUNTING_VERSION,
        "initial_capital": float(initial_capital),
        "dates": dates,
        "equity": equity,
        "drawdowns": drawdowns,
        "positions": positions_series,
        "capital_exposures": capital_exposures,
        "benchmark_equity": benchmark_equity,
        "benchmark_drawdowns": benchmark_drawdowns,
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

