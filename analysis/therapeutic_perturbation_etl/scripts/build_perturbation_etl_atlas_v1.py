#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

SCHEMA = "THERAPEUTIC_PERTURBATION_ETL_ATLAS_V1"
EXPECTED_STUDIES = {
    "GSE175721", "GSE178317", "GSE240609", "GSE241858",
    "GSE254205", "GSE293118", "GSE301119", "GSE311359",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require_columns(frame: pd.DataFrame, columns: set[str], label: str) -> None:
    missing = columns - set(frame.columns)
    if missing:
        raise SystemExit(f"{label} missing columns: {sorted(missing)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--data-root", default="data/external/v4/perturbation")
    ap.add_argument("--out-dir", default="analysis/therapeutic_perturbation_etl/evidence")
    ap.add_argument("--require-physical", action="store_true")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    out = (root / args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    identity = pd.read_csv(root / "results/v4/stage81a1c_p_perturbation_identity_registry.csv")
    hashes = pd.read_csv(root / "results/v4/stage81a1c_p_download_hashes.csv")
    catalog = pd.read_csv(root / "results/v4/stage81a1c_p_processed_asset_catalog.csv")
    readiness = pd.read_csv(root / "results/v4/pre_stage81a2_perturbation_readiness_registry.csv")

    require_columns(identity, {"accession", "cell_model", "perturbation_type", "crispr_mode", "guide_assignment_available", "primary_role"}, "identity")
    require_columns(hashes, {"accession", "path", "size_bytes", "sha256", "format_open_pass"}, "hashes")
    require_columns(catalog, {"accession", "asset_id", "filename", "remote_size", "decision", "raw_sequencing_selected"}, "catalog")
    require_columns(readiness, {"study_id", "source_path", "guide_to_cell_assignments_resolved", "controls_resolved", "replicates_resolved", "perturbation_identities_resolved", "perturbation_training_ready", "readiness_blockers"}, "readiness")

    observed_studies = set(identity.accession.astype(str))
    if observed_studies != EXPECTED_STUDIES:
        raise SystemExit(f"study universe drifted: {sorted(observed_studies)}")
    if catalog.raw_sequencing_selected.astype(bool).any():
        raise SystemExit("raw sequencing unexpectedly selected")
    if not hashes.format_open_pass.astype(bool).all():
        raise SystemExit("historical format-open verification contains failures")

    physical_rows = []
    for row in hashes.itertuples(index=False):
        path = root / str(row.path)
        present = path.is_file()
        observed_size = path.stat().st_size if present else None
        observed_sha = sha256(path) if present else None
        size_match = bool(present and observed_size == int(row.size_bytes))
        sha_match = bool(present and observed_sha == str(row.sha256).lower())
        physical_rows.append({
            "accession": str(row.accession),
            "path": str(row.path),
            "expected_size_bytes": int(row.size_bytes),
            "expected_sha256": str(row.sha256).lower(),
            "physical_present": present,
            "observed_size_bytes": observed_size,
            "observed_sha256": observed_sha,
            "size_match": size_match,
            "sha256_match": sha_match,
            "physical_authenticated": bool(present and size_match and sha_match),
        })
    physical = pd.DataFrame(physical_rows)
    if args.require_physical and not physical.physical_authenticated.all():
        bad = physical.loc[
            ~physical.physical_authenticated,
            ["accession", "path", "physical_present", "size_match", "sha256_match"],
        ]
        raise SystemExit("physical authentication failed:\n" + bad.to_string(index=False))

    study_rows = []
    for accession, group in readiness.groupby("study_id", sort=True):
        ident = identity.loc[identity.accession.astype(str) == str(accession)].iloc[0]
        study_rows.append({
            "accession": accession,
            "cell_model": ident.cell_model,
            "perturbation_type": ident.perturbation_type,
            "crispr_mode": ident.crispr_mode,
            "primary_role": ident.primary_role,
            "guide_assignment_declared_available": bool(ident.guide_assignment_available),
            "asset_rows": int(len(group)),
            "all_controls_resolved": bool(group.controls_resolved.astype(bool).all()),
            "all_replicates_resolved": bool(group.replicates_resolved.astype(bool).all()),
            "all_perturbation_identities_resolved": bool(group.perturbation_identities_resolved.astype(bool).all()),
            "all_guide_to_cell_assignments_resolved": bool(group.guide_to_cell_assignments_resolved.astype(bool).all()),
            "any_training_ready": bool(group.perturbation_training_ready.astype(bool).any()),
            "all_training_ready": bool(group.perturbation_training_ready.astype(bool).all()),
            "readiness_blockers": " | ".join(
                sorted(set(str(x) for x in group.readiness_blockers if str(x) and str(x) != "nan"))
            ),
        })
    studies = pd.DataFrame(study_rows)

    summary = {
        "schema": SCHEMA,
        "scope": "PERTURBATION_DATASET_ETL_AND_READINESS__NO_JEPA_TRAINING__NO_THERAPEUTIC_RANKING",
        "study_count": int(len(studies)),
        "processed_asset_count": int(len(catalog)),
        "historical_verified_asset_count": int(len(hashes)),
        "physical_authenticated_asset_count": int(physical.physical_authenticated.sum()),
        "physical_missing_or_mismatch_count": int((~physical.physical_authenticated).sum()),
        "training_ready_study_count": int(studies.all_training_ready.sum()),
        "guide_assignment_study_count": int(studies.guide_assignment_declared_available.sum()),
        "single_cell_guide_assignment_fully_resolved_study_count": int(studies.all_guide_to_cell_assignments_resolved.sum()),
        "firewall": {
            "jepa_training": "OFF",
            "therapeutic_ranking": "OFF",
            "protected_full104_outcomes": "UNOPENED",
            "pathology_adaptive_selection": "FORBIDDEN",
        },
        "interpretation": [
            "Historical acquisition/hash success is provenance evidence, not perturbation-analysis readiness.",
            "Guide assignment, controls, replicate structure, stable feature identity and measurement masks must be resolved before per-cell intervention effects are authoritative.",
            "Different cell models and modalities remain separate strata and are not concatenated by label alone.",
        ],
    }

    physical.to_csv(out / "PERTURBATION_ETL_PHYSICAL_AUTHENTICATION.csv", index=False, lineterminator="\n")
    studies.to_csv(out / "PERTURBATION_ETL_STUDY_READINESS.csv", index=False, lineterminator="\n")
    (out / "PERTURBATION_ETL_ATLAS_SUMMARY_V1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest = []
    for path in sorted(out.iterdir()):
        if path.is_file() and path.name != "PERTURBATION_ETL_OUTPUT_SHA256.csv":
            manifest.append({"path": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})
    pd.DataFrame(manifest).to_csv(
        out / "PERTURBATION_ETL_OUTPUT_SHA256.csv",
        index=False,
        lineterminator="\n",
    )

    print(json.dumps({
        "terminal": "PASS_PERTURBATION_ETL_METADATA_ATLAS_V1"
        if not args.require_physical else "PASS_PERTURBATION_ETL_PHYSICAL_ATLAS_V1",
        "study_count": len(studies),
        "training_ready_study_count": int(studies.all_training_ready.sum()),
        "physical_authenticated_asset_count": int(physical.physical_authenticated.sum()),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
