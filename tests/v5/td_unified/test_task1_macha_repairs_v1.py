from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import numpy as np
import pytest

import scripts.v5.td_unified.canonical_v1 as canonical_mod
from scripts.v5.td_unified.canonical_v1 import (
    CanonicalError,
    canonical_bytes,
    canonical_sha256,
    make_scientific_receipt,
    verify_scientific_receipt,
)
from scripts.v5.td_unified.authority_v1 import (
    ActiveLineageStatus,
    AuthorityError,
    AuthorityRecord,
    QualificationStage,
    validate_authority_record,
)

ROOT = Path(__file__).resolve().parents[3]
AUTH_SCHEMA = ROOT / "schemas" / "target_discovery" / "unified_v1" / "authority_record_v1.json"


def _git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


CODE_BYTES = b"print('producer')\n"
CODE_SHA = _git_blob_sha1(CODE_BYTES)

ROLE_OBJECTS = {
    "output": {"artifact": "output", "object_role": "OUTPUT", "version": 1},
    "manifest": {"artifact": "manifest", "object_role": "MANIFEST", "version": 1},
    "registry": {"artifact": "registry", "object_role": "REGISTRY", "version": 1},
    "access": {"artifact": "access", "object_role": "ACCESS_POLICY", "version": 1},
}
ROLE_SHAS = {name: canonical_sha256(obj) for name, obj in ROLE_OBJECTS.items()}


def _resolver(extra=None):
    mapping = {CODE_SHA: CODE_BYTES}
    mapping.update({ROLE_SHAS[name]: obj for name, obj in ROLE_OBJECTS.items()})
    if extra:
        mapping.update(extra)
    return mapping.get


def _receipt(**overrides):
    kwargs = {
        "payload": {"fixed": 1},
        "producer_code_sha": CODE_SHA,
        "input_shas": [],
        "parent_receipt_shas": [],
        "output_sha": ROLE_SHAS["output"],
        "manifest_sha": ROLE_SHAS["manifest"],
        "registry_sha": ROLE_SHAS["registry"],
        "access_policy_sha": ROLE_SHAS["access"],
    }
    kwargs.update(overrides)
    return make_scientific_receipt(**kwargs)


class EvilFloat(float):
    def __repr__(self):
        return "999"


class EvilInt(int):
    def __str__(self):
        return "777"


class EvilStr(str):
    def replace(self, *_args, **_kwargs):
        return 'FORGED"'


def test_t1_b1_builtin_subclasses_cannot_control_canonical_bytes():
    for value in (EvilFloat(1.5), EvilInt(7), EvilStr("safe")):
        with pytest.raises(CanonicalError, match="unsupported|exact|subclass"):
            canonical_bytes(value)


def test_t1_b1_numpy_scalar_policy_is_old_task1_compatible_and_frozen():
    assert canonical_bytes(np.bool_(True)) == b"true"
    assert canonical_bytes(np.int64(7)) == b"7"
    assert canonical_bytes(np.float64(1.5)) == b"1.5"
    assert canonical_bytes(np.float32(0.1)) == b"0.10000000149011612"
    if np.dtype(np.longdouble).itemsize > 8:
        with pytest.raises(CanonicalError, match="wider|float64"):
            canonical_bytes(np.longdouble("1.5"))


def test_t1_b2_producer_code_identity_must_resolve_and_recompute():
    receipt = _receipt()
    assert verify_scientific_receipt(receipt, _resolver())
    with pytest.raises(CanonicalError, match="producer|code"):
        verify_scientific_receipt(receipt, lambda sha: None if sha == CODE_SHA else _resolver()(sha))
    with pytest.raises(CanonicalError, match="producer|code"):
        verify_scientific_receipt(receipt, _resolver({CODE_SHA: b"print('mutated')\n"}))


def test_t1_b3_authority_dependency_roles_are_typed_and_cross_role_unique():
    receipt = _receipt()
    assert verify_scientific_receipt(receipt, _resolver())

    wrong_manifest = {"artifact": "manifest", "object_role": "OUTPUT", "version": 1}
    wrong_manifest_sha = canonical_sha256(wrong_manifest)
    bad_role = _receipt(manifest_sha=wrong_manifest_sha)
    with pytest.raises(CanonicalError, match="role|manifest"):
        verify_scientific_receipt(bad_role, _resolver({wrong_manifest_sha: wrong_manifest}))

    duplicate = _receipt(manifest_sha=ROLE_SHAS["output"])
    with pytest.raises(CanonicalError, match="role|distinct|duplicate"):
        verify_scientific_receipt(duplicate, _resolver())


