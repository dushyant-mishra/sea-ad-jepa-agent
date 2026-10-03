#!/usr/bin/env python3
"""Estimate V73 stress/full synthetic storage and peak working memory.

The analytical core covers master truth, FULL104-like RNA and paired multiome matrices.
When a measured smoke root is supplied, deterministic synthetic fragment storage is also
measured and projected by observed bytes/cell. Peak/consensus/motif/network products stay
explicitly outside the total until they have their own measured calibration.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

N_GENES = 96
N_MULTIOME_RNA = 64
N_MULTIOME_ATAC = 256
TRUTH_FLOATS = 14
TRUTH_FIXED_BYTES_PER_CELL = TRUTH_FLOATS * 4 + 8 + 2 + 1 + 2
RNA_FIXED_BYTES_PER_CELL = N_GENES * (2 + 1) + 8
MULTIOME_FIXED_BYTES_PER_CELL = (N_MULTIOME_RNA + N_MULTIOME_ATAC) * 2 + 8 + 2 + 1 + 2
DEFAULT_METADATA_BYTES_PER_CELL = 58


def estimate(n_cells: int, shard_size: int, metadata_bytes_per_cell: int = DEFAULT_METADATA_BYTES_PER_CELL):
    n_shards = math.ceil(n_cells / shard_size)
    truth_payload = n_cells * TRUTH_FIXED_BYTES_PER_CELL
    full104_payload = n_cells * (RNA_FIXED_BYTES_PER_CELL + metadata_bytes_per_cell)
    paired_multiome_payload = n_cells * MULTIOME_FIXED_BYTES_PER_CELL
    known_payload = truth_payload + full104_payload + paired_multiome_payload
    full104_peak = shard_size * N_GENES * (8 + 8 + 8 + 2 + 1)
    multiome_peak = shard_size * (N_MULTIOME_RNA + N_MULTIOME_ATAC) * (8 + 8 + 2)
    peak_working = max(full104_peak, multiome_peak)
    return dict(
        n_cells=n_cells,
        shard_size=shard_size,
        n_shards=n_shards,
        truth_payload_bytes=truth_payload,
        full104_observable_payload_bytes=full104_payload,
        paired_multiome_payload_bytes=paired_multiome_payload,
        known_combined_payload_bytes=known_payload,
        combined_payload_bytes=known_payload,
        conservative_peak_working_bytes=peak_working,
        fragment_projection_requires_measured_calibration=True,
        excluded_unestimated_terms=[
            "pseudobulk fragment files",
            "peak calls and consensus region universe",
            "motif databases and ranking matrices",
            "cisTarget database outputs",
            "regulatory network outputs",
            "perturbation observer",
            "spatial observer"
        ],
        full_ecosystem_total_is_not_yet_estimated=True,
        assumptions=dict(
            full104_genes=N_GENES,
            paired_multiome_rna_genes=N_MULTIOME_RNA,
            paired_multiome_atac_regions=N_MULTIOME_ATAC,
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
    full = root / "observable_raw" / "FULL104_like_sharded"
    multi = root / "observable_raw" / "PAIRED_MULTIOME_like_sharded"
    frag = root / "observable_raw" / "PAIRED_MULTIOME_fragments"
    tm = json.loads((truth / "TRUTH_MANIFEST.json").read_text())
    fm = json.loads((full / "FULL104_SHARDED_MANIFEST.json").read_text())
    n = int(tm["n_cells"])
    tbytes = sum((truth / s["file"]).stat().st_size for s in tm["shards"])
    fbytes = 0
    for s in fm["shards"]:
        fbytes += (full / s["rna_file"]).stat().st_size
        fbytes += (full / s["metadata_file"]).stat().st_size
    mbytes = 0
    if (multi / "PAIRED_MULTIOME_SHARDED_MANIFEST.json").exists():
        mm = json.loads((multi / "PAIRED_MULTIOME_SHARDED_MANIFEST.json").read_text())
        mbytes = sum((multi / s["file"]).stat().st_size for s in mm["shards"])
    gbytes = grows = gmult = 0
    if (frag / "SYNTHETIC_FRAGMENT_MANIFEST.json").exists():
        gm = json.loads((frag / "SYNTHETIC_FRAGMENT_MANIFEST.json").read_text())
        gbytes = sum((frag / s["file"]).stat().st_size for s in gm["shards"])
        grows = int(gm["total_rows"])
        gmult = int(gm["total_multiplicity"])
    total = tbytes + fbytes + mbytes + gbytes
    return dict(
        n_cells=n,
        truth_file_bytes=tbytes,
        full104_observable_file_bytes=fbytes,
        paired_multiome_file_bytes=mbytes,
        fragment_file_bytes=gbytes,
        fragment_rows=grows,
        fragment_multiplicity=gmult,
        known_total_file_bytes=total,
        truth_bytes_per_cell=tbytes / n,
        full104_observable_bytes_per_cell=fbytes / n,
        paired_multiome_bytes_per_cell=mbytes / n,
        fragment_bytes_per_cell=gbytes / n,
        fragment_rows_per_cell=grows / n,
        fragment_multiplicity_per_cell=gmult / n,
        known_total_bytes_per_cell=total / n,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", type=int, required=True)
    ap.add_argument("--shard-size", type=int, default=10000)
    ap.add_argument("--measure-root", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    est = estimate(a.cells, a.shard_size)
    out = dict(
        schema="V73_SYNTHETIC_STRESS_RESOURCE_ESTIMATE_V3_COUPLED_FRAGMENTS",
        estimate=est,
    )
    if a.measure_root:
        measured = measured_bytes(Path(a.measure_root))
        out["measured"] = measured
        projected_frag = int(round(measured["fragment_bytes_per_cell"] * a.cells))
        out["calibrated_projection"] = dict(
            fragment_bytes_at_requested_cells=projected_frag,
            known_matrices_plus_fragments_bytes=(
                est["known_combined_payload_bytes"] + projected_frag
            ),
            calibration_cells=measured["n_cells"],
            calibration_is_ci_scale_only=True,
            requires_100k_measurement_before_500k_promotion=True,
        )
        out["measurement_scope"] = (
            "actual serialized master truth + FULL104-like RNA + paired multiome + "
            "deterministic synthetic fragments; peak/motif/network terms remain unestimated"
        )
    text = json.dumps(out, indent=2) + "\n"
    if a.out:
        Path(a.out).write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
