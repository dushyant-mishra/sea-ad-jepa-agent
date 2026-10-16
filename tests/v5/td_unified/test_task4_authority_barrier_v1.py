import pytest

from scripts.v5.td_unified import task4_registry_adapter_v1 as registry_adapter
from scripts.v5.td_unified.task4_authority_barrier_v1 import (
    Task4BarrierError,
    Task4BarrierStatus,
    evaluate_task4_preauthority_barrier,
    require_task4_preauthority_barrier_green,
)


def _green():
    return {
        "C1_PERSISTENT_REVOCATION": "PERSISTENT_EXTERNAL",
        "C3_CURRENT_REGISTRY": "PASS",
        "C4_DIAGNOSTIC_ONLY": "PASS",
        "C5_ACTOR_CREDENTIALS": "AUTHENTICATED_EXTERNAL",
        "C6_REVOCATION_ACTOR_POLICY": "PASS",
        "C7_REQUIREMENT_CLASSES": "PASS",
        "C8_TASK1_CONSTRUCTION_LAW": "PASS",
        "C9_PROCESS_ISOLATION": "PASS",
        "R5_CLAIM_SCOPE": "PASS",
    }


def test_green_barrier_still_has_no_authority_effect():
    s = Task4BarrierStatus("GREEN", _green())
    assert s.authority_effect == "NONE"
    assert s.claim_scope == "POOLED_DONOR_LEVEL_ONLY"
    require_task4_preauthority_barrier_green(s)


@pytest.mark.parametrize("key", sorted(_green()))
def test_each_missing_or_fixture_only_condition_blocks(key):
    checks = _green()
    checks[key] = "FIXTURE_ONLY"
    s = Task4BarrierStatus("GREEN", checks)
    with pytest.raises(Task4BarrierError):
        require_task4_preauthority_barrier_green(s)


@pytest.mark.parametrize("key", sorted(_green()))
def test_each_absent_required_condition_blocks(key):
    checks = _green()
    checks.pop(key)
    with pytest.raises(Task4BarrierError):
        require_task4_preauthority_barrier_green(Task4BarrierStatus("GREEN", checks))


def test_generic_green_alias_cannot_replace_exact_check_value():
    checks = _green()
    checks["C1_PERSISTENT_REVOCATION"] = "GREEN"
    with pytest.raises(Task4BarrierError):
        require_task4_preauthority_barrier_green(Task4BarrierStatus("GREEN", checks))


def test_unknown_extra_condition_blocks_closed_barrier():
    checks = _green()
    checks["CALLER_MINTED_CHECK"] = "PASS"
    with pytest.raises(Task4BarrierError):
        require_task4_preauthority_barrier_green(Task4BarrierStatus("GREEN", checks))


def test_empty_green_status_cannot_unlock_barrier():
    with pytest.raises(Task4BarrierError):
        require_task4_preauthority_barrier_green(Task4BarrierStatus("GREEN", {}))


def test_red_overall_blocks_even_when_individual_checks_look_green():
    with pytest.raises(Task4BarrierError):
        require_task4_preauthority_barrier_green(Task4BarrierStatus("RED", _green()))


def test_barrier_cannot_be_constructed_with_promotion_authority():
    with pytest.raises(Task4BarrierError):
        Task4BarrierStatus("GREEN", _green(), authority_effect="PROMOTE")


def test_self_asserted_actor_context_mapping_cannot_make_barrier_green(monkeypatch):
    monkeypatch.setattr(registry_adapter, "validate_registry_snapshot_for_task4", lambda *args, **kwargs: None)

    class Replay:
        authoritative = True
        head = "h" * 64

    class Store:
        def replay(self):
            return Replay()

    raw_context = {
        "actor_attestation_mode": "AUTHENTICATED_EXTERNAL",
        "revocation_policy_current": True,
        "requirement_policy_current": True,
        "construction_law_current": True,
        "process_isolation": "EXTERNAL_HARNESS",
    }
    status = evaluate_task4_preauthority_barrier(
        "G8",
        object(),
        custody_store=Store(),
        expected_head="h" * 64,
        actor_context=raw_context,
    )
    assert status.overall == "RED"
    assert status.checks["C5_ACTOR_CREDENTIALS"] == "FAIL"
    assert status.checks["C9_PROCESS_ISOLATION"] == "FAIL"
