"""PART 1.1 - source-specific within-operator recurrence, validated estimator.

Uncertainty is a donor-cluster bootstrap of the OOF R2 STATISTIC with the fitted
models held fixed. It captures evaluation-sample variability only; it does NOT
propagate refit variability, and it carries no acceptance authority.
"""
import numpy as np, pandas as pd, json, pathlib
S = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
LAM = 1e-2; NF = 5; B = 1000
z = np.load(S / 'screen_out.npz')
fm = pd.read_csv(S / 'final_manifest.csv', usecols=['donor_id', 'operator_index', 'source', 'stratum'])
base = (fm.stratum == 'BASE_MECHANICS').values
V0 = np.asarray(z['p100_v0'][base], dtype=np.float64)
V1 = np.asarray(z['p100_v1'][base], dtype=np.float64)
dser = fm.donor_id[base].to_numpy(); oser = fm.operator_index[base].to_numpy(); sser = fm.source[base].to_numpy()

print('=== FEASIBILITY: per-source support for donor-held-out operator-centring ===')
print('%-8s %9s %8s %10s %14s' % ('source', 'cells', 'donors', 'operators', 'donors/fold'))
for s in ['HVS', 'NPH52', 'SEA_AD']:
    m = sser == s
    nd = pd.unique(dser[m]).size
    print('%-8s %9d %8d %10d %14.1f' % (s, int(m.sum()), nd, pd.unique(oser[m]).size, nd / NF))
print()


def fit_oof(A, Y, lv, fold):
    """Returns per-row squared error and the OOF-centred target, models fit per fold."""
    K = 1 if lv is None else int(lv.max()) + 1
    se = np.zeros(len(A)); Yc = np.zeros_like(Y)
    for f in range(NF):
        te = fold == f; tr = ~te
        if tr.sum() < 50 or te.sum() < 5:
            se[te] = np.nan; continue
        if lv is None:
            A_tr, A_te, Y_tr, Y_te = A[tr], A[te], Y[tr], Y[te]
        else:
            def bm(X):
                s_ = np.zeros((K, X.shape[1])); c = np.zeros(K)
                np.add.at(s_, lv[tr], X[tr]); np.add.at(c, lv[tr], 1)
                g = X[tr].mean(0)
                return np.where(c[:, None] > 0, s_ / np.maximum(c, 1)[:, None], g)
            m0, m1 = bm(A), bm(Y)
            A_tr = A[tr] - m0[lv[tr]]; A_te = A[te] - m0[lv[te]]
            Y_tr = Y[tr] - m1[lv[tr]]; Y_te = Y[te] - m1[lv[te]]
        mu = A_tr.mean(0); sd = np.maximum(A_tr.std(0), 1e-12)
        As = (A_tr - mu) / sd; muB = Y_tr.mean(0)
        w = np.linalg.solve(As.T @ As + LAM * len(As) * np.eye(As.shape[1]), As.T @ (Y_tr - muB))
        r = Y_te - (((A_te - mu) / sd) @ w + muB)
        se[te] = (r * r).sum(1); Yc[te] = Y_te
    return se, Yc


def r2_and_boot(se, Yc, don_codes, rng):
    ok = ~np.isnan(se)
    se, Yc, dc = se[ok], Yc[ok], don_codes[ok]
    gm = Yc.mean(0); sst_row = ((Yc - gm) ** 2).sum(1)
    r2 = 1 - se.sum() / sst_row.sum()
    uniq = np.unique(dc)
    idx = {d: np.where(dc == d)[0] for d in uniq}
    a = np.array([se[idx[d]].sum() for d in uniq]); b = np.array([sst_row[idx[d]].sum() for d in uniq])
    draws = rng.integers(0, len(uniq), size=(B, len(uniq)))
    bs = 1 - a[draws].sum(1) / b[draws].sum(1)
    return r2, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


rng = np.random.default_rng(20260915)
res = {}
print('=== WITHIN-OPERATOR CROSS-VIEW RECURRENCE BY SOURCE ===')
print('%-8s %9s %7s %6s %9s %22s %22s' % ('source', 'cells', 'donors', 'ops', 'ESS(don)', 'raw R2 [95% boot]', 'op-centred R2 [95%]'))
for s in ['ALL', 'HVS', 'NPH52', 'SEA_AD']:
    m = np.ones(len(V0), bool) if s == 'ALL' else (sser == s)
    dc = pd.factorize(dser[m])[0]; oc = pd.factorize(oser[m])[0]
    fold = (dc % NF).astype(np.int8)
    A, Y = V0[m], V1[m]
    se_r, Yc_r = fit_oof(A, Y, None, fold)
    se_o, Yc_o = fit_oof(A, Y, oc, fold)
    r_raw, lo_r, hi_r = r2_and_boot(se_r, Yc_r, dc, rng)
    r_op, lo_o, hi_o = r2_and_boot(se_o, Yc_o, dc, rng)
    nd = int(dc.max() + 1)
    res[s] = dict(cells=int(m.sum()), donors=nd, operators=int(oc.max() + 1),
                  raw_r2=r_raw, raw_ci=[lo_r, hi_r], op_centred_r2=r_op, op_centred_ci=[lo_o, hi_o],
                  retained_fraction=r_op / r_raw if r_raw > 0 else None)
    print('%-8s %9d %7d %6d %9d %10.4f [%.4f,%.4f] %10.4f [%.4f,%.4f]'
          % (s, int(m.sum()), nd, oc.max() + 1, nd, r_raw, lo_r, hi_r, r_op, lo_o, hi_o))
print()
print('%-8s %s' % ('source', 'fraction of cross-view signal surviving operator-centring'))
for s in ['ALL', 'HVS', 'NPH52', 'SEA_AD']:
    f = res[s]['retained_fraction']
    print('  %-8s %6.1f%%' % (s, 100 * f))
json.dump(res, open(S / 'y_source.json', 'w'), indent=2, sort_keys=True)
print('SOURCE_DONE')
