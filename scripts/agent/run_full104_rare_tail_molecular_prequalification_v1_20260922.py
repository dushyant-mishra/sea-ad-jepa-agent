#!/usr/bin/env python3
"""Execute the frozen FULL104 rare-tail molecular prequalification V1.

IMPORTANT: This is the molecular-outcome executor. It must not be run until its
authority/contract branch is reviewed and explicitly handed to the GPU lane.

Inputs
------
- authenticated 105,553-cell qualification sample (identity-only selection);
- authenticated FULL104 Level-4 raw-count blocks;
- frozen 104-donor source/fold receipt;
- frozen rare-tail molecular authority.

Mechanics
---------
For each of two fixed TD59 panels:
1. materialize only the 1,536 fixed Z/X/Y gene values for retained sample cells
   as log1p10K from raw counts and authenticated source_library;
2. derive exact 2,048 hashed pair-sign coordinates per view;
3. within donor x operator, Z nearest-half selects locality and q95 isolation
   tail anchors; sample <=64 tail triplets/stratum;
4. X defines the base relation, Y tests it;
5. require >=5 q95 tail anchors/donor and >=20 resolved observed X/Y triplets;
6. evaluate current source x authenticated fold cases (no new donor halves);
7. generate 64 Y-only matched wrong-cell nulls inside donor x operator
   depth/detection blocks;
8. all 24 panel x source x fold cases must PASS.

No pathology/class label is read. No teacher representation is read. Training is
never authorized by this executor.
"""
from __future__ import annotations

import argparse
from dataclasses import fields
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import scipy.sparse as sp

from sea_ad_jepa.v5.full104_rare_tail_molecular_authority_v1 import (
    FULL104_MANIFEST_SHA256,
    MIN_MEASURABLE_DONORS_PER_CASE,
    MIN_RESOLVED_TRIPLETS_PER_DONOR,
    MIN_TAIL_ANCHORS_PER_DONOR,
    NULL_REPLICATES,
    PANEL_PAIR_ADDRESS_SHA256,
    PASS_TERMINAL,
    FAIL_TERMINAL,
    NOT_ESTIMABLE_TERMINAL,
    REQUIRED_CASES,
    Full104RareTailMolecularAuthorityV1,
    case_pass,
    full_gate_terminal,
)
from sea_ad_jepa.v5.full104_rare_tail_molecular_primitives_v1 import (
    build_depth_detection_blocks,
    distance_matrix,
    matched_y_permutation,
    pair_signs,
    select_gene_views,
    select_pairs,
    select_tail_triplets,
    verify_pair_address_hash,
)
from sea_ad_jepa.v5.full104_target_qualification_sample_authority_v1 import (
    EXPECTED_SAMPLE_CELLS,
    FULL104_READER_FIT_DONORS,
    Full104TargetQualificationSampleAuthorityV1,
    Full104TargetQualificationSampleReceiptV1,
)

N_LEDGER = 41_238
EXPECTED_SOURCE_NAMES = ("HVS", "NPH52", "SEA_AD")
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


def _typed(payload: dict[str, Any], cls):
    names = {f.name for f in fields(cls)}
    missing = names - set(payload)
    if missing:
        raise ValueError(f"{cls.__name__} missing fields: {sorted(missing)}")
    return cls(**{name: payload[name] for name in names})


