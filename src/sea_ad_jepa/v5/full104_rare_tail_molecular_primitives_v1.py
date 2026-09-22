"""Pure, outcome-agnostic mechanics for FULL104 rare-tail molecular gate V1.

These functions are frozen before expression outcomes are opened. They contain
no pass/fail observations and no biological labels.
"""
from __future__ import annotations

import hashlib
import math
from typing import Iterable, Sequence

import numpy as np

from .full104_rare_biology_preservation_authority_v1 import (
    select_q95_isolation_tail_v1,
)
from .full104_rare_tail_molecular_authority_v1 import (
    LOCALITY_DENOMINATOR,
    MIN_INFORMATIVE_PAIR_COORDINATES,
    PAIR_COUNT_PER_VIEW,
    PANEL_GENE_SHA256,
    PANEL_PAIR_ADDRESS_SHA256,
    PANEL_VIEW_RANK_SLICES,
    TRIPLETS_PER_STRATUM_CAP,
)


def digest(text: str) -> bytes:
    return hashlib.sha256(text.encode("utf-8")).digest()


def u64(text: str) -> int:
    return int.from_bytes(digest(text)[:8], "big", signed=False)


def ranked_common(common_addresses: Sequence[int]) -> np.ndarray:
    common = np.asarray(common_addresses, dtype=np.int64)
    if common.ndim != 1 or common.size < 9216:
        raise ValueError("common_addresses must contain at least 9,216 addresses")
    if np.unique(common).size != common.size or np.any(common < 0):
        raise ValueError("common_addresses must be unique nonnegative integers")
    return np.asarray(
        sorted(
            (int(x) for x in common),
            key=lambda g: digest(f"TD56S|gene|{g}"),
        ),
        dtype=np.int64,
    )


def select_gene_views(common_addresses: Sequence[int], panel: int) -> dict[str, np.ndarray]:
    if panel not in PANEL_VIEW_RANK_SLICES:
        raise ValueError("panel must be 0 or 1")
    ranked = ranked_common(common_addresses)
    views = {
        label: ranked[start:end].copy()
        for label, (start, end) in PANEL_VIEW_RANK_SLICES[panel].items()
    }
    for label, genes in views.items():
        if genes.size != 512:
            raise ValueError(f"{label} view must contain exactly 512 addresses")
        observed = hashlib.sha256(genes.astype("<i4").tobytes()).hexdigest()
        expected = PANEL_GENE_SHA256[panel][label]
        if observed != expected:
            raise ValueError(
                f"TD59 gene-view hash mismatch for panel={panel} view={label}: "
                f"{observed} != {expected}"
            )
    labels = tuple(views)
    for i, a in enumerate(labels):
        for b in labels[i + 1:]:
            if set(views[a].tolist()) & set(views[b].tolist()):
                raise ValueError("TD59 Z/X/Y gene views must remain disjoint")
    return views


def select_pairs(
    genes: Sequence[int],
    *,
    panel: int,
    view: str,
) -> tuple[np.ndarray, np.ndarray]:
    gene = np.asarray(genes, dtype=np.int64)
    if gene.ndim != 1 or gene.size != 512 or np.unique(gene).size != gene.size:
        raise ValueError("genes must be 512 unique addresses")
    if panel not in (0, 1) or view not in ("Z", "X", "Y"):
        raise ValueError("invalid panel/view")
    candidates: list[tuple[bytes, int, int, int, int]] = []
    for a in range(511):
        ga = int(gene[a])
        for b in range(a + 1, 512):
            gb = int(gene[b])
            g0, g1 = sorted((ga, gb))
            preimage = f"TD59|panel|{panel}|view|{view}|g0|{g0}|g1|{g1}"
            candidates.append((digest(preimage), a, b, g0, g1))
    candidates.sort(key=lambda x: x[0])
    kept = candidates[:PAIR_COUNT_PER_VIEW]
    positions = np.asarray([[x[1], x[2]] for x in kept], dtype=np.int32)
    addresses = np.asarray([[x[3], x[4]] for x in kept], dtype=np.int32)
    return positions, addresses


def verify_pair_address_hash(addresses: np.ndarray, *, panel: int, view: str) -> str:
    arr = np.asarray(addresses)
    if arr.shape != (PAIR_COUNT_PER_VIEW, 2):
        raise ValueError("pair-address array has unexpected geometry")
    digest_value = hashlib.sha256(arr.astype("<i4").tobytes()).hexdigest()
    expected = PANEL_PAIR_ADDRESS_SHA256[panel][view]
    if digest_value != expected:
        raise ValueError(
            f"TD59 pair-address hash mismatch for panel={panel} view={view}: "
            f"{digest_value} != {expected}"
        )
    return digest_value


