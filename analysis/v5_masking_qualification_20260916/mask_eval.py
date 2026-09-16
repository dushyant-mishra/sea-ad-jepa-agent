"""Candidate masking comparison against the frozen qualification contract.

Anti-circularity: masks are BUILT from edges estimated on donor half A and SCORED against
edges estimated independently on donor half B. Scoring a dependency-aware mask against its
own edges would be tautological.
"""
import hashlib, json, pathlib, sys, time
import numpy as np

sys.path.insert(0, r'D:/jepa_mask_20260916/src')
from sea_ad_jepa.v5.dependency_recurrence_estimator_v1 import DonorStratifiedRankRecurrenceV1
from sea_ad_jepa.v5.masking_audit_metrics_v1 import (
    correlated_partner_exposure, address_coverage, normalized_coverage_concentration,
    deterministic_mask_digest, sparse_support_failure_rate)

S = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
NS = 'JEPA_V5_MASKING_CANDIDATE_EVAL_V1'
z = np.load(S / 'mask_sample.npz', allow_pickle=True)
V = z['values'].astype(np.float64); dcode = z['donor_code']; meas = z['meas_by_donor']
is_common = z['is_common']; src_of_donor = z['src_of_donor']; op_of_donor = z['op_of_donor']
src_cell = z['source']; n_addr = V.shape[1]
n_donors = meas.shape[0]
t0 = time.time()

def seeded(name):
    return np.random.default_rng(int.from_bytes(hashlib.sha256(f'{NS}|{name}'.encode()).digest()[:8], 'big'))

