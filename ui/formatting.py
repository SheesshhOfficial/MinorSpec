"""
Formatting utilities for currency, percentages, ratios, and dates.
Preserves strict financial truth:
- Indian NSE assets (.NS or ^NSEI): INR (₹)
- US assets (SPY, QQQ, AAPL, etc.): USD ($)
- Unknown/custom ticker: Neutral quote-currency units (pts / units) unless currency known.
"""

from typing import Tuple
import math


def get_asset_currency_info(ticker: str) -> Tuple[str, str]:
    """
    Returns (currency_symbol, currency_code).
    """
    clean = ticker.strip().upper()
    if clean.endswith(".NS") or clean == "^NSEI" or clean == "NIFTY":
        return "₹", "INR"
    elif clean in ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL"]:
        return "$", "USD"
    else:
        return "", "units"


def format_currency(value: float, ticker: str, include_symbol: bool = True) -> str:
    """
    Formats a nominal monetary amount with appropriate symbol and thousands commas.
    """
    symbol, code = get_asset_currency_info(ticker)
    if abs(value) >= 1e7:
        formatted_num = f"{value:,.0f}"
    else:
        formatted_num = f"{value:,.2f}"

    if include_symbol and symbol:
        return f"{symbol}{formatted_num}"
    elif include_symbol and not symbol:
        return f"{formatted_num} {code}"
    return formatted_num


def format_pct(value: float, include_sign: bool = False, decimal_places: int = 2) -> str:
    """
    Formats decimal ratio as percentage string (e.g. 0.1234 -> +12.34% or 12.34%).
    """
    if value is None or not math.isfinite(value):
        return "N/A"
    sign_fmt = "+" if include_sign else ""
    return f"{value * 100.0:{sign_fmt}.{decimal_places}f}%"


def format_ratio(value: float, decimal_places: int = 2) -> str:
    """
    Formats unitless ratios such as Sharpe ratio.
    """
    if value is None or not math.isfinite(value):
        return "N/A"
    return f"{value:.{decimal_places}f}"

