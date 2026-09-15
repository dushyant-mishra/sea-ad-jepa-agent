import inspect
from pathlib import Path

import pytest

from sea_ad_jepa.v5.target_identity_shortcut_gate_authority_v1 import TargetIdentityShortcutGateAuthorityV1


def make_authority() -> TargetIdentityShortcutGateAuthorityV1:
    return TargetIdentityShortcutGateAuthorityV1(
        authority_id="prospective-target-identity-gate",
        teacher_target_semantics_sha256="1" * 64,
        representation_authority_sha256="2" * 64,
        base_training_estimand_sha256="3" * 64,
        masking_authority_sha256="4" * 64,
        comparator_ids=("EXPLICIT_COMPARATOR_A", "EXPLICIT_COMPARATOR_B"),
        null_reference_id="EXPLICIT_NULL_REFERENCE",
        primary_metric_id="EXPLICIT_PRIMARY_METRIC",
        molecular_memory_margin_numerator=1,
        molecular_memory_margin_denominator=100,
        max_identity_contribution_numerator=1,
        max_identity_contribution_denominator=10,
        rare_address_guardrail_authority_sha256="5" * 64,
        shared_current_failure_semantics_id="EXPLICIT_FAILURE_SEMANTICS",
    )


def test_all_decision_inputs_are_explicit() -> None:
    sig = inspect.signature(TargetIdentityShortcutGateAuthorityV1)
    for name, param in sig.parameters.items():
        if name == "training_authorized":
            continue
        assert param.default is inspect._empty


def test_gate_binds_rule_without_training_authority() -> None:
    authority = make_authority()
    authority.validate()
    assert authority.training_authorized is False
    assert authority.molecular_memory_margin == pytest.approx(0.01)
    assert authority.max_identity_contribution == pytest.approx(0.1)
    assert len(authority.canonical_digest()) == 64


def test_duplicate_comparators_and_invalid_fraction_fail_closed() -> None:
    values = make_authority().__dict__.copy()
    values["comparator_ids"] = ("A", "A")
    with pytest.raises(ValueError, match="comparator_ids"):
        TargetIdentityShortcutGateAuthorityV1(**values).validate()
    values = make_authority().__dict__.copy()
    values["max_identity_contribution_numerator"] = 2
    values["max_identity_contribution_denominator"] = 1
    with pytest.raises(ValueError, match="max_identity_contribution"):
        TargetIdentityShortcutGateAuthorityV1(**values).validate()


def test_source_does_not_hardcode_comparators_or_thresholds() -> None:
    source = Path("src/sea_ad_jepa/v5/target_identity_shortcut_gate_authority_v1.py").read_text(encoding="utf-8")
    forbidden = (
        "IDENTITY_ONLY_SHARED_CURRENT",
        "IDENTITY_ONLY_FIXED_ADDRESS",
        "FULL_SHARED_CURRENT",
        "FULL_FIXED_ADDRESS",
        "0.01",
        "0.1",
    )
    assert [token for token in forbidden if token in source] == []
