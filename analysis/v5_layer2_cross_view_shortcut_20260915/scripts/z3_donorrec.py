"""ITEM 4 - donor-level recurrence of the within-donor relation.

Design: donor-centred, CELL-held-out (validated earlier: donor-structure-only fixture -> -0.0019).
For each donor, report that donor's held-out contribution under the COMMON model:
    R2_d = 1 - sum_{i in d} ||y_i - yhat_i||^2 / sum_{i in d} ||y_i||^2
on the donor-centred target. Descriptive only; no pass threshold.
"""
import numpy as np, pandas as pd, json, pathlib
S = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
LAM = 1e-2; NF = 5
B = np.load(S / 'bind_population.npz')
bidx, fold_c, dc = B['base_index'], B['fold_cell'], B['donor_code']
z = np.load(S / 'screen_out.npz')
fm = pd.read_csv(S / 'final_manifest.csv', usecols=['source', 'donor_id'])
V0 = np.asarray(z['p100_v0'][bidx], dtype=np.float64)
V1 = np.asarray(z['p100_v1'][bidx], dtype=np.float64)
src = fm.source.values[bidx]
K = int(dc.max()) + 1
sse_d = np.zeros(K); sst_d = np.zeros(K); n_d = np.zeros(K, int)
for f in range(NF):
    te = fold_c == f; tr = ~te
    def bm(X):
        s_ = np.zeros((K, X.shape[1])); c = np.zeros(K)
        np.add.at(s_, dc[tr], X[tr]); np.add.at(c, dc[tr], 1)
        g = X[tr].mean(0)
        return np.where(c[:, None] > 0, s_ / np.maximum(c, 1)[:, None], g)
    m0, m1 = bm(V0), bm(V1)
    A_tr = V0[tr] - m0[dc[tr]]; A_te = V0[te] - m0[dc[te]]
    Y_tr = V1[tr] - m1[dc[tr]]; Y_te = V1[te] - m1[dc[te]]
    mu = A_tr.mean(0); sd = np.maximum(A_tr.std(0), 1e-12)
    As = (A_tr - mu) / sd; muB = Y_tr.mean(0)
    w = np.linalg.solve(As.T @ As + LAM * len(As) * np.eye(As.shape[1]), As.T @ (Y_tr - muB))
    r = Y_te - (((A_te - mu) / sd) @ w + muB)
    np.add.at(sse_d, dc[te], (r * r).sum(1))
    np.add.at(sst_d, dc[te], (Y_te * Y_te).sum(1))
    np.add.at(n_d, dc[te], 1)
ok = (n_d >= 30) & (sst_d > 0)
r2d = np.full(K, np.nan); r2d[ok] = 1 - sse_d[ok] / sst_d[ok]
dsrc = np.array([src[dc == k][0] for k in range(K)])
print('=== ITEM 4: DONOR-LEVEL RECURRENCE (within-donor design, common model) ===')
print('  donors total %d ; evaluable (>=30 held-out cells) %d ; excluded %d'
      % (K, int(ok.sum()), int((~ok).sum())))
print()
print('%-9s %8s %9s %9s %9s %9s %9s %12s' % ('source', 'donors', 'min', 'Q1', 'median', 'Q3', 'max', 'frac > 0'))
out = {}
for s in ['ALL', 'HVS', 'NPH52', 'SEA_AD']:
    m = ok if s == 'ALL' else (ok & (dsrc == s))
    v = r2d[m]
    out[s] = dict(n_donors=int(m.sum()), min=float(v.min()), q1=float(np.percentile(v, 25)),
                  median=float(np.median(v)), q3=float(np.percentile(v, 75)), max=float(v.max()),
                  frac_positive=float((v > 0).mean()), frac_above_0p05=float((v > 0.05).mean()),
                  frac_above_0p10=float((v > 0.10).mean()))
    print('%-9s %8d %9.4f %9.4f %9.4f %9.4f %9.4f %11.1f%%'
          % (s, m.sum(), v.min(), np.percentile(v, 25), np.median(v), np.percentile(v, 75), v.max(),
             100 * (v > 0).mean()))
print()
print('%-9s %14s %14s' % ('source', 'frac > 0.05', 'frac > 0.10'))
for s in ['ALL', 'HVS', 'NPH52', 'SEA_AD']:
    print('%-9s %13.1f%% %13.1f%%' % (s, 100 * out[s]['frac_above_0p05'], 100 * out[s]['frac_above_0p10']))
json.dump({'per_source': out, 'donor_r2': {str(i): (None if np.isnan(r2d[i]) else float(r2d[i]))
                                           for i in range(K)}},
          open(S / 'z_donorrec.json', 'w'), indent=2, sort_keys=True)
print('DONORREC_DONE')
