"""Finite non-enumerative relational sampling primitives for prospective V5.

These helpers sample exact anchored triplet identities from a frozen set of
canonical cell keys without enumerating O(n^3) relations.  The numerical triplet
budget has no default and remains separate authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from numbers import Integral
from typing import Sequence

_DOMAIN = b"SEA_AD_JEPA_V5_FINITE_ANCHORED_TRIPLETS_V1\0"


def _exact_nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an exact integer")
    out = int(value)
    if out < 0:
        raise ValueError(f"{name} must be nonnegative")
    return out


def anchored_triplet_capacity(group_size: int) -> int:
    n = _exact_nonnegative_int(group_size, "group_size")
    if n < 3:
        return 0
    return n * ((n - 1) * (n - 2) // 2)


def _pair_prefix(a: int, m: int) -> int:
    return a * (2 * m - a - 1) // 2


def _unrank_pair(rank: int, m: int) -> tuple[int, int]:
    """Lexicographically unrank one unordered pair among m positions."""
    total = m * (m - 1) // 2
    if rank < 0 or rank >= total:
        raise ValueError("pair rank out of range")
    lo, hi = 0, m - 1
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if _pair_prefix(mid, m) <= rank:
            lo = mid
        else:
            hi = mid
    a = lo
    while a + 1 < m and _pair_prefix(a + 1, m) <= rank:
        a += 1
    offset = rank - _pair_prefix(a, m)
    b = a + 1 + offset
    if not (0 <= a < b < m):
        raise RuntimeError("pair unranking failed")
    return a, b


def unrank_anchored_triplet(rank: int, group_size: int) -> tuple[int, int, int]:
    """Map a canonical rank to (anchor,j,k), j<k, without enumeration."""
    n = _exact_nonnegative_int(group_size, "group_size")
    cap = anchored_triplet_capacity(n)
    r = _exact_nonnegative_int(rank, "rank")
    if cap == 0 or r >= cap:
        raise ValueError("triplet rank out of range")
    pairs_per_anchor = (n - 1) * (n - 2) // 2
    anchor = r // pairs_per_anchor
    pair_rank = r % pairs_per_anchor
    a, b = _unrank_pair(pair_rank, n - 1)
    j = a if a < anchor else a + 1
    k = b if b < anchor else b + 1
    if j > k:
        j, k = k, j
    if anchor in (j, k) or j == k:
        raise RuntimeError("triplet unranking emitted duplicate cells")
    return anchor, j, k


class _Sha256CounterRandom:
    def __init__(self, seed_material: bytes) -> None:
        self.seed = hashlib.sha256(_DOMAIN + seed_material).digest()
        self.counter = 0

    def _word256(self) -> int:
        raw = hashlib.sha256(self.seed + self.counter.to_bytes(16, "little")).digest()
        self.counter += 1
        return int.from_bytes(raw, "little")

    def randbelow(self, upper: int) -> int:
        if upper <= 0:
            raise ValueError("upper must be positive")
        modulus = 1 << 256
        limit = modulus - (modulus % upper)
        while True:
            x = self._word256()
            if x < limit:
                return x % upper


@dataclass(frozen=True)
class FiniteTripletKeySample:
    triplet_cell_keys: tuple[tuple[int, int, int], ...]
    sampled_ranks: tuple[int, ...]
    capacity: int
    requested_budget: int
    realized_count: int


def sample_finite_anchored_triplet_keys(
    cell_keys: Sequence[int],
    *,
    triplet_budget: int,
    authority_seed: int,
    update_index: int,
    group_key: str,
) -> FiniteTripletKeySample:
    """Uniformly sample unique anchored relations without full enumeration.

    Cell identities are sorted before ranking, so triplet identity is invariant
    to incoming batch order.  Floyd's algorithm samples unique integer ranks in
    O(budget) memory/time.  The budget is explicit and has no default.
    """
    budget = _exact_nonnegative_int(triplet_budget, "triplet_budget")
    seed = _exact_nonnegative_int(authority_seed, "authority_seed")
    update = _exact_nonnegative_int(update_index, "update_index")
    if not isinstance(group_key, str) or not group_key:
        raise ValueError("group_key must be a nonempty canonical string")
    canonical = []
    for raw in cell_keys:
        value = _exact_nonnegative_int(raw, "cell_key")
        canonical.append(value)
    if len(canonical) < 3:
        return FiniteTripletKeySample((), (), 0, budget, 0)
    if len(set(canonical)) != len(canonical):
        raise ValueError("cell_keys must be unique")
    canonical.sort()
    capacity = anchored_triplet_capacity(len(canonical))
    count = min(budget, capacity)
    if count == 0:
        return FiniteTripletKeySample((), (), capacity, budget, 0)
    material = bytearray()
    material.extend(seed.to_bytes(16, "little", signed=False))
    material.extend(update.to_bytes(16, "little", signed=False))
    encoded_group = group_key.encode("utf-8")
    material.extend(len(encoded_group).to_bytes(4, "little"))
    material.extend(encoded_group)
    material.extend(len(canonical).to_bytes(8, "little"))
    for key in canonical:
        material.extend(key.to_bytes(8, "little", signed=False))
    rng = _Sha256CounterRandom(bytes(material))
    selected: set[int] = set()
    for j in range(capacity - count, capacity):
        t = rng.randbelow(j + 1)
        selected.add(j if t in selected else t)
    ranks = tuple(sorted(selected))
    if len(ranks) != count:
        raise RuntimeError("finite triplet sampler failed uniqueness")
    triplets = []
    for rank in ranks:
        i, j, k = unrank_anchored_triplet(rank, len(canonical))
        a, b, c = canonical[i], canonical[j], canonical[k]
        if b > c:
            b, c = c, b
        triplets.append((a, b, c))
    return FiniteTripletKeySample(tuple(triplets), ranks, capacity, budget, count)


def map_triplet_keys_to_rows(
    triplet_cell_keys: Sequence[tuple[int, int, int]],
    batch_cell_keys: Sequence[int],
) -> tuple[tuple[int, int, int], ...]:
    """Map frozen canonical triplet identities to local row indices for V4 loss."""
    row_by_key: dict[int, int] = {}
    for row, raw in enumerate(batch_cell_keys):
        key = _exact_nonnegative_int(raw, "batch_cell_key")
        if key in row_by_key:
            raise ValueError("batch_cell_keys must be unique")
        row_by_key[key] = row
    out = []
    seen: set[tuple[int, int, int]] = set()
    for raw in triplet_cell_keys:
        if len(raw) != 3:
            raise ValueError("triplet key must have three cells")
        try:
            i, j, k = (row_by_key[int(raw[0])], row_by_key[int(raw[1])], row_by_key[int(raw[2])])
        except KeyError as exc:
            raise ValueError("frozen triplet cell missing from local relational batch") from exc
        if len({i, j, k}) != 3:
            raise ValueError("triplet cells must be distinct")
        if j > k:
            j, k = k, j
        canonical = (i, j, k)
        duplicate_key = (i, min(j, k), max(j, k))
        if duplicate_key in seen:
            raise ValueError("duplicate frozen anchored relation")
        seen.add(duplicate_key)
        out.append(canonical)
    return tuple(out)
