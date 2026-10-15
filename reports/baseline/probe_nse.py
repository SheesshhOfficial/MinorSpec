"""
Reproducible Probe of NSE Feasibility (yfinance Daily Historical OHLCV).
Saves structured JSON evidence to reports/baseline/nse_feasibility_evidence.json
"""
import json
from pathlib import Path
import yfinance as yf
import pandas as pd
from src.config import REPORTS_DIR


def probe_nse_universe():
    tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "^NSEI"]
    evidence = {}

    print("Probing NSE Universe via yfinance...")
    for t in tickers:
        print(f"Fetching {t}...")
        tk = yf.Ticker(t)
        df = tk.history(start="2000-01-01", auto_adjust=True)

        if df.empty:
            evidence[t] = {"status": "EMPTY"}
            continue

        nan_dict = {col: int(df[col].isna().sum()) for col in ["Open", "High", "Low", "Close", "Volume"]}
        zero_vol = int((df["Volume"] == 0).sum())
        total_rows = len(df)
        start_date = str(df.index.min())[:10]
        end_date = str(df.index.max())[:10]

        evidence[t] = {
            "status": "AVAILABLE",
            "provider": "yfinance",
            "adjustment": "auto_adjust=True (stock splits & dividends adjusted)",
            "start_date": start_date,
            "end_date": end_date,
            "total_rows": total_rows,
            "nan_counts": nan_dict,
            "zero_volume_bars": zero_vol,
            "zero_volume_pct": round((zero_vol / total_rows) * 100, 2),
            "data_frequency": "1d (daily bars)",
            "known_limitations": [
                "Zero-volume daily bars appear in the provider feed (observed in equity series and prominently in ^NSEI index series where volume is intermittently unpopulated by the provider).",
                "Survivorship bias: Individual current tickers reflect surviving corporate entities and do not reconstruct historical point-in-time index constituent changes.",
                "TCS.NS historical series provided by yfinance commences on 2002-08-12; provider data prior to that date is not available.",
            ],
        }

    out_file = REPORTS_DIR / "baseline" / "nse_feasibility_evidence.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(evidence, f, indent=2)

    print(f"Saved NSE feasibility evidence -> {out_file}")
    return evidence


if __name__ == "__main__":
    probe_nse_universe()
