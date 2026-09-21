"""Dataset-field role semantics for pathology-blind V5 diagnostics.

These roles describe what a field may be used for in anti-shortcut diagnostics.
They do not authorize model inputs. The key distinction is that a field can look
technical while encoding biological structure; such fields are MIXED_BIO_TECH
and are not legal exact strata for the G4 technical/nuisance decoy.
"""
from __future__ import annotations

from enum import Enum
from typing import Mapping


class DatasetFieldRole(str, Enum):
    DOMAIN_NUISANCE = "DOMAIN_NUISANCE"
    EXOGENOUS_TECHNICAL = "EXOGENOUS_TECHNICAL"
    MIXED_BIO_TECH = "MIXED_BIO_TECH"
    BIOLOGICAL = "BIOLOGICAL"
    GROUPING_ONLY = "GROUPING_ONLY"
    UNKNOWN = "UNKNOWN"


LEGAL_EXACT_DECOY_ROLES = frozenset({
    DatasetFieldRole.DOMAIN_NUISANCE,
    DatasetFieldRole.EXOGENOUS_TECHNICAL,
})


CURRENT_FULL104_FIELD_ROLES: Mapping[str, DatasetFieldRole] = {
    "source": DatasetFieldRole.DOMAIN_NUISANCE,
    "matrix_id": DatasetFieldRole.MIXED_BIO_TECH,
    "operator_index": DatasetFieldRole.MIXED_BIO_TECH,
    "native_class": DatasetFieldRole.BIOLOGICAL,
    "broad_class": DatasetFieldRole.BIOLOGICAL,
    "source_library": DatasetFieldRole.MIXED_BIO_TECH,
    "support_fingerprint": DatasetFieldRole.MIXED_BIO_TECH,
    "donor_id": DatasetFieldRole.GROUPING_ONLY,
    "cell_id": DatasetFieldRole.GROUPING_ONLY,
    "stable_key": DatasetFieldRole.GROUPING_ONLY,
}


def normalize_role(value: object) -> DatasetFieldRole:
    if isinstance(value, DatasetFieldRole):
        return value
    try:
        return DatasetFieldRole(str(value))
    except ValueError as exc:
        raise ValueError(f"unknown dataset field role: {value!r}") from exc


def require_legal_exact_decoy_roles(*roles: object) -> tuple[DatasetFieldRole, ...]:
    if not roles:
        raise ValueError("at least one explicit field role is required")
    normalized = tuple(normalize_role(r) for r in roles)
    bad = tuple(r for r in normalized if r not in LEGAL_EXACT_DECOY_ROLES)
    if bad:
        raise ValueError(
            "exact nuisance-decoy strata reject mixed/biological/grouping/unknown "
            f"roles: {[r.value for r in bad]}"
        )
    return normalized
