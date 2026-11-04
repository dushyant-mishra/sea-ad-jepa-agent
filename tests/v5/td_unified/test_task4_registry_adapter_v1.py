from pathlib import Path

import pytest

from scripts.v5.td_unified.task4_registry_adapter_v1 import (
    Task4RegistryAdapterError,
    assert_no_legacy_registry_dependency,
    build_validated_registry_unit,
    diagnostic_real_reference_ready,
)


def test_invalid_task1_scope_stage_is_refused_before_registry_construction():
    with pytest.raises(Task4RegistryAdapterError):
        build_validated_registry_unit(
            {
                "unit_id": "BAD",
                "qualification_stage": "TRAINING_AUTHORIZED",
                "active_lineage_status": "ACTIVE",
                "authority_scope": "UNIT:BAD",
                "authority_restrictions": ["NO_TRAINING_AUTHORITY"],
            }
        )


def test_ready_diagnostic_is_explicitly_nonauthorizing_even_when_unavailable():
    result = diagnostic_real_reference_ready(None, None)
    assert result["authority_effect"] == "NONE"
    assert result["ready"] is False


def test_task4_import_firewall_detects_direct_legacy_import(tmp_path: Path):
    p = tmp_path / "task4_bad.py"
    p.write_text("from scripts.v5.td_unified import registry_v1_legacy\n", encoding="utf-8")
    with pytest.raises(Task4RegistryAdapterError):
        assert_no_legacy_registry_dependency((p,))


def test_task4_import_firewall_ignores_frozen_registry_facade_legacy_internals():
    assert_no_legacy_registry_dependency((Path("scripts/v5/td_unified"),))
