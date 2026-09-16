"""Scaled masking qualification on the common core, where evaluability is uniform.

Restricting to common-core addresses (measurable in all 42 operators) makes every pair
jointly evaluable in every stratum, which removes measurability as a confound in the
recurrence denominator. COMMON_CORE_SUPPORT_IS_COMPARABILITY_NOT_BIOLOGY_AUTHORITY:
this is a comparability convenience, not a claim that these addresses matter more.
"""
import csv, hashlib, json, pathlib, sys, time
import numpy as np
from scipy.stats import rankdata

sys.path.insert(0, r'D:/jepa_mask_20260916/src')
from sea_ad_jepa.v5.masking_audit_metrics_v1 import (
    correlated_partner_exposure, address_coverage, normalized_coverage_concentration,
    deterministic_mask_digest)

P = pathlib.Path(r'D:/Jepa project')
L4 = P / 'outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4'
OBS = P / 'exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz'
S = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
NS = 'JEPA_V5_MASKING_SCALED_V1'
N_ADDR_SEL, BLOCKS_PER_OP = 6000, 3
K, R_FRAC, MIN_STRATA = 10, 0.6, 3
t0 = time.time()

def seeded(name):
    return np.random.default_rng(int.from_bytes(hashlib.sha256(f'{NS}|{name}'.encode()).digest()[:8], 'big'))

st = np.load(OBS, allow_pickle=False)['states']
common = np.flatnonzero((st == 1).all(axis=0))
addr_sel = np.sort(seeded('addr').choice(common, size=min(N_ADDR_SEL, common.size), replace=False))
pos = {int(a): i for i, a in enumerate(addr_sel)}
n_addr = addr_sel.size
print('common core %d ; sampled %d' % (common.size, n_addr), flush=True)

rows = list(csv.DictReader((L4 / 'PHASE2_EXPRESSION_BLOCK_MANIFEST.csv').open(newline='')))
by_op = {}
for i, r in enumerate(rows):
    by_op.setdefault(int(r['operator_index']), []).append(i)
blocks = []
for op in sorted(by_op):
    idxs = by_op[op]; g = seeded(f'b|{op}')
    blocks += [idxs[int(k)] for k in g.choice(len(idxs), size=min(BLOCKS_PER_OP, len(idxs)), replace=False)]
blocks = sorted(set(blocks))

vals, donors, srcs = [], [], []
for n, bi in enumerate(blocks):
    r = rows[bi]
    zz = np.load(L4 / r['counts_path'], allow_pickle=False)
    indptr, indices, data = zz['indptr'], zz['indices'], zz['data'].astype(np.float64)
    nr = len(indptr) - 1
    md = list(csv.DictReader((L4 / r['meta_path']).open(newline='')))
    lib = np.array([float(x['source_library']) for x in md])
    sel_mask = np.zeros(41238, dtype=bool); sel_mask[addr_sel] = True
    remap = np.full(41238, -1, dtype=np.int64); remap[addr_sel] = np.arange(n_addr)
    dense = np.zeros((nr, n_addr), dtype=np.float32)
    for i in range(nr):
        a, b = indptr[i], indptr[i + 1]
        if b <= a or lib[i] <= 0: continue
        ix = indices[a:b]; keep = sel_mask[ix]
        if not keep.any(): continue
        dense[i, remap[ix[keep]]] = np.log1p(data[a:b][keep] * 10000.0 / lib[i])
    vals.append(dense); donors += [x['donor_id'] for x in md]; srcs += [r['source']] * nr
    if (n + 1) % 30 == 0: print('  %d/%d blocks %.1f min' % (n + 1, len(blocks), (time.time() - t0) / 60), flush=True)

V = np.vstack(vals).astype(np.float32)
donors = np.array(donors); srcs = np.array(srcs)
duniq, dcode = np.unique(donors, return_inverse=True)
src_of_donor = np.array([srcs[dcode == d][0] for d in range(duniq.size)])
print('cells %d donors %d addr %d | %.1f min' % (V.shape[0], duniq.size, n_addr, (time.time() - t0) / 60), flush=True)

