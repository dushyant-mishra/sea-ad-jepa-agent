from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.current_runtime_source_authority_v1 import CurrentRuntimeSourceAuthorityV1


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="JEPA_V5_CURRENT_RUNTIME_SOURCE_AUTHORITY_V1",
        source_manifest_sha256=h("source-manifest"),
        source_root_sha256=h("source-root"),
        runtime_environment_artifact_sha256=h("runtime-environment"),
        entrypoint_source_sha256=h("entrypoint-source"),
        source_packaging_policy_id="MULTIFILE_SOURCE_MANIFEST_AND_ROOT_V1",
        entrypoint_policy_id="CURRENT_V5_ENTRYPOINT_ONLY__NO_V4_PRODUCTION_UPDATE_V1",
        runtime_abi_id="CPYTHON_RUNTIME_ABI_EXACTLY_RECORDED_V1",
        training_authorized=False,
    )
    values.update(updates)
    return CurrentRuntimeSourceAuthorityV1(**values)


def test_valid_runtime_source_authority_is_deterministic() -> None:
    a = authority(); a.validate()
    assert a.canonical_digest() == authority().canonical_digest()


def test_runtime_requires_manifest_root_environment_and_entrypoint_as_distinct_roots() -> None:
    same = h("same")
    with pytest.raises(ValueError, match="distinct"):
        authority(source_manifest_sha256=same, source_root_sha256=same).validate()
    with pytest.raises(ValueError, match="source_manifest_sha256"):
        authority(source_manifest_sha256="one-file.py").validate()


def test_historical_v4_entrypoint_cannot_be_selected() -> None:
    with pytest.raises(ValueError, match="entrypoint_policy_id"):
        authority(entrypoint_policy_id="V4_PRODUCTION_UPDATE").validate()
    with pytest.raises(ValueError, match="source_packaging_policy_id"):
        authority(source_packaging_policy_id="SINGLE_FILE_TRUST_ME").validate()


def test_runtime_abi_semantics_are_enumerated_not_free_form() -> None:
    with pytest.raises(ValueError, match="runtime_abi_id"):
        authority(runtime_abi_id="python-whatever").validate()


def test_runtime_source_authority_cannot_authorize_training() -> None:
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()
