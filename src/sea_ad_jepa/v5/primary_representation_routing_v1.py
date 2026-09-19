"""Executable routing boundary for the current FULL104 primary representation.

This module resolves a semantic ambiguity without selecting model geometry.

There are two distinct molecular/context routes:
1. Remaining-RNA route: canonical address-indexed expression values from the
   authenticated FULL104 Level-4 stream, normalized exactly once as log1p10K.
2. Lawful global-context route: the value half [0:256) of each authenticated
   V0/V1 512-channel cell-level feature parent.

The V0/V1 visibility half [256:512) is observation/QC information only.  It is
never silently concatenated into either molecular route.

This module does not select a target panel, masking policy, latent dimension,
teacher/student geometry, EMA schedule, or training authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterator, Mapping

import numpy as np
import scipy.sparse as sp

from .full104_masking_streaming_executor_v1 import (
    Full104ManifestStreamV1,
    StreamingBlock,
)

FULL104_BLOCK_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
CANONICAL_REGISTRY_SHA256 = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
OBSERVATION_STATE_SHA256 = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
FEATURE_PARENT_MANIFEST_SHA256 = "0ceec0884d8bb03b00046e9d57ffceadae0c2d389953e51b12c20ae3614a8eaa"
VALUE_ONLY_SELECTION_ARTIFACT_SHA256 = "5802bd0b71d7ecccf3feddef6ba1edbf88f708f264b853b9596207d7568c68ce"
V0_FULL_PARENT_SHA256 = "3b3f102c6767727ca4ab56832f8e70baf203676d6b65973c42903b22b6d56ada"
V1_FULL_PARENT_SHA256 = "c41df46d842d643f04566b8523a8aa711fa54bec1c836e0b394c0146017f231c"

RNA_VALUE_ROUTE_ID = "AUTHENTICATED_FULL104_CANONICAL_ADDRESS_LOG1P10K_VALUES_V1"
GLOBAL_CONTEXT_ROUTE_ID = "AUTHENTICATED_V0_V1_VALUE_CHANNELS_0_256_GLOBAL_CONTEXT_ONLY_V1"
VISIBILITY_POLICY_ID = "V0_V1_CHANNELS_256_512_OBSERVATION_QC_ONLY__FORBIDDEN_FROM_MOLECULAR_VALUE_ROUTES_V1"

VALUE_START = 0
VALUE_STOP = 256
VISIBILITY_START = 256
VISIBILITY_STOP = 512
PARENT_WIDTH = 512


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class PrimaryRepresentationRoutingAuthorityV1:
    authority_id: str
    full104_block_manifest_sha256: str
    canonical_registry_sha256: str
    observation_state_sha256: str
    feature_parent_manifest_sha256: str
    value_only_selection_artifact_sha256: str
    v0_full_parent_sha256: str
    v1_full_parent_sha256: str
    full104_streaming_source_sha256: str
    rna_value_route_id: str = RNA_VALUE_ROUTE_ID
    global_context_route_id: str = GLOBAL_CONTEXT_ROUTE_ID
    visibility_policy_id: str = VISIBILITY_POLICY_ID
    value_start: int = VALUE_START
    value_stop: int = VALUE_STOP
    visibility_start: int = VISIBILITY_START
    visibility_stop: int = VISIBILITY_STOP
    parent_width: int = PARENT_WIDTH
    model_geometry_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        if _sha(self.full104_block_manifest_sha256, "full104_block_manifest_sha256") != FULL104_BLOCK_MANIFEST_SHA256:
            raise ValueError("representation routing binds a different FULL104 manifest")
        if _sha(self.canonical_registry_sha256, "canonical_registry_sha256") != CANONICAL_REGISTRY_SHA256:
            raise ValueError("representation routing binds a different canonical registry")
        if _sha(self.observation_state_sha256, "observation_state_sha256") != OBSERVATION_STATE_SHA256:
            raise ValueError("representation routing binds a different observation state")
        if _sha(self.feature_parent_manifest_sha256, "feature_parent_manifest_sha256") != FEATURE_PARENT_MANIFEST_SHA256:
            raise ValueError("representation routing binds a different V0/V1 parent manifest")
        if _sha(self.value_only_selection_artifact_sha256, "value_only_selection_artifact_sha256") != VALUE_ONLY_SELECTION_ARTIFACT_SHA256:
            raise ValueError("representation routing binds a different value-only selection")
        if _sha(self.v0_full_parent_sha256, "v0_full_parent_sha256") != V0_FULL_PARENT_SHA256:
            raise ValueError("representation routing binds a different V0 full parent")
        if _sha(self.v1_full_parent_sha256, "v1_full_parent_sha256") != V1_FULL_PARENT_SHA256:
            raise ValueError("representation routing binds a different V1 full parent")
        _sha(self.full104_streaming_source_sha256, "full104_streaming_source_sha256")
        if self.rna_value_route_id != RNA_VALUE_ROUTE_ID:
            raise ValueError("rna_value_route_id mismatch")
        if self.global_context_route_id != GLOBAL_CONTEXT_ROUTE_ID:
            raise ValueError("global_context_route_id mismatch")
        if self.visibility_policy_id != VISIBILITY_POLICY_ID:
            raise ValueError("visibility_policy_id mismatch")
        if (
            self.value_start,
            self.value_stop,
            self.visibility_start,
            self.visibility_stop,
            self.parent_width,
        ) != (0, 256, 256, 512, 512):
            raise ValueError("V0/V1 channel routing geometry drifted")
        if self.model_geometry_authorized is not False:
            raise ValueError("representation routing cannot select model geometry")
        if self.training_authorized is not False:
            raise ValueError("representation routing cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_PRIMARY_REPRESENTATION_ROUTING_AUTHORITY_V1",
                **self.__dict__,
            }
        )

    def bind_streaming_source(self, source_path: Path) -> None:
        """Recompute the exact streaming implementation root from live bytes."""

        self.validate()
        path = Path(source_path)
        if not path.is_file():
            raise ValueError("FULL104 streaming source file is missing")
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if observed != self.full104_streaming_source_sha256:
            raise ValueError("FULL104 streaming implementation source root mismatch")

    def bind_stream(self, stream: Full104ManifestStreamV1) -> None:
        self.validate()
        if not isinstance(stream, Full104ManifestStreamV1):
            raise ValueError("remaining-RNA route requires Full104ManifestStreamV1")
        if stream.expected_manifest_sha256 != self.full104_block_manifest_sha256:
            raise ValueError("remaining-RNA stream binds a different FULL104 manifest")
        stream.validate_layout()

    def bind_global_context_parent_files(
        self,
        *,
        v0_parent_path: Path,
        v1_parent_path: Path,
    ) -> None:
        """Authenticate exact V0/V1 full parent files from live bytes.

        This is a provenance check only. It does not by itself prove that a
        future production model consumes these files; F13 remains open until
        the production consumer is bound to this verifier or an equivalent one.
        """

        self.validate()
        for label, path, expected in (
            ("V0", Path(v0_parent_path), self.v0_full_parent_sha256),
            ("V1", Path(v1_parent_path), self.v1_full_parent_sha256),
        ):
            if not path.is_file():
                raise ValueError(f"{label} full parent file is missing")
            observed = hashlib.sha256(path.read_bytes()).hexdigest()
            if observed != expected:
                raise ValueError(f"{label} full parent file root mismatch")


def validate_value_only_selection_payload(
    authority: PrimaryRepresentationRoutingAuthorityV1,
    selection_payload: Mapping[str, Any],
    parent_payload: Mapping[str, Any],
) -> None:
    """Bind the existing channel-role freeze to its exact current FULL104 scope."""

    authority.validate()
    if selection_payload.get("schema") != "JEPA_V5_PRIMARY_REPRESENTATION_SELECTION_V1":
        raise ValueError("value-only selection schema mismatch")
    if selection_payload.get("feature_parent_manifest_sha256") != authority.feature_parent_manifest_sha256:
        raise ValueError("value-only selection binds a different feature parent")
    if selection_payload.get("primary_molecular_columns") != {
        "start_inclusive": 0,
        "stop_exclusive": 256,
    }:
        raise ValueError("value-only selection must be exactly channels [0:256)")
    if selection_payload.get("excluded_from_primary_molecular_path", {}).get("visibility_columns") != {
        "start_inclusive": 256,
        "stop_exclusive": 512,
    }:
        raise ValueError("visibility channels are not explicitly excluded")
    if selection_payload.get("training_authorized") is not False:
        raise ValueError("value-only selection unexpectedly authorizes training")

    if parent_payload.get("schema") != "JEPA_V5_PRIMARY_REPRESENTATION_FEATURE_PARENTS_V1":
        raise ValueError("feature-parent schema mismatch")
    if parent_payload.get("full104_expression_manifest_sha256") != authority.full104_block_manifest_sha256:
        raise ValueError("feature parents bind a different FULL104 manifest")
    if parent_payload.get("registry_observation_state_binding_sha256") != authority.canonical_registry_sha256:
        raise ValueError("feature parents bind a different registry/observation-state authority")
    if parent_payload.get("column_layout") != {
        "value": {"start_inclusive": 0, "stop_exclusive": 256},
        "visibility": {"start_inclusive": 256, "stop_exclusive": 512},
    }:
        raise ValueError("feature-parent channel layout drifted")
    views = parent_payload.get("views")
    if not isinstance(views, Mapping):
        raise ValueError("feature-parent manifest lacks V0/V1 views")
    for view_id, expected_sha256 in (
        ("V0", authority.v0_full_parent_sha256),
        ("V1", authority.v1_full_parent_sha256),
    ):
        view = views.get(view_id)
        if not isinstance(view, Mapping):
            raise ValueError(f"feature-parent manifest lacks {view_id}")
        if view.get("full_array_sha256") != expected_sha256:
            raise ValueError(f"{view_id} full-parent root mismatch")
        if view.get("shape") != [4_553_407, 512]:
            raise ValueError(f"{view_id} full-parent shape mismatch")
        if view.get("dtype") != "float32":
            raise ValueError(f"{view_id} full-parent dtype mismatch")
    if parent_payload.get("normalization") != "log1p(raw_count * 10000 / full_source_library)__APPLIED_EXACTLY_ONCE":
        raise ValueError("feature-parent normalization semantics drifted")
    if parent_payload.get("training_authorized") is not False:
        raise ValueError("feature parents unexpectedly authorize training")


def value_only_global_context_views(
    authority: PrimaryRepresentationRoutingAuthorityV1,
    *,
    v0_full: np.ndarray,
    v1_full: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Mechanical channel slicer only; not a production provenance boundary.

    The caller must separately bind the physical V0/V1 files before these arrays
    can be treated as current FULL104 inputs. This helper deliberately does not
    claim F13 closure; it only enforces shape, dtype, finiteness, and exclusion
    of the visibility half.
    """

    authority.validate()
    v0 = np.asarray(v0_full)
    v1 = np.asarray(v1_full)
    if v0.ndim != 2 or v1.ndim != 2 or v0.shape[0] != v1.shape[0]:
        raise ValueError("V0/V1 parents must be aligned two-dimensional arrays")
    if v0.shape[1] != PARENT_WIDTH or v1.shape[1] != PARENT_WIDTH:
        raise ValueError("V0/V1 parents must have exactly 512 channels")
    if not np.issubdtype(v0.dtype, np.floating) or not np.issubdtype(v1.dtype, np.floating):
        raise ValueError("V0/V1 parents must be floating-point arrays")
    if not np.all(np.isfinite(v0)) or not np.all(np.isfinite(v1)):
        raise ValueError("V0/V1 parents contain nonfinite values")
    return v0[:, VALUE_START:VALUE_STOP], v1[:, VALUE_START:VALUE_STOP]


