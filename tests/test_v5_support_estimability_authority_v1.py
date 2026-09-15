import dataclasses
import inspect
from pathlib import Path

import pytest

from sea_ad_jepa.v5.support_estimability_authority_v1 import SupportEstimabilityAuthorityV1


def make_authority() -> SupportEstimabilityAuthorityV1:
    return SupportEstimabilityAuthorityV1(
        authority_id="support-invariants",
        full104_substrate_sha256="1" * 64,
        measurement_support_authority_sha256="2" * 64,
        comparable_common_core_artifact_sha256="3" * 64,
        target_eligibility_rule_id="EXPLICIT_MEASURED_TARGET_ELIGIBILITY",
        missing_value_semantics_id="EXPLICIT_MISSINGNESS_SEMANTICS",
        common_core_role_semantics_id="EXPLICIT_COMMON_CORE_ROLE",
        native_support_role_semantics_id="EXPLICIT_NATIVE_SUPPORT_ROLE",
        support_to_latent_semantics_policy_id="EXPLICIT_SUPPORT_TO_LATENT_POLICY",
    )


def test_all_support_semantics_are_explicit() -> None:
    sig = inspect.signature(SupportEstimabilityAuthorityV1)
    for name, param in sig.parameters.items():
        if name == "training_authorized":
            continue
        assert param.default is inspect._empty


def test_support_authority_is_hash_bound_and_training_off() -> None:
    authority = make_authority()
    authority.validate()
    assert authority.training_authorized is False
    assert len(authority.canonical_digest()) == 64


def test_bad_support_root_fails_closed() -> None:
    authority = dataclasses.replace(make_authority(), measurement_support_authority_sha256="bad")
    with pytest.raises(ValueError, match="measurement_support_authority_sha256"):
        authority.validate()


def test_source_does_not_assign_target_components_or_latent_biology() -> None:
    source = Path("src/sea_ad_jepa/v5/support_estimability_authority_v1.py").read_text(encoding="utf-8")
    forbidden = (
        "CALIBRATION_ONLY",
        "CONSISTENCY_DIAGNOSTIC_ONLY",
        "COMMON_CORE_ONLY_TARGET",
        "NATIVE_SUPPORT_TARGET",
        "D_shared",
        "D_private",
        "private biology",
        "biological truth",
    )
    assert [token for token in forbidden if token in source] == []
