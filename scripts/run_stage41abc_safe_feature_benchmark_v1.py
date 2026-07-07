from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_stage41abc_seaad_safe_feature_download_analyze_benchmark_v1 import load_cfg, skipped_benchmark_tables, write_csv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_cfg(args.config)
    reason = "No schema-reviewed donor-linked safe feature matrix was available for standalone Stage 41ABC benchmark."
    tables = skipped_benchmark_tables(cfg, reason)
    for key, df in tables.items():
        write_csv(df, cfg["outputs"][key])
    print("benchmark_training_ran=False")
    print("benchmark_lock_decision=manual_feature_acquisition_required")


if __name__ == "__main__":
    main()
