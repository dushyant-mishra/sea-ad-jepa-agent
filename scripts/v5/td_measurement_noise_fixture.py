"""Synthetic-only same-cell count split and depth-thinning reference.

Pure standard-library fixture helper. It opens no files and creates no authority.
"""
from __future__ import annotations

import hashlib
from collections.abc import Mapping

FROZEN_DEPTH_GRID = (0.25, 0.5, 0.75, 1.0)
_PRF_VERSION = 'JEPA_TD_MEASUREMENT_PSEUDOREPLICATE_PRF_V1'


class MeasurementFixtureError(ValueError):
    pass


def _validate(counts, support, seed_material, cell_id):
    if not isinstance(counts, Mapping):
        raise MeasurementFixtureError('counts must be a mapping')
    try:
        support = set(support)
    except Exception as exc:
        raise MeasurementFixtureError('support must be iterable') from exc
    if not isinstance(seed_material, str) or not isinstance(cell_id, str):
        raise MeasurementFixtureError('seed_material and cell_id must be exact strings')
    if not seed_material.strip():
        raise MeasurementFixtureError('seed_material must be nonempty')
    if not cell_id.strip():
        raise MeasurementFixtureError('cell_id must be nonempty')
    if '\0' in seed_material or '\0' in cell_id:
        raise MeasurementFixtureError('seed_material and cell_id must be NUL-free')
    for address in support:
        if isinstance(address, bool) or type(address) is not int or address < 0:
            raise MeasurementFixtureError(
                'support addresses must be nonnegative exact Python integers'
            )
    unknown = set(counts) - support
    if unknown:
        raise MeasurementFixtureError(
            f'count address outside physical support: {sorted(unknown, key=repr)[:5]}'
        )
    clean = {}
    for address in support:
        value = counts.get(address, 0)
        if isinstance(value, bool) or type(value) is not int or value < 0:
            raise MeasurementFixtureError(
                'counts must be nonnegative exact Python integers'
            )
        clean[address] = value
    return clean, support, seed_material, cell_id


def _byte(namespace, seed_material, cell_id, address, molecule_index):
    preimage = (
        f'{_PRF_VERSION}\0{namespace}\0{seed_material}\0{cell_id}\0'
        f'{address}\0{molecule_index}'
    ).encode('utf-8')
    return hashlib.sha256(preimage).digest()[0]


def split_counts(counts, support, *, seed_material, cell_id):
    """Create deterministic complementary 50/50 same-cell pseudoreplicates."""
    clean, support, seed_material, cell_id = _validate(
        counts, support, seed_material, cell_id
    )
    left = {address: 0 for address in support}
    right = {address: 0 for address in support}
    for address in sorted(support, key=repr):
        for molecule_index in range(clean[address]):
            if _byte('split50', seed_material, cell_id, address, molecule_index) < 128:
                left[address] += 1
            else:
                right[address] += 1
    return left, right


def nested_depth_thinning(counts, support, *, seed_material, cell_id):
    """Create nested deterministic 25/50/75/100% thinnings of the same evidence universe."""
    clean, support, seed_material, cell_id = _validate(
        counts, support, seed_material, cell_id
    )
    curves = {
        fraction: {address: 0 for address in support}
        for fraction in FROZEN_DEPTH_GRID
    }
    thresholds = {0.25: 64, 0.5: 128, 0.75: 192, 1.0: 256}
    for address in sorted(support, key=repr):
        for molecule_index in range(clean[address]):
            rank = _byte('depth', seed_material, cell_id, address, molecule_index)
            for fraction in FROZEN_DEPTH_GRID:
                if rank < thresholds[fraction]:
                    curves[fraction][address] += 1
    return curves
