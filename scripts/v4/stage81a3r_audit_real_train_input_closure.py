"""Metadata-only closure audit for the provisional Stage81A3R TRAIN input."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from sea_ad_jepa.v4.a3r_global_state import input_closure_counts


STATUS = "GLOBAL_STATE_PILOT_INPUT_CONTRACT_LIMITED"
BLOCKER = "TRAIN_ONLY_FULL_ADDRESS_EXTRACTION_NOT_POSSIBLE_UNDER_CURRENT_FIREWALL"
COLUMN_ADDRESSABLE_SUFFIXES = {".h5", ".h5ad", ".zarr", ".parquet", ".feather"}


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def atomic_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(dir=path.parent, suffix=".csv")
    os.close(descriptor)
    temporary = Path(name)
    frame.to_csv(temporary, index=False, lineterminator="\n")
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--source-project", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a3r_real_train_global_state.yaml"))
    args = parser.parse_args()
    project = args.project_dir.resolve()
    source = (args.source_project or project).resolve()
    config = yaml.safe_load((project / args.config).read_text(encoding="utf-8"))
    registry = pd.read_csv(source / config["inputs"]["address_registry"])
    support = pd.read_csv(source / config["inputs"]["measurement_support"])
    provenance = pd.read_csv(source / config["inputs"]["source_provenance"], low_memory=False)
    historical = set(
        pd.read_csv(source / config["inputs"]["nph_cache_vocabulary"])
        .canonical_ensembl_gene_id.astype(str)
    )

    if len(registry) != 41_238 or support.matrix_id.nunique() != 42:
        raise RuntimeError("frozen successor-address or 42-operator contract mismatch")

    rows: list[dict[str, Any]] = []
    for (matrix_id, source_id), group in support.groupby(["matrix_id", "source_dataset_id"], sort=True):
        expected_frame = group[group.measured_address.astype(bool)]
        expected = set(expected_frame.molecular_address_id.astype(str))
        if str(matrix_id).startswith("NPH52::matrix::"):
            actual = expected & historical
            input_representation = "historical_train_only_4096_address_cache"
        else:
            actual = set(
                provenance.loc[
                    provenance.source_dataset_id.astype(str).eq(str(source_id)),
                    "molecular_address_id",
                ].astype(str)
            )
            input_representation = "column_addressable_h5_source"
        counts = input_closure_counts(expected, actual)
        missing = expected_frame[expected_frame.molecular_address_id.astype(str).isin(expected - actual)]
        rows.append({
            "status": STATUS,
            "matrix_id": str(matrix_id),
            "source_dataset_id": str(source_id),
            "input_representation": input_representation,
            **counts,
            "missing_current_exact": int(missing.identity_class.eq("current_exact").sum()),
            "missing_legacy_exact": int(missing.identity_class.eq("legacy_exact").sum()),
            "missing_source_native_anchored": int(missing.identity_class.eq("source_native_anchored").sum()),
            "historical_top_k_truncation_detected": bool(counts["expected_but_missing"] > 0 and str(matrix_id).startswith("NPH52::matrix::")),
            "closure_pass": counts["expected_but_missing"] == 0 and counts["unexpected_addresses"] == 0,
        })

    frame = pd.DataFrame(rows).sort_values("matrix_id").reset_index(drop=True)
    nph_root = source / config["inputs"]["nph_source_root"]
    nph_files = sorted(path for path in nph_root.iterdir() if path.is_file())
    qs_files = [path for path in nph_files if path.suffix.lower() == ".qs"]
    column_addressable = [path for path in nph_files if path.suffix.lower() in COLUMN_ADDRESSABLE_SUFFIXES]
    if len(qs_files) != 7:
        raise RuntimeError(f"expected seven authoritative NPH QS objects, found {len(qs_files)}")
    if column_addressable:
        raise RuntimeError("column-addressable NPH source discovered; firewall classification requires review")
    if int(frame.closure_pass.sum()) != 35 or int((~frame.closure_pass).sum()) != 7:
        raise RuntimeError("unexpected operator-closure pattern")

    outputs = {key: project / value for key, value in config["outputs"].items()}
    atomic_csv(outputs["input_closure_audit"], frame)
    report = {
        "status": STATUS,
        "classification": BLOCKER,
        "full_successor_address_input_closure_pass": False,
        "operators": 42,
        "operators_closed": int(frame.closure_pass.sum()),
        "operators_blocked": int((~frame.closure_pass).sum()),
        "blocked_operator_family": "NPH52",
        "nph_authoritative_count_objects": len(qs_files),
        "nph_source_storage_format": "monolithic_qs_serialized_SingleCellExperiment",
        "nph_column_addressable_full_feature_assets": 0,
        "qread_occurs_before_column_selection_in_repository_extractors": True,
        "mixed_split_materialization_permitted": False,
        "corrected_real_train_rerun_permitted": False,
        "pilot_results_overwritten": False,
        "pilot_classification": STATUS,
        "execution_history_incident": {
            "mixed_split_rna_transiently_materialized": True,
            "classification": "GOVERNANCE / DATA-ACCESS INCIDENT",
        },
        "accepted_analytic_lineage": {
            "train_rna_only": True,
            "development_rna_used_in_analysis": False,
            "sealed_rna_used_in_analysis": False,
            "discarded_mixed_split_cache_used": False,
            "discarded_mixed_split_cache_retained": False,
            "pathology_opened": False,
        },
    }
    atomic_json(outputs["input_closure_report"], report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
