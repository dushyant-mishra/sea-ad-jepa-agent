"""Deterministic technical-stratum decoy for prospective G4 falsification.

The decoy preserves the exact multivariate state multiset within each caller-
declared nuisance stratum while breaking row-specific coupling by a fixed-point-
free within-stratum permutation. Every stratum component must carry an explicit
role. DOMAIN_NUISANCE and EXOGENOUS_TECHNICAL components are accepted for exact
stratification; MIXED_BIO_TECH, BIOLOGICAL, and UNKNOWN components fail closed.

This distinction matters in FULL104 because an "operator" may encode biological
structure (for example brain region or cell class) rather than a pure technical
batch. Pathology labels are neither required nor accepted by this primitive.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any

import numpy as np


ALLOWED_EXACT_STRATUM_ROLES = frozenset({
    "DOMAIN_NUISANCE",
    "EXOGENOUS_TECHNICAL",
})
FORBIDDEN_EXACT_STRATUM_ROLES = frozenset({
    "MIXED_BIO_TECH",
    "BIOLOGICAL",
    "UNKNOWN",
})


@dataclass(frozen=True)
class TechnicalDecoyReceiptV1:
    permutation: np.ndarray
    stratum_size_by_row: np.ndarray
    salt: str

    def __post_init__(self) -> None:
        p = np.array(self.permutation, dtype=np.int64, copy=True)
        s = np.array(self.stratum_size_by_row, dtype=np.int64, copy=True)
        if p.ndim != 1 or p.size == 0 or s.shape != p.shape:
            raise ValueError("permutation and stratum sizes must be aligned vectors")
        if sorted(map(int, p)) != list(range(p.size)):
            raise ValueError("permutation must be a bijection over rows")
        if np.any(p == np.arange(p.size)):
            raise ValueError("technical decoy must be fixed-point-free")
        if np.any(s < 2):
            raise ValueError("every technical stratum must have at least two rows")
        if not isinstance(self.salt, str) or not self.salt:
            raise ValueError("salt must be nonempty")
        p.flags.writeable = False
        s.flags.writeable = False
        object.__setattr__(self, "permutation", p)
        object.__setattr__(self, "stratum_size_by_row", s)


def build_technical_stratum_id(
    *components: Any,
    component_roles: tuple[str, ...],
) -> np.ndarray:
    """Combine only prospectively role-qualified nuisance components.

    Exact stratification is intentionally conservative. Mixed biological/
    technical fields must first be decomposed into a defensible nuisance-only
    component or be handled by a separately labelled mixed-nuisance diagnostic.
    """

    if not components:
        raise ValueError("at least one technical/nuisance component is required")
    if not isinstance(component_roles, tuple) or len(component_roles) != len(components):
        raise ValueError("component_roles must explicitly align every stratum component")
    normalized_roles = tuple(str(r) for r in component_roles)
    unknown = [r for r in normalized_roles if r not in ALLOWED_EXACT_STRATUM_ROLES | FORBIDDEN_EXACT_STRATUM_ROLES]
    if unknown:
        raise ValueError(f"unrecognized nuisance component roles: {unknown}")
    forbidden = [r for r in normalized_roles if r not in ALLOWED_EXACT_STRATUM_ROLES]
    if forbidden:
        raise ValueError(
            "exact technical-decoy stratification rejects mixed/biological/unknown "
            f"components: {forbidden}"
        )
    arrays = [np.asarray([str(v) for v in x], dtype=object) for x in components]
    n = arrays[0].size
    if n == 0 or any(a.ndim != 1 or a.size != n for a in arrays):
        raise ValueError("technical components must be aligned nonempty vectors")
    return np.asarray(["\x1f".join(a[i] for a in arrays) for i in range(n)], dtype=object)


def deterministic_stratified_derangement(
    row_key: Any,
    technical_stratum_id: Any,
    *,
    salt: str = "V5_G4_TECHNICAL_ONLY_DECOY_V1",
) -> TechnicalDecoyReceiptV1:
    keys = np.asarray([str(v) for v in row_key], dtype=object)
    strata = np.asarray([str(v) for v in technical_stratum_id], dtype=object)
    if keys.ndim != 1 or keys.size == 0 or strata.shape != keys.shape:
        raise ValueError("row_key and technical_stratum_id must be aligned vectors")
    if len(set(keys.tolist())) != keys.size:
        raise ValueError("row_key must be unique")
    if not isinstance(salt, str) or not salt:
        raise ValueError("salt must be nonempty")

    p = np.empty(keys.size, dtype=np.int64)
    sizes = np.empty(keys.size, dtype=np.int64)
    for stratum in sorted(set(strata.tolist())):
        ix = np.flatnonzero(strata == stratum).tolist()
        if len(ix) < 2:
            raise ValueError(
                f"technical stratum {stratum!r} has <2 rows; cannot break biology while preserving stratum"
            )
        ordered = sorted(
            ix,
            key=lambda i: hashlib.sha256(
                (salt + "|" + stratum + "|" + keys[i]).encode("utf-8")
            ).digest(),
        )
        for j, i in enumerate(ordered):
            p[i] = ordered[(j + 1) % len(ordered)]
            sizes[i] = len(ordered)
    return TechnicalDecoyReceiptV1(permutation=p, stratum_size_by_row=sizes, salt=salt)


def apply_technical_only_decoy(
    state: Any,
    receipt: TechnicalDecoyReceiptV1,
    technical_stratum_id: Any,
) -> np.ndarray:
    """Apply the decoy and verify exact within-stratum row provenance."""

    x = np.asarray(state)
    strata = np.asarray([str(v) for v in technical_stratum_id], dtype=object)
    if x.ndim < 1 or x.shape[0] != receipt.permutation.size or strata.shape != (x.shape[0],):
        raise ValueError("state and technical strata must align receipt rows")
    out = np.array(x[receipt.permutation], copy=True)
    for stratum in sorted(set(strata.tolist())):
        ix = np.flatnonzero(strata == stratum)
        if np.any(strata[receipt.permutation[ix]] != stratum):
            raise AssertionError("decoy crossed technical strata")
        if set(map(int, receipt.permutation[ix])) != set(map(int, ix)):
            raise AssertionError("decoy did not preserve exact within-stratum row multiset")
    return out
