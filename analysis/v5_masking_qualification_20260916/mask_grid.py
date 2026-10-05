"""Frozen (K, R) grid sweep + recurrence-fraction diagnostics on the common core.

Diagnoses whether zero edges at large pool size is a real absence of structure or simply
a rank threshold whose stringency scales with the candidate pool. The grid was frozen in
the qualification contract before any of this was run.
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
NS = 'JEPA_V5_MASKING_GRID_V1'
N_SEL, BLOCKS_PER_OP, KMAX = 2000, 3, 20
K_GRID, R_GRID = [5, 10, 20], [0.5, 0.6, 0.75]
t0 = time.time()

def seeded(n):
    return np.random.default_rng(int.from_bytes(hashlib.sha256(f'{NS}|{n}'.encode()).digest()[:8], 'big'))

st = np.load(OBS, allow_pickle=False)['states']
common = np.flatnonzero((st == 1).all(axis=0))
addr_sel = np.sort(seeded('addr').choice(common, size=N_SEL, replace=False))
n_addr = addr_sel.size
rows = list(csv.DictReader((L4 / 'PHASE2_EXPRESSION_BLOCK_MANIFEST.csv').open(newline='')))
by_op = {}
for i, r in enumerate(rows):
    by_op.setdefault(int(r['operator_index']), []).append(i)
blocks = []
for op in sorted(by_op):
    idxs = by_op[op]; g = seeded(f'b|{op}')
    blocks += [idxs[int(k)] for k in g.choice(len(idxs), size=min(BLOCKS_PER_OP, len(idxs)), replace=False)]
blocks = sorted(set(blocks))
sel_mask = np.zeros(41238, bool); sel_mask[addr_sel] = True
remap = np.full(41238, -1, np.int64); remap[addr_sel] = np.arange(n_addr)

vals, donors, srcs = [], [], []
for bi in blocks:
    r = rows[bi]
    zz = np.load(L4 / r['counts_path'], allow_pickle=False)
    indptr, indices, data = zz['indptr'], zz['indices'], zz['data'].astype(np.float64)
    nr = len(indptr) - 1
    md = list(csv.DictReader((L4 / r['meta_path']).open(newline='')))
    lib = np.array([float(x['source_library']) for x in md])
    dense = np.zeros((nr, n_addr), np.float32)
    for i in range(nr):
        a, b = indptr[i], indptr[i + 1]
        if b <= a or lib[i] <= 0: continue
        ix = indices[a:b]; keep = sel_mask[ix]
        if keep.any():
            dense[i, remap[ix[keep]]] = np.log1p(data[a:b][keep] * 10000.0 / lib[i])
    vals.append(dense); donors += [x['donor_id'] for x in md]; srcs += [r['source']] * nr
V = np.vstack(vals).astype(np.float32)
donors = np.array(donors); srcs = np.array(srcs)
duniq, dcode = np.unique(donors, return_inverse=True)
src_of_donor = np.array([srcs[dcode == d][0] for d in range(duniq.size)])
print('cells %d donors %d addr %d (%.1f min)' % (V.shape[0], duniq.size, n_addr, (time.time() - t0) / 60), flush=True)

half = np.zeros(duniq.size, int)
for s in np.unique(src_of_donor):
    idx = np.flatnonzero(src_of_donor == s); perm = seeded(f'split|{s}').permutation(idx)
    half[perm[len(perm) // 2:]] = 1

def topk_ranks(donor_ids):
    """Per-donor top-KMAX neighbour lists, ordered best-first."""
    out = {}
    for d in donor_ids:
        sel = dcode == d
        if sel.sum() < 20: continue
        X = V[sel].astype(np.float64)
        live = X.var(0) > 0
        if live.sum() < KMAX + 1: continue
        li = np.flatnonzero(live)
        Xr = rankdata(X[:, live], axis=0)
        Xr -= Xr.mean(0); sd = np.sqrt((Xr * Xr).sum(0)); sd[sd == 0] = np.nan
        Xr /= sd
        M = np.abs(Xr.T @ Xr)
        np.fill_diagonal(M, -1.0)
        M = np.nan_to_num(M, nan=-1.0)
        part = np.argpartition(M, -KMAX, axis=1)[:, -KMAX:]
        ordr = np.take_along_axis(M, part, 1).argsort(1)[:, ::-1]
        top = np.take_along_axis(part, ordr, 1)
        out[int(d)] = (li, li[top])
    return out

print('computing per-donor top-%d lists ...' % KMAX, flush=True)
TA = topk_ranks(np.flatnonzero(half == 0)); TB = topk_ranks(np.flatnonzero(half == 1))
print('  strata A=%d B=%d (%.1f min)' % (len(TA), len(TB), (time.time() - t0) / 60), flush=True)

def votes_for(T, k):
    v = np.zeros((n_addr, n_addr), np.float32)
    for d, (li, top) in T.items():
        for loc in range(li.size):
            v[li[loc], top[loc, :k]] += 1.0
    return v / max(len(T), 1)

print('\n=== RECURRENCE-FRACTION DISTRIBUTION (half A) ===')
for k in K_GRID:
    f = votes_for(TA, k)
    nz = f[f > 0]
    print('  K=%-3d max %.3f  p99.99 %.3f  p99.9 %.3f  pairs>=0.5 %d  >=0.6 %d  >=0.75 %d'
          % (k, nz.max() if nz.size else 0, np.percentile(nz, 99.99) if nz.size else 0,
             np.percentile(nz, 99.9) if nz.size else 0,
             int((f >= 0.5).sum()), int((f >= 0.6).sum()), int((f >= 0.75).sum())))

def und(f, r):
    aa, bb = np.nonzero(f >= r)
    return sorted({(int(min(a, b)), int(max(a, b))) for a, b in zip(aa, bb)})
def jac(a, b):
    A, B = set(a), set(b); return len(A & B) / len(A | B) if (A or B) else 0.0

print('\n=== FROZEN (K,R) GRID: edges and split-half stability ===')
print('%-5s %-6s %10s %10s %10s %14s' % ('K', 'R', '|E_A|', '|E_B|', 'Jaccard', 'targets_w_nbr'))
grid = {}
best = None
for k in K_GRID:
    fA, fB = votes_for(TA, k), votes_for(TB, k)
    for r in R_GRID:
        eA, eB = und(fA, r), und(fB, r)
        j = jac(eA, eB)
        degB = {}
        for a, b in eB: degB[a] = degB.get(a, 0) + 1; degB[b] = degB.get(b, 0) + 1
        grid[f'K{k}_R{r}'] = dict(edges_A=len(eA), edges_B=len(eB), jaccard=j, targets_with_nbr=len(degB))
        print('%-5d %-6.2f %10d %10d %10.4f %14d' % (k, r, len(eA), len(eB), j, len(degB)))
        if len(eA) > 0 and len(eB) > 0 and (best is None or j > best[2]):
            best = (k, r, j, eA, eB, fA)
json.dump({'namespace': NS, 'n_addr': n_addr, 'cells': int(V.shape[0]), 'donors': int(duniq.size),
           'grid': grid}, open(S / 'mask_grid.json', 'w'), indent=2, sort_keys=True)
if best is None:
    print('\nNO GRID CELL PRODUCED EDGES IN BOTH HALVES -> metric D NOT_ESTIMABLE')
    raise SystemExit
k, r, j, eA, eB, fA = best
print('\nselected by frozen tie-break (highest stability among cells with edges): K=%d R=%.2f Jaccard=%.4f' % (k, r, j))
nbrA = {}
for a, b in eA: nbrA.setdefault(a, []).append(b); nbrA.setdefault(b, []).append(a)
degB = {}
for a, b in eB: degB[a] = degB.get(a, 0) + 1; degB[b] = degB.get(b, 0) + 1
targets = np.array(sorted(set(degB) & set(nbrA)))[:400]
print('targets with a held-out partner AND a half-A neighbour: %d' % targets.size)
if targets.size == 0:
    print('VACUOUS -> metric D NOT_ESTIMABLE'); raise SystemExit
BURDEN = int(round(0.20 * n_addr))
def build(policy):
    m = np.zeros((targets.size, n_addr), bool); exp = []
    for i, t in enumerate(targets):
        g = seeded(f'm|{policy}|{int(t)}'); ch = {int(t)}
        if policy == 'R': ch |= set(nbrA.get(int(t), [])[:int(np.floor(BURDEN * 0.5))])
        exp.append(len(ch))
        pool = np.setdiff1d(np.arange(n_addr), np.array(sorted(ch)))
        need = max(0, BURDEN - len(ch))
        if need and pool.size: ch |= set(int(x) for x in g.choice(pool, size=min(need, pool.size), replace=False))
        m[i, np.array(sorted(ch))] = True
    return m, exp
out = {}
print('\n=== METRIC D: exposure at matched burden (%d targets, burden %d) ===' % (targets.size, BURDEN))
for c in ('U', 'R'):
    m, e = build(c)
    ex = float(np.mean([correlated_partner_exposure(m[i], eB) for i in range(targets.size)]))
    out[c] = dict(exposure=ex, struct_expansion=float(np.mean(e)), max_component=int(max(e)),
                  masked_fraction=float(m.sum(1).mean() / n_addr),
                  digest=deterministic_mask_digest(m))
    print('  %-3s exposure %.4f  structExp %.1f  maskedFrac %.4f' % (c, ex, np.mean(e), m.sum(1).mean() / n_addr))
red = 100 * (out['U']['exposure'] - out['R']['exposure']) / max(out['U']['exposure'], 1e-12)
print('  reduction %.1f%% (contract >= 20%%) -> %s' % (red, 'MEETS' if red >= 20 else 'DOES NOT MEET'))
json.dump({'namespace': NS, 'grid': grid, 'selected': {'K': k, 'R': r, 'jaccard': j},
           'targets': int(targets.size), 'burden': BURDEN, 'candidates': out,
           'reduction_pct': red, 'meets_contract_D': bool(red >= 20)},
          open(S / 'mask_grid.json', 'w'), indent=2, sort_keys=True)
print('wall %.1f min GRID_DONE' % ((time.time() - t0) / 60))
