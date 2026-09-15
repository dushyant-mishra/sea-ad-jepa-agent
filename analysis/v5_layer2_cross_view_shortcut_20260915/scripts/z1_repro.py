"""ITEM 2 - independent second implementation of the context-shortcut decomposition.

PATH A (original): hand-rolled normal equations, np.linalg.solve, manual standardisation,
                   manual total-variance-explained R2, pandas get_dummies.
PATH B (independent): sklearn StandardScaler + Ridge (its own solver) + sklearn OneHotEncoder
                   + sklearn r2_score(multioutput='variance_weighted').

Both are bound to the SAME cells and the SAME fold identities loaded from bind_population.npz.
"""
import numpy as np, pandas as pd, json, pathlib
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import r2_score
S = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
LAM = 1e-2; NF = 5
B = np.load(S / 'bind_population.npz')
bidx, fold = B['base_index'], B['fold_donor']
z = np.load(S / 'screen_out.npz'); q = np.load(S / 'qc_post.npz')
fm = pd.read_csv(S / 'final_manifest.csv', usecols=['donor_id', 'operator_index', 'source'])
V0 = np.asarray(z['p100_v0'][bidx], dtype=np.float64)
V1 = np.asarray(z['p100_v1'][bidx], dtype=np.float64)
L = np.log1p(q['lib_p100'][bidx].astype(np.float64)); Dt = np.log1p(q['det_p100'][bidx].astype(np.float64))
Q = np.column_stack([L, Dt, L ** 2, Dt ** 2, L * Dt])
srcA = pd.get_dummies(fm.source.values[bidx]).to_numpy(float)
opA = pd.get_dummies(fm.operator_index.values[bidx]).to_numpy(float)
enc = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
srcB = enc.fit_transform(fm.source.values[bidx].reshape(-1, 1))
opB = OneHotEncoder(sparse_output=False, handle_unknown='ignore').fit_transform(
    fm.operator_index.values[bidx].reshape(-1, 1))

SETS = [('Q only', ['Q']), ('source only', ['S']), ('operator only', ['O']),
        ('source + operator', ['S', 'O']), ('operator + Q', ['O', 'Q']), ('V0 only', ['V']),
        ('operator + V0', ['O', 'V']), ('operator + Q + V0', ['O', 'Q', 'V'])]
PA = {'Q': Q, 'S': srcA, 'O': opA, 'V': V0}
PB = {'Q': Q, 'S': srcB, 'O': opB, 'V': V0}


def path_a(A, Y):
    sse = 0.0; Ys = []
    for f in range(NF):
        te = fold == f; tr = ~te
        At, Yt = A[tr], Y[tr]
        mu = At.mean(0); sd = np.maximum(At.std(0), 1e-12)
        As = (At - mu) / sd; muB = Yt.mean(0)
        w = np.linalg.solve(As.T @ As + LAM * len(As) * np.eye(A.shape[1]), As.T @ (Yt - muB))
        r = Y[te] - (((A[te] - mu) / sd) @ w + muB)
        sse += float((r * r).sum()); Ys.append(Y[te])
    Yv = np.vstack(Ys); d = Yv - Yv.mean(0)
    return 1.0 - sse / float((d * d).sum())


def path_b(A, Y):
    preds = []; trues = []
    for f in range(NF):
        te = fold == f; tr = ~te
        sc = StandardScaler().fit(A[tr])
        m = Ridge(alpha=LAM * int(tr.sum()), fit_intercept=True)
        m.fit(sc.transform(A[tr]), Y[tr])
        preds.append(m.predict(sc.transform(A[te]))); trues.append(Y[te])
    return float(r2_score(np.vstack(trues), np.vstack(preds), multioutput='variance_weighted'))


res = {}
print('=== ITEM 2: INDEPENDENT REPRODUCTION (identical cells, identical folds) ===')
print('    binding digest f0ca25e5e91d2b87991a6ea301d41a4f64d8805519aa39370e29dd43c8635ec0')
print()
print('%-22s %12s %12s %14s' % ('predictor set', 'PATH A', 'PATH B', 'abs diff'))
worst = 0.0
for name, keys in SETS:
    a = path_a(np.column_stack([PA[k] for k in keys]), V1)
    b = path_b(np.column_stack([PB[k] for k in keys]), V1)
    worst = max(worst, abs(a - b))
    res[name] = {'path_A': a, 'path_B': b, 'abs_diff': abs(a - b)}
    print('%-22s %12.6f %12.6f %14.2e' % (name, a, b, abs(a - b)))
print()
print('  worst absolute disagreement: %.2e' % worst)
TOL = 1e-4
ok = worst < TOL
print('  tolerance (declared before run): %.0e' % TOL)
print('  CONTEXT_SHORTCUT_DECOMPOSITION_INDEPENDENTLY_REPRODUCED: %s' % ('PASS' if ok else 'FAIL - CLOSED'))
print()
print('=== EXACT OVERLAP IDENTITIES (PATH A) ===')
rO = res['operator only']['path_A']; rV = res['V0 only']['path_A']; rOV = res['operator + V0']['path_A']
rOQV = res['operator + Q + V0']['path_A']; rOQ = res['operator + Q']['path_A']
print('  R2(operator)                      %.4f' % rO)
print('  R2(V0)                            %.4f' % rV)
print('  R2(operator + V0)                 %.4f' % rOV)
print('  unique to V0   = R2(O+V) - R2(O)  %+.4f' % (rOV - rO))
print('  unique to oper = R2(O+V) - R2(V)  %+.4f' % (rOV - rV))
print('  shared         = R2(O)+R2(V)-R2(O+V) %+.4f' % (rO + rV - rOV))
print('  Q increment over operator+V0      %+.4f' % (rOQV - rOV))
print('  V0 increment over operator+Q      %+.4f' % (rOQV - rOQ))
res['_overlap'] = {'unique_V0': rOV - rO, 'unique_operator': rOV - rV, 'shared': rO + rV - rOV,
                   'Q_increment_over_OV': rOQV - rOV, 'V0_increment_over_OQ': rOQV - rOQ}
res['_reproduced'] = bool(ok); res['_worst_abs_diff'] = worst; res['_tolerance'] = TOL
json.dump(res, open(S / 'z_repro.json', 'w'), indent=2, sort_keys=True)
if not ok:
    raise SystemExit('INDEPENDENT REPRODUCTION FAILED - FAIL CLOSED')
print('REPRO_DONE')
