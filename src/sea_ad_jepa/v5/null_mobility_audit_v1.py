"""Substrate-independent mobility audit for prospective blocked nulls.

This module does not choose a V3 null or block definition. It validates a
caller-supplied permutation against caller-supplied discrete block labels and
reports whether the proposed null actually moves eligible observations.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Sequence


class NullMobilityStop(RuntimeError):
    pass


def _sha64(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc
    return value.lower()


def _probability(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric in [0,1]")
    out = float(value)
    if not math.isfinite(out) or out < 0.0 or out > 1.0:
        raise ValueError(f"{name} must be finite numeric in [0,1]")
    return out


def audit_blocked_permutation_v1(
    *,
    block_labels: Sequence[object],
    permutation: Sequence[int],
    parent_sha256: str,
    rng_binding_sha256: str,
    min_changed_fraction: float,
    d_shared_outcomes_used: bool = False,
    protected_data_used: bool = False,
    pathology_used: bool = False,
    checkpoint_outcomes_used: bool = False,
    training_authorized: bool = False,
) -> dict[str, object]:
    """Audit a predeclared blocked permutation without choosing its blocks.

    `permutation[i]` is the source row assigned to destination row `i`. The map
    must be a full bijection and must never cross a declared block. Singleton
    blocks remain part of the population and are explicitly noneligible.
    """
    forbidden = {
        "d_shared_outcomes_used": d_shared_outcomes_used,
        "protected_data_used": protected_data_used,
        "pathology_used": pathology_used,
        "checkpoint_outcomes_used": checkpoint_outcomes_used,
        "training_authorized": training_authorized,
    }
    bad = sorted(k for k, v in forbidden.items() if v is not False)
    if bad:
        raise NullMobilityStop(f"STOP_NULL_MOBILITY_FORBIDDEN:{','.join(bad)}")

    parent = _sha64(parent_sha256, "parent_sha256")
    rng = _sha64(rng_binding_sha256, "rng_binding_sha256")
    threshold = _probability(min_changed_fraction, "min_changed_fraction")

    labels = tuple(str(x) for x in block_labels)
    if not labels or any(not x for x in labels):
        raise ValueError("block_labels must be nonempty row-aligned labels")
    n = len(labels)
    raw_perm = tuple(permutation)
    if any(isinstance(x, bool) or not isinstance(x, int) for x in raw_perm):
        raise ValueError("permutation must contain integer indices without coercion")
    perm = raw_perm
    if len(perm) != n or sorted(perm) != list(range(n)):
        raise NullMobilityStop("STOP_NULL_MOBILITY_NOT_BIJECTION")

    cross = [i for i, src in enumerate(perm) if labels[i] != labels[src]]
    if cross:
        raise NullMobilityStop("STOP_NULL_MOBILITY_CROSS_BLOCK")

    sizes = Counter(labels)
    eligible = [sizes[label] >= 2 for label in labels]
    changed = [src != i for i, src in enumerate(perm)]
    eligible_count = sum(eligible)
    changed_count = sum(changed)
    identity_count = n - changed_count
    changed_eligible_count = sum(c and e for c, e in zip(changed, eligible))
    changed_fraction_eligible = (
        changed_eligible_count / eligible_count if eligible_count else 0.0
    )

    block_rows: dict[str, dict[str, object]] = {}
    for label in sorted(sizes):
        idx = [i for i, x in enumerate(labels) if x == label]
        block_changed = sum(changed[i] for i in idx)
        block_rows[label] = {
            "size": len(idx),
            "eligible": len(idx) >= 2,
            "changed_count": block_changed,
            "identity_count": len(idx) - block_changed,
            "changed_fraction": block_changed / len(idx),
        }

    return {
        "schema": "JEPA_V5_NULL_MOBILITY_AUDIT_V1",
        "parent_sha256": parent,
        "rng_binding_sha256": rng,
        "population_count": n,
        "eligible_count": eligible_count,
        "noneligible_count": n - eligible_count,
        "changed_count": changed_count,
        "identity_count": identity_count,
        "changed_eligible_count": changed_eligible_count,
        "population_changed_fraction": changed_count / n,
        "changed_fraction_of_eligible": changed_fraction_eligible,
        "min_changed_fraction": threshold,
        "block_count": len(sizes),
        "blocks": block_rows,
        "marginals_preserved": True,
        "permutation_is_bijection": True,
        "null_mobility_qualifying": bool(
            eligible_count > 0 and changed_fraction_eligible >= threshold
        ),
        "authority_classification": "MECHANICS_ONLY__V3_NULL_NOT_FROZEN",
        "d_shared_real_outcome_access_authorized": False,
        "training_authorized": False,
    }
