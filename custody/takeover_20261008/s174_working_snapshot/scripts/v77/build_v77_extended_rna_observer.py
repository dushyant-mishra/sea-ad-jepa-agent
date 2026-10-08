#!/usr/bin/env python3
"""V77 extended FULL104-like RNA observer.

NEW file. World A's observer (`scripts/v64/build_v73_full104_sharded_observer.py`) is frozen
and is imported read-only for its availability model, empirical depth/support targets and
exact-count realisation. Nothing in it is modified.

The observer is where RECOVERABILITY CLASSES are physically created. The design rule is that
a component's class must follow from its MECHANISM, not from a tuning constant:

* a factor loading on genes that are available under nearly every operator is recoverable;
* a factor loading on genes that are structurally unavailable under most operators is not
  recoverable from the permitted partial-RNA view, however strong its effect;
* B6 steps the mixture between those two gene pools, which is what produces a graded
  partial-recoverability ladder rather than World A's all-or-nothing 0.67/0.00.

Availability is a deterministic function of operator in World A, so the per-gene availability
profile is computed here from the frozen model and used to define the gene pools.
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "v64"))
sys.path.insert(0, str(HERE))
import build_v73_sharded_master_truth as T          # frozen
import build_v73_full104_sharded_observer as F      # frozen
import v73_full104_qc_calibration as Q              # frozen
import v77_regulatory_graph as RG

N_GENES = F.N_GENES

# effect scales, declared here so they are visible rather than buried
SC = dict(state=0.55, donor=0.45, rare_hi=1.70, rare_lo=1.70, transient=0.80,
          marker=1.30, partial=0.95, interact=1.10, gain=0.90, tf=0.65,
          niche=0.60, pert_direct=1.10)
N_MARKER_GENES = 5          # B5: few-gene programs
INTERACT_GENES = 6          # C1: the third module activated only by co-occurrence
LOCAL_MODULE_GENES = 10     # C2: the module whose loading is modulated
NICHE_GENES = 8             # E1
PERT_DIRECT_GENES = 7       # E2 arm 3


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def availability_profile(operator_ids, qc_by_op, seed, operator_counts):
    """Per-gene fraction of CELLS under which the gene is measured.

    Computed from World A's frozen availability model, weighted by how many cells each
    operator contributes, so the gene pools reflect the realised cohort.
    """
    n_ops = len(operator_ids)
    avail = np.ones((n_ops, N_GENES), dtype=np.float64)
    gid = np.arange(N_GENES, dtype=np.uint64)
    for op in range(n_ops):
        row = qc_by_op[operator_ids[op]]
        measured = int(row.get("measured_scalar_addresses",
                               round(F.FULL_ADDRESSES * (1 - float(row["structural_missing_fraction"])
                                     - float(row.get("collision_unresolved_fraction", 0.0))))))
        nmeas = min(N_GENES, max(0, int(round(measured / F.FULL_ADDRESSES * N_GENES))))
        nun = N_GENES - nmeas
        if nun:
            scores = T.u01(seed + 811, gid, 1100 + int(op))
            miss = np.argsort(scores, kind="stable")[:nun]
            avail[op, miss] = 0.0
    w = np.asarray(operator_counts, dtype=np.float64)
    w = w / max(w.sum(), 1.0)
    return (avail * w[:, None]).sum(axis=0)


def gene_pools(profile, seed):
    """Split the panel into a high-availability and a low-availability pool."""
    order = np.argsort(-profile, kind="stable")
    hi = order[: N_GENES // 2]
    lo = order[N_GENES // 2:]
    return hi, lo, profile[hi].mean(), profile[lo].mean()


def _pick(seed, pool, k, stream):
    s = T.u01(seed, np.asarray(pool, dtype=np.uint64), stream)
    return np.asarray(pool)[np.argsort(s, kind="stable")[:k]]


def _dense(seed, n_latent, stream0, scale):
    gid = np.arange(N_GENES, dtype=np.uint64)
    return np.stack([T.normal(seed, gid, stream0 + j) for j in range(n_latent)],
                    axis=0).astype(np.float64) * scale


def _sparse(seed, genes, stream, scale):
    v = np.zeros(N_GENES, dtype=np.float64)
    s = T.normal(seed, np.asarray(genes, dtype=np.uint64), stream)
    v[np.asarray(genes)] = np.sign(s) * scale
    return v


def build_eta(z, enabled, seed, hi, lo, graph):
    """Additive log-relative-rate contributions from every enabled component."""
    n = len(z["global_cell_index"])
    # --- World A base, unchanged ---
    latent = np.c_[z["z_global"], z["z_query"], z["z_reg_shared"]].astype(np.float32)
    eta = (latent @ F.weights(seed)).astype(np.float64)
    parts = {"world_A_base": eta.copy()}

    def add(name, contrib):
        nonlocal eta
        eta = eta + contrib
        parts[name] = contrib

    if "B1" in enabled:
        Wst = _dense(seed + 4100, 6, 4100, SC["state"])
        add("B1_state", Wst[z["state_index"].astype(np.int64)])
    if "B2" in enabled:
        add("B2_donor", z["z_donor"].astype(np.float64) @ _dense(seed + 4200, 3, 4200, SC["donor"]))
    if "B3" in enabled:
        # recoverable arms load on the HIGH-availability pool, non-recoverable arms on the LOW pool
        from build_v77_extended_truth import RARE_RECOVERABLE
        # A non-recoverable arm must be absent from the RNA view ENTIRELY. Loading it on
        # low-availability genes was not enough: "low availability" still means measured under
        # SOME operators, and the first construction leaked lift 19.4 and 6.0 on arms designed
        # to be invisible. The non-recoverable arms are therefore routed to the ATAC-only
        # modality and contribute nothing here, exactly as z_reg_private does in World A.
        c = np.zeros((n, N_GENES))
        for j, recoverable in enumerate(RARE_RECOVERABLE):
            if not recoverable:
                continue
            genes = _pick(seed + 4300 + j, hi, 6, 4300 + j)
            c += z["rare_flags"][:, j][:, None] * _sparse(
                seed + 4300 + j, genes, 4310 + j, SC["rare_hi"])[None, :]
        add("B3_rare", c)
    if "B4" in enabled:
        band = np.exp(-((z["pseudotime"].astype(np.float64) - 0.5) / 0.15) ** 2)
        genes = _pick(seed + 4400, hi, 8, 4400)
        add("B4_transient", band[:, None] * _sparse(seed + 4400, genes, 4401, SC["transient"])[None, :])
    if "B5" in enabled:
        W = np.zeros((z["z_marker"].shape[1], N_GENES))
        for j in range(W.shape[0]):
            W[j] = _sparse(seed + 4500 + j, _pick(seed + 4500 + j, hi, N_MARKER_GENES, 4500 + j),
                           4510 + j, SC["marker"])
        add("B5_marker", z["z_marker"].astype(np.float64) @ W)
    if "B6" in enabled:
        # THE LADDER. Rung j expresses fraction f_j of its total effect in RNA and the
        # remaining 1-f_j in the ATAC-only modality. Grading by MODALITY SHARE grades how much
        # of the factor is visible in the permitted view at all, which is the premise question.
        # The first construction graded the split between high- and low-availability gene
        # pools and produced a U-shaped curve, because it was measuring loading DILUTION rather
        # than visibility: a low-availability gene is still measured under some operators.
        K = z["z_partial"].shape[1]
        fracs = np.linspace(0.0, 1.0, K)
        W = np.zeros((K, N_GENES))
        for j, f in enumerate(fracs):
            gh = _pick(seed + 4600 + j, hi, 8, 4600 + j)
            W[j] = f * _sparse(seed + 4600 + j, gh, 4640 + j, SC["partial"])
        add("B6_partial", z["z_partial"].astype(np.float64) @ W)
    if "C1" in enabled:
        # A and B each carry their OWN marginal program, and their co-occurrence additionally
        # activates a THIRD disjoint module. Without the marginal programs the only RNA signal
        # of A or B is the conjunction itself, so an additive summary of A and B trivially
        # reproduces the conjunction and the test cannot detect anything. That was an
        # implementation bug against this component's own specification.
        A = z["c_state_a"].astype(np.float64)
        B = z["c_state_b"].astype(np.float64)
        gA = _pick(seed + 4700, hi, INTERACT_GENES, 4702)
        gB = _pick(seed + 4701, hi, INTERACT_GENES, 4703)
        gAB = _pick(seed + 4702, hi, INTERACT_GENES, 4704)
        add("C1_marginal_A", A[:, None] * _sparse(seed + 4700, gA, 4705, SC["interact"])[None, :])
        add("C1_marginal_B", B[:, None] * _sparse(seed + 4701, gB, 4706, SC["interact"])[None, :])
        add("C1_interaction", (A * B)[:, None]
            * _sparse(seed + 4702, gAB, 4707, SC["interact"])[None, :])
    if "C2" in enabled:
        # a MULTIPLICATIVE gain on one module's loading, not another additive global axis.
        # The module's own contribution is scaled per cell, so the effect is only visible by
        # conditioning on that module.
        genes = _pick(seed + 4800, hi, LOCAL_MODULE_GENES, 4800)
        globals()["_C2_MODULE_GENES"] = np.asarray(genes).tolist()
        base = _sparse(seed + 4800, genes, 4801, 1.0)
        drive = z["z_global"][:, 0].astype(np.float64)          # the module this gain modulates
        gain = 1.0 + SC["gain"] * np.tanh(z["z_gain"].astype(np.float64))
        add("C2_local_gain", (drive * gain)[:, None] * base[None, :])
    if ("D1" in enabled) and graph is not None:
        M = RG.tf_gene_matrix(graph, "panel").astype(np.float64)
        ztf = z.get("_z_tf_effective", z["z_tf"]).astype(np.float64)
        add("D1_regulation", SC["tf"] * (ztf @ M))
    if "E1" in enabled:
        genes = _pick(seed + 4900, hi, NICHE_GENES, 4900)
        add("E1_niche", z["niche_score"].astype(np.float64)[:, None]
            * _sparse(seed + 4900, genes, 4901, SC["niche"])[None, :])
    if "E2" in enabled:
        genes = _pick(seed + 5000, hi, PERT_DIRECT_GENES, 5000)
        direct = (z["pert_id"] == 3).astype(np.float64) * z["pert_dose"].astype(np.float64)
        add("E2_pert_direct", direct[:, None] * _sparse(seed + 5000, genes, 5001, SC["pert_direct"])[None, :])
    return eta, parts


def apply_perturbation_to_tf(z, enabled):
    """TF arms shift the EFFECTIVE regulator activity, so the cascade flows through the graph.

    The null arm is assigned and dosed exactly like a real arm and shifts nothing, which is
    the false-positive control.
    """
    if not ({"E2", "D1"} <= set(enabled)):
        return
    from build_v77_extended_truth import PERTURBATIONS
    ztf = z["z_tf"].astype(np.float32).copy()
    for arm in PERTURBATIONS:
        if arm["kind"] != "tf_cascade":
            continue
        m = z["pert_id"] == arm["pert_id"]
        if m.any():
            ztf[m, arm["target_tf"]] += np.float32(arm["effect"]) * z["pert_dose"][m].astype(np.float32)
    z["_z_tf_effective"] = ztf


def biology_coupled_availability(avail, z, enabled, seed, ids):
    """C3: make measurement quality depend partly on biological state.

    Cells with high z_bioqc lose additional measured features beyond what their operator
    already removes, and their panel depth is scaled down. This deliberately breaks the
    independence that World A assumes and measures at |corr| <= 0.009.
    """
    if "C3" not in enabled:
        return avail, np.ones(len(ids))
    q = np.tanh(z["z_bioqc"].astype(np.float64))
    extra_frac = np.clip(0.22 * (q + 1.0) / 2.0, 0.0, 0.5)      # 0 .. 11% extra dropout
    gid = np.arange(N_GENES, dtype=np.uint64)
    out = avail.copy()
    for i in range(len(ids)):
        navail = int(out[i].sum())
        k = int(round(extra_frac[i] * navail))
        if k <= 0:
            continue
        cand = np.where(out[i] > 0)[0]
        s = T.u01(seed + 5100, (np.uint64(ids[i]) * np.uint64(2654435761)
                                + cand.astype(np.uint64)), 5100)
        out[i, cand[np.argsort(s, kind="stable")[:k]]] = 0
    depth_scale = 1.0 - 0.30 * (q + 1.0) / 2.0                   # 1.0 .. 0.70
    return out, depth_scale


def observe(root: Path, seed: int, measurement_seed: int | None) -> dict:
    truth_root = root / "hidden_truth"
    obs = root / "observable_raw" / "FULL104_like_sharded"
    obs.mkdir(parents=True, exist_ok=True)
    tm = json.loads((truth_root / "TRUTH_MANIFEST.json").read_text())
    if int(tm["seed"]) != int(seed):
        raise ValueError("observer seed must equal master-truth seed")
    measurement_seed = int(seed if measurement_seed is None else measurement_seed)
    enabled = set(tm["enabled_components"])
    qmeta, qc_by_op = Q.by_operator()
    qprobs = np.array(qmeta["quantile_probabilities"], dtype=float)
    operator_ids = tm["operator_ids"]
    graph = RG.build_graph(seed) if ({"D1", "D3", "E2"} & enabled) else None

    op_counts = tm["population_summary"]["operator_counts"]
    profile = availability_profile(operator_ids, qc_by_op, seed, op_counts)
    hi, lo, hi_mean, lo_mean = gene_pools(profile, seed)

    out_shards, total = [], 0
    for s in tm["shards"]:
        tp = truth_root / s["file"]
        if sha256_file(tp) != s["sha256"]:
            raise RuntimeError("truth shard digest mismatch: " + s["file"])
        zf = np.load(tp, allow_pickle=False)
        z = {k: zf[k] for k in zf.files}
        ids = z["global_cell_index"].astype(np.int64)
        op = z["operator_index"].astype(np.int16)

        apply_perturbation_to_tf(z, enabled)
        eta, _ = build_eta(z, enabled, seed, hi, lo, graph)
        rel = np.exp(np.clip(eta, -3, 3))

        avail = F.operator_availability(op, qc_by_op, operator_ids, seed)
        avail, depth_scale = biology_coupled_availability(avail, z, enabled, seed, ids)
        rel = rel * avail

        lib, dtarget, ztarget, projected, pdet, panel_count, panel_detected = F.empirical_targets(
            ids, op, avail, qc_by_op, operator_ids, qprobs, measurement_seed)
        if "C3" in enabled:
            panel_count = np.maximum(0, np.rint(panel_count * depth_scale).astype(np.int64))
            panel_detected = np.minimum(panel_detected, avail.sum(axis=1).astype(np.int64))
            panel_detected = np.minimum(panel_detected, panel_count)
            panel_count = np.maximum(panel_count, panel_detected)

        counts = F.exact_counts(rel, avail, ids, panel_count, panel_detected, measurement_seed)
        start, stop = int(ids[0]), int(ids[-1]) + 1
        opath = obs / f"RNA_{start:09d}_{stop:09d}.npz"
        np.savez(opath, counts=counts.T, availability=avail.T, genes=F.GENES,
                 gene_names=F.GENE_NAMES, global_cell_index=ids, cell_id=z["cell_id"],
                 empirical_projected_panel_count_target_int=panel_count.astype(np.int32),
                 empirical_projected_detected_feature_target_int=panel_detected.astype(np.int16),
                 empirical_full_library_size_target=lib.astype(np.float32),
                 empirical_measured_zero_fraction_target=ztarget.astype(np.float32))
        mpath = obs / f"META_{start:09d}_{stop:09d}.csv.gz"
        with gzip.open(mpath, "wt", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["global_cell_index", "cell_id", "donor", "source", "operator"])
            for i in range(len(ids)):
                w.writerow([int(ids[i]), str(z["cell_id"][i]),
                            tm["donor_ids"][int(z["donor_index"][i])],
                            str(np.array(T.SOURCE_NAMES)[int(z["source_index"][i])]),
                            operator_ids[int(op[i])]])
        out_shards.append(dict(start=start, stop=stop, cells=len(ids), rna_file=opath.name,
                               rna_sha256=sha256_file(opath), metadata_file=mpath.name,
                               metadata_sha256=sha256_file(mpath)))
        total += len(ids)

    manifest = dict(
        schema="V77_EXTENDED_FULL104_OBSERVER_MANIFEST_V1",
        seed=seed, truth_seed=seed, measurement_seed=measurement_seed,
        n_cells=total, n_genes=N_GENES, enabled_components=sorted(enabled),
        world_a_observer_frozen_and_imported=True,
        effect_scales=SC,
        gene_pools=dict(high_availability_genes=hi.tolist(), low_availability_genes=lo.tolist(),
                        mean_availability_high=float(hi_mean), mean_availability_low=float(lo_mean),
                        rationale=("recoverability class is created by WHICH POOL a factor loads on, "
                                   "not by a tuning constant")),
        b6_ladder_rna_share=np.linspace(0, 1, 5).tolist(),
        b6_ladder_semantics=("rung j expresses fraction f_j of its effect in RNA and 1-f_j in the "
                             "ATAC-only modality; the ladder grades VISIBILITY, not effect size"),
        c2_local_module_genes=globals().get("_C2_MODULE_GENES"),
        biology_coupled_measurement=("C3" in enabled),
        regulatory_graph_used=(graph is not None),
        hidden_truth_path_exposed=False,
        master_truth_digest_binding=[dict(file=x["file"], sha256=x["sha256"]) for x in tm["shards"]],
        shards=out_shards)
    (obs / "FULL104_SHARDED_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--seed", type=int, default=7302)
    ap.add_argument("--measurement-seed", type=int, default=None)
    a = ap.parse_args()
    m = observe(Path(a.root), a.seed, a.measurement_seed)
    print(json.dumps(dict(status="PASS", cells=m["n_cells"], shards=len(m["shards"]),
                          enabled_components=m["enabled_components"],
                          biology_coupled_measurement=m["biology_coupled_measurement"]), indent=2))


if __name__ == "__main__":
    main()
