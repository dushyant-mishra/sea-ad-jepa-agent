from __future__ import annotations

from copy import deepcopy
from typing import Mapping

from .artifact_binding_v1 import seal_artifact, validate_artifact

PASS_FULL104_TERMINAL = "PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE"
FULL104_DIMENSION_INPUT_ARTIFACT_SCHEMA = "JEPA_V5_FULL104_DIMENSION_INPUT_ARTIFACT_V1"
EXPECTED_BLOCK_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_CONTRACT_SHA256 = "612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17"
EXPECTED_AUDIT_SHA256 = "9fa0ede3135a606bb1fe4cd4cc11881c439b7726b6dec62147c1892967eba7cf"
EXPECTED_METADATA_SQLITE_SHA256 = "a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"
EXPECTED_SELECTION_SHA256 = "edec0fe29d1425ecbe9fa889a610c4ce18621ae060c8144866315db57c3fc62b"
EXPECTED_SELECTION_MANIFEST_SHA256 = "3db3614bf544b183143f39b27bad516b3a7a75284df4b2410d9f3e99f0b0842e"

_EXPECTED_GEOMETRY = {
    "cells": 4_553_407,
    "donors": 104,
    "operators": 42,
    "matrices": 42,
    "blocks": 8_915,
    "addresses": 41_238,
}


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc
    return value.lower()


def _parent_hashes(receipt: Mapping[str, object]) -> dict[str, str]:
    return {
        "block_manifest": _sha(receipt.get("block_manifest_sha256"), "block_manifest_sha256"),
        "materialization_contract": _sha(receipt.get("materialization_contract_sha256"), "materialization_contract_sha256"),
        "materialization_audit": _sha(receipt.get("materialization_audit_sha256"), "materialization_audit_sha256"),
        "metadata_sqlite": _sha(receipt.get("metadata_sqlite_sha256"), "metadata_sqlite_sha256"),
        "selection": _sha(receipt.get("selection_sha256"), "selection_sha256"),
        "selection_manifest": _sha(receipt.get("selection_manifest_sha256"), "selection_manifest_sha256"),
    }


def project_full104_receipt_for_dimension_authority(receipt: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(receipt, Mapping):
        raise ValueError("FULL104 receipt must be a mapping")
    if receipt.get("schema") != "JEPA_V5_FULL104_EXPRESSION_BLOCK_BINDING_V4":
        raise RuntimeError("STOP_FULL104_DIMENSION_INTERFACE_SCHEMA_MISMATCH")
    if receipt.get("status") != PASS_FULL104_TERMINAL:
        raise RuntimeError("STOP_FULL104_DIMENSION_INTERFACE_TERMINAL_MISMATCH")

    expected_hashes = {
        "block_manifest_sha256": EXPECTED_BLOCK_MANIFEST_SHA256,
        "materialization_contract_sha256": EXPECTED_CONTRACT_SHA256,
        "materialization_audit_sha256": EXPECTED_AUDIT_SHA256,
        "metadata_sqlite_sha256": EXPECTED_METADATA_SQLITE_SHA256,
        "selection_sha256": EXPECTED_SELECTION_SHA256,
        "selection_manifest_sha256": EXPECTED_SELECTION_MANIFEST_SHA256,
    }
    for name, expected in expected_hashes.items():
        if _sha(receipt.get(name), name) != expected:
            raise RuntimeError(f"STOP_FULL104_DIMENSION_INTERFACE_{name.upper()}_MISMATCH")

    for name, expected in _EXPECTED_GEOMETRY.items():
        value = receipt.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value != expected:
            raise RuntimeError(f"STOP_FULL104_DIMENSION_INTERFACE_{name.upper()}_MISMATCH")

    if receipt.get("cross_ledger_identity_mismatches") != 0 or receipt.get("cross_ledger_missing_cells") != 0:
        raise RuntimeError("STOP_FULL104_DIMENSION_INTERFACE_IDENTITY_NOT_CLOSED")
    if receipt.get("test_fixture_mode") is not False or receipt.get("synthetic_data_used") is not False:
        raise RuntimeError("STOP_FULL104_DIMENSION_INTERFACE_FIXTURE_OR_SYNTHETIC")
    if receipt.get("pathology_used") is not False:
        raise RuntimeError("STOP_FULL104_DIMENSION_INTERFACE_PATHOLOGY_OR_UNKNOWN")
    if receipt.get("checkpoint_outcomes_used") is not False:
        raise RuntimeError("STOP_FULL104_DIMENSION_INTERFACE_CHECKPOINT_ADAPTATION_OR_UNKNOWN")
    if receipt.get("training_authorized") is not False:
        raise RuntimeError("STOP_FULL104_DIMENSION_INTERFACE_AUTHORITY_ESCALATION")

    out = deepcopy(dict(receipt))
    out.update({
        "expression_binding_terminal": PASS_FULL104_TERMINAL,
        "population_mode": "FULL_READER_FIT_STREAM",
        "estimand": "EQUAL_DONOR__EQUAL_CELL_WITHIN_DONOR",
        "null_geometry": "FULL_REFIT_EVERY_REPLICATE",
        "sampled_stratum_cap": None,
        "training_authorized": False,
    })
    return out


def seal_full104_dimension_input(receipt: Mapping[str, object]) -> dict[str, object]:
    projected = project_full104_receipt_for_dimension_authority(receipt)
    return seal_artifact(
        FULL104_DIMENSION_INPUT_ARTIFACT_SCHEMA,
        projected,
        _parent_hashes(projected),
    )


def validate_full104_dimension_input(envelope: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(envelope, Mapping):
        raise ValueError("FULL104 dimension artifact must be a mapping")
    raw_payload = envelope.get("payload")
    if not isinstance(raw_payload, Mapping):
        raise ValueError("FULL104 dimension artifact payload must be a mapping")
    payload = validate_artifact(
        envelope,
        expected_schema=FULL104_DIMENSION_INPUT_ARTIFACT_SCHEMA,
        expected_parents=_parent_hashes(raw_payload),
    )
    return project_full104_receipt_for_dimension_authority(payload)
