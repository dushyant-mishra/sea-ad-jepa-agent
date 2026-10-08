"""Derived FULL104 census: measured-zero frequency, evidence-budget feasibility,
remaining-RNA, burden-failure rates, ESS/precision, target x outer-fold support.
Read-only. No RIDGE8/TOP8/PREFIX3 outcome is opened."""
import numpy as np, pathlib, json, hashlib

P = pathlib.Path(r'D:/Jepa project')
OUT = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad/census')
d = np.load(OUT / 'pass1.npz', allow_pickle=True)
cell_donor = d['cell_donor']; cell_op = d['cell_op']; cell_nnz_tot = d['cell_nnz_tot']
cell_nnz_core = d['cell_nnz_core']; donor_addr_nnz = d['donor_addr_nnz']
donor_src = d['donor_src']; core = d['core']
st = np.load(P / 'exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz',
             allow_pickle=False)['states']
NA = 41238; NCORE = core.size; SRCN = ['HVS', 'NPH52', 'SEA_AD']
panel = (st == 1).sum(1)
R = {}

print('=' * 74)
print('1. MEASURED-ZERO vs STRUCTURAL-MISSING   (atlas said PENDING -- now computed)')
print('=' * 74)
psize = panel[cell_op].astype(np.int64)
mz = psize - cell_nnz_tot
sm = NA - psize
print('  per-cell means over all 4,553,407 cells (of 41,238 addresses):')
print('    measured nonzero   %10.1f  (%.4f)' % (cell_nnz_tot.mean(), cell_nnz_tot.mean() / NA))
print('    measured ZERO      %10.1f  (%.4f)   <- measured_zero_frequency' % (mz.mean(), mz.mean() / NA))
print('    structural missing %10.1f  (%.4f)' % (sm.mean(), sm.mean() / NA))
print('  measured_zero_frequency (zero / measured) = %.6f' % (mz.sum() / psize.sum()))
R['measured_zero_frequency_over_measured'] = float(mz.sum() / psize.sum())
print()
print('  by source:')
for s in range(3):
    m = donor_src[cell_donor] == s
    print('    %-7s cells=%9d  nonzero=%8.1f  meas_zero=%9.1f  struct_miss=%8.1f  mz_frac=%.6f'
          % (SRCN[s], m.sum(), cell_nnz_tot[m].mean(), mz[m].mean(), sm[m].mean(), mz[m].sum() / psize[m].sum()))
print()
print('  WITHIN TERMINAL COMMON CORE (17,186 addr, measured-scalar in ALL 42 operators):')
cz = NCORE - cell_nnz_core.astype(np.int64)   # int64: int32 accumulation overflows at 4.55M cells
print('    measured nonzero %9.1f    measured ZERO %9.1f    structural missing 0 by construction'
      % (cell_nnz_core.mean(), cz.mean()))
print('    core measured_zero_frequency = %.6f' % (cz.sum() / (len(cell_op) * float(NCORE))))
R['core_measured_zero_frequency'] = float(cz.sum() / (len(cell_op) * float(NCORE)))
for s in range(3):
    m = donor_src[cell_donor] == s
    print('      %-7s core nonzero %8.1f  (%.4f of core)' % (SRCN[s], cell_nnz_core[m].mean(), cell_nnz_core[m].mean() / NCORE))
q = np.percentile(cell_nnz_core, [0, 1, 5, 25, 50, 75, 95, 99, 100])
print('    core-nonzero per-cell pct 0/1/5/25/50/75/95/99/100: ' + ' '.join('%d' % x for x in q))
R['core_nonzero_percentiles'] = [float(x) for x in q]

print()
print('=' * 74)
print('2. EVIDENCE-BUDGET FEASIBILITY / REMAINING MEASURED RNA AFTER MASKING')
print('=' * 74)
print('  Universe = terminal common core (17,186). Burden B = round(f * 17186).')
print('  Expected remaining measured RNA after masking fraction f = (1-f) * core_nonzero.')
rows = []
for f in (0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50):
    B = int(round(f * NCORE)); rem = (1 - f) * cell_nnz_core
    r = {'f': f, 'burden_B': B, 'mean_remaining': float(rem.mean()),
         'p01_remaining': float(np.percentile(rem, 1)), 'min_remaining': float(rem.min())}
    for K in (32, 64, 128, 256):
        r['frac_cells_below_%d' % K] = float((rem < K).mean())
    rows.append(r)
    print('   f=%.2f B=%5d  mean_rem=%8.1f  p01=%7.1f  min=%6.1f   <32:%.5f <64:%.5f <128:%.5f <256:%.5f'
          % (f, B, r['mean_remaining'], r['p01_remaining'], r['min_remaining'],
             r['frac_cells_below_32'], r['frac_cells_below_64'], r['frac_cells_below_128'], r['frac_cells_below_256']))
