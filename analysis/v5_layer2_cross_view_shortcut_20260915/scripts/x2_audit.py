"""Cross-view measurement-shortcut audit. Executes X_CROSS_VIEW_SHORTCUT_AUDIT_SPEC.json
(sha256 b280a1ed40127ec08e493deb2096c50c0734d76152405e6a32cf1b5cddc490e7) exactly."""
import numpy as np, pandas as pd, json, pathlib, time
S = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
PS = [100, 90, 75, 50, 25]
LAM = 1e-2
NF = 5

z = np.load(S / 'screen_out.npz')
q = np.load(S / 'qc_post.npz')
fm = pd.read_csv(S / 'final_manifest.csv', usecols=['donor_id', 'stratum'])
base = (fm.stratum == 'BASE_MECHANICS').values

# cells estimable at EVERY p, both views
ok = base.copy()
for p in PS:
    for v in (0, 1):
        ok &= ~np.isnan(z['p%d_v%d' % (p, v)][:, 0])
print('BASE cells %d ; estimable at every p in both views %d ; dropped %d'
      % (int(base.sum()), int(ok.sum()), int(base.sum() - ok.sum())), flush=True)

don = pd.factorize(fm.donor_id)[0]
fold = (don[ok] % NF).astype(np.int8)
n = int(ok.sum())
X = {}
for p in PS:
    for v in (0, 1):
        X[(v, p)] = np.ascontiguousarray(z['p%d_v%d' % (p, v)][ok], dtype=np.float32)
print('arrays loaded', flush=True)
SC = {}
for p in PS:
    SC[('L', p)] = np.log1p(q['lib_p%d' % p][ok].astype(np.float64))
    SC[('D', p)] = np.log1p(q['det_p%d' % p][ok].astype(np.float64))

D = 256
I = np.eye(D)


def moments(A, B=None):
    """float64 A.T@A (or A.T@B) and column sums, chunked."""
    G = np.zeros((A.shape[1], A.shape[1] if B is None else B.shape[1]))
    s = np.zeros(A.shape[1])
    for b in range(0, len(A), 32768):
        a = np.asarray(A[b:b + 32768], dtype=np.float64)
        G += a.T @ (a if B is None else np.asarray(B[b:b + 32768], dtype=np.float64))
        s += a.sum(0)
    return G, s


t0 = time.time()
Gf, s1f = {}, {}
for k in X:
    Gf[k], s1f[k] = moments(X[k])
Cf = {}
for pi in PS:
    for pj in PS:
        Cf[(pi, pj)] = moments(X[(0, pi)], X[(1, pj)])[0]
print('full moments %.1f min' % ((time.time() - t0) / 60), flush=True)

Gt, s1t, Ct, NT = {}, {}, {}, {}
for f in range(NF):
    m = fold == f
    NT[f] = int(m.sum())
    for k in X:
        Gt[(k, f)], s1t[(k, f)] = moments(X[k][m])
    for pi in PS:
        for pj in PS:
            Ct[(pi, pj, f)] = moments(X[(0, pi)][m], X[(1, pj)][m])[0]
print('fold moments %.1f min' % ((time.time() - t0) / 60), flush=True)


def r2_matrix(pred_view, targ_view):
    """OOF total-variance-explained R2 for every (p_pred, p_targ)."""
    out = {}
    for pi in PS:
        kp = (pred_view, pi)
        for pj in PS:
            kt = (targ_view, pj)
            if pred_view == 0:
                Cfull, Cfold = Cf[(pi, pj)], lambda f: Ct[(pi, pj, f)]
            else:
                Cfull, Cfold = Cf[(pj, pi)].T, lambda f: Ct[(pj, pi, f)].T
            sse = 0.0
            Yall = X[kt]
            gm = s1f[kt] / n
            sst = 0.0
            for f in range(NF):
                m = fold == f
                nt = n - NT[f]
                Gtr = Gf[kp] - Gt[(kp, f)]
                s1 = s1f[kp] - s1t[(kp, f)]
                mu = s1 / nt
                var = np.diag(Gtr) / nt - mu ** 2
                sd = np.sqrt(np.maximum(var, 1e-12))
                Gc = (Gtr - nt * np.outer(mu, mu)) / np.outer(sd, sd)
                muB = (s1f[kt] - s1t[(kt, f)]) / nt
                Cc = (Cfull - Cfold(f) - nt * np.outer(mu, muB)) / sd[:, None]
                w = np.linalg.solve(Gc + LAM * nt * I, Cc)
                Xte = (np.asarray(X[kp][m], dtype=np.float64) - mu) / sd
                Yte = np.asarray(Yall[m], dtype=np.float64)
                r = Yte - (Xte @ w + muB)
                sse += float((r * r).sum())
                d = Yte - gm
                sst += float((d * d).sum())
            out[(pi, pj)] = 1.0 - sse / sst
    return out


C01 = r2_matrix(0, 1)
print('C01 done %.1f min' % ((time.time() - t0) / 60), flush=True)
C10 = r2_matrix(1, 0)
print('C10 done %.1f min' % ((time.time() - t0) / 60), flush=True)


