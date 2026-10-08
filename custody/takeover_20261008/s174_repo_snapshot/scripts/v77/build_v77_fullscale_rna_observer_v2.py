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
import v77_background_v2 as BG2

N = AU.N_ADDRESSES

# module sizes as a fraction of a 41,238-address space: a 400-address program is ~1%
MOD = dict(state=400, donor=300, rare=60, transient=150, marker=30, partial=180,
           interact=150, local=220, niche=150, pert=180, tf_target=220)
SC = dict(state=0.95, donor=0.80, rare=2.40, transient=1.30, marker=2.20, partial=1.60,
          interact=1.60, gain=1.00, niche=1.10, pert_direct=1.70, tf=1.10, background=0.55)
N_BACKGROUND_PROGRAMS = 60
BACKGROUND_GENES_PER = 600
REDUNDANT_OVERLAP = 0.45     # declared pathway-redundancy fraction within a module family


# Stream registry for planted module loadings. The oracle needs the SIGN of each loading to
# read a signed module correctly (defect S127: an unweighted mean of a mixed-sign module is a
# symmetric function of its driver and destroys the signal). This table mirrors the vec() calls
# below, and `module_sign_vector` reconstructs the exact signs the observer used, so the
# correction works on worlds that were already generated.
MODULE_STREAMS = {}
for _k in range(6):   MODULE_STREAMS[f"B1_state{_k}"]   = 9200 + _k
for _j in range(3):   MODULE_STREAMS[f"B2_donor{_j}"]   = 9300 + _j
for _j in range(4):   MODULE_STREAMS[f"B3_rare{_j}"]    = 9400 + _j
MODULE_STREAMS["B4_transient"] = 9500
for _j in range(2):   MODULE_STREAMS[f"B5_marker{_j}"]  = 9600 + _j
for _j in range(5):   MODULE_STREAMS[f"B6_rung{_j}"]    = 9700 + _j
MODULE_STREAMS["C1_A"] = 9800; MODULE_STREAMS["C1_B"] = 9801; MODULE_STREAMS["C1_AB"] = 9802
MODULE_STREAMS["C2_local"] = 9900
for _t in range(4):   MODULE_STREAMS[f"D1_tf{_t}"]      = 9950 + _t
MODULE_STREAMS["E1_niche"] = 9990
MODULE_STREAMS["E2_direct"] = 9995


def module_sign_vector(seed: int, name: str, addresses):
    """Exact signs the observer used for this module, or None if the module has no own loading.

    `*__private` entries are sub-allocations made by the redundancy allocator; the loading is
    applied to the parent union, so they carry no independent sign vector.
    """
    if name.endswith("__private") or name not in MODULE_STREAMS:
        return None
    stream = MODULE_STREAMS[name]
    g = np.asarray(addresses, dtype=np.uint64)
    return np.sign(T.normal(seed + stream, g, stream)).astype(np.float64)


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


STRUCTURAL_SUPPORT_RULE = "S146_S147_NAME_MAPPED_REGISTRY_RELATIVE_V1"


