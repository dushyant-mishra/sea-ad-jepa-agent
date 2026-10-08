from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def resolve(p: str | Path) -> Path:
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/agent/stage38a_external_data_acquisition_preprocessing_v1.yaml")
    ap.add_argument("--output", default="results/tables/stage38a_download_manifest_v1.csv")
    args = ap.parse_args()
    cfg = yaml.safe_load(resolve(args.config).read_text(encoding="utf-8"))
    rows = []
    for ds in cfg["datasets"]:
        for file_type in ["expression_matrix", "metadata", "gene_metadata"]:
            rows.append({
                "dataset_id": ds["dataset_id"],
                "accession": ds["accession"],
                "file_id": f"{ds['dataset_id']}_{file_type}",
                "file_type": file_type,
                "source_url_or_accession": f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={ds['accession']}",
                "expected_filename": f"{ds['accession']}_{file_type}",
                "local_path": f"data/external/{ds['dataset_id']}/raw/",
                "download_attempted": False,
                "download_success": False,
                "file_size_bytes": 0,
                "checksum_sha256": "",
                "required_for_analysis": file_type in {"expression_matrix", "metadata"},
                "notes": "Manual/official acquisition if local files are absent; Stage 38A does not scrape.",
            })
    out = resolve(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(str(out.relative_to(ROOT)))


if __name__ == "__main__":
    main()
