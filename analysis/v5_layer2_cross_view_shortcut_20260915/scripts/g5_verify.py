import numpy as np, pandas as pd, json, pathlib, hashlib
S=pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
PS=[100,90,75,50,25]; TGT={100:1.00,90:0.90,75:0.75,50:0.50,25:0.25}
q=np.load(S/'qc_post.npz'); z=np.load(S/'screen_out.npz')
fm=pd.read_csv(S/'final_manifest.csv')
V={}
# identity / uniqueness
V['selection_row_unique']=bool(fm.selection_row.is_unique)
V['canonical_cell_id_unique']=bool(fm.canonical_cell_id.is_unique)
V['N']=int(len(fm))
# full-library arithmetic
lhs=q['ledger']+q['outside']; rhs=fm.source_library.values.astype(np.int64)
V['ledger_plus_outside_equals_source_library_exact']=bool((lhs==rhs).all())
V['ledger_plus_outside_max_abs_diff']=float(np.abs(lhs-rhs).max())
V['outside_ledger_nonneg']=bool((q['outside']>=0).all())
V['outside_ledger_zero_cells']=int((q['outside']==0).sum())
V['outside_ledger_mass_fraction']=float(q['outside'].sum()/rhs.sum())
# qdepth row authority
dep=np.load(S/'qdepth_cnt.npy'); det=np.load(S/'qdetect_cnt.npy')
V['qdepth_row_authority_matches_ledger']=bool((dep[fm.selection_row.values]==q['ledger']).all())
V['qdetect_row_authority_matches_p1_detect']=bool((det[fm.selection_row.values]==q['det_p100']).all())
# p=1 identity replay
V['p1_identity_lib_equals_source_library']=bool((z['lib_p100']==rhs).all())
V['replay_vs_frozen_total_deviation']=float(sum(np.abs(q['lib_p%d'%p].astype(np.float64)-z['lib_p%d'%p]).max() for p in PS))
# nesting
V['nesting_violations_ascending_correct_orientation']=int(q['nest_violations'][0])
V['screen_mech_json_nesting_flag_raw']=json.load(open(S/'screen_mech.json'))['nesting_monotone']
V['screen_mech_json_nesting_flag_note']=('recorded flag is FALSE due to a checker orientation defect in screen.py '
  '(it iterated PS descending while asserting prev<=tc ascending); correct-orientation re-verification over the '
  'same frozen realization gives 0 violations, and frozen library totals are monotone with 0 violations')
V['lib_total_nesting_violations']=int(sum((q['lib_p%d'%a]>q['lib_p%d'%b]).sum() for a,b in zip(PS[1:],PS[:-1])))
# analytic thinning sanity
V['analytic_retention']={}
for p in PS:
    obs=float(q['lib_p%d'%p].sum()/q['lib_p100'].sum())
    V['analytic_retention']['%.2f'%(p/100)]={'observed':obs,'target':TGT[p],'abs_error':abs(obs-TGT[p])}
V['analytic_retention_max_abs_error']=max(v['abs_error'] for v in V['analytic_retention'].values())
# zero-library accounting (unconditional denominators)
V['zero_library']={'%.2f'%(p/100):{'attempted':int(len(fm)),'non_estimable':int((q['lib_p%d'%p]<=0).sum())} for p in PS}
for k,v in V.items():
    if not isinstance(v,(dict,)): print('  %-56s %s'%(k,v))
print()
print('  analytic retention: '+'  '.join('p=%s %.6f(t=%.2f)'%(k,v['observed'],v['target']) for k,v in V['analytic_retention'].items()))
print('  zero-library non-estimable: '+'  '.join('p=%s %d/%d'%(k,v['non_estimable'],v['attempted']) for k,v in V['zero_library'].items()))
json.dump(V,open(S/'aud_verify.json','w'),indent=2,sort_keys=True,default=str)
# hashes
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<22),b''): h.update(c)
    return h.hexdigest()
H={}
for n in ['final_manifest.csv','pair_plan.csv','screen_out.npz','qc_post.npz','screen.py','rebuild.py',
          'qc_replay.py','w1_design.py','w2_audit.py','g1_geo.py','g2_stress.py','g3_spec.py','g4_qc.py',
          'g5_verify.py','aud_design.json','aud_weights.json','aud_geometry.json','aud_stress.json',
          'aud_spectra.json','aud_qc.json','aud_verify.json','screen_mech.json','freeze_receipt.json',
          'screen_sample_plan.json','ablation.json','partition_v1.json']:
    p=S/n
    if p.exists(): H[n]=sha(p)
json.dump(H,open(S/'aud_hashes.json','w'),indent=2,sort_keys=True)
print()
print('=== ARTIFACT HASHES ===')
for k,v in sorted(H.items()): print('  %-28s %s'%(k,v))
print('VERIFY_DONE')
