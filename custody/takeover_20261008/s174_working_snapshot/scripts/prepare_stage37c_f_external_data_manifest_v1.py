from __future__ import annotations

import argparse
from pathlib import Path
import yaml
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_cfg(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage37c_f_multidataset_external_support_v1.yaml")
    parser.add_argument("--output", default="results/tables/stage37c_f_data_acquisition_manifest_v1.csv")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    rows = []
    for ds in cfg["datasets"]:
        for file_type, content, priority in [
            ("expression_matrix", "gene-by-cell or cell-by-gene expression matrix with gene symbols", "high"),
            ("cell_metadata", "cell/sample metadata with cell type, donor/sample, disease/pathology fields", "high"),
            ("pathology_metadata", "tau/pTau, amyloid/A beta, AD/control, or mechanism-specific readouts where available", "high"),
            ("gene_metadata", "feature metadata or gene-symbol mapping", "medium"),
        ]:
            rows.append(
                {
                    "dataset_id": ds["dataset_id"],
                    "dataset_name": ds["dataset_name"],
                    "required_file_type": file_type,
                    "expected_content": content,
                    "local_expected_path": f"data/external/{ds['dataset_id']}/",
                    "official_accession_or_source": ds["accession"],
                    "required_for_analysis": file_type in {"expression_matrix", "cell_metadata"},
                    "priority": priority,
                    "notes": "Acquire manually/officially if not already local; do not commit raw data.",
                }
            )
    out = resolve(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(str(out.relative_to(ROOT)))


if __name__ == "__main__":
    main()
