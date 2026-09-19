from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.v5 import primary_representation_routing_v1 as routing


def h_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authority(*, v0_sha: str, v1_sha: str) -> routing.PrimaryRepresentationRoutingAuthorityV1:
    return routing.PrimaryRepresentationRoutingAuthorityV1(
        authority_id="TEST_FULL104_PRIMARY_REPRESENTATION_ROUTING_V1",
        full104_block_manifest_sha256=routing.FULL104_BLOCK_MANIFEST_SHA256,
        canonical_registry_sha256=routing.CANONICAL_REGISTRY_SHA256,
        observation_state_sha256=routing.OBSERVATION_STATE_SHA256,
        feature_parent_manifest_sha256=routing.FEATURE_PARENT_MANIFEST_SHA256,
        value_only_selection_artifact_sha256=routing.VALUE_ONLY_SELECTION_ARTIFACT_SHA256,
        v0_full_parent_sha256=v0_sha,
        v1_full_parent_sha256=v1_sha,
        full104_streaming_source_sha256="a" * 64,
    )


def test_global_context_parent_files_are_bound_from_live_bytes(tmp_path, monkeypatch):
    v0 = tmp_path / "v0_full.bin"
    v1 = tmp_path / "v1_full.bin"
    v0.write_bytes(b"current-full104-v0")
    v1.write_bytes(b"current-full104-v1")
    v0_sha = h_bytes(v0)
    v1_sha = h_bytes(v1)
    monkeypatch.setattr(routing, "V0_FULL_PARENT_SHA256", v0_sha)
    monkeypatch.setattr(routing, "V1_FULL_PARENT_SHA256", v1_sha)

    auth = authority(v0_sha=v0_sha, v1_sha=v1_sha)
    auth.bind_global_context_parent_files(
        v0_parent_path=v0,
        v1_parent_path=v1,
    )

    v0.write_bytes(b"historical-or-stale-v0")
    with pytest.raises(ValueError, match="V0 full parent file root mismatch"):
        auth.bind_global_context_parent_files(
            v0_parent_path=v0,
            v1_parent_path=v1,
        )


def test_parent_manifest_must_name_exact_full_parent_roots(tmp_path, monkeypatch):
    v0 = tmp_path / "v0"
    v1 = tmp_path / "v1"
    v0.write_bytes(b"v0")
    v1.write_bytes(b"v1")
    v0_sha = h_bytes(v0)
    v1_sha = h_bytes(v1)
    monkeypatch.setattr(routing, "V0_FULL_PARENT_SHA256", v0_sha)
    monkeypatch.setattr(routing, "V1_FULL_PARENT_SHA256", v1_sha)
    auth = authority(v0_sha=v0_sha, v1_sha=v1_sha)

    selection = {
        "schema": "JEPA_V5_PRIMARY_REPRESENTATION_SELECTION_V1",
        "feature_parent_manifest_sha256": routing.FEATURE_PARENT_MANIFEST_SHA256,
        "primary_molecular_columns": {"start_inclusive": 0, "stop_exclusive": 256},
        "excluded_from_primary_molecular_path": {
            "visibility_columns": {"start_inclusive": 256, "stop_exclusive": 512}
        },
        "training_authorized": False,
    }
    parent = {
        "schema": "JEPA_V5_PRIMARY_REPRESENTATION_FEATURE_PARENTS_V1",
        "full104_expression_manifest_sha256": routing.FULL104_BLOCK_MANIFEST_SHA256,
        "registry_observation_state_binding_sha256": routing.CANONICAL_REGISTRY_SHA256,
        "column_layout": {
            "value": {"start_inclusive": 0, "stop_exclusive": 256},
            "visibility": {"start_inclusive": 256, "stop_exclusive": 512},
        },
        "normalization": "log1p(raw_count * 10000 / full_source_library)__APPLIED_EXACTLY_ONCE",
        "training_authorized": False,
        "views": {
            "V0": {"full_array_sha256": v0_sha, "shape": [4_553_407, 512], "dtype": "float32"},
            "V1": {"full_array_sha256": v1_sha, "shape": [4_553_407, 512], "dtype": "float32"},
        },
    }
    routing.validate_value_only_selection_payload(auth, selection, parent)

    parent["views"]["V1"]["full_array_sha256"] = "b" * 64
    with pytest.raises(ValueError, match="V1 full-parent root mismatch"):
        routing.validate_value_only_selection_payload(auth, selection, parent)


def test_value_only_helper_never_exposes_visibility_half(tmp_path, monkeypatch):
    v0_sha = hashlib.sha256(b"v0").hexdigest()
    v1_sha = hashlib.sha256(b"v1").hexdigest()
    monkeypatch.setattr(routing, "V0_FULL_PARENT_SHA256", v0_sha)
    monkeypatch.setattr(routing, "V1_FULL_PARENT_SHA256", v1_sha)
    auth = authority(v0_sha=v0_sha, v1_sha=v1_sha)
    v0 = np.arange(1024, dtype=np.float32).reshape(2, 512)
    v1 = (np.arange(1024, dtype=np.float32) + 5000).reshape(2, 512)
    o0, o1 = routing.value_only_global_context_views(
        auth,
        v0_full=v0,
        v1_full=v1,
    )
    assert o0.shape == (2, 256)
    assert o1.shape == (2, 256)
    assert np.array_equal(o0, v0[:, :256])
    assert np.array_equal(o1, v1[:, :256])


def test_builder_requires_live_full104_and_parent_file_inputs():
    source = Path(
        "scripts/agent/build_full104_primary_representation_routing_v1_20260919.py"
    ).read_text(encoding="utf-8")
    compile(source, "build_full104_primary_representation_routing_v1_20260919.py", "exec")
    for flag in (
        "--level4-root",
        "--registry",
        "--observation-state",
        "--v0-full-parent",
        "--v1-full-parent",
    ):
        assert flag in source
    assert "sha256_file(path)" in source
    assert "historical, smaller-run, placeholder, or reconstructed bytes" in source
    assert '"production_model_consumer_bound": False' in source
    assert '"physical_v0_v1_parent_bytes_authenticated": True' in source