def iter_remaining_rna_value_blocks(
    authority: PrimaryRepresentationRoutingAuthorityV1,
    *,
    stream: Full104ManifestStreamV1,
    address_cols: np.ndarray,
) -> Iterator[StreamingBlock]:
    """Yield the exact authenticated FULL104 value route for canonical addresses."""

    authority.bind_stream(stream)
    cols = np.asarray(address_cols)
    if cols.ndim != 1 or not np.issubdtype(cols.dtype, np.integer):
        raise ValueError("address_cols must be a one-dimensional integer array")
    if cols.size < 1 or np.unique(cols).size != cols.size:
        raise ValueError("address_cols must be nonempty and unique")
    yield from stream.iter_blocks(columns=cols.astype(np.int64, copy=False))


def assert_value_block_is_molecular_values_only(block: StreamingBlock) -> None:
    """Mechanical check for normalized value blocks; support/QC is not a channel."""

    if not isinstance(block, StreamingBlock):
        raise ValueError("block must be StreamingBlock")
    if not sp.isspmatrix_csr(block.X):
        raise ValueError("representation value block must be CSR")
    if block.X.data.size and (
        not np.all(np.isfinite(block.X.data)) or np.any(block.X.data < 0)
    ):
        raise ValueError("representation value block contains invalid normalized values")
