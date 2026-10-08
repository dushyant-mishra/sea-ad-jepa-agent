from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/agent/stage38a_external_data_acquisition_preprocessing_v1.yaml")
    args = ap.parse_args()
    cmd = [sys.executable, str(ROOT / "scripts" / "run_stage38a_external_data_acquisition_preprocessing_v1.py"), "--config", args.config]
    raise SystemExit(subprocess.call(cmd, cwd=ROOT))


if __name__ == "__main__":
    main()