def pair_signs(expression: np.ndarray, pair_positions: np.ndarray) -> np.ndarray:
    x = np.asarray(expression, dtype=np.float64)
    pairs = np.asarray(pair_positions, dtype=np.int64)
    if x.ndim != 2 or x.shape[1] != 512:
        raise ValueError("expression must be cells x 512 genes")
    if pairs.shape != (PAIR_COUNT_PER_VIEW, 2):
        raise ValueError("pair_positions must be 2048 x 2")
    if np.any(pairs < 0) or np.any(pairs >= 512):
        raise ValueError("pair positions out of range")
    if not np.all(np.isfinite(x)):
        raise ValueError("expression must be finite")
    return np.sign(x[:, pairs[:, 0]] - x[:, pairs[:, 1]]).astype(np.int8)


def distance_matrix(signs: np.ndarray) -> np.ndarray:
    s = np.asarray(signs, dtype=np.int8)
    if s.ndim != 2 or s.shape[1] != PAIR_COUNT_PER_VIEW:
        raise ValueError("signs must be cells x 2048")
    if np.any(~np.isin(s, (-1, 0, 1))):
        raise ValueError("signs must be in {-1,0,+1}")
    p = s.shape[1]
    pos = (s == 1).astype(np.float32)
    neg = (s == -1).astype(np.float32)
    zero = (s == 0).astype(np.float32)
    nonzero = (s != 0).sum(axis=1).astype(np.int32)
    same = np.rint(pos @ pos.T + neg @ neg.T).astype(np.int32)
    both_zero = np.rint(zero @ zero.T).astype(np.int32)
    l1 = nonzero[:, None] + nonzero[None, :] - 2 * same
    informative = p - both_zero
    out = np.full((len(s), len(s)), np.nan, dtype=np.float64)
    good = informative >= MIN_INFORMATIVE_PAIR_COORDINATES
    out[good] = l1[good] / (2.0 * informative[good])
    return out


def nearest_half_candidates(
    distance: np.ndarray,
    *,
    anchor: int,
    selection_rows: Sequence[int],
) -> np.ndarray:
    d = np.asarray(distance, dtype=np.float64)
    rows = np.asarray(selection_rows, dtype=np.int64)
    if d.ndim != 2 or d.shape[0] != d.shape[1] or d.shape[0] != rows.size:
        raise ValueError("distance matrix and selection_rows must align")
    if anchor < 0 or anchor >= rows.size:
        raise ValueError("anchor out of range")
    if np.unique(rows).size != rows.size:
        raise ValueError("selection_rows must be unique")
    others = np.asarray(
        [i for i in range(rows.size) if i != anchor and np.isfinite(d[anchor, i])],
        dtype=np.int64,
    )
    if others.size == 0:
        return np.empty(0, dtype=np.int64)
    order = np.lexsort((rows[others], d[anchor, others]))
    ranked = others[order]
    k = math.ceil(ranked.size / LOCALITY_DENOMINATOR)
    return ranked[:k]


def isolation_scores_and_candidates(
    distance: np.ndarray,
    selection_rows: Sequence[int],
) -> tuple[np.ndarray, tuple[np.ndarray, ...]]:
    d = np.asarray(distance, dtype=np.float64)
    rows = np.asarray(selection_rows, dtype=np.int64)
    if d.ndim != 2 or d.shape != (rows.size, rows.size):
        raise ValueError("distance matrix and selection_rows must align")
    scores = np.full(rows.size, np.nan, dtype=np.float64)
    candidates: list[np.ndarray] = []
    for anchor in range(rows.size):
        selected = nearest_half_candidates(d, anchor=anchor, selection_rows=rows)
        candidates.append(selected)
        if selected.size:
            scores[anchor] = float(d[anchor, selected[-1]])
    return scores, tuple(candidates)


def _unrank_pair(rank: int, m: int) -> tuple[int, int]:
    if m < 2 or rank < 0 or rank >= m * (m - 1) // 2:
        raise ValueError("pair rank out of range")
    r = int(rank)
    for a in range(m - 1):
        width = m - a - 1
        if r < width:
            return a, a + 1 + r
        r -= width
    raise AssertionError("unreachable")


