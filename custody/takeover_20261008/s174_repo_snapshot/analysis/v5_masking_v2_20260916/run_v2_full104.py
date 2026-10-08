"""Real FULL104 V2 evaluation under the frozen contract.

Contract: docs/agent/V5_MASKING_V2_SHORTCUT_PREDICTABILITY_CONTRACT_20260916.json
digest 0c3e89cf2be164bb22d43e5ba5592d562b2f33c32b4aea78bfa460f825a44ecf, commit 15732d4c.
Nothing below may alter a threshold. Read-only FULL104. No training. No D_shared.
"""
import csv, hashlib, json, pathlib, sys, time
import numpy as np

sys.path.insert(0, r'D:/jepa_mask_v2_20260916/src')
from sea_ad_jepa.v5.shortcut_predictability_v2 import (
    CheapRidgeAttackerV1, DonorBalancedScreenerV1, donor_standardize,
    baseline_sums, baseline_from_sums, combine_direction_shortcuts,
    global_cell_state_baseline, inner_rotation, stratified_outer_folds, _rank_columns)

P = pathlib.Path(r'D:/Jepa project')
L4 = P / 'outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4'
OBS = P / 'exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz'
OUT = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')

NS = 'JEPA_V5_MASKING_V2_FULL104'
N_ADDR, N_TARGETS = 2000, 60
OUTER_FOLDS, CAND_M, ALPHA, MAXF = 10, 20, 1e-2, 64
SHORTCUT_REDUCTION, SHORTCUT_CAP, NO_SHORTCUT_FLOOR = 0.50, 8, 0.05
MASK_FRACTION = 0.20                       # QUALIFICATION_ONLY_NOT_PRODUCTION_AUTHORITY
CELL_CAP = 250_000                         # memory bound, identical across all conditions
LADDER = [3, 8, 20]
V1_K, V1_R = 10, 0.6                       # frozen V1 definition, unchanged


def seeded(n):
    return np.random.default_rng(int.from_bytes(hashlib.sha256(f'{NS}|{n}'.encode()).digest()[:8], 'big'))


def load(blocks_per_op):
    st = np.load(OBS, allow_pickle=False)['states']
    common = np.flatnonzero((st == 1).all(axis=0))
    addr = np.sort(seeded('addr').choice(common, size=N_ADDR, replace=False))
    remap = np.full(41238, -1, np.int64); remap[addr] = np.arange(N_ADDR)
    sel = np.zeros(41238, bool); sel[addr] = True
    rows = list(csv.DictReader((L4 / 'PHASE2_EXPRESSION_BLOCK_MANIFEST.csv').open(newline='')))
    byop = {}
    for i, r in enumerate(rows):
        byop.setdefault(int(r['operator_index']), []).append(i)
    blocks = []
    for op in sorted(byop):
        idxs = byop[op]; g = seeded(f'blk|{op}|{blocks_per_op}')
        blocks += [idxs[int(k)] for k in g.choice(len(idxs), size=min(blocks_per_op, len(idxs)), replace=False)]
    blocks = sorted(set(blocks))
    vals, don, src = [], [], []
    for bi in blocks:
        r = rows[bi]
        z = np.load(L4 / r['counts_path'], allow_pickle=False)
        ip, ix_all, da = z['indptr'], z['indices'], z['data'].astype(np.float64)
        nr = len(ip) - 1
        md = list(csv.DictReader((L4 / r['meta_path']).open(newline='')))
        lib = np.array([float(x['source_library']) for x in md])
        dense = np.zeros((nr, N_ADDR), np.float32)
        for i in range(nr):
            a, b = ip[i], ip[i + 1]
            if b <= a or lib[i] <= 0: continue
            ix = ix_all[a:b]; keep = sel[ix]
            if keep.any():
                dense[i, remap[ix[keep]]] = np.log1p(da[a:b][keep] * 10000.0 / lib[i])
        vals.append(dense); don += [x['donor_id'] for x in md]; src += [r['source']] * nr
    V = np.vstack(vals); don = np.array(don); src = np.array(src)
    if V.shape[0] > CELL_CAP:
        keep = np.sort(seeded('cellcap').choice(V.shape[0], size=CELL_CAP, replace=False))
        V, don, src = V[keep], don[keep], src[keep]
    duniq, dcode = np.unique(don, return_inverse=True)
    src_of_donor = np.array([src[dcode == d][0] for d in range(duniq.size)])
    return V, dcode, src_of_donor, addr


