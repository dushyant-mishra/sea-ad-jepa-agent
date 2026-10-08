from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_stage41abc_seaad_safe_feature_download_analyze_benchmark_v1 import analyze_downloads, load_cfg, resolve, write_csv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_cfg(args.config)
    manifest_path = resolve(cfg["outputs"]["download_manifest"])
    links_path = resolve(cfg["outputs"]["discovered_download_links"])
    manifest = pd.read_csv(manifest_path) if manifest_path.exists() else pd.DataFrame()
    links = pd.read_csv(links_path) if links_path.exists() else pd.DataFrame()
    tables = analyze_downloads(cfg, manifest, links)
    for key, df in tables.items():
        write_csv(df, cfg["outputs"][key])
    print(f"downloaded_files_analyzed={len(tables['downloaded_file_analysis'])}")


if __name__ == "__main__":
    main()
