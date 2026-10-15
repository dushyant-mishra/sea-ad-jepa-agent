from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.v5.td_unified.canonical_v1 import (
    CanonicalError,
    canonical_bytes,
    canonical_sha256,
    make_scientific_receipt,
    verify_scientific_receipt,
)

HEX40_A = "a" * 40
HEX64_B = "b" * 64
ROOT = Path(__file__).resolve().parents[3]
SCHEMA = ROOT / "schemas" / "target_discovery" / "unified_v1" / "scientific_receipt_v1.json"

DEFAULT_OBJECTS = {
    "output": {"artifact": "output", "version": 1},
    "manifest": {"artifact": "manifest", "version": 1},
    "registry": {"artifact": "registry", "version": 1},
    "access": {"artifact": "access", "version": 1},
}
DEFAULT_SHAS = {name: canonical_sha256(obj) for name, obj in DEFAULT_OBJECTS.items()}
DEFAULT_BY_SHA = {DEFAULT_SHAS[name]: obj for name, obj in DEFAULT_OBJECTS.items()}


def _resolver(extra=None, omit=None):
    mapping = dict(DEFAULT_BY_SHA)
    if extra:
        mapping.update(extra)
    if omit:
        mapping.pop(omit, None)
    return mapping.get


def _leaf(payload=None):
    return make_scientific_receipt(
        payload=payload or {"measured_zero": 0, "missing": None},
        producer_code_sha=HEX40_A,
        input_shas=[],
        parent_receipt_shas=[],
        output_sha=DEFAULT_SHAS["output"],
        manifest_sha=DEFAULT_SHAS["manifest"],
        registry_sha=DEFAULT_SHAS["registry"],
        access_policy_sha=DEFAULT_SHAS["access"],
    )


def test_canonical_bytes_are_mapping_order_invariant_and_semantically_strict():
    assert canonical_bytes({"b": [1, 0.0], "a": None}) == canonical_bytes({"a": None, "b": [1, 0.0]})
    assert canonical_sha256(None) != canonical_sha256(0)
    assert canonical_sha256(0) != canonical_sha256(0.0)
    with pytest.raises(CanonicalError):
        canonical_bytes(float("nan"))
    with pytest.raises(CanonicalError):
        canonical_bytes(b"raw")


def test_reused_old_task1_canonical_byte_rules_remain_compatible():
    assert canonical_bytes({"b": [1, 2.5], "a": None}) == b'{"a":null,"b":[1,2.5]}'
    assert canonical_bytes("a\r\nb\rc") == b'"a\\nb\\nc"'
    assert canonical_bytes(-0.0) == b"0.0"
    assert canonical_bytes([True, 1, 1.0, None]) == b"[true,1,1.0,null]"
    assert canonical_bytes("é") == b'"\xc3\xa9"'


def test_declared_digest_never_authenticates_mutated_payload():
    receipt = _leaf({"x": 1})
    tampered = copy.deepcopy(receipt)
    tampered["payload"] = {"x": 2}
    with pytest.raises(CanonicalError, match="payload"):
        verify_scientific_receipt(tampered, _resolver())


def test_valid_child_with_missing_or_invalid_parent_fails_closed():
    parent = _leaf({"parent": 1})
    child = make_scientific_receipt(
        payload={"child": 1},
        producer_code_sha=HEX40_A,
        input_shas=[],
        parent_receipt_shas=[parent["receipt_sha256"]],
        output_sha=DEFAULT_SHAS["output"],
        manifest_sha=DEFAULT_SHAS["manifest"],
        registry_sha=DEFAULT_SHAS["registry"],
        access_policy_sha=DEFAULT_SHAS["access"],
    )
    with pytest.raises(CanonicalError, match="parent"):
        verify_scientific_receipt(child, _resolver())

    bad_parent = copy.deepcopy(parent)
    bad_parent["payload"] = {"parent": 999}
    with pytest.raises(CanonicalError):
        verify_scientific_receipt(child, _resolver({parent["receipt_sha256"]: bad_parent}))


def test_receipt_binds_schema_producer_inputs_parents_output_manifest_registry_and_access():
    receipt = _leaf({"x": 1})
    for field in (
        "receipt_schema",
        "producer_code_sha",
        "input_shas",
        "parent_receipt_shas",
        "output_sha",
        "manifest_sha",
        "registry_sha",
        "access_policy_sha",
    ):
        tampered = copy.deepcopy(receipt)
        if isinstance(tampered[field], list):
            tampered[field] = list(tampered[field]) + [HEX64_B]
        else:
            tampered[field] = "f" * len(tampered[field])
        with pytest.raises(CanonicalError):
            verify_scientific_receipt(tampered, _resolver())