def per_donor_rho(V, dcode, targets):
    """rho[d][ti, :] = |Spearman| of target ti against every address, within donor d."""
    out = {}
    for d in np.unique(dcode):
        rows = dcode == d
        if rows.sum() < 30: continue
        X = V[rows].astype(np.float64)
        live = X.var(0) > 0
        R = np.zeros_like(X)
        li = np.flatnonzero(live)
        if li.size < 2: continue
        Rl = _rank_columns(X[:, li])
        Rl -= Rl.mean(0); sd = np.sqrt((Rl * Rl).sum(0)); sd[sd == 0] = np.nan
        Rl /= sd
        R[:, li] = np.nan_to_num(Rl, nan=0.0)
        out[int(d)] = (np.abs(R[:, targets].T @ R), live)
    return out


def screen(rho, donors, targets_idx, src_of_donor, visible, budget):
    """Donor- and source-balanced screening restricted to VISIBLE addresses."""
    per_src = {}
    for d in donors: per_src[src_of_donor[d]] = per_src.get(src_of_donor[d], 0) + 1
    ns = len(per_src)
    acc = np.zeros(visible.size); w = 0.0
    for d in donors:
        if int(d) not in rho: continue
        r, live = rho[int(d)]
        ww = 1.0 / (ns * per_src[src_of_donor[d]])
        acc += ww * np.where(live & visible, r[targets_idx], 0.0)
        w += ww
    acc /= max(w, 1e-12)
    acc[~visible] = -1.0
    m = min(budget, int((acc > 0).sum()))
    if m <= 0: return np.empty(0, np.int64), acc
    # SCORE ORDER, descending, ties by address index. The frozen shortcut rule takes a
    # PREFIX of this list, so index-sorting here would make that prefix arbitrary.
    return np.lexsort((np.arange(acc.size), -acc))[:m].astype(np.int64), acc


ATK = CheapRidgeAttackerV1(alpha=ALPHA, max_features=MAXF)


def partial_r2(V, t, feats, base, tr_rows, tr_don, ev_rows, ev_don, src_of_donor):
    return ATK.incremental_r2(values=V, target=t, features=feats, visible=None,
                              train_rows=tr_rows, eval_rows=ev_rows,
                              eval_donor_codes=ev_don, train_donor_codes=tr_don,
                              source_by_donor=src_of_donor, precomputed_baseline=base)


def v1_neighbours(rho, donors, targets_idx, src_of_donor, n_addr):
    """Frozen V1 top-K recurrence, unchanged K and R, at this evidence budget."""
    votes = np.zeros((len(targets_idx), n_addr)); w = 0.0
    for d in donors:
        if int(d) not in rho: continue
        r, live = rho[int(d)]
        M = np.where(live, r, -1.0)
        k = min(V1_K, int(live.sum()) - 1)
        if k < 1: continue
        part = np.argpartition(M, -k, axis=1)[:, -k:]
        for i in range(len(targets_idx)):
            votes[i, part[i]] += 1.0
        w += 1.0
    frac = votes / max(w, 1e-12)
    return {i: np.flatnonzero(frac[i] >= V1_R) for i in range(len(targets_idx))}


