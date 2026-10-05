#!/usr/bin/env python3
"""V77 full-scale RNA observer v2: canonical identities + registry-derived background.

WHAT CHANGED FROM v1 AND WHY
----------------------------
v1 moved to 41,238 addresses, which fixed module collision. An audit of v1's background then
showed it was, in the reviewer's phrase, a 96-gene simulator wearing a 41K coat:

  abundance max/median        9.56x        (real transcriptomes: 100-10000x)
  counts in the top 1%        4.9%         (real: typically 20-50%)
  module pairwise overlap     0            (strict disjointness: no pathway redundancy)
  addresses with structure    14.4%        (the other 85.6% carried a 3-dim field only)

v2 fixes all four, and takes every structural prior from the FROZEN REGISTRY rather than
inventing it:

* abundance and detectability are conditioned on `biotype` (45.8% protein_coding, 15.0%
  lincRNA, ...) and on `contributing_source_feature_count`;
* structural unmeasurement is now REAL and source-dependent: HVS measured 45.4% of addresses,
  NPH52 86.2%, SEA-AD 86.8%, with 17,569 addresses common to all three and 9,990 unique to
  one. A program living on HVS-only addresses is genuinely invisible to SEA-AD cells;
* 60 sparse background covariance programs span the whole space, so broad covariance is not
  a free win for a model that learns correlation instead of biology;
* modules are organised into FAMILIES with controlled partial overlap, restoring pathway
  redundancy and partially-redundant substitutes.

IDENTITY BOUNDARY. Addresses use the registry's order and real identifiers so the vocabulary
matches the production tokenizer. Modules are allocated by seeded permutation with no
knowledge of gene symbols, so synthetic signal at a real gene identity asserts nothing about
that gene. This is not the blocked 96-feature-to-canonical-address projection.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "v64"))
sys.path.insert(0, str(HERE))
import build_v73_sharded_master_truth as T
import v73_full104_qc_calibration as Q
import v77_regulatory_graph as RG
import v77_address_universe as AU

N = AU.N_ADDRESSES

# module sizes as a fraction of a 41,238-address space: a 400-address program is ~1%
MOD = dict(state=400, donor=300, rare=60, transient=150, marker=30, partial=180,
           interact=150, local=220, niche=150, pert=180, tf_target=220)
SC = dict(state=0.95, donor=0.80, rare=2.40, transient=1.30, marker=2.20, partial=1.60,
          interact=1.60, gain=1.00, niche=1.10, pert_direct=1.70, tf=1.10, background=0.55)
N_BACKGROUND_PROGRAMS = 60
BACKGROUND_GENES_PER = 600
REDUNDANT_OVERLAP = 0.45     # declared pathway-redundancy fraction within a module family


def sha256_file(p: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def _ncdf(x):
    x = np.asarray(x, dtype=np.float64); ax = np.abs(x)
    t = 1.0 / (1.0 + 0.2316419 * ax)
    poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    tail = np.exp(-0.5 * ax * ax) / np.sqrt(2 * np.pi) * poly
    return np.where(x >= 0, 1.0 - tail, tail)


def structural_support(uni, source_ix, op_index, qc, operator_ids, seed):
    """Support = the cohort really measured the address AND this operator retained it.

    The first factor is a registry fact. The second is the operator-level attrition already
    modelled in World A, applied within what the cohort measured.
    """
    sup = uni.source_support[np.asarray(source_ix, dtype=np.int64)].copy()   # (cells, N) bool
    aid = np.arange(N, dtype=np.uint64)
    for op in np.unique(op_index):
        row = qc[operator_ids[int(op)]]
        frac_keep = 1.0 - float(row["structural_missing_fraction"]) \
                        - float(row.get("collision_unresolved_fraction", 0.0))
        frac_keep = float(np.clip(frac_keep, 0.05, 1.0))
        s = T.u01(seed + 811, aid, 1100 + int(op))
        drop = s > frac_keep
        rows = np.where(op_index == op)[0]
        sup[np.ix_(rows, np.where(drop)[0])] = False
    return sup


def depth_targets(ids, op, sup, qc, operator_ids, qprobs, mseed):
    ids_u = np.asarray(ids, dtype=np.uint64)
    zd = T.normal(mseed + 701, ids_u, 951); zi = T.normal(mseed + 704, ids_u, 954)
    ud = _ncdf(zd)
    n = len(ids); lib = np.empty(n); det = np.empty(n)
    navail = sup.sum(1).astype(np.float64)
    for oi in np.unique(op):
        ix = np.where(op == oi)[0]; row = qc[operator_ids[int(oi)]]
        rho = float(np.clip(float(row.get("log1p_library_vs_detected_pearson", 0.0) or 0.0), -.98, .98))
        zs = rho * zd[ix] + np.sqrt(max(0.0, 1 - rho * rho)) * zi[ix]
        lib[ix] = Q.interp_quantiles(ud[ix], qprobs, row["rna_library_size_quantiles"])
        det[ix] = Q.interp_quantiles(_ncdf(zs), qprobs, row["rna_detected_feature_quantiles"])
    det = np.clip(np.rint(det), 1, np.maximum(navail, 1)).astype(np.int64)
    lib = np.maximum(np.rint(lib).astype(np.int64), det)
    return lib, det


def sparse_counts(rel, sup, ids, lib, det, mseed):
    n = len(ids)
    indptr = np.zeros(n + 1, dtype=np.int64)
    idx_all, val_all = [], []
    aid = np.arange(N, dtype=np.uint64)
    for i in range(n):
        k = int(det[i])
        score = np.where(sup[i], np.log(np.maximum(rel[i], 1e-30)), -np.inf)
        u = T.u01(mseed + 510, np.uint64(ids[i]) * np.uint64(1315423911) + aid, 902)
        score = score + 0.35 * (-np.log(-np.log(np.clip(u, 1e-12, 1 - 1e-12))))
        top = np.argpartition(score, -k)[-k:]
        top = top[np.argsort(top)]
        w = np.maximum(rel[i, top], 1e-30); w = w / w.sum()
        remaining = int(lib[i]) - k
        base = np.floor(w * remaining).astype(np.int64)
        resid = remaining - int(base.sum())
        if resid > 0:
            base[np.argsort(-(w * remaining - base))[:resid]] += 1
        idx_all.append(top.astype(np.int32)); val_all.append((base + 1).astype(np.int32))
        indptr[i + 1] = indptr[i] + k
    return np.concatenate(idx_all), np.concatenate(val_all), indptr


def build_eta(z, enabled, seed, uni, alloc, bg, n, suppress=frozenset()):
    """eta = registry abundance + background covariance + World A base + planted components."""
    present = set(enabled) | set(suppress)   # allocate for every planted component
    eta = np.tile(uni.log_abundance.astype(np.float32), (n, 1))     # heavy-tailed abundance

    # background correlated programs: the 'correlated substitutes' a model can exploit
    brow, bcol, bval, n_prog = bg
    aidu = np.arange(n, dtype=np.uint64)
    Zb = np.stack([T.normal(seed + 8100 + p, aidu + np.uint64(z["global_cell_index"][0]), 8100 + p)
                   for p in range(n_prog)], axis=1).astype(np.float32)
    Wb = np.zeros((n_prog, N), dtype=np.float32)
    Wb[brow, bcol] = bval
    eta += SC["background"] * (Zb @ Wb)

    lat = np.c_[z["z_global"], z["z_query"], z["z_reg_shared"]].astype(np.float32)
    aid = np.arange(N, dtype=np.uint64)
    W = np.stack([T.normal(seed + 100, aid, 200 + j) for j in range(lat.shape[1])],
                 axis=0).astype(np.float32) * np.float32(0.22)
    eta += lat @ W

    def vec(name, k, stream, scale, family=None, parent=None, gate=1.0):
        # the module is ALLOCATED even when gated to zero, so a suppressed off-twin has the
        # identical planted design and identical module_address_sets. Only the EFFECT is removed.
        g = (alloc.take_redundant(family, name, k, REDUNDANT_OVERLAP, parent)
             if family else alloc.take(name, k))
        scale = scale * gate
        v = np.zeros(N, dtype=np.float32)
        s = T.normal(seed + stream, np.asarray(g, dtype=np.uint64), stream)
        v[g] = np.sign(s).astype(np.float32) * np.float32(scale)
        return v

    if "B1" in present:
        # states form a FAMILY with partial overlap: adjacent states share a pathway
        prev = None
        for k in range(6):
            nm = f"B1_state{k}"
            eta += (z["state_index"] == k).astype(np.float32)[:, None] * \
                   vec(nm, MOD["state"], 9200 + k, SC["state"], gate=(0.0 if "B1" in suppress else 1.0), family="B1_states", parent=prev)[None, :]
            prev = nm
    if "B2" in present:
        for j in range(z["z_donor"].shape[1]):
            eta += z["z_donor"][:, j].astype(np.float32)[:, None] * \
                   vec(f"B2_donor{j}", MOD["donor"], 9300 + j, SC["donor"], gate=(0.0 if "B2" in suppress else 1.0))[None, :]
    if "B3" in present:
        from build_v77_extended_truth import RARE_RECOVERABLE
        for j, rec in enumerate(RARE_RECOVERABLE):
            if not rec:
                continue
            eta += z["rare_flags"][:, j].astype(np.float32)[:, None] * \
                   vec(f"B3_rare{j}", MOD["rare"], 9400 + j, SC["rare"], gate=(0.0 if "B3" in suppress else 1.0))[None, :]
    if "B4" in present:
        band = np.exp(-((z["pseudotime"].astype(np.float32) - .5) / .15) ** 2)
        eta += band[:, None] * vec("B4_transient", MOD["transient"], 9500, SC["transient"], gate=(0.0 if "B4" in suppress else 1.0))[None, :]
    if "B5" in present:
        for j in range(z["z_marker"].shape[1]):
            eta += z["z_marker"][:, j].astype(np.float32)[:, None] * \
                   vec(f"B5_marker{j}", MOD["marker"], 9600 + j, SC["marker"], gate=(0.0 if "B5" in suppress else 1.0))[None, :]
    if "B6" in present:
        K = z["z_partial"].shape[1]
        for j, f in enumerate(np.linspace(0.0, 1.0, K)):
            eta += (f * z["z_partial"][:, j].astype(np.float32))[:, None] * \
                   vec(f"B6_rung{j}", MOD["partial"], 9700 + j, SC["partial"], gate=(0.0 if "B6" in suppress else 1.0))[None, :]
    if "C1" in present:
        A = z["c_state_a"].astype(np.float32); B = z["c_state_b"].astype(np.float32)
        eta += A[:, None] * vec("C1_A", MOD["interact"], 9800, SC["interact"], gate=(0.0 if "C1" in suppress else 1.0))[None, :]
        eta += B[:, None] * vec("C1_B", MOD["interact"], 9801, SC["interact"], gate=(0.0 if "C1" in suppress else 1.0))[None, :]
        eta += (A * B)[:, None] * vec("C1_AB", MOD["interact"], 9802, SC["interact"], gate=(0.0 if "C1" in suppress else 1.0))[None, :]
    if "C2" in present:
        base = vec("C2_local", MOD["local"], 9900, 1.0, gate=(0.0 if "C2" in suppress else 1.0))
        drive = z["z_global"][:, 0].astype(np.float32)
        gain = (1.0 + SC["gain"] * np.tanh(z["z_gain"].astype(np.float32))).astype(np.float32)
        eta += (drive * gain)[:, None] * base[None, :]
    if "D1" in present:
        ztf = z.get("_z_tf_effective", z["z_tf"]).astype(np.float32)
        prev = None
        for t in range(ztf.shape[1]):
            nm = f"D1_tf{t}"
            eta += ztf[:, t][:, None] * vec(nm, MOD["tf_target"], 9950 + t, SC["tf"] * (0.0 if "D1" in suppress else 1.0),
                                            family="D1_regulons", parent=prev)[None, :]
            prev = nm
    if "E1" in present:
        eta += z["niche_score"].astype(np.float32)[:, None] * \
               vec("E1_niche", MOD["niche"], 9990, SC["niche"], gate=(0.0 if "E1" in suppress else 1.0))[None, :]
    if "E2" in present:
        d = (z["pert_id"] == 3).astype(np.float32) * z["pert_dose"].astype(np.float32)
        eta += d[:, None] * vec("E2_direct", MOD["pert"], 9995, SC["pert_direct"], gate=(0.0 if "E2" in suppress else 1.0))[None, :]
    return eta


def observe(root: Path, seed: int, mseed: int | None,
            out_name="FULLSCALE_V2_CANONICAL_sharded", suppress: set[str] | None = None) -> dict:
    """`suppress` removes components from the OBSERVATION while the truth keeps their latents.

    This is what makes an off-twin a real control: the statistic can still be computed, and
    must return approximately zero. Removing the component from the TRUTH instead would mean
    the statistic is never evaluated, which is a check that cannot fail."""
    truth_root = root / "hidden_truth"
    obs = root / "observable_raw" / out_name
    obs.mkdir(parents=True, exist_ok=True)
    tm = json.loads((truth_root / "TRUTH_MANIFEST.json").read_text())
    mseed = int(seed if mseed is None else mseed)
    truth_components = set(tm["enabled_components"])
    suppress = set(suppress or ())
    enabled = truth_components - suppress
    qmeta, qc = Q.by_operator()
    qprobs = np.array(qmeta["quantile_probabilities"], dtype=float)
    operator_ids = tm["operator_ids"]
    uni = AU.AddressUniverse(seed)
    alloc = uni.module_allocator()
    bg = uni.background_programs(N_BACKGROUND_PROGRAMS, BACKGROUND_GENES_PER)
    from build_v77_extended_rna_observer import apply_perturbation_to_tf

    shards, total, dens = [], 0, []
    for s in tm["shards"]:
        tp = truth_root / s["file"]
        if sha256_file(tp) != s["sha256"]:
            raise RuntimeError("truth shard digest mismatch: " + s["file"])
        zf = np.load(tp, allow_pickle=False)
        z = {k: zf[k] for k in zf.files}
        ids = z["global_cell_index"].astype(np.int64)
        op = z["operator_index"].astype(np.int16)
        src = z["source_index"].astype(np.int64)
        apply_perturbation_to_tf(z, enabled)
        eta = build_eta(z, enabled, seed, uni, alloc, bg, len(ids), suppress=suppress)
        np.clip(eta, -8, 8, out=eta)
        rel = np.exp(eta, dtype=np.float32)
        sup = structural_support(uni, src, op, qc, operator_ids, seed)
        # gene-specific detectability modulates preference within what is supported
        rel *= (1.0 / (1.0 + np.exp(-uni.logit_detect)))[None, :]
        rel *= sup
        lib, det = depth_targets(ids, op, sup, qc, operator_ids, qprobs, mseed)
        if "C3" in truth_components and "C3" not in suppress:
            # BIOLOGY x MEASUREMENT-OPERATOR coupling. Measurement quality depends partly on
            # biological state: cells with high z_bioqc yield fewer detected features and a
            # smaller library. This deliberately breaks the independence World A assumes and
            # measures at |corr| <= 0.009.
            #
            # This was present in the 96-feature observer and was LOST when the full-scale
            # observer was written, leaving z_bioqc consumed by nothing -- the same inert-latent
            # defect recorded against technical_latents[1:2] in the Phase 2 inventory.
            q = np.tanh(z["z_bioqc"].astype(np.float64))
            keep = 1.0 - 0.30 * (q + 1.0) / 2.0          # 1.00 .. 0.70
            det = np.clip(np.rint(det * keep), 1, np.maximum(sup.sum(1), 1)).astype(np.int64)
            lib = np.maximum(np.rint(lib * keep).astype(np.int64), det)
        idx, val, indptr = sparse_counts(rel, sup, ids, lib, det, mseed)
        dens.append(float(det.mean() / N))
        start, stop = int(ids[0]), int(ids[-1]) + 1
        p = obs / f"RNA_SPARSE_{start:09d}_{stop:09d}.npz"
        np.savez_compressed(p, indices=idx, data=val, indptr=indptr,
                            n_addresses=np.int64(N), global_cell_index=ids, cell_id=z["cell_id"],
                            support_count=sup.sum(1).astype(np.int32),
                            library_target=lib.astype(np.int64), detected_target=det.astype(np.int64))
        shards.append(dict(start=start, stop=stop, cells=len(ids), file=p.name,
                           sha256=sha256_file(p), nnz=int(len(idx))))
        total += len(ids)

    fam_overlap = {}
    for fam, members in alloc.families.items():
        sets = [set(alloc.assigned[m]) for m in members]
        pairs = [(len(a & b) / max(len(a), 1)) for i, a in enumerate(sets) for b in sets[i + 1:]]
        fam_overlap[fam] = dict(members=members,
                                mean_pairwise_overlap_fraction=float(np.mean(pairs)) if pairs else 0.0)

    manifest = dict(
        schema="V77_FULLSCALE_CANONICAL_RNA_OBSERVER_MANIFEST_V2",
        seed=seed, truth_seed=seed, measurement_seed=mseed, n_cells=total, n_addresses=N,
        enabled_components=sorted(enabled),
        truth_components=sorted(truth_components),
        suppressed_from_observation=sorted(suppress),
        address_universe=uni.summary(),
        vocabulary=dict(uses_canonical_registry_order=True,
                        tokenizer_compatible=True,
                        example_addresses=uni.address_id[:5].tolist(),
                        example_symbols=uni.symbol[:5].tolist(),
                        identity_caveat=("planted biology is allocated by seeded permutation with no "
                                         "knowledge of gene symbols. Synthetic signal at a real gene "
                                         "identity asserts NOTHING about that gene and must never be "
                                         "read as a biological finding about it.")),
        background=dict(n_programs=N_BACKGROUND_PROGRAMS, genes_per_program=BACKGROUND_GENES_PER,
                        purpose=("correlated substitutes spanning the whole space, so broad covariance "
                                 "is not a free win; these carry no truth label")),
        pathway_redundancy=dict(declared_overlap_fraction=REDUNDANT_OVERLAP, families=fam_overlap),
        modules=dict(n=len(alloc.assigned), addresses_used=alloc.used,
                     fraction_of_space=alloc.used / N, sizes={k: len(v) for k, v in alloc.assigned.items()}),
        module_address_sets=alloc.assigned,
        mean_detected_fraction=float(np.mean(dens)),
        effect_scales=SC, module_sizes=MOD,
        master_truth_digest_binding=[dict(file=x["file"], sha256=x["sha256"]) for x in tm["shards"]],
        shards=shards)
    (obs / "FULLSCALE_V2_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--seed", type=int, default=7302)
    ap.add_argument("--measurement-seed", type=int, default=None)
    ap.add_argument("--suppress", default=None,
                    help="comma-separated components removed from OBSERVATION only; "
                         "the truth keeps their latents so off-twin statistics still run")
    a = ap.parse_args()
    sup = {c.strip() for c in a.suppress.split(",")} if a.suppress else None
    m = observe(Path(a.root), a.seed, a.measurement_seed, suppress=sup)
    print(json.dumps(dict(status="PASS", cells=m["n_cells"], addresses=m["n_addresses"],
                          modules=m["modules"]["n"],
                          fraction_of_space=round(m["modules"]["fraction_of_space"], 4),
                          mean_detected_fraction=round(m["mean_detected_fraction"], 4),
                          background_programs=m["background"]["n_programs"]), indent=2))


if __name__ == "__main__":
    main()
