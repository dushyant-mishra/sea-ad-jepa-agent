"""Verify that collision-masked source-to-address mappings are injective."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml


EXPECTED_SUPPLEMENTAL_ADDRESSES = {"ENSG00000183889", "ENSG00000281635"}
EXPECTED_SUPPLEMENTAL_MATRICES = {
    "NPH52::matrix::Astro_data_arranged_updatedId_final_batches.qs",
    "NPH52::matrix::Endo_data_arranged_updatedId_final_batches.qs",
    "NPH52::matrix::ExN_data_arranged_updatedId_final_batches.qs",
    "NPH52::matrix::InN_data_arranged_updatedId_final_batches.qs",
    "NPH52::matrix::MG_data_arranged_updatedId_final_batches.qs",
    "NPH52::matrix::OPC_data_arranged_updatedId_final_batches.qs",
    "NPH52::matrix::Oligo_data_arranged_updatedId_final_batches.qs",
}


def is_exact_known_supplemental(frame: pd.DataFrame) -> bool:
    expected_pairs = {
        (matrix_id, address)
        for matrix_id in EXPECTED_SUPPLEMENTAL_MATRICES
        for address in EXPECTED_SUPPLEMENTAL_ADDRESSES
    }
    observed_pairs = set(zip(frame.matrix_id.astype(str), frame.molecular_address_id.astype(str), strict=True))
    return (
        observed_pairs == expected_pairs
        and len(frame) == len(expected_pairs)
        and frame.unregistered_source_rows.astype(int).eq(2).all()
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--source-project", type=Path, required=True)
    parser.add_argument("--accept-known-supplemental", action="store_true")
    args = parser.parse_args()
    project, source = args.project_dir.resolve(), args.source_project.resolve()
    config = yaml.safe_load((project / "configs/v4/stage81a3r_real_train_global_state.yaml").read_text(encoding="utf-8"))
    provenance = pd.read_csv(source / config["inputs"]["source_provenance"], low_memory=False)
    collision = pd.read_csv(project / config["inputs"]["collision_ledger"], low_memory=False)
    support = pd.read_csv(source / config["inputs"]["measurement_support"])
    rows = []
    for matrix_id, group in support.groupby("matrix_id", sort=True):
        source_id = str(group.source_dataset_id.iloc[0])
        mapping = provenance[provenance.source_dataset_id.astype(str).eq(source_id)].copy()
        blocked = set(collision.loc[collision.matrix_id.astype(str).eq(str(matrix_id)), "source_feature_index"].astype(int))
        remaining = mapping[~mapping.source_feature_index.astype(int).isin(blocked)]
        duplicated = remaining[remaining.molecular_address_id.duplicated(False)]
        for address, local in duplicated.groupby("molecular_address_id", sort=True):
            rows.append({
                "matrix_id": str(matrix_id), "source_dataset_id": source_id,
                "molecular_address_id": str(address),
                "source_feature_indices": "|".join(map(str, sorted(local.source_feature_index.astype(int)))),
                "mapping_evidence_classes": "|".join(sorted(set(local.mapping_evidence_class.astype(str)))),
                "unregistered_source_rows": len(local),
            })
    frame = pd.DataFrame(rows)
    supplemental_accepted = bool(args.accept_known_supplemental and is_exact_known_supplemental(frame))
    report = {
        "operators_audited": int(support.matrix_id.nunique()),
        "operators_with_unregistered_collisions": int(frame.matrix_id.nunique()) if len(frame) else 0,
        "unregistered_matrix_address_collisions": int(len(frame)),
        "unique_addresses": int(frame.molecular_address_id.nunique()) if len(frame) else 0,
        "rows": frame.to_dict(orient="records"),
        "checkpoint_collision_mask_injective": not len(frame),
        "known_supplemental_mask_accepted": supplemental_accepted,
        "scalar_mapping_injective_after_checkpoint_plus_supplemental_mask": bool(not len(frame) or supplemental_accepted),
    }
    output = project / "results/v4/stage81a3r_scalar_mapping_injectivity_preflight.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    frame.to_csv(
        project / "results/v4/stage81a3r_scalar_mapping_unregistered_collisions.csv",
        index=False, lineterminator="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.accept_known_supplemental:
        return 0 if supplemental_accepted else 2
    return 0 if not len(frame) else 2


if __name__ == "__main__":
    raise SystemExit(main())
