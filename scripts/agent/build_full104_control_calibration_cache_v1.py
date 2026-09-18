#!/usr/bin/env python3
"""Build the outcome-blind FULL104 control-calibration cache V1."""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import shutil
import tempfile

import numpy as np

from sea_ad_jepa.v5.full104_census_receipt_v2 import canonical_sha, sha256_file
from sea_ad_jepa.v5.full104_control_calibration_cache_v1 import (
    CACHE_ROLE_ID,
    DISTRACTOR_COUNT,
    DISTRACTOR_NAMESPACE,
    EXPECTED_DONOR_COUNT,
    Full104ControlCalibrationCacheManifestV1,
    MAX_ROWS_PER_DONOR,
    MAX_TARGET_COUNT,
    NORMALIZATION_ID,
    RetainedRowSelectorV1,
    ROW_SELECTION_NAMESPACE,
    SOURCE_SUBSTRATE_ROLE_ID,
    X_DTYPE_ID,
    select_calibration_columns,
    vector_digest,
)
from sea_ad_jepa.v5.full104_masking_streaming_executor_v1 import Full104ManifestStreamV1
from sea_ad_jepa.v5.target_panel_selector_v2 import select_target_cols

EXPECTED_BLOCK_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_REGISTRY_SHA256 = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
EXPECTED_REGISTRY_ROWS = 41238
EXPECTED_CELLS = 4553407
EXPECTED_ELIGIBLE_TARGETS = 17053


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require_receipt(payload: dict, schema: str, path: Path) -> str:
    if payload.get("schema") != schema:
        raise SystemExit(f"{path}: expected schema {schema}")
    declared = payload.get("receipt_sha256")
    semantic = dict(payload)
    semantic.pop("receipt_sha256", None)
    if declared != canonical_sha(semantic):
        raise SystemExit(f"{path}: receipt digest mismatch")
    if payload.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit(f"{path}: terminal masking outcomes must remain unopened")
    return str(declared)


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


def load_registry(path: Path) -> np.ndarray:
    if sha256_file(path) != EXPECTED_REGISTRY_SHA256:
        raise SystemExit("canonical molecular-address registry hash mismatch")
    indices: list[int] = []
    ids: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        names = set(reader.fieldnames or ())
        if not {"molecular_address_index", "molecular_address_id"}.issubset(names):
            raise SystemExit("canonical registry lacks model-facing identity fields")
        for row in reader:
            indices.append(int(row["molecular_address_index"]))
            ids.append(str(row["molecular_address_id"]))
    if len(indices) != EXPECTED_REGISTRY_ROWS:
        raise SystemExit("canonical registry row count mismatch")
    if indices != list(range(EXPECTED_REGISTRY_ROWS)):
        raise SystemExit("canonical registry ordering invariant failed")
    if len(set(ids)) != len(ids) or any(not item for item in ids):
        raise SystemExit("canonical registry identifier invariant failed")
    return np.asarray(ids, dtype=object)


