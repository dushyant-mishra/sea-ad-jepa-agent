"""Deterministic matched wrong-cell reassignment for synthetic/compact metadata rows."""
from collections import defaultdict
import hashlib

STRATUM_KEYS = ('donor_id', 'operator_id', 'support_key', 'depth_bin', 'detection_bin')


class NotEstimableStratum(RuntimeError):
    pass


def _rank(seed_material, cell_id):
    return hashlib.sha256(f'{seed_material}\0{cell_id}'.encode('utf-8')).digest()


def build_matched_wrong_cell_map(rows, seed_material):
    by_id = {}
    strata = defaultdict(list)
    for row in rows:
        cid = row['cell_id']
        if cid in by_id:
            raise ValueError(f'duplicate cell_id: {cid}')
        by_id[cid] = row
        key = tuple(row[k] for k in STRATUM_KEYS)
        strata[key].append(cid)

    out = {}
    for key in sorted(strata, key=repr):
        ids = strata[key]
        if len(ids) < 2:
            raise NotEstimableStratum(f'stratum cannot be deranged: {key!r}')
        ordered = sorted(ids, key=lambda cid: (_rank(seed_material, cid), cid))
        shift_seed = hashlib.sha256((str(seed_material) + '\0' + repr(key)).encode('utf-8')).digest()
        shift = 1 + (int.from_bytes(shift_seed[:8], 'big') % (len(ordered) - 1))
        for i, src in enumerate(ordered):
            dst = ordered[(i + shift) % len(ordered)]
            if src == dst:
                raise AssertionError('internal derangement failure')
            out[src] = dst
    return out
