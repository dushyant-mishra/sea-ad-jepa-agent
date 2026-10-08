import dataclasses
import inspect
from pathlib import Path

import pytest

from sea_ad_jepa.v5.target_address_query_authority_v1 import TargetAddressQueryAuthorityV1


def make_authority() -> TargetAddressQueryAuthorityV1:
    return TargetAddressQueryAuthorityV1(
        authority_id="prospective-target-address-query",
        address_registry_authority_sha256="1" * 64,
        query_provider_id="EXPLICIT_CALLER_SELECTED_PROVIDER",
        query_artifact_sha256="2" * 64,
        replay_policy_id="EXPLICIT_REPLAY_POLICY",
        parameter_sharing_policy_id="EXPLICIT_PARAMETER_SHARING_POLICY",
        gradient_policy_id="EXPLICIT_GRADIENT_POLICY",
    )


def test_all_scientific_query_choices_are_explicit() -> None:
    sig = inspect.signature(TargetAddressQueryAuthorityV1)
    for name, param in sig.parameters.items():
        if name == "training_authorized":
            continue
        assert param.default is inspect._empty


def test_authority_binds_provider_replay_sharing_and_gradient_policy() -> None:
    authority = make_authority()
    authority.validate()
    fields = {f.name for f in dataclasses.fields(authority)}
    assert {"query_provider_id", "replay_policy_id", "parameter_sharing_policy_id", "gradient_policy_id"} <= fields
    assert authority.training_authorized is False
    assert len(authority.canonical_digest()) == 64


def test_bad_query_artifact_root_fails_closed() -> None:
    authority = dataclasses.replace(make_authority(), query_artifact_sha256="bad")
    with pytest.raises(ValueError, match="query_artifact_sha256"):
        authority.validate()


def test_source_does_not_pick_shared_online_identity_or_fixed_codebook_candidate() -> None:
    source = Path("src/sea_ad_jepa/v5/target_address_query_authority_v1.py").read_text(encoding="utf-8")
    forbidden = (
        "online.tokenizer.gene_identity",
        "FIXED_ADDRESS_CODEBOOK",
        "FIXED_SEPARATE_ADDRESS",
        "shared_online_identity",
        "target_blocks: int = 16",
        "0.40",
    )
    assert [token for token in forbidden if token in source] == []