R['evidence_budget'] = rows
print()
print('  BURDEN-FEASIBILITY FAILURE (cells that cannot supply B distinct MEASURED maskees):')
for f in (0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50):
    B = int(round(f * NCORE))
    print('   f=%.2f B=%5d  cells with core_nonzero < B : %9d  (%.6f)'
          % (f, B, int((cell_nnz_core < B).sum()), float((cell_nnz_core < B).mean())))

print()
print('=' * 74)
print('3. TARGET x OUTER-FOLD SUPPORT  (source-stratified donor-held-out, 4 folds)')
print('=' * 74)
fold = np.full(104, -1, int)
for s in range(3):
    ds = np.flatnonzero(donor_src == s)
    seed = int.from_bytes(hashlib.sha256(('JEPA_FULL104_CENSUS_FOLD|' + SRCN[s]).encode()).digest()[:8], 'big')
    for i, dd in enumerate(np.random.default_rng(seed).permutation(ds)):
        fold[dd] = i % 4
print('  fold sizes (donors): ' + str([int((fold == k).sum()) for k in range(4)]))
for s in range(3):
    print('    %-7s per fold: %s' % (SRCN[s], [int(((fold == k) & (donor_src == s)).sum()) for k in range(4)]))
MINCELL = 30
core_ok = (donor_addr_nnz >= MINCELL)[:, core]
print()
print('  estimability = donor has >= %d cells with a nonzero value at that address' % MINCELL)
print('  donors supporting each core address: mean %.1f  median %.1f  min %d'
      % (core_ok.sum(0).mean(), float(np.median(core_ok.sum(0))), int(core_ok.sum(0).min())))
per_fold = []
allok = np.ones(NCORE, bool)
for k in range(4):
    trd = np.flatnonzero(fold != k); vad = np.flatnonzero(fold == k)
    ok = (core_ok[trd].sum(0) >= 20) & (core_ok[vad].sum(0) >= 5)
    allok &= ok; per_fold.append(int(ok.sum()))
    print('   fold %d: train=%2d val=%2d   core addr with train>=20 & val>=5 : %6d (%.4f)'
          % (k, len(trd), len(vad), int(ok.sum()), float(ok.mean())))
print('   core addresses estimable in ALL FOUR folds : %6d  (%.4f)  <- eligible target panel'
      % (int(allok.sum()), float(allok.mean())))
R['eligible_target_panel_all_folds'] = int(allok.sum())
R['per_fold_estimable'] = per_fold

print()
print('=' * 74)
print('4. EFFECTIVE SAMPLE SIZE / PRECISION (clustered by donor)')
print('=' * 74)
dc = np.bincount(cell_donor, minlength=104).astype(np.float64)
print('  cells %d over 104 donors; donor sizes min %d median %d max %d'
      % (int(dc.sum()), int(dc.min()), int(np.median(dc)), int(dc.max())))
kish = dc.sum() ** 2 / (dc ** 2).sum()
print('  Kish ESS over donor clusters = %.1f donor-equivalents' % kish)
print('  independent inclusion units for any DONOR-level claim = 104; cells do NOT raise this')
for s in range(3):
    m = donor_src == s; ds = dc[m]
    print('    %-7s donors=%3d cells=%9d  Kish ESS=%.1f' % (SRCN[s], int(m.sum()), int(ds.sum()), ds.sum() ** 2 / (ds ** 2).sum()))
R['kish_ess_donor_clusters'] = float(kish); R['independent_donor_units'] = 104

print()
print('=' * 74)
print('5. RESOURCE / RUNTIME / MEMORY')
print('=' * 74)
print('  FULL104 Level-4 counts blocks on disk : 44.4 GB (8,915 npz, mean 4.98 MB)')
print('  sparsity-only full pass (this census)  : 27.9 min wall, ~0.5 GB RSS')
print('  dense core slice float32, 17,186 addresses:')
for nc in (50_000, 250_000, 1_000_000, 4_553_407):
    print('     %9d cells -> %8.1f GB dense' % (nc, 17186 * nc * 4 / 1e9))
print('  => FULL104 dense core is NOT materializable; runner must stream or subsample addresses.')
json.dump(R, open(OUT / 'census_summary.json', 'w'), indent=2)
print()
print('CENSUS_DERIVED_DONE')