half = np.zeros(duniq.size, dtype=int)
for s in np.unique(src_of_donor):
    idx = np.flatnonzero(src_of_donor == s); perm = seeded(f'split|{s}').permutation(idx)
    half[perm[len(perm) // 2:]] = 1

def recurrent_edges(donor_ids, balanced):
    per_src = {}
    for d in donor_ids: per_src[src_of_donor[d]] = per_src.get(src_of_donor[d], 0) + 1
    ns = len(per_src)
    votes = np.zeros((n_addr, n_addr), dtype=np.float32)
    total_w, strata = 0.0, 0
    for d in donor_ids:
        sel = dcode == d
        if sel.sum() < 20: continue
        X = V[sel].astype(np.float64)
        live = X.var(0) > 0
        if live.sum() < 2: continue
        Xr = rankdata(X[:, live], axis=0)
        Xr -= Xr.mean(0); sd = np.sqrt((Xr * Xr).sum(0)); sd[sd == 0] = np.nan
        Xr /= sd
        C = Xr.T @ Xr
        np.fill_diagonal(C, np.nan)
        M = np.abs(C)
        w = (1.0 / (ns * per_src[src_of_donor[d]])) if balanced else 1.0
        li = np.flatnonzero(live)
        k = min(K, li.size - 1)
        part = np.argpartition(np.nan_to_num(M, nan=-1.0), -k, axis=1)[:, -k:]
        for loc in range(li.size):
            votes[li[loc], li[part[loc]]] += w
        total_w += w; strata += 1
    frac = votes / max(total_w, 1e-12)
    aa, bb = np.nonzero(frac >= R_FRAC)
    und = sorted({(int(min(a, b)), int(max(a, b))) for a, b in zip(aa, bb)})
    nbr = {}
    for a, b in zip(aa, bb): nbr.setdefault(int(a), []).append(int(b))
    return und, nbr, strata

A_ids = np.flatnonzero(half == 0); B_ids = np.flatnonzero(half == 1)
print('fitting halves (A=%d B=%d donors) ...' % (A_ids.size, B_ids.size), flush=True)
undA, nbrA, sA = recurrent_edges(A_ids, False)
undB, nbrB, sB = recurrent_edges(B_ids, False)
undCA, nbrCA, _ = recurrent_edges(A_ids, True)
undCB, _, _ = recurrent_edges(B_ids, True)
print('  R: |A|=%d |B|=%d strata %d/%d | C: |A|=%d |B|=%d | %.1f min' % (
    len(undA), len(undB), sA, sB, len(undCA), len(undCB), (time.time() - t0) / 60), flush=True)

def jac(a, b):
    A, B = set(a), set(b); return len(A & B) / len(A | B) if (A or B) else 0.0
def null(a, b, n=100):
    out = []
    for i in range(n):
        p = seeded(f'perm|{i}').permutation(n_addr)
        out.append(jac(a, {(min(int(p[x]), int(p[y])), max(int(p[x]), int(p[y]))) for x, y in b}))
    return float(np.mean(out)), float(np.percentile(out, 95))
jR = jac(undA, undB); mR, p95R = null(undA, undB)
jC = jac(undCA, undCB); mC, p95C = null(undCA, undCB)
deg = {}
for a, b in undB: deg[a] = deg.get(a, 0) + 1; deg[b] = deg.get(b, 0) + 1
print('\n=== METRIC A/C: recurrence + split-half stability ===')
print('  R Jaccard %.4f (null mean %.5f p95 %.5f) ABOVE_NULL=%s' % (jR, mR, p95R, jR > p95R))
print('  C Jaccard %.4f (null mean %.5f p95 %.5f) ABOVE_NULL=%s' % (jC, mC, p95C, jC > p95C))
print('  held-out edges %d ; targets with >=1 held-out partner: %d of %d' % (len(undB), len(deg), n_addr))

BURDEN = int(round(0.20 * n_addr))
targets = np.array(sorted(deg))[:400]
print('\n=== METRIC D: exposure at matched burden (%d targets, burden %d) ===' % (targets.size, BURDEN))
assert targets.size > 0, 'VACUOUS'
def build(policy, nbr):
    masks = np.zeros((targets.size, n_addr), dtype=bool); exp = []
    for i, t in enumerate(targets):
        g = seeded(f'm|{policy}|{int(t)}'); chosen = {int(t)}
        if policy != 'U':
            chosen |= set(nbr.get(int(t), [])[:int(np.floor(BURDEN * 0.5))])
        exp.append(len(chosen))
        pool = np.setdiff1d(np.arange(n_addr), np.array(sorted(chosen)), assume_unique=False)
        need = max(0, BURDEN - len(chosen))
        if need and pool.size:
            chosen |= set(int(x) for x in g.choice(pool, size=min(need, pool.size), replace=False))
        masks[i, np.array(sorted(chosen))] = True
    return masks, exp
res = {}
print('%-4s %12s %10s %12s %12s' % ('cand', 'exposure', 'vs U', 'structExp', 'maxComp'))
for cand, nbr in (('U', {}), ('R', nbrA), ('C', nbrCA)):
    m, e = build(cand, nbr)
    ex = float(np.mean([correlated_partner_exposure(m[i], undB) for i in range(targets.size)]))
    res[cand] = dict(exposure=ex, masked_fraction=float(m.sum(1).mean() / n_addr),
                     struct_expansion=float(np.mean(e)), max_component=int(max(e)),
                     digest=deterministic_mask_digest(m),
                     concentration=float(normalized_coverage_concentration(address_coverage(m, vocabulary_size=n_addr))))
    rel = '' if cand == 'U' else '%+.1f%%' % (100 * (ex - res['U']['exposure']) / max(res['U']['exposure'], 1e-12))
    res[cand]['relative_to_U'] = rel
    print('%-4s %12.4f %10s %12.1f %12d' % (cand, ex, rel, np.mean(e), max(e)))
red = 100 * (res['U']['exposure'] - res['R']['exposure']) / max(res['U']['exposure'], 1e-12)
print('\n  R reduction vs uniform: %.1f%%  (contract requires >= 20%%) -> %s' % (red, 'MEETS' if red >= 20 else 'DOES NOT MEET'))
json.dump({'namespace': NS, 'n_addr': n_addr, 'cells': int(V.shape[0]), 'donors': int(duniq.size),
           'K': K, 'R': R_FRAC, 'edges': {'R_A': len(undA), 'R_B': len(undB), 'C_A': len(undCA), 'C_B': len(undCB)},
           'stability': {'R': {'jaccard': jR, 'null_p95': p95R, 'above_null': bool(jR > p95R)},
                         'C': {'jaccard': jC, 'null_p95': p95C, 'above_null': bool(jC > p95C)}},
           'targets_with_partner': len(deg), 'targets_evaluated': int(targets.size),
           'burden': BURDEN, 'candidates': res, 'reduction_pct': red,
           'meets_contract_D': bool(red >= 20)},
          open(S / 'mask_scaled.json', 'w'), indent=2, sort_keys=True)
print('wall %.1f min SCALED_DONE' % ((time.time() - t0) / 60))
