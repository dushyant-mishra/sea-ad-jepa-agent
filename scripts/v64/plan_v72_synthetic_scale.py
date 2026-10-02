#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

FULL104_COUNTS = {"HVS": 198718, "NPH52": 236476, "SEA_AD": 4118213}
FULL104_TOTAL = sum(FULL104_COUNTS.values())


def ordered_digest(items):
    h = hashlib.sha256()
    for i, x in enumerate(items):
        h.update(str(i).encode())
        h.update(b"\x1f")
        h.update(str(x).encode())
        h.update(b"\x1e")
    return h.hexdigest()


def allocate_counts(total, weights):
    raw = {k: total * v for k, v in weights.items()}
    base = {k: int(math.floor(v)) for k, v in raw.items()}
    rem = total - sum(base.values())
    order = sorted(weights, key=lambda k: (raw[k] - base[k], k), reverse=True)
    for k in order[:rem]:
        base[k] += 1
    return base


def plan(cells: int, donors: int, cells_per_shard: int = 50000):
    if cells <= 0 or donors <= 0 or cells_per_shard <= 0:
        raise ValueError("cells, donors and cells_per_shard must be positive")
    weights = {k: v / FULL104_TOTAL for k, v in FULL104_COUNTS.items()}
    source_counts = allocate_counts(cells, weights)
    cell_ids = [f"SYN_CELL_{i:08d}" for i in range(cells)]
    donor_ids = [f"SYN_DONOR_{i:03d}" for i in range(donors)]

    shards = []
    for shard_id, start in enumerate(range(0, cells, cells_per_shard)):
        stop = min(cells, start + cells_per_shard)
        shard_cells = cell_ids[start:stop]
        shards.append({
            "shard_id": shard_id,
            "start_global_index": start,
            "stop_global_index_exclusive": stop,
            "n_cells": stop - start,
            "first_cell_id": shard_cells[0],
            "last_cell_id": shard_cells[-1],
            "ordered_cell_digest": ordered_digest(shard_cells),
        })

    return {
        "schema": "V72_SYNTHETIC_SCALE_PLAN_V1",
        "cells": cells,
        "donors": donors,
        "cells_per_shard": cells_per_shard,
        "n_shards": len(shards),
        "source_counts": source_counts,
        "source_count_sum": sum(source_counts.values()),
        "donor_registry": donor_ids,
        "global_cell_registry_digest": ordered_digest(cell_ids),
        "shards": shards,
        "merge_invariants": {
            "exact_global_index_cover": True,
            "duplicates_allowed": False,
            "reordering_allowed": False,
        },
        "resource_status": "REQUIRES_MEASURED_BYTES_PER_UNIT_BEFORE_EXECUTION",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", type=int, required=True)
    ap.add_argument("--donors", type=int, required=True)
    ap.add_argument("--cells-per-shard", type=int, default=50000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    obj = plan(a.cells, a.donors, a.cells_per_shard)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(obj, indent=2) + "\n")
    print(out)


if __name__ == "__main__":
    main()
