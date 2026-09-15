import json, hashlib, pathlib, shutil, os
S = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
R = pathlib.Path(r'D:/jepa_layer2_20260915')
D = R / 'analysis' / 'v5_layer2_cross_view_shortcut_20260915'
(D / 'scripts').mkdir(parents=True, exist_ok=True)
(D / 'results').mkdir(parents=True, exist_ok=True)
(D / 'withdrawn').mkdir(parents=True, exist_ok=True)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 22), b''):
            h.update(c)
    return h.hexdigest()


SCRIPTS = ['qc_replay.py', 'w1_design.py', 'w2_audit.py', 'g1_geo.py', 'g2_stress.py', 'g3_spec.py',
           'g4_qc.py', 'g5_verify.py', 'g6_receipt.py', 'g7_weighted.py',
           'x1_spec.py', 'x2_audit.py', 'x3_nuis.py', 'x5_within.py', 'x6_fixture.py',
           'y1_source.py', 'y2_donor.py', 'y3_qc.py', 'y4_ln.py',
           'z1_repro.py', 'z2_estimand.py', 'z3_donorrec.py', 'z5_lodo.py', 'z6_closeout.py', 'z7_stage.py']
RESULTS = ['aud_design.json', 'aud_weights.json', 'aud_geometry.json', 'aud_stress.json', 'aud_spectra.json',
           'aud_qc.json', 'aud_verify.json', 'aud_weighted_response.json', 'aud_hashes.json',
           'x_audit.json', 'x_nuisance.json', 'x_within.json', 'x_fixture.json',
           'y_source.json', 'y_donor.json', 'y_qc.json', 'y_ln.json',
           'z_repro.json', 'z_estimand.json', 'z_donorrec.json', 'z_lodo.json',
           'screen_mech.json', 'freeze_receipt.json', 'screen_sample_plan.json']
TOP = ['V5_LAYER2_CROSS_VIEW_SHORTCUT_CLOSEOUT.json', 'X_CROSS_VIEW_SHORTCUT_AUDIT_SPEC.json',
       'Z_RESIDUAL_OVER_CONTEXT_SPECIFICATION.md',
       'V5_VALUE_ONLY_SAME_CELL_MEASUREMENT_PREFLIGHT_RECEIPT.json']

for n in SCRIPTS:
    if (S / n).exists():
        shutil.copy2(S / n, D / 'scripts' / n)
for n in RESULTS:
    if (S / n).exists():
        shutil.copy2(S / n, D / 'results' / n)
for n in TOP:
    if (S / n).exists():
        shutil.copy2(S / n, D / n)

# withdrawn defective implementation, kept so the defect claim is verifiable
if (S / 'x4_within.py').exists():
    hdr = ('"""WITHDRAWN - DEFECTIVE. DO NOT RUN.\n\n'
           'This implementation double-centred training data inconsistently across folds. On a\n'
           'controlled fixture containing ONLY operator-level shared structure and ZERO cell-level\n'
           'shared signal it reported substantial "within-operator signal". Its outputs were\n'
           'discarded and never entered the evidence record. Superseded by scripts/x5_within.py,\n'
           'which is validated in scripts/x6_fixture.py (null fixture -0.0068, recovery 0.233/0.595,\n'
           'negative control -0.0020). Retained only so the defect claim can be reproduced.\n"""\n\n')
    (D / 'withdrawn' / 'x4_within_DEFECTIVE.py').write_text(hdr + (S / 'x4_within.py').read_text())

# large artifacts referenced, not committed
LARGE = {
    'screen_out.npz': 'frozen VALUE_ONLY same-cell thinning output (5 p-levels x 2 views x 201,149 cells)',
    'qc_post.npz': 're-derived post-intervention Q_DEPTH/Q_DETECT; bit-identical replay of screen_out',
    'bind_population.npz': 'bound cell index and fold identities; deterministically regenerable from final_manifest.csv',
    'final_manifest.csv': 'frozen sample manifest (201,149 cells: BASE_MECHANICS + source-conditional stress strata)',
    'pair_plan.csv': 'frozen pair plan (154,631 pairs)',
    'rowmap.csv': 'FULL104 population row map (4,553,407 cells) used to derive B_o and q_i',
}
refs = {}
for n, desc in LARGE.items():
    p = S / n
    if p.exists():
        refs[n] = {'path': str(p), 'size_bytes': p.stat().st_size, 'sha256': sha(p), 'description': desc}
SUB = pathlib.Path(r'D:/jepa_v5_substrate_20260914')
for n, d in [('V0_full.npy', 'disjoint-view substrate, view 0'), ('V1_full.npy', 'disjoint-view substrate, view 1')]:
    p = SUB / n
    if p.exists():
        refs[n] = {'path': str(p), 'size_bytes': p.stat().st_size, 'sha256_declared_in_manifest': True,
                   'description': d}
(D / 'LARGE_ARTIFACT_REFERENCES.json').write_text(json.dumps(
    {'policy': ('Large binary artifacts are referenced by path, size and SHA-256 rather than committed, '
                'per the project production-run protocol. Every committed result is reproducible from these '
                'inputs using the committed scripts.'),
     'artifacts': refs}, indent=2, sort_keys=True))

n_s = len(list((D / 'scripts').glob('*.py')))
n_r = len(list((D / 'results').glob('*.json')))
print('staged: %d scripts, %d result files, %d top-level docs, %d large-artifact references'
      % (n_s, n_r, len(list(D.glob('*.json'))) + len(list(D.glob('*.md'))), len(refs)))
for n, r in sorted(refs.items()):
    print('  %-24s %14d bytes  %s' % (n, r['size_bytes'], r.get('sha256', 'in manifest')[:16]))
