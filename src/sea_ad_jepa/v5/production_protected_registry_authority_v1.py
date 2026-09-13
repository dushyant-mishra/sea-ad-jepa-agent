"""Production protected-tensor registry authority for dataset-first V5.

Historical C2/V4 mechanics used a six-block model, so the protected attention
cross-product happened to contain exactly 48 tensors (6 blocks x 4 roles x 2
parameter kinds).  Current V5 production geometry is data-derived and may select
a different model depth.  Therefore 48 is not itself production authority.

This module freezes the exact protected tensor identities for the prospectively
selected production model depth.  Every block must expose the same protected
attention roles and weight/bias parameters.  The canonical registry digest is
then shared by GPU qualification, preexecution authority and checkpoint
telemetry.  Nothing here authorizes training.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

PROTECTED_ROLES = (
    "attention_norm",
    "attention.query",
    "attention.key",
    "attention.value",
)
PROTECTED_PARAMETERS = ("weight", "bias")

PRODUCTION_MECHANICS_CHAIN_V1 = (
    "FP16_FORWARD",
    "BACKWARD_AUTOCAST_DISABLED",
    "UNSCALE",
    "PROTECTED_REGISTRY_GRADIENT_GATE",
    "OPTIMIZER_STEP_PROVED_BEYOND_DECAY",
    "ADAM_EXP_AVG_PROVED",
    "ADAM_EXP_AVG_SQ_PROVED",
    "EMA_UPDATE",
    "SUCCESSFUL_PRESENTATION_CURSOR_ADVANCE",
    "ATOMIC_CHECKPOINT_TELEMETRY_COMMIT",
)


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _id(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value.strip()


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class ProductionProtectedRegistryAuthorityV1:
    authority_id: str
    model_depth: int
    records: Sequence[Mapping[str, Any]]
    training_authorized: bool = False

    @property
    def expected_tensors(self) -> int:
        return _positive_int(self.model_depth, "model_depth") * len(PROTECTED_ROLES) * len(PROTECTED_PARAMETERS)

    def normalized_records(self) -> list[dict[str, Any]]:
        depth = _positive_int(self.model_depth, "model_depth")
        _id(self.authority_id, "authority_id")
        if self.training_authorized is not False:
            raise ValueError("protected-registry authority cannot authorize training")
        if not isinstance(self.records, Sequence) or isinstance(self.records, (str, bytes)):
            raise ValueError("records must be a sequence")
        if len(self.records) != self.expected_tensors:
            raise ValueError(
                f"protected registry must contain exactly {self.expected_tensors} tensors for model_depth={depth}, got {len(self.records)}"
            )

        expected = {
            (block, role, parameter)
            for block in range(depth)
            for role in PROTECTED_ROLES
            for parameter in PROTECTED_PARAMETERS
        }
        seen: set[tuple[int, str, str]] = set()
        names: set[str] = set()
        normalized: list[dict[str, Any]] = []
        for row in self.records:
            if not isinstance(row, Mapping):
                raise ValueError("protected registry rows must be mappings")
            block = row.get("block_index")
            role = row.get("role")
            parameter = row.get("parameter")
            name = row.get("tensor_name")
            if isinstance(block, bool) or not isinstance(block, int) or block not in range(depth):
                raise ValueError(f"protected block_index must lie in [0,{depth - 1}]")
            if role not in PROTECTED_ROLES or parameter not in PROTECTED_PARAMETERS:
                raise ValueError("protected role/parameter outside production cross-product")
            tensor_name = _id(name, "tensor_name")
            key = (block, str(role), str(parameter))
            if key in seen or tensor_name in names:
                raise ValueError("protected registry contains duplicate identity or tensor_name")
            seen.add(key)
            names.add(tensor_name)
            normalized.append(
                {
                    "block_index": block,
                    "role": str(role),
                    "parameter": str(parameter),
                    "tensor_name": tensor_name,
                }
            )
        if seen != expected:
            raise ValueError("protected registry is not the exact production depth x role x parameter cross-product")
        normalized.sort(
            key=lambda row: (
                row["block_index"],
                row["role"],
                row["parameter"],
                row["tensor_name"],
            )
        )
        return normalized

    def registry_sha256(self) -> str:
        return _canonical_sha(
            {
                "schema": "V5_PRODUCTION_PROTECTED_REGISTRY_V1",
                "model_depth": _positive_int(self.model_depth, "model_depth"),
                "protected_roles": list(PROTECTED_ROLES),
                "protected_parameters": list(PROTECTED_PARAMETERS),
                "records": self.normalized_records(),
            }
        )

    def canonical_digest(self) -> str:
        return _canonical_sha(
            {
                "schema": "V5_PRODUCTION_PROTECTED_REGISTRY_AUTHORITY_V1",
                "authority_id": _id(self.authority_id, "authority_id"),
                "model_depth": _positive_int(self.model_depth, "model_depth"),
                "expected_tensors": self.expected_tensors,
                "registry_sha256": self.registry_sha256(),
                "training_authorized": False,
            }
        )

    def validate(self) -> None:
        self.normalized_records()
        self.registry_sha256()
        self.canonical_digest()