def ladder(targ_view, pj, cols):
    """OOF R2 predicting view targ_view at pj from an explicit column set."""
    parts = []
    for c in cols:
        if c[0] == 'V':
            parts.append(np.asarray(X[(int(c[1]), int(c[3:]))], dtype=np.float64))
        else:
            parts.append(SC[(c[0], int(c[2:]))][:, None])
    A = np.hstack(parts)
    Y = np.asarray(X[(targ_view, pj)], dtype=np.float64)
    gm = Y.mean(0)
    sse = sst = 0.0
    for f in range(NF):
        m = fold == f
        tr = ~m
        At, Yt = A[tr], Y[tr]
        mu, sd = At.mean(0), np.maximum(At.std(0), 1e-12)
        As = (At - mu) / sd
        muB = Yt.mean(0)
        G = As.T @ As + LAM * len(As) * np.eye(A.shape[1])
        w = np.linalg.solve(G, As.T @ (Yt - muB))
        r = Y[m] - (((A[m] - mu) / sd) @ w + muB)
        sse += float((r * r).sum())
        d = Y[m] - gm
        sst += float((d * d).sum())
    return 1.0 - sse / sst


LAD = {}
for pj in [90, 75, 50, 25]:
    LAD[pj] = {
        'V0_clean': ladder(1, pj, ['V0_100']),
        'V0_clean+Lp': ladder(1, pj, ['V0_100', 'L_%d' % pj]),
        'V0_clean+Lp+Dp': ladder(1, pj, ['V0_100', 'L_%d' % pj, 'D_%d' % pj]),
        'V0_clean+Lp+Dp+L1+D1': ladder(1, pj, ['V0_100', 'L_%d' % pj, 'D_%d' % pj, 'L_100', 'D_100']),
        'V0_matched': ladder(1, pj, ['V0_%d' % pj]),
    }
    print('ladder p=%.2f done %.1f min' % (pj / 100, (time.time() - t0) / 60), flush=True)

res = {'n_cells': n, 'n_base': int(base.sum()),
       'C01': {'%d|%d' % k: v for k, v in C01.items()},
       'C10': {'%d|%d' % k: v for k, v in C10.items()},
       'ladder': {str(k): v for k, v in LAD.items()}}
json.dump(res, open(S / 'x_audit.json', 'w'), indent=2, sort_keys=True)

print()
print('=== T1  MATCHED-STATE PREDICTIVE ADVANTAGE (target identical in both arms) ===')
print('%-8s %-28s %10s %10s %10s' % ('dir', 'target', 'matched', 'clean', 'advantage'))
for pj in [90, 75, 50, 25]:
    a, b = C01[(pj, pj)], C01[(100, pj)]
    print('%-8s %-28s %10.4f %10.4f %+10.4f' % ('V0->V1', 'V1^%.2f' % (pj / 100), a, b, a - b))
for pj in [90, 75, 50, 25]:
    a, b = C10[(pj, pj)], C10[(100, pj)]
    print('%-8s %-28s %10.4f %10.4f %+10.4f' % ('V1->V0', 'V0^%.2f' % (pj / 100), a, b, a - b))
print()
print('=== T4  5x5 MATRIX  C(p_pred, p_targ) = R2(V1^ptarg <- V0^ppred) ===')
print('%-10s' % 'pred\\targ' + ''.join('%9.2f' % (p / 100) for p in PS))
for pi in PS:
    print('%-10.2f' % (pi / 100) + ''.join('%9.4f' % C01[(pi, pj)] for pj in PS))
print()
print('=== T4  EXCESS RATIO R = C(i,j)*C(1,1) / (C(i,1)*C(1,j))   [null = 1.000] ===')
print('%-10s' % 'pred\\targ' + ''.join('%9.2f' % (p / 100) for p in PS))
for pi in PS:
    row = ''
    for pj in PS:
        row += '%9.4f' % (C01[(pi, pj)] * C01[(100, 100)] / (C01[(pi, 100)] * C01[(100, pj)]))
    print('%-10.2f' % (pi / 100) + row)
print()
print('=== T2  SCALAR-CHANNEL RECOVERY (target V1^p) ===')
ks = ['V0_clean', 'V0_clean+Lp', 'V0_clean+Lp+Dp', 'V0_clean+Lp+Dp+L1+D1', 'V0_matched']
print('%-24s' % 'predictor' + ''.join('%12s' % ('p=%.2f' % (p / 100)) for p in [90, 75, 50, 25]))
for k in ks:
    print('%-24s' % k + ''.join('%12.4f' % LAD[pj][k] for pj in [90, 75, 50, 25]))
print()
print('%-24s' % 'recovered fraction' + ''.join('%12s' % '' for _ in [1]))
for k in ks[1:-1]:
    fr = []
    for pj in [90, 75, 50, 25]:
        gap = LAD[pj]['V0_matched'] - LAD[pj]['V0_clean']
        fr.append((LAD[pj][k] - LAD[pj]['V0_clean']) / gap if abs(gap) > 1e-9 else float('nan'))
    print('%-24s' % k + ''.join('%12.3f' % x for x in fr))
print('AUDIT_DONE')
