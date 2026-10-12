"""Frozen contract validation for the corrected TD56/TD57B/TD57C/TD59 replay.

This module is metadata-only. It validates identities and repository-resident
executor bytes; it never opens corrected biological values.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    pass


SCHEMA = "JEPA_TD_CORRECTED_REPLAY_CONTRACT_V1"
G6_PRODUCER_COMMIT = "ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0"
G6_ACCEPTANCE_SHA256 = "89932183a2c7b56d1e3ae42264ea3f3b3ae9001d865cfa93604b46f0db2129fb"
G6_RECEIPT_SHA256 = "2edaa2d2e03b8d862172e97b35fb94888305ef0e843cd71206ee56f53b28a52b"
G6_VALUES_SHA256 = "fdc13516a31a4163498cfc1bb9b9dd5fc615bc4ba8e7ec3fd3f4a51522e344a9"
G6_META_SHA256 = "bd3a494b3dd8239a78485dfc6006e75a75c32e5f2eb0a33afd2da2472522fe74"
G7_IMPLEMENTATION_COMMIT = "8d41fb9838b425ddcb704ecbdf5cd51f3eeb9f27"
G7_MARKER_SHA256 = "2579b9a6a5cbfc89f4dd38082515a290681fc5413afeb95536b62bbfd46f2667"
G7_RECEIPT_SHA256 = "47f9be6e8fef3fa70c07fbe8011fa1360df72e26b8259fc9655a369768a97fcf"
G7_TERMINAL = "NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP"
DIAGNOSTIC_COMMIT = "0b50938e48f7c257b362a0c66899bc1caa0d27a1"
DIAGNOSTIC_CLASSIFICATION = "GENUINELY_DISJOINT_NATURAL_CELL_SETS"
TD57B_SHA256 = "1654011ca1aeb20dab8e707b229ec3de00106b937ed49b33b2432b789d8c4e0e"
TD57C_SHA256 = "530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c"
TD59_SHA256 = "870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085"
TD56_HVS_NPH52_SHA256 = "a1ea8653e24213a3b14ccc52ea64011c92553aec4df5edb7b55d6ba309f61b43"
TD56_SEAAD_SHA256 = "c77ceac26f0ff4c3ae7a3955c39218af56339adda0225b9c663c9d92710c8866"
STAGE_ORDER = ("TD56", "TD57B", "TD57C", "TD59")
DOWNSTREAM_FLAGS = (
    "g6_execution_authorized",
    "g7_execution_authorized",
    "target_selection_authorized",
    "target_selected",
    "representation_selected",
    "td60_authorized",
    "stage4_authorized",
    "training_authorized",
)


def _sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_contract(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ContractError("contract must be a JSON object")
    return obj


def _require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ContractError(f"{label} mismatch: expected {expected!r}, got {actual!r}")


def _validate_td56(executor: dict[str, Any]) -> None:
    selected = executor.get("selected_artifacts")
    if not isinstance(selected, list):
        raise ContractError("TD56 selected_artifacts must be a list")
    by_source: dict[str, list[dict[str, Any]]] = {}
    for item in selected:
        if not isinstance(item, dict):
            raise ContractError("TD56 selected artifact must be an object")
        by_source.setdefault(str(item.get("source")), []).append(item)
    if set(by_source) != {"HVS", "NPH52", "SEA_AD"} or any(len(v) != 1 for v in by_source.values()):
        raise ContractError("TD56 must bind exactly one selected artifact for HVS, NPH52, and SEA_AD")
    _require_equal(by_source["HVS"][0].get("sha256"), TD56_HVS_NPH52_SHA256, "TD56 HVS executor sha256")
    _require_equal(by_source["NPH52"][0].get("sha256"), TD56_HVS_NPH52_SHA256, "TD56 NPH52 executor sha256")
    _require_equal(by_source["SEA_AD"][0].get("sha256"), TD56_SEAAD_SHA256, "TD56 SEA_AD executor sha256")
    for source, rows in by_source.items():
        row = rows[0]
        if row.get("storage") != "external_frozen_artifact":
            raise ContractError(f"TD56 {source} storage must remain external_frozen_artifact")
        if not row.get("artifact_id"):
            raise ContractError(f"TD56 {source} missing artifact_id")


def validate_contract(contract: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    """Validate immutable replay lineage and executor bindings.

    Repository-resident executors are hashed from ``repo_root``. External frozen
    artifacts are identity-bound here and physically authenticated by QUALIFY.
    """
    _require_equal(contract.get("schema"), SCHEMA, "schema")
    p = contract.get("predecessors") or {}
    g6 = p.get("g6") or {}
    _require_equal(g6.get("producer_commit"), G6_PRODUCER_COMMIT, "G6 producer commit")
    _require_equal(g6.get("external_acceptance_sha256"), G6_ACCEPTANCE_SHA256, "G6 acceptance sha256")
    _require_equal(g6.get("receipt_sha256"), G6_RECEIPT_SHA256, "G6 receipt sha256")
    _require_equal(g6.get("corrected_values_sha256"), G6_VALUES_SHA256, "G6 corrected values sha256")
    _require_equal(g6.get("corrected_metadata_sha256"), G6_META_SHA256, "G6 corrected metadata sha256")

    g7 = p.get("g7") or {}
    _require_equal(g7.get("implementation_commit"), G7_IMPLEMENTATION_COMMIT, "G7 implementation commit")
    _require_equal(g7.get("marker_sha256"), G7_MARKER_SHA256, "G7 marker sha256")
    _require_equal(g7.get("receipt_sha256"), G7_RECEIPT_SHA256, "G7 receipt sha256")
    _require_equal(g7.get("terminal"), G7_TERMINAL, "G7 terminal")
    if g7.get("accepted_as_pass") is not False:
        raise ContractError("G7 NOT_ESTIMABLE must never be relabeled as PASS")

    diag = p.get("diagnostic") or {}
    _require_equal(diag.get("commit"), DIAGNOSTIC_COMMIT, "diagnostic commit")
    _require_equal(diag.get("classification"), DIAGNOSTIC_CLASSIFICATION, "diagnostic classification")
    if diag.get("claims_value_agreement") is not False:
        raise ContractError("diagnostic may not claim value agreement")

    stages = contract.get("stages")
    if not isinstance(stages, list) or tuple(x.get("id") for x in stages if isinstance(x, dict)) != STAGE_ORDER:
        raise ContractError(f"stage order must be {STAGE_ORDER!r}")

    executors = contract.get("executors") or {}
    if set(executors) != set(STAGE_ORDER):
        raise ContractError("executors must contain exactly TD56, TD57B, TD57C, TD59")
    _validate_td56(executors["TD56"])
    _require_equal(executors["TD57B"].get("sha256"), TD57B_SHA256, "TD57B executor sha256")
    _require_equal(executors["TD57C"].get("sha256"), TD57C_SHA256, "TD57C executor sha256")
    _require_equal(executors["TD59"].get("sha256"), TD59_SHA256, "TD59 executor sha256")
    if executors["TD57C"].get("storage") != "external_frozen_artifact":
        raise ContractError("TD57C must remain an external frozen-artifact binding")
    if executors["TD59"].get("historical_original_recovered") is not False:
        raise ContractError("TD59 may not impersonate the unrecovered historical original")

    authority = contract.get("downstream_authority")
    if not isinstance(authority, dict) or set(authority) != set(DOWNSTREAM_FLAGS):
        raise ContractError("downstream authority flags are incomplete")
    if any(value is not False for value in authority.values()):
        raise ContractError("all downstream authority flags must be false")

    policy = contract.get("authority_policy") or {}
    if policy.get("qualify_reads_protected_values") is not False:
        raise ContractError("QUALIFY must not read protected replay values")
    if policy.get("execute_requires_fresh_replay_authority") is not True:
        raise ContractError("EXECUTE_ONCE must require fresh replay-specific authority")
    if policy.get("start_marker_spends_authority") is not True:
        raise ContractError("start marker must spend authority")

    for stage in ("TD57B", "TD59"):
        ex = executors[stage]
        if ex.get("storage") != "repository":
            raise ContractError(f"{stage} storage must be repository")
        rel = ex.get("repository_path")
        if not isinstance(rel, str) or not rel:
            raise ContractError(f"{stage} missing repository_path")
        observed = _sha256_path(repo_root / rel)
        _require_equal(observed, ex["sha256"], f"{stage} repository bytes")

    interp = contract.get("interpretation_policy") or {}
    if interp.get("not_estimable_is_pass") is not False:
        raise ContractError("NOT_ESTIMABLE may not be treated as biological PASS")
    if interp.get("source_disagreement_may_be_averaged") is not False:
        raise ContractError("source disagreement may not be averaged away")

    return contract
