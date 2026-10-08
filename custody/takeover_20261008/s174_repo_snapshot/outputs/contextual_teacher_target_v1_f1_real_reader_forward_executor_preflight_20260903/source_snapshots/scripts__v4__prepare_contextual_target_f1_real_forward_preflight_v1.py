"""Freeze F1 real-forward authorities and a metadata-only technical fixture.

This program must run before any fixture expression or current-model forward.
It reads metadata and observation-state authorities only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


EXPECTED = {
    "f0_root": "e45dd8d885c4f6918bcaf0b24bde971c08c16322b27555e112693f46e42ddb4b",
    "weights": "001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70",
    "states": "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537",
    "split": "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511",
    "assignments": "12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617",
    "dedup": "3fcd11908723e2cc80db0f5a0f017ad382bd1ed9be522f97081587ae989c2423",
    "null_map": "aba31aea56190c32a00ac27a0356ea860761143f00f874db9c71c2080eb371a6",
    "cell_authority": "32437e5ebb01deb8fad771f8b2d4d9bd2b62b061f89c1e79fdbc6629d11af9fe",
    "evidence_contract": "d1eefdab177501a00370d71521ae86932e60540fb9f769dfe2b56c7994ca5c5a",
    "checkpoint": "19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4",
    "encoder": "732ea46f72384f29d503de1e0cc9d853315e2493cace054cced74849aa77485a",
    "tokenizer": "2a2ba7f4c2e52364cce471466ebacceefc2a1fccb29f4959860c885f281a89f4",
    "constructor": "6bd641cd22c160dfbec4e1ae4a0cc31929af436526487383f290397f4f55eeaa",
    "reader": "1fc1e7fcc90fe639e7826c996584e1fc220cae8c976748210d563a9f560edbdf",
    "row_lineage": "a6065751667b35a38c5990107c6b3f0177e262f7d145addb24bea24206eeb61b",
    "namespace_file": "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd",
}
NAMESPACE_SEMANTIC_ROOT = "595fd8bc860b13ce9ec2a957b0f3d92f850effcb51ae6e2f06b8c5d25d7bd53f"
EVIDENCE_SEED = "c5c5bc472850f17f0ca6249e3a2765e5924d411ef054691a5e7a5d9d29363a4f"
LEVELS = (20, 40, 60, 80, 100)
ROLES = ("teacher", "correct_student", "matched_null_student")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canonical_sha(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--worktree-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.canonical_root.resolve()
    worktree = args.worktree_root.resolve()
    out = worktree / "docs/agent/f1_real_reader_forward_executor_preflight_20260903"
    if out.exists():
        raise RuntimeError("STOP_F1_PREFLIGHT_EXISTING_BINDING_DIRECTORY")
    out.mkdir(parents=True)

    paths = {
        "weights": root / "exports/contextual_biology_v6r5a_20260822/program_weights.npz",
        "states": root / "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz",
        "split": root / "exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv",
        "assignments": root / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv",
        "dedup": root / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_EXECUTION_DEDUP_MAP.csv",
        "null_map": root / "outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_MATCHED_NULL_PRIMARY_MAP.csv",
        "cell_authority": root / "outputs/contextual_teacher_target_v1_f1_preflight_20260901/CONTEXTUAL_TARGET_V1_F1_CELL_DONOR_OPERATOR_AUTHORITY.json",
        "evidence_contract": root / "outputs/contextual_teacher_target_v1_f1_preflight_20260901/CONTEXTUAL_TARGET_V1_F1_EVIDENCE_MASK_CONTRACT.md",
        "checkpoint": root / "exports/prod41k_teacher_t1_20260823/t1_run/t1_checkpoint_u0000.pt",
        "encoder": root / "src/sea_ad_jepa/v4/ipb_jepa.py",
        "tokenizer": root / "src/sea_ad_jepa/v4/gene_tokenizer.py",
        "constructor": root / "src/sea_ad_jepa/v4/contextual_query_local.py",
        "reader": root / "scripts/v4/full104_expression_interface_consumer.py",
        "row_lineage": root / "outputs/full104_v014_20260826/01_full104_metadata_adapter/FULL104_ROW_LINEAGE.csv",
        "namespace_file": root / "exports/foundation_calibration_bundle_20260824/contracts/address_namespace.csv",
    }
    actual = {key: sha(path) for key, path in paths.items()}
    mismatch = {key: {"expected": EXPECTED[key], "actual": value} for key, value in actual.items() if value != EXPECTED[key]}
    if mismatch:
        raise RuntimeError("STOP_F1_PREFLIGHT_AUTHORITY_MISMATCH " + json.dumps(mismatch, sort_keys=True))
    f0_root_path = root / "outputs/contextual_teacher_target_v1_f0_implementation_20260901/CONTEXTUAL_TARGET_V1_F0_OUTPUT_MANIFEST_ROOT_SHA256.txt"
    if f0_root_path.read_text(encoding="utf-8").strip() != EXPECTED["f0_root"]:
        raise RuntimeError("STOP_F1_PREFLIGHT_AUTHORITY_MISMATCH f0_root")

    binding = {
        "schema": "f1-real-forward-preflight-authority-binding-v1",
        "result_state": "FROZEN_PRE_RESULT_METADATA_ONLY",
        "f0_root": EXPECTED["f0_root"],
        "evidence_trend_reviewed_commit": "249bc3b37cb6368ad97fde6bfb2a4560e83ff5a4",
        "evidence_trend_package_root": "ce759e1397cba36d3d595603b14472ccbb756826144a4dbb3db31a964da0c607",
        "namespace_semantic_root": NAMESPACE_SEMANTIC_ROOT,
        "authorities": {key: {"path": rel(root, path), "sha256": actual[key]} for key, path in paths.items()},
        "model_authority": {
            "checkpoint_role": "AUTHENTICATED_U0_CURRENT_QUALIFICATION_COMPARATOR",
            "vocabulary_size": 41238,
            "d_gene": 160,
            "heads": 4,
            "blocks": 6,
        },
        "expression_opened": False,
        "checkpoint_tensor_opened": False,
        "candidate_outcome_opened": False,
    }
    write_json(out / "F1_PREFLIGHT_AUTHORITY_BINDING.json", binding)

    evidence = {
        "schema": "f1-preflight-evidence-mask-binding-v1",
        "result_state": "FROZEN_PRE_RESULT",
        "contract": {"path": rel(root, paths["evidence_contract"]), "sha256": actual["evidence_contract"]},
        "implementation_authority": {
            "path": "scripts/v4/benchmark_contextual_target_f1_repair_v1.py",
            "function": "evidence_mask",
            "implementation_sha256": sha(root / "scripts/v4/benchmark_contextual_target_f1_repair_v1.py"),
        },
        "seed_sha256": EVIDENCE_SEED,
        "levels_percent": list(LEVELS),
        "physical_state_distinct_from_evidence_mask": True,
        "measured_zero_is_evidence": True,
        "query_identity_retained": True,
        "query_scalar_withheld": True,
        "nested_prefix_algorithm": "SHA256(seed|canonical-row-locator|decimal-q|decimal-j), digest bytes then address; floor(p*eligible/100)",
        "expression_opened": False,
    }
    write_json(out / "F1_PREFLIGHT_EVIDENCE_MASK_BINDING.json", evidence)

    cell_doc = json.loads(paths["cell_authority"].read_text(encoding="utf-8"))
    cells = cell_doc["selected_rows"]
    if len(cells) != 2781:
        raise RuntimeError("STOP_F1_PREFLIGHT_AUTHORITY_MISMATCH cell count")
    cell_by_id = {str(row["canonical_cell_id"]): row for row in cells}
    if len(cell_by_id) != 2781:
        raise RuntimeError("STOP_F1_PREFLIGHT_AUTHORITY_MISMATCH cell uniqueness")
    null_rows = read_csv(paths["null_map"])
    null_by_cell = {row["recipient_canonical_cell_id"]: row for row in null_rows}
    dedup = read_csv(paths["dedup"])
    if len(dedup) != 43108 or len({(r["canonical_cell_id"], r["selected_query_address"]) for r in dedup}) != 43108:
        raise RuntimeError("STOP_F1_PREFLIGHT_AUTHORITY_MISMATCH dedup population")

    packed = np.load(paths["states"], allow_pickle=False)
    operators = packed["operator_index"].astype(int)
    states = packed["states"].astype(np.uint8)
    if states.shape != (42, 41238) or set(operators.tolist()) != set(range(42)):
        raise RuntimeError("STOP_F1_PREFLIGHT_AUTHORITY_MISMATCH observation shape")
    state_by_op = {int(op): states[index] for index, op in enumerate(operators)}

    candidates: list[dict[str, object]] = []
    for row in dedup:
        cell = cell_by_id.get(row["canonical_cell_id"])
        if cell is None:
            raise RuntimeError("STOP_F1_PREFLIGHT_AUTHORITY_MISMATCH dedup cell")
        q = int(row["selected_query_address"])
        op = int(cell["operator_index"])
        state = state_by_op[op]
        if int(state[q]) != 1:
            raise RuntimeError("STOP_F1_PREFLIGHT_EVIDENCE_MASK_AUTHORITY_UNRESOLVED query not scalar")
        candidates.append({
            "canonical_cell_id": row["canonical_cell_id"],
            "q": q,
            "donor": cell["canonical_donor_id"],
            "source": cell["source"],
            "operator": op,
            "row_locator": cell["row_locator"],
            "context_support_count": int(np.count_nonzero(state == 1) - 1),
        })

    support_values = {
        source: sorted({int(row["context_support_count"]) for row in candidates if row["source"] == source})
        for source in ("HVS", "NPH52", "SEA_AD")
    }
    stress_target: dict[tuple[str, str], int] = {}
    for source, values in support_values.items():
        if not values:
            raise RuntimeError("STOP_F1_PREFLIGHT_AUTHORITY_MISMATCH missing source")
        positions = {"low": 0, "median": (len(values) - 1) // 2, "high": len(values) - 1}
        stress_target.update({(source, label): values[position] for label, position in positions.items()})

    tasks: list[dict[str, object]] = []
    for op in range(42):
        tasks.append({"reason": f"operator_{op:02d}", "operator": op, "level": LEVELS[op % len(LEVELS)], "role": ROLES[op % len(ROLES)]})
    for source in ("HVS", "NPH52", "SEA_AD"):
        for offset, label in enumerate(("low", "median", "high")):
            token = hashlib.sha256(f"F1-PREFLIGHT-STRESS|{source}|{label}".encode("utf-8")).digest()
            tasks.append({
                "reason": f"source_{source}_{label}_support",
                "source": source,
                "support": stress_target[(source, label)],
                "level": LEVELS[token[0] % len(LEVELS)],
                "role": ROLES[token[1] % len(ROLES)],
            })

    selected: list[dict[str, object]] = []
    used: set[tuple[str, int]] = set()
    for task in tasks:
        pool = [row for row in candidates if ("operator" not in task or row["operator"] == task["operator"]) and ("source" not in task or row["source"] == task["source"]) and ("support" not in task or row["context_support_count"] == task["support"])]
        enriched = []
        for row in pool:
            null = null_by_cell[row["canonical_cell_id"]]
            record = dict(row)
            record.update({
                "evidence_level": int(task["level"]),
                "role": str(task["role"]),
                "null_source_cell": null["source_canonical_cell_id"] if task["role"] == "matched_null_student" else None,
                "null_source_row_locator": null["source_row_locator"] if task["role"] == "matched_null_student" else None,
                "selection_reason": task["reason"],
            })
            identity = [record[key] for key in ("canonical_cell_id", "q", "donor", "source", "operator", "evidence_level", "role", "null_source_cell", "context_support_count")]
            record["selection_sha256"] = canonical_sha(identity)
            enriched.append(record)
        enriched.sort(key=lambda row: (row["selection_sha256"], row["canonical_cell_id"], row["q"]))
        choice = next((row for row in enriched if (row["canonical_cell_id"], row["q"]) not in used), None)
        if choice is None:
            raise RuntimeError("STOP_F1_PREFLIGHT_CONTEXT_BUDGET_UNRESOLVED " + str(task))
        selected.append(choice)
        used.add((str(choice["canonical_cell_id"]), int(choice["q"])))

    if {int(row["operator"]) for row in selected} != set(range(42)):
        raise RuntimeError("STOP_F1_PREFLIGHT_CONTEXT_BUDGET_UNRESOLVED operator coverage")
    if {str(row["source"]) for row in selected} != {"HVS", "NPH52", "SEA_AD"}:
        raise RuntimeError("STOP_F1_PREFLIGHT_CONTEXT_BUDGET_UNRESOLVED source coverage")
    if {int(row["evidence_level"]) for row in selected} != set(LEVELS) or {str(row["role"]) for row in selected} != set(ROLES):
        raise RuntimeError("STOP_F1_PREFLIGHT_CONTEXT_BUDGET_UNRESOLVED level/role coverage")
    for source in ("HVS", "NPH52", "SEA_AD"):
        got = {int(row["context_support_count"]) for row in selected if row["source"] == source}
        want = {stress_target[(source, label)] for label in ("low", "median", "high")}
        if not want.issubset(got):
            raise RuntimeError("STOP_F1_PREFLIGHT_CONTEXT_BUDGET_UNRESOLVED stress coverage")

    selected.sort(key=lambda row: (int(row["operator"]), str(row["selection_reason"]), str(row["canonical_cell_id"]), int(row["q"])))
    membership_root = canonical_sha(selected)
    fixture = {
        "schema": "f1-preflight-technical-fixture-binding-v1",
        "result_state": "FROZEN_PRE_RESULT_METADATA_ONLY",
        "selection_rule": "contract-hash-bound operator coverage plus source low/median/high support stress; lexicographically smallest SHA256; unique cell-q",
        "input_authorities": {key: actual[key] for key in ("assignments", "dedup", "cell_authority", "null_map", "states")},
        "candidate_unique_cell_q": len(candidates),
        "fixture_unique_cell_q": len(selected),
        "cells": len({row["canonical_cell_id"] for row in selected}),
        "donors": len({row["donor"] for row in selected}),
        "operators": len({row["operator"] for row in selected}),
        "sources": sorted({str(row["source"]) for row in selected}),
        "evidence_levels": sorted({int(row["evidence_level"]) for row in selected}),
        "roles": sorted({str(row["role"]) for row in selected}),
        "stress_targets": {f"{source}:{label}": stress_target[(source, label)] for source in ("HVS", "NPH52", "SEA_AD") for label in ("low", "median", "high")},
        "selected": selected,
        "membership_root_sha256": membership_root,
        "expression_opened": False,
        "model_forward_run": False,
        "candidate_outcome_opened": False,
    }
    write_json(out / "F1_PREFLIGHT_TECHNICAL_FIXTURE_BINDING.json", fixture)

    nph_manifest_path = root / "outputs/full104_v014_20260826/full104_expression_interface_v8_verified/FULL104_EXPRESSION_INTERFACE_V8/NPH_READER_FIT_DERIVATIVE_MANIFEST.csv"
    nph_by_op = {int(row["operator_index"]): row for row in read_csv(nph_manifest_path)}
    exact_rows = []
    for row in selected:
        ids = [("recipient", row["canonical_cell_id"], row["row_locator"])]
        if row["role"] == "matched_null_student":
            ids.append(("null_source", row["null_source_cell"], row["null_source_row_locator"]))
        for role, cell_id, locator in ids:
            meta = cell_by_id[str(cell_id)]
            if meta["source"] == "NPH52":
                nph = nph_by_op[int(meta["operator_index"])]
                asset = "outputs/full104_v014_20260826/full104_expression_interface_v8_verified/FULL104_EXPRESSION_INTERFACE_V8/" + nph["derivative_relative_path"].replace("\\", "/")
                asset_sha = nph["derivative_sha256"]
                asset_authority = "FIT_ONLY_NPH_DERIVATIVE"
            else:
                asset = str(meta["source_path"]).replace("\\", "/")
                asset_sha = None
                asset_authority = "AUTHENTICATED_ASSET_REGISTRY_MUST_VERIFY_BEFORE_READ"
            exact_rows.append({
                "fixture_role": role,
                "canonical_cell_id": cell_id,
                "row_locator": locator,
                "source": meta["source"],
                "operator": int(meta["operator_index"]),
                "asset_path": asset,
                "asset_sha256": asset_sha,
                "asset_authority": asset_authority,
            })
    exact_rows.sort(key=lambda row: (row["source"], row["operator"], row["asset_path"], row["row_locator"], row["fixture_role"]))
    justification = {
        "schema": "f1-preflight-expression-justification-v1",
        "result_state": "FROZEN_PRE_RESULT_METADATA_ONLY",
        "reason": "Frozen summaries cannot establish query-safe current-model parity, real reader latency, CUDA memory, or executor throughput.",
        "allowed_reads": exact_rows,
        "allowed_unique_rows": len({row["row_locator"] for row in exact_rows}),
        "allowed_assets": sorted({row["asset_path"] for row in exact_rows}),
        "all_rows_reader_fit_foundation_train": True,
        "original_mixed_nph_assets_forbidden": True,
        "protected_partitions_touched": False,
        "output_is_non_conclusion_bearing": True,
        "forbidden_outputs": ["per_cell_expression", "H", "S", "T", "effects", "program_scores", "candidate_outcomes", "biological_gate_vector"],
        "expression_opened_during_derivation": False,
    }
    write_json(out / "F1_PREFLIGHT_EXPRESSION_JUSTIFICATION.json", justification)

    manifest_rows = []
    for path in sorted(out.iterdir(), key=lambda p: p.name):
        manifest_rows.append({"path": path.name, "bytes": path.stat().st_size, "sha256": sha(path), "state": "FROZEN_PRE_RESULT"})
    manifest_path = out / "F1_PREFLIGHT_METADATA_FREEZE_MANIFEST.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("path", "bytes", "sha256", "state"), lineterminator="\n")
        writer.writeheader()
        writer.writerows(manifest_rows)
    print(json.dumps({"status": "PASS_F1_PREFLIGHT_METADATA_FIXTURE_FROZEN", "fixture_pairs": len(selected), "membership_root": membership_root, "manifest_sha256": sha(manifest_path)}))


if __name__ == "__main__":
    main()
