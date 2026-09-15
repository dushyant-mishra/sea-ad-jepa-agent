"""Is the surviving cross-view residual CELL-level, or donor-composition structure
that operator-centring cannot reach?

Two designs, answering different questions:
  (A) operator-centred, DONOR-held-out  -> generalises to new donors; still contains
      between-donor-within-operator structure, because a held-out donor's mean is unknown.
  (B) donor-centred, CELL-held-out      -> removes donor means (estimable because cells,
      not donors, are held out); isolates WITHIN-DONOR cell-level signal.
      This deliberately does NOT test donor generalisation.

(B) is validated here on a fixture containing donor-level structure and zero cell-level
signal before it is used.
"""
import numpy as np, pandas as pd, json, pathlib
S = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
LAM = 1e-2; NF = 5


def centred_r2(A, Y, lv, fold):
    K = 1 if lv is None else int(lv.max()) + 1
    sse = 0.0; Ys = []
    for f in range(NF):
        te = fold == f; tr = ~te
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
        sse += float((r * r).sum()); Ys.append(Y_te)
    Yv = np.vstack(Ys); d = Yv - Yv.mean(0)
    return 1.0 - sse / float((d * d).sum())


print('=== FIXTURE for design (B): donor-level structure only, zero cell-level signal ===')
g = np.random.default_rng(11)
n, ndon, D = 40000, 94, 64
don = g.integers(0, ndon, n)
sh = g.normal(size=(ndon, 8)); Ad = g.normal(size=(8, D)); Bd = g.normal(size=(8, D))
F0 = sh[don] @ Ad + g.normal(size=(n, D)); F1 = sh[don] @ Bd + g.normal(size=(n, D))
cf = g.integers(0, NF, n).astype(np.int8)          # CELL-level folds
print('  raw (no centring)            %.4f' % centred_r2(F0, F1, None, cf))
c0 = centred_r2(F0, F1, don, cf)
print('  donor-centred                %.4f   (MUST be ~0)' % c0)
u = g.normal(size=(n, 4)); Ac = g.normal(size=(4, D)); Bc = g.normal(size=(4, D))
G0 = F0 + 0.8 * (u @ Ac); G1 = F1 + 0.8 * (u @ Bc)
c1 = centred_r2(G0, G1, don, cf)
print('  + planted cell-level latent  %.4f   (MUST be >0)' % c1)
okB = abs(c0) < 0.01 and c1 > 0.05
print('  DESIGN_B_VALIDATION %s' % ('PASS' if okB else 'FAIL'))
if not okB:
    raise SystemExit('estimator not validated')

z = np.load(S / 'screen_out.npz')
fm = pd.read_csv(S / 'final_manifest.csv', usecols=['donor_id', 'operator_index', 'source', 'stratum'])
base = (fm.stratum == 'BASE_MECHANICS').values
V0 = np.asarray(z['p100_v0'][base], dtype=np.float64)
V1 = np.asarray(z['p100_v1'][base], dtype=np.float64)
dser = fm.donor_id[base].to_numpy(); oser = fm.operator_index[base].to_numpy(); sser = fm.source[base].to_numpy()

print()
print('=== VARIANCE DECOMPOSITION OF V1 (explains the per-source differences) ===')
print('%-8s %8s %8s %9s %12s %14s %12s' % ('source', 'donors', 'ops', 'don/op', 'betw-oper', 'don-within-op', 'within-don'))
dec = {}
for s in ['HVS', 'NPH52', 'SEA_AD']:
    m = sser == s
    Y = V1[m]; dc = pd.factorize(dser[m])[0]; oc = pd.factorize(oser[m])[0]
    tot = float(((Y - Y.mean(0)) ** 2).sum())
    def gmeans(lv):
        K = int(lv.max()) + 1
        s_ = np.zeros((K, Y.shape[1])); c = np.zeros(K)
        np.add.at(s_, lv, Y); np.add.at(c, lv, 1)
        return s_ / c[:, None], c
    mo, co = gmeans(oc); md, cd = gmeans(dc)
    bo = float((co[:, None] * (mo - Y.mean(0)) ** 2).sum())
    d_in_o = float((cd[:, None] * (md - mo[[oc[dc == k][0] for k in range(len(cd))]]) ** 2).sum())
    wd = tot - bo - d_in_o
    dec[s] = dict(between_operator=bo / tot, donor_within_operator=d_in_o / tot, within_donor=wd / tot,
                  donors=int(dc.max() + 1), operators=int(oc.max() + 1))
    print('%-8s %8d %8d %9.2f %11.3f %13.3f %12.3f'
          % (s, dc.max() + 1, oc.max() + 1, (dc.max() + 1) / (oc.max() + 1), bo / tot, d_in_o / tot, wd / tot))

print()
print('=== CROSS-VIEW SIGNAL UNDER BOTH DESIGNS ===')
print('%-8s %26s %28s' % ('source', '(A) op-centred, donor-held-out', '(B) donor-centred, cell-held-out'))
res = {}
prev = json.load(open(S / 'y_source.json'))
rng = np.random.default_rng(7)
for s in ['ALL', 'HVS', 'NPH52', 'SEA_AD']:
    m = np.ones(len(V0), bool) if s == 'ALL' else (sser == s)
    dc = pd.factorize(dser[m])[0]
    cf = rng.integers(0, NF, int(m.sum())).astype(np.int8)
    b = centred_r2(V0[m], V1[m], dc, cf)
    a = prev[s]['op_centred_r2']
    res[s] = dict(design_A_op_centred_donor_heldout=a, design_B_donor_centred_cell_heldout=b,
                  raw=prev[s]['raw_r2'])
    print('%-8s %26.4f %28.4f' % (s, a, b))
json.dump({'decomposition': dec, 'designs': res}, open(S / 'y_donor.json', 'w'), indent=2, sort_keys=True)
print('DONOR_DONE')
