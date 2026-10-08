#!/usr/bin/env python3
"""Extract the REAL expression geometry of FOUNDATION TRAIN RNA as a frozen calibration target.

WHY. An audit of the synthetic world against the real TRAIN data showed the marginals were
close but the DEPENDENCE STRUCTURE was wrong by about five-fold:

  statistic                         real      synthetic
  median |corr| among HVGs          0.3291    0.0675
  HVG pairs |corr| > 0.3            56.2%     2.3%
  HVG pairs |corr| > 0.5            15.6%     0.1%
  variance in the top 10 PCs        0.509     0.310

Real transcriptomes are dominated by a few very large correlated axes, principally cell
identity. A synthetic world without them is "random" in the way that matters: a model can
look good on it and still fail on data whose correlation structure is nothing like it.

WHAT IS AND IS NOT TAKEN FROM REAL DATA. This extracts MARGINALS and CORRELATION SHAPE only:
per-gene abundance, per-gene detection rate, the gene-gene correlation distribution, the
eigenvalue spectrum, and the cell-class composition. It does NOT decide which genes belong to
which planted program. Planted modules remain randomly placed, because planting real programs
would let a model with real biological priors score well without learning from the data. The
line is: real GEOMETRY, random CONTENT.

GOVERNANCE. The source metadata carries only cell_id, donor_id, broad_cell_class and
source_library, so the read is pathology-blind. It is TRAIN-only and read-only, and no model
is fitted. This implements the standing requirement that fixtures match the real dataset.
"""
from __future__ import annotations
import argparse, glob, hashlib, json
from pathlib import Path
import numpy as np
from scipy import sparse

DEFAULT_CACHE = Path("D:/Jepa project/data/cache/stage81a3r_corrected_real_train")
N_ADDRESSES = 41238
FORBIDDEN_META = ("pathology", "braak", "cerad", "adnc", "plaque", "tangle", "at8", "diagnosis")


