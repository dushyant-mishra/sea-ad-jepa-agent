"""Strict FULL104 support selection and per-cell address classification.

The operator x address observation state is ternary, not binary:

    0  STRUCTURALLY_UNMEASURED
    1  MEASURED_SCALAR
    2  MEASURED_COLLISION_UNRESOLVED

Two readings of "measured in every operator" are therefore possible. The strict
reading (state == 1 everywhere) yields the terminal common core of 17,186
addresses. The loose reading (state in {1, 2} everywhere) yields 17,405 and
admits 219 further addresses.

The FULL104 read-only census settled which is correct. Across all 23.7 billion
stored nonzeros, ``nnz_outside_declared_panel == 0`` and
``nnz_in_collision_unresolved == 0``: no value is ever stored at an address an
operator declares structurally unmeasured or collision-unresolved. The 219
loose-only addresses therefore carry no expression data at all in the operators
where they are collision-unresolved. Admitting them would enter structural
absence into the universe as a solid block of zeros that would be indistinguishable
from measured zero -- the precise confusion the masking design must prevent.

Hence the terminal universe is strict, and this module refuses the loose reading.
"""
from __future__ import annotations

from typing import Mapping, Tuple

import numpy as np

STRUCTURALLY_UNMEASURED = 0
MEASURED_SCALAR = 1
MEASURED_COLLISION_UNRESOLVED = 2

STATE_NAMES: Tuple[str, ...] = (
    "STRUCTURALLY_UNMEASURED",
    "MEASURED_SCALAR",
    "MEASURED_COLLISION_UNRESOLVED",
)

SUPPORT_SEMANTICS_ID = "STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1"
TERMINAL_UNIVERSE_ID = "FULL_COMMON_CORE_17186_V1"
TERMINAL_UNIVERSE_SIZE = 17186


def _validate_states(states: np.ndarray) -> np.ndarray:
    arr = np.asarray(states)
    if arr.ndim != 2:
        raise ValueError("observation state must be a 2-D operator x address array")
    allowed = {STRUCTURALLY_UNMEASURED, MEASURED_SCALAR, MEASURED_COLLISION_UNRESOLVED}
    present = set(int(v) for v in np.unique(arr))
    if not present <= allowed:
        raise ValueError(
            f"observation state contains unknown codes {sorted(present - allowed)!r}; "
            f"allowed codes are {sorted(allowed)!r}"
        )
    return arr


def select_strict_common_core(states: np.ndarray) -> np.ndarray:
    """Addresses that are MEASURED_SCALAR in **every** operator.

    This is the only admissible terminal universe.
    """
    arr = _validate_states(states)
    return np.flatnonzero((arr == MEASURED_SCALAR).all(axis=0))


def select_loose_common_core(states: np.ndarray) -> np.ndarray:
    """Addresses measured (scalar OR collision-unresolved) in every operator.

    Provided only so the strict/loose difference can be measured and regressed
    against. It must never be used to build a terminal universe.
    """
    arr = _validate_states(states)
    measured = (arr == MEASURED_SCALAR) | (arr == MEASURED_COLLISION_UNRESOLVED)
    return np.flatnonzero(measured.all(axis=0))


def loose_only_addresses(states: np.ndarray) -> np.ndarray:
    """Addresses admitted by the loose reading but excluded by the strict one."""
    return np.setdiff1d(
        select_loose_common_core(states), select_strict_common_core(states)
    )


def assert_terminal_universe_is_strict(states: np.ndarray, universe: np.ndarray) -> None:
    """Fail if a proposed terminal universe contains any loose-only address."""
    arr = _validate_states(states)
    proposed = np.asarray(universe, dtype=np.int64)
    strict = select_strict_common_core(arr)
    intruders = np.intersect1d(proposed, loose_only_addresses(arr))
    if intruders.size:
        raise ValueError(
            f"{intruders.size} loose-only address(es) would enter the terminal "
            f"universe, first few {intruders[:5].tolist()!r}. These are "
            "collision-unresolved in at least one operator and carry no expression "
            "data there; admitting them enters structural absence as zero-filled "
            "pseudo-measurement."
        )
    extra = np.setdiff1d(proposed, strict)
    if extra.size:
        raise ValueError(
            f"{extra.size} address(es) in the proposed universe are not in the strict "
            "common core"
        )


def classify_cell_addresses(
    states: np.ndarray, operator_index: int, nonzero_addresses: np.ndarray
) -> Mapping[str, int]:
    """Classify every address for one cell, keeping measured zero distinct.

    Returns counts for four mutually exclusive, exhaustive classes:

    ``measured_nonzero``
        strictly supported, a value is stored
    ``measured_zero``
        strictly supported, no value stored -- this IS an observation, namely
        that the transcript was not detected, and it is legitimate evidence
    ``structurally_unmeasured``
        never observed by this operator
    ``collision_unresolved``
        observed but not resolvable to this address

    ``measured_zero`` must never be folded into ``structurally_unmeasured``: the
    first is data and the second is absence.
    """
    arr = _validate_states(states)
    op = int(operator_index)
    if op < 0 or op >= arr.shape[0]:
        raise ValueError(f"operator_index {op} out of range for {arr.shape[0]} operators")
    row = arr[op]
    nz = np.asarray(nonzero_addresses, dtype=np.int64)
    if nz.size and (nz.min() < 0 or nz.max() >= row.size):
        raise ValueError("nonzero address index out of range")
    if np.unique(nz).size != nz.size:
        raise ValueError("nonzero addresses must be distinct")

    offending = nz[row[nz] != MEASURED_SCALAR]
    if offending.size:
        raise ValueError(
            f"{offending.size} stored nonzero value(s) fall outside the operator's "
            f"MEASURED_SCALAR panel, first few {offending[:5].tolist()!r}. The FULL104 "
            "census established this count is 0; a nonzero here means the support "
            "declaration and the data disagree."
        )

    supported = int((row == MEASURED_SCALAR).sum())
    counts = {
        "measured_nonzero": int(nz.size),
        "measured_zero": supported - int(nz.size),
        "structurally_unmeasured": int((row == STRUCTURALLY_UNMEASURED).sum()),
        "collision_unresolved": int((row == MEASURED_COLLISION_UNRESOLVED).sum()),
    }
    if sum(counts.values()) != int(row.size):
        raise ValueError("address classification is not exhaustive")
    if counts["measured_zero"] < 0:
        raise ValueError("more stored nonzeros than supported addresses")
    return counts


def eligible_masking_addresses(
    states: np.ndarray, universe: np.ndarray, target_address: int
) -> np.ndarray:
    """Eligible masking units: strict non-target addresses of the universe.

    Eligibility depends only on the support declaration and the target identity.
    It does not consult any expression value, so it is identical for every cell.
    A value-dependent eligibility rule would leak the hidden realization.
    """
    arr = _validate_states(states)
    proposed = np.asarray(universe, dtype=np.int64)
    assert_terminal_universe_is_strict(arr, proposed)
    target = int(target_address)
    if target not in set(proposed.tolist()):
        raise ValueError("target address must belong to the terminal universe")
    return np.sort(proposed[proposed != target])
