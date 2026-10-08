#!/usr/bin/env python3
"""F1 frozen evidence-mask construction, reproduced exactly from its authority.

Controlling authority:
`outputs/contextual_teacher_target_v1_f1_preflight_20260901/CONTEXTUAL_TARGET_V1_F1_EVIDENCE_MASK_CONTRACT.md`
(`d1eefdab177501a00370d71521ae86932e60540fb9f769dfe2b56c7994ca5c5a`), resolved
by `F1_EVIDENCE_MASK_AUTHORITY.json`
(`b637e2b8c77a499cbb32c48a02f7ef79f259ff972e1ce3b695fec8331288241a`).

## Why this module exists

An independent review asked whether the producer's evidence mask was the frozen
construction. It was not, and the mismatch is confirmed. The previous
implementation took the first measured addresses in index order up to a rounded
percentage:

```python
take = int(round(eligible.size * (level / 100.0)))
mask[eligible[:max(take, 1)]] = True
```

That is wrong in three independent ways against the authority:

1. it did not withhold the query's own scalar, which the authority requires at
   every level and which `construct_query_local_contextual_state` separately
   rejects with "q scalar evidence must be withheld";
2. it ordered candidates by gene address rather than by the seeded digest, so
   the selected set was not the authorised one;
3. it used `round` where the authority specifies `floor(p*|E|/100)`.

Any of the three would have produced a different student evidence set from the
frozen design, and F1's estimand depends on query-local evidence semantics, so
the numbers would have been wrong while every count still reconciled.

## The frozen rule, verbatim in behaviour

For row `r` with scalar-measured query `q`:

- eligible context `E = {j : state[r,j] == MEASURED_SCALAR and j != q}`;
- reject the row/query outright if `q` is not scalar-measured;
- for every `j` in `E` compute
  `SHA256(seed || "|" || canonical-row-locator || "|" || decimal-q || "|" || decimal-j)`
  over UTF-8, with the seed as its lowercase hex string;
- sort by digest bytes, then by integer address;
- level `p` selects the first `floor(p * |E| / 100)` entries of that one ordering.

Because a single ordering is reused, the levels nest:
20 subset 40 subset 60 subset 80 subset 100. At 100% the selection is all of
`E`. The teacher-rich safe target uses all of `E`, which is why the teacher state
is evidence-invariant and there are 43,108 teacher forwards rather than 215,540.

Selection uses no expression value and no model output, so a measured zero has
exactly the same eligibility and hash rank as a nonzero scalar. State 0
(structurally unmeasured), state 2 (collision unresolved) and artificial masking
remain distinct.
"""

from __future__ import annotations

import hashlib
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

EVIDENCE_MASK_CONTRACT_SHA256 = (
    "d1eefdab177501a00370d71521ae86932e60540fb9f769dfe2b56c7994ca5c5a")
EVIDENCE_MASK_AUTHORITY_SHA256 = (
    "b637e2b8c77a499cbb32c48a02f7ef79f259ff972e1ce3b695fec8331288241a")

# Seed authority from the contract. Used as its lowercase hex string in UTF-8.
EVIDENCE_MASK_SEED_SHA256 = (
    "c5c5bc472850f17f0ca6249e3a2765e5924d411ef054691a5e7a5d9d29363a4f")

EVIDENCE_LEVELS: tuple[int, ...] = (20, 40, 60, 80, 100)
PRIMARY_EVIDENCE_LEVEL = 60

# Physical observation-state codes, from the same authority the D1 and F1 lanes
# share: FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz orders the names
# STRUCTURALLY_UNMEASURED, MEASURED_SCALAR, MEASURED_COLLISION_UNRESOLVED.
STRUCTURALLY_UNMEASURED = 0
MEASURED_SCALAR = 1
MEASURED_COLLISION_UNRESOLVED = 2

STOP_QUERY_NOT_MEASURED = "STOP_F1_EVIDENCE_QUERY_NOT_SCALAR_MEASURED"
STOP_EMPTY_ELIGIBLE = "STOP_F1_EVIDENCE_ELIGIBLE_CONTEXT_EMPTY"
STOP_NOT_NESTED = "STOP_F1_EVIDENCE_LEVELS_NOT_NESTED"
STOP_QUERY_VISIBLE = "STOP_F1_EVIDENCE_QUERY_NOT_WITHHELD"
STOP_NOT_SUBSET = "STOP_F1_EVIDENCE_NOT_SUBSET_OF_MEASURED_SCALAR"
STOP_LEVEL = "STOP_F1_EVIDENCE_LEVEL_NOT_AUTHORIZED"
STOP_SEED = "STOP_F1_EVIDENCE_SEED_AUTHORITY"


