"""Real bundled-data dashboard smoke test; no browser/visual QA is implied.

Run from the repository root: python -m scripts.verify_dashboard_offline
"""
import json
from pathlib import Path
from unittest.mock import patch

from streamlit import config
from streamlit.testing.v1 import AppTest


def main():
    root = Path(__file__).resolve().parent.parent
    config.get_config_options(options_from_flags={"global.developmentMode": False})
    with patch("yfinance.Ticker", side_effect=AssertionError("Offline demo must not download")), patch(
        "yfinance.download", side_effect=AssertionError("Offline demo must not download")
    ):
        at = AppTest.from_file(str(root / "app.py"), default_timeout=180).run()
        assert not at.exception
        at.checkbox(key="checkbox_offline").set_value(True).run()
        at.button(key="btn_run_experiment").click().run(timeout=180)
        assert not at.exception, [e.message for e in at.exception]
        assert [tab.label for tab in at.tabs] == ["Overview", "Strategies", "Model", "Trades", "Method"]
        result = at.session_state["pipeline_results"]
        assert result["data_provenance"]["source"] == "offline_snapshot"
        assert at.session_state["executed_settings"]["pop_size"] == 40
        ids = result["summary_df"]["id"].tolist()
        primary = result["frozen_strategy_id"]
        alternatives = [candidate for candidate in ids if candidate != primary]
        if alternatives:
            at.selectbox(key="select_candidate_id").select(alternatives[0]).run()
            assert not at.exception
            assert at.session_state["pipeline_results"]["frozen_strategy_id"] == primary
        at.slider(key="slider_pop_size").set_value(50).run()
        assert not at.exception
        assert at.session_state["executed_settings"]["pop_size"] == 40
        assert any("Pending" in element.value for element in at.markdown)
        at.slider(key="slider_pop_size").set_value(40).run()
        at.button(key="btn_run_experiment").click().run(timeout=180)
        assert not at.exception
        assert at.selectbox(key="select_candidate_id").value == primary
        d = result["detailed_test_result"]
        evidence = {
            "test": "Real offline Streamlit AppTest; not browser visual QA",
            "engine_accounting_version": d["engine_accounting_version"],
            "settings": {"ticker": "RELIANCE.NS", "population": 40, "generations": 15, "seed": 42, "offline": True},
            "tabs": [tab.label for tab in at.tabs],
            "exceptions": len(at.exception),
            "verified": ["initial state", "offline real pipeline", "five tabs", "candidate selection preserves primary", "pending edits preserve executed settings", "repeat run resets selection"],
            "data_sha256": result["data_provenance"]["raw_sha256"],
            "metrics": {name: d[name] for name in ("total_return", "benchmark_return", "max_drawdown", "sharpe_ratio", "total_trades", "win_rate")},
        }
        output = root / "reports/verification/dashboard_apptest_v2.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2) + "\n")
        print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
