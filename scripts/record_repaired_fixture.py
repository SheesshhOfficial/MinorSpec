"""Record one explicitly versioned offline v2 verification fold; never touch archives.

Run: python -m scripts.record_repaired_fixture
The output must not exist; recording a new baseline requires an explicit new path.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

from src.backtest_engine import ENGINE_ACCOUNTING_VERSION
from src.rolling_runner import RollingNSEExperimentRunner, compute_sha256


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=root / "reports/verification/repaired_tcs_2021_seed42.json")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite a recorded fixture: {args.output}")
    runner = RollingNSEExperimentRunner(
        inputs_dir=root / "reports/experiments/inputs", output_dir=root / "reports/verification",
        protocol_path=root / "reports/experiments/protocol.json", test_years=[2021],
        universe=["TCS.NS"], ga_seeds=[42], model_seed=42,
    )
    fold = runner.run_fold("TCS.NS", runner.load_processed_asset("TCS.NS"), 2021)
    result = {
        "metadata": {
            "purpose": "Repaired-engine regression fixture; not a replacement for archived research results",
            "engine_accounting_version": ENGINE_ACCOUNTING_VERSION,
            "command": "OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m scripts.record_repaired_fixture",
            "python": platform.python_version(),
            "dependencies": {name: importlib.metadata.version(name) for name in ("numpy", "pandas", "lightgbm", "numba", "scikit-learn", "pyarrow")},
            "source_sha256": {str(path.relative_to(root)): compute_sha256(path) for path in sorted((root / "src").glob("*.py"))},
            "ticker": "TCS.NS", "test_year": 2021, **fold["run_provenance"],
        },
        "hybrid": fold["ga_runs"]["42"]["hybrid"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(f"Recorded {args.output} (SHA-256: {compute_sha256(args.output)})")


if __name__ == "__main__":
    main()