def eligible_context(physical_state_row: Sequence[int], query_index: int) -> np.ndarray:
    """`E = {j : state[j] == MEASURED_SCALAR and j != q}`, query rejected if unmeasured."""
    state = np.asarray(physical_state_row)
    if state.ndim != 1:
        raise ValueError("physical_state_row must be 1-D")
    q = int(query_index)
    if not 0 <= q < state.size:
        raise ValueError("query_index out of range")
    if int(state[q]) != MEASURED_SCALAR:
        raise ValueError("%s: state[q]=%d" % (STOP_QUERY_NOT_MEASURED, int(state[q])))
    eligible = np.flatnonzero(state == MEASURED_SCALAR)
    eligible = eligible[eligible != q]
    if eligible.size == 0:
        raise ValueError(STOP_EMPTY_ELIGIBLE)
    return eligible.astype(np.int64)


def _rank_digest(row_locator: str, query_address: int, address: int, *,
                 seed: str = EVIDENCE_MASK_SEED_SHA256) -> bytes:
    """`SHA256(seed || "|" || row-locator || "|" || decimal-q || "|" || decimal-j)`."""
    message = "%s|%s|%d|%d" % (str(seed), str(row_locator), int(query_address), int(address))
    return hashlib.sha256(message.encode("utf-8")).digest()


def seeded_ordering(eligible: Iterable[int], *, row_locator: str, query_address: int,
                    seed: str = EVIDENCE_MASK_SEED_SHA256) -> np.ndarray:
    """The single authorised ordering: by digest bytes, then by integer address.

    Reused at every level, which is what makes the levels nested. The ordering
    depends only on the row locator, the query address and the candidate
    address; it never touches an expression value or a model output.
    """
    if len(str(seed)) != 64:
        raise ValueError(STOP_SEED)
    candidates = [int(j) for j in eligible]
    ordered = sorted(candidates, key=lambda j: (_rank_digest(row_locator, query_address, j,
                                                             seed=seed), j))
    return np.asarray(ordered, dtype=np.int64)


