"""Within-batch cross-view signal, done correctly.

For each donor-held-out fold: estimate batch means from TRAINING rows only, subtract
the SAME means from training and test rows, fit ridge, evaluate out of fold.

Donor-centring is NOT identifiable here: under donor-held-out CV a test donor has no
training rows, so its donor mean cannot be estimated. It is excluded by construction,
not dropped after seeing a result.
"""
import numpy as np, pandas as pd, json, pathlib
S = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
LAM = 1e-2; NF = 5
z = np.load(S / 'screen_out.npz')
fm = pd.read_csv(S / 'final_manifest.csv', usecols=['donor_id', 'operator_index', 'source', 'stratum'])
base = (fm.stratum == 'BASE_MECHANICS').values
don = pd.factorize(fm.donor_id)[0][base]
fold = (don % NF).astype(np.int8)
op = pd.factorize(fm.operator_index[base])[0]
src = pd.factorize(fm.source[base])[0]
V0 = np.asarray(z['p100_v0'][base], dtype=np.float64)
V1 = np.asarray(z['p100_v1'][base], dtype=np.float64)


def batch_means(X, lv, rows, K):
    s = np.zeros((K, X.shape[1])); c = np.zeros(K)
    np.add.at(s, lv[rows], X[rows]); np.add.at(c, lv[rows], 1)
    g = X[rows].mean(0)
    return np.where(c[:, None] > 0, s / np.maximum(c, 1)[:, None], g), int((c == 0).sum())


def run(lv):
    K = 1 if lv is None else int(lv.max()) + 1
    sse = 0.0; Yte_all = []; unseen = 0
    for f in range(NF):
        te = fold == f; tr = ~te
        if lv is None:
            A_tr, A_te, Y_tr, Y_te = V0[tr], V0[te], V1[tr], V1[te]
        else:
            m0, u0 = batch_means(V0, lv, tr, K)
            m1, u1 = batch_means(V1, lv, tr, K)
            unseen = max(unseen, u0)
            A_tr = V0[tr] - m0[lv[tr]]; A_te = V0[te] - m0[lv[te]]
            Y_tr = V1[tr] - m1[lv[tr]]; Y_te = V1[te] - m1[lv[te]]
        mu = A_tr.mean(0); sd = np.maximum(A_tr.std(0), 1e-12)
        As = (A_tr - mu) / sd
        muB = Y_tr.mean(0)
        w = np.linalg.solve(As.T @ As + LAM * len(As) * np.eye(As.shape[1]), As.T @ (Y_tr - muB))
        pred = ((A_te - mu) / sd) @ w + muB
        r = Y_te - pred
        sse += float((r * r).sum())
        Yte_all.append(Y_te)
    Y = np.vstack(Yte_all); gm = Y.mean(0)
    d = Y - gm
    return 1.0 - sse / float((d * d).sum()), unseen


res = {}
print('=== CROSS-VIEW R2 AFTER REMOVING BATCH MEAN STRUCTURE ===')
print('    batch means from TRAINING folds only; donor-held-out throughout')
print()
print('  %-36s %8s %10s' % ('level removed', 'R2', 'retained'))
raw, _ = run(None); res['raw'] = raw
print('  %-36s %8.4f %9.1f%%' % ('none (raw V0 -> V1)', raw, 100.0))
for lv, label, key in [(src, 'source (3 levels)', 'source'), (op, 'operator (42 levels)', 'operator')]:
    v, u = run(lv); res[key] = v
    print('  %-36s %8.4f %9.1f%%' % (label, v, 100 * v / raw))
    if u: print('      (levels unseen in some training fold: %d)' % u)
print()
print('  donor (94 levels)                    NOT IDENTIFIABLE under donor-held-out CV')
json.dump(res, open(S / 'x_within.json', 'w'), indent=2, sort_keys=True)
print('WITHIN_DONE')
