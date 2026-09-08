#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ARRAY_ROOT = Path('/mnt/data/td_matrix_npz/arrays')
SUPPORT_PATH = Path('/mnt/data/td_support_extract/FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz')
META_PATHS = {
    'HVS': Path('/mnt/data/td50_HVS.npz'),
    'NPH52': Path('/mnt/data/td50_NPH52.npz'),
    'SEA_AD': Path('/mnt/data/td50_SEA_AD.npz'),
}
META_SHA256 = {
    'HVS': 'd6d30cb5ef791fdaaa6f751ee6d802f8e64e062ab641a48194dfc9b596609aeb',
    'NPH52': '9de0c199414db0705d25cce18cb5007915bcf527c245ed039e2f966437c790fe',
    'SEA_AD': 'ab4fa37a2596de609b4245e82dec0ba7e4a43f95d03421acd46c5814eaaa57d4',
}
ARRAY_SHA256 = {
    'data.npy': '0276be0538515146a66012fc9f871eebff2b5cab4de644a7a3a20c29242ef72e',
    'indices.npy': 'f1fc3200adfcebaa5a1214a4f4259fd5a469f6ddbd1379ad73b1222a440e9771',
    'indptr.npy': '58182d0a8fb8af88cc5b010775056b04e637279669d352b85935ef36d66cf4b1',
    'shape.npy': '5547a1cd96a984b5163c5540a616006baca3d2a91985005a8f23e970a3133beb',
}
SUPPORT_SHA256 = '852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537'
PAIR_COUNT = 2048
MIN_INFORMATIVE = 256
TRIPLETS_PER_STRATUM = 64
NULLS = 64
DONOR_SPLITS = (0, 1)
LOCAL_DENOMINATOR = 2  # nearest one-half
PANEL_SLICES = {
    0: {'Z': (6144, 6656), 'X': (6656, 7168), 'Y': (7168, 7680)},
    1: {'Z': (7680, 8192), 'X': (8192, 8704), 'Y': (8704, 9216)},
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def digest(text: str) -> bytes:
    return hashlib.sha256(text.encode('utf-8')).digest()


def u64(text: str) -> int:
    return int.from_bytes(digest(text)[:8], 'big', signed=False)


def verify_inputs(source: str) -> None:
    for name, expected in ARRAY_SHA256.items():
        actual = sha256_file(ARRAY_ROOT / name)
        if actual != expected:
            raise RuntimeError(f'array SHA mismatch {name}: {actual} != {expected}')
    actual = sha256_file(SUPPORT_PATH)
    if actual != SUPPORT_SHA256:
        raise RuntimeError(f'support SHA mismatch: {actual} != {SUPPORT_SHA256}')
    actual = sha256_file(META_PATHS[source])
    if actual != META_SHA256[source]:
        raise RuntimeError(f'metadata SHA mismatch {source}: {actual} != {META_SHA256[source]}')


def ranked_common(common: np.ndarray) -> np.ndarray:
    return np.array(
        sorted((int(x) for x in common), key=lambda g: digest(f'TD56S|gene|{g}')),
        dtype=np.int32,
    )


def select_gene_views(common: np.ndarray, panel: int) -> dict[str, np.ndarray]:
    ranked = ranked_common(common)
    views = {
        label: ranked[start:end]
        for label, (start, end) in PANEL_SLICES[panel].items()
    }
    for label, genes in views.items():
        if len(genes) != 512:
            raise RuntimeError(f'{label} view is not 512 genes')
        if set(ranked[:6144].tolist()) & set(genes.tolist()):
            raise RuntimeError('TD59 view overlaps previously opened TD56/TD57B genes')
    labels = tuple(views)
    for i, a in enumerate(labels):
        for b in labels[i + 1:]:
            if set(views[a].tolist()) & set(views[b].tolist()):
                raise RuntimeError('TD59 views are not disjoint')
    return views


def select_pairs(genes: np.ndarray, panel: int, view: str) -> tuple[np.ndarray, np.ndarray]:
    candidates: list[tuple[bytes, int, int, int, int]] = []
    for a in range(511):
        ga = int(genes[a])
        for b in range(a + 1, 512):
            gb = int(genes[b])
            g0, g1 = sorted((ga, gb))
            preimage = f'TD59|panel|{panel}|view|{view}|g0|{g0}|g1|{g1}'
            candidates.append((digest(preimage), a, b, g0, g1))
    candidates.sort(key=lambda x: x[0])
    kept = candidates[:PAIR_COUNT]
    positions = np.array([[x[1], x[2]] for x in kept], dtype=np.int32)
    addresses = np.array([[x[3], x[4]] for x in kept], dtype=np.int32)
    return positions, addresses


def distance_matrix(signs: np.ndarray) -> np.ndarray:
    p = signs.shape[1]
    # Exact integer category counts through float32 GEMM: all counts <= 2048.
    pos = (signs == 1).astype(np.float32)
    neg = (signs == -1).astype(np.float32)
    zero = (signs == 0).astype(np.float32)
    nonzero = (signs != 0).sum(axis=1).astype(np.int32)
    same = np.rint(pos @ pos.T + neg @ neg.T).astype(np.int32)
    both_zero = np.rint(zero @ zero.T).astype(np.int32)
    l1 = nonzero[:, None] + nonzero[None, :] - 2 * same
    informative = p - both_zero
    out = np.full((len(signs), len(signs)), np.nan, dtype=np.float64)
    good = informative >= MIN_INFORMATIVE
    out[good] = l1[good] / (2.0 * informative[good])
    return out


def unrank_pair(rank: int, m: int) -> tuple[int, int]:
    r = int(rank)
    for a in range(m - 1):
        width = m - a - 1
        if r < width:
            return a, a + 1 + r
        r -= width
    raise RuntimeError('pair rank out of range')


def sample_flat_indices(population: int, panel: int, source: str, donor: str, operator: str) -> list[int]:
    if population <= TRIPLETS_PER_STRATUM:
        return list(range(population))
    chosen: list[int] = []
    seen: set[int] = set()
    counter = 0
    rejection_limit = ((1 << 64) // population) * population
    while len(chosen) < TRIPLETS_PER_STRATUM:
        value = u64(
            f'TD59|tripletsample|panel|{panel}|source|{source}|donor|{donor}|operator|{operator}|counter|{counter}'
        )
        counter += 1
        if value >= rejection_limit:
            continue
        index = value % population
        if index in seen:
            continue
        seen.add(index)
        chosen.append(index)
    return chosen


def build_depth_detection_blocks(rows, donor, operator, library, detected):
    blocks = []
    for d in sorted(np.unique(donor)):
        for o in sorted(np.unique(operator[donor == d])):
            ids = np.where((donor == d) & (operator == o))[0]
            n = len(ids)
            if n == 1:
                blocks.append((d, o, 0, ids.copy()))
                continue
            position = {int(x): k for k, x in enumerate(ids)}
            detected_rank = np.empty(n, dtype=np.int64)
            order = ids[np.lexsort((rows[ids], detected[ids]))]
            for k, x in enumerate(order):
                detected_rank[position[int(x)]] = k
            library_rank = np.empty(n, dtype=np.int64)
            order = ids[np.lexsort((rows[ids], library[ids]))]
            for k, x in enumerate(order):
                library_rank[position[int(x)]] = k
            detected_fraction = detected_rank / n
            library_fraction = library_rank / n
            detected_octile = np.floor(8 * detected_fraction).astype(np.int64)
            ordered = ids[np.lexsort((rows[ids], detected_fraction, library_fraction, detected_octile))]
            chunks = [ordered[a:a + 8] for a in range(0, n, 8)]
            if len(chunks) > 1 and len(chunks[-1]) == 1:
                chunks[-2] = np.r_[chunks[-2], chunks[-1]]
                chunks = chunks[:-1]
            for block_index, block in enumerate(chunks):
                blocks.append((d, o, block_index, block))
    return blocks


def structural_eligible_donors(donor: np.ndarray, operator: np.ndarray) -> set[str]:
    totals: dict[str, int] = {}
    for d in sorted(np.unique(donor)):
        total = 0
        for o in sorted(np.unique(operator[donor == d])):
            n = int(np.sum((donor == d) & (operator == o)))
            if n < 4:
                continue
            k = math.ceil((n - 1) / LOCAL_DENOMINATOR)
            population = n * (k * (k - 1) // 2)
            total += min(population, TRIPLETS_PER_STRATUM)
        if total >= 20:
            totals[d] = total
    return set(totals)


def build_local_triplets(
    source: str,
    panel: int,
    rows: np.ndarray,
    donor: np.ndarray,
    operator: np.ndarray,
    strata: dict,
    local: dict,
    dz: dict,
):
    triplets = []
    total_population = 0
    candidate_fractions = []
    candidate_sizes = []
    anchors_with_candidates = 0

    for (d, o), ids in strata.items():
        matrix = dz[(d, o)]
        candidate_lists: list[np.ndarray] = []
        counts = []
        for anchor in range(len(ids)):
            others = np.array([x for x in range(len(ids)) if x != anchor and np.isfinite(matrix[anchor, x])], dtype=np.int64)
            if len(others) == 0:
                selected = np.array([], dtype=np.int64)
            else:
                order = np.lexsort((rows[ids[others]], matrix[anchor, others]))
                ranked = others[order]
                k = math.ceil(len(ranked) / LOCAL_DENOMINATOR)
                selected = ranked[:k]
                candidate_fractions.append(k / len(ranked))
                candidate_sizes.append(k)
                anchors_with_candidates += 1
            candidate_lists.append(selected)
            counts.append(len(selected) * (len(selected) - 1) // 2)

        prefix = np.cumsum(np.asarray(counts, dtype=np.int64))
        population = int(prefix[-1]) if len(prefix) else 0
        total_population += population
        if population == 0:
            continue
        for flat in sample_flat_indices(population, panel, source, d, o):
            anchor = int(np.searchsorted(prefix, flat, side='right'))
            before = int(prefix[anchor - 1]) if anchor else 0
            local_rank = int(flat - before)
            candidates = candidate_lists[anchor]
            b, c = unrank_pair(local_rank, len(candidates))
            i = int(ids[anchor])
            j = int(ids[int(candidates[b])])
            k = int(ids[int(candidates[c])])
            if rows[j] > rows[k]:
                j, k = k, j
            triplets.append((d, o, i, j, k))

    diagnostics = {
        'local_triplet_population': total_population,
        'sampled_local_triplets': len(triplets),
        'anchors_with_selector_candidates': anchors_with_candidates,
        'candidate_size_median': float(np.median(candidate_sizes)) if candidate_sizes else None,
        'candidate_size_min': int(min(candidate_sizes)) if candidate_sizes else None,
        'candidate_size_max': int(max(candidate_sizes)) if candidate_sizes else None,
        'candidate_fraction_median': float(np.median(candidate_fractions)) if candidate_fractions else None,
        'candidate_fraction_max': float(max(candidate_fractions)) if candidate_fractions else None,
    }
    return triplets, diagnostics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', choices=tuple(META_PATHS), required=True)
    parser.add_argument('--panel', type=int, choices=(0, 1), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source
    panel = int(args.panel)
    verify_inputs(source)

    data = np.load(ARRAY_ROOT / 'data.npy', mmap_mode='r')
    indices = np.load(ARRAY_ROOT / 'indices.npy', mmap_mode='r')
    indptr = np.load(ARRAY_ROOT / 'indptr.npy', mmap_mode='r')
    shape = tuple(np.load(ARRAY_ROOT / 'shape.npy'))
    states = np.load(SUPPORT_PATH)['states']
    common = np.where((states == 1).all(axis=0))[0]
    if len(common) != 17186:
        raise RuntimeError(f'common-scalar count mismatch: {len(common)}')

    views = select_gene_views(common, panel)
    pair_positions = {}
    pair_addresses = {}
    for label in ('Z', 'X', 'Y'):
        pair_positions[label], pair_addresses[label] = select_pairs(views[label], panel, label)

    meta = np.load(META_PATHS[source], allow_pickle=True)
    rows = meta['global_row'].astype(np.int64)
    donor = meta['donor'].astype(str)
    operator = meta['operator'].astype(str)
    library = meta['source_library'].astype(float)
    detected = meta['detected'].astype(float)
    expected_rows = {'HVS': 1129, 'NPH52': 1310, 'SEA_AD': 22561}[source]
    if len(rows) != expected_rows:
        raise RuntimeError(f'{source} A-row count mismatch: {len(rows)} != {expected_rows}')
    if len(np.unique(rows)) != len(rows) or np.any(rows < 0) or np.any(rows >= 25000):
        raise RuntimeError('global_row binding invalid or outside A_NATURAL_MIXTURE')

    selected = np.r_[views['Z'], views['X'], views['Y']]
    lut = np.full(shape[1], -1, dtype=np.int32)
    lut[selected] = np.arange(1536, dtype=np.int32)
    values = np.zeros((len(rows), 1536), dtype=np.float32)
    for i, row in enumerate(rows):
        begin, end = int(indptr[row]), int(indptr[row + 1])
        ix = indices[begin:end]
        loc = lut[ix]
        keep = loc >= 0
        if keep.any():
            values[i, loc[keep]] = data[begin:end][keep]

    signs = {}
    for view_index, label in enumerate(('Z', 'X', 'Y')):
        offset = 512 * view_index
        block = values[:, offset:offset + 512]
        positions = pair_positions[label]
        signs[label] = np.sign(block[:, positions[:, 0]] - block[:, positions[:, 1]]).astype(np.int8)

    strata = {}
    local = {}
    distances = {'Z': {}, 'X': {}, 'Y': {}}
    for d in sorted(np.unique(donor)):
        for o in sorted(np.unique(operator[donor == d])):
            ids = np.where((donor == d) & (operator == o))[0]
            if len(ids) < 4:
                continue
            ids = ids[np.argsort(rows[ids], kind='stable')]
            key = (d, o)
            strata[key] = ids
            for k, idx in enumerate(ids):
                local[int(idx)] = (key, k)
            for label in ('Z', 'X', 'Y'):
                distances[label][key] = distance_matrix(signs[label][ids])

    triplets, local_diag = build_local_triplets(
        source, panel, rows, donor, operator, strata, local, distances['Z']
    )

    base_by = {}
    observed_by = {}
    for d, o, i, j, k in triplets:
        key = (d, o)
        li, lj, lk = local[i][1], local[j][1], local[k][1]
        x1, x2 = distances['X'][key][li, lj], distances['X'][key][li, lk]
        if not np.isfinite(x1) or not np.isfinite(x2):
            continue
        rx = int(np.sign(x1 - x2))
        if rx == 0:
            continue
        base_by.setdefault(d, []).append((o, i, j, k, rx))
        y1, y2 = distances['Y'][key][li, lj], distances['Y'][key][li, lk]
        if not np.isfinite(y1) or not np.isfinite(y2):
            continue
        ry = int(np.sign(y1 - y2))
        if ry == 0:
            continue
        observed_by.setdefault(d, []).append((o, i, j, k, rx, ry))

    observed_donor_agreement = {
        d: float(np.mean([row[4] == row[5] for row in vals]))
        for d, vals in observed_by.items()
        if len(vals) >= 20
    }

    structural = structural_eligible_donors(donor, operator)
    if len(structural) < 8:
        raise RuntimeError(f'only {len(structural)} structurally eligible donors')

    blocks = build_depth_detection_blocks(rows, donor, operator, library, detected)
    cases = []
    for split in DONOR_SPLITS:
        ordered = sorted(
            structural,
            key=lambda d: digest(f'TD59|panel|{panel}|split|{split}|source|{source}|donor|{d}')
        )
        halves = [set(ordered[0::2]), set(ordered[1::2])]
        for half_index, half_donors in enumerate(halves):
            observed_values = [
                observed_donor_agreement[d]
                for d in half_donors
                if d in observed_donor_agreement
            ]
            if len(observed_values) < 4:
                raise RuntimeError(f'observed split {split} half {half_index} has <4 measurable donors')
            observed = float(np.median(observed_values))
            null_values = []
            null_donor_counts = []
            for q in range(NULLS):
                permutation = np.arange(len(rows))
                for d, o, block_index, ids in blocks:
                    if d not in half_donors or len(ids) < 2:
                        continue
                    shift = 1 + (
                        u64(
                            f'TD59|null|panel|{panel}|q|{q}|source|{source}|split|{split}|half|{half_index}|donor|{d}|operator|{o}|block|{block_index}'
                        ) % (len(ids) - 1)
                    )
                    permutation[ids] = np.roll(ids, -shift)

                donor_null = []
                for d in half_donors:
                    agreements = []
                    for o, i, j, k, rx in base_by.get(d, []):
                        key = (d, o)
                        pi, pj, pk = int(permutation[i]), int(permutation[j]), int(permutation[k])
                        li, lj, lk = local[pi][1], local[pj][1], local[pk][1]
                        y1, y2 = distances['Y'][key][li, lj], distances['Y'][key][li, lk]
                        if not np.isfinite(y1) or not np.isfinite(y2):
                            continue
                        ry = int(np.sign(y1 - y2))
                        if ry == 0:
                            continue
                        agreements.append(rx == ry)
                    if len(agreements) >= 20:
                        donor_null.append(float(np.mean(agreements)))
                if len(donor_null) < 4:
                    raise RuntimeError(f'null {q} split {split} half {half_index} has <4 measurable donors')
                null_values.append(float(np.median(donor_null)))
                null_donor_counts.append(len(donor_null))

            null_array = np.asarray(null_values, dtype=np.float64)
            if len(null_array) != 64 or not np.isfinite(null_array).all():
                raise RuntimeError('null vector is not exactly 64 finite values')
            p95 = float(np.sort(null_array)[60])
            passed = bool(observed > 0.5 and observed > p95)
            cases.append({
                'split': int(split),
                'half': int(half_index),
                'observed_median_donor_local_triplet_agreement': observed,
                'null_median': float(np.median(null_array)),
                'null_p95_index60': p95,
                'null_max': float(np.max(null_array)),
                'observed_measurable_donors': len(observed_values),
                'null_measurable_donors_min': int(min(null_donor_counts)),
                'null_measurable_donors_max': int(max(null_donor_counts)),
                'pass': passed,
            })

    payload = {
        'schema': 'TD59_THREE_VIEW_LOCAL_GEOMETRY_RESULT_V1',
        'status': 'PASS' if all(row['pass'] for row in cases) else 'FAIL',
        'source': source,
        'panel': panel,
        'input_sha256': {'metadata': META_SHA256[source], 'support': SUPPORT_SHA256, **ARRAY_SHA256},
        'common_scalar_addresses': int(len(common)),
        'gene_views': {label: views[label].astype(int).tolist() for label in ('Z', 'X', 'Y')},
        'pair_address_sha256': {
            label: hashlib.sha256(pair_addresses[label].astype('<i4').tobytes()).hexdigest()
            for label in ('Z', 'X', 'Y')
        },
        'pair_count_per_view': PAIR_COUNT,
        'minimum_informative_pair_coordinates': MIN_INFORMATIVE,
        'local_selector_fraction': '1/2',
        'structurally_eligible_donors': len(structural),
        'measurable_observed_donors_total': len(observed_donor_agreement),
        **local_diag,
        'cases': cases,
        'terminal': 'TD59_SOURCE_PANEL_PASS' if all(row['pass'] for row in cases) else 'TD59_SOURCE_PANEL_FAIL',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