def test_duplicate_or_conflicting_parent_identity_is_rejected():
    parent = _leaf({"p": 1})
    with pytest.raises(CanonicalError, match="duplicate"):
        make_scientific_receipt(
            payload={"child": 1},
            producer_code_sha=HEX40_A,
            input_shas=[],
            parent_receipt_shas=[parent["receipt_sha256"], parent["receipt_sha256"]],
            output_sha=DEFAULT_SHAS["output"],
            manifest_sha=DEFAULT_SHAS["manifest"],
            registry_sha=DEFAULT_SHAS["registry"],
            access_policy_sha=DEFAULT_SHAS["access"],
        )


def test_closed_receipt_schema_matches_actual_emitted_fields():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    receipt = _leaf({"x": 1})
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(receipt)
    assert set(schema["properties"]) == set(receipt)


def test_unexpected_receipt_field_fails_closed_even_if_attacker_rehashes():
    receipt = _leaf({"x": 1})
    receipt["extra_scientific_knob"] = "hidden"
    receipt["receipt_sha256"] = canonical_sha256({k: v for k, v in receipt.items() if k != "receipt_sha256"})
    with pytest.raises(CanonicalError, match="fields"):
        verify_scientific_receipt(receipt, _resolver())


def test_input_digest_string_never_authenticates_missing_or_mutated_input_object():
    input_object = {"source": "fixture", "measured_zero": 0}
    input_sha = canonical_sha256(input_object)
    receipt = make_scientific_receipt(
        payload={"x": 1},
        producer_code_sha=HEX40_A,
        input_shas=[input_sha],
        parent_receipt_shas=[],
        output_sha=DEFAULT_SHAS["output"],
        manifest_sha=DEFAULT_SHAS["manifest"],
        registry_sha=DEFAULT_SHAS["registry"],
        access_policy_sha=DEFAULT_SHAS["access"],
    )
    assert verify_scientific_receipt(receipt, _resolver({input_sha: input_object}))
    with pytest.raises(CanonicalError, match="input"):
        verify_scientific_receipt(receipt, _resolver())
    with pytest.raises(CanonicalError, match="input"):
        verify_scientific_receipt(receipt, _resolver({input_sha: {"source": "mutated"}}))


def test_input_receipt_must_resolve_to_the_exact_requested_receipt_identity():
    input_receipt = _leaf({"input_receipt": 1})
    consumer = make_scientific_receipt(
        payload={"consumer": 1},
        producer_code_sha=HEX40_A,
        input_shas=[input_receipt["receipt_sha256"]],
        parent_receipt_shas=[],
        output_sha=DEFAULT_SHAS["output"],
        manifest_sha=DEFAULT_SHAS["manifest"],
        registry_sha=DEFAULT_SHAS["registry"],
        access_policy_sha=DEFAULT_SHAS["access"],
    )
    assert verify_scientific_receipt(
        consumer,
        _resolver({input_receipt["receipt_sha256"]: input_receipt}),
    )
    other = _leaf({"different": 1})
    with pytest.raises(CanonicalError, match="input"):
        verify_scientific_receipt(
            consumer,
            _resolver({input_receipt["receipt_sha256"]: other}),
        )


def test_authority_bearing_output_manifest_registry_and_access_hashes_require_actual_objects():
    objects = {
        "output": {"artifact": "output-special", "v": 1},
        "manifest": {"artifact": "manifest-special", "v": 1},
        "registry": {"artifact": "registry-special", "v": 1},
        "access": {"artifact": "access-special", "v": 1},
    }
    shas = {name: canonical_sha256(obj) for name, obj in objects.items()}
    receipt = make_scientific_receipt(
        payload={"x": 1},
        producer_code_sha=HEX40_A,
        input_shas=[],
        parent_receipt_shas=[],
        output_sha=shas["output"],
        manifest_sha=shas["manifest"],
        registry_sha=shas["registry"],
        access_policy_sha=shas["access"],
    )
    by_sha = {shas[name]: obj for name, obj in objects.items()}
    assert verify_scientific_receipt(receipt, by_sha.get)
    for missing_name, missing_sha in shas.items():
        with pytest.raises(CanonicalError, match=missing_name if missing_name != "access" else "access"):
            verify_scientific_receipt(
                receipt,
                lambda sha, missing_sha=missing_sha: None if sha == missing_sha else by_sha.get(sha),
            )
