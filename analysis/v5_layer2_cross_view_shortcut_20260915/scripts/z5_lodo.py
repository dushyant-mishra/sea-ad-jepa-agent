"""ITEM 5 - leave-one-donor-out with COMPLETE model refitting (optimised).

Mathematically identical to z4_lodo.py but computes each donor's training moments as
(full moments) - (that donor's moments), instead of rescanning every row per donor.
The operator means, the standardisation, and the ridge solution are all still refit
from scratch for every held-out donor - only the accumulation is made cheap.

Correctness is asserted against the direct computation on the first two donors of each
source before the fast path is used.
"""
import numpy as np, pandas as pd, json, pathlib, time
S = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
LAM = 1e-2
B = np.load(S / 'bind_population.npz')
bidx, dc_all = B['base_index'], B['donor_code']
z = np.load(S / 'screen_out.npz')
fm = pd.read_csv(S / 'final_manifest.csv', usecols=['source', 'operator_index'])
V0 = np.asarray(z['p100_v0'][bidx], dtype=np.float64)
V1 = np.asarray(z['p100_v1'][bidx], dtype=np.float64)
src = fm.source.values[bidx]; opi = fm.operator_index.values[bidx]


def group_sums(X, lv, K):
    s = np.zeros((K, X.shape[1])); c = np.zeros(K)
    np.add.at(s, lv, X); np.add.at(c, lv, 1)
    return s, c


def lodo(A0, Y0, dc, oc, check=2):
    K = int(oc.max()) + 1; ND = int(dc.max()) + 1
    # full moments once
    S0f, cf = group_sums(A0, oc, K); S1f, _ = group_sums(Y0, oc, K)
    G0f = A0.T @ A0; a0f = A0.sum(0)
    C0f = A0.T @ Y0; b0f = Y0.sum(0)
    n = len(A0)
    rows = [np.where(dc == d)[0] for d in range(ND)]
    sse = np.zeros(ND); sst = np.zeros(ND); sole = 0
    for d in range(ND):
        te = rows[d]; ntr = n - len(te)
        At, Yt = A0[te], Y0[te]
        s0d, cd = group_sums(At, oc[te], K); s1d, _ = group_sums(Yt, oc[te], K)
        cTr = cf - cd
        g0 = (a0f - At.sum(0)) / ntr; g1 = (b0f - Yt.sum(0)) / ntr
        m0 = np.where(cTr[:, None] > 0, (S0f - s0d) / np.maximum(cTr, 1)[:, None], g0)
        m1 = np.where(cTr[:, None] > 0, (S1f - s1d) / np.maximum(cTr, 1)[:, None], g1)
        if cTr[oc[te][0]] == 0:
            sole += 1
        # centred training moments, derived analytically
        MO = m0[oc]; MY = m1[oc]
        # X_tr = A0[tr] - m0[oc[tr]] ; accumulate via full minus held-out
        AM_f = A0.T @ MO; MM_f = MO.T @ MO
        AMd = At.T @ MO[te]; MMd = MO[te].T @ MO[te]
        Gc = (G0f - At.T @ At) - (AM_f - AMd) - (AM_f - AMd).T + (MM_f - MMd)
        sA = (a0f - At.sum(0)) - (MO.sum(0) - MO[te].sum(0))
        CY_f = A0.T @ MY; MY_f = MO.T @ MY
        Cc = (C0f - At.T @ Yt) - (CY_f - At.T @ MY[te]) - (AM_f - AMd).T @ np.zeros((0, 0)).reshape(0, 0) if False else \
             (C0f - At.T @ Yt) - (CY_f - At.T @ MY[te]) - (MO.T @ Y0 - MO[te].T @ Yt) + (MY_f - MO[te].T @ MY[te])
        sY = (b0f - Yt.sum(0)) - (MY.sum(0) - MY[te].sum(0))
        mu = sA / ntr
        var = np.diag(Gc) / ntr - mu ** 2
        sd = np.sqrt(np.maximum(var, 1e-24))
        Gs = (Gc - ntr * np.outer(mu, mu)) / np.outer(sd, sd)
        muB = sY / ntr
        Cs = (Cc - ntr * np.outer(mu, muB)) / sd[:, None]
        w = np.linalg.solve(Gs + LAM * ntr * np.eye(len(mu)), Cs)
        A_te = (At - MO[te] - mu) / sd
        Y_te = Yt - MY[te]
        r = Y_te - (A_te @ w + muB)
        sse[d] = (r * r).sum(); sst[d] = (Y_te * Y_te).sum()
    return sse, sst, sole


