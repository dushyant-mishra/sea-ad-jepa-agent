"""DEVELOPMENT ONLY. Realistic per-gene magnitudes for planting V2_CORE qualification worlds, from the
authenticated G500 compact cache with the frozen cheap proxies (no NUTS, no identities, positions only).

Per gene (all 500 cache genes): detection logistic and positive lognormal ridge fits of the V2_CORE fixed structure
(intercept, depth, centred depth^2, class and source on orthonormal sum-to-zero contrasts) plus donor-within-source
effects as ridge-shrunk (lambda=1) coefficients on the within-source sum-to-zero basis; donor SD is the SD of those
shrunk donor effects (biased low: shrinkage). Positive residual sigma from the same fit."""
import hashlib, json, sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
sys.path.insert(0, "D:/v79_runs/02fb78c3/scripts/v79")
import run_v79_s174_structure_replay as R
CACHE = Path("D:/v79_runs/615b55eb/results/v79/development/s174_structure_replay/V79_ANALYSIS_CACHE_G500.npz")
REC = CACHE.with_name("V79_ANALYSIS_CACHE_G500_RECEIPT.json")
d = R.load_compact_cache(CACHE, REC)

def stz(k):  # normalized Helmert sum-to-zero basis, K x (K-1): column j = (1,...,1,-j,0,...)/sqrt(j(j+1))
    B = np.zeros((k, k - 1))
    for j in range(1, k):
        B[:j, j - 1] = 1.0; B[j, j - 1] = -j; B[:, j - 1] /= np.sqrt(j * (j + 1))
    return B

L = d["log_lib_centered"].astype(float)
LOGLIB_SD = float(L.std())                                   # population SD (ddof=0)
x = (L - L.mean()) / LOGLIB_SD; q = x * x - 1.0              # standardized depth and centred square (mean z^2 = 1)
Bc, Bs = stz(3), stz(3)
C = np.eye(3)[d["cls"]] @ Bc; S = np.eye(3)[d["src"]] @ Bs
donors = np.unique(d["donor"]); src_of = {int(k): int(d["src"][d["donor"] == k][0]) for k in donors}
cols = []
for s in range(3):
    ds = [k for k in donors if src_of[int(k)] == s]
    B = stz(len(ds))
    for j in range(B.shape[1]):
        v = np.zeros(len(d["donor"]))
        for i, k in enumerate(ds): v[d["donor"] == k] = B[i, j]
        cols.append(v)
U = np.column_stack(cols)                                   # within-source sum-to-zero donor basis
X = np.column_stack([np.ones_like(x), x, q, C, S, U])
nf = 1 + 2 + 2 + 2                                          # intercept, depth, depth^2, class(2), source(2)
pen = np.r_[0.0, np.full(nf - 1, R.RIDGE), np.full(U.shape[1], 1.0)]

def donor_sd(beta_u):  # SD of donor effects back on the donor scale
    eff = U @ beta_u
    return float(np.std([eff[d["donor"] == k][0] for k in donors]))

rows = []
for g in range(d["counts_selected"].shape[1]):
    c = d["counts_selected"][:, g].astype(float); y = (c > 0).astype(float)
    b = R._logistic_fit(X, y, penalty=pen)
    rec = dict(gene_position=g, prevalence=float(y.mean()),
               det=dict(intercept=float(b[0]), depth=float(b[1]), depth2=float(b[2]), cls=b[3:5].tolist(),
                        src=b[5:7].tolist(), donor_sd=donor_sd(b[nf:])))
    pos = c > 0
    if pos.sum() > X.shape[1] + 5:
        Xp = X[pos]; z = np.log(c[pos])
        bp = np.linalg.solve(Xp.T @ Xp + np.diag(pen), Xp.T @ z)
        r = z - Xp @ bp
        rec["pos"] = dict(intercept=float(bp[0]), depth=float(bp[1]), depth2=float(bp[2]), cls=bp[3:5].tolist(),
                          src=bp[5:7].tolist(), donor_sd=donor_sd(bp[nf:]), sigma=float(np.sqrt(np.mean(r * r))),
                          n_positive=int(pos.sum()))
    rows.append(rec)

def q(v): v = np.asarray(v, float); return {p: float(np.quantile(v, p)) for p in (0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99)}
summ = {}
for part in ("det", "pos"):
    R_ = [r[part] for r in rows if part in r]
    summ[part] = dict(n=len(R_), intercept=q([r["intercept"] for r in R_]), depth=q([r["depth"] for r in R_]),
                      depth2=q([r["depth2"] for r in R_]), abs_cls=q([abs(v) for r in R_ for v in r["cls"]]),
                      abs_src=q([abs(v) for r in R_ for v in r["src"]]), donor_sd=q([r["donor_sd"] for r in R_]),
                      **({"sigma": q([r["sigma"] for r in R_])} if part == "pos" else {}))
out = dict(schema="V79_V2_CORE_PLANTING_CALIBRATION_Z_V1", status="DEVELOPMENT_ONLY__PLANTING_MAGNITUDES_FOR_NEW_WORLDS",
           cache_sha256=hashlib.sha256(CACHE.read_bytes()).hexdigest(), code_snapshot="02fb78c36473d9863ae9482619133c052ba4a480", depth_covariate="z = standardized log library (ddof=0); quadratic term z^2 - 1", loglib_sd=LOGLIB_SD, contrast_basis="normalized Helmert",
           method=__doc__, donor_ridge_lambda=1.0, n_genes=len(rows), summary=summ, per_gene=rows)
Path("D:/v79_runs/v2core_dev/V79_V2_CORE_PLANTING_CALIBRATION_Z.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(json.dumps(summ, indent=1))
