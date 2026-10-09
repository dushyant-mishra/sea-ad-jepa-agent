#!/usr/bin/env python3
"""V77 full-scale RNA observer: 41,238 addresses, sparse, at the real measured geometry.

WHY THIS EXISTS
---------------
The inherited observer projects the measured library onto a 96-gene panel. That preserves
RATES but not SCALE, and scale is the thing that matters:

* a real cell detects about 4,687 of 41,238 addresses (11.4% density); a 96-gene cell detects
  about 24, so the data are dense where the real data are sparse;
* with 96 genes, fourteen sparse biological programs CANNOT be disjoint, so every module
  collides with every other one. That is not a design bug to be allocated around, it is the
  panel being 430x too small. Measured consequence: World A's own base ceilings fell from
  0.683 to 0.442 once other components were added, purely from module collision;
* rare-state and sparse-marker claims are not meaningful when a "sparse" program is 6 of 96
  features, i.e. 6% of the transcriptome.

IDENTITY BOUNDARY (not negotiable)
----------------------------------
This uses the canonical SIZE (41,238) and the frozen per-operator measured-support and
depth structure. Addresses are synthetic identifiers. Address k carries NO claim to
correspond to the real gene at registry position k, and this observer does not create the
96-feature -> canonical-address bridge that the October 5 reset holds as
BLOCKED__GENE_IDENTITY_MAPPING_UNDEFINED. Matching geometry is not claiming identity.

World A's generators remain frozen and are imported read-only for their RNG primitives and
QC calibration only; the count realisation here is new because the old one cannot run at
this scale.
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "v64"))
sys.path.insert(0, str(HERE))
import build_v73_sharded_master_truth as T       # frozen
import v73_full104_qc_calibration as Q           # frozen
import v77_regulatory_graph as RG

N_ADDRESSES = 41238

# Module sizes are now expressed as a FRACTION OF THE REAL ADDRESS SPACE, which is what makes
# "sparse" mean sparse. A 40-gene program is 0.1% of the transcriptome, not 6%.
MOD = dict(state=400, donor=300, rare=40, transient=120, marker=25, partial=150,
           interact=120, local=200, niche=120, pert=150, tf_target=200)
SC = dict(state=0.95, donor=0.80, rare=2.40, transient=1.30, marker=2.20, partial=1.60,
          interact=1.60, gain=1.00, niche=1.10, pert_direct=1.70, tf=1.10)


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


class ModuleAllocator:
    """Hands out DISJOINT address blocks. At 41,238 addresses this is finally possible."""

    def __init__(self, seed: int, n: int = N_ADDRESSES):
        order = np.argsort(T.u01(seed + 9100, np.arange(n, dtype=np.uint64), 9100), kind="stable")
        self._pool = order
        self._cursor = 0
        self.assigned: dict[str, list[int]] = {}

    def take(self, name: str, k: int) -> np.ndarray:
        if self._cursor + k > len(self._pool):
            raise RuntimeError("module allocator exhausted")
        sel = np.sort(self._pool[self._cursor:self._cursor + k])
        self._cursor += k
        self.assigned[name] = sel.tolist()
        return sel

    @property
    def used(self) -> int:
        return self._cursor


def operator_support(op_index, qc_by_op, operator_ids, seed):
    """Per-cell boolean support over 41,238 addresses, from the REAL measured counts."""
    sup = np.zeros((len(op_index), N_ADDRESSES), dtype=bool)
    aid = np.arange(N_ADDRESSES, dtype=np.uint64)
    for op in np.unique(op_index):
        row = qc_by_op[operator_ids[int(op)]]
        measured = int(row.get("measured_scalar_addresses",
                       round(N_ADDRESSES * (1 - float(row["structural_missing_fraction"])
                             - float(row.get("collision_unresolved_fraction", 0.0))))))
        measured = int(np.clip(measured, 1, N_ADDRESSES))
        s = T.u01(seed + 811, aid, 1100 + int(op))
        keep = np.argsort(s, kind="stable")[:measured]
        rows = np.where(op_index == op)[0]
        sup[np.ix_(rows, keep)] = True
    return sup


def depth_targets(ids, op, sup, qc_by_op, operator_ids, qprobs, mseed):
    """Library size and detected-feature counts drawn from the REAL operator quantiles.

    No projection: at full scale the quantiles apply directly, which is the whole point.
    """
    ids_u = np.asarray(ids, dtype=np.uint64)
    zd = T.normal(mseed + 701, ids_u, 951)
    zi = T.normal(mseed + 704, ids_u, 954)
    ud = _ncdf(zd)
    n = len(ids)
    lib = np.empty(n); det = np.empty(n)
    navail = sup.sum(1).astype(np.float64)
    for oi in np.unique(op):
        ix = np.where(op == oi)[0]
        row = qc_by_op[operator_ids[int(oi)]]
        rho = float(np.clip(float(row.get("log1p_library_vs_detected_pearson", 0.0) or 0.0), -0.98, 0.98))
        zs = rho * zd[ix] + np.sqrt(max(0.0, 1 - rho * rho)) * zi[ix]
        lib[ix] = Q.interp_quantiles(ud[ix], qprobs, row["rna_library_size_quantiles"])
        det[ix] = Q.interp_quantiles(_ncdf(zs), qprobs, row["rna_detected_feature_quantiles"])
    det = np.clip(np.rint(det), 1, navail).astype(np.int64)
    lib = np.maximum(np.rint(lib).astype(np.int64), det)
    return lib, det


def _ncdf(x):
    x = np.asarray(x, dtype=np.float64); ax = np.abs(x)
    t = 1.0 / (1.0 + 0.2316419 * ax)
    poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    tail = np.exp(-0.5 * ax * ax) / np.sqrt(2 * np.pi) * poly
    return np.where(x >= 0, 1.0 - tail, tail)


def sparse_counts(rel, sup, ids, lib, det, mseed):
    """Realise exactly `det` detected addresses and exactly `lib` total counts per cell.

    Returns CSR-style arrays. Operates per cell so peak memory stays near one row.
    """
    n = len(ids)
    indptr = np.zeros(n + 1, dtype=np.int64)
    idx_all, val_all = [], []
    aid = np.arange(N_ADDRESSES, dtype=np.uint64)
    for i in range(n):
        k = int(det[i])
        score = np.where(sup[i], np.log(np.maximum(rel[i], 1e-30)), -np.inf)
        u = T.u01(mseed + 510, np.uint64(ids[i]) * np.uint64(1315423911) + aid, 902)
        score = score + 0.35 * (-np.log(-np.log(np.clip(u, 1e-12, 1 - 1e-12))))
        top = np.argpartition(score, -k)[-k:]
        top = top[np.argsort(top)]
        w = np.maximum(rel[i, top], 1e-30)
        w = w / w.sum()
        remaining = int(lib[i]) - k
        base = np.floor(w * remaining).astype(np.int64)
        resid = remaining - int(base.sum())
        if resid > 0:
            frac = w * remaining - base
            base[np.argsort(-frac)[:resid]] += 1
        vals = (base + 1).astype(np.int32)
        idx_all.append(top.astype(np.int32)); val_all.append(vals)
        indptr[i + 1] = indptr[i] + k
    return (np.concatenate(idx_all), np.concatenate(val_all), indptr)


def build_eta(z, enabled, seed, alloc, graph, n):
    """Dense float32 eta for one shard. Components use DISJOINT address modules."""
    eta = np.zeros((n, N_ADDRESSES), dtype=np.float32)

    def sparse_vec(name, k, stream, scale):
        g = alloc.assigned.get(name)
        g = alloc.take(name, k) if g is None else np.asarray(g)
        v = np.zeros(N_ADDRESSES, dtype=np.float32)
        s = T.normal(seed + stream, np.asarray(g, dtype=np.uint64), stream)
        v[g] = np.sign(s).astype(np.float32) * np.float32(scale)
        return v

    # World A base: a dense low-rank field over the whole address space
    lat = np.c_[z["z_global"], z["z_query"], z["z_reg_shared"]].astype(np.float32)
    aidx = np.arange(N_ADDRESSES, dtype=np.uint64)
    W = np.stack([T.normal(seed + 100, aidx, 200 + j) for j in range(lat.shape[1])],
                 axis=0).astype(np.float32) * np.float32(0.22)
    eta += lat @ W

    if "B1" in enabled:
        for k in range(6):
            eta += (z["state_index"] == k).astype(np.float32)[:, None] * \
                   sparse_vec(f"B1_state{k}", MOD["state"], 9200 + k, SC["state"])[None, :]
    if "B2" in enabled:
        for j in range(z["z_donor"].shape[1]):
            eta += z["z_donor"][:, j].astype(np.float32)[:, None] * \
                   sparse_vec(f"B2_donor{j}", MOD["donor"], 9300 + j, SC["donor"])[None, :]
    if "B3" in enabled:
        from build_v77_extended_truth import RARE_RECOVERABLE
        for j, rec in enumerate(RARE_RECOVERABLE):
            if not rec:
                continue      # non-recoverable arms live in the ATAC-only modality
            eta += z["rare_flags"][:, j].astype(np.float32)[:, None] * \
                   sparse_vec(f"B3_rare{j}", MOD["rare"], 9400 + j, SC["rare"])[None, :]
    if "B4" in enabled:
        band = np.exp(-((z["pseudotime"].astype(np.float32) - 0.5) / 0.15) ** 2)
        eta += band[:, None] * sparse_vec("B4_transient", MOD["transient"], 9500, SC["transient"])[None, :]
    if "B5" in enabled:
        for j in range(z["z_marker"].shape[1]):
            eta += z["z_marker"][:, j].astype(np.float32)[:, None] * \
                   sparse_vec(f"B5_marker{j}", MOD["marker"], 9600 + j, SC["marker"])[None, :]
    if "B6" in enabled:
        K = z["z_partial"].shape[1]
        for j, f in enumerate(np.linspace(0.0, 1.0, K)):
            eta += (f * z["z_partial"][:, j].astype(np.float32))[:, None] * \
                   sparse_vec(f"B6_rung{j}", MOD["partial"], 9700 + j, SC["partial"])[None, :]
    if "C1" in enabled:
        A = z["c_state_a"].astype(np.float32); B = z["c_state_b"].astype(np.float32)
        eta += A[:, None] * sparse_vec("C1_A", MOD["interact"], 9800, SC["interact"])[None, :]
        eta += B[:, None] * sparse_vec("C1_B", MOD["interact"], 9801, SC["interact"])[None, :]
        eta += (A * B)[:, None] * sparse_vec("C1_AB", MOD["interact"], 9802, SC["interact"])[None, :]
    if "C2" in enabled:
        base = sparse_vec("C2_local", MOD["local"], 9900, 1.0)
        drive = z["z_global"][:, 0].astype(np.float32)
        gain = (1.0 + SC["gain"] * np.tanh(z["z_gain"].astype(np.float32))).astype(np.float32)
        eta += (drive * gain)[:, None] * base[None, :]
    if ("D1" in enabled) and graph is not None:
        ztf = z.get("_z_tf_effective", z["z_tf"]).astype(np.float32)
        for t in range(ztf.shape[1]):
            eta += ztf[:, t][:, None] * sparse_vec(f"D1_tf{t}", MOD["tf_target"], 9950 + t, SC["tf"])[None, :]
    if "E1" in enabled:
        eta += z["niche_score"].astype(np.float32)[:, None] * \
               sparse_vec("E1_niche", MOD["niche"], 9990, SC["niche"])[None, :]
    if "E2" in enabled:
        d = ((z["pert_id"] == 3).astype(np.float32) * z["pert_dose"].astype(np.float32))
        eta += d[:, None] * sparse_vec("E2_direct", MOD["pert"], 9995, SC["pert_direct"])[None, :]
    return eta


def observe(root: Path, seed: int, mseed: int | None, out_name="FULLSCALE_41238_sharded") -> dict:
    truth_root = root / "hidden_truth"
    obs = root / "observable_raw" / out_name
    obs.mkdir(parents=True, exist_ok=True)
    tm = json.loads((truth_root / "TRUTH_MANIFEST.json").read_text())
    mseed = int(seed if mseed is None else mseed)
    enabled = set(tm["enabled_components"])
    qmeta, qc = Q.by_operator()
    qprobs = np.array(qmeta["quantile_probabilities"], dtype=float)
    operator_ids = tm["operator_ids"]
    graph = RG.build_graph(seed) if ({"D1", "D3", "E2"} & enabled) else None
    alloc = ModuleAllocator(seed)

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
        apply_perturbation_to_tf(z, enabled)
        eta = build_eta(z, enabled, seed, alloc, graph, len(ids))
        np.clip(eta, -3, 3, out=eta)
        rel = np.exp(eta, dtype=np.float32)
        sup = operator_support(op, qc, operator_ids, seed)
        rel *= sup
        lib, det = depth_targets(ids, op, sup, qc, operator_ids, qprobs, mseed)
        idx, val, indptr = sparse_counts(rel, sup, ids, lib, det, mseed)
        dens.append(float(det.mean() / N_ADDRESSES))
        start, stop = int(ids[0]), int(ids[-1]) + 1
        p = obs / f"RNA_SPARSE_{start:09d}_{stop:09d}.npz"
        np.savez_compressed(p, indices=idx, data=val, indptr=indptr,
                            n_addresses=np.int64(N_ADDRESSES),
                            global_cell_index=ids, cell_id=z["cell_id"],
                            support_count=sup.sum(1).astype(np.int32),
                            library_target=lib.astype(np.int64),
                            detected_target=det.astype(np.int64))
        shards.append(dict(start=start, stop=stop, cells=len(ids), file=p.name,
                           sha256=sha256_file(p), nnz=int(len(idx))))
        total += len(ids)

    manifest = dict(
        schema="V77_FULLSCALE_41238_RNA_OBSERVER_MANIFEST_V1",
        seed=seed, truth_seed=seed, measurement_seed=mseed, n_cells=total,
        n_addresses=N_ADDRESSES, storage="CSR sparse (indices/data/indptr) per shard",
        enabled_components=sorted(enabled),
        mean_detected_fraction=float(np.mean(dens)),
        real_geometry_matched=dict(
            address_space=N_ADDRESSES,
            detected_per_cell_source="frozen operator rna_detected_feature_quantiles, applied directly",
            library_size_source="frozen operator rna_library_size_quantiles, applied directly",
            projection_to_96_panel_removed=True),
        identity_boundary=("synthetic address identifiers at canonical SCALE. Address k makes no "
                           "claim to be the real gene at registry position k. This is not the "
                           "BLOCKED 96-feature to canonical-address identity bridge."),
        disjoint_modules=dict(n_modules=len(alloc.assigned), addresses_used=alloc.used,
                              fraction_of_space_used=alloc.used / N_ADDRESSES,
                              modules={k: len(v) for k, v in alloc.assigned.items()}),
        module_address_sets=alloc.assigned,
        effect_scales=SC, module_sizes=MOD,
        master_truth_digest_binding=[dict(file=x["file"], sha256=x["sha256"]) for x in tm["shards"]],
        shards=shards)
    (obs / "FULLSCALE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--seed", type=int, default=7302)
    ap.add_argument("--measurement-seed", type=int, default=None)
    a = ap.parse_args()
    m = observe(Path(a.root), a.seed, a.measurement_seed)
    print(json.dumps(dict(status="PASS", cells=m["n_cells"], addresses=m["n_addresses"],
                          mean_detected_fraction=round(m["mean_detected_fraction"], 4),
                          n_disjoint_modules=m["disjoint_modules"]["n_modules"],
                          fraction_of_address_space_used=round(
                              m["disjoint_modules"]["fraction_of_space_used"], 4)), indent=2))


if __name__ == "__main__":
    main()
