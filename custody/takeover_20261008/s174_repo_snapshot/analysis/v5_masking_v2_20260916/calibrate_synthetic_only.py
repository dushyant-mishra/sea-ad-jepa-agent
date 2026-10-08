"""SYNTHETIC-ONLY calibration of candidate budget m and ridge penalty alpha.

No real FULL104 value influences these choices. Run BEFORE the V2 contract freezes.
Selection rule, declared here before the numbers are read:
  1. maximise planted-shortcut recall across S1/S2/S3
  2. subject to null partial R2 < 0.10 on every nuisance fixture
  3. tie-break: smallest candidate budget, then LARGEST alpha (weakest attacker)
"""
import json, sys, pathlib
import numpy as np
sys.path.insert(0, 'tests'); sys.path.insert(0, 'src')
from test_v5_shortcut_predictability_v2 import world, screen_and_attack

M_GRID = [20, 40, 80, 160]
A_GRID = [1e-3, 1e-2, 1e-1]
NUISANCES = [None, 'donor', 'operator', 'source', 'within_donor_depth', 'within_donor_shift']
rows = []
for m in M_GRID:
    for a in A_GRID:
        recall, plant_scores = [], []
        for seed, plant, truth_n in ((1, 'single', 1), (2, 'redundant', 4), (3, 'distributed', 4)):
            V, d, s, meas, truth = world(np.random.default_rng(seed), plant=plant)
            cand, p, _ = screen_and_attack(V, d, s, meas, budget=m, alpha=a)
            recall.append(len([t for t in truth if t in cand]) / len(truth))
            plant_scores.append(p)
        nulls = []
        for c in NUISANCES:
            V, d, s, meas, _ = world(np.random.default_rng(4), plant='none', confound=c)
            _, p, _ = screen_and_attack(V, d, s, meas, budget=m, alpha=a)
            nulls.append(p)
        rows.append(dict(m=m, alpha=a, recall=float(np.mean(recall)),
                         min_plant=float(min(plant_scores)), max_null=float(max(nulls)),
                         passes_null=bool(max(nulls) < 0.10)))
ok = [r for r in rows if r['passes_null']]
print('%-6s %-8s %8s %10s %10s %8s' % ('m', 'alpha', 'recall', 'min_plant', 'max_null', 'null_ok'))
for r in rows:
    print('%-6d %-8.0e %8.3f %10.3f %10.4f %8s' % (r['m'], r['alpha'], r['recall'],
                                                    r['min_plant'], r['max_null'], r['passes_null']))
if not ok:
    print('\nNO CONFIGURATION SATISFIES THE NULL CONSTRAINT'); sys.exit(1)
best = sorted(ok, key=lambda r: (-r['recall'], r['m'], -r['alpha']))[0]
print('\nSELECTED (frozen rule): m=%d alpha=%.0e  recall=%.3f min_plant=%.3f max_null=%.4f'
      % (best['m'], best['alpha'], best['recall'], best['min_plant'], best['max_null']))
json.dump({'grid': rows, 'selected': best,
           'selection_rule': 'max recall; null partial R2 < 0.10 on every nuisance; '
                             'tie-break smallest m then largest alpha',
           'synthetic_only': True, 'no_real_full104_input': True},
          open('analysis/v5_masking_v2_20260916/calibration_synthetic_only.json', 'w'),
          indent=2, sort_keys=True)
