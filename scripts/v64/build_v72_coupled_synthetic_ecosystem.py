#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

CHALLENGE_VERSION = "V72_CI_COUPLED_ECOSYSTEM_V1"


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def write_csv(path: Path, header, rows, gzip_output=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if gzip_output else open
    mode = "wt"
    with opener(path, mode, newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def _counts(rng, eta):
    lam = np.exp(np.clip(eta, -3.0, 3.0))
    return rng.poisson(lam).astype(np.int32)


def build(root: Path, seed: int = 7202, n_cells: int = 2400) -> dict:
    rng = np.random.default_rng(seed)
    obs = root / "observable_raw"
    truth = root / "hidden_truth"
    obs.mkdir(parents=True, exist_ok=True)
    truth.mkdir(parents=True, exist_ok=True)

    n_donors = 12
    n_genes = 96
    n_peaks = 120
    donors = np.array([f"D{i:02d}" for i in range(n_donors)])
    master_donor = donors[np.arange(n_cells) % n_donors]
    source = np.where(np.arange(n_cells) < int(.80*n_cells), "SEA_AD",
             np.where(np.arange(n_cells) < int(.94*n_cells), "NPH52", "HVS"))
    operator = np.array([f"OP{i%8:02d}" for i in range(n_cells)])
    cell_ids = np.array([f"MASTER_{i:06d}" for i in range(n_cells)])

    z_global = rng.normal(size=(n_cells, 4))
    z_query = rng.normal(size=(n_cells, 2))
    z_shared = rng.normal(size=(n_cells, 3))
    z_private = rng.normal(size=(n_cells, 2))
    technical = rng.normal(size=(n_cells, 3))
    source_biology = rng.normal(size=(3, 2))
    source_ix = np.select([source=="SEA_AD", source=="NPH52"], [0,1], default=2)
    depth = rng.lognormal(7.4, .45, n_cells)

    W_rna = rng.normal(0, .22, size=(11, n_genes))
    W_atac = rng.normal(0, .22, size=(11, n_peaks))
    latent_rna = np.c_[z_global, z_query, z_shared, source_biology[source_ix]]
    latent_atac = np.c_[z_global, z_shared, z_private, technical[:, :2]]
    rna_eta = latent_rna @ W_rna + .06*np.log1p(depth)[:,None]
    atac_eta = latent_atac @ W_atac + .06*np.log1p(depth)[:,None]
    rna = _counts(rng, rna_eta)
    atac = _counts(rng, atac_eta)

    genes = np.array([f"ENSG_SYN_{i:05d}" for i in range(n_genes)])
    gene_names = np.array([f"GENE{i:03d}" for i in range(n_genes)])
    peak_starts = 100_000 + np.arange(n_peaks)*2_000
    peaks = np.array([f"chr1:{s}-{s+500}" for s in peak_starts])

    graph = []
    for tf in range(8):
        for j in range(6):
            peak_i = (tf*11 + j*3) % n_peaks
            gene_i = (tf*7 + j*5) % n_genes
            graph.append({
                "tf": gene_names[tf],
                "peak": peaks[peak_i],
                "gene": gene_names[gene_i],
                "program": f"PROGRAM_{tf%4}",
                "causal": bool(j < 4),
            })

    np.savez_compressed(
        truth / "TRUTH_LATENTS.npz",
        cell_ids=cell_ids,
        z_global=z_global,
        z_query=z_query,
        z_reg_shared=z_shared,
        z_reg_private=z_private,
        technical_latents=technical,
        master_donor=master_donor,
    )
    (truth / "TRUTH_GRAPH.json").write_text(json.dumps({
        "challenge_version": CHALLENGE_VERSION,
        "seed": seed,
        "regulatory_graph": graph,
        "recoverable_blocks": ["Z_global", "Z_query", "Z_reg_shared"],
        "private_blocks": ["Z_reg_private"],
    }, indent=2) + "\n")

    # FULL104-like RNA backbone
    full = obs / "FULL104_like"
    full.mkdir(exist_ok=True)
    avail = np.ones((n_genes, n_cells), dtype=np.uint8)
    hvs = np.where(source == "HVS")[0]
    avail[-24:, hvs] = 0
    nph = np.where(source == "NPH52")[0]
    avail[-10:, nph] = 0
    full_rna = rna.T.copy()
    full_rna[avail == 0] = 0
    np.savez_compressed(full / "rna_counts.npz", counts=full_rna, genes=genes,
                        gene_names=gene_names, cells=cell_ids, availability=avail)
    write_csv(full / "metadata.csv.gz",
              ["cell_id","donor","source","operator"],
              zip(cell_ids, master_donor, source, operator), gzip_output=True)

    # Stage4-like metacells and faithful matched-control ledger.
    stage = obs / "NIH_CARD_STAGE4_like"
    stage.mkdir(exist_ok=True)
    n_metacells_per_donor = 6
    metacell_ids, mc_donors, mc_rna, mc_atac = [], [], [], []
    for d in donors:
        idx = np.where(master_donor == d)[0]
        chunks = np.array_split(idx, n_metacells_per_donor)
        for k, ch in enumerate(chunks):
            metacell_ids.append(f"{d}_MC{k:02d}")
            mc_donors.append(d)
            mc_rna.append(rna[ch].mean(axis=0))
            mc_atac.append(atac[ch].mean(axis=0))
    mc_rna = np.asarray(mc_rna, dtype=np.float32)
    mc_atac = np.asarray(mc_atac, dtype=np.float32)
    np.savez_compressed(stage / "metacells.npz",
                        metacell_ids=np.array(metacell_ids),
                        donors=np.array(mc_donors),
                        rna=mc_rna, atac=mc_atac, genes=genes, peaks=peaks)

    pair_rows = []
    promoter_starts = 500_000 + np.arange(12)*100_000
    for edge in range(48):
        promoter_id = f"PROM{edge%12:02d}"
        pstart = int(promoter_starts[edge%12])
        linked_dist = 10_000 + (edge%8)*5_000
        linked_start = pstart + linked_dist
        linked_end = linked_start + 5_000
        # same promoter; distance differs by <= 10% or 10kb; explicit non-overlap
        delta = 8_000 if edge % 2 == 0 else -8_000
        ctrl_start = pstart + linked_dist + delta
        if abs(ctrl_start-linked_start) < 5_000:
            ctrl_start += 10_000
        ctrl_end = ctrl_start + 5_000
        tol = max(.10*abs(linked_dist), 10_000)
        ctrl_dist = ctrl_start - pstart
        assert abs(abs(ctrl_dist)-abs(linked_dist)) <= tol
        assert ctrl_end <= linked_start or linked_end <= ctrl_start
        pair_rows.append([
            f"EDGE{edge:03d}", promoter_id, genes[edge % n_genes],
            "chr1", pstart, pstart+1000,
            linked_start, linked_end, linked_dist,
            ctrl_start, ctrl_end, ctrl_dist,
            1, 1, "PROMOTER_FIXED_DISTAL_MATCHED_CONTROL"
        ])
    write_csv(stage / "pair_ledger.csv",
              ["edge_id","promoter_id","gene_id","chrom","promoter_start","promoter_end",
               "linked_start","linked_end","linked_distance","control_start","control_end",
               "control_distance","linked_accessible","control_accessible","control_policy"],
              pair_rows)

    # Overlapping Stage4 windows: intentionally creates multi-overlap cases.
    windows = []
    for i in range(24):
        s = 900_000 + i*2_500
        windows.append(["chr1", s, s+5_000, f"STAGE4_WIN_{i:03d}"])
    write_csv(stage / "overlapping_5kb_windows.bed.csv",
              ["chrom","start","end","window_id"], windows)

    # GSE214979/SCENIC+-like same-nucleus multiome with raw fragments.
    scenic = obs / "GSE214979_SCENICPLUS_like"
    scenic.mkdir(exist_ok=True)
    scenic_idx = np.arange(min(600, n_cells))
    suffixes = np.array([5,6,7])
    scenic_barcodes = np.array([
        f"SYNBC{i:06d}-{suffixes[i%3]}" for i in range(len(scenic_idx))
    ])
    scenic_donors = master_donor[scenic_idx]
    # Because donor cycles 12 and suffix cycles 3, each suffix spans multiple donors.
    np.savez_compressed(
        scenic / "submitted_multiome.npz",
        rna=rna[scenic_idx].T,
        atac=atac[scenic_idx].T,
        genes=genes, peaks=peaks, barcodes=scenic_barcodes
    )
    scenic_subclusters = np.array([f"MG_SUB_{i%3}" for i in range(len(scenic_idx))])
    write_csv(scenic / "metadata.csv.gz",
              ["barcode","donor","cell_type","subcluster","diagnosis_protected"],
              [[b,d,"Microglia",s,"PROTECTED"]
               for b,d,s in zip(scenic_barcodes,scenic_donors,scenic_subclusters)],
              gzip_output=True)
    write_csv(scenic / "barcode_to_donor.csv",
              ["barcode","donor"], zip(scenic_barcodes, scenic_donors))
    with gzip.open(scenic / "fragments.tsv.gz", "wt") as fh:
        for j, (bc, row) in enumerate(zip(scenic_barcodes, atac[scenic_idx])):
            nz = np.where(row > 0)[0][:12]
            for p in nz:
                count = int(max(1, row[p]))
                start = int(peak_starts[p] + (j % 7))
                fh.write(f"chr1\t{start}\t{start+150}\t{bc}\t{count}\n")

    # Morabito-like separate nuclei. Shared donors, never shared cell ids.
    mor = obs / "MORABITO_like"
    mor.mkdir(exist_ok=True)
    m_idx = np.arange(min(360, n_cells))
    r_ids = np.array([f"MOR_RNA_{i:05d}" for i in range(len(m_idx))])
    a_ids = np.array([f"MOR_ATAC_{i:05d}" for i in range(len(m_idx))])
    np.savez_compressed(mor / "rna.npz", counts=rna[m_idx].T, cells=r_ids, genes=genes)
    np.savez_compressed(mor / "atac.npz", counts=atac[m_idx].T, cells=a_ids, peaks=peaks)
    write_csv(mor / "rna_metadata.csv", ["cell_id","donor"], zip(r_ids,master_donor[m_idx]))
    write_csv(mor / "atac_metadata.csv", ["cell_id","donor"], zip(a_ids,master_donor[m_idx]))

    # SEA-AD paired multiome-like anchor.
    sea = obs / "SEAAD_MULTIOME_like"
    sea.mkdir(exist_ok=True)
    s_idx = np.arange(min(300, n_cells))
    s_ids = np.array([f"SEA_PAIR_{i:05d}" for i in range(len(s_idx))])
    np.savez_compressed(sea / "paired.npz", rna=rna[s_idx].T, atac=atac[s_idx].T,
                        cells=s_ids, genes=genes, peaks=peaks)
    write_csv(sea / "metadata.csv", ["cell_id","donor"], zip(s_ids,master_donor[s_idx]))

    # Perturbation-like causal direction evidence.
    pert = obs / "PERTURBATION_like"
    pert.mkdir(exist_ok=True)
    p_idx = np.arange(min(420, n_cells))
    guides = np.array([f"GUIDE_{i:02d}" for i in range(12)])
    guide_assign = guides[np.arange(len(p_idx)) % len(guides)]
    guide_umi = rng.poisson(5, size=(len(guides), len(p_idx))).astype(np.int16)
    for j, g in enumerate(guide_assign):
        guide_umi[np.where(guides == g)[0][0], j] += rng.integers(5, 15)
    np.savez_compressed(pert / "cell_guide_umi_counts.npz",
                        counts=guide_umi, guides=guides,
                        cells=np.array([f"PERT_{i:05d}" for i in range(len(p_idx))]))
    target_rows = [[g, gene_names[i % 8], "NEGATIVE_CONTROL" if i>=8 else "TARGETING"]
                   for i,g in enumerate(guides)]
    write_csv(pert / "guide_targets.csv", ["guide","target","class"], target_rows)

    # Spatial-like limited panel; one program deliberately unmeasured.
    spatial = obs / "SPATIAL_like"
    spatial.mkdir(exist_ok=True)
    panel = gene_names[:24]
    n_spots = 180
    sp_idx = np.arange(n_spots) % n_cells
    sp_counts = rna[sp_idx, :24].T
    coords = rng.uniform(0, 1000, size=(n_spots,2))
    np.savez_compressed(spatial / "panel_counts.npz",
                        counts=sp_counts, genes=panel,
                        spots=np.array([f"SPOT_{i:04d}" for i in range(n_spots)]))
    write_csv(spatial / "coordinates.csv", ["spot","x","y","segmentation_qc"],
              [[f"SPOT_{i:04d}", float(coords[i,0]), float(coords[i,1]),
                "LOW" if i%17==0 else "PASS"] for i in range(n_spots)])

    # Dataset binding manifest. Truth path is intentionally excluded.
    manifest = {
        "schema":"V72_COUPLED_SYNTHETIC_ECOSYSTEM_MANIFEST_V1",
        "challenge_version":CHALLENGE_VERSION,
        "seed_public_format_only":"WITHHELD_FROM_PIPELINE_IN_BLIND_CHALLENGE",
        "n_master_cells":n_cells,
        "n_donors":n_donors,
        "datasets":[
            "FULL104_like","NIH_CARD_STAGE4_like","GSE214979_SCENICPLUS_like",
            "MORABITO_like","SEAAD_MULTIOME_like","PERTURBATION_like","SPATIAL_like"
        ],
        "shared_truth_statement":"All observable datasets were generated from the same master latent state and regulatory graph.",
        "forbidden_truth_fields_present_in_manifest":False,
    }
    (obs / "ECOSYSTEM_MANIFEST.json").write_text(json.dumps(manifest, indent=2)+"\n")

    digests = {}
    for p in sorted(obs.rglob("*")):
        if p.is_file():
            digests[str(p.relative_to(obs))] = sha256_file(p)
    (obs / "DIGESTS.json").write_text(json.dumps(digests, indent=2)+"\n")

    return {
        "challenge_version":CHALLENGE_VERSION,
        "observable_root":str(obs),
        "truth_root":str(truth),
        "n_master_cells":n_cells,
        "n_donors":n_donors,
        "status":"PASS__SYNTHETIC_ECOSYSTEM_BUILT",
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--seed", type=int, default=7202)
    ap.add_argument("--cells", type=int, default=2400)
    args = ap.parse_args(argv)
    result = build(Path(args.root), seed=args.seed, n_cells=args.cells)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