results = {}
t0 = time.time()
for level, bpo in enumerate(LADDER, start=1):
    V, dcode, src_of_donor, addr = load(bpo)
    n_donor = src_of_donor.size
    print('\n=== LEVEL %d (blocks/op=%d): cells %d donors %d addr %d (%.1f min) ==='
          % (level, bpo, V.shape[0], n_donor, N_ADDR, (time.time() - t0) / 60), flush=True)
    targets = np.sort(seeded('targets').choice(N_ADDR, size=N_TARGETS, replace=False))
    rho = per_donor_rho(V, dcode, targets)
    S1, S2 = baseline_sums(V)
    print('  per-donor rho computed for %d donors (%.1f min)' % (len(rho), (time.time() - t0) / 60), flush=True)
    folds = stratified_outer_folds(src_of_donor, OUTER_FOLDS, NS)
    burden = int(round(MASK_FRACTION * N_ADDR))
    rec = {c: [] for c in ('U', 'V1', 'V2')}
    per_target = []
    n_short = 0
    for f in range(OUTER_FOLDS):
        val_d = np.flatnonzero(folds == f); tr_d = np.flatnonzero(folds != f)
        if val_d.size < 3: continue
        iA, iB = inner_rotation(tr_d, src_of_donor, NS)
        ev_rows = np.flatnonzero(np.isin(dcode, val_d)); ev_don = dcode[ev_rows]
        rowsA = np.flatnonzero(np.isin(dcode, iA)); donA = dcode[rowsA]
        rowsB = np.flatnonzero(np.isin(dcode, iB)); donB = dcode[rowsB]
        trrows = np.flatnonzero(np.isin(dcode, tr_d)); trdon = dcode[trrows]
        v1nb = v1_neighbours(rho, tr_d, targets, src_of_donor, N_ADDR)
        for ti, t in enumerate(targets):
            allvis = np.ones(N_ADDR, bool); allvis[t] = False
            base_disc = baseline_from_sums(V, S1, S2, np.array([t]), N_ADDR)
            # ---- discovery (training donors only), union of both rotation directions
            # Two INDEPENDENT discovery directions, as the frozen contract specifies:
            #   A screens -> B fits -> evaluate on A   (A never fits)
            #   B screens -> A fits -> evaluate on B   (B never fits)
            # The evaluation side is never the fitting side, so discovery is genuinely
            # cross-fitted. Shortcut sets are combined afterwards under UNION_WITH_SUPPORT.
            def _direction(screen_d, fit_rows, fit_don, eval_rows, eval_don):
                cnd, _ = screen(rho, screen_d, ti, src_of_donor, allvis, CAND_M)
                if cnd.size == 0:
                    return [], 0.0
                d0 = partial_r2(V, t, cnd, base_disc, fit_rows, fit_don,
                                eval_rows, eval_don, src_of_donor)
                p0 = d0['partial_r2']
                if p0 < NO_SHORTCUT_FLOOR:
                    return [], p0
                for n in range(1, min(SHORTCUT_CAP, cnd.size) + 1):
                    trial = np.setdiff1d(cnd, cnd[:n])
                    d2 = partial_r2(V, t, trial, base_disc, fit_rows, fit_don,
                                    eval_rows, eval_don, src_of_donor)
                    if d2['partial_r2'] <= SHORTCUT_REDUCTION * p0:
                        return list(cnd[:n]), p0
                return list(cnd[:min(SHORTCUT_CAP, cnd.size)]), p0

            sAB, pAB = _direction(iA, rowsB, donB, rowsA, donA)
            sBA, pBA = _direction(iB, rowsA, donA, rowsB, donB)
            # UNION_WITH_SUPPORT then the deterministic GLOBAL cap. Each direction may
            # return up to SHORTCUT_CAP; their union must still not exceed it.
            _, acc_tr = screen(rho, tr_d, ti, src_of_donor, allvis, CAND_M)
            short = combine_direction_shortcuts([sAB, sBA], acc_tr, SHORTCUT_CAP)
            assert len(short) <= SHORTCUT_CAP, "global shortcut cap violated"
            base_pr = max(pAB, pBA)
            if short: n_short += 1
            # ---- three matched-budget conditions, fresh refit each
            g = seeded(f'mask|{level}|{f}|{int(t)}')
            pool = np.setdiff1d(np.arange(N_ADDR), np.array([t]))
            masks = {}
            masks['U'] = set(g.choice(pool, size=burden - 1, replace=False).tolist()) | {int(t)}
            v1s = [int(x) for x in v1nb[ti] if x != t][:burden - 1]
            rest = np.setdiff1d(pool, np.array(v1s, dtype=np.int64)) if v1s else pool
            g2 = seeded(f'maskv1|{level}|{f}|{int(t)}')
            masks['V1'] = set(v1s) | set(g2.choice(rest, size=max(0, burden - 1 - len(v1s)), replace=False).tolist()) | {int(t)}
            s2 = [int(x) for x in short][:burden - 1]
            rest2 = np.setdiff1d(pool, np.array(s2, dtype=np.int64)) if s2 else pool
            g3 = seeded(f'maskv2|{level}|{f}|{int(t)}')
            masks['V2'] = set(s2) | set(g3.choice(rest2, size=max(0, burden - 1 - len(s2)), replace=False).tolist()) | {int(t)}
            row = {'fold': f, 'target': int(t), 'n_shortcut': len(short), 'disc_partial_r2': base_pr}
            for cname, mset in masks.items():
                mcols = np.array(sorted(mset), dtype=np.int64)
                vis = np.ones(N_ADDR, bool); vis[mcols] = False
                fc, _ = screen(rho, np.concatenate([iA, iB]), ti, src_of_donor, vis, CAND_M)
                bse = baseline_from_sums(V, S1, S2, mcols, N_ADDR)
                fr = partial_r2(V, t, fc, bse, trrows, trdon, ev_rows, ev_don, src_of_donor)
                rec[cname].append(fr['partial_r2'])
                row[cname] = fr['partial_r2']
            per_target.append(row)
        print('  fold %d done (%.1f min)' % (f, (time.time() - t0) / 60), flush=True)
    out = {c: {'mean': float(np.mean(v)), 'median': float(np.median(v)), 'n': len(v)}
           for c, v in rec.items() if v}
    u, v2 = np.array(rec['U']), np.array(rec['V2'])
    red = 100 * (u.mean() - v2.mean()) / max(abs(u.mean()), 1e-12) if u.size else float('nan')
    results[f'level{level}'] = {'blocks_per_op': bpo, 'cells': int(V.shape[0]), 'donors': int(n_donor),
                               'targets': int(N_TARGETS), 'burden': burden,
                               'targets_with_shortcut': n_short,
                               'shortcut_set_size_histogram': {
                                   str(k): int(sum(1 for r in per_target if r['n_shortcut'] == k))
                                   for k in range(0, SHORTCUT_CAP + 1)},
                               'target_folds_with_nonempty_shortcut': int(
                                   sum(1 for r in per_target if r['n_shortcut'] > 0)),
                               'target_folds_total': int(len(per_target)),
                               'mean_shortcut_set_size_when_nonempty': (
                                   float(np.mean([r['n_shortcut'] for r in per_target
                                                  if r['n_shortcut'] > 0]))
                                   if any(r['n_shortcut'] > 0 for r in per_target) else 0.0),
                               'max_shortcut_set_size': int(max([r['n_shortcut'] for r in per_target], default=0)),
                               'conditions': out,
                               'reduction_pct_V2_vs_U': float(red),
                               'abs_reduction': float(u.mean() - v2.mean()) if u.size else None,
                               'frac_improved': float(np.mean(v2 < u)) if u.size else None,
                               'per_target': per_target}
    hist = results[f'level{level}']['shortcut_set_size_histogram']
    print('  shortcut-set size histogram (0..8): %s' % {k: hist[k] for k in sorted(hist, key=int)}, flush=True)
    print('  target-folds with a NON-EMPTY capped shortcut set: %d of %d'
          % (results[f'level{level}']['target_folds_with_nonempty_shortcut'],
             results[f'level{level}']['target_folds_total']), flush=True)
    print('  U %.4f  V1 %.4f  V2 %.4f   reduction %.1f%%  shortcuts found %d/%d'
          % (out.get('U', {}).get('mean', float('nan')), out.get('V1', {}).get('mean', float('nan')),
             out.get('V2', {}).get('mean', float('nan')), red, n_short, N_TARGETS * OUTER_FOLDS), flush=True)
    json.dump(results, open(OUT / 'v2_full104_results.json', 'w'), indent=2, sort_keys=True)
print('\nwall %.1f min V2_FULL104_DONE' % ((time.time() - t0) / 60))
