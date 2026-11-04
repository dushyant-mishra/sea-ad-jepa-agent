"""Independent read-only hostile tests for frozen Task3 history-custody validation.

These are NOT a repair of accepted Task 3 or Task 4. New test-only route:
  R1: a subclass overrides validate_current and is accepted by _require_history_custody.
  R2: the original exact-type custody object can have its HMAC head overwritten
      after lawful genesis, but validate_current does not check chain/provenance.
A lawful current empty genesis still succeeds. No protected values, new world,
registered gate, authority, training or model execution.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

import pytest

from scripts.v5.td_unified import registry_v1 as registry


def _genesis():
    return registry.TDQualificationRegistry((), (), (), (), actor_registry_sha="a" * 64)


class _NonValidatingHistoryCustody(registry.RegistryHistoryCustody):
    def __init__(self):
        pass

    def validate_current(self, snapshot):
        return None


def test_r1_red_task3_refuses_overridden_history_validator():
    """RED: a forged subclass must not pass the exact external custody boundary."""
    with pytest.raises(registry.RegistryError):
        registry._require_history_custody(
            object(), _NonValidatingHistoryCustody(), context="frozen Task3 independent hostile"
        )


def test_r2_red_task3_refuses_mutated_hmac_history_head():
    """RED: exact class type and a self-consistent snapshot are not HMAC custody proof."""
    genesis = _genesis()
    custody = registry.RegistryHistoryCustody(genesis, attestation_key=b"original-harness-secret")
    assert custody.head_attestation != "f" * 64
    custody._head = "f" * 64
    with pytest.raises(registry.RegistryError):
        registry._require_history_custody(genesis, custody, context="frozen Task3 independent hostile")


def test_guard_lawful_task3_history_genesis_still_passes():
    genesis = _genesis()
    custody = registry.RegistryHistoryCustody(genesis, attestation_key=b"original-harness-secret")
    assert registry._require_history_custody(
        genesis, custody, context="lawful current genesis"
    ) is custody