def sha256_file(p: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def load_real(cache: Path):
    fs = sorted(glob.glob(str(cache / "*.counts.npz")))
    if not fs:
        raise FileNotFoundError(f"no real TRAIN count shards under {cache}")
    Xs, cls, don, src, digests = [], [], [], [], []
    for f in fs:
        z = np.load(f, allow_pickle=False)
        shp = tuple(z["shape"])
        if shp[1] != N_ADDRESSES:
            raise ValueError(f"{f} is not in the canonical {N_ADDRESSES}-address space: {shp}")
        Xs.append(sparse.csr_matrix((z["data"], z["indices"], z["indptr"]), shape=shp))
        m = np.load(f.replace(".counts.", ".meta."), allow_pickle=True)
        bad = [k for k in m.files if any(t in k.lower() for t in FORBIDDEN_META)]
        if bad:
            raise PermissionError(f"pathology-like metadata present, refusing to read: {bad}")
        cls.append(m["broad_cell_class"]); don.append(m["donor_id"]); src.append(m["source_library"])
        digests.append(dict(file=Path(f).name, sha256=sha256_file(Path(f))))
    return (sparse.vstack(Xs).tocsr(), np.concatenate(cls), np.concatenate(don),
            np.concatenate(src), digests)


def extract(cache: Path, n_hvg: int = 3000, det_floor: float = 0.05) -> dict:
    X, cls, don, src, digests = load_real(cache)
    n, G = X.shape
    lib = np.asarray(X.sum(1)).ravel()
    gsum = np.asarray(X.sum(0)).ravel()
    gdet = np.asarray((X > 0).sum(0)).ravel() / n
    gmean = gsum / n

    keep = np.where(gdet > det_floor)[0]
    Xk = X[:, keep].astype(np.float64)
    Xk.data = np.log1p(Xk.data / np.repeat(np.maximum(lib, 1), np.diff(Xk.indptr)) * 1e4)
    Ld = np.asarray(Xk.todense())
    v = Ld.var(0)
    sel = np.argsort(-v)[:n_hvg]
    H = Ld[:, sel]
    H = (H - H.mean(0)) / (H.std(0) + 1e-9)
    C = (H.T @ H) / len(H)
    off = C[~np.eye(len(C), dtype=bool)]
    ev = np.linalg.eigvalsh(C)[::-1]
    tot = float(ev.sum())

    uc, cc = np.unique(cls, return_counts=True)
    return dict(
        schema="V77_REAL_TRAIN_EXPRESSION_CALIBRATION_V1",
        source=dict(cache=str(cache), n_shards=len(digests), shard_digests=digests,
                    pathology_blind=True, train_only=True, read_only=True,
                    metadata_fields=["cell_id", "donor_id", "broad_cell_class", "source_library"]),
        cohort=dict(n_cells=int(n), n_addresses=int(G), n_donors=int(len(np.unique(don))),
                    n_source_libraries=int(len(np.unique(src))),
                    cell_class_counts={str(k): int(c) for k, c in zip(uc, cc)}),
        per_cell=dict(median_library=float(np.median(lib)),
                      median_detected=float(np.median(np.diff(X.indptr))),
                      density=float(np.diff(X.indptr).mean() / G)),
        per_gene=dict(
            expressed_fraction=float((gmean > 0).mean()),
            abundance_max_over_median_nonzero=float(gmean.max() / np.median(gmean[gmean > 0])),
            top1pct_count_share=float(np.sort(gmean)[::-1][:G // 100].sum() / gmean.sum()),
            detection_quantiles=[float(x) for x in np.quantile(gdet, [.5, .75, .9, .99])]),
        dependence_targets=dict(
            n_hvg=n_hvg, det_floor=det_floor,
            genes_above_det_floor=int(len(keep)),
            abs_corr_quantiles={"p50": float(np.quantile(np.abs(off), .5)),
                                "p90": float(np.quantile(np.abs(off), .9)),
                                "p99": float(np.quantile(np.abs(off), .99)),
                                "p999": float(np.quantile(np.abs(off), .999))},
            fraction_abs_corr_gt_0p3=float((np.abs(off) > .3).mean()),
            fraction_abs_corr_gt_0p5=float((np.abs(off) > .5).mean()),
            variance_in_top_pcs={"10": float(ev[:10].sum() / tot),
                                 "50": float(ev[:50].sum() / tot),
                                 "200": float(ev[:200].sum() / tot)},
            components_for_90pct=int(np.searchsorted(np.cumsum(ev) / tot, .90) + 1)),
        what_this_is_used_for=[
            "per-gene abundance and detection priors, replacing the invented biotype prior",
            "a calibration TARGET for the synthetic background covariance",
            "cell-class composition, so synthetic cell identity carries realistic dominance"],
        what_this_is_NOT_used_for=[
            "deciding which genes belong to which planted program",
            "any planted biological content; modules stay randomly placed so that a model with "
            "real biological priors cannot score well without learning from the data"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(DEFAULT_CACHE))
    ap.add_argument("--out", required=True)
    ap.add_argument("--arrays-out", default=None,
                    help="optional .npz for the per-gene abundance and detection vectors")
    a = ap.parse_args()
    cache = Path(a.cache)
    rec = extract(cache)

    if a.arrays_out:
        X, cls, don, src, _ = load_real(cache)
        n = X.shape[0]
        gmean = np.asarray(X.sum(0)).ravel() / n
        gdet = np.asarray((X > 0).sum(0)).ravel() / n
        np.savez_compressed(a.arrays_out, gene_mean=gmean.astype(np.float32),
                            gene_detection_rate=gdet.astype(np.float32),
                            n_cells=np.int64(n))
        rec["arrays"] = dict(path=str(a.arrays_out), sha256=sha256_file(Path(a.arrays_out)))

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(rec, indent=2) + "\n")
    d = rec["dependence_targets"]
    print(json.dumps(dict(status="PASS", n_cells=rec["cohort"]["n_cells"],
                          n_donors=rec["cohort"]["n_donors"],
                          median_abs_corr=d["abs_corr_quantiles"]["p50"],
                          frac_gt_0p3=d["fraction_abs_corr_gt_0p3"],
                          var_top10=d["variance_in_top_pcs"]["10"]), indent=2))


if __name__ == "__main__":
    main()
