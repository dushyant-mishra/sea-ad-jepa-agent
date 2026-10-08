import inspect
from pathlib import Path

import pytest

from sea_ad_jepa.v5.primary_representation_authority_v1 import (
    PrimaryRepresentationAuthorityV1,
)


def make_authority() -> PrimaryRepresentationAuthorityV1:
    return PrimaryRepresentationAuthorityV1(
        authority_id="prospective-primary-representation",
        substrate_authority_sha256="1" * 64,
        support_authority_sha256="2" * 64,
        feature_artifact_sha256="3" * 64,
        feature_selection_artifact_sha256="4" * 64,
        representation_semantics_id="EXPLICIT_CALLER_SELECTED_REPRESENTATION",
        primary_channel_role_id="EXPLICIT_PRIMARY_CHANNEL_ROLE",
        observation_channel_policy_id="EXPLICIT_OBSERVATION_CHANNEL_POLICY",
    )


def test_representation_choices_have_no_defaults() -> None:
    sig = inspect.signature(PrimaryRepresentationAuthorityV1)
    for name, param in sig.parameters.items():
        if name == "training_authorized":
            continue
        assert param.default is inspect._empty


def test_representation_authority_is_hash_bound_and_cannot_authorize_training() -> None:
    authority = make_authority()
    authority.validate()
    assert authority.training_authorized is False
    assert len(authority.canonical_digest()) == 64


def test_bad_feature_selection_root_fails_closed() -> None:
    authority = PrimaryRepresentationAuthorityV1(
        authority_id="x",
        substrate_authority_sha256="1" * 64,
        support_authority_sha256="2" * 64,
        feature_artifact_sha256="3" * 64,
        feature_selection_artifact_sha256="bad",
        representation_semantics_id="r",
        primary_channel_role_id="p",
        observation_channel_policy_id="o",
    )
    with pytest.raises(ValueError, match="feature_selection_artifact_sha256"):
        authority.validate()


def test_source_does_not_pick_current_candidate_or_restore_observation_channels() -> None:
    source = Path("src/sea_ad_jepa/v5/primary_representation_authority_v1.py").read_text(encoding="utf-8")
    forbidden = (
        "VALUE_ONLY_256",
        "VISIBILITY_ONLY",
        "FULL_512",
        "visibility channels are molecular",
        "width=256",
        "width = 256",
    )
    assert [token for token in forbidden if token in source] == []
