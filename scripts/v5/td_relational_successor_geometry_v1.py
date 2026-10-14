from __future__ import annotations

import hashlib
import math
from itertools import combinations
from typing import Iterable, Sequence

import numpy as np


class RelationalGeometryError(ValueError):
    pass


VIEW_FEATURE_COUNT = 512
PAIR_WIDTH = 2048
MIN_INFORMATIVE_COORDINATES = 256
N_NULL = 64


def _sha256_u64(text: str) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


def _feature_ids(feature_ids: Sequence[str]) -> tuple[str, ...]:
    if isinstance(feature_ids, (str, bytes)):
        raise RelationalGeometryError("feature_ids must be a sequence of unique strings")
    ids = tuple(feature_ids)
    if not ids or any(not isinstance(v, str) or not v for v in ids):
        raise RelationalGeometryError("feature_ids must contain nonempty strings")
    if len(ids) != len(set(ids)):
        raise RelationalGeometryError("feature_ids must be unique")
    return ids


def select_pair_coordinates(
    feature_ids: Sequence[str],
    *,
    panel_id: str,
    view_id: str,
    pair_count: int = PAIR_WIDTH,
) -> tuple[tuple[str, str], ...]:
    ids = _feature_ids(feature_ids)
    if not isinstance(panel_id, str) or not panel_id:
        raise RelationalGeometryError("panel_id must be a nonempty string")
    if view_id not in {"Z", "X", "Y"}:
        raise RelationalGeometryError("view_id must be Z, X or Y")
    if not isinstance(pair_count, int) or isinstance(pair_count, bool) or pair_count < 1:
        raise RelationalGeometryError("pair_count must be a positive integer")
    if math.comb(len(ids), 2) < pair_count:
        raise RelationalGeometryError("feature view does not contain enough unique pairs")

    ranked: list[tuple[bytes, str, str]] = []
    for a, b in combinations(ids, 2):
        g0, g1 = (a, b) if a < b else (b, a)
        preimage = f"TD316|panel|{panel_id}|view|{view_id}|g0|{g0}|g1|{g1}"
        ranked.append((hashlib.sha256(preimage.encode("utf-8")).digest(), g0, g1))
    ranked.sort(key=lambda item: (item[0], item[1], item[2]))
    return tuple((g0, g1) for _, g0, g1 in ranked[:pair_count])


def build_pair_sign_matrix(
    values,
    measured,
    feature_ids: Sequence[str],
    pairs: Sequence[tuple[str, str]],
) -> np.ndarray:
    ids = _feature_ids(feature_ids)
    x = np.asarray(values, dtype=float)
    support = np.asarray(measured, dtype=bool)
    if x.ndim != 2 or support.shape != x.shape:
        raise RelationalGeometryError("values and measured must be same-shape 2D arrays")
    if x.shape[1] != len(ids):
        raise RelationalGeometryError("feature_ids length does not match value width")
    if np.any(~np.isfinite(x[support])):
        raise RelationalGeometryError("measured values must be finite")
    index = {feature_id: i for i, feature_id in enumerate(ids)}
    pair_list = tuple(pairs)
    if not pair_list:
        raise RelationalGeometryError("pairs must be nonempty")
    if len(pair_list) != len(set(pair_list)):
        raise RelationalGeometryError("pairs must be unique")

    signs = np.full((x.shape[0], len(pair_list)), np.nan, dtype=np.float32)
    for p, pair in enumerate(pair_list):
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise RelationalGeometryError("each pair must be a two-string tuple")
        g0, g1 = pair
        if g0 not in index or g1 not in index or g0 == g1:
            raise RelationalGeometryError("pair references invalid feature IDs")
        i0, i1 = index[g0], index[g1]
        resolved = support[:, i0] & support[:, i1]
        diff = x[:, i0] - x[:, i1]
        signs[resolved, p] = np.sign(diff[resolved]).astype(np.float32)
    return signs


def concordance_distance_from_signs(a: np.ndarray, b: np.ndarray, *, min_informative: int) -> float:
    if not isinstance(min_informative, int) or isinstance(min_informative, bool) or min_informative < 1:
        raise RelationalGeometryError("min_informative must be a positive integer")
    if a.shape != b.shape or a.ndim != 1:
        raise RelationalGeometryError("pair-sign vectors must be same-shape 1D arrays")
    resolved = np.isfinite(a) & np.isfinite(b)
    informative = resolved & ((a != 0) | (b != 0))
    if int(informative.sum()) < min_informative:
        return float("nan")
    return float(np.mean(np.abs(a[informative] - b[informative])) / 2.0)


def build_concordance_distance_matrix(
    values,
    measured,
    feature_ids: Sequence[str],
    pairs: Sequence[tuple[str, str]],
    *,
    min_informative: int = MIN_INFORMATIVE_COORDINATES,
) -> np.ndarray:
    signs = build_pair_sign_matrix(values, measured, feature_ids, pairs)
    n = signs.shape[0]
    out = np.full((n, n), np.nan, dtype=np.float32)
    for i in range(n):
        for j in range(i, n):
            value = concordance_distance_from_signs(signs[i], signs[j], min_informative=min_informative)
            out[i, j] = value
            out[j, i] = value
    return out


