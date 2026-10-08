#!/usr/bin/env python3
"""Validate a materialized FULL104 target-qualification sample V1."""
from __future__ import annotations

import argparse
import csv
from dataclasses import fields
import hashlib
import heapq
import json
from pathlib import Path

import numpy as np

from sea_ad_jepa.v5.full104_target_qualification_sample_authority_v1 import (
    EXPECTED_DONORS_AT_CAP,
    EXPECTED_SAMPLE_CELLS,
    EXPECTED_SHORT_DONOR_CELLS,
    FULL104_READER_FIT_CELLS,
    FULL104_READER_FIT_DONORS,
    PER_DONOR_CAP,
    Full104TargetQualificationSampleAuthorityV1,
    Full104TargetQualificationSampleReceiptV1,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUILDER = ROOT / "scripts/agent/build_full104_target_qualification_sample_v1_20260921.py"

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


def _typed(payload: dict, cls):
    names = {f.name for f in fields(cls)}
    missing = names - set(payload)
    if missing:
        raise SystemExit(f"{cls.__name__} missing fields: {sorted(missing)}")
    return cls(**{name: payload[name] for name in names})


def _integer_vector(path: Path, expected_len: int, name: str) -> np.ndarray:
    x = np.load(path, allow_pickle=False)
    if x.ndim != 1 or x.size != expected_len or not np.issubdtype(x.dtype, np.integer):
        raise SystemExit(f"{name} must be a length-{expected_len} integer vector")
    return x.astype(np.int64, copy=False)




def _canonical_sha(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _safe_under(root: Path, relative: str) -> Path:
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


def _independent_priority(
    authority: Full104TargetQualificationSampleAuthorityV1,
    *,
    donor_code: int,
    selection_row: int,
) -> int:
    # Deliberately reproduce the frozen preimage here instead of calling the
    # production selector helper. The replay path is intended to detect drift in
    # the materialized package, not merely re-read its receipt.
    payload = (
        f"{authority.selection_namespace_id}|"
        f"{authority.population_authority_sha256}|"
        f"donor|{donor_code}|selection_row|{selection_row}"
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest(), "big", signed=False)


def _replay_full_source_selection(
    *,
    authority: Full104TargetQualificationSampleAuthorityV1,
    level4_root: Path,
    split_receipt: Path,
    expected_selection: np.ndarray,
    expected_donor: np.ndarray,
    expected_rank: np.ndarray,
    expected_retained: np.ndarray,
    expected_full_n: np.ndarray,
    expected_fold: np.ndarray,
    expected_source: np.ndarray,
) -> None:
    """Independently replay sample identities from authenticated metadata only."""
    manifest_path = level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if not manifest_path.is_file():
        raise SystemExit("FULL104 Level-4 block manifest is missing")
    if sha256_file(manifest_path) != authority.full104_block_manifest_sha256:
        raise SystemExit("FULL104 Level-4 block manifest hash mismatch")

    split = json.loads(split_receipt.read_text(encoding="utf-8"))
    if split.get("schema") != "V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1":
        raise SystemExit("current source-stratified FULL104 split receipt V1 is required")
    declared = str(split.get("receipt_sha256", ""))
    semantic = dict(split)
    semantic.pop("receipt_sha256", None)
    if declared != _canonical_sha(semantic):
        raise SystemExit("split receipt canonical digest mismatch")
    if declared != authority.outer_split_receipt_sha256:
        raise SystemExit("split receipt differs from sample authority")
    if split.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit("split receipt records terminal outcome access")

    donor_ids = tuple(map(str, split.get("donor_ids", ())))
    if len(donor_ids) != FULL104_READER_FIT_DONORS or len(set(donor_ids)) != len(donor_ids):
        raise SystemExit("split receipt must contain 104 unique donor IDs")
    donor_id_to_code = {donor_id: i for i, donor_id in enumerate(donor_ids)}

    source_names = tuple(map(str, split.get("source_names", ())))
    donor_source = np.asarray(split.get("donor_source_code", ()), dtype=np.int64)
    fold_by_donor = np.asarray(split.get("fold_by_donor", ()), dtype=np.int64)
    if len(source_names) != 3 or len(set(source_names)) != 3:
        raise SystemExit("split receipt must contain exactly three unique sources")
    if donor_source.shape != (FULL104_READER_FIT_DONORS,):
        raise SystemExit("split donor_source_code does not align with 104 donors")
    if fold_by_donor.shape != (FULL104_READER_FIT_DONORS,):
        raise SystemExit("split fold_by_donor does not align with 104 donors")
    if not np.array_equal(donor_source, expected_source):
        raise SystemExit("sample donor_source_code differs from authenticated split")
    if not np.array_equal(fold_by_donor, expected_fold):
        raise SystemExit("sample fold_by_donor differs from authenticated split")
    if np.any(donor_source < 0) or np.any(donor_source >= len(source_names)):
        raise SystemExit("split donor_source_code contains invalid source index")
    source_by_donor = np.asarray(
        [source_names[int(x)] for x in donor_source],
        dtype=object,
    )

    with manifest_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != MANIFEST_COLUMNS:
            raise SystemExit("FULL104 block manifest schema mismatch")
        manifest_rows = [dict(row) for row in reader]
    if not manifest_rows or len({r["block_key"] for r in manifest_rows}) != len(manifest_rows):
        raise SystemExit("FULL104 block manifest is empty or has duplicate block keys")

    seen = np.zeros(FULL104_READER_FIT_CELLS, dtype=np.bool_)
    full_n = np.zeros(FULL104_READER_FIT_DONORS, dtype=np.int64)
    heaps: list[list[tuple[int, int]]] = [
        [] for _ in range(FULL104_READER_FIT_DONORS)
    ]
    total_rows = 0

    for entry in manifest_rows:
        meta_path = _safe_under(level4_root, entry["meta_path"])
        if not meta_path.is_file():
            raise SystemExit(f"missing metadata block: {entry['block_key']}")
        if sha256_file(meta_path) != entry["meta_sha256"]:
            raise SystemExit(f"metadata block hash mismatch: {entry['block_key']}")

        block_rows = 0
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
                full_n[donor] += 1
                block_rows += 1

                priority = _independent_priority(
                    authority,
                    donor_code=donor,
                    selection_row=selection_row,
                )
                item = (-priority, -selection_row)
                heap = heaps[donor]
                if len(heap) < authority.per_donor_cap:
                    heapq.heappush(heap, item)
                elif item > heap[0]:
                    heapq.heapreplace(heap, item)

        if block_rows != int(entry["rows"]):
            raise SystemExit(f"metadata row-count mismatch: {entry['block_key']}")
        total_rows += block_rows

    if total_rows != FULL104_READER_FIT_CELLS or not np.all(seen):
        raise SystemExit("metadata replay does not close exactly over FULL104 global rows")
    if not np.array_equal(full_n, expected_full_n):
        raise SystemExit("sample full_donor_n differs from full metadata replay")

    rows_out: list[int] = []
    donors_out: list[int] = []
    ranks_out: list[int] = []
    retained = np.zeros(FULL104_READER_FIT_DONORS, dtype=np.int64)
    for donor, heap in enumerate(heaps):
        selected = sorted(
            [(-neg_priority, -neg_row) for neg_priority, neg_row in heap],
            key=lambda pair: (pair[0], pair[1]),
        )
        expected_n = min(int(full_n[donor]), authority.per_donor_cap)
        if len(selected) != expected_n:
            raise SystemExit("replay retained donor rows do not equal min(cap, donor cells)")
        retained[donor] = len(selected)
        for rank, (_, row) in enumerate(selected):
            rows_out.append(row)
            donors_out.append(donor)
            ranks_out.append(rank)

    replay_selection = np.asarray(rows_out, dtype=np.int64)
    replay_donor = np.asarray(donors_out, dtype=np.int64)
    replay_rank = np.asarray(ranks_out, dtype=np.int64)
    if not np.array_equal(replay_selection, expected_selection):
        raise SystemExit("materialized selection_rows differ from full metadata replay")
    if not np.array_equal(replay_donor, expected_donor):
        raise SystemExit("materialized donor_code differs from full metadata replay")
    if not np.array_equal(replay_rank, expected_rank):
        raise SystemExit("materialized row_rank differs from full metadata replay")
    if not np.array_equal(retained, expected_retained):
        raise SystemExit("materialized retained_count_by_donor differs from full metadata replay")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sample-dir", type=Path, required=True)
    p.add_argument("--builder-source", type=Path, default=DEFAULT_BUILDER)
    p.add_argument(
        "--level4-root",
        type=Path,
        default=None,
        help="Optional authenticated Level-4 root for independent metadata-only replay.",
    )
    p.add_argument(
        "--split-receipt",
        type=Path,
        default=None,
        help="Required with --level4-root; current source-stratified split receipt.",
    )
    args = p.parse_args()

    receipt_path = args.sample_dir / "sample_receipt.json"
    if not receipt_path.is_file():
        raise SystemExit("sample_receipt.json is missing")
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    if payload.get("schema") != "V5_FULL104_TARGET_QUALIFICATION_SAMPLE_RECEIPT_V1":
        raise SystemExit("sample receipt schema mismatch")

    authority_payload = payload.get("authority")
    if not isinstance(authority_payload, dict):
        raise SystemExit("sample receipt lacks embedded authority")
    authority = _typed(authority_payload, Full104TargetQualificationSampleAuthorityV1)
    authority.validate()

    receipt = _typed(payload, Full104TargetQualificationSampleReceiptV1)
    receipt.validate_against_authority(authority)
    if payload.get("sample_receipt_sha256") != receipt.canonical_digest():
        raise SystemExit("sample receipt canonical digest mismatch")

    if not args.builder_source.is_file():
        raise SystemExit("bound builder source is unavailable")
    if sha256_file(args.builder_source) != receipt.builder_source_sha256:
        raise SystemExit("builder source hash mismatch")

    names = payload.get("file_names")
    if not isinstance(names, dict):
        raise SystemExit("sample receipt lacks file_names")

    role_to_sha = {
        "selection_rows": receipt.selection_rows_file_sha256,
        "donor_code": receipt.donor_code_file_sha256,
        "row_rank": receipt.row_rank_file_sha256,
        "retained_count_by_donor": receipt.retained_count_by_donor_file_sha256,
        "full_donor_n": receipt.full_donor_n_file_sha256,
        "fold_by_donor": receipt.fold_by_donor_file_sha256,
        "donor_source_code": receipt.donor_source_code_file_sha256,
    }
    paths: dict[str, Path] = {}
    for role, expected_sha in role_to_sha.items():
        file_name = names.get(role)
        if not isinstance(file_name, str) or not file_name:
            raise SystemExit(f"sample receipt missing filename for {role}")
        path = (args.sample_dir / file_name).resolve()
        try:
            path.relative_to(args.sample_dir.resolve())
        except ValueError as exc:
            raise SystemExit(f"sample filename escapes sample directory: {role}") from exc
        if not path.is_file():
            raise SystemExit(f"sample file missing: {role}")
        if sha256_file(path) != expected_sha:
            raise SystemExit(f"sample file hash mismatch: {role}")
        paths[role] = path

    selection = _integer_vector(
        paths["selection_rows"], EXPECTED_SAMPLE_CELLS, "selection_rows"
    )
    donor = _integer_vector(paths["donor_code"], EXPECTED_SAMPLE_CELLS, "donor_code")
    rank = _integer_vector(paths["row_rank"], EXPECTED_SAMPLE_CELLS, "row_rank")
    retained = _integer_vector(
        paths["retained_count_by_donor"],
        FULL104_READER_FIT_DONORS,
        "retained_count_by_donor",
    )
    full_n = _integer_vector(
        paths["full_donor_n"], FULL104_READER_FIT_DONORS, "full_donor_n"
    )
    fold = _integer_vector(
        paths["fold_by_donor"], FULL104_READER_FIT_DONORS, "fold_by_donor"
    )
    source = _integer_vector(
        paths["donor_source_code"], FULL104_READER_FIT_DONORS, "donor_source_code"
    )

    if np.any(selection < 0) or np.any(selection >= FULL104_READER_FIT_CELLS):
        raise SystemExit("selection_rows contain out-of-range FULL104 identities")
    if np.unique(selection).size != selection.size:
        raise SystemExit("selection_rows are not globally unique")
    if np.any(donor < 0) or np.any(donor >= FULL104_READER_FIT_DONORS):
        raise SystemExit("donor_code contains invalid donor")
    if np.any(rank < 0):
        raise SystemExit("row_rank contains negative rank")

    observed_retained = np.bincount(donor, minlength=FULL104_READER_FIT_DONORS)
    if not np.array_equal(observed_retained, retained):
        raise SystemExit("retained_count_by_donor disagrees with donor_code")
    if int(np.sum(retained == PER_DONOR_CAP)) != EXPECTED_DONORS_AT_CAP:
        raise SystemExit("donors-at-cap geometry mismatch")
    if retained.min() != EXPECTED_SHORT_DONOR_CELLS or retained.max() != PER_DONOR_CAP:
        raise SystemExit("retained donor min/max geometry mismatch")

    if np.any(full_n < retained) or int(full_n.sum()) != FULL104_READER_FIT_CELLS:
        raise SystemExit("full_donor_n is inconsistent with FULL104 population")
    if int(np.sum(full_n >= PER_DONOR_CAP)) != EXPECTED_DONORS_AT_CAP:
        raise SystemExit("full donor cap geometry mismatch")
    if full_n.min() != EXPECTED_SHORT_DONOR_CELLS:
        raise SystemExit("full donor minimum geometry mismatch")

    if np.any(fold < 0) or np.any(fold >= 4):
        raise SystemExit("fold_by_donor contains invalid fold")
    if np.any(source < 0) or np.unique(source).size != 3:
        raise SystemExit("donor_source_code must encode exactly three sources")

    for d in range(FULL104_READER_FIT_DONORS):
        ix = np.flatnonzero(donor == d)
        if ix.size != retained[d]:
            raise SystemExit(f"donor {d}: retained count mismatch")
        donor_ranks = np.sort(rank[ix])
        if not np.array_equal(donor_ranks, np.arange(ix.size, dtype=np.int64)):
            raise SystemExit(f"donor {d}: row_rank is not contiguous from zero")

    if (args.level4_root is None) != (args.split_receipt is None):
        raise SystemExit("--level4-root and --split-receipt must be supplied together")
    full_source_replay = args.level4_root is not None
    if full_source_replay:
        _replay_full_source_selection(
            authority=authority,
            level4_root=args.level4_root,
            split_receipt=args.split_receipt,
            expected_selection=selection,
            expected_donor=donor,
            expected_rank=rank,
            expected_retained=retained,
            expected_full_n=full_n,
            expected_fold=fold,
            expected_source=source,
        )

    print(
        json.dumps(
            {
                "status": "PASS_FULL104_TARGET_QUALIFICATION_SAMPLE_V1",
                "sample_receipt_sha256": receipt.canonical_digest(),
                "retained_cells": int(selection.size),
                "retained_donors": FULL104_READER_FIT_DONORS,
                "full_source_replay": bool(full_source_replay),
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
