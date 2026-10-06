#!/usr/bin/env python3
"""V77 full-scale paired multiome ATAC observer: 40,000 cis-placed regions, same cells as RNA.

WHY THIS EXISTS. The 41,238-address worlds were RNA-only. That made World D vacuous -- D1
directed regulator->region->gene recovery and D2, the mandatory repair separating biological
from technical ATAC-private variation, had no observable layer at all. It also falsified two
documented B-component mechanisms (defect S126):

  * B3's non-recoverable rare arms were specified as "routed to the ATAC-only modality".
    With no ATAC they hit `continue` and were emitted NOWHERE, so they were inert rather
    than relocated.
  * B6's ladder was specified as grading "RNA-versus-ATAC modality share". With no ATAC only
    the f fraction existed; the 1-f remainder went nowhere, so rung 0 carried no signal in
    any modality and was a degenerate rung.

This observer emits the missing half, so both mechanisms become true as written and World D
becomes measurable.

PAIRING. Cells are the SAME global cells the RNA observer sees, by construction: both read
the same truth shards and key every draw on global_cell_index.

D2 SEPARATION, which is the repair the project requires before any cross-modal biological
claim:

  biological ATAC-private  (z_atac_bio)  -> SPARSE loadings concentrated on TF-BOUND regions,
                                            and statistically linked to those TFs' target
                                            genes, so it has cis structure
  technical  ATAC-private  (z_atac_tech) -> DENSE, near-uniform across ALL regions, and
                                            correlated with ATAC depth, with no cis structure

In World A these two were structurally identical (both 0.000 from RNA, both ~0.85 from ATAC).
Here they differ in loading sparsity, in cis-distance structure, and in depth correlation,
so a method can be asked to tell them apart and can fail.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "v64"))
sys.path.insert(0, str(HERE))
import build_v73_sharded_master_truth as T
import v77_regulatory_graph as RG
import v77_address_universe as AU
import v77_genomic_layout as GL

N_REGIONS = 40_000
N_ADDR = AU.N_ADDRESSES
CELL_CHUNK = 2500          # sub-batch so peak memory stays near 0.4 GB per chunk

# realistic scATAC geometry: a few thousand accessible regions per cell, near-binary counts
ACCESSIBLE_FRAC = (0.08, 0.28)      # per-cell fraction of regions with a fragment
MAX_COUNT = 6

SC = dict(shared=0.55, reg_private=1.15, atac_bio=1.30, atac_tech=0.75,
          tf=1.05, rare_hidden=2.30, partial_hidden=1.45, decoy=0.85)
MOD = dict(rare_hidden=120, partial_hidden=260, atac_bio=900, atac_tech=N_REGIONS)


def sha256_file(p: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


class RegionAllocator:
    """Disjoint region blocks, mirroring the address allocator used on the RNA side."""

    def __init__(self, seed: int, n: int = N_REGIONS):
        self._pool = np.argsort(T.u01(seed + 9600, np.arange(n, dtype=np.uint64), 9600),
                                kind="stable")
        self._cur = 0
        self.assigned: dict[str, list[int]] = {}

    def take(self, name: str, k: int) -> np.ndarray:
        if name in self.assigned:
            return np.asarray(self.assigned[name])
        sel = np.sort(self._pool[self._cur:self._cur + k])
        self._cur += k
        self.assigned[name] = sel.tolist()
        return sel

    @property
    def used(self) -> int:
        return self._cur


def _signed(seed, idx, stream, scale):
    s = T.normal(seed + stream, np.asarray(idx, dtype=np.uint64), stream)
    return np.sign(s).astype(np.float32) * np.float32(scale)


def build_graph_regions(graph, layout, alloc, seed):
    """Map the planted TF regulons onto CIS-PLACED regions, with nearby decoys.

    A TF's bound regions are drawn from the cis windows of its target genes, so a real edge
    is genuinely local to its target. Decoys are drawn from the SAME windows, so a method
    cannot separate them by distance alone -- which is the point.
    """
    tf_regions, tf_decoys = {}, {}
    for e in graph["tf"]:
        t = e["tf"]
        targets = np.asarray(e["target_panel_genes"], dtype=np.int64)
        targets = targets[targets < N_ADDR]
        cand = layout.cis_candidates(targets)
        pool = np.unique(np.concatenate([c for c in cand if len(c)])) if any(
            len(c) for c in cand) else np.array([], dtype=np.int64)
        if len(pool) < 8:
            pool = alloc.take(f"TF{t}_fallback", 24)
        sc = T.u01(seed + 9700 + t, pool.astype(np.uint64), 9700 + t)
        order = np.argsort(sc, kind="stable")
        tf_regions[t] = pool[order[:12]]
        tf_decoys[t] = pool[order[12:24]] if len(pool) >= 24 else np.array([], dtype=np.int64)
    return tf_regions, tf_decoys


def observe(root: Path, seed: int, mseed: int | None,
            out_name="FULLSCALE_V2_MULTIOME_ATAC_sharded") -> dict:
    truth_root = root / "hidden_truth"
    obs = root / "observable_raw" / out_name
    obs.mkdir(parents=True, exist_ok=True)
    tm = json.loads((truth_root / "TRUTH_MANIFEST.json").read_text())
    mseed = int(seed if mseed is None else mseed)
    enabled = set(tm["enabled_components"])
    layout = GL.GenomicLayout(seed, N_ADDR, N_REGIONS)
    alloc = RegionAllocator(seed)
    graph = RG.build_graph(seed) if ({"D1", "D3", "E2"} & enabled) else None
    tf_regions, tf_decoys = (build_graph_regions(graph, layout, alloc, seed)
                             if graph else ({}, {}))

    from build_v77_extended_rna_observer import apply_perturbation_to_tf
    rid = np.arange(N_REGIONS, dtype=np.uint64)
    shards, total, dens = [], 0, []

    for s in tm["shards"]:
        tp = truth_root / s["file"]
        if sha256_file(tp) != s["sha256"]:
            raise RuntimeError("truth shard digest mismatch: " + s["file"])
        zf = np.load(tp, allow_pickle=False)
        z = {k: zf[k] for k in zf.files}
        apply_perturbation_to_tf(z, enabled)
        ids_all = z["global_cell_index"].astype(np.int64)
        idx_parts, val_parts, ptr = [], [], [0]

        for c0 in range(0, len(ids_all), CELL_CHUNK):
            c1 = min(c0 + CELL_CHUNK, len(ids_all))
            n = c1 - c0
            ids = ids_all[c0:c1]
            eta = np.zeros((n, N_REGIONS), dtype=np.float32)

            # shared biology: the 7 dims RNA and ATAC have in common
            lat = np.c_[z["z_global"][c0:c1], z["z_reg_shared"][c0:c1]].astype(np.float32)
            W = np.stack([T.normal(seed + 9500, rid, 9500 + j) for j in range(lat.shape[1])],
                         axis=0).astype(np.float32) * np.float32(SC["shared"] * 0.3)
            eta += lat @ W

            # regulatory-private: ATAC-only, as in World A but now with cis structure
            zp = z["z_reg_private"][c0:c1].astype(np.float32)
            for j in range(zp.shape[1]):
                g = alloc.take(f"reg_private{j}", 700)
                v = np.zeros(N_REGIONS, dtype=np.float32)
                v[g] = _signed(seed, g, 9710 + j, SC["reg_private"])
                eta += zp[:, j][:, None] * v[None, :]

            # ---- S126 REPAIR: the fractions that previously went nowhere now land here ----
            if "B3" in enabled:
                from build_v77_extended_truth import RARE_RECOVERABLE
                for j, rec in enumerate(RARE_RECOVERABLE):
                    if rec:
                        continue                       # recoverable arms live in RNA
                    g = alloc.take(f"B3_rare_hidden{j}", MOD["rare_hidden"])
                    v = np.zeros(N_REGIONS, dtype=np.float32)
                    v[g] = _signed(seed, g, 9720 + j, SC["rare_hidden"])
                    eta += z["rare_flags"][c0:c1, j].astype(np.float32)[:, None] * v[None, :]
            if "B6" in enabled:
                K = z["z_partial"].shape[1]
                for j, f in enumerate(np.linspace(0.0, 1.0, K)):
                    if f >= 1.0:
                        continue                       # rung K-1 is fully in RNA
                    g = alloc.take(f"B6_rung_hidden{j}", MOD["partial_hidden"])
                    v = np.zeros(N_REGIONS, dtype=np.float32)
                    v[g] = _signed(seed, g, 9740 + j, SC["partial_hidden"])
                    eta += ((1.0 - f) * z["z_partial"][c0:c1, j].astype(np.float32))[:, None] * v[None, :]

            # ---- D2 REPAIR: distinguishable ATAC-private signatures ----
            if "D2" in enabled:
                # biological: SPARSE, concentrated on TF-bound regions, so it has cis structure
                bio_regions = (np.unique(np.concatenate(list(tf_regions.values())))
                               if tf_regions else alloc.take("atac_bio_fallback", MOD["atac_bio"]))
                v = np.zeros(N_REGIONS, dtype=np.float32)
                v[bio_regions] = _signed(seed, bio_regions, 9760, SC["atac_bio"])
                eta += z["z_atac_bio"][c0:c1].astype(np.float32)[:, None] * v[None, :]
                # technical: DENSE and near-uniform across every region, no cis structure
                vt = (np.float32(SC["atac_tech"])
                      * (1.0 + 0.08 * T.normal(seed + 9770, rid, 9770)).astype(np.float32))
                eta += z["z_atac_tech"][c0:c1].astype(np.float32)[:, None] * vt[None, :]

            # ---- D1: TF activity opens its bound regions; decoys co-vary but regulate nothing ----
            if graph is not None and "z_tf" in z:
                ztf = z.get("_z_tf_effective", z["z_tf"])[c0:c1].astype(np.float32)
                for t, regs in tf_regions.items():
                    v = np.zeros(N_REGIONS, dtype=np.float32)
                    v[regs] = _signed(seed, regs, 9780 + t, SC["tf"])
                    dec = tf_decoys.get(t, np.array([], dtype=np.int64))
                    if len(dec):
                        v[dec] = _signed(seed, dec, 9790 + t, SC["decoy"])
                    eta += ztf[:, t][:, None] * v[None, :]

            np.clip(eta, -6, 6, out=eta)
            rel = np.exp(eta, dtype=np.float32)

            lo, hi = ACCESSIBLE_FRAC
            frac = lo + (hi - lo) * T.u01(mseed + 9800, np.asarray(ids, dtype=np.uint64), 9800)
            k_per_cell = np.maximum(1, (frac * N_REGIONS).astype(np.int64))
            for i in range(n):
                k = int(k_per_cell[i])
                u = T.u01(mseed + 9810,
                          np.uint64(ids[i]) * np.uint64(2654435761) + rid, 9810)
                score = np.log(np.maximum(rel[i], 1e-30)) - np.log(-np.log(np.clip(u, 1e-12, 1 - 1e-12)))
                top = np.argpartition(score, -k)[-k:]
                top = top[np.argsort(top)]
                uu = T.u01(mseed + 9820,
                           np.uint64(ids[i]) * np.uint64(40503) + top.astype(np.uint64), 9820)
                cnt = 1 + (uu * np.minimum(rel[i, top] / (rel[i, top].mean() + 1e-9), MAX_COUNT - 1)).astype(np.int32)
                idx_parts.append(top.astype(np.int32)); val_parts.append(cnt.astype(np.int32))
                ptr.append(ptr[-1] + k)
            dens.append(float(k_per_cell.mean() / N_REGIONS))
            del eta, rel

        start, stop = int(ids_all[0]), int(ids_all[-1]) + 1
        p = obs / f"ATAC_SPARSE_{start:09d}_{stop:09d}.npz"
        np.savez_compressed(p, indices=np.concatenate(idx_parts),
                            data=np.concatenate(val_parts),
                            indptr=np.asarray(ptr, dtype=np.int64),
                            n_regions=np.int64(N_REGIONS),
                            global_cell_index=ids_all, cell_id=z["cell_id"],
                            region_chrom=layout.region_chrom, region_start=layout.region_start,
                            region_end=layout.region_end)
        shards.append(dict(start=start, stop=stop, cells=len(ids_all), file=p.name,
                           sha256=sha256_file(p), nnz=int(ptr[-1])))
        total += len(ids_all)

    manifest = dict(
        schema="V77_FULLSCALE_MULTIOME_ATAC_OBSERVER_MANIFEST_V1",
        seed=seed, truth_seed=seed, measurement_seed=mseed, n_cells=total,
        n_regions=N_REGIONS, n_addresses=N_ADDR,
        paired_same_cell_identity=True,
        pairing_mechanism="both observers read the same truth shards and key every draw on global_cell_index",
        enabled_components=sorted(enabled),
        mean_accessible_fraction=float(np.mean(dens)),
        genomic_layout=layout.summary(),
        S126_REPAIR=dict(
            defect="B3 non-recoverable arms and the B6 1-f remainder were emitted nowhere at 41K",
            repair="both are now emitted into ATAC-only region modules, as originally specified",
            b3_hidden_arms=[k for k in alloc.assigned if k.startswith("B3_rare_hidden")],
            b6_hidden_rungs=[k for k in alloc.assigned if k.startswith("B6_rung_hidden")]),
        D2_SEPARATION=dict(
            biological="z_atac_bio: SPARSE, concentrated on TF-bound regions, carries cis structure",
            technical="z_atac_tech: DENSE and near-uniform over all regions, no cis structure",
            why="in World A both were structurally identical; a method can now be asked to separate them"),
        regulatory_graph_used=graph is not None,
        tf_bound_regions={str(t): list(map(int, r)) for t, r in tf_regions.items()},
        tf_decoy_regions={str(t): list(map(int, r)) for t, r in tf_decoys.items()},
        region_modules=alloc.assigned,
        regions_used=alloc.used,
        effect_scales=SC,
        identity_caveat=("synthetic coordinates and synthetic region identities; no claim is made "
                         "about the real locus of any named gene"),
        master_truth_digest_binding=[dict(file=x["file"], sha256=x["sha256"]) for x in tm["shards"]],
        shards=shards)
    (obs / "FULLSCALE_MULTIOME_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--seed", type=int, default=7302)
    ap.add_argument("--measurement-seed", type=int, default=None)
    a = ap.parse_args()
    m = observe(Path(a.root), a.seed, a.measurement_seed)
    print(json.dumps(dict(status="PASS", cells=m["n_cells"], regions=m["n_regions"],
                          mean_accessible_fraction=round(m["mean_accessible_fraction"], 4),
                          regions_used_by_modules=m["regions_used"],
                          tf_with_bound_regions=len(m["tf_bound_regions"])), indent=2))


if __name__ == "__main__":
    main()