def structural_support(uni, source_ix, op_index, qc, operator_ids, seed):
    """PRE-REPAIR RULE, retained only so worlds built before the repair stay reproducible.
    Never call it for a new world. It carries two defects, both introduced in 4e95aac4:

    S146  it indexes uni.source_support, whose rows are (HVS, NPH52, SEA_AD), with a truth
          source_index that follows World A's order (SEA_AD, NPH52, HVS). HVS and SEA-AD
          coverage were swapped, so the ~90% of cells that are SEA-AD received HVS coverage.
    S147  structural_missing_fraction is measured against the whole registry, so it already
          contains the cohort's own coverage gap. Applying it again inside that coverage counts
          the gap twice: an HVS operator keeps 0.4543 of the registry, exactly HVS coverage, yet
          this rule left an HVS-operator cell with about 0.21.

    Original description: support = the cohort really measured the address AND this operator
    retained it, with the operator attrition applied within what the cohort measured.
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


def structural_support_v2(uni, source_ix, op_index, qc, operator_ids, operator_sources,
                          source_names, seed):
    """Support = the cohort measured the address AND this operator retained it, with both
    defects of the pre-repair rule removed.

    * source_index is mapped to its registry family by NAME, never by position (S146).
    * an operator's kept fraction is registry-relative, and a real operator cannot measure an
      address its cohort does not cover, so the attrition WITHIN the cohort's coverage is
      keep_registry / coverage (S147). An HVS operator therefore keeps all of HVS coverage,
      which is exactly what its own QC row reports.
    * a cell whose operator belongs to a different cohort than its source_index describes an
      impossible measurement and is refused rather than modelled.
    """
    fam_of_source = AU.family_rows_for_source_names(source_names)
    fam_of_operator = AU.family_rows_for_source_names(operator_sources)
    src_rows = fam_of_source[np.asarray(source_ix, dtype=np.int64)]
    op_index = np.asarray(op_index, dtype=np.int64)
    bad = fam_of_operator[op_index] != src_rows
    if bad.any():
        raise RuntimeError(f"{int(bad.sum())} cells have an operator from a different cohort than "
                           "their source_index; refusing to model an impossible measurement")
    sup = uni.source_support[src_rows].copy()                                 # (cells, N) bool
    aid = np.arange(N, dtype=np.uint64)
    for op in np.unique(op_index):
        row = qc[operator_ids[int(op)]]
        keep_registry = (1.0 - float(row["structural_missing_fraction"])
                         - float(row.get("collision_unresolved_fraction", 0.0)))
        coverage = float(uni.source_support[fam_of_operator[int(op)]].mean())
        within = keep_registry / coverage
        if within > 1.0 + 1e-9:
            raise RuntimeError(f"operator {operator_ids[int(op)]} keeps {keep_registry:.6f} of the "
                               f"registry but its cohort covers only {coverage:.6f}")
        within = float(np.clip(within, 0.05, 1.0))
        s = T.u01(seed + 811, aid, 1100 + int(op))
        drop = s > within
        cells = np.where(op_index == op)[0]
        sup[np.ix_(cells, np.where(drop)[0])] = False
    return sup


def observation_identity_block(tm: dict, support_rule_id: str) -> dict:
    """Producer-side observation identity (S161): which study, operator and donor measured each
    cell, with every positional index resolvable by NAME against a roster (the S146 failure was a
    positional index read against the wrong order). These are facts of the measurement design,
    known for real cells too, so they belong to the observable layer and a consumer never needs
    the hidden-truth folder to learn them."""
    rows = AU.family_rows_for_source_names(tm["source_names"])
    roster = [AU.SOURCE_FAMILIES[r] for r in rows]
    op_src = [AU.SOURCE_FAMILIES[r] for r in AU.family_rows_for_source_names(tm["operator_sources"])]
    ops = [str(o) for o in tm["operator_ids"]]
    if len(ops) != len(op_src) or len(set(ops)) != len(ops):
        raise RuntimeError("operator roster is malformed: ids and sources must align one-to-one, ids unique")
    if len(set(roster)) != len(roster):
        raise RuntimeError("source roster contains duplicate cohorts")
    donors = [str(d) for d in tm.get("donor_ids", [])]
    return dict(source_roster=roster, source_index_semantics="index into source_roster",
                operator_ids=ops, operator_index_semantics="index into operator_ids",
                operator_source_map=[[o, s] for o, s in zip(ops, op_src)],
                donor_ids=donors, donor_index_semantics="index into donor_ids",
                support_rule_id=support_rule_id)


CHALLENGE_SPEC_FILE = "CHALLENGE_SPEC.json"   # hidden truth only; never copied to observable output
CHALLENGE_STREAM = 7710
CHALLENGE_KINDS = ("BIO", "TWIN_EXACT", "TWIN_OPERATOR")


def load_challenge(truth_root: Path):
    """The S157 paired-challenge spec, read from the HIDDEN truth folder. The observer never writes
    it, or anything derived from its arm label, into the observable layer."""
    p = Path(truth_root) / CHALLENGE_SPEC_FILE
    if not p.exists():
        return None
    spec = json.loads(p.read_text())
    if spec.get("kind") not in CHALLENGE_KINDS:
        raise RuntimeError(f"unknown challenge kind {spec.get('kind')!r}")
    return spec


def challenge_latent(spec: dict, z: dict, ids, seed: int) -> np.ndarray:
    """The S157 challenge latent; one implementation, used by the observer and by the scorer.

    BIO and TWIN_EXACT group cells by their biological state and draw the same stateless noise, so
    their latents, and therefore their observables, are identical: an exact semantic twin, in which
    only the hidden interpretation (biology or capture) differs. TWIN_OPERATOR groups cells by the
    operator that measured them instead."""
    kind = spec["kind"]
    if kind in ("BIO", "TWIN_EXACT"):
        g = (np.asarray(z["state_index"]).astype(np.int64) == int(spec["k_star"]))
    elif kind == "TWIN_OPERATOR":
        g = np.isin(np.asarray(z["operator_index"]).astype(np.int64),
                    np.asarray(spec["operator_set"], dtype=np.int64))
    else:
        raise RuntimeError(f"unknown challenge kind {kind!r}")
    eps = T.normal(seed + CHALLENGE_STREAM, np.asarray(ids, dtype=np.uint64), 1)
    return float(spec["delta"]) * g.astype(np.float64) + eps


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


def build_eta(z, enabled, seed, uni, alloc, bg, n, suppress=frozenset(), bg2=None):
    """eta = registry abundance + background covariance + World A base + planted components."""
    present = set(enabled) | set(suppress)   # allocate for every planted component
    eta = np.tile(uni.log_abundance.astype(np.float32), (n, 1))     # heavy-tailed abundance

    # background correlated programs: the 'correlated substitutes' a model can exploit
    if bg2 is not None:
        # successor background: hierarchical broad/mid/narrow factors plus paralog groups,
        # calibrated to the real dependence topology rather than to the marginals alone
        Zb = bg2.cell_factors(z["global_cell_index"])
        eta += Zb @ bg2.loading_matrix()
    else:
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
            out_name="FULLSCALE_V2_CANONICAL_sharded", suppress: set[str] | None = None,
            background: str = "v1") -> dict:
    """`suppress` removes components from the OBSERVATION while the truth keeps their latents.

    This is what makes an off-twin a real control: the statistic can still be computed, and
    must return approximately zero. Removing the component from the TRUTH instead would mean
    the statistic is never evaluated, which is a check that cannot fail."""
    truth_root = root / "hidden_truth"
    obs = root / "observable_raw" / out_name
    obs.mkdir(parents=True, exist_ok=True)
    tm = json.loads((truth_root / "TRUTH_MANIFEST.json").read_text())
    challenge = load_challenge(truth_root)
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
    bg2 = BG2.BackgroundV2(seed, N) if background == "v2" else None
    from build_v77_extended_rna_observer import apply_perturbation_to_tf

    shards, total, dens = [], 0, []
    sup_acc = {}
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
        eta = build_eta(z, enabled, seed, uni, alloc, bg, len(ids), suppress=suppress, bg2=bg2)
        np.clip(eta, -8, 8, out=eta)
        rel = np.exp(eta, dtype=np.float32)
        sup = structural_support_v2(uni, src, op, qc, operator_ids, tm["operator_sources"],
                                    tm["source_names"], seed)
        for si in np.unique(src):
            m = src == si
            acc = sup_acc.setdefault(str(tm["source_names"][int(si)]), [0.0, 0])
            acc[0] += float(sup[m].mean(1).sum()); acc[1] += int(m.sum())
        # gene-specific detectability modulates preference within what is supported
        rel *= (1.0 / (1.0 + np.exp(-uni.logit_detect)))[None, :]
        rel *= sup
        if challenge is not None:
            # S157 paired challenge. The biological arm and its exact twin enter through IDENTICAL
            # arithmetic on purpose: an exact semantic twin is defined by identical observables.
            zc = challenge_latent(challenge, z, ids, seed)
            mod = np.asarray(challenge["module_addresses"], dtype=np.int64)
            rel[:, mod] *= np.exp(float(challenge["beta"]) * zc).astype(np.float32)[:, None]
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
                            # per-element structural support, so a consumer never has to guess
                            # which zeros were measurable (S135); bits run along addresses
                            support_mask_packed=np.packbits(sup, axis=1),
                            # producer-side observation identity, per cell (S161)
                            source_index=src.astype(np.int16), operator_index=op.astype(np.int16),
                            donor_index=np.asarray(z["donor_index"]).astype(np.int32),
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
        structural_support_rule=STRUCTURAL_SUPPORT_RULE,
        support_mask_in_shards="support_mask_packed, np.packbits along addresses",
        observation_identity=observation_identity_block(tm, STRUCTURAL_SUPPORT_RULE),
        feature_identity=dict(registry_sha256=AU.REGISTRY_SHA256, n_addresses=N,
                              address_id_order_sha256=hashlib.sha256(
                                  "\n".join(map(str, uni.address_id)).encode()).hexdigest()),
        realized_support_fraction_by_source={k: v[0] / v[1] for k, v in sorted(sup_acc.items())},
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
        background_model=background,
        background_v2=(bg2.summary() if bg2 is not None else None),
        background=dict(n_programs=N_BACKGROUND_PROGRAMS, genes_per_program=BACKGROUND_GENES_PER,
                        purpose=("correlated substitutes spanning the whole space, so broad covariance "
                                 "is not a free win; these carry no truth label")),
        pathway_redundancy=dict(declared_overlap_fraction=REDUNDANT_OVERLAP, families=fam_overlap),
        modules=dict(n=len(alloc.assigned), addresses_used=alloc.used,
                     fraction_of_space=alloc.used / N, sizes={k: len(v) for k, v in alloc.assigned.items()}),
        module_address_sets=alloc.assigned,
        module_streams={k: v for k, v in MODULE_STREAMS.items() if k in alloc.assigned},
        signed_loadings_note=("module loadings are mixed-sign; an unweighted mean is a symmetric "
                              "function of the driver and destroys the signal. See defect S127."),
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
    ap.add_argument("--background", choices=["v1", "v2"], default="v1",
                    help="v2 is the topology-calibrated successor background")
    ap.add_argument("--suppress", default=None,
                    help="comma-separated components removed from OBSERVATION only; "
                         "the truth keeps their latents so off-twin statistics still run")
    a = ap.parse_args()
    sup = {c.strip() for c in a.suppress.split(",")} if a.suppress else None
    m = observe(Path(a.root), a.seed, a.measurement_seed, suppress=sup, background=a.background)
    print(json.dumps(dict(status="PASS", cells=m["n_cells"], addresses=m["n_addresses"],
                          modules=m["modules"]["n"],
                          fraction_of_space=round(m["modules"]["fraction_of_space"], 4),
                          mean_detected_fraction=round(m["mean_detected_fraction"], 4),
                          background_programs=m["background"]["n_programs"]), indent=2))


if __name__ == "__main__":
    main()