def deterministic_flat_sample(
    population: int,
    *,
    namespace: str,
    cap: int = TRIPLETS_PER_STRATUM_CAP,
) -> tuple[int, ...]:
    if population < 0 or cap < 0:
        raise ValueError("population/cap must be nonnegative")
    if population <= cap:
        return tuple(range(population))
    chosen: list[int] = []
    seen: set[int] = set()
    counter = 0
    rejection_limit = ((1 << 64) // population) * population
    while len(chosen) < cap:
        value = u64(f"{namespace}|counter|{counter}")
        counter += 1
        if value >= rejection_limit:
            continue
        index = value % population
        if index in seen:
            continue
        seen.add(index)
        chosen.append(index)
    return tuple(chosen)


def select_tail_triplets(
    *,
    z_distance: np.ndarray,
    selection_rows: Sequence[int],
    panel: int,
    source_code: int,
    fold_index: int,
    donor_code: int,
    operator_code: int,
) -> tuple[tuple[int, int, int], ...]:
    """Return local indices (anchor,j,k) for frozen q95 tail triplets."""
    rows = np.asarray(selection_rows, dtype=np.int64)
    scores, candidates = isolation_scores_and_candidates(z_distance, rows)
    tail = select_q95_isolation_tail_v1(scores, rows)
    counts = np.asarray(
        [
            len(candidates[int(anchor)]) * (len(candidates[int(anchor)]) - 1) // 2
            for anchor in tail
        ],
        dtype=np.int64,
    )
    prefix = np.cumsum(counts)
    population = int(prefix[-1]) if prefix.size else 0
    namespace = (
        "V5_FULL104_RARE_TAIL|triplet|"
        f"panel|{panel}|source|{source_code}|fold|{fold_index}|"
        f"donor|{donor_code}|operator|{operator_code}"
    )
    chosen = deterministic_flat_sample(population, namespace=namespace)
    out: list[tuple[int, int, int]] = []
    for flat in chosen:
        tail_pos = int(np.searchsorted(prefix, flat, side="right"))
        before = int(prefix[tail_pos - 1]) if tail_pos else 0
        local_rank = int(flat - before)
        anchor = int(tail[tail_pos])
        cand = candidates[anchor]
        b, c = _unrank_pair(local_rank, len(cand))
        j = int(cand[b])
        k = int(cand[c])
        if rows[j] > rows[k]:
            j, k = k, j
        out.append((anchor, j, k))
    return tuple(out)


def build_depth_detection_blocks(
    *,
    selection_rows: Sequence[int],
    source_library: Sequence[float],
    detected_count: Sequence[float],
) -> tuple[np.ndarray, ...]:
    """Historical TD59 matching-block construction within one donor x operator."""
    rows = np.asarray(selection_rows, dtype=np.int64)
    library = np.asarray(source_library, dtype=np.float64)
    detected = np.asarray(detected_count, dtype=np.float64)
    if (
        rows.ndim != 1
        or library.ndim != 1
        or detected.ndim != 1
        or not (rows.size == library.size == detected.size)
    ):
        raise ValueError("block inputs must be aligned vectors")
    if rows.size == 0 or np.unique(rows).size != rows.size:
        raise ValueError("selection_rows must be nonempty and unique")
    if not np.all(np.isfinite(library)) or not np.all(np.isfinite(detected)):
        raise ValueError("matching covariates must be finite")

    n = rows.size
    if n == 1:
        return (np.asarray([0], dtype=np.int64),)

    detected_rank = np.empty(n, dtype=np.int64)
    order = np.lexsort((rows, detected))
    detected_rank[order] = np.arange(n, dtype=np.int64)

    library_rank = np.empty(n, dtype=np.int64)
    order = np.lexsort((rows, library))
    library_rank[order] = np.arange(n, dtype=np.int64)

    detected_fraction = detected_rank / n
    library_fraction = library_rank / n
    detected_octile = np.floor(8 * detected_fraction).astype(np.int64)
    ordered = np.lexsort((rows, detected_fraction, library_fraction, detected_octile))
    chunks = [ordered[a:a + 8].astype(np.int64, copy=True) for a in range(0, n, 8)]
    if len(chunks) > 1 and len(chunks[-1]) == 1:
        chunks[-2] = np.r_[chunks[-2], chunks[-1]].astype(np.int64, copy=False)
        chunks = chunks[:-1]
    return tuple(chunks)


def matched_y_permutation(
    *,
    n_rows: int,
    blocks: Iterable[np.ndarray],
    panel: int,
    q: int,
    source_code: int,
    fold_index: int,
    donor_code: int,
    operator_code: int,
) -> np.ndarray:
    """Reassign Y identity only, by deterministic nonzero shifts within blocks."""
    if q < 0 or q >= 64:
        raise ValueError("q must be one of the 64 frozen null replicates")
    perm = np.arange(n_rows, dtype=np.int64)
    seen = np.zeros(n_rows, dtype=np.bool_)
    for block_index, raw in enumerate(blocks):
        ids = np.asarray(raw, dtype=np.int64)
        if ids.ndim != 1 or ids.size == 0:
            raise ValueError("null blocks must be nonempty vectors")
        if np.any(ids < 0) or np.any(ids >= n_rows) or np.unique(ids).size != ids.size:
            raise ValueError("null block contains invalid row indices")
        if np.any(seen[ids]):
            raise ValueError("null blocks overlap")
        seen[ids] = True
        if ids.size < 2:
            continue
        shift = 1 + (
            u64(
                "V5_FULL104_RARE_TAIL|null|"
                f"panel|{panel}|q|{q}|source|{source_code}|fold|{fold_index}|"
                f"donor|{donor_code}|operator|{operator_code}|block|{block_index}"
            )
            % (ids.size - 1)
        )
        perm[ids] = np.roll(ids, -int(shift))
    if not np.array_equal(np.sort(perm), np.arange(n_rows)):
        raise ValueError("Y-null permutation is not one-to-one")
    return perm