def _safe_under(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute():
        raise ValueError("manifest paths must be relative")
    root = root.resolve()
    path = (root / rel).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("manifest path escapes Level-4 root") from exc
    return path


def _parse_positive_integral_library(raw: object) -> int:
    token = str(raw).strip()
    try:
        value = float(token)
    except ValueError as exc:
        raise ValueError("invalid source_library") from exc
    if not np.isfinite(value) or value <= 0 or value != np.floor(value):
        raise ValueError("source_library must be a positive integer")
    return int(value)


def load_sample(sample_dir: Path) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    receipt_path = sample_dir / "sample_receipt.json"
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    if payload.get("schema") != "V5_FULL104_TARGET_QUALIFICATION_SAMPLE_RECEIPT_V1":
        raise ValueError("sample receipt schema mismatch")
    authority_payload = payload.get("authority")
    if not isinstance(authority_payload, dict):
        raise ValueError("sample receipt lacks embedded authority")
    authority = _typed(authority_payload, Full104TargetQualificationSampleAuthorityV1)
    authority.validate()
    receipt = _typed(payload, Full104TargetQualificationSampleReceiptV1)
    receipt.validate_against_authority(authority)
    if payload.get("sample_receipt_sha256") != receipt.canonical_digest():
        raise ValueError("sample receipt canonical digest mismatch")

    file_names = payload.get("file_names")
    if not isinstance(file_names, dict):
        raise ValueError("sample receipt lacks file_names")
    roles = {
        "selection_rows": (receipt.selection_rows_file_sha256, EXPECTED_SAMPLE_CELLS),
        "donor_code": (receipt.donor_code_file_sha256, EXPECTED_SAMPLE_CELLS),
        "fold_by_donor": (receipt.fold_by_donor_file_sha256, FULL104_READER_FIT_DONORS),
        "donor_source_code": (
            receipt.donor_source_code_file_sha256,
            FULL104_READER_FIT_DONORS,
        ),
    }
    arrays: dict[str, np.ndarray] = {}
    for role, (expected_sha, expected_n) in roles.items():
        name = file_names.get(role)
        if not isinstance(name, str) or not name:
            raise ValueError(f"missing sample filename for {role}")
        path = (sample_dir / name).resolve()
        path.relative_to(sample_dir.resolve())
        if sha256_file(path) != expected_sha:
            raise ValueError(f"sample array hash mismatch: {role}")
        arr = np.load(path, allow_pickle=False)
        if (
            arr.ndim != 1
            or arr.size != expected_n
            or not np.issubdtype(arr.dtype, np.integer)
        ):
            raise ValueError(f"invalid sample array geometry: {role}")
        arrays[role] = arr.astype(np.int64, copy=False)

    if np.unique(arrays["selection_rows"]).size != EXPECTED_SAMPLE_CELLS:
        raise ValueError("qualification sample selection_rows are not unique")
    if np.unique(arrays["donor_code"]).size != FULL104_READER_FIT_DONORS:
        raise ValueError("qualification sample does not contain all 104 donors")
    return payload, arrays


def load_split(split_path: Path) -> dict[str, Any]:
    payload = json.loads(split_path.read_text(encoding="utf-8"))
    if payload.get("schema") != "V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1":
        raise ValueError("split receipt schema mismatch")
    if payload.get("source_names") != list(EXPECTED_SOURCE_NAMES):
        raise ValueError("split source ordering drifted")
    if payload.get("n_folds") != 4:
        raise ValueError("split must contain exactly four folds")
    if len(payload.get("donor_ids", [])) != 104:
        raise ValueError("split must contain exactly 104 donors")
    return payload


def load_authority(path: Path) -> Full104RareTailMolecularAuthorityV1:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "V5_FULL104_RARE_TAIL_MOLECULAR_AUTHORITY_V1":
        raise ValueError("rare-tail molecular authority schema mismatch")
    authority = _typed(payload, Full104RareTailMolecularAuthorityV1)
    authority.validate()
    if payload.get("authority_sha256") != authority.canonical_digest():
        raise ValueError("rare-tail molecular authority digest mismatch")
    return authority


def load_manifest(level4_root: Path) -> list[dict[str, str]]:
    manifest = level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if sha256_file(manifest) != FULL104_MANIFEST_SHA256:
        raise ValueError("FULL104 Level-4 manifest hash mismatch")
    with manifest.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != MANIFEST_COLUMNS:
            raise ValueError("FULL104 manifest schema mismatch")
        rows = [dict(x) for x in reader]
    if not rows or len({x["block_key"] for x in rows}) != len(rows):
        raise ValueError("manifest is empty or has duplicate block keys")
    return rows


def materialize_panel(
    *,
    level4_root: Path,
    manifest_rows: list[dict[str, str]],
    selected_rows: np.ndarray,
    donor_code: np.ndarray,
    donor_id_to_code: dict[str, int],
    donor_source_code: np.ndarray,
    genes_by_view: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    """Authenticate blocks and materialize retained cells x 1536 panel values."""
    selected_index = {int(row): i for i, row in enumerate(selected_rows)}
    if len(selected_index) != selected_rows.size:
        raise ValueError("selected_rows are not unique")

    genes = np.concatenate([genes_by_view[x] for x in ("Z", "X", "Y")]).astype(
        np.int64
    )
    if genes.size != 1536 or np.unique(genes).size != genes.size:
        raise ValueError("panel must contain 1536 unique Z/X/Y addresses")
    if np.any(genes < 0) or np.any(genes >= N_LEDGER):
        raise ValueError("panel gene address out of ledger range")

    values = np.zeros((selected_rows.size, genes.size), dtype=np.float32)
    operator_code = np.full(selected_rows.size, -1, dtype=np.int16)
    source_library = np.zeros(selected_rows.size, dtype=np.int64)
    detected_count = np.zeros(selected_rows.size, dtype=np.int32)
    hits = np.zeros(selected_rows.size, dtype=np.int8)

    for entry in manifest_rows:
        op = int(entry["operator_index"])
        if op < 0 or op >= 42:
            raise ValueError("manifest operator index out of range")
        counts_path = _safe_under(level4_root, entry["counts_path"])
        meta_path = _safe_under(level4_root, entry["meta_path"])
        if sha256_file(counts_path) != entry["counts_sha256"]:
            raise ValueError(f"counts block hash mismatch: {entry['block_key']}")
        if sha256_file(meta_path) != entry["meta_sha256"]:
            raise ValueError(f"metadata block hash mismatch: {entry['block_key']}")

        matrix = sp.load_npz(counts_path).tocsr()
        if matrix.shape[1] != N_LEDGER or matrix.shape[0] != int(entry["rows"]):
            raise ValueError(f"counts geometry mismatch: {entry['block_key']}")
        if matrix.nnz != int(entry["nnz"]):
            raise ValueError(f"counts nnz mismatch: {entry['block_key']}")
        if matrix.data.size and (
            not np.all(np.isfinite(matrix.data))
            or np.any(matrix.data < 0)
            or not np.allclose(matrix.data, np.rint(matrix.data))
        ):
            raise ValueError(f"counts are not raw nonnegative integers: {entry['block_key']}")

        with meta_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != META_COLUMNS:
                raise ValueError(f"metadata schema mismatch: {entry['block_key']}")
            meta = list(reader)
        if len(meta) != matrix.shape[0]:
            raise ValueError(f"metadata row count mismatch: {entry['block_key']}")

        local_rows: list[int] = []
        out_rows: list[int] = []
        libraries: list[int] = []
        for local, row in enumerate(meta):
            selection_row = int(row["selection_row"])
            out = selected_index.get(selection_row)
            if out is None:
                continue
            if hits[out]:
                raise ValueError(f"selected row appears in multiple blocks: {selection_row}")
            donor_id = str(row["donor_id"])
            if donor_id not in donor_id_to_code:
                raise ValueError(f"unknown donor_id: {donor_id}")
            d = donor_id_to_code[donor_id]
            if int(donor_code[out]) != d:
                raise ValueError("sample donor_code disagrees with authenticated metadata")
            source_name = str(entry["source"])
            expected_source = EXPECTED_SOURCE_NAMES[int(donor_source_code[d])]
            if source_name != expected_source:
                raise ValueError("manifest source disagrees with donor source receipt")
            local_rows.append(local)
            out_rows.append(out)
            libraries.append(_parse_positive_integral_library(row["source_library"]))

        if not local_rows:
            continue

        local_ix = np.asarray(local_rows, dtype=np.int64)
        out_ix = np.asarray(out_rows, dtype=np.int64)
        libs = np.asarray(libraries, dtype=np.float64)
        sub = matrix[local_ix][:, genes].astype(np.float64).tocsr()
        dense = sub.toarray()
        dense = np.log1p(dense * (10000.0 / libs[:, None]))
        values[out_ix] = dense.astype(np.float32)
        operator_code[out_ix] = op
        source_library[out_ix] = libs.astype(np.int64)
        detected_count[out_ix] = np.diff(matrix[local_ix].indptr).astype(np.int32)
        hits[out_ix] = 1

    if np.any(hits != 1):
        raise ValueError(f"not all selected rows materialized exactly once: missing={int(np.sum(hits == 0))}")
    if set(np.unique(operator_code).tolist()) != set(range(42)):
        raise ValueError("materialized qualification sample does not represent all 42 operators")

    return {
        "values": values,
        "operator_code": operator_code.astype(np.int64),
        "source_library": source_library,
        "detected_count": detected_count.astype(np.int64),
    }


def _relation(distance: np.ndarray, i: int, j: int, k: int) -> int | None:
    a = float(distance[i, j])
    b = float(distance[i, k])
    if not np.isfinite(a) or not np.isfinite(b):
        return None
    q = int(np.sign(a - b))
    return None if q == 0 else q


def evaluate_panel(
    *,
    panel: int,
    values: np.ndarray,
    selection_rows: np.ndarray,
    donor_code: np.ndarray,
    operator_code: np.ndarray,
    source_library: np.ndarray,
    detected_count: np.ndarray,
    fold_by_donor: np.ndarray,
    source_by_donor: np.ndarray,
    genes_by_view: dict[str, np.ndarray],
) -> dict[str, Any]:
    signs: dict[str, np.ndarray] = {}
    for view_index, view in enumerate(("Z", "X", "Y")):
        genes = genes_by_view[view]
        positions, addresses = select_pairs(genes, panel=panel, view=view)
        verify_pair_address_hash(addresses, panel=panel, view=view)
        block = values[:, view_index * 512:(view_index + 1) * 512]
        signs[view] = pair_signs(block, positions)

    donor_observed: dict[int, list[bool]] = {}
    donor_tail_anchor_count: dict[int, int] = {}
    donor_triplets: dict[int, list[tuple[int, int, int, int]]] = {}
    strata_state: dict[tuple[int, int], dict[str, Any]] = {}

    # Compute fixed Z/X/Y distance geometry once per donor x operator.
    for d in range(104):
        ix_d = np.flatnonzero(donor_code == d)
        for op in sorted(set(map(int, operator_code[ix_d]))):
            ids = ix_d[operator_code[ix_d] == op]
            if ids.size < 2:
                continue
            order = np.argsort(selection_rows[ids], kind="stable")
            ids = ids[order]
            z = distance_matrix(signs["Z"][ids])
            x = distance_matrix(signs["X"][ids])
            y = distance_matrix(signs["Y"][ids])

            triplets_local = select_tail_triplets(
                z_distance=z,
                selection_rows=selection_rows[ids],
                panel=panel,
                source_code=int(source_by_donor[d]),
                fold_index=int(fold_by_donor[d]),
                donor_code=d,
                operator_code=op,
            )

            # Count q95 anchors independently from the unique anchors in sampled
            # triplets: a valid q95 anchor can have <2 candidates and therefore
            # contribute zero triplets.
            from sea_ad_jepa.v5.full104_rare_tail_molecular_primitives_v1 import (
                isolation_scores_and_candidates,
            )
            from sea_ad_jepa.v5.full104_rare_biology_preservation_authority_v1 import (
                select_q95_isolation_tail_v1,
            )
            isolation, _ = isolation_scores_and_candidates(z, selection_rows[ids])
            tail = select_q95_isolation_tail_v1(isolation, selection_rows[ids])
            donor_tail_anchor_count[d] = donor_tail_anchor_count.get(d, 0) + int(tail.size)

            base: list[tuple[int, int, int, int]] = []
            observed: list[bool] = []
            for i, j, k in triplets_local:
                qx = _relation(x, i, j, k)
                if qx is None:
                    continue
                # Store global-row positions inside this stratum plus X relation.
                base.append((i, j, k, qx))
                qy = _relation(y, i, j, k)
                if qy is not None:
                    observed.append(qx == qy)
            donor_observed.setdefault(d, []).extend(observed)

            blocks = build_depth_detection_blocks(
                selection_rows=selection_rows[ids],
                source_library=source_library[ids],
                detected_count=detected_count[ids],
            )
            strata_state[(d, op)] = {
                "ids": ids,
                "y_distance": y,
                "base": base,
                "blocks": blocks,
                "tail_anchors": int(tail.size),
            }

    donor_agreement: dict[int, float] = {}
    for d, agreements in donor_observed.items():
        if (
            donor_tail_anchor_count.get(d, 0) >= MIN_TAIL_ANCHORS_PER_DONOR
            and len(agreements) >= MIN_RESOLVED_TRIPLETS_PER_DONOR
        ):
            donor_agreement[d] = float(np.mean(agreements))

    cases: list[dict[str, Any]] = []
    for source in range(3):
        for fold in range(4):
            case_donors = [
                d
                for d in range(104)
                if int(source_by_donor[d]) == source and int(fold_by_donor[d]) == fold
            ]
            observed_donors = [d for d in case_donors if d in donor_agreement]
            if len(observed_donors) < MIN_MEASURABLE_DONORS_PER_CASE:
                cases.append({
                    "panel": panel,
                    "source_code": source,
                    "fold_index": fold,
                    "state": "NOT_ESTIMABLE",
                    "reason": "observed_measurable_donors_below_minimum",
                    "observed_measurable_donors": len(observed_donors),
                    "required_measurable_donors": MIN_MEASURABLE_DONORS_PER_CASE,
                })
                continue

            observed = float(np.median([donor_agreement[d] for d in observed_donors]))
            null_values: list[float] = []
            null_donor_counts: list[int] = []
            null_failed = False
            for q in range(NULL_REPLICATES):
                donor_null: list[float] = []
                for d in case_donors:
                    if donor_tail_anchor_count.get(d, 0) < MIN_TAIL_ANCHORS_PER_DONOR:
                        continue
                    agreements: list[bool] = []
                    for (dd, op), state in strata_state.items():
                        if dd != d:
                            continue
                        ids = state["ids"]
                        perm = matched_y_permutation(
                            n_rows=len(ids),
                            blocks=state["blocks"],
                            panel=panel,
                            q=q,
                            source_code=source,
                            fold_index=fold,
                            donor_code=d,
                            operator_code=op,
                        )
                        y = state["y_distance"]
                        for i, j, k, qx in state["base"]:
                            # Y identity is reassigned, while X relation and Z
                            # triplet identities stay fixed.
                            pi, pj, pk = int(perm[i]), int(perm[j]), int(perm[k])
                            qy = _relation(y, pi, pj, pk)
                            if qy is not None:
                                agreements.append(qx == qy)
                    if len(agreements) >= MIN_RESOLVED_TRIPLETS_PER_DONOR:
                        donor_null.append(float(np.mean(agreements)))
                if len(donor_null) < MIN_MEASURABLE_DONORS_PER_CASE:
                    null_failed = True
                    break
                null_values.append(float(np.median(donor_null)))
                null_donor_counts.append(len(donor_null))

            if null_failed or len(null_values) != NULL_REPLICATES:
                cases.append({
                    "panel": panel,
                    "source_code": source,
                    "fold_index": fold,
                    "state": "NOT_ESTIMABLE",
                    "reason": "one_or_more_null_replicates_below_donor_minimum",
                    "observed_measurable_donors": len(observed_donors),
                    "null_replicates_completed": len(null_values),
                })
                continue

            passed = case_pass(
                observed_median_donor_agreement=observed,
                null_values=tuple(null_values),
            )
            cases.append({
                "panel": panel,
                "source_code": source,
                "fold_index": fold,
                "state": "PASS" if passed else "FAIL",
                "observed_median_donor_agreement": observed,
                "observed_measurable_donors": len(observed_donors),
                "null_median": float(np.median(null_values)),
                "null_p95_index60": float(sorted(null_values)[60]),
                "null_max": float(max(null_values)),
                "null_measurable_donors_min": int(min(null_donor_counts)),
                "null_measurable_donors_max": int(max(null_donor_counts)),
            })

    if len(cases) != 12:
        raise ValueError("each panel must emit exactly 12 source x fold cases")
    return {
        "panel": panel,
        "cases": cases,
        "eligible_donor_count": len(donor_agreement),
        "donor_tail_anchor_count": {
            str(d): int(donor_tail_anchor_count.get(d, 0)) for d in range(104)
        },
        "donor_resolved_observed_triplets": {
            str(d): int(len(donor_observed.get(d, []))) for d in range(104)
        },
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--authority", type=Path, required=True)
    p.add_argument("--sample-dir", type=Path, required=True)
    p.add_argument("--split-receipt", type=Path, required=True)
    p.add_argument("--level4-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        raise SystemExit("output already exists; refuse overwrite")

    authority = load_authority(args.authority)
    sample_payload, sample = load_sample(args.sample_dir)
    split = load_split(args.split_receipt)

    if sample_payload.get("sample_receipt_sha256") != authority.sample_receipt_sha256:
        raise SystemExit("molecular authority binds a different qualification sample")
    if split.get("receipt_sha256") != authority.outer_split_receipt_sha256:
        raise SystemExit("molecular authority binds a different split receipt")

    if not np.array_equal(sample["fold_by_donor"], np.asarray(split["fold_by_donor"])):
        raise SystemExit("sample fold vector differs from authenticated split")
    if not np.array_equal(
        sample["donor_source_code"],
        np.asarray(split["donor_source_code"]),
    ):
        raise SystemExit("sample source vector differs from authenticated split")

    manifest_rows = load_manifest(args.level4_root)
    common = np.asarray(
        sorted(
            {
                int(x)
                for x in json.loads(
                    (Path("analysis/v5_full104_pass1_rebuild_20260920/evidence/full104_target_eligibility_v1.json"))
                    .read_text(encoding="utf-8")
                )["strict_core_cols"]
            }
        ),
        dtype=np.int64,
    )
    if common.size != 17_186:
        raise SystemExit("strict common-core cardinality drifted")
    donor_id_to_code = {str(x): i for i, x in enumerate(split["donor_ids"])}

    panel_results = []
    for panel in (0, 1):
        views = select_gene_views(common, panel)
        # Verify all pair-address hashes before loading expression.
        for view in ("Z", "X", "Y"):
            _, addresses = select_pairs(views[view], panel=panel, view=view)
            observed = verify_pair_address_hash(addresses, panel=panel, view=view)
            if observed != PANEL_PAIR_ADDRESS_SHA256[panel][view]:
                raise SystemExit("pair-address authority mismatch")

        materialized = materialize_panel(
            level4_root=args.level4_root,
            manifest_rows=manifest_rows,
            selected_rows=sample["selection_rows"],
            donor_code=sample["donor_code"],
            donor_id_to_code=donor_id_to_code,
            donor_source_code=sample["donor_source_code"],
            genes_by_view=views,
        )
        panel_results.append(
            evaluate_panel(
                panel=panel,
                values=materialized["values"],
                selection_rows=sample["selection_rows"],
                donor_code=sample["donor_code"],
                operator_code=materialized["operator_code"],
                source_library=materialized["source_library"],
                detected_count=materialized["detected_count"],
                fold_by_donor=sample["fold_by_donor"],
                source_by_donor=sample["donor_source_code"],
                genes_by_view=views,
            )
        )

    cases = [
        case
        for panel_result in panel_results
        for case in panel_result["cases"]
    ]
    if len(cases) != REQUIRED_CASES:
        raise SystemExit("molecular executor did not emit exactly 24 cases")
    terminal = full_gate_terminal(tuple(case["state"] for case in cases))

    payload = {
        "schema": "V5_FULL104_RARE_TAIL_MOLECULAR_RESULT_V1",
        "authority_sha256": authority.canonical_digest(),
        "sample_receipt_sha256": authority.sample_receipt_sha256,
        "full104_manifest_sha256": authority.full104_manifest_sha256,
        "outer_split_receipt_sha256": authority.outer_split_receipt_sha256,
        "panel_results": panel_results,
        "cases": cases,
        "case_count": len(cases),
        "terminal": terminal,
        "molecular_prequalification_passed": terminal == PASS_TERMINAL,
        "teacher_tail_evaluation_authorized": False,
        "td60_authorized": False,
        "training_authorized": False,
        "pathology_labels_used": False,
        "disease_labels_used": False,
        "native_class_labels_used": False,
        "rare_state_labels_used": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "terminal": terminal,
        "cases": len(cases),
        "pass_cases": sum(x["state"] == "PASS" for x in cases),
        "fail_cases": sum(x["state"] == "FAIL" for x in cases),
        "not_estimable_cases": sum(x["state"] == "NOT_ESTIMABLE" for x in cases),
        "teacher_tail_evaluation_authorized": False,
        "training_authorized": False,
    }, sort_keys=True))
    return 0 if terminal == PASS_TERMINAL else 2


if __name__ == "__main__":
    raise SystemExit(main())
