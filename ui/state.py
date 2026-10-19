"""Validate a completed pipeline result before replacing the displayed run."""

import pandas as pd


def validate_results_for_display(results: dict) -> None:
    """Reject incomplete runs while the UI can still retain its prior valid result."""
    for name in ("train", "val", "dev", "test"):
        partition = results.get("splits", {}).get(name)
        if not isinstance(partition, pd.DataFrame) or partition.empty:
            raise ValueError(f"The {name} partition has no usable rows.")
        if "Date" not in partition:
            raise ValueError(f"The {name} partition has no dates.")

    summary = results.get("summary_df")
    if not isinstance(summary, pd.DataFrame) or summary.empty:
        raise ValueError("The evolutionary search returned no candidate strategies.")
    if "id" not in summary or results.get("frozen_strategy_id") not in summary["id"].values:
        raise ValueError("The frozen primary strategy is missing from the search results.")
