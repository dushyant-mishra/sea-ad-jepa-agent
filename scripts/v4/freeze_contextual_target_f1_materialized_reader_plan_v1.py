"""Bind the frozen F1 technical fixture to authenticated FULL104 blocks.

Reads only CSV/JSON metadata. It never opens a counts payload.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


BLOCK_MANIFEST_SHA = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--worktree-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.canonical_root.resolve()
    worktree = args.worktree_root.resolve()
    frozen = worktree / "docs/agent/f1_real_reader_forward_executor_preflight_20260903"
    fixture_path = frozen / "F1_PREFLIGHT_TECHNICAL_FIXTURE_BINDING.json"
    justification_path = frozen / "F1_PREFLIGHT_EXPRESSION_JUSTIFICATION.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if fixture["expression_opened"] or fixture["model_forward_run"]:
        raise RuntimeError("STOP_F1_PREFLIGHT_FIREWALL fixture is not pre-result")

    expression_root = root / "outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4"
    block_manifest = expression_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if sha(block_manifest) != BLOCK_MANIFEST_SHA:
        raise RuntimeError("STOP_F1_PREFLIGHT_AUTHORITY_MISMATCH block manifest")
    manifest = read_csv(block_manifest)
    by_operator: dict[int, list[dict[str, str]]] = {}
    for row in manifest:
        by_operator.setdefault(int(row["operator_index"]), []).append(row)
    if set(by_operator) != set(range(42)) or len(manifest) != 8915:
        raise RuntimeError("STOP_F1_PREFLIGHT_AUTHORITY_MISMATCH block geometry")

    wanted: dict[str, dict[str, object]] = {}
    for row in fixture["selected"]:
        wanted[str(row["canonical_cell_id"])] = {"role": "recipient", "operator": int(row["operator"]), "row_locator": row["row_locator"]}
        if row["role"] == "matched_null_student":
            wanted[str(row["null_source_cell"])] = {"role": "null_source", "operator": int(row["operator"]), "row_locator": row["null_source_row_locator"]}

    found: dict[str, dict[str, object]] = {}
    meta_hashes_checked: set[str] = set()
    for operator in sorted({int(value["operator"]) for value in wanted.values()}):
        targets = {cell for cell, value in wanted.items() if int(value["operator"]) == operator}
        for block in by_operator[operator]:
            if targets.issubset(found):
                break
            meta_path = expression_root / block["meta_path"]
            if sha(meta_path) != block["meta_sha256"]:
                raise RuntimeError("STOP_F1_PREFLIGHT_AUTHORITY_MISMATCH meta block")
            meta_hashes_checked.add(block["meta_path"])
            with meta_path.open("r", encoding="utf-8-sig", newline="") as handle:
                for row_index, meta in enumerate(csv.DictReader(handle)):
                    cell = str(meta["canonical_cell_id"])
                    if cell not in targets:
                        continue
                    if cell in found:
                        raise RuntimeError("STOP_F1_PREFLIGHT_AUTHORITY_MISMATCH duplicate fixture cell")
                    expected = wanted[cell]
                    found[cell] = {
                        "fixture_role": expected["role"],
                        "canonical_cell_id": cell,
                        "row_locator": expected["row_locator"],
                        "operator": operator,
                        "block_key": block["block_key"],
                        "counts_path": block["counts_path"].replace("\\", "/"),
                        "counts_sha256": block["counts_sha256"],
                        "meta_path": block["meta_path"].replace("\\", "/"),
                        "meta_sha256": block["meta_sha256"],
                        "row_index_within_block": row_index,
                        "source_library_hex": float(meta["source_library"]).hex(),
                    }
        missing = targets - set(found)
        if missing:
            raise RuntimeError("STOP_F1_PREFLIGHT_AUTHORITY_MISMATCH missing fixture cells " + str(sorted(missing)[:3]))
    if set(found) != set(wanted):
        raise RuntimeError("STOP_F1_PREFLIGHT_AUTHORITY_MISMATCH exact fixture population")

    rows = sorted(found.values(), key=lambda row: (row["operator"], row["counts_path"], row["row_index_within_block"], row["canonical_cell_id"]))
    asset_auth = expression_root / "ASSET_AUTHENTICATION.csv"
    materialization_audit = expression_root / "PHASE2_EXPRESSION_MATERIALIZATION_AUDIT.json"
    materialization_manifest = expression_root / "PHASE2_EXPRESSION_MATERIALIZATION_MANIFEST.csv"
    reader_plan = {
        "schema": "f1-preflight-materialized-reader-plan-v1",
        "result_state": "FROZEN_PRE_RESULT_METADATA_ONLY",
        "fixture_membership_root_sha256": fixture["membership_root_sha256"],
        "block_manifest": {"path": block_manifest.relative_to(root).as_posix(), "sha256": BLOCK_MANIFEST_SHA, "blocks": len(manifest)},
        "materialization_authorities": {
            "asset_authentication": {"path": asset_auth.relative_to(root).as_posix(), "sha256": sha(asset_auth)},
            "audit": {"path": materialization_audit.relative_to(root).as_posix(), "sha256": sha(materialization_audit)},
            "manifest": {"path": materialization_manifest.relative_to(root).as_posix(), "sha256": sha(materialization_manifest)},
        },
        "reader_rows": rows,
        "unique_rows": len(rows),
        "unique_counts_blocks": len({row["counts_path"] for row in rows}),
        "meta_blocks_hash_verified": len(meta_hashes_checked),
        "counts_payloads_opened": False,
        "normalization": "float32 log1p(raw_count * (10000.0 / source_library)); applied exactly once after CSR row retrieval",
        "model_facing_return_keys": ["normalized_values", "observation_states"],
        "identity_sidecar_excluded_from_model_input": True,
        "original_mixed_nph_paths_denied": True,
    }
    reader_plan["reader_plan_root_sha256"] = hashlib.sha256(json.dumps(reader_plan, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    write_json(frozen / "F1_PREFLIGHT_READER_PLAN_BINDING.json", reader_plan)

    old = json.loads(justification_path.read_text(encoding="utf-8"))
    old["allowed_reads"] = rows
    old["allowed_unique_rows"] = len(rows)
    old["allowed_assets"] = sorted({(expression_root / row["counts_path"]).relative_to(root).as_posix() for row in rows})
    old["reader_plan_root_sha256"] = reader_plan["reader_plan_root_sha256"]
    old["raw_source_expression_assets_opened_by_preflight"] = False
    old["expression_materialization_reused"] = True
    write_json(justification_path, old)

    manifest_path = frozen / "F1_PREFLIGHT_METADATA_FREEZE_MANIFEST.csv"
    entries = []
    for path in sorted((p for p in frozen.iterdir() if p.is_file() and p != manifest_path), key=lambda p: p.name):
        entries.append({"path": path.name, "bytes": path.stat().st_size, "sha256": sha(path), "state": "FROZEN_PRE_RESULT"})
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("path", "bytes", "sha256", "state"), lineterminator="\n")
        writer.writeheader()
        writer.writerows(entries)
    print(json.dumps({"status": "PASS_F1_PREFLIGHT_READER_PLAN_FROZEN", "rows": len(rows), "blocks": reader_plan["unique_counts_blocks"], "root": reader_plan["reader_plan_root_sha256"], "manifest_sha256": sha(manifest_path)}))


if __name__ == "__main__":
    main()
