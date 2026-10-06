#!/usr/bin/env python3
"""A_REPLICA control statistic: a reader that needs NO planted module support.

WHY IT IS NEEDED. A_REPLICA is the control world: World A's base latents only, with no planted
components. The module-projection oracle correctly FAILS CLOSED on it, because
module_address_sets is empty and there is nothing to project onto. That is right behaviour, not
a run failure, but it left the control world unmeasurable and therefore unable to do its job.

THE STATISTIC. Unsupervised principal components of the observed CPM-log1p matrix, then a
held-out linear readout of each World A base latent from those components. The reader is given
NO truth-side support: it must find structure itself. That makes it strictly weaker than the
module oracle and appropriate for a world with no planted modules.

WHAT IT IS FOR. A_REPLICA is a DETECT/REJECT control, not a ceiling. The base latents that drive
RNA must be readable, and the ones that do not drive RNA must not be:

  z_global, z_query, z_reg_shared   drive RNA           -> must be RECOVERABLE
  z_reg_private                     ATAC-only by design -> must NOT be recoverable from RNA
  technical_latents[1], [2]         inert, defect D1    -> must NOT be recoverable at all

A reader that recovers z_reg_private from RNA is leaking. A reader that cannot recover
z_global is too weak to serve as a control. Both failures are caught by the same test.

THRESHOLD PROVENANCE, stated honestly. This exact reader has never been run, at any scale, so
the acceptance values below are set from prior reasoning rather than from a measurement of it:

  * the 0.05 null band is the SAME band already used for the component off-twin controls, where
    four independent statistics rejected at -0.0217, -0.0141, -0.0010 and 0.0151;
  * the 0.30 recoverable floor is set at roughly half of World A's locked 96-gene ceilings of
    0.6832, 0.6629 and 0.6678, on the reasoning that an unsupervised PCA reader at 41,238
    addresses should retain at least half of what a supervised reader achieved on 96. It is a
    FLOOR, not a band, because the control's job is to show the base is readable at all.

These are frozen here, before the next generator family is built or tested.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from scipy import sparse

N_COMPONENTS = 50          # frozen prospectively
SPLIT_SEED = 20261006
RECOVERABLE_FLOOR = 0.30
NULL_BAND = 0.05
SEPARATION_MIN = 0.25

RECOVERABLE = ["z_global", "z_query", "z_reg_shared"]
NOT_RECOVERABLE_FROM_RNA = ["z_reg_private"]
INERT = [("technical_latents", 1), ("technical_latents", 2)]


def load_observed(root: Path, obs_dir: str):
    d = root / "observable_raw" / obs_dir
    man = json.loads(next(d.glob("*MANIFEST*.json")).read_text())
    N = int(man["n_addresses"])
    Xs = []
    for s in man["shards"]:
        z = np.load(d / s["file"], allow_pickle=False)
        X = sparse.csr_matrix((z["data"].astype(np.float64), z["indices"], z["indptr"]),
                              shape=(len(z["indptr"]) - 1, N))
        lib = np.asarray(X.sum(1)).ravel()
        X.data = np.log1p(X.data / np.repeat(np.maximum(lib, 1), np.diff(X.indptr)) * 1e4)
        Xs.append(X)
    return sparse.vstack(Xs).tocsr(), man


def load_truth(root: Path):
    acc = {}
    for f in sorted((root / "hidden_truth").glob("TRUTH_*.npz")):
        z = np.load(f, allow_pickle=False)
        for k in z.files:
            if k != "cell_id":
                acc.setdefault(k, []).append(z[k])
    return {k: np.concatenate(v, 0) for k, v in acc.items()}


def top_components(X, k=N_COMPONENTS, seed=SPLIT_SEED):
    """Randomised SVD on the sparse matrix; the 41,238-address matrix is never densified."""
    rng = np.random.default_rng(seed)
    n, N = X.shape
    mu = np.asarray(X.mean(0)).ravel()

    def mm(M):                      # (X - mu) @ M, without ever densifying X
        return X @ M - np.outer(np.ones(n), mu @ M)

    def mmT(M):                     # (X - mu).T @ M
        return X.T @ M - np.outer(mu, M.sum(0))

    Q, _ = np.linalg.qr(mm(rng.standard_normal((N, k + 10))))
    for _ in range(2):              # power iterations sharpen the leading subspace
        Q, _ = np.linalg.qr(mm(mmT(Q)))
    # project onto the found subspace and take the leading left singular vectors
    B = mmT(Q).T                    # (k+10, N)
    U, S, _ = np.linalg.svd(B @ B.T)
    scores = (Q @ U)[:, :k] * S[:k] ** 0.25
    return scores


def evaluate(root: Path, obs_dir="FULLSCALE_V2_CANONICAL_sharded") -> dict:
    X, man = load_observed(root, obs_dir)
    t = load_truth(root)
    n = X.shape[0]
    PC = top_components(X)
    rng = np.random.default_rng(SPLIT_SEED)
    p = rng.permutation(n)
    tr, te = p[: n // 2], p[n // 2:]

    def r2(y):
        X1 = np.c_[np.ones(n), PC]
        B, *_ = np.linalg.lstsq(X1[tr], y[tr], rcond=None)
        pr = X1[te] @ B
        yt = y[te]
        tt = ((yt - yt.mean()) ** 2).sum()
        return float(1 - ((yt - pr) ** 2).sum() / tt) if tt > 0 else float("nan")

    rec, nonrec = {}, {}
    for blk in RECOVERABLE:
        if blk in t:
            v = [r2(t[blk][:, j].astype(np.float64)) for j in range(t[blk].shape[1])]
            rec[blk] = dict(per_dim=v, mean=float(np.mean(v)))
    for blk in NOT_RECOVERABLE_FROM_RNA:
        if blk in t:
            v = [r2(t[blk][:, j].astype(np.float64)) for j in range(t[blk].shape[1])]
            nonrec[blk] = dict(per_dim=v, mean=float(np.mean(v)))
    for blk, j in INERT:
        if blk in t and t[blk].shape[1] > j:
            nonrec[f"{blk}[{j}]"] = dict(per_dim=[r2(t[blk][:, j].astype(np.float64))],
                                         mean=r2(t[blk][:, j].astype(np.float64)))

    rec_mean = float(np.mean([v["mean"] for v in rec.values()])) if rec else float("nan")
    non_mean = float(np.mean([v["mean"] for v in nonrec.values()])) if nonrec else float("nan")
    detect = bool(rec_mean >= RECOVERABLE_FLOOR)
    reject = bool(all(abs(v["mean"]) <= NULL_BAND for v in nonrec.values()))
    separated = bool((rec_mean - non_mean) >= SEPARATION_MIN)

    return dict(
        schema="V77_AREPLICA_CONTROL_STATISTIC_RESULT_V1",
        statistic="UNSUPERVISED_PCA_READOUT__NO_PLANTED_MODULE_SUPPORT_REQUIRED",
        n_components=N_COMPONENTS, n_cells=n, n_addresses=X.shape[1],
        recoverable=rec, not_recoverable=nonrec,
        recoverable_mean=rec_mean, not_recoverable_mean=non_mean,
        thresholds=dict(recoverable_floor=RECOVERABLE_FLOOR, null_band=NULL_BAND,
                        separation_min=SEPARATION_MIN),
        DETECT=detect, REJECT=reject, SEPARATED=separated,
        VERDICT=("PASS" if (detect and reject and separated) else "FAIL"),
        ceiling_label="this is a CONTROL, not a ceiling; it asserts readability and leak-freedom only")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--obs-dir", default="FULLSCALE_V2_CANONICAL_sharded")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    r = evaluate(Path(a.root), a.obs_dir)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps({k: r[k] for k in ("VERDICT", "DETECT", "REJECT", "SEPARATED",
                                        "recoverable_mean", "not_recoverable_mean")}, indent=2))


if __name__ == "__main__":
    main()
