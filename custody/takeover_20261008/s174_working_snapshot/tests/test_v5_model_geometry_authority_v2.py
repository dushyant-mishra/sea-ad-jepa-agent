from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.model_geometry_authority_v2 import ModelGeometryAuthorityV2


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="JEPA_V5_MODEL_GEOMETRY_AUTHORITY_V2",
        qualified_dimension_authority_sha256=h("dimension"),
        dimension_selection_artifact_sha256=h("dimension-selection"),
        rank_to_geometry_rule_authority_sha256=h("rank-rule"),
        geometry_artifact_sha256=h("geometry-artifact"),
        protected_registry_authority_sha256=h("protected-registry"),
        memorization_qualification_authority_sha256=h("memorization-qualification"),
        geometry_schema_id="DATA_DERIVED_JEPA_GEOMETRY_V2",
        rank_to_geometry_rule_id="FROZEN_DATA_DERIVED_RANK_TO_GEOMETRY_RULE_V1",
        memorization_policy_id="GEOMETRY_SPECIFIC_MEMORIZATION_QUALIFICATION_REQUIRED_V1",
        training_authorized=False,
    )
    values.update(updates)
    return ModelGeometryAuthorityV2(**values)


def test_valid_geometry_v2_is_deterministic() -> None:
    a = authority(); a.validate()
    assert a.canonical_digest() == authority().canonical_digest()


def test_geometry_roles_are_sha_bound_and_distinct() -> None:
    same = h("same")
    with pytest.raises(ValueError, match="distinct"):
        authority(
            geometry_artifact_sha256=same,
            memorization_qualification_authority_sha256=same,
        ).validate()
    with pytest.raises(ValueError, match="geometry_artifact_sha256"):
        authority(geometry_artifact_sha256="width=160").validate()


def test_geometry_schema_and_rule_are_enumerated_not_historical_defaults() -> None:
    with pytest.raises(ValueError, match="geometry_schema_id"):
        authority(geometry_schema_id="HISTORICAL_160_4HEAD_6BLOCK").validate()
    with pytest.raises(ValueError, match="rank_to_geometry_rule_id"):
        authority(rank_to_geometry_rule_id="JUST_USE_512").validate()


def test_geometry_specific_memorization_rerun_is_mandatory() -> None:
    with pytest.raises(ValueError, match="memorization_policy_id"):
        authority(memorization_policy_id="STAGE_A_OLD_RESULT_IS_ENOUGH").validate()


def test_geometry_v2_cannot_authorize_training() -> None:
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()