# frozen donor split, stratified by source so both halves see all sources
half = np.zeros(n_donors, dtype=int)
for s in np.unique(src_of_donor):
    idx = np.flatnonzero(src_of_donor == s)
    g = seeded(f'split|{s}'); perm = g.permutation(idx)
    half[perm[len(perm) // 2:]] = 1
print('donor split: A=%d B=%d | by source %s' % (
    (half == 0).sum(), (half == 1).sum(),
    {str(s): [int(((half == h) & (src_of_donor == s)).sum()) for h in (0, 1)] for s in np.unique(src_of_donor)}))

K, R, MIN_STRATA = 10, 0.6, 3            # from the frozen grid
EST = DonorStratifiedRankRecurrenceV1(top_k=K, recurrence_fraction=R, min_evaluable_strata=MIN_STRATA)

def fit_half(h, balanced):
    keep = np.isin(dcode, np.flatnonzero(half == h))
    dsub = dcode[keep]
    return EST.fit_dense(values=V[keep], donor_codes=dsub, measurable_by_donor=meas,
                         source_by_donor=(src_of_donor if balanced else None))

print('fitting R (donor-recurrent) and C (source-balanced) on both halves ...', flush=True)
RA, RB = fit_half(0, False), fit_half(1, False)
CA, CB = fit_half(0, True), fit_half(1, True)
print('  R: |A|=%d |B|=%d   C: |A|=%d |B|=%d   (%.1f min)' % (
    len(RA['undirected_edges']), len(RB['undirected_edges']),
    len(CA['undirected_edges']), len(CB['undirected_edges']), (time.time() - t0) / 60), flush=True)

# --- Candidate H: historical pooled Pearson top-K comparator (HISTORICAL_COMPARATOR_ONLY)
def pooled_pearson_topk(k=K):
    Xc = V - V.mean(0); sd = Xc.std(0); sd[sd == 0] = np.nan
    C = (Xc / sd).T @ (Xc / sd) / V.shape[0]
    np.fill_diagonal(C, np.nan); M = np.abs(C)
    e = set()
    for a in range(n_addr):
        row = M[a]; fin = np.flatnonzero(np.isfinite(row))
        if fin.size == 0: continue
        top = fin[np.argsort(-row[fin], kind='mergesort')[:k]]
        for b in top: e.add((min(a, int(b)), max(a, int(b))))
    return sorted(e)
H_edges = pooled_pearson_topk()
print('  H (pooled Pearson top-K, comparator only): |E|=%d' % len(H_edges))

# --- metric C: stability vs permuted null
def jac(a, b):
    A, B = set(a), set(b)
    return len(A & B) / len(A | B) if (A or B) else 0.0
def perm_null(edges_a, edges_b, n=200):
    out = []
    for i in range(n):
        g = seeded(f'perm|{i}'); p = g.permutation(n_addr)
        pe = {(min(int(p[a]), int(p[b])), max(int(p[a]), int(p[b]))) for a, b in edges_b}
        out.append(jac(edges_a, pe))
    return float(np.mean(out)), float(np.percentile(out, 95))
jR = jac(RA['undirected_edges'], RB['undirected_edges'])
jC = jac(CA['undirected_edges'], CB['undirected_edges'])
mR, p95R = perm_null(RA['undirected_edges'], RB['undirected_edges'])
mC, p95C = perm_null(CA['undirected_edges'], CB['undirected_edges'])
print('\n=== METRIC C: split-half stability vs permuted null ===')
print('  R  Jaccard %.4f   null mean %.4f  null p95 %.4f   ABOVE_NULL=%s' % (jR, mR, p95R, jR > p95R))
print('  C  Jaccard %.4f   null mean %.4f  null p95 %.4f   ABOVE_NULL=%s' % (jC, mC, p95C, jC > p95C))

# --- neighbour maps built from half A only; scored against half B
def nbr_map(res):
    m = {}
    for a, b, _, _ in res['edges']:
        m.setdefault(a, []).append(b)
    return {k: sorted(v) for k, v in m.items()}
NB = {'R': nbr_map(RA), 'C': nbr_map(CA)}
Hmap = {}
for a, b in H_edges:
    Hmap.setdefault(a, []).append(b); Hmap.setdefault(b, []).append(a)
NB['H'] = {k: sorted(v) for k, v in Hmap.items()}

held_out_edges = [(a, b) for a, b in RB['undirected_edges']]
print('  held-out scoring edge set (donor half B, R): %d edges' % len(held_out_edges))

# --- mask construction at matched burden
STRUCT_FRAC = {'U': 0.0, 'H': 0.5, 'R': 0.5, 'C': 0.5}      # mixture 2:2 from frozen grid
def build_masks(policy, targets, burden, measurable_row):
    masks = np.zeros((len(targets), n_addr), dtype=bool)
    expansions, comps = [], []
    for i, t in enumerate(targets):
        g = seeded(f'mask|{policy}|{int(t)}')
        live = np.flatnonzero(measurable_row)
        chosen = {int(t)}
        if policy != 'U':
            nb = [b for b in NB[policy].get(int(t), []) if measurable_row[b]]
            take = int(np.floor(burden * STRUCT_FRAC[policy]))
            chosen |= set(nb[:take])
        expansions.append(len(chosen))
        pool = np.array([a for a in live if a not in chosen])
        need = max(0, burden - len(chosen))
        if need and pool.size:
            chosen |= set(int(x) for x in g.choice(pool, size=min(need, pool.size), replace=False))
        idx = np.array(sorted(chosen))
        masks[i, idx] = True
        comps.append(len(chosen))
    return masks, expansions, comps

targets = np.flatnonzero(meas.all(0))[:120]          # targets measurable in every donor
print('\n  evaluation targets (measurable in all donors): %d' % targets.size)
assert targets.size > 0, 'VACUOUS: no eligible targets'
measurable_row = meas.all(0)
BURDEN = int(round(0.20 * measurable_row.sum()))
print('  matched burden: %d addresses (%.1f%% of measurable support)' % (BURDEN, 100 * BURDEN / measurable_row.sum()))

print('\n=== METRIC D: anti-interpolation exposure (held-out edges) + F: burden ===')
print('%-4s %12s %12s %10s %12s %12s' % ('cand', 'exposure', 'vs U', 'maskedFrac', 'structExp', 'maxComp'))
results = {}
for cand in ('U', 'H', 'R', 'C'):
    masks, expansions, comps = build_masks(cand, targets, BURDEN, measurable_row)
    exp = float(np.mean([correlated_partner_exposure(masks[i], held_out_edges) for i in range(len(targets))]))
    frac = float(masks.sum(1).mean() / measurable_row.sum())
    results[cand] = dict(exposure=exp, masked_fraction=frac,
                         struct_expansion_mean=float(np.mean(expansions)),
                         max_component=int(max(comps)),
                         digest=deterministic_mask_digest(masks),
                         concentration=float(normalized_coverage_concentration(
                             address_coverage(masks, vocabulary_size=n_addr))))
    rel = '' if cand == 'U' else '%+.1f%%' % (100 * (exp - results['U']['exposure']) / max(results['U']['exposure'], 1e-12))
    print('%-4s %12.4f %12s %10.4f %12.1f %12d' % (cand, exp, rel, frac, np.mean(expansions), max(comps)))
    results[cand]['relative_to_U'] = rel

json.dump({'namespace': NS, 'K': K, 'R': R, 'min_strata': MIN_STRATA,
           'donor_split': {'A': int((half == 0).sum()), 'B': int((half == 1).sum())},
           'edges': {'R_A': len(RA['undirected_edges']), 'R_B': len(RB['undirected_edges']),
                     'C_A': len(CA['undirected_edges']), 'C_B': len(CB['undirected_edges']),
                     'H_pooled': len(H_edges)},
           'stability': {'R': {'jaccard': jR, 'null_mean': mR, 'null_p95': p95R, 'above_null': bool(jR > p95R)},
                         'C': {'jaccard': jC, 'null_mean': mC, 'null_p95': p95C, 'above_null': bool(jC > p95C)}},
           'targets': int(targets.size), 'burden': int(BURDEN),
           'held_out_edges': len(held_out_edges),
           'candidates': results},
          open(S / 'mask_eval.json', 'w'), indent=2, sort_keys=True)
print('\nwall %.1f min  EVAL_DONE' % ((time.time() - t0) / 60))
