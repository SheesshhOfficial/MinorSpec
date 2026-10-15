"""
Configuration settings for the Computational Intelligence Stock Market Optimization System.
"""
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"

# Ensure directories exist
for d in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Default Asset Universe
DEFAULT_TICKERS = ["SPY", "RELIANCE.NS", "TCS.NS", "INFY.NS", "^NSEI", "QQQ", "AAPL", "MSFT", "NVDA"]
BENCHMARK_TICKER = "SPY"

# Time Horizon (Multi-Regime: Dot-com aftermath, 2008 GFC, 2020 COVID, 2022 Bear, 2023-2024 AI rally)
START_DATE = "2000-01-01"
END_DATE = None  # None pulls until the latest available date

# Market Frictions (Realistic simulation)
DEFAULT_COMMISSION_PCT = 0.0005  # 0.05% (5 bps) per trade
DEFAULT_SLIPPAGE_PCT = 0.0005    # 0.05% (5 bps) estimated slippage
INITIAL_CAPITAL = 100000.0       # $100,000 portfolio base

# Prediction Horizons
PREDICTION_HORIZON_BARS = 3       # Predict 3-day forward return direction
VOLATILITY_LOOKBACK = 20          # 20-day realized volatility window

# NSGA-II Genetic Algorithm Hyperparameters
POPULATION_SIZE = 80
NUM_GENERATIONS = 35
CROSSOVER_PROB = 0.85
MUTATION_PROB = 0.20
ETA_CROSSOVER = 15.0             # SBX distribution index
ETA_MUTATION = 20.0              # Polynomial mutation distribution index

# Chromosome Gene Definitions: [Lower Bound, Upper Bound, Description]
# 1. p_entry_threshold: Min model confidence to trigger LONG position [0.52, 0.85]
# 2. p_exit_threshold: Confidence drop triggering early exit [0.35, 0.50]
# 3. stop_loss_atr_mult: Multiplier for Average True Range dynamic stop loss [1.0, 4.5]
# 4. take_profit_atr_mult: Multiplier for ATR dynamic take profit target [1.5, 7.0]
# 5. trailing_stop_pct: Trailing stop percentage to lock profits [0.01, 0.06]
# 6. regime_vol_discount: Position scale factor when in high volatility regime [0.1, 1.0]
# 7. max_holding_period: Max bars to hold if neither TP nor SL triggers [5, 45]

GENE_BOUNDS = [
    (0.52, 0.85),  # p_entry_threshold
    (0.35, 0.50),  # p_exit_threshold
    (1.0, 4.5),    # stop_loss_atr_mult
    (1.5, 7.0),    # take_profit_atr_mult
    (0.01, 0.06),  # trailing_stop_pct
    (0.10, 1.00),  # regime_vol_discount
    (5.0, 45.0),   # max_holding_period
]
