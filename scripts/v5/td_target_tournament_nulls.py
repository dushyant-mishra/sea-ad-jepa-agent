"""Deterministic matched wrong-cell reassignment for synthetic/compact metadata rows."""
from collections import defaultdict
import hashlib
import json

STRATUM_KEYS = ('donor_id', 'operator_id', 'support_key', 'depth_bin', 'detection_bin')
ROW_KEYS = frozenset(('cell_id',) + STRATUM_KEYS)
_PRF_VERSION = 'JEPA_TD_MATCHED_WRONG_CELL_NULL_V1'


class NullContractError(ValueError):
    pass


class NotEstimableStratum(RuntimeError):
    pass


def _validate_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise NullContractError(f'{label} must be a nonempty string')
    if '\0' in value:
        raise NullContractError(f'{label} must be NUL-free')
    return value


def _rank(seed_material, cell_id):
    preimage = json.dumps(
        [_PRF_VERSION, 'rank', seed_material, cell_id],
        separators=(',', ':'),
        ensure_ascii=False,
    ).encode('utf-8')
    return hashlib.sha256(preimage).digest()


def _shift_seed(seed_material, key):
    preimage = json.dumps(
        [_PRF_VERSION, 'shift', seed_material, list(key)],
        separators=(',', ':'),
        ensure_ascii=False,
    ).encode('utf-8')
    return hashlib.sha256(preimage).digest()


def build_matched_wrong_cell_map(rows, seed_material):
    seed_material = _validate_text(seed_material, 'seed_material')
    if not isinstance(rows, list) or not rows:
        raise NullContractError('rows must be a nonempty list')
    by_id = {}
    strata = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict) or set(row) != ROW_KEYS:
            raise NullContractError('row fields must exactly match frozen null schema')
        cid = _validate_text(row['cell_id'], 'cell_id')
        if cid in by_id:
            raise NullContractError(f'duplicate cell_id: {cid}')
        by_id[cid] = row
        key = tuple(_validate_text(row[k], k) for k in STRATUM_KEYS)
        strata[key].append(cid)

    out = {}
    for key in sorted(strata):
        ids = strata[key]
        if len(ids) < 2:
            raise NotEstimableStratum(f'stratum cannot be deranged: {key!r}')
        ordered = sorted(ids, key=lambda cid: (_rank(seed_material, cid), cid))
        shift_seed = _shift_seed(seed_material, key)
        shift = 1 + (int.from_bytes(shift_seed[:8], 'big') % (len(ordered) - 1))
        for i, src in enumerate(ordered):
            dst = ordered[(i + shift) % len(ordered)]
            if src == dst:
                raise AssertionError('internal derangement failure')
            out[src] = dst
    return out