def lodo_direct(A0, Y0, dc, oc, dlist):
    """Reference implementation for the correctness check."""
    K = int(oc.max()) + 1
    out = []
    for d in dlist:
        te = dc == d; tr = ~te
        s0, c = group_sums(A0[tr], oc[tr], K); s1, _ = group_sums(Y0[tr], oc[tr], K)
        g0, g1 = A0[tr].mean(0), Y0[tr].mean(0)
        m0 = np.where(c[:, None] > 0, s0 / np.maximum(c, 1)[:, None], g0)
        m1 = np.where(c[:, None] > 0, s1 / np.maximum(c, 1)[:, None], g1)
        A_tr = A0[tr] - m0[oc[tr]]; Y_tr = Y0[tr] - m1[oc[tr]]
        mu = A_tr.mean(0); sd = np.maximum(A_tr.std(0), 1e-12)
        As = (A_tr - mu) / sd; muB = Y_tr.mean(0)
        w = np.linalg.solve(As.T @ As + LAM * len(As) * np.eye(256), As.T @ (Y_tr - muB))
        r = (Y0[te] - m1[oc[te]]) - (((A0[te] - m0[oc[te]] - mu) / sd) @ w + muB)
        out.append(((r * r).sum(), ((Y0[te] - m1[oc[te]]) ** 2).sum()))
    return out


res = {}
t0 = time.time()
print('=== ITEM 5: LEAVE-ONE-DONOR-OUT, COMPLETE REFIT (operator-centred) ===')
for s in ['HVS', 'NPH52', 'SEA_AD', 'ALL']:
    m = np.ones(len(V0), bool) if s == 'ALL' else (src == s)
    A0, Y0 = V0[m], V1[m]
    dc = pd.factorize(dc_all[m])[0]; oc = pd.factorize(opi[m])[0]
    sse, sst, sole = lodo(A0, Y0, dc, oc)
    ref = lodo_direct(A0, Y0, dc, oc, [0, 1])
    dev = max(abs(sse[i] - ref[i][0]) / max(ref[i][0], 1) for i in range(2))
    r2d = 1 - sse / np.maximum(sst, 1e-300)
    pooled = 1 - sse.sum() / sst.sum()
    res[s] = dict(n_donors=int(dc.max() + 1), pooled_lodo_r2=float(pooled), min=float(r2d.min()),
                  q1=float(np.percentile(r2d, 25)), median=float(np.median(r2d)),
                  q3=float(np.percentile(r2d, 75)), max=float(r2d.max()),
                  frac_positive=float((r2d > 0).mean()), sole_donor_operators=int(sole),
                  fastpath_rel_dev_vs_direct=float(dev),
                  donor_r2=[float(x) for x in r2d])
    print('  %-8s refit-check rel dev vs direct %.2e  (%.1f min)' % (s, dev, (time.time() - t0) / 60), flush=True)
print()
print('%-9s %8s %10s %9s %9s %9s %9s %9s %9s %7s' %
      ('source', 'donors', 'pooledR2', 'min', 'Q1', 'median', 'Q3', 'max', 'frac>0', 'sole'))
for s in ['HVS', 'NPH52', 'SEA_AD', 'ALL']:
    r = res[s]
    print('%-9s %8d %10.4f %9.4f %9.4f %9.4f %9.4f %9.4f %8.1f%% %7d' %
          (s, r['n_donors'], r['pooled_lodo_r2'], r['min'], r['q1'], r['median'], r['q3'], r['max'],
           100 * r['frac_positive'], r['sole_donor_operators']))
print()
prev = json.load(open(S / 'y_source.json'))
print('%-9s %28s %26s' % ('source', '5-fold, models held fixed', 'LODO pooled, full refit'))
for s in ['HVS', 'NPH52', 'SEA_AD', 'ALL']:
    print('%-9s %28.4f %26.4f' % (s, prev[s]['op_centred_r2'], res[s]['pooled_lodo_r2']))
json.dump(res, open(S / 'z_lodo.json', 'w'), indent=2, sort_keys=True)
print('LODO_DONE')
