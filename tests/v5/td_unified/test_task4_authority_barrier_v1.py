import pytest

from scripts.v5.td_unified.task4_authority_barrier_v1 import (
    Task4BarrierError,
    Task4BarrierStatus,
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


def test_red_overall_blocks_even_when_individual_checks_look_green():
    with pytest.raises(Task4BarrierError):
        require_task4_preauthority_barrier_green(Task4BarrierStatus("RED", _green()))


def test_barrier_cannot_be_constructed_with_promotion_authority():
    with pytest.raises(Task4BarrierError):
        Task4BarrierStatus("GREEN", _green(), authority_effect="PROMOTE")
