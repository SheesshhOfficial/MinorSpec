"""Check dashboard imports without downloading prices or starting a server."""
import importlib


RUNTIME_MODULES = (
    "streamlit", "plotly", "pandas", "numpy", "pyarrow", "scipy", "sklearn",
    "numba", "yfinance", "lightgbm", "src.pipeline", "ui.charts",
)


def check_runtime_dependencies(importer=None):
    importer = importer or importlib.import_module
    failures = []
    for module in RUNTIME_MODULES:
        try:
            importer(module)
        except Exception as exc:
            failures.append((module, str(exc)))
    return failures


def main():
    failures = check_runtime_dependencies()
    for module, error in failures:
        print(f"[ERROR] Cannot import {module}: {error}")
    if failures:
        print("Install or repair requirements.txt in the active Python environment.")
        return 1
    print("[INFO] Dashboard runtime imports are available.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
