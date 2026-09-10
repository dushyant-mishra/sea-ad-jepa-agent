"""Executable proposal-weight invariance gate for V5.

Importance weights are scientific quantities: w_i = p_i / q_i.  Repacking may
change where a presentation is stored or which microbatch carries it, but it
may not change the weight attached to a stable presentation identity.

The gate compares two complete presentations of the same frozen schedule after
canonicalizing by presentation identity. It requires exact identity coverage
and bitwise-equal float64 weights. No training authority is granted here.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Sequence

import numpy as np


def _id(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc
    return value.lower()


def _keys(values: Sequence[object], name: str) -> tuple[str, ...]:
    out = tuple(str(v) for v in values)
    if not out or any(not v for v in out) or len(set(out)) != len(out):
        raise ValueError(f"{name} must contain unique nonempty presentation identities")
    return out


def _weights(values: object, n: int, name: str) -> np.ndarray:
    out = np.asarray(values, dtype=np.float64)
    if out.ndim != 1 or len(out) != n or not np.isfinite(out).all() or bool((out <= 0).any()):
        raise ValueError(f"{name} must be finite positive float64 aligned to identities")
    return out


def _canonical_digest(keys: tuple[str, ...], weights: np.ndarray) -> str:
    h = hashlib.sha256()
    for key, weight in sorted(zip(keys, weights.tolist()), key=lambda x: x[0]):
        raw = key.encode("utf-8")
        h.update(len(raw).to_bytes(8, "little"))
        h.update(raw)
        h.update(np.float64(weight).tobytes())
    return h.hexdigest()


@dataclass(frozen=True)
class ProposalWeightInvarianceAuthorityV1:
    authority_id: str
    proposal_policy_authority_id: str
    schedule_authority_id: str
    full_reader_expression_artifact_sha256: str
    schedule_artifact_sha256: str
    rules_frozen_before_optimizer_start: bool

    def validate(self) -> None:
        _id(self.authority_id, "authority_id")
        _id(self.proposal_policy_authority_id, "proposal_policy_authority_id")
        _id(self.schedule_authority_id, "schedule_authority_id")
        _sha(self.full_reader_expression_artifact_sha256, "full_reader_expression_artifact_sha256")
        _sha(self.schedule_artifact_sha256, "schedule_artifact_sha256")
        if self.rules_frozen_before_optimizer_start is not True:
            raise ValueError("proposal-weight invariance rules must be frozen before optimizer start")


def qualify_proposal_weight_invariance(
    *,
    reference_presentation_ids: Sequence[object],
    reference_weights: object,
    repacked_presentation_ids: Sequence[object],
    repacked_weights: object,
    authority: ProposalWeightInvarianceAuthorityV1,
) -> dict[str, object]:
    authority.validate()
    ref_keys = _keys(reference_presentation_ids, "reference_presentation_ids")
    alt_keys = _keys(repacked_presentation_ids, "repacked_presentation_ids")
    ref_w = _weights(reference_weights, len(ref_keys), "reference_weights")
    alt_w = _weights(repacked_weights, len(alt_keys), "repacked_weights")

    if set(ref_keys) != set(alt_keys):
        raise RuntimeError("STOP_V5_PROPOSAL_WEIGHT_PRESENTATION_SET_MISMATCH")
    ref = {key: ref_w[i] for i, key in enumerate(ref_keys)}
    alt = {key: alt_w[i] for i, key in enumerate(alt_keys)}
    changed = [key for key in sorted(ref) if np.float64(ref[key]).tobytes() != np.float64(alt[key]).tobytes()]
    if changed:
        raise RuntimeError(f"STOP_V5_PROPOSAL_WEIGHT_CHANGED_BY_REPACKING: {changed[:8]}")

    ref_digest = _canonical_digest(ref_keys, ref_w)
    alt_digest = _canonical_digest(alt_keys, alt_w)
    if ref_digest != alt_digest:
        raise RuntimeError("STOP_V5_PROPOSAL_WEIGHT_CANONICAL_DIGEST_MISMATCH")
    return {
        "schema": "JEPA_V5_PROPOSAL_WEIGHT_INVARIANCE_V1",
        "authority_id": authority.authority_id,
        "proposal_policy_authority_id": authority.proposal_policy_authority_id,
        "schedule_authority_id": authority.schedule_authority_id,
        "full_reader_expression_artifact_sha256": authority.full_reader_expression_artifact_sha256,
        "schedule_artifact_sha256": authority.schedule_artifact_sha256,
        "presentations": len(ref_keys),
        "canonical_weight_map_sha256": ref_digest,
        "packing_position_enters_weight": False,
        "microbatch_ordinal_enters_weight": False,
        "device_ordinal_enters_weight": False,
        "passed": True,
        "training_authorized": False,
    }
