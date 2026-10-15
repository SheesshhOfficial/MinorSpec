"""
Gene definitions, technical indicator glossary, and academic methodology descriptions.
Factual references matching src/config.py and feature_pipeline.py.
"""

from typing import List, Dict, Any


GENE_DEFINITIONS = [
    {
        "name": "p_entry_threshold",
        "label": "Entry Probability Threshold",
        "units": "prob [0,1]",
        "bounds": "[0.52, 0.85]",
        "purpose": "Minimum model confidence P(Up) required at bar t-1 Close to queue a long entry at bar t Open.",
        "fmt": lambda v: f"{v:.3f}",
    },
    {
        "name": "p_exit_threshold",
        "label": "Exit Probability Threshold",
        "units": "prob [0,1]",
        "bounds": "[0.35, 0.50]",
        "purpose": "Confidence floor; if model P(Up) drops below this level, an exit is queued for next bar Open.",
        "fmt": lambda v: f"{v:.3f}",
    },
    {
        "name": "stop_loss_atr_mult",
        "label": "Dynamic ATR Stop Loss",
        "units": "x ATR(14)",
        "bounds": "[1.0, 4.5]",
        "purpose": "Distance below entry price for dynamic stop loss, scaled by 14-day Average True Range.",
        "fmt": lambda v: f"{v:.2f}x",
    },
    {
        "name": "take_profit_atr_mult",
        "label": "Dynamic ATR Take Profit",
        "units": "x ATR(14)",
        "bounds": "[1.5, 7.0]",
        "purpose": "Target distance above entry price for dynamic profit taking, scaled by 14-day ATR.",
        "fmt": lambda v: f"{v:.2f}x",
    },
    {
        "name": "trailing_stop_pct",
        "label": "Trailing Stop Percentage",
        "units": "% from peak",
        "bounds": "[1.0%, 6.0%]",
        "purpose": "Ratchet mechanism locking in gains; tracks highest price achieved and pulls stop upward.",
        "fmt": lambda v: f"{v * 100.0:.2f}%",
    },
    {
        "name": "regime_vol_discount",
        "label": "Volatility Regime Scale Factor",
        "units": "fraction [0,1]",
        "bounds": "[0.10, 1.00]",
        "purpose": "Position sizing multiplier applied when market is in high-volatility regime (volatility > 100-day median).",
        "fmt": lambda v: f"{v:.2f}",
    },
    {
        "name": "max_holding_period",
        "label": "Max Holding Duration",
        "units": "bars (days)",
        "bounds": "[5, 45]",
        "purpose": "Time-based exit ceiling; forces trade liquidation if neither stop loss nor take profit triggers within N bars.",
        "fmt": lambda v: f"{int(v)} bars",
    },
]


FEATURE_FRIENDLY_NAMES: Dict[str, str] = {
    "dist_sma_10": "Distance to SMA 10",
    "dist_sma_50": "Distance to SMA 50",
    "dist_sma_200": "Distance to SMA 200",
    "macd_ratio": "MACD Normalized Ratio",
    "macd_hist": "MACD Signal Histogram",
    "rsi_14": "RSI (14-Day Momentum)",
    "stoch_k": "Stochastic %K Oscillator",
    "stoch_d": "Stochastic %D Smoothing",
    "roc_5": "Rate of Change (5-Day)",
    "roc_10": "Rate of Change (10-Day)",
    "roc_20": "Rate of Change (20-Day)",
    "atr_pct": "ATR Volatility Ratio",
    "volatility_20": "Realized Volatility (20-Day)",
    "volatility_60": "Realized Volatility (60-Day)",
    "bb_pct_b": "Bollinger Bands %B",
    "bb_width": "Bollinger Bands Width",
    "volume_zscore": "Volume Z-Score",
    "obv_roc_5": "On-Balance Volume 5D ROC",
    "regime_high_vol": "High Volatility Regime Flag",
    "regime_trend": "Trend Regime Flag (Bull/Bear)",
}


FEATURE_GLOSSARY: Dict[str, Dict[str, str]] = {
    "Trend Indicators": {
        "dist_sma_10": "Percentage distance from current Close to 10-day Simple Moving Average ((Close / SMA10) - 1).",
        "dist_sma_50": "Percentage distance from current Close to 50-day Simple Moving Average.",
        "dist_sma_200": "Percentage distance from current Close to 200-day Simple Moving Average (macro trend anchor).",
        "macd_ratio": "MACD line (EMA12 - EMA26) normalized by Close price.",
        "macd_hist": "MACD histogram (difference between MACD line and 9-day signal EMA).",
    },
    "Momentum Indicators": {
        "rsi_14": "14-day Relative Strength Index measuring speed and change of price movements [0, 100].",
        "stoch_k": "Stochastic %K fast momentum oscillator over 14-day high-low range.",
        "stoch_d": "Stochastic %D smoothed 3-day average of %K.",
        "roc_5": "5-day price Rate of Change (pct_change(5)).",
        "roc_10": "10-day price Rate of Change.",
        "roc_20": "20-day price Rate of Change.",
    },
    "Volatility Indicators": {
        "atr_pct": "14-day Average True Range normalized by Close price (ATR14 / Close).",
        "volatility_20": "20-day realized volatility annualized using standard sqrt(252) scaling.",
        "volatility_60": "60-day realized volatility annualized.",
        "bb_pct_b": "Bollinger Bands %B position relative to upper and lower 2-sigma bands.",
        "bb_width": "Bollinger Bands width ((Upper - Lower) / Mid) measuring volatility expansion/contraction.",
    },
    "Volume & Regime Indicators": {
        "volume_zscore": "Standardized volume z-score over rolling 20-day mean and standard deviation.",
        "obv_roc_5": "5-day Rate of Change in cumulative On-Balance Volume.",
        "regime_high_vol": "Binary flag (1 if 20-day volatility exceeds rolling 100-day median, else 0).",
        "regime_trend": "Categorical trend regime flag (1 for Bullish Close > SMA50 > SMA200; -1 for Bearish; 0 neutral).",
    },
}