def _validate_null_vectors(
    donor_ids,
    operator_ids,
    global_rows,
    source_library,
    detected_genes,
):
    donors = np.asarray(donor_ids, dtype=object)
    operators = np.asarray(operator_ids, dtype=object)
    rows = np.asarray(global_rows)
    library = np.asarray(source_library, dtype=float)
    detected = np.asarray(detected_genes)
    n = len(donors)
    if n == 0 or any(len(v) != n for v in (operators, rows, library, detected)):
        raise RelationalGeometryError("null-matching vectors must have equal nonzero length")
    if len(set(rows.tolist())) != n:
        raise RelationalGeometryError("global_rows must be unique")
    if np.any(~np.isfinite(library)) or np.any(library < 0):
        raise RelationalGeometryError("source_library must be finite and nonnegative")
    if not np.issubdtype(detected.dtype, np.integer) or np.any(detected < 0):
        raise RelationalGeometryError("detected_genes must be nonnegative integers")
    if any(not isinstance(v, str) or not v for v in donors.tolist()):
        raise RelationalGeometryError("donor IDs must be nonempty strings")
    if any(not isinstance(v, str) or not v for v in operators.tolist()):
        raise RelationalGeometryError("operator IDs must be nonempty strings")
    return donors, operators, rows.astype(np.int64), library, detected.astype(np.int64)


def _ordinal_rank_fractions(values: np.ndarray, rows: np.ndarray, indices: np.ndarray) -> dict[int, float]:
    ordered = sorted((int(i) for i in indices), key=lambda i: (values[i], int(rows[i])))
    n = len(ordered)
    return {i: rank / n for rank, i in enumerate(ordered)}


def build_td37a_blocks(
    *,
    donor_ids,
    operator_ids,
    global_rows,
    source_library,
    detected_genes,
) -> tuple[tuple[int, ...], ...]:
    donors, operators, rows, library, detected = _validate_null_vectors(
        donor_ids, operator_ids, global_rows, source_library, detected_genes
    )
    blocks: list[tuple[int, ...]] = []
    seen: list[tuple[str, str]] = []
    for donor, operator in zip(donors.tolist(), operators.tolist()):
        key = (str(donor), str(operator))
        if key not in seen:
            seen.append(key)
    donor_s = donors.astype(str)
    operator_s = operators.astype(str)
    for donor, operator in seen:
        indices = np.where((donor_s == donor) & (operator_s == operator))[0]
        det_rank = _ordinal_rank_fractions(detected, rows, indices)
        lib_rank = _ordinal_rank_fractions(library, rows, indices)
        ordered = sorted(
            (int(i) for i in indices),
            key=lambda i: (
                math.floor(8 * det_rank[i]),
                lib_rank[i],
                det_rank[i],
                int(rows[i]),
            ),
        )
        if len(ordered) == 1:
            blocks.append((ordered[0],))
            continue
        local = [tuple(ordered[start:start + 8]) for start in range(0, len(ordered), 8)]
        if len(local) >= 2 and len(local[-1]) == 1:
            local[-2] = tuple(local[-2]) + tuple(local[-1])
            local.pop()
        blocks.extend(local)
    return tuple(blocks)


def build_td37a_matched_y_null_maps(
    *,
    source: str,
    panel_id: str,
    donor_ids,
    operator_ids,
    global_rows,
    source_library,
    detected_genes,
) -> tuple[np.ndarray, tuple[tuple[int, ...], ...]]:
    if not isinstance(source, str) or not source or not isinstance(panel_id, str) or not panel_id:
        raise RelationalGeometryError("source and panel_id must be nonempty strings")
    donors, operators, rows, library, detected = _validate_null_vectors(
        donor_ids, operator_ids, global_rows, source_library, detected_genes
    )
    blocks = build_td37a_blocks(
        donor_ids=donors,
        operator_ids=operators,
        global_rows=rows,
        source_library=library,
        detected_genes=detected,
    )
    n = len(donors)
    maps = np.tile(np.arange(n, dtype=np.int64), (N_NULL, 1))
    for q in range(N_NULL):
        for block_index, block in enumerate(blocks):
            m = len(block)
            if m < 2:
                continue
            first = block[0]
            donor = str(donors[first])
            operator = str(operators[first])
            preimage = (
                f"TD316|null|panel|{panel_id}|q|{q}|source|{source}|donor|{donor}|"
                f"operator|{operator}|block|{block_index}"
            )
            shift = 1 + (_sha256_u64(preimage) % (m - 1))
            for pos, target in enumerate(block):
                maps[q, target] = block[(pos + shift) % m]
    return maps, blocks
