#!/usr/bin/env python3
"""Estimate V73 stress/full synthetic storage and peak working memory."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

N_GENES = 96
TRUTH_FLOATS = 14
TRUTH_FIXED_BYTES_PER_CELL = TRUTH_FLOATS * 4 + 8 + 2 + 1 + 2
RNA_FIXED_BYTES_PER_CELL = N_GENES * (2 + 1) + 8
DEFAULT_METADATA_BYTES_PER_CELL = 58


def estimate(n_cells: int, shard_size: int, metadata_bytes_per_cell: int = DEFAULT_METADATA_BYTES_PER_CELL):
    n_shards = math.ceil(n_cells / shard_size)
    truth_payload = n_cells * TRUTH_FIXED_BYTES_PER_CELL
    observable_payload = n_cells * (RNA_FIXED_BYTES_PER_CELL + metadata_bytes_per_cell)
    # Working matrix for one FULL104 observer shard: eta/lambda/u float64 plus output counts
    # and availability, intentionally conservative because temporaries coexist.
    peak_working = shard_size * N_GENES * (8 + 8 + 8 + 2 + 1)
    return dict(
        n_cells=n_cells,
        shard_size=shard_size,
        n_shards=n_shards,
        truth_payload_bytes=truth_payload,
        full104_observable_payload_bytes=observable_payload,
        combined_payload_bytes=truth_payload + observable_payload,
        conservative_peak_working_bytes=peak_working,
        assumptions=dict(
            genes=N_GENES,
            truth_float32_dimensions=TRUTH_FLOATS,
            counts_dtype="int16",
            availability_dtype="uint8",
            metadata_bytes_per_cell=metadata_bytes_per_cell,
            excludes_compression_gain=True,
            excludes_filesystem_npz_zip_headers=True,
        ),
    )


def measured_bytes(root: Path):
    truth = root / "hidden_truth"
    obs = root / "observable_raw" / "FULL104_like_sharded"
    tm = json.loads((truth / "TRUTH_MANIFEST.json").read_text())
    om = json.loads((obs / "FULL104_SHARDED_MANIFEST.json").read_text())
    n = int(tm["n_cells"])
    tbytes = sum((truth / s["file"]).stat().st_size for s in tm["shards"])
    obytes = 0
    for s in om["shards"]:
        obytes += (obs / s["rna_file"]).stat().st_size
        obytes += (obs / s["metadata_file"]).stat().st_size
    return dict(
        n_cells=n,
        truth_file_bytes=tbytes,
        observable_file_bytes=obytes,
        truth_bytes_per_cell=tbytes / n,
        observable_bytes_per_cell=obytes / n,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", type=int, required=True)
    ap.add_argument("--shard-size", type=int, default=10000)
    ap.add_argument("--measure-root", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = dict(
        schema="V73_SYNTHETIC_STRESS_RESOURCE_ESTIMATE_V1",
        estimate=estimate(a.cells, a.shard_size),
    )
    if a.measure_root:
        out["measured"] = measured_bytes(Path(a.measure_root))
        out["measurement_scope"] = (
            "actual serialized truth + FULL104-like observer only; used to calibrate the "
            "analytical estimate before 1e5-cell promotion"
        )
    text = json.dumps(out, indent=2) + "\n"
    if a.out:
        Path(a.out).write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
