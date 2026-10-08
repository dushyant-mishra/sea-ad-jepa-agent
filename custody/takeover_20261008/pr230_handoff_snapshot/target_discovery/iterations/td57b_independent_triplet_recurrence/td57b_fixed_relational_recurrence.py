#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
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
PANEL_SLICES = {
    0: ((1024, 1536), (1536, 2048)),
    1: ((2048, 2560), (2560, 3072)),
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


def select_gene_views(common: np.ndarray, panel: int) -> tuple[np.ndarray, np.ndarray]:
    ranked = np.array(sorted((int(x) for x in common), key=lambda g: digest(f'TD56S|gene|{g}')), dtype=np.int32)
    (xa, xb), (ya, yb) = PANEL_SLICES[panel]
    gx = ranked[xa:xb]
    gy = ranked[ya:yb]
    if len(gx) != 512 or len(gy) != 512 or set(gx.tolist()) & set(gy.tolist()):
        raise RuntimeError('invalid disjoint gene views')
    if set(ranked[:1024].tolist()) & (set(gx.tolist()) | set(gy.tolist())):
        raise RuntimeError('independent panel overlaps previously used TD56 genes')
    return gx, gy


def select_pairs(genes: np.ndarray, panel: int, view: str) -> tuple[np.ndarray, np.ndarray]:
    candidates: list[tuple[bytes, int, int, int, int]] = []
    for a in range(511):
        ga = int(genes[a])
        for b in range(a + 1, 512):
            gb = int(genes[b])
            g0, g1 = sorted((ga, gb))
            preimage = f'TD57B|panel|{panel}|view|{view}|g0|{g0}|g1|{g1}'
            candidates.append((digest(preimage), a, b, g0, g1))
    candidates.sort(key=lambda x: x[0])
    kept = candidates[:PAIR_COUNT]
    positions = np.array([[x[1], x[2]] for x in kept], dtype=np.int32)
    addresses = np.array([[x[3], x[4]] for x in kept], dtype=np.int32)
    return positions, addresses


def distance_matrix(signs: np.ndarray) -> np.ndarray:
    p = signs.shape[1]
    pos = (signs == 1).astype(np.int16)
    neg = (signs == -1).astype(np.int16)
    zero = (signs == 0).astype(np.int16)
    nonzero = (signs != 0).sum(axis=1).astype(np.int32)
    same = (pos @ pos.T + neg @ neg.T).astype(np.int32)
    both_zero = (zero @ zero.T).astype(np.int32)
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


def sample_triplet_indices(population: int, source: str, donor: str, operator: str) -> list[int]:
    if population <= TRIPLETS_PER_STRATUM:
        return list(range(population))
    chosen: list[int] = []
    seen: set[int] = set()
    counter = 0
    rejection_limit = ((1 << 64) // population) * population
    while len(chosen) < TRIPLETS_PER_STRATUM:
        value = u64(f'TD57B|tripletsample|source|{source}|donor|{donor}|operator|{operator}|counter|{counter}')
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

    gx, gy = select_gene_views(common, panel)
    px, ax = select_pairs(gx, panel, 'X')
    py, ay = select_pairs(gy, panel, 'Y')

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

    selected = np.r_[gx, gy]
    lut = np.full(shape[1], -1, dtype=np.int32)
    lut[selected] = np.arange(1024, dtype=np.int32)
    values = np.zeros((len(rows), 1024), dtype=np.float32)
    for i, row in enumerate(rows):
        begin, end = int(indptr[row]), int(indptr[row + 1])
        ix = indices[begin:end]
        loc = lut[ix]
        keep = loc >= 0
        if keep.any():
            values[i, loc[keep]] = data[begin:end][keep]

    sx = np.sign(values[:, px[:, 0]] - values[:, px[:, 1]]).astype(np.int8)
    sy = np.sign(values[:, 512:][:, py[:, 0]] - values[:, 512:][:, py[:, 1]]).astype(np.int8)

    strata = {}
    local = {}
    dx = {}
    dy = {}
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
            dx[key] = distance_matrix(sx[ids])
            dy[key] = distance_matrix(sy[ids])

    triplets = []
    triplet_population = 0
    for (d, o), ids in strata.items():
        n = len(ids)
        comparison_pairs = (n - 1) * (n - 2) // 2
        population = n * comparison_pairs
        triplet_population += population
        for flat_index in sample_triplet_indices(population, source, d, o):
            anchor_position = flat_index // comparison_pairs
            pair_rank = flat_index % comparison_pairs
            others = [x for x in range(n) if x != anchor_position]
            b, c = unrank_pair(pair_rank, n - 1)
            i = int(ids[anchor_position])
            j = int(ids[others[b]])
            k = int(ids[others[c]])
            if rows[j] >= rows[k]:
                raise RuntimeError('comparison-cell ordering invariant failed')
            triplets.append((d, o, i, j, k))

    base_by = {}
    observed_by = {}
    for d, o, i, j, k in triplets:
        key = (d, o)
        li, lj, lk = local[i][1], local[j][1], local[k][1]
        dx1, dx2 = dx[key][li, lj], dx[key][li, lk]
        if not np.isfinite(dx1) or not np.isfinite(dx2):
            continue
        rx = int(np.sign(dx1 - dx2))
        if rx == 0:
            continue
        base_by.setdefault(d, []).append((o, i, j, k, rx))
        dy1, dy2 = dy[key][li, lj], dy[key][li, lk]
        if not np.isfinite(dy1) or not np.isfinite(dy2):
            continue
        ry = int(np.sign(dy1 - dy2))
        if ry == 0:
            continue
        observed_by.setdefault(d, []).append((o, i, j, k, rx, ry))

    observed_donor_agreement = {
        d: float(np.mean([row[4] == row[5] for row in vals]))
        for d, vals in observed_by.items()
        if len(vals) >= 20
    }

    blocks = build_depth_detection_blocks(rows, donor, operator, library, detected)
    all_donors = sorted(np.unique(donor))
    cases = []
    for split in DONOR_SPLITS:
        ordered_donors = sorted(
            all_donors,
            key=lambda d: digest(f'TD57B|panel|{panel}|split|{split}|source|{source}|donor|{d}')
        )
        halves = [set(ordered_donors[0::2]), set(ordered_donors[1::2])]
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
                            f'TD57B|null|panel|{panel}|q|{q}|source|{source}|split|{split}|half|{half_index}|donor|{d}|operator|{o}|block|{block_index}'
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
                        dy1, dy2 = dy[key][li, lj], dy[key][li, lk]
                        if not np.isfinite(dy1) or not np.isfinite(dy2):
                            continue
                        ry = int(np.sign(dy1 - dy2))
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
                'observed_median_donor_triplet_agreement': observed,
                'null_median': float(np.median(null_array)),
                'null_p95_index60': p95,
                'null_max': float(np.max(null_array)),
                'observed_measurable_donors': len(observed_values),
                'null_measurable_donors_min': int(min(null_donor_counts)),
                'null_measurable_donors_max': int(max(null_donor_counts)),
                'pass': passed,
            })

    payload = {
        'schema': 'TD57B_FIXED_RELATIONAL_RECURRENCE_RESULT_V1',
        'status': 'PASS' if all(row['pass'] for row in cases) else 'FAIL',
        'source': source,
        'panel': panel,
        'input_sha256': {'metadata': META_SHA256[source], 'support': SUPPORT_SHA256, **ARRAY_SHA256},
        'common_scalar_addresses': int(len(common)),
        'gene_view_X': gx.astype(int).tolist(),
        'gene_view_Y': gy.astype(int).tolist(),
        'pair_addresses_X_sha256': hashlib.sha256(ax.astype('<i4').tobytes()).hexdigest(),
        'pair_addresses_Y_sha256': hashlib.sha256(ay.astype('<i4').tobytes()).hexdigest(),
        'pair_count_per_view': PAIR_COUNT,
        'minimum_informative_pair_coordinates': MIN_INFORMATIVE,
        'triplets_per_stratum_cap': TRIPLETS_PER_STRATUM,
        'triplet_population': int(triplet_population),
        'sampled_triplets': int(len(triplets)),
        'measurable_observed_donors_total': int(len(observed_donor_agreement)),
        'cases': cases,
        'terminal': 'TD57B_SOURCE_PANEL_PASS' if all(row['pass'] for row in cases) else 'TD57B_SOURCE_PANEL_FAIL',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
