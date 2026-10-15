"""
Performance & Correctness Benchmark for Numba Vectorized Simulator.
"""
import time
import numpy as np
from src.backtest_engine import run_vectorized_simulation_fast


def test_numba_backtest_speed_and_costs():
    n = 5000
    np.random.seed(42)
    close = 100.0 * np.exp(np.cumsum(np.random.normal(0.0003, 0.015, n)))
    high = close * (1.0 + np.abs(np.random.normal(0, 0.005, n)))
    low = close * (1.0 - np.abs(np.random.normal(0, 0.005, n)))
    open_prices = (close + np.roll(close, 1)) / 2.0
    open_prices[0] = 100.0
    p_up = np.random.uniform(0.3, 0.8, n)
    atr = close * 0.02
    regime_vol = np.random.choice([0, 1], n)

    sample_chromosome = np.array([0.60, 0.40, 2.0, 4.0, 0.03, 0.5, 20.0], dtype=np.float64)

    # Warmup
    run_vectorized_simulation_fast(open_prices, close, high, low, p_up, atr, regime_vol, sample_chromosome)

    # Benchmark 500 evaluations
    t0 = time.perf_counter()
    for _ in range(500):
        sharpe, mdd, ret, trades, to = run_vectorized_simulation_fast(
            open_prices, close, high, low, p_up, atr, regime_vol, sample_chromosome
        )
    elapsed = time.perf_counter() - t0

    ms_per_eval = (elapsed / 500) * 1000
    print(f"Backtest speed: {ms_per_eval:.3f} ms per simulation over {n} bars")
    assert ms_per_eval < 2.0, f"Simulation too slow: {ms_per_eval} ms"
    assert 0.0 <= mdd <= 1.0, f"Invalid max drawdown: {mdd}"


if __name__ == "__main__":
    test_numba_backtest_speed_and_costs()
    print("All backtest performance tests passed successfully!")