def test_t1_b3_plain_untyped_object_cannot_fill_authority_role():
    plain = {"artifact": "untyped", "version": 1}
    plain_sha = canonical_sha256(plain)
    receipt = _receipt(output_sha=plain_sha)
    with pytest.raises(CanonicalError, match="role|output"):
        verify_scientific_receipt(receipt, _resolver({plain_sha: plain}))


def test_t1_b4_scope_grammar_is_closed_and_restrictions_are_separate():
    params = inspect.signature(AuthorityRecord).parameters
    assert "authority_restrictions" in params

    for bad_scope in ("PIPELINE", "PROJECT_WIDE", "ALL", "TRAINING_PROJECT", "Project Training"):
        with pytest.raises(AuthorityError, match="scope"):
            validate_authority_record(
                AuthorityRecord(
                    unit_id="G8",
                    qualification_stage=QualificationStage.FIXTURE_SAME_INTERFACE,
                    active_lineage_status=ActiveLineageStatus.ACTIVE,
                    authority_scope=bad_scope,
                    authority_restrictions=(),
                )
            )


def test_t1_b4_scope_stage_table_blocks_authority_widening():
    unit = AuthorityRecord(
        unit_id="G8",
        qualification_stage=QualificationStage.KNOWN_TRUTH_QUALIFIED,
        active_lineage_status=ActiveLineageStatus.ACTIVE,
        authority_scope="UNIT:G8",
        authority_restrictions=("NO_TRAINING_AUTHORITY",),
    )
    assert validate_authority_record(unit) is unit

    with pytest.raises(AuthorityError, match="scope|stage"):
        validate_authority_record(
            AuthorityRecord(
                unit_id="G8",
                qualification_stage=QualificationStage.TRAINING_ELIGIBLE,
                active_lineage_status=ActiveLineageStatus.ACTIVE,
                authority_scope="UNIT:G8",
                authority_restrictions=(),
            )
        )
    with pytest.raises(AuthorityError, match="scope|stage"):
        validate_authority_record(
            AuthorityRecord(
                unit_id="TD",
                qualification_stage=QualificationStage.FIXTURE_SAME_INTERFACE,
                active_lineage_status=ActiveLineageStatus.ACTIVE,
                authority_scope="PIPELINE:TD",
                authority_restrictions=(),
            )
        )
    with pytest.raises(AuthorityError, match="scope|stage"):
        validate_authority_record(
            AuthorityRecord(
                unit_id="PROJECT",
                qualification_stage=QualificationStage.KNOWN_TRUTH_QUALIFIED,
                active_lineage_status=ActiveLineageStatus.ACTIVE,
                authority_scope="PROJECT",
                authority_restrictions=(),
            )
        )


def test_t1_b4_authority_schema_freezes_scope_grammar_and_restrictions_field():
    schema = json.loads(AUTH_SCHEMA.read_text(encoding="utf-8"))
    assert "authority_restrictions" in schema["properties"]
    assert "authority_restrictions" in schema["required"]
    assert schema["properties"]["authority_scope"]["pattern"] == r"^(?:UNIT:[A-Za-z0-9_.-]+|PIPELINE:[A-Za-z0-9_.-]+|PROJECT)$"


def test_t1_b5_known_answer_fingerprints_freeze_identity_format():
    assert canonical_sha256({"a": 1, "b": [True, None, 1.0]}) == "8b441603e35b6bb16384a91a82453ad13144a79cc9b5b15750a4dc00d09030e9"
    assert CODE_SHA == "690c626dea80137c7fde8eac31590f8972893d83"
    receipt = _receipt()
    assert receipt["receipt_sha256"] == "7fd72094c9ce8b73391a932a329c828752859aba07f7309287f647d507c77578"
    assert "FINGERPRINT FORMAT V1" in (canonical_mod.__doc__ or "")
