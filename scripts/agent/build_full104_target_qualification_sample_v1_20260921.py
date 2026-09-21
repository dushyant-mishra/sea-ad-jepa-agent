#!/usr/bin/env python3
"""Build the expression-blind FULL104 target-qualification sample V1.

This builder authenticates the Level-4 manifest and every metadata block, but it
never opens expression/count arrays. It selects <=1024 rows per donor using only
global selection_row + donor code under a dedicated target-qualification
namespace, then writes identity arrays and a content-addressed receipt.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

import numpy as np

from sea_ad_jepa.v5.full104_target_qualification_sample_authority_v1 import (
    EXPECTED_SAMPLE_CELLS,
    FULL104_READER_FIT_CELLS,
    FULL104_READER_FIT_DONORS,
    Full104TargetQualificationSampleAuthorityV1,
    Full104TargetQualificationSampleReceiptV1,
    RetainedQualificationRowSelectorV1,
)


EXPECTED_BLOCK_MANIFEST_SHA256 = (
    "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
)
EXPECTED_POPULATION_AUTHORITY_SHA256 = (
    "a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"
)
MANIFEST_COLUMNS = (
    "block_key",
    "source",
    "operator_index",
    "matrix_id",
    "rows",
    "nnz",
    "counts_path",
    "counts_sha256",
    "meta_path",
    "meta_sha256",
)
META_COLUMNS = (
    "selection_row",
    "canonical_cell_id",
    "donor_id",
    "expression_row",
    "primary_row_weight",
    "source_library",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def safe_under(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute():
        raise SystemExit("manifest metadata path must be relative")
    root_resolved = root.resolve()
    path = (root_resolved / rel).resolve()
    try:
        path.relative_to(root_resolved)
    except ValueError as exc:
        raise SystemExit("manifest metadata path escapes Level-4 root") from exc
    return path


def load_split(path: Path) -> tuple[dict, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1":
        raise SystemExit("current source-stratified FULL104 split receipt V1 is required")
    declared = str(payload.get("receipt_sha256", ""))
    semantic = dict(payload)
    semantic.pop("receipt_sha256", None)
    observed = canonical_sha(semantic)
    if declared != observed:
        raise SystemExit("split receipt canonical digest mismatch")
    if payload.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit("split receipt records terminal outcome access")
    if len(payload.get("donor_ids", ())) != FULL104_READER_FIT_DONORS:
        raise SystemExit("split receipt must contain 104 donors")
    if int(payload.get("n_folds", 0)) != 4:
        raise SystemExit("split receipt must contain four folds")
    return payload, observed


def load_etl_atlas(path: Path) -> tuple[dict, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "FULL104_DATASET_ETL_ATLAS_V3":
        raise SystemExit("FULL104 ETL atlas V3 is required")
    pop = payload.get("population", {})
    if int(pop.get("reader_fit_cells", -1)) != FULL104_READER_FIT_CELLS:
        raise SystemExit("ETL atlas reader-fit cell count mismatch")
    if int(pop.get("reader_fit_donors", -1)) != FULL104_READER_FIT_DONORS:
        raise SystemExit("ETL atlas reader-fit donor count mismatch")
    meta = payload.get("verified_inputs", {}).get("metadata/foundation_metadata_rows.sqlite", {})
    if meta.get("sha256") != EXPECTED_POPULATION_AUTHORITY_SHA256:
        raise SystemExit("ETL atlas binds a different population metadata authority")
    protected = payload.get("protected_state", {})
    if protected.get("training") != "OFF":
        raise SystemExit("ETL atlas does not preserve training-off state")
    return payload, sha256_file(path)


def save_npy(path: Path, value: np.ndarray) -> str:
    np.save(path, value, allow_pickle=False)
    return sha256_file(path)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--level4-root", type=Path, required=True)
    p.add_argument("--split-receipt", type=Path, required=True)
    p.add_argument("--etl-atlas-summary", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    args = p.parse_args()

    if args.out_dir.exists():
        raise SystemExit("output directory already exists; refuse overwrite/mixing")
    args.out_dir.parent.mkdir(parents=True, exist_ok=True)

    manifest_path = args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if sha256_file(manifest_path) != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise SystemExit("FULL104 Level-4 block manifest hash mismatch")

    split, split_root = load_split(args.split_receipt)
    _, etl_sha = load_etl_atlas(args.etl_atlas_summary)

    donor_ids = tuple(map(str, split["donor_ids"]))
    donor_id_to_code = {x: i for i, x in enumerate(donor_ids)}
    if len(donor_id_to_code) != FULL104_READER_FIT_DONORS:
        raise SystemExit("split donor identifiers are not unique")

    source_names = tuple(map(str, split["source_names"]))
    donor_source_code = np.asarray(split["donor_source_code"], dtype=np.int64)
    fold_by_donor = np.asarray(split["fold_by_donor"], dtype=np.int64)
    if donor_source_code.shape != (FULL104_READER_FIT_DONORS,):
        raise SystemExit("donor_source_code does not align with 104 donors")
    if fold_by_donor.shape != (FULL104_READER_FIT_DONORS,):
        raise SystemExit("fold_by_donor does not align with 104 donors")
    if np.any(fold_by_donor < 0) or np.any(fold_by_donor >= 4):
        raise SystemExit("fold_by_donor contains invalid fold index")
    if np.any(donor_source_code < 0) or np.any(donor_source_code >= len(source_names)):
        raise SystemExit("donor_source_code contains invalid source index")
    source_by_donor = np.asarray(
        [source_names[int(x)] for x in donor_source_code],
        dtype=object,
    )

    authority = Full104TargetQualificationSampleAuthorityV1(
        authority_id="JEPA_V5_FULL104_TARGET_QUALIFICATION_SAMPLE_AUTHORITY_V1",
        population_authority_sha256=EXPECTED_POPULATION_AUTHORITY_SHA256,
        full104_block_manifest_sha256=EXPECTED_BLOCK_MANIFEST_SHA256,
        dataset_etl_atlas_sha256=etl_sha,
        outer_split_receipt_sha256=split_root,
    )
    authority.validate()
    selector = RetainedQualificationRowSelectorV1(authority)

    with manifest_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != MANIFEST_COLUMNS:
            raise SystemExit("FULL104 block manifest schema mismatch")
        manifest_rows = [dict(row) for row in reader]
    if not manifest_rows or len({r["block_key"] for r in manifest_rows}) != len(manifest_rows):
        raise SystemExit("FULL104 block manifest is empty or has duplicate block keys")

    seen = np.zeros(FULL104_READER_FIT_CELLS, dtype=np.bool_)
    observed_donor_n = np.zeros(FULL104_READER_FIT_DONORS, dtype=np.int64)
    total_rows = 0

    for entry in manifest_rows:
        meta_path = safe_under(args.level4_root, entry["meta_path"])
        if not meta_path.is_file():
            raise SystemExit(f"missing metadata block: {entry['block_key']}")
        if sha256_file(meta_path) != entry["meta_sha256"]:
            raise SystemExit(f"metadata block hash mismatch: {entry['block_key']}")

        rows: list[int] = []
        donors: list[int] = []
        with meta_path.open(newline="", encoding="utf-8") as mh:
            mr = csv.DictReader(mh)
            if tuple(mr.fieldnames or ()) != META_COLUMNS:
                raise SystemExit(f"metadata schema mismatch: {entry['block_key']}")
            for row in mr:
                selection_row = int(row["selection_row"])
                donor_id = str(row["donor_id"])
                if donor_id not in donor_id_to_code:
                    raise SystemExit(f"unknown donor in metadata: {donor_id!r}")
                donor = donor_id_to_code[donor_id]
                if source_by_donor[donor] != entry["source"]:
                    raise SystemExit(
                        f"donor/source mismatch in {entry['block_key']}: "
                        f"{donor_id!r} belongs to {source_by_donor[donor]!r}, "
                        f"manifest says {entry['source']!r}"
                    )
                if selection_row < 0 or selection_row >= FULL104_READER_FIT_CELLS:
                    raise SystemExit("metadata selection_row outside FULL104 range")
                if seen[selection_row]:
                    raise SystemExit("duplicate global selection_row in FULL104 metadata")
                seen[selection_row] = True
                rows.append(selection_row)
                donors.append(donor)
                observed_donor_n[donor] += 1

        if len(rows) != int(entry["rows"]):
            raise SystemExit(f"metadata row-count mismatch: {entry['block_key']}")
        total_rows += len(rows)
        selector.update(
            np.asarray(rows, dtype=np.int64),
            np.asarray(donors, dtype=np.int64),
        )

    if total_rows != FULL104_READER_FIT_CELLS or not np.all(seen):
        raise SystemExit("metadata traversal does not close exactly over 4,553,407 global rows")
    if np.any(observed_donor_n <= 0):
        raise SystemExit("metadata traversal missed one or more authorized donors")

    selection_rows, donor_code, row_rank, retained = selector.finalize()
    if selection_rows.size != EXPECTED_SAMPLE_CELLS:
        raise SystemExit("target-qualification sample size mismatch")

    tmp = Path(
        tempfile.mkdtemp(prefix=args.out_dir.name + ".tmp.", dir=str(args.out_dir.parent))
    )
    try:
        file_sha = {
            "selection_rows": save_npy(tmp / "selection_rows_i64.npy", selection_rows),
            "donor_code": save_npy(tmp / "donor_code_i64.npy", donor_code),
            "row_rank": save_npy(tmp / "row_rank_i64.npy", row_rank),
            "retained_count_by_donor": save_npy(
                tmp / "retained_count_by_donor_i64.npy", retained
            ),
            "full_donor_n": save_npy(tmp / "full_donor_n_i64.npy", observed_donor_n),
            "fold_by_donor": save_npy(tmp / "fold_by_donor_i64.npy", fold_by_donor),
            "donor_source_code": save_npy(
                tmp / "donor_source_code_i64.npy", donor_source_code
            ),
        }
        receipt = Full104TargetQualificationSampleReceiptV1(
            sample_authority_sha256=authority.canonical_digest(),
            full104_block_manifest_sha256=EXPECTED_BLOCK_MANIFEST_SHA256,
            population_authority_sha256=EXPECTED_POPULATION_AUTHORITY_SHA256,
            dataset_etl_atlas_sha256=etl_sha,
            outer_split_receipt_sha256=split_root,
            retained_cells=int(selection_rows.size),
            retained_donors=FULL104_READER_FIT_DONORS,
            donors_at_cap=int(np.sum(retained == authority.per_donor_cap)),
            min_retained_per_donor=int(retained.min()),
            max_retained_per_donor=int(retained.max()),
            selection_rows_file_sha256=file_sha["selection_rows"],
            donor_code_file_sha256=file_sha["donor_code"],
            row_rank_file_sha256=file_sha["row_rank"],
            retained_count_by_donor_file_sha256=file_sha["retained_count_by_donor"],
            full_donor_n_file_sha256=file_sha["full_donor_n"],
            fold_by_donor_file_sha256=file_sha["fold_by_donor"],
            donor_source_code_file_sha256=file_sha["donor_source_code"],
        )
        receipt.validate_against_authority(authority)
        manifest = {
            "schema": "V5_FULL104_TARGET_QUALIFICATION_SAMPLE_RECEIPT_V1",
            **receipt.__dict__,
            "sample_receipt_sha256": receipt.canonical_digest(),
            "authority": authority.__dict__,
            "file_names": {
                "selection_rows": "selection_rows_i64.npy",
                "donor_code": "donor_code_i64.npy",
                "row_rank": "row_rank_i64.npy",
                "retained_count_by_donor": "retained_count_by_donor_i64.npy",
                "full_donor_n": "full_donor_n_i64.npy",
                "fold_by_donor": "fold_by_donor_i64.npy",
                "donor_source_code": "donor_source_code_i64.npy",
            },
            "selection_inputs": [
                "global_selection_row",
                "donor_code",
                "frozen_population_root",
                "frozen_selection_namespace",
            ],
        }
        (tmp / "sample_receipt.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, args.out_dir)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise

    print(
        json.dumps(
            {
                "status": "FULL104_TARGET_QUALIFICATION_SAMPLE_BUILT",
                "rows": EXPECTED_SAMPLE_CELLS,
                "expression_opened": False,
                "masking_authorized": False,
                "training_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
