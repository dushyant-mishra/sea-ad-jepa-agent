#!/usr/bin/env python3
from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np


RANKING_SEED = 20261001
BLAS_THREADS = 1
FULL104_SOURCE_COUNTS = {"HVS": 198718, "NPH52": 236476, "SEA_AD": 4118213}
FULL104_TOTAL = sum(FULL104_SOURCE_COUNTS.values())


def allocate_source_counts(total: int):
    raw = {k: total * v / FULL104_TOTAL for k, v in FULL104_SOURCE_COUNTS.items()}
    base = {k: int(np.floor(v)) for k, v in raw.items()}
    rem = total - sum(base.values())
    order = sorted(raw, key=lambda k: (raw[k] - base[k], k), reverse=True)
    for k in order[:rem]:
        base[k] += 1
    return base



def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_csv(path: Path, rows, header):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def interval_overlap(a0, a1, b0, b1):
    return max(a0, b0) < min(a1, b1)


def build(root: Path, seed: int = 7201, n_cells: int = 10000) -> Path:
    rng = np.random.default_rng(seed)
    observable = root / "observable_raw"
    truth = root / "hidden_truth"
    observable.mkdir(parents=True, exist_ok=True)
    truth.mkdir(parents=True, exist_ok=True)

    if n_cells < 1000:
        raise ValueError("V72 coupled CI fixture requires at least 1000 cells")
    n_donors = 12
    n_genes = 32
    n_peaks = 48

    donors = np.array([f"D{i:02d}" for i in range(n_donors)], dtype="U4")
    cell_donor = np.array([donors[i % n_donors] for i in range(n_cells)], dtype="U4")
    source_counts = allocate_source_counts(n_cells)
    source = np.array(
        ["SEA_AD"] * source_counts["SEA_AD"]
        + ["NPH52"] * source_counts["NPH52"]
        + ["HVS"] * source_counts["HVS"],
        dtype="U8",
    )
    operators = np.array([f"OP{i % 6:02d}" for i in range(n_cells)], dtype="U4")
    genes = np.array([f"ENSG_SYN_{i:05d}" for i in range(n_genes)], dtype="U32")
    tfs = np.array([f"TF_SYN_{i:03d}" for i in range(8)], dtype="U16")

    z_global = rng.normal(size=(n_cells, 3))
    z_query = rng.normal(size=(n_cells, 1))
    z_shared = rng.normal(size=(n_cells, 3))
    z_private = rng.normal(size=(n_cells, 2))
    tech = rng.normal(size=(n_cells, 2))
    source_bio = np.zeros((n_cells, 2))
    source_bio[source == "NPH52", 0] = 0.5
    source_bio[source == "HVS", 1] = -0.5

    wg = rng.normal(scale=0.28, size=(9, n_genes))
    eta_rna = np.c_[z_global, z_query, z_shared, source_bio] @ wg
    eta_rna += tech[:, :1] * rng.normal(scale=0.12, size=(1, n_genes))
    rna = rng.poisson(np.exp(np.clip(eta_rna, -2.5, 2.5))).astype(np.int32)

    peak_starts = np.arange(n_peaks, dtype=int) * 2500 + 10000
    peak_ends = peak_starts + 1200
    peak_names = np.array(
        [f"chr1:{s}-{e}" for s, e in zip(peak_starts, peak_ends)], dtype="U40"
    )
    wa = rng.normal(scale=0.25, size=(10, n_peaks))
    eta_atac = np.c_[z_global, z_shared, z_private, tech] @ wa
    atac = rng.poisson(np.exp(np.clip(eta_atac, -2.5, 2.5))).astype(np.int32)

    # Truth graph: explicit and shared across every observation operator.
    truth_graph = []
    for i in range(24):
        truth_graph.append({
            "tf": str(tfs[i % len(tfs)]),
            "peak": str(peak_names[i]),
            "gene": str(genes[(i * 3) % n_genes]),
            "program": f"PROGRAM_{i % 4}",
            "causal": bool(i % 5 != 0),
        })
    np.savez_compressed(
        truth / "LATENTS.npz",
        z_global=z_global,
        z_query=z_query,
        z_reg_shared=z_shared,
        z_reg_private=z_private,
        technical_latents=tech,
        source_specific_biology=source_bio,
    )
    (truth / "REGULATORY_GRAPH.json").write_text(
        json.dumps({"schema": "V72_SYNTHETIC_TRUTH_GRAPH_V1", "edges": truth_graph}, indent=2) + "\n"
    )

    # FULL104-like RNA backbone.
    full = observable / "FULL104_LIKE"
    full.mkdir()
    availability = np.ones((n_genes, n_cells), dtype=np.uint8)
    hvs_idx = np.where(source == "HVS")[0]
    availability[n_genes - 8 :, hvs_idx] = 0
    full_rna = rna.copy().T
    full_rna[availability == 0] = 0
    np.savez_compressed(
        full / "rna_counts.npz",
        matrix=full_rna,
        genes=genes,
        cells=np.array([f"CELL{i:05d}" for i in range(n_cells)], dtype="U16"),
        availability=availability,
    )
    write_csv(
        full / "metadata.csv",
        [
            [f"CELL{i:05d}", cell_donor[i], source[i], operators[i], "Microglia"]
            for i in range(n_cells)
        ],
        ["cell_id", "donor", "source", "operator", "cell_type"],
    )
    (full / "contract.json").write_text(
        json.dumps(
            {
                "schema": "V72_FULL104_LIKE_OBSERVABLE_V1",
                "structural_missingness_is_not_zero": True,
                "source_families": ["SEA_AD", "NPH52", "HVS"],
                "operators": sorted(set(operators.tolist())),
            },
            indent=2,
        )
        + "\n"
    )

    # Stage4-like linked/control construction. Controls are promoter-fixed and distance-matched.
    stage4 = observable / "STAGE4_LIKE"
    stage4.mkdir()
    stage4_windows = []
    for i in range(18):
        start = 8000 + i * 4000
        stage4_windows.append((f"W{i:03d}", "chr1", start, start + 5000))
    write_csv(stage4 / "intervals_5kb.csv", stage4_windows, ["interval_id", "chrom", "start", "end"])

    pair_rows = []
    for i in range(16):
        promoter = f"PROM{i % 6:02d}"
        linked = stage4_windows[i]
        control = stage4_windows[(i + 2) % len(stage4_windows)]
        linked_mid = (linked[2] + linked[3]) // 2
        control_mid = (control[2] + control[3]) // 2
        promoter_pos = 1000 + (i % 6) * 8000
        ld = abs(linked_mid - promoter_pos)
        cd = abs(control_mid - promoter_pos)
        # The frozen tolerance has a 10 kb floor; adjust the synthetic promoter if necessary.
        if abs(ld - cd) > max(int(round(ld * 0.10)), 10000):
            promoter_pos = (linked_mid + control_mid) // 2
            ld = abs(linked_mid - promoter_pos)
            cd = abs(control_mid - promoter_pos)
        pair_rows.append(
            [
                f"EDGE{i:03d}",
                promoter,
                promoter_pos,
                linked[0],
                control[0],
                ld,
                cd,
                1,
                1,
                0,
            ]
        )
    write_csv(
        stage4 / "matched_pairs.csv",
        pair_rows,
        [
            "edge_id",
            "promoter_id",
            "promoter_pos",
            "linked_interval",
            "control_interval",
            "linked_distance",
            "control_distance",
            "linked_accessible",
            "control_accessible",
            "trimmed",
        ],
    )

    # All-overlap crosswalk: one external peak can map to multiple 5 kb windows.
    overlap_rows = []
    for peak, ps, pe in zip(peak_names, peak_starts, peak_ends):
        for wid, chrom, ws, we in stage4_windows:
            if interval_overlap(int(ps), int(pe), int(ws), int(we)):
                overlap_rows.append([peak, wid, chrom, int(ps), int(pe), int(ws), int(we)])
    write_csv(
        stage4 / "all_overlap_crosswalk.csv",
        overlap_rows,
        ["peak", "interval_id", "chrom", "peak_start", "peak_end", "window_start", "window_end"],
    )
    (stage4 / "decision_contract.json").write_text(
        json.dumps(
            {
                "schema": "V72_STAGE4_SYNTHETIC_INTERFACE_V1",
                "control_construction": "PROMOTER_FIXED_DISTAL_MATCHED_CONTROL",
                "distance_tolerance": "max(10_percent_of_linked_distance,10000_bp)",
                "overlap_policy": "ALL_OVERLAPS",
                "G2": {
                    "status": "OPEN_PROSPECTIVE_SPECIFICATION_REQUIRED",
                    "current_executor_history": "two-sided 95% donor-bootstrap interval contains zero",
                    "numeric_threshold_frozen_here": False,
                    "allowed_diagnostics": [
                        "control_vs_control_delta",
                        "abs_control_vs_control_delta_over_abs_primary_delta",
                    ],
                },
            },
            indent=2,
        )
        + "\n"
    )

    # SCENIC+-like paired multiome with suffix collisions by construction.
    scenic = observable / "SCENICPLUS_LIKE"
    scenic.mkdir()
    scenic_idx = np.arange(144)
    suffixes = np.array([5, 6, 7] * 48)
    scenic_barcodes = np.array(
        [f"NUC{i:05d}-{suffixes[i]}" for i in scenic_idx], dtype="U20"
    )
    scenic_donor = np.array([donors[(i * 5) % n_donors] for i in scenic_idx], dtype="U4")
    np.savez_compressed(
        scenic / "paired_multiome.npz",
        rna=rna[scenic_idx],
        atac=atac[scenic_idx],
        barcodes=scenic_barcodes,
        genes=genes,
        peaks=peak_names,
    )
    write_csv(
        scenic / "metadata.csv",
        [
            [scenic_barcodes[i], scenic_donor[i], "Microglia", f"SUB{i % 3}", "SYNTHETIC_PROTECTED"]
            for i in range(len(scenic_idx))
        ],
        ["barcode", "donor", "cell_type", "subcluster", "Diagnosis"],
    )
    with gzip.open(scenic / "fragments.tsv.gz", "wt", encoding="utf-8") as fh:
        for i, bc in enumerate(scenic_barcodes):
            for j in range(6):
                p = (i * 7 + j * 5) % n_peaks
                start = int(peak_starts[p] + (j * 13) % 100)
                end = min(start + 70, int(peak_ends[p]))
                fh.write(f"chr1\t{start}\t{end}\t{bc}\t1\n")
    (scenic / "route_config.json").write_text(
        json.dumps(
            {
                "schema": "V72_SCENICPLUS_SYNTHETIC_INTERFACE_V1",
                "donor_map_source": "EXPLICIT_METADATA_JOIN",
                "barcode_suffix_is_donor": False,
                "ranking_seed": RANKING_SEED,
                "blas_threads": BLAS_THREADS,
                "union_scoring_reuse": True,
                "rankings_shared_across_routes": False,
                "immutable_script_snapshot_required": True,
                "shard_completion_requires_disk_reread": True,
                "merge_requires_exact_ordered_motif_axis": True,
                "route_A": "submitted peak matrix",
                "route_B": "fragments.tsv.gz→donor-aware pseudobulk→peak-call/consensus adapter",
            },
            indent=2,
        )
        + "\n"
    )

    # Morabito-like separate-nucleus RNA and ATAC. Donors overlap; nuclei do not.
    mora = observable / "MORABITO_LIKE"
    mora.mkdir()
    rna_ids = np.array([f"M_RNA_{i:04d}" for i in range(72)], dtype="U16")
    atac_ids = np.array([f"M_ATAC_{i:04d}" for i in range(84)], dtype="U16")
    np.savez_compressed(
        mora / "rna.npz",
        matrix=rna[:72],
        nuclei=rna_ids,
        donors=np.array([donors[i % n_donors] for i in range(72)], dtype="U4"),
        genes=genes,
    )
    np.savez_compressed(
        mora / "atac.npz",
        matrix=atac[:84],
        nuclei=atac_ids,
        donors=np.array([donors[i % n_donors] for i in range(84)], dtype="U4"),
        peaks=peak_names,
    )
    (mora / "contract.json").write_text(
        json.dumps(
            {
                "schema": "V72_MORABITO_LIKE_INTERFACE_V1",
                "cell_pairing": "FORBIDDEN_SEPARATE_NUCLEI",
                "inference_unit": "DONOR",
            },
            indent=2,
        )
        + "\n"
    )

    # Perturbation-like observations coupled to the same program truth.
    pert = observable / "PERTURBATION_LIKE"
    pert.mkdir()
    n_pert = 96
    guides = np.array([f"G{i % 12:02d}" for i in range(n_pert)], dtype="U8")
    guide_umi = rng.poisson(6, size=(n_pert, 12)).astype(np.int16)
    for i in range(n_pert):
        guide_umi[i, i % 12] += 20
    np.savez_compressed(
        pert / "cell_guide_umi.npz",
        counts=guide_umi,
        cells=np.array([f"P_CELL{i:04d}" for i in range(n_pert)], dtype="U16"),
        guides=np.array([f"G{i:02d}" for i in range(12)], dtype="U8"),
    )
    write_csv(
        pert / "guide_annotation.csv",
        [
            [f"G{i:02d}", str(tfs[i % len(tfs)]), f"PROGRAM_{i % 4}", "NEG" if i >= 10 else "TARGET"]
            for i in range(12)
        ],
        ["guide", "target_tf", "program", "class"],
    )

    # Spatial-like limited panel: deliberately omits PROGRAM_3 genes.
    spatial = observable / "SPATIAL_LIKE"
    spatial.mkdir()
    panel = genes[:20]
    rows = []
    for i in range(80):
        rows.append(
            [
                f"SPOT{i:04d}",
                float(i % 10),
                float(i // 10),
                str(panel[i % len(panel)]),
                int(rna[i, i % len(panel)]),
                f"REGION_{i % 3}",
            ]
        )
    write_csv(
        spatial / "spatial_counts.csv",
        rows,
        ["spot_id", "x", "y", "gene", "count", "region"],
    )
    (spatial / "panel_contract.json").write_text(
        json.dumps(
            {
                "schema": "V72_SPATIAL_LIKE_INTERFACE_V1",
                "limited_panel": True,
                "program_3_not_measured_by_design": True,
                "missing_program_is_not_biological_absence": True,
            },
            indent=2,
        )
        + "\n"
    )

    # Checkpoint twins are real representation/uncertainty outputs, not sentence-only labels.
    checkpoints = observable / "CHECKPOINT_TWIN"
    checkpoints.mkdir()
    per_source_eval = 24
    eval_idx = np.concatenate([
        np.where(source == "SEA_AD")[0][:per_source_eval],
        np.where(source == "NPH52")[0][:per_source_eval],
        np.where(source == "HVS")[0][:per_source_eval],
    ])
    n_eval = len(eval_idx)
    src_code = np.array([
        0.0 if x == "SEA_AD" else 1.0 if x == "NPH52" else 2.0
        for x in source[eval_idx]
    ])
    donor_code = np.array([int(x[1:]) for x in cell_donor[eval_idx]], dtype=float)
    noise = rng.normal(scale=0.05, size=(n_eval, 2))
    healthy = np.c_[z_shared[eval_idx, :2], noise]
    collapsed = np.zeros_like(healthy) + 1e-5
    source_shortcut = np.c_[src_code * 4.0, src_code ** 2, noise]
    donor_shortcut = np.c_[donor_code * 1.5, donor_code ** 2 / 10.0, noise]
    private_leak = np.c_[z_shared[eval_idx, 0], z_shared[eval_idx, 1],
                         z_private[eval_idx, 0] * 3.0, z_private[eval_idx, 1] * 3.0]
    overconfident = healthy.copy()
    corrupt_manifest = healthy.copy()
    checkpoint_ids = np.array([
        "HEALTHY", "COLLAPSED", "SOURCE_SHORTCUT", "DONOR_SHORTCUT",
        "PRIVATE_STATE_LEAK", "OVERCONFIDENT_UNRECOVERABLE", "CORRUPT_MANIFEST"
    ], dtype="U32")
    reps = np.stack([
        healthy, collapsed, source_shortcut, donor_shortcut,
        private_leak, overconfident, corrupt_manifest
    ])
    uncertainty = np.full((len(checkpoint_ids), n_eval), 0.80, dtype=float)
    uncertainty[5, :] = 0.01
    np.savez_compressed(
        checkpoints / "checkpoint_outputs.npz",
        checkpoint_ids=checkpoint_ids,
        representations=reps,
        uncertainty=uncertainty,
        cell_ids=np.array([f"CELL{i:05d}" for i in eval_idx], dtype="U16"),
        eval_global_indices=eval_idx.astype(np.int64),
    )
    checkpoint_manifest = {
        "schema": "V72_CHECKPOINT_TWIN_MANIFEST_V1",
        "checkpoint_ids": checkpoint_ids.tolist(),
        "output_file": "checkpoint_outputs.npz",
        "corrupt_manifest_case": {
            "checkpoint_id": "CORRUPT_MANIFEST",
            "declared_output_sha256": "0" * 64,
            "purpose": "positive control for checkpoint/manifest custody mismatch"
        },
        "blind_gate_targets": {
            "COLLAPSED": "representation variance collapse",
            "SOURCE_SHORTCUT": "source identity recoverable from representation",
            "DONOR_SHORTCUT": "donor identity recoverable from representation",
            "OVERCONFIDENT_UNRECOVERABLE": "near-zero uncertainty despite private state being unavailable"
        },
        "unblinded_only_targets": {
            "PRIVATE_STATE_LEAK": "private latent is linearly recoverable from representation"
        }
    }
    (checkpoints / "checkpoint_manifest.json").write_text(
        json.dumps(checkpoint_manifest, indent=2) + "\n"
    )

    # Observable manifest binds every emitted file after generation.
    manifest = {}
    for p in sorted(observable.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.json":
            manifest[str(p.relative_to(observable))] = {
                "bytes": p.stat().st_size,
                "sha256": sha256(p),
            }
    (observable / "MANIFEST.json").write_text(
        json.dumps(
            {
                "schema": "V72_COUPLED_MULTIDATASET_OBSERVABLE_MANIFEST_V1",
                "seed_label": "HIDDEN_NOT_EXPOSED_TO_PIPELINE",
                "files": manifest,
                "dataset_families": [
                    "FULL104_LIKE",
                    "STAGE4_LIKE",
                    "SCENICPLUS_LIKE",
                    "MORABITO_LIKE",
                    "PERTURBATION_LIKE",
                    "SPATIAL_LIKE",
                    "CHECKPOINT_TWIN",
                ],
            },
            indent=2,
        )
        + "\n"
    )
    return root


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seed", type=int, default=7201)
    ap.add_argument("--n-cells", type=int, default=10000)
    args = ap.parse_args()
    build(Path(args.out), args.seed, args.n_cells)
    print(Path(args.out).resolve())