def selected_count(level_percent: int, eligible_size: int) -> int:
    """`floor(p * |E| / 100)`. Floor, not round: the authority says floor."""
    if int(level_percent) not in EVIDENCE_LEVELS:
        raise ValueError("%s: %r" % (STOP_LEVEL, level_percent))
    return int((int(level_percent) * int(eligible_size)) // 100)


def evidence_visible_at_level(physical_state_row: Sequence[int], query_index: int, *,
                              level_percent: int, row_locator: str,
                              query_address: int,
                              seed: str = EVIDENCE_MASK_SEED_SHA256) -> np.ndarray:
    """Boolean evidence mask for one row at one authorised level."""
    eligible = eligible_context(physical_state_row, query_index)
    ordering = seeded_ordering(eligible, row_locator=row_locator,
                               query_address=query_address, seed=seed)
    take = selected_count(level_percent, eligible.size)
    mask = np.zeros(np.asarray(physical_state_row).size, dtype=bool)
    if take:
        mask[ordering[:take]] = True
    if bool(mask[int(query_index)]):
        raise AssertionError(STOP_QUERY_VISIBLE)
    return mask


def build_row_evidence_masks(physical_state_row: Sequence[int], query_index: int, *,
                             row_locator: str, query_address: int,
                             seed: str = EVIDENCE_MASK_SEED_SHA256) -> dict[str, Any]:
    """All five authorised levels for one row, plus the teacher-rich target.

    The teacher target uses all of `E`, which is identical to the 100% student
    level; it is returned under its own name so the evidence-invariance of the
    teacher state is explicit rather than implied.
    """
    eligible = eligible_context(physical_state_row, query_index)
    ordering = seeded_ordering(eligible, row_locator=row_locator,
                               query_address=query_address, seed=seed)
    width = np.asarray(physical_state_row).size
    masks: dict[int, np.ndarray] = {}
    counts: dict[int, int] = {}
    for level in EVIDENCE_LEVELS:
        take = selected_count(level, eligible.size)
        mask = np.zeros(width, dtype=bool)
        if take:
            mask[ordering[:take]] = True
        masks[level] = mask
        counts[level] = int(take)

    teacher_mask = np.zeros(width, dtype=bool)
    teacher_mask[eligible] = True

    assert_evidence_masks_lawful(masks, physical_state_row=physical_state_row,
                                 query_index=query_index)
    if not np.array_equal(masks[100], teacher_mask):
        raise AssertionError(
            "STOP_F1_EVIDENCE_HUNDRED_PERCENT_NOT_ALL_ELIGIBLE: the authority states "
            "that at 100% all of E is selected and that the teacher-rich target uses "
            "all of E")
    return {
        "schema": "f1-evidence-mask-v1",
        "eligible_size": int(eligible.size),
        "ordering": ordering,
        "masks": masks,
        "selected_counts": counts,
        "teacher_rich_mask": teacher_mask,
        "primary_level_percent": PRIMARY_EVIDENCE_LEVEL,
        "mask_sha256": {level: hashlib.sha256(
            masks[level].tobytes()).hexdigest() for level in EVIDENCE_LEVELS},
        "contract_sha256": EVIDENCE_MASK_CONTRACT_SHA256,
        "seed_sha256": str(seed),
    }


def assert_evidence_masks_lawful(masks: Mapping[int, np.ndarray], *,
                                 physical_state_row: Sequence[int],
                                 query_index: int) -> dict[str, Any]:
    """Nesting, query withholding and measured-scalar subsetting are all terminal.

    The authority calls any nesting, query-withholding, authority-hash or
    state-semantic failure terminal, so each is checked rather than assumed.
    """
    state = np.asarray(physical_state_row)
    measured = state == MEASURED_SCALAR
    q = int(query_index)
    for level in EVIDENCE_LEVELS:
        mask = np.asarray(masks[level], dtype=bool)
        if bool(mask[q]):
            raise AssertionError("%s: level %d" % (STOP_QUERY_VISIBLE, level))
        if bool(np.any(mask & ~measured)):
            raise AssertionError("%s: level %d selects a non-scalar address"
                                 % (STOP_NOT_SUBSET, level))
    for lower, upper in zip(EVIDENCE_LEVELS, EVIDENCE_LEVELS[1:]):
        low = np.asarray(masks[lower], dtype=bool)
        high = np.asarray(masks[upper], dtype=bool)
        if bool(np.any(low & ~high)):
            raise AssertionError("%s: %d is not a subset of %d"
                                 % (STOP_NOT_NESTED, lower, upper))
    return {"nested": True, "query_withheld": True,
            "subset_of_measured_scalar": True,
            "levels": list(EVIDENCE_LEVELS)}


def verify_contract_authority(contract_text: str, *, contract_sha256: str) -> dict[str, Any]:
    """Bind this implementation to the controlling contract bytes.

    The digest is required, and the contract's own decisive phrases are checked
    so that a same-length replacement cannot pass, and so that this module names
    the sentences it claims to implement.
    """
    if contract_sha256 != EVIDENCE_MASK_CONTRACT_SHA256:
        raise AssertionError(
            "STOP_F1_EVIDENCE_CONTRACT_DIGEST: %s expected %s"
            % (contract_sha256, EVIDENCE_MASK_CONTRACT_SHA256))
    required = (
        "Evidence levels are exactly 20, 40, 60, 80 and 100%",
        "state[r,j]=MEASURED_SCALAR and j!=q",
        EVIDENCE_MASK_SEED_SHA256,
        "sort by digest bytes then integer address",
        "first `floor(p*|E|/100)` entries",
        "The query scalar is withheld at every level.",
        "The teacher-rich safe target uses all of `E`",
    )
    absent = [phrase for phrase in required if phrase not in contract_text]
    if absent:
        raise AssertionError("STOP_F1_EVIDENCE_CONTRACT_TEXT: absent=%r" % absent)
    return {"contract_sha256": contract_sha256,
            "seed_sha256": EVIDENCE_MASK_SEED_SHA256,
            "levels": list(EVIDENCE_LEVELS),
            "primary_level_percent": PRIMARY_EVIDENCE_LEVEL,
            "bound_phrases": len(required)}


__all__ = [name for name in dir() if not name.startswith("_")]
