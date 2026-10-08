from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_stage41abc_seaad_safe_feature_download_analyze_benchmark_v1 import donor_linkage_and_matrix_build, load_cfg, resolve, write_csv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_cfg(args.config)
    analysis = {}
    for key in ["donor_metadata_analysis", "mri_volumetrics_analysis"]:
        path = resolve(cfg["outputs"][key])
        analysis[key] = pd.read_csv(path) if path.exists() else pd.DataFrame()
    manifest_path = resolve(cfg["outputs"]["download_manifest"])
    manifest = pd.read_csv(manifest_path) if manifest_path.exists() else pd.DataFrame()
    linkage, matrices, summary = donor_linkage_and_matrix_build(cfg, analysis, manifest)
    write_csv(linkage, cfg["outputs"]["donor_linkage_audit"])
    write_csv(matrices, cfg["outputs"]["safe_feature_matrix_manifest"])
    write_csv(summary, cfg["outputs"]["safe_metadata_mri_feature_matrix_summary"])
    print(f"feature_matrices_built={int(matrices['safe_feature_matrix_built'].sum()) if not matrices.empty else 0}")


if __name__ == "__main__":
    main()
