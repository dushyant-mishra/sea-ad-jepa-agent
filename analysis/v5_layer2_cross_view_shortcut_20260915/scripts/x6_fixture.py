"""Validate the within-batch estimator on controlled fixtures BEFORE using it on real data.

Fixture A: ONLY operator-level shared structure, zero cell-level shared signal.
           A correct estimator must return raw R2 >> 0 and operator-centred R2 ~ 0.
Fixture B: operator-level structure PLUS a known cell-level shared latent.
           A correct estimator must recover roughly the planted cell-level fraction.

Both fixtures reproduce the real nesting: donors nested within operators, folds by donor.
"""
import numpy as np, json, pathlib
S = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
LAM = 1e-2; NF = 5


def batch_means(X, lv, rows, K):
    s = np.zeros((K, X.shape[1])); c = np.zeros(K)
    np.add.at(s, lv[rows], X[rows]); np.add.at(c, lv[rows], 1)
    g = X[rows].mean(0)
    return np.where(c[:, None] > 0, s / np.maximum(c, 1)[:, None], g)


def within_r2(V0, V1, lv, fold, NFOLD=NF):
    """Estimator under test. lv=None means no centring."""
    K = 1 if lv is None else int(lv.max()) + 1
    sse = 0.0; Yte_all = []
    for f in range(NFOLD):
        te = fold == f; tr = ~te
        if lv is None:
            A_tr, A_te, Y_tr, Y_te = V0[tr], V0[te], V1[tr], V1[te]
        else:
            m0 = batch_means(V0, lv, tr, K); m1 = batch_means(V1, lv, tr, K)
            A_tr = V0[tr] - m0[lv[tr]]; A_te = V0[te] - m0[lv[te]]
            Y_tr = V1[tr] - m1[lv[tr]]; Y_te = V1[te] - m1[lv[te]]
        mu = A_tr.mean(0); sd = np.maximum(A_tr.std(0), 1e-12)
        As = (A_tr - mu) / sd
        muB = Y_tr.mean(0)
        w = np.linalg.solve(As.T @ As + LAM * len(As) * np.eye(As.shape[1]), As.T @ (Y_tr - muB))
        r = Y_te - (((A_te - mu) / sd) @ w + muB)
        sse += float((r * r).sum())
        Yte_all.append(Y_te)
    Y = np.vstack(Yte_all); d = Y - Y.mean(0)
    return 1.0 - sse / float((d * d).sum())


def make(n=40000, nop=42, ndon=94, D=64, cell_share=0.0, seed=0):
    g = np.random.default_rng(seed)
    don = g.integers(0, ndon, n)
    don2op = g.integers(0, nop, ndon)          # donors nested within operators
    op = don2op[don]
    fold = (don % NF).astype(np.int8)
    Lop0 = g.normal(size=(nop, D)); Lop1 = g.normal(size=(nop, D))
    shared_op = g.normal(size=(nop, 8))        # operator effects correlated across views
    Aop = g.normal(size=(8, D)); Bop = g.normal(size=(8, D))
    V0 = shared_op[op] @ Aop + 0.3 * Lop0[op] + g.normal(size=(n, D))
    V1 = shared_op[op] @ Bop + 0.3 * Lop1[op] + g.normal(size=(n, D))
    if cell_share > 0:                          # planted CELL-level shared latent
        u = g.normal(size=(n, 4))
        Ac = g.normal(size=(4, D)); Bc = g.normal(size=(4, D))
        V0 = V0 + cell_share * (u @ Ac); V1 = V1 + cell_share * (u @ Bc)
    return V0, V1, op, fold


print('=== FIXTURE A: operator-level shared structure ONLY, zero cell-level shared signal ===')
V0, V1, op, fold = make(cell_share=0.0, seed=1)
ra = within_r2(V0, V1, None, fold); ca = within_r2(V0, V1, op, fold)
print('  raw V0->V1 R2                 %.4f   (should be well above 0)' % ra)
print('  operator-centred R2           %.4f   (MUST be ~0)' % ca)
passA = abs(ca) < 0.01 and ra > 0.05
print('  FIXTURE A %s' % ('PASS' if passA else 'FAIL'))

print()
print('=== FIXTURE B: same, PLUS a planted cell-level shared latent ===')
for cs in (0.5, 1.0):
    V0, V1, op, fold = make(cell_share=cs, seed=2)
    rb = within_r2(V0, V1, None, fold); cb = within_r2(V0, V1, op, fold)
    print('  cell_share=%.1f   raw %.4f   operator-centred %.4f' % (cs, rb, cb))
V0, V1, op, fold = make(cell_share=1.0, seed=2)
passB = within_r2(V0, V1, op, fold) > 0.05
print('  FIXTURE B %s  (planted cell-level signal must be recovered)' % ('PASS' if passB else 'FAIL'))

print()
print('=== NEGATIVE CONTROL: no shared structure of any kind ===')
g = np.random.default_rng(3)
n = 40000; D = 64
don = g.integers(0, 94, n); op = g.integers(0, 42, 94)[don]; fold = (don % NF).astype(np.int8)
rc = within_r2(g.normal(size=(n, D)), g.normal(size=(n, D)), None, fold)
cc = within_r2(g.normal(size=(n, D)), g.normal(size=(n, D)), op, fold)
print('  raw R2 %.4f   operator-centred R2 %.4f   (both MUST be ~0)' % (rc, cc))
passC = abs(rc) < 0.01 and abs(cc) < 0.01
print('  NEGATIVE CONTROL %s' % ('PASS' if passC else 'FAIL'))

print()
ok = passA and passB and passC
print('ESTIMATOR_VALIDATION: %s' % ('PASS' if ok else 'FAIL'))
json.dump({'fixtureA_raw': ra, 'fixtureA_operator_centred': ca, 'passA': bool(passA),
           'passB': bool(passB), 'negcontrol_raw': rc, 'negcontrol_centred': cc,
           'passC': bool(passC), 'validated': bool(ok)},
          open(S / 'x_fixture.json', 'w'), indent=2, sort_keys=True)
if not ok:
    raise SystemExit('ESTIMATOR NOT VALIDATED - do not run on real data')