def save_npy(path: Path, value: np.ndarray) -> str:
    np.save(path, value, allow_pickle=False)
    return sha256_file(path)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--level4-root", type=Path, required=True)
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--census-authority", type=Path, required=True)
    p.add_argument("--split-receipt", type=Path, required=True)
    p.add_argument("--target-eligibility", type=Path, required=True)
    p.add_argument("--support-authority", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    args = p.parse_args()

    if args.out_dir.exists():
        raise SystemExit("output directory already exists; refuse to mix or overwrite calibration artifacts")
    args.out_dir.parent.mkdir(parents=True, exist_ok=True)

    manifest_path = args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    manifest_sha = sha256_file(manifest_path)
    if manifest_sha != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise SystemExit("FULL104 Level-4 block manifest hash mismatch")

    registry_ids = load_registry(args.registry)

    census = load_json(args.census_authority)
    if census.get("schema") != "V5_FULL104_READONLY_CENSUS_AUTHORITY_V2":
        raise SystemExit("census V2 authority is required")
    census_root = str(census.get("census_authority_sha256", ""))
    semantic_census = dict(census)
    semantic_census.pop("census_authority_sha256", None)
    if census_root != canonical_sha(semantic_census):
        raise SystemExit("census V2 canonical digest mismatch")
    if census.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit("census authority records terminal masking outcome access")
    if census.get("substrate", {}).get("full104_block_manifest_sha256") != manifest_sha:
        raise SystemExit("census authority is bound to a different FULL104 substrate")

    split = load_json(args.split_receipt)
    split_root = require_receipt(
        split, "V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1", args.split_receipt
    )
    eligibility = load_json(args.target_eligibility)
    eligibility_root = require_receipt(
        eligibility, "V5_FULL104_TARGET_ELIGIBILITY_RECEIPT_V1", args.target_eligibility
    )
    receipts = census.get("execution_receipts", {})
    if receipts.get("split_receipt_sha256") != split_root:
        raise SystemExit("census authority is bound to a different donor split")
    if receipts.get("target_eligibility_receipt_sha256") != eligibility_root:
        raise SystemExit("census authority is bound to a different target-eligibility receipt")
    if eligibility.get("split_receipt_sha256") != split_root:
        raise SystemExit("target eligibility is bound to a different donor split")

    support = load_json(args.support_authority)
    support_sha = sha256_file(args.support_authority)
    if support.get("schema") != "V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1":
        raise SystemExit("support authority schema mismatch")
    if support.get("full104_substrate_sha256") != manifest_sha:
        raise SystemExit("support authority is bound to a different FULL104 substrate")
    if support.get("training_authorized") is not False:
        raise SystemExit("support authority unexpectedly authorizes training")
    if census.get("support_estimability_authority", {}).get("sha256") != support_sha:
        raise SystemExit("census authority is bound to a different support authority")

    eligible_cols = np.asarray(eligibility["eligible_target_cols_all_folds"], dtype=np.int64)
    strict_core = np.asarray(eligibility["strict_core_cols"], dtype=np.int64)
    if eligible_cols.size != EXPECTED_ELIGIBLE_TARGETS:
        raise SystemExit("current eligible target count is not 17,053")
    if strict_core.size != 17186:
        raise SystemExit("terminal strict common core is not 17,186 addresses")

    target_cols = select_target_cols(
        eligible_cols,
        target_count=MAX_TARGET_COUNT,
        eligibility_receipt_sha256=eligibility_root,
    )
    target_ids = tuple(str(registry_ids[int(col)]) for col in target_cols)
    column_plan = select_calibration_columns(
        eligible_cols=eligible_cols,
        target_cols=target_cols,
        target_ids=target_ids,
        target_eligibility_receipt_sha256=eligibility_root,
    )
    cache_cols = np.asarray(column_plan["cache_cols"], dtype=np.int64)

    donor_ids = tuple(map(str, split["donor_ids"]))
    donor_source_code = np.asarray(split["donor_source_code"], dtype=np.int64)
    source_names = tuple(map(str, split["source_names"]))
    fold_by_donor = np.asarray(split["fold_by_donor"], dtype=np.int64)
    if len(donor_ids) != EXPECTED_DONOR_COUNT:
        raise SystemExit("donor split does not contain exactly 104 donors")
    if donor_source_code.shape != (EXPECTED_DONOR_COUNT,) or fold_by_donor.shape != (EXPECTED_DONOR_COUNT,):
        raise SystemExit("donor split vectors do not align with 104 donors")
    donor_id_to_code = {donor_id: i for i, donor_id in enumerate(donor_ids)}
    source_by_donor = np.asarray([source_names[int(code)] for code in donor_source_code], dtype=object)

    stream = Full104ManifestStreamV1(
        manifest_path=manifest_path,
        block_root=args.level4_root,
        expected_manifest_sha256=manifest_sha,
        donor_id_to_code=donor_id_to_code,
        source_by_donor=source_by_donor,
        fold_by_donor=fold_by_donor,
        universe_cols=strict_core,
        target_cols=np.asarray(target_cols, dtype=np.int64),
        target_ids=np.asarray(target_ids, dtype=object),
        expected_cell_count=EXPECTED_CELLS,
        verify_block_hashes=True,
    )
    # This authenticates every counts block, every metadata block, raw-count
    # semantics, selection-row closure, donor/source binding, and geometry.
    stream.validate_layout()

    selector = RetainedRowSelectorV1(
        full104_manifest_sha256=manifest_sha,
        donor_count=EXPECTED_DONOR_COUNT,
        max_rows_per_donor=MAX_ROWS_PER_DONOR,
    )
    for row in stream._load_manifest():
        meta_path = safe_under(args.level4_root, row["meta_path"])
        selection, block_donor_ids, _, _, _ = stream._read_meta(meta_path)
        codes = np.asarray([donor_id_to_code[item] for item in block_donor_ids], dtype=np.int64)
        selector.update(selection, codes)
    selection_rows, donor_code, row_rank, retained_counts = selector.finalize()

    tmp = Path(
        tempfile.mkdtemp(
            prefix=args.out_dir.name + ".tmp.",
            dir=str(args.out_dir.parent),
        )
    )
    try:
        x_path = tmp / "X_log1p10k_f32.npy"
        X = np.lib.format.open_memmap(
            x_path,
            mode="w+",
            dtype=np.float32,
            shape=(selection_rows.size, cache_cols.size),
        )
        sorted_order = np.argsort(selection_rows)
        sorted_rows = selection_rows[sorted_order]
        seen = np.zeros(selection_rows.size, dtype=np.bool_)
        full_donor_n = np.zeros(EXPECTED_DONOR_COUNT, dtype=np.int64)
        full_donor_sum = np.zeros((EXPECTED_DONOR_COUNT, cache_cols.size), dtype=np.float64)
        full_donor_sumsq = np.zeros((EXPECTED_DONOR_COUNT, cache_cols.size), dtype=np.float64)
        for block in stream.iter_blocks(columns=cache_cols):
            rows = np.asarray(block.selection_rows, dtype=np.int64)
            block_donors = np.asarray(block.donor_code, dtype=np.int64)
            for donor in np.unique(block_donors):
                ix = block_donors == int(donor)
                local_all = block.X[ix].tocsr()
                full_donor_n[int(donor)] += int(local_all.shape[0])
                full_donor_sum[int(donor)] += np.asarray(local_all.sum(axis=0)).reshape(-1)
                full_donor_sumsq[int(donor)] += np.asarray(local_all.power(2).sum(axis=0)).reshape(-1)
            pos = np.searchsorted(sorted_rows, rows)
            valid = pos < sorted_rows.size
            safe_pos = np.minimum(pos, max(sorted_rows.size - 1, 0))
            valid &= sorted_rows[safe_pos] == rows
            if not np.any(valid):
                continue
            dest = sorted_order[pos[valid]]
            if np.any(seen[dest]):
                raise SystemExit("duplicate retained selection row during cache materialization")
            local = block.X[valid].toarray().astype(np.float32, copy=False)
            X[dest, :] = local
            seen[dest] = True
        X.flush()
        del X
        if not np.all(seen):
            raise SystemExit("cache materialization did not close over every selected row")
        if int(full_donor_n.sum()) != EXPECTED_CELLS or np.any(full_donor_n <= 0):
            raise SystemExit("full-donor sufficient statistics do not close over 4,553,407 cells")

        file_sha: dict[str, str] = {"x": sha256_file(x_path)}
        arrays = {
            "selection_rows_i64.npy": selection_rows.astype(np.int64, copy=False),
            "donor_code_i64.npy": donor_code.astype(np.int64, copy=False),
            "row_rank_i64.npy": row_rank.astype(np.int64, copy=False),
            "retained_count_by_donor_i64.npy": retained_counts.astype(np.int64, copy=False),
            "fold_by_donor_i64.npy": fold_by_donor.astype(np.int64, copy=False),
            "donor_source_code_i64.npy": donor_source_code.astype(np.int64, copy=False),
            "full_donor_n_i64.npy": full_donor_n,
            "full_donor_sum_f64.npy": full_donor_sum,
            "full_donor_sumsq_f64.npy": full_donor_sumsq,
            "target_cols_i64.npy": np.asarray(column_plan["target_cols"], dtype=np.int64),
            "proxy_cols_i64.npy": np.asarray(column_plan["proxy_cols"], dtype=np.int64),
            "distractor_cols_i64.npy": np.asarray(column_plan["distractor_cols"], dtype=np.int64),
            "cache_cols_i64.npy": cache_cols,
        }
        for name, value in arrays.items():
            file_sha[name] = save_npy(tmp / name, value)

        target_ids_path = tmp / "target_ids.json"
        target_ids_path.write_text(
            json.dumps(list(target_ids), ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        file_sha["target_ids.json"] = sha256_file(target_ids_path)

        manifest = Full104ControlCalibrationCacheManifestV1(
            authority_id="JEPA_V5_FULL104_CONTROL_CALIBRATION_CACHE_V1",
            cache_role_id=CACHE_ROLE_ID,
            source_substrate_role_id=SOURCE_SUBSTRATE_ROLE_ID,
            normalization_id=NORMALIZATION_ID,
            x_dtype_id=X_DTYPE_ID,
            full104_block_manifest_sha256=manifest_sha,
            canonical_registry_sha256=EXPECTED_REGISTRY_SHA256,
            census_authority_sha256=census_root,
            support_estimability_authority_sha256=support_sha,
            split_receipt_sha256=split_root,
            target_eligibility_receipt_sha256=eligibility_root,
            row_selection_namespace=ROW_SELECTION_NAMESPACE,
            distractor_namespace=DISTRACTOR_NAMESPACE,
            max_rows_per_donor=MAX_ROWS_PER_DONOR,
            max_target_count=MAX_TARGET_COUNT,
            distractor_count=DISTRACTOR_COUNT,
            retained_row_count=int(selection_rows.size),
            retained_donor_count=EXPECTED_DONOR_COUNT,
            min_retained_rows_per_donor=int(retained_counts.min()),
            max_retained_rows_observed_per_donor=int(retained_counts.max()),
            cache_column_count=int(cache_cols.size),
            x_shape_rows=int(selection_rows.size),
            x_shape_cols=int(cache_cols.size),
            target_cols_semantic_sha256=vector_digest(column_plan["target_cols"]),
            target_ids_semantic_sha256=vector_digest(target_ids),
            proxy_cols_semantic_sha256=vector_digest(column_plan["proxy_cols"]),
            distractor_cols_semantic_sha256=vector_digest(column_plan["distractor_cols"]),
            cache_cols_semantic_sha256=vector_digest(column_plan["cache_cols"]),
            x_file_sha256=file_sha["x"],
            selection_rows_file_sha256=file_sha["selection_rows_i64.npy"],
            donor_code_file_sha256=file_sha["donor_code_i64.npy"],
            row_rank_file_sha256=file_sha["row_rank_i64.npy"],
            retained_count_by_donor_file_sha256=file_sha["retained_count_by_donor_i64.npy"],
            fold_by_donor_file_sha256=file_sha["fold_by_donor_i64.npy"],
            donor_source_code_file_sha256=file_sha["donor_source_code_i64.npy"],
            full_donor_n_file_sha256=file_sha["full_donor_n_i64.npy"],
            full_donor_sum_file_sha256=file_sha["full_donor_sum_f64.npy"],
            full_donor_sumsq_file_sha256=file_sha["full_donor_sumsq_f64.npy"],
            target_cols_file_sha256=file_sha["target_cols_i64.npy"],
            proxy_cols_file_sha256=file_sha["proxy_cols_i64.npy"],
            distractor_cols_file_sha256=file_sha["distractor_cols_i64.npy"],
            cache_cols_file_sha256=file_sha["cache_cols_i64.npy"],
            target_ids_file_sha256=file_sha["target_ids.json"],
        )
        manifest.validate()
        payload = {
            "schema": "V5_FULL104_CONTROL_CALIBRATION_CACHE_MANIFEST_V1",
            **manifest.__dict__,
            "cache_manifest_sha256": manifest.canonical_digest(),
            "file_names": {
                "x": "X_log1p10k_f32.npy",
                "selection_rows": "selection_rows_i64.npy",
                "donor_code": "donor_code_i64.npy",
                "row_rank": "row_rank_i64.npy",
                "retained_count_by_donor": "retained_count_by_donor_i64.npy",
                "fold_by_donor": "fold_by_donor_i64.npy",
                "donor_source_code": "donor_source_code_i64.npy",
                "full_donor_n": "full_donor_n_i64.npy",
                "full_donor_sum": "full_donor_sum_f64.npy",
                "full_donor_sumsq": "full_donor_sumsq_f64.npy",
                "target_cols": "target_cols_i64.npy",
                "proxy_cols": "proxy_cols_i64.npy",
                "distractor_cols": "distractor_cols_i64.npy",
                "cache_cols": "cache_cols_i64.npy",
                "target_ids": "target_ids.json",
            },
            "scientific_scope_note": (
                "CONTROL CALIBRATION ONLY. This cache is forbidden as terminal FULL104 "
                "masking qualification input and forbidden as training input."
            ),
        }
        (tmp / "cache_manifest.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, args.out_dir)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise

    print(json.dumps({
        "status": "FULL104_CONTROL_CALIBRATION_CACHE_BUILT",
        "cache_role_id": CACHE_ROLE_ID,
        "out_dir": str(args.out_dir),
        "terminal_masking_qualification_authorized": False,
        "training_authorized": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
