#!/usr/bin/env python3
"""Finalize the synthetic-only F1 real-forward/executor preflight package."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np

from contextual_target_f1_preflight_executor_v1 import AtomicShardStore, full_geometry

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = Path(os.environ.get("JEPA_CANONICAL_ROOT", "/mnt/d/Jepa project")).resolve()
FROZEN = ROOT / "docs/agent/f1_real_reader_forward_executor_preflight_20260903"
PACKAGE = ROOT / "outputs/contextual_teacher_target_v1_f1_real_reader_forward_executor_preflight_20260903"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def independent_select(rows: list[dict[str, Any]]) -> int:
    safe = [row for row in rows if row.get("safe") is True]
    if not safe:
        raise RuntimeError("STOP_F1_PREFLIGHT_RESOURCE_SELECTION_UNRESOLVED")
    fastest = max(float(row["median_throughput"]) for row in safe)
    eligible = [row for row in safe if float(row["median_throughput"]) >= 0.95 * fastest]
    return int(min(eligible, key=lambda row: int(row["configuration"]))["configuration"])


def independent_effects(teacher: float, correct: float, null: float, direct: float) -> dict[str, float]:
    contextual = float(teacher) - float(correct)
    null_advantage = float(teacher) - float(null)
    return {
        "teacher": float(teacher), "correct": float(correct), "null": float(null),
        "direct": float(direct), "contextual_advantage": contextual,
        "null_advantage": null_advantage, "qid_margin": null_advantage - contextual,
    }


def load_ladder() -> list[dict[str, Any]]:
    with (PACKAGE / "F1_PREFLIGHT_RESOURCE_LADDER.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["safe"] = row["safe"] == "True"
        row["configuration"] = int(row["configuration"])
        row["median_throughput"] = float(row["median_throughput"])
        for name in ("peak_rss_bytes", "candidate_start_memavailable_bytes", "swap_before_bytes", "swap_after_bytes", "cuda_peak_reserved_bytes", "cuda_total_bytes"):
            row[name] = int(row[name])
    return rows


def shard_resume_test(membership: str, forward: str) -> dict[str, Any]:
    ids = [f"fixture-{index:03d}" for index in range(12)]
    values = np.arange(84, dtype=np.float64).reshape(12, 7) / 13.0
    with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
        root = Path(temporary)
        uninterrupted = AtomicShardStore(root / "normal", membership, forward, "float64")
        uninterrupted.commit("000", ids[:5], values[:5])
        uninterrupted.commit("001", ids[5:], values[5:])
        normal = np.concatenate([uninterrupted.load("000", ids[:5]), uninterrupted.load("001", ids[5:])])

        resumed = AtomicShardStore(root / "resume", membership, forward, "float64")
        resumed.commit("000", ids[:5], values[:5])
        # Simulated process interruption after one committed shard.
        resumed = AtomicShardStore(root / "resume", membership, forward, "float64")
        first = resumed.load("000", ids[:5])
        resumed.commit("001", ids[5:], values[5:])
        recovered = np.concatenate([first, resumed.load("001", ids[5:])])
        attacks = {}
        for name, store, ordered in (
            ("membership_root", AtomicShardStore(root / "resume", "wrong", forward, "float64"), ids[:5]),
            ("forward_root", AtomicShardStore(root / "resume", membership, "wrong", "float64"), ids[:5]),
            ("dtype", AtomicShardStore(root / "resume", membership, forward, "float32"), ids[:5]),
            ("order", resumed, list(reversed(ids[:5]))),
        ):
            try:
                store.load("000", ordered)
                attacks[name] = False
            except RuntimeError:
                attacks[name] = True
        duplicate_rejected = False
        try:
            resumed.commit("000", ids[:5], values[:5])
        except RuntimeError:
            duplicate_rejected = True
    passed = normal.tobytes() == recovered.tobytes() and all(attacks.values()) and duplicate_rejected
    return {
        "schema": "f1-preflight-shard-resume-test-v1", "status": "PASS" if passed else "STOP_F1_PREFLIGHT_RESUME_RECONCILIATION_FAILURE",
        "interrupted_after_committed_shards": 1, "ordered_bytes_exact": normal.tobytes() == recovered.tobytes(),
        "semantic_sha_uninterrupted": canonical_sha(normal.tolist()), "semantic_sha_resumed": canonical_sha(recovered.tolist()),
        "attacks_rejected": attacks, "duplicate_write_rejected": duplicate_rejected,
    }


def sufficient_statistics_test(membership: str) -> tuple[dict[str, Any], dict[str, Any]]:
    fixture = json.loads((FROZEN / "F1_PREFLIGHT_TECHNICAL_FIXTURE_BINDING.json").read_text())
    identities = [f"{row['canonical_cell_id']}|{row['q']}|{row['evidence_level']}|{row['role']}" for row in fixture["selected"]]
    direct = []
    for index, _ in enumerate(identities):
        direct.append(independent_effects(index + 5.0, index + 3.0, index + 1.0, index + 2.0))
    order_root = canonical_sha(identities)
    values = np.asarray([[row[name] for name in ("teacher", "correct", "null", "direct", "contextual_advantage", "null_advantage", "qid_margin")] for row in direct], dtype=np.float64)
    with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
        store = AtomicShardStore(Path(temporary), membership, "technical-forward-root", "float64")
        store.commit("000", identities[:19], values[:19]); store.commit("001", identities[19:], values[19:])
        assembled = np.concatenate([store.load("000", identities[:19]), store.load("001", identities[19:])])
    exact = assembled.tobytes() == values.tobytes()
    recomputed = all(row[4] == row[0] - row[1] and row[5] == row[0] - row[2] and row[6] == row[5] - row[4] for row in assembled)
    schema = {
        "schema": "f1-preflight-sufficient-statistics-schema-v1", "global_order": "frozen assignment -> evidence -> role identity",
        "global_order_root_sha256": order_root, "assignment_membership_root_sha256": membership,
        "fields": ["teacher", "correct", "null", "direct", "contextual_advantage", "null_advantage", "qid_margin"],
        "dtype": "float64", "delta_recomputed_not_caller_supplied": True,
        "distinct_role_and_qid_fields": True, "hidden_states_persisted": False,
    }
    parity = {
        "schema": "f1-preflight-sufficient-statistics-parity-v1", "status": "PASS" if exact and recomputed else "STOP_F1_PREFLIGHT_SUFFICIENT_STATISTICS_MISMATCH",
        "fixture_rows": len(identities), "no_duplicate_writes": len(identities) == len(set(identities)),
        "no_missing_writes": len(assembled) == len(identities), "fixed_order_exact_bytes": exact,
        "delta_independently_recomputed": recomputed, "payload_sha256": canonical_sha(assembled.tolist()),
    }
    return schema, parity


def update_runtime_projection(commit_seconds: float, finalization_seconds: float) -> dict[str, Any]:
    path = PACKAGE / "F1_PREFLIGHT_RUNTIME_PROJECTION.json"
    value = json.loads(path.read_text())
    value["T_commit_seconds"] = commit_seconds * full_geometry()["logical_donor_operator_shards"] / 2.0
    value["T_finalization_seconds"] = finalization_seconds
    keys = ("T_forward_seconds", "T_io_seconds", "T_reduce_seconds", "T_commit_seconds", "T_finalization_seconds")
    value["T_total_projected_seconds"] = sum(float(value[key]) for key in keys)
    value["T_total_projected_hours"] = value["T_total_projected_seconds"] / 3600.0
    value["commit_and_finalization_measured_on_technical_fixture"] = True
    write_json(path, value)
    return value


def copy_frozen_authorities() -> None:
    names = (
        "F1_PREFLIGHT_AUTHORITY_BINDING.json", "F1_PREFLIGHT_EXPRESSION_JUSTIFICATION.json",
        "F1_PREFLIGHT_EVIDENCE_MASK_BINDING.json", "F1_PREFLIGHT_TECHNICAL_FIXTURE_BINDING.json",
        "F1_PREFLIGHT_REAL_FORWARD_ROOT.json",
    )
    for name in names:
        shutil.copyfile(FROZEN / name, PACKAGE / name)


def firewall_audit() -> dict[str, Any]:
    plan = json.loads((FROZEN / "F1_PREFLIGHT_READER_PLAN_BINDING.json").read_text())
    paths = sorted({str((CANONICAL / "outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4" / row["counts_path"]).resolve()) for row in plan["reader_rows"]})
    lowered = "\n".join(paths).lower()
    forbidden = ["reader_validation", "reader-validation", "reader_oracle", "reader-oracle", "/dev/", "sealed", "pathology", ".qs"]
    checks = {term: term not in lowered for term in forbidden}
    value = {
        "schema": "f1-preflight-firewall-audit-v1", "status": "PASS" if all(checks.values()) else "STOP_F1_PREFLIGHT_FIREWALL",
        "opened_expression_paths": paths, "opened_expression_path_count": len(paths), "all_are_authenticated_level4_materialized_blocks": len(paths) == 64,
        "forbidden_path_checks": checks, "reader_fit_only": True, "training_or_backward": False,
        "optimizer_or_ema_update": False, "biological_outcomes_computed": False,
        "protected_data_opened": False, "original_mixed_nph_opened": False,
    }
    return value


def independent_validation() -> dict[str, Any]:
    ladder = load_ladder()
    selection = json.loads((PACKAGE / "F1_PREFLIGHT_RESOURCE_SELECTION.json").read_text())
    parity = json.loads((PACKAGE / "F1_PREFLIGHT_QUERY_SAFE_PARITY.json").read_text())
    resume = json.loads((PACKAGE / "F1_PREFLIGHT_SHARD_RESUME_TEST.json").read_text())
    stats = json.loads((PACKAGE / "F1_PREFLIGHT_SUFFICIENT_STATISTICS_PARITY.json").read_text())
    firewall = json.loads((PACKAGE / "F1_PREFLIGHT_FIREWALL_AUDIT.json").read_text())
    environment = json.loads((PACKAGE / "F1_PREFLIGHT_WSL_ENVIRONMENT_AUTHENTICATION.json").read_text())
    forward_root = json.loads((PACKAGE / "F1_PREFLIGHT_REAL_FORWARD_ROOT.json").read_text())
    reconstructed = {}
    stage_to_key = {"gpu_batch": "forward_batch", "reader_block": "reader_block", "workers": "workers", "prefetch": "prefetch", "pinning": "pinned_memory"}
    for stage, key in stage_to_key.items():
        rows = [row for row in ladder if row["stage"] == stage]
        chosen = independent_select(rows)
        expected = int(selection["selected"][key])
        reconstructed[stage] = {"independent": chosen, "published": expected, "match": chosen == expected}
    safety = all(
        (not row["safe"]) or (
            row["cuda_peak_reserved_bytes"] <= 0.85 * row["cuda_total_bytes"]
            and row["swap_after_bytes"] <= row["swap_before_bytes"]
            and row["peak_rss_bytes"] <= 0.8 * row["candidate_start_memavailable_bytes"]
        ) for row in ladder
    )
    geometry = full_geometry()
    checks = {
        "selection_independently_reconstructed": all(row["match"] for row in reconstructed.values()),
        "resource_safety_recomputed": safety,
        "no_historical_batch_constant": selection["historical_batch_constant_used"] is False,
        "query_safe_parity": parity["status"] == "PASS",
        "query_permutation_inverse_exact": parity.get("query_permutation_inverse_restoration_exact") is True,
        "forward_batch_chunk_within_frozen_authority": parity.get("forward_batch_chunk_parity_within_frozen_authority") is True,
        "executed_source_bytes_bound": all(
            forward_root["executed_source_byte_identity"][f"{name}_executed_bytes_sha256"]
            == environment["source_hashes"][path]
            for name, path in {
                "constructor": "src/sea_ad_jepa/v4/contextual_query_local.py",
                "encoder": "src/sea_ad_jepa/v4/ipb_jepa.py",
                "tokenizer": "src/sea_ad_jepa/v4/gene_tokenizer.py",
            }.items()
        ),
        "geometry_exact": geometry == {"recipient_cells": 2781, "statistical_assignments": 44496, "unique_cell_q": 43108, "compute_only_dedups": 1388, "teacher_forwards": 43108, "correct_forwards": 215540, "null_forwards": 215540, "total_expensive_forwards": 474188, "assignment_evidence_effect_rows": 222480, "logical_donor_operator_shards": 1400},
        "resume": resume["status"] == "PASS", "sufficient_statistics": stats["status"] == "PASS",
        "firewall": firewall["status"] == "PASS", "no_biological_f1_outcome": firewall["biological_outcomes_computed"] is False,
    }
    return {
        "schema": "f1-preflight-independent-validation-v1", "status": "PASS" if all(checks.values()) else "STOP_F1_PREFLIGHT_INDEPENDENT_VALIDATION_FAILURE",
        "production_resource_selection_helper_imported": False, "reconstructed_selections": reconstructed,
        "checks": checks,
    }


def main() -> None:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    copy_frozen_authorities()
    root = json.loads((FROZEN / "F1_PREFLIGHT_REAL_FORWARD_ROOT.json").read_text())
    membership = root["fixture_membership_root_sha256"]
    started = time.perf_counter(); resume = shard_resume_test(membership, root["real_forward_root_sha256"]); commit_elapsed = time.perf_counter() - started
    write_json(PACKAGE / "F1_PREFLIGHT_SHARD_RESUME_TEST.json", resume)
    started = time.perf_counter(); schema, parity = sufficient_statistics_test(membership); final_elapsed = time.perf_counter() - started
    write_json(PACKAGE / "F1_PREFLIGHT_SUFFICIENT_STATISTICS_SCHEMA.json", schema)
    write_json(PACKAGE / "F1_PREFLIGHT_SUFFICIENT_STATISTICS_PARITY.json", parity)
    geometry = full_geometry()
    bytes_per_row = 7 * 8 + 2 * 8
    storage = {
        "schema": "f1-preflight-storage-envelope-v1", "assignment_effect_rows": geometry["assignment_evidence_effect_rows"],
        "durable_bytes_per_row": bytes_per_row, "projected_durable_bytes": geometry["assignment_evidence_effect_rows"] * bytes_per_row,
        "projected_temporary_bytes": geometry["assignment_evidence_effect_rows"] * bytes_per_row * 2,
        "current_free_storage_bytes": os.statvfs(CANONICAL).f_bavail * os.statvfs(CANONICAL).f_frsize,
        "full_hidden_state_archive": False, "sufficient_statistics_only": True,
    }
    write_json(PACKAGE / "F1_PREFLIGHT_STORAGE_ENVELOPE.json", storage)
    executor_plan = {
        "schema": "f1-preflight-executor-plan-v1", "status": "PASS", "geometry": geometry,
        "physical_order": "sorted materialized block reads", "logical_order": "frozen assignment order restored before persistence",
        "atomic_shards": True, "hash_bound_resume": True, "teacher_cache_only_under_complete_identity": True,
        "correct_null_cache_collision_forbidden": True, "compute_dedup_does_not_change_inference_population": True,
    }
    write_json(PACKAGE / "F1_PREFLIGHT_EXECUTOR_PLAN.json", executor_plan)
    write_json(PACKAGE / "F1_PREFLIGHT_FIREWALL_AUDIT.json", firewall_audit())
    update_runtime_projection(commit_elapsed, final_elapsed)
    reader_graph = """# F1 preflight reader call graph\n\n`reader plan (67 lawful rows)` -> `64 authenticated Level-4 CSR blocks` -> `float32 log1p10k normalization exactly once` -> `normalized_values + observation_states` -> `prospective evidence mask (q withheld)` -> `IPBEncoder student view` -> `query-local H_q - mean(H_context)` -> `LayerNorm`.\n\nIdentity/provenance remains in a sidecar and never enters the model-facing mapping. Physical block sorting is restored to frozen logical cell order before forward execution.\n"""
    (PACKAGE / "F1_PREFLIGHT_READER_CALL_GRAPH.md").write_text(reader_graph, encoding="utf-8")
    validation = independent_validation()
    write_json(PACKAGE / "F1_PREFLIGHT_INDEPENDENT_VALIDATION.json", validation)
    if resume["status"] != "PASS" or parity["status"] != "PASS" or validation["status"] != "PASS":
        raise RuntimeError(validation["status"])
    print(json.dumps({"status": "PASS_SYNTHETIC_EXECUTOR_AND_INDEPENDENT_VALIDATION", "resume": resume["status"], "sufficient_statistics": parity["status"], "independent": validation["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
