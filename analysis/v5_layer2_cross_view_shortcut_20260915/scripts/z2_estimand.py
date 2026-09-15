"""ITEM 3 - estimand sensitivity. Same core quantities under three separately-reported
scientific weightings plus the unweighted reconnaissance view. Never combined.

Weights are the Horvitz-Thompson weights already audited for the BASE probability sample
(q_i = min(12,B_o)/B_o, content-independence proven by reproduction). Weighted ridge:
   (X'WX + lam*sum(w)*I) beta = X'W y ;  R2_w = 1 - sum w(y-yhat)^2 / sum w(y-ybar_w)^2
"""
import numpy as np, pandas as pd, json, pathlib
S = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
LAM = 1e-2; NF = 5
B = np.load(S / 'bind_population.npz')
bidx, fold_d, fold_c, dc = B['base_index'], B['fold_donor'], B['fold_cell'], B['donor_code']
z = np.load(S / 'screen_out.npz'); q = np.load(S / 'qc_post.npz')
fm = pd.read_csv(S / 'final_manifest.csv', usecols=['source', 'operator_index'])
V0 = np.asarray(z['p100_v0'][bidx], dtype=np.float64)
V1 = np.asarray(z['p100_v1'][bidx], dtype=np.float64)
L = np.log1p(q['lib_p100'][bidx].astype(np.float64)); Dt = np.log1p(q['det_p100'][bidx].astype(np.float64))
Q = np.column_stack([L, Dt, L ** 2, Dt ** 2, L * Dt])
CTX = np.column_stack([Q, pd.get_dummies(fm.source.values[bidx]).to_numpy(float),
                       pd.get_dummies(fm.operator_index.values[bidx]).to_numpy(float)])
W = {'UNWEIGHTED_RECON': np.ones(len(bidx)),
     'EMPIRICAL_FULL104_STRUCTURE': np.load(S / 'w_base_A.npy'),
     'SOURCE_UNIFORM_CELL_WITHIN_SOURCE': np.load(S / 'w_base_B.npy'),
     'DONOR_PRIMARY_OPERATOR_BALANCED': np.load(S / 'w_base_C.npy')}
ESS = {'UNWEIGHTED_RECON': 196817, 'EMPIRICAL_FULL104_STRUCTURE': 61374,
       'SOURCE_UNIFORM_CELL_WITHIN_SOURCE': 96338, 'DONOR_PRIMARY_OPERATOR_BALANCED': 34726}


def wr2(A, Y, w, fold, lv=None):
    sse = 0.0; Ys = []; Ws = []
    K = 1 if lv is None else int(lv.max()) + 1
    for f in range(NF):
        te = fold == f; tr = ~te
        wt = w[tr]; sw = wt.sum()
        if lv is None:
            A_tr, A_te, Y_tr, Y_te = A[tr], A[te], Y[tr], Y[te]
        else:
            def bm(X):
                s_ = np.zeros((K, X.shape[1])); c = np.zeros(K)
                np.add.at(s_, lv[tr], X[tr] * wt[:, None]); np.add.at(c, lv[tr], wt)
                g = (X[tr] * wt[:, None]).sum(0) / sw
                return np.where(c[:, None] > 0, s_ / np.maximum(c, 1e-300)[:, None], g)
            m0, m1 = bm(A), bm(Y)
            A_tr = A[tr] - m0[lv[tr]]; A_te = A[te] - m0[lv[te]]
            Y_tr = Y[tr] - m1[lv[tr]]; Y_te = Y[te] - m1[lv[te]]
        mu = (A_tr * wt[:, None]).sum(0) / sw
        var = (A_tr ** 2 * wt[:, None]).sum(0) / sw - mu ** 2
        sd = np.sqrt(np.maximum(var, 1e-24))
        As = (A_tr - mu) / sd
        muB = (Y_tr * wt[:, None]).sum(0) / sw
        G = As.T @ (As * wt[:, None]) + LAM * sw * np.eye(A.shape[1])
        beta = np.linalg.solve(G, As.T @ ((Y_tr - muB) * wt[:, None]))
        r = Y_te - (((A_te - mu) / sd) @ beta + muB)
        sse += float((w[te][:, None] * r * r).sum()); Ys.append(Y_te); Ws.append(w[te])
    Yv = np.vstack(Ys); wv = np.concatenate(Ws)
    gm = (Yv * wv[:, None]).sum(0) / wv.sum()
    d = Yv - gm
    return 1.0 - sse / float((wv[:, None] * d * d).sum())


rows = []
print('=== ITEM 3: ESTIMAND SENSITIVITY (views reported separately, never combined) ===')
print('%-34s %9s %9s %9s %9s %11s %12s' % ('estimand', 'ESS', 'ctx R2', 'V0 R2', 'both', 'mol incr', 'within-donor'))
for nm, w in W.items():
    a = wr2(CTX, V1, w, fold_d)
    b = wr2(V0, V1, w, fold_d)
    c = wr2(np.column_stack([CTX, V0]), V1, w, fold_d)
    d = wr2(V0, V1, w, fold_c, lv=dc)
    rows.append(dict(estimand=nm, kish_ess=ESS[nm], context_only_r2=a, v0_only_r2=b,
                     combined_r2=c, molecular_increment_over_context=c - a, within_donor_molecular_r2=d))
    print('%-34s %9d %9.4f %9.4f %9.4f %+11.4f %12.4f' % (nm[:34], ESS[nm], a, b, c, c - a, d))
json.dump(rows, open(S / 'z_estimand.json', 'w'), indent=2, sort_keys=True)
print()
print('  Qualitative conclusions to check for survival across all four views:')
print('   (i)  context alone is comparable to the whole molecular view        ',
      all(abs(r['context_only_r2'] - r['v0_only_r2']) < 0.10 for r in rows))
print('   (ii) molecular increment over context is positive but small         ',
      all(0 < r['molecular_increment_over_context'] < 0.15 for r in rows))
print('   (iii) within-donor molecular signal is substantial (>0.10)          ',
      all(r['within_donor_molecular_r2'] > 0.10 for r in rows))
print('ESTIMAND_DONE')
