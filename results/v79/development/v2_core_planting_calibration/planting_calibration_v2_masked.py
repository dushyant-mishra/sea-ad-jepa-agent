"""DEVELOPMENT ONLY (V2, structural-support masked). Realistic per-gene magnitudes for planting V2_CORE qualification
worlds from the authenticated G500 compact cache, using ONLY structurally measured cells (Stage81A2R matrix-level
measurement support joined through the S174 operator bridge). Supersedes V1 (Z), which treated 5.8% structurally
unmeasured cell-gene entries as measured zeros. Same proxy fits as V1: detection logistic / positive lognormal ridge
on intercept, z, z^2-1, normalized-Helmert class and source contrasts, within-source Helmert donor basis (ridge 1).
Source contrasts and intercepts are summarized only over genes measured in all three sources."""
import hashlib, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, "D:/v79_runs/02fb78c3/scripts/v79")
import run_v79_s174_structure_replay as R
CACHE = Path("D:/v79_runs/615b55eb/results/v79/development/s174_structure_replay/V79_ANALYSIS_CACHE_G500.npz")
d = R.load_compact_cache(CACHE, CACHE.with_name("V79_ANALYSIS_CACHE_G500_RECEIPT.json"))
SUP = json.load(open("V79_G500_STRUCTURAL_SUPPORT_DEV.json"))
M = np.load("V79_G500_STRUCTURAL_SUPPORT_OPxGENE.npy")
assert hashlib.sha256(np.ascontiguousarray(M).tobytes()).hexdigest() == SUP["op_x_gene_sha256"]
ops = np.array(SUP["operators"]); cellmask = M[np.searchsorted(ops, d["op"])]

def stz(k):
    B = np.zeros((k, k - 1))
    for j in range(1, k):
        B[:j, j - 1] = 1.0; B[j, j - 1] = -j; B[:, j - 1] /= np.sqrt(j * (j + 1))
    return B
L = d["log_lib_centered"].astype(float); LOGLIB_SD = float(L.std())
x = (L - L.mean()) / LOGLIB_SD; qd = x * x - 1.0
Bc = stz(3); C = np.eye(3)[d["cls"]] @ Bc; S = np.eye(3)[d["src"]] @ Bc
donors = np.unique(d["donor"]); src_of = {int(k): int(d["src"][d["donor"] == k][0]) for k in donors}
cols = []
for s in range(3):
    ds = [k for k in donors if src_of[int(k)] == s]; B = stz(len(ds))
    for j in range(B.shape[1]):
        v = np.zeros(len(d["donor"]))
        for i, k in enumerate(ds): v[d["donor"] == k] = B[i, j]
        cols.append(v)
U = np.column_stack(cols); X = np.column_stack([np.ones_like(x), x, qd, C, S, U]); nf = 7
pen = np.r_[0.0, np.full(nf - 1, R.RIDGE), np.full(U.shape[1], 1.0)]
def donor_sd(bu, keep):
    eff = U @ bu
    return float(np.std([eff[(d["donor"] == k) & keep][0] for k in donors if ((d["donor"] == k) & keep).any()]))
rows = []
for g in range(d["counts_selected"].shape[1]):
    m = cellmask[:, g]; full3 = all(m[d["src"] == s].any() for s in range(3))
    keepcols = np.r_[np.ones(nf, bool), np.array([m[U[:, j] != 0].any() for j in range(U.shape[1])])]
    c = d["counts_selected"][m, g].astype(float); y = (c > 0).astype(float); Xg = X[m][:, keepcols]; pg = pen[keepcols]
    if not full3:   # an unmeasured source leaves its contrasts unidentified: drop source columns, keep the rest
        keep_fixed = np.r_[np.ones(5, bool), np.zeros(2, bool), np.ones(Xg.shape[1] - nf, bool)]
        Xg, pg = Xg[:, keep_fixed], pg[keep_fixed]
    b = R._logistic_fit(Xg, y, penalty=pg)
    rec = dict(gene_position=g, measured_fraction=float(m.mean()), all_sources_measured=bool(full3), prevalence=float(y.mean()),
               det=dict(intercept=float(b[0]), depth=float(b[1]), depth2=float(b[2]), cls=b[3:5].tolist(),
                        **({"src": b[5:7].tolist()} if full3 else {})))
    bu = np.zeros(U.shape[1]); bu[keepcols[nf:]] = b[(nf if full3 else 5):]
    rec["det"]["donor_sd"] = donor_sd(bu, m)
    pos = c > 0
    if pos.sum() > Xg.shape[1] + 5:
        Xp = Xg[pos]; zz = np.log(c[pos]); bp = np.linalg.solve(Xp.T @ Xp + np.diag(pg), Xp.T @ zz); r = zz - Xp @ bp
        bup = np.zeros(U.shape[1]); bup[keepcols[nf:]] = bp[(nf if full3 else 5):]
        rec["pos"] = dict(intercept=float(bp[0]), depth=float(bp[1]), depth2=float(bp[2]), cls=bp[3:5].tolist(),
                          **({"src": bp[5:7].tolist()} if full3 else {}), donor_sd=donor_sd(bup, m),
                          sigma=float(np.sqrt(np.mean(r * r))), n_positive=int(pos.sum()))
    rows.append(rec)
P = (0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99)
def q(v): v = np.asarray(v, float); return {str(p): float(np.quantile(v, p)) for p in P}
summ = {}
for part in ("det", "pos"):
    R_ = [r for r in rows if part in r]; F = [r for r in R_ if r["all_sources_measured"]]
    summ[part] = dict(n=len(R_), n_all_sources=len(F), intercept_all_sources=q([r[part]["intercept"] for r in F]),
                      depth=q([r[part]["depth"] for r in R_]), depth2=q([r[part]["depth2"] for r in R_]),
                      abs_cls=q([abs(v) for r in R_ for v in r[part]["cls"]]), abs_src=q([abs(v) for r in F for v in r[part]["src"]]),
                      donor_sd=q([r[part]["donor_sd"] for r in R_]),
                      **({"sigma": q([r[part]["sigma"] for r in R_])} if part == "pos" else {}))
summ["prevalence_measured_cells"] = q([r["prevalence"] for r in rows])
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
out = dict(schema="V79_V2_CORE_PLANTING_CALIBRATION_MASKED_V2", status="DEVELOPMENT_ONLY__PLANTING_MAGNITUDES_FOR_NEW_WORLDS",
           supersedes="V79_V2_CORE_PLANTING_CALIBRATION_Z_V1 (treated structurally unmeasured entries as measured zeros)",
           cache_sha256=sha(CACHE), structural_support=dict(record_sha256=sha("V79_G500_STRUCTURAL_SUPPORT_DEV.json"), op_x_gene_sha256=SUP["op_x_gene_sha256"],
           support_authority_sha256=SUP["support_sha256"], bridge_sha256=SUP["bridge_sha256"]),
           code_snapshot="02fb78c36473d9863ae9482619133c052ba4a480", loglib_sd=LOGLIB_SD, method=__doc__, n_genes=len(rows),
           summary=summ, per_gene=rows)
Path("V79_V2_CORE_PLANTING_CALIBRATION_MASKED_V2.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(json.dumps(summ, indent=0))
