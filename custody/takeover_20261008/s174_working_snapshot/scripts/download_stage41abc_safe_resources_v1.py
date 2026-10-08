from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_stage41abc_seaad_safe_feature_download_analyze_benchmark_v1 import download_safe_resources, load_cfg, resolve, write_csv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_cfg(args.config)
    links_path = resolve(cfg["outputs"]["discovered_download_links"])
    links = pd.read_csv(links_path) if links_path.exists() else pd.DataFrame()
    attempts, manifest, checksums = download_safe_resources(cfg, links)
    write_csv(attempts, cfg["outputs"]["download_attempts"])
    write_csv(manifest, cfg["outputs"]["download_manifest"])
    write_csv(checksums, cfg["outputs"]["file_checksum_manifest"])
    print(f"files_downloaded={len(manifest)}")
    print(f"download_attempts={len(attempts)}")


if __name__ == "__main__":
    main()
