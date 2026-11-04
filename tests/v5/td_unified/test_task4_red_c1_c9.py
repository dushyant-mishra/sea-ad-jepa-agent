"""RED-only preservation of Task 4 C1-C9 authority attacks.

This file intentionally targets Task 4 public interfaces that do not yet exist.
All hidden material is synthetic. No authority is granted by these tests.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def _load(name: str):
    return importlib.import_module(f"scripts.v5.td_unified.{name}")


def test_revoked_identity_cannot_reenter_with_added_cosmetic_restriction():
    m = _load("task4_custody_store_v1")
    base = {
        "unit_id": "G8",
        "producer_actor_identity": "producer-sha",
        "executor_actor_identity": "executor-sha",
        "manifest_sha": "a" * 64,
        "authority_scope": "NO_TRAINING_AUTHORITY",
        "authority_restrictions": ["A"],
        "qualification_stage": "SAME_CODE_PATH",
        "active_lineage_status": "ACTIVE",
    }
    changed = dict(base, authority_restrictions=["A", "COSMETIC"])
    assert m.revocation_subject_identity(base) == m.revocation_subject_identity(changed)


def test_revoked_identity_cannot_reenter_with_reordered_restrictions():
    m = _load("task4_custody_store_v1")
    a = {
        "unit_id": "G8",
        "producer_actor_identity": "producer-sha",
        "executor_actor_identity": "executor-sha",
        "manifest_sha": "a" * 64,
        "authority_scope": "NO_TRAINING_AUTHORITY",
        "authority_restrictions": ["A", "B"],
    }
    b = dict(a, authority_restrictions=["B", "A"])
    assert m.revocation_subject_identity(a) == m.revocation_subject_identity(b)


def test_revoked_identity_target_fork_cannot_evade_anchor():
    m = _load("task4_custody_store_v1")
    payload = {
        "unit_id": "G8",
        "producer_actor_identity": "producer-sha",
        "executor_actor_identity": "executor-sha",
        "manifest_sha": "a" * 64,
        "target_identity_sha": "t" * 64,
        "authority_restrictions": ["A"],
    }
    same_science_cosmetic = dict(payload, authority_restrictions=["A", "DISPLAY_ONLY"])
    assert m.revocation_subject_identity(payload) == m.revocation_subject_identity(same_science_cosmetic)


def test_nested_revoked_prerequisite_depth2_blocks_authority():
    m = _load("task4_authority_barrier_v1")
    status = m.Task4BarrierStatus(
        overall="RED",
        checks={"C1_FULL_PREREQUISITE_REVOCATION": "FAIL_DEPTH_2"},
        authority_effect="NONE",
        claim_scope="POOLED_DONOR_LEVEL_ONLY",
    )
    with pytest.raises(Exception):
        m.require_task4_preauthority_barrier_green(status)


def test_nested_revoked_prerequisite_depth3_blocks_authority():
    m = _load("task4_authority_barrier_v1")
    status = m.Task4BarrierStatus(
        overall="RED",
        checks={"C1_FULL_PREREQUISITE_REVOCATION": "FAIL_DEPTH_3"},
        authority_effect="NONE",
        claim_scope="POOLED_DONOR_LEVEL_ONLY",
    )
    with pytest.raises(Exception):
        m.require_task4_preauthority_barrier_green(status)


def test_fresh_process_cannot_erase_revocation(tmp_path: Path):
    m = _load("task4_custody_store_v1")
    assert hasattr(m.PersistentCustodyStore, "open")
    assert hasattr(m.PersistentCustodyStore, "assert_subject_not_revoked")


def test_truncated_rechained_ledger_cannot_regain_authority(tmp_path: Path):
    m = _load("task4_custody_store_v1")
    assert hasattr(m.PersistentCustodyStore, "replay")


def test_task4_has_no_legacy_registry_import_route():
    m = _load("task4_registry_adapter_v1")
    m.assert_no_legacy_registry_dependency((Path("scripts/v5/td_unified"),))


def test_ready_diagnostic_cannot_be_used_as_authority():
    m = _load("task4_registry_adapter_v1")
    result = m.diagnostic_real_reference_ready(None, None)
    assert result["authority_effect"] == "NONE"


def test_actor_name_without_attestation_cannot_authorize_action():
    m = _load("task4_actor_attestation_v1")
    with pytest.raises(Exception):
        m.validate_actor_action(None, actor_registry=None, frozen_policy=None, verifier=None)


def test_revocation_requires_frozen_privileged_actor_policy():
    m = _load("task4_actor_attestation_v1")
    with pytest.raises(Exception):
        m.validate_actor_action(None, actor_registry={}, frozen_policy={}, verifier=None)


def test_unknown_requirement_class_fails_closed():
    m = _load("task4_requirement_policy_v1")
    with pytest.raises(Exception):
        m.RequirementClass("UNKNOWN_DYNAMIC_CLASS")


def test_registry_unit_invalid_under_task1_law_is_refused_at_task4_boundary():
    m = _load("task4_registry_adapter_v1")
    with pytest.raises(Exception):
        m.build_validated_registry_unit(
            {
                "unit_id": "BAD",
                "authority_scope": "NO_TRAINING_AUTHORITY",
                "qualification_stage": "TRAINING_AUTHORIZED",
            }
        )


def test_same_process_fixture_state_cannot_upgrade_to_authoritative_mode():
    m = _load("task4_authority_barrier_v1")
    status = m.Task4BarrierStatus(
        overall="GREEN",
        checks={"C9_PROCESS_ISOLATION": "FIXTURE_ONLY"},
        authority_effect="NONE",
        claim_scope="POOLED_DONOR_LEVEL_ONLY",
    )
    assert status.authority_effect == "NONE"
    with pytest.raises(Exception):
        m.require_task4_preauthority_barrier_green(status)
