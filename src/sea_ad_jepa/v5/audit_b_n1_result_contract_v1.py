"""Audit-B N1 result artifact contract V1.

Frozen before N1. The raw N1 artifact stores donor-level normalized burden for
all 256 targets x 3 nonuniform policies x 6 burden rungs x 104 donors.

This deliberately preserves enough information to independently recompute:
- source-balanced primary Audit-B target values;
- donor-uniform robustness target values;
- per-source target values;
- the one decision-driving RIDGE8_CONDITIONAL @ 5% precision vector.

The result contract never consumes terminal masking outcomes.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
from typing import Any, Mapping, Sequence

import numpy as np

from .audit_b_n1_execution_authority_v1 import (
    B4_CONTRACT_SHA256,
    N1_TARGET_COUNT,
)
from .audit_b_precision_rule_v2 import (
    PRIMARY_POLICY_ID,
    PRIMARY_RUNG,
)
from .audit_b_production_burden_v1 import (
    BURDEN_RUNGS,
    NONUNIFORM_POLICIES,
)

N1_EXECUTION_AUTHORITY_SHA256 = (
    "2917a84b5796b0c6dfe8a962d67dbf69b2932dafa1894f56922c2e9257c59bb2"
)
N_DONORS = 104
N_SOURCES = 3
N_POLICIES = 3
N_RUNGS = 6
EXPECTED_TENSOR_SHAPE = (N1_TARGET_COUNT, N_POLICIES, N_RUNGS, N_DONORS)
POLICY_ORDER = tuple(NONUNIFORM_POLICIES)
RUNG_ORDER = tuple((r.numerator, r.denominator) for r in BURDEN_RUNGS)

RESULT_ARRAY_SCHEMA_ID = "V5_AUDIT_B_N1_DONOR_BURDEN_ARRAYS_V1"
RESULT_RECEIPT_SCHEMA_ID = "V5_AUDIT_B_N1_RESULT_RECEIPT_V1"


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _as_targets(value: Any) -> np.ndarray:
    x = np.asarray(value)
    if (
        x.ndim != 1
        or x.size != N1_TARGET_COUNT
        or not np.issubdtype(x.dtype, np.integer)
        or np.unique(x).size != x.size
        or np.any(x < 0)
    ):
        raise ValueError("target_cols must be exactly 256 unique nonnegative integers")
    return x.astype(np.int64, copy=False)


def _as_burden(value: Any, name: str) -> np.ndarray:
    x = np.asarray(value, dtype=np.float64)
    if x.shape != EXPECTED_TENSOR_SHAPE:
        raise ValueError(f"{name} must have shape {EXPECTED_TENSOR_SHAPE}")
    if not np.all(np.isfinite(x)):
        raise ValueError(f"{name} must be finite for all N1 donor observations")
    return x


def validate_n1_arrays(
    *,
    target_cols: Any,
    donor_normalized_delta_detected: Any,
    donor_normalized_delta_umi: Any,
    expected_target_cols: Sequence[int],
    donor_source_code: Sequence[int],
) -> dict[str, np.ndarray]:
    target = _as_targets(target_cols)
    expected = _as_targets(expected_target_cols)
    if not np.array_equal(target, expected):
        raise ValueError("N1 target_cols differ from the frozen N1 prefix order")

    detected = _as_burden(
        donor_normalized_delta_detected,
        "donor_normalized_delta_detected",
    )
    umi = _as_burden(
        donor_normalized_delta_umi,
        "donor_normalized_delta_umi",
    )

    source = np.asarray(donor_source_code)
    if (
        source.ndim != 1
        or source.size != N_DONORS
        or not np.issubdtype(source.dtype, np.integer)
        or set(map(int, np.unique(source))) != {0, 1, 2}
    ):
        raise ValueError("donor_source_code must align 104 donors across source codes 0,1,2")
    source = source.astype(np.int64, copy=False)

    return {
        "target_cols": target,
        "donor_normalized_delta_detected": detected,
        "donor_normalized_delta_umi": umi,
        "donor_source_code": source,
    }


def aggregate_target_values(
    donor_values: np.ndarray,
    donor_source_code: Sequence[int],
) -> dict[str, np.ndarray]:
    x = _as_burden(donor_values, "donor_values")
    source = np.asarray(donor_source_code, dtype=np.int64)
    if source.shape != (N_DONORS,) or set(np.unique(source).tolist()) != {0, 1, 2}:
        raise ValueError("donor_source_code geometry mismatch")

    source_means = np.empty(
        (N1_TARGET_COUNT, N_POLICIES, N_RUNGS, N_SOURCES),
        dtype=np.float64,
    )
    for s in range(N_SOURCES):
        ix = source == s
        if not np.any(ix):
            raise ValueError(f"source {s} has no donors")
        source_means[..., s] = np.mean(x[..., ix], axis=-1)
    source_balanced = np.mean(source_means, axis=-1)
    donor_uniform = np.mean(x, axis=-1)
    return {
        "source_means": source_means,
        "source_balanced": source_balanced,
        "donor_uniform": donor_uniform,
    }


def primary_target_values(
    donor_normalized_delta_detected: np.ndarray,
    donor_source_code: Sequence[int],
) -> np.ndarray:
    agg = aggregate_target_values(
        donor_normalized_delta_detected,
        donor_source_code,
    )
    policy_index = POLICY_ORDER.index(PRIMARY_POLICY_ID)
    rung_index = RUNG_ORDER.index((PRIMARY_RUNG.numerator, PRIMARY_RUNG.denominator))
    out = agg["source_balanced"][:, policy_index, rung_index]
    if out.shape != (N1_TARGET_COUNT,) or not np.all(np.isfinite(out)):
        raise ValueError("primary target values are incomplete")
    return out


@dataclass(frozen=True)
class AuditBN1ResultReceiptV1:
    result_artifact_sha256: str
    target_cols_sha256: str
    donor_normalized_delta_detected_sha256: str
    donor_normalized_delta_umi_sha256: str
    donor_source_code_sha256: str

    target_count: int = N1_TARGET_COUNT
    donor_count: int = N_DONORS
    policy_order: tuple[str, ...] = POLICY_ORDER
    rung_order: tuple[tuple[int, int], ...] = RUNG_ORDER
    tensor_shape: tuple[int, int, int, int] = EXPECTED_TENSOR_SHAPE

    b4_contract_sha256: str = B4_CONTRACT_SHA256
    n1_execution_authority_sha256: str = N1_EXECUTION_AUTHORITY_SHA256

    terminal_masking_outcomes_inspected: bool = False
    terminal_masking_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        for name in (
            "result_artifact_sha256",
            "target_cols_sha256",
            "donor_normalized_delta_detected_sha256",
            "donor_normalized_delta_umi_sha256",
            "donor_source_code_sha256",
            "b4_contract_sha256",
            "n1_execution_authority_sha256",
        ):
            _sha(getattr(self, name), name)
        if self.b4_contract_sha256 != B4_CONTRACT_SHA256:
            raise ValueError("N1 result receipt binds a different B4 contract")
        if self.n1_execution_authority_sha256 != N1_EXECUTION_AUTHORITY_SHA256:
            raise ValueError("N1 result receipt binds a different N1 execution authority")
        if self.target_count != N1_TARGET_COUNT or self.donor_count != N_DONORS:
            raise ValueError("N1 result geometry drifted")
        if tuple(self.policy_order) != POLICY_ORDER:
            raise ValueError("policy_order drifted")
        if tuple(tuple(x) for x in self.rung_order) != RUNG_ORDER:
            raise ValueError("rung_order drifted")
        if tuple(self.tensor_shape) != EXPECTED_TENSOR_SHAPE:
            raise ValueError("tensor_shape drifted")
        for name in (
            "terminal_masking_outcomes_inspected",
            "terminal_masking_authorized",
            "training_authorized",
        ):
            if getattr(self, name) is not False:
                raise ValueError(f"{name} must remain false")

    def canonical_digest(self) -> str:
        self.validate()
        payload = asdict(self)
        payload["policy_order"] = list(self.policy_order)
        payload["rung_order"] = [list(x) for x in self.rung_order]
        payload["tensor_shape"] = list(self.tensor_shape)
        return hashlib.sha256(
            _canonical({"schema": RESULT_RECEIPT_SCHEMA_ID, **payload})
        ).hexdigest()


def array_sha256(array: Any, *, dtype: str) -> str:
    x = np.asarray(array).astype(dtype, copy=False)
    return hashlib.sha256(x.tobytes(order="C")).hexdigest()
