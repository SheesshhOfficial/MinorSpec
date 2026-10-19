"""Portable launcher checks; these do not execute Windows cmd.exe."""
from pathlib import Path

from scripts.check_runtime_dependencies import check_runtime_dependencies, RUNTIME_MODULES


def test_runtime_dependency_check_visits_all_modules_without_installing():
    visited = []
    assert check_runtime_dependencies(visited.append) == []
    assert tuple(visited) == RUNTIME_MODULES


def test_runtime_dependency_check_reports_missing_and_binary_failures():
    def importer(name):
        if name == "lightgbm":
            raise ImportError("missing lightgbm")
        if name == "numba":
            raise OSError("binary dependency unavailable")
    failures = dict(check_runtime_dependencies(importer))
    assert failures == {"numba": "binary dependency unavailable", "lightgbm": "missing lightgbm"}


def test_batch_uses_live_errorlevel_and_rechecks_after_install():
    script = (Path(__file__).resolve().parents[1] / "run_app.bat").read_text()
    assert "if %ERRORLEVEL%" not in script
    assert "python -m pip install -r requirements.txt" in script
    assert script.count("python -m scripts.check_runtime_dependencies") == 2
    assert "if errorlevel 1 (" in script
    assert script.index("python -m pip install") < script.rindex("python -m scripts.check_runtime_dependencies")
    assert script.rindex("python -m scripts.check_runtime_dependencies") < script.index("python -m streamlit run")
