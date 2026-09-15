import numpy as np, pandas as pd, json, pathlib
S=pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
D=json.load(open(S/'aud_design.json')); Bo={int(k):v for k,v in D['Bo'].items()}
Ns=D['Ns']; Ntot=D['N_total']; SRC=3
fm=pd.read_csv(S/'final_manifest.csv',usecols=['selection_row','donor_id','block_key','operator_index','source','stratum'])
base=fm[fm.stratum=='BASE_MECHANICS'].reset_index(drop=True)
base['q']=base.operator_index.map({o:min(12,B)/B for o,B in Bo.items()})

def audit(name,w,df):
    w=np.asarray(w,float); tot=w.sum(); wn=w/tot
    by=pd.Series(w).groupby(df.source.values).sum()
    blk=pd.Series(wn).groupby(df.block_key.values).sum()
    opm=pd.Series(wn).groupby(df.operator_index.values).sum()
    return dict(estimand=name,n_cells=int(len(w)),
      total_estimated_target_mass=float(tot),
      mass_by_source={k:float(v) for k,v in by.items()},
      normalized_mass_by_source={k:float(v/tot) for k,v in by.items()},
      w_min=float(w.min()),w_median=float(np.median(w)),w_max=float(w.max()),
      kish_ess=float(tot**2/(w**2).sum()),
      kish_ess_frac=float((tot**2/(w**2).sum())/len(w)),
      max_norm_cell_weight=float(wn.max()),
      max_block_contribution=float(blk.max()),
      max_operator_contribution=float(opm.max()),
      n_blocks=int(df.block_key.nunique()),n_operators=int(df.operator_index.nunique()),
      n_donors=int(df.donor_id.nunique()))

R=[]
# A. EMPIRICAL / FULL104-STRUCTURE  p_i = 1/N_total
wA=(1.0/Ntot)/base.q.values
R.append(audit('EMPIRICAL_FULL104_STRUCTURE',wA,base))
# B. SOURCE-UNIFORM  p_i = 1/(S*N_s)
pB=base.source.map({k:1.0/(SRC*v) for k,v in Ns.items()}).values
wB=pB/base.q.values
R.append(audit('SOURCE_UNIFORM_CELL_WITHIN_SOURCE',wB,base))
# C. DONOR-PRIMARY / OPERATOR-BALANCED  a_dc = 1/(|O_d| * n_do)
ndo=base.groupby(['donor_id','operator_index']).size().rename('n_do')
Od=base.groupby('donor_id').operator_index.nunique().rename('Od')
t=base.join(ndo,on=['donor_id','operator_index']).join(Od,on='donor_id')
wC=(1.0/(t.Od.values*t.n_do.values))
R.append(audit('DONOR_PRIMARY_OPERATOR_BALANCED',wC,base))

print('%-36s %10s %12s %10s %8s %10s %10s'%('ESTIMAND','n','HT_mass','KishESS','ESS%','maxblock','maxop'))
for r in R:
    print('%-36s %10d %12.6f %10.0f %7.1f%% %10.4f %10.4f'%(r['estimand'],r['n_cells'],
      r['total_estimated_target_mass'],r['kish_ess'],100*r['kish_ess_frac'],
      r['max_block_contribution'],r['max_operator_contribution']))
print()
for r in R:
    print('%s'%r['estimand'])
    print('   normalized source mass: %s'%{k:round(v,5) for k,v in r['normalized_mass_by_source'].items()})
    print('   weight min/med/max: %.4e / %.4e / %.4e   max single-cell norm weight %.3e'%(
      r['w_min'],r['w_median'],r['w_max'],r['max_norm_cell_weight']))
print()
# donor-primary verification
wCn=wC/wC.sum(); dm=pd.Series(wCn).groupby(base.donor_id.values).sum()
print('=== DONOR-PRIMARY VERIFICATION ===')
print('  donors %d   donor mass min %.6f max %.6f  (uniform target %.6f)  max|dev| %.2e'%(
  len(dm),dm.min(),dm.max(),1/len(dm),float(np.abs(dm-1/len(dm)).max())))
wd=pd.DataFrame({'d':base.donor_id.values,'o':base.operator_index.values,'w':wC})
g=wd.groupby(['d','o']).w.sum()
dev=[]
for d,gg in g.groupby(level=0):
    dev.append(float((gg/gg.sum()).std()))
print('  within-donor operator mass: max sd across donors %.3e (0 = perfectly balanced)'%max(dev))
print('  source mass INDUCED by donor distribution: %s'%{k:round(v,5) for k,v in R[2]['normalized_mass_by_source'].items()})
print()
print('=== INDEPENDENT UNIT COUNTS (NOT the Kish cell ESS) ===')
print('  primary inclusion unit = BLOCK (whole blocks sampled): %d'%base.block_key.nunique())
print('  donors %d   operators %d   sources 3'%(base.donor_id.nunique(),base.operator_index.nunique()))
cells_per_block=base.groupby('block_key').size()
print('  cells per selected block: min %d median %d max %d'%(cells_per_block.min(),cells_per_block.median(),cells_per_block.max()))
json.dump({'estimands':R,'donor_mass_max_abs_dev':float(np.abs(dm-1/len(dm)).max()),
  'within_donor_operator_mass_max_sd':float(max(dev)),
  'independent_units':{'primary_inclusion_unit':'BLOCK','blocks':int(base.block_key.nunique()),
    'donors':int(base.donor_id.nunique()),'operators':int(base.operator_index.nunique()),'sources':3}},
  open(S/'aud_weights.json','w'),indent=2,sort_keys=True)
np.save(S/'w_base_A.npy',wA); np.save(S/'w_base_B.npy',wB); np.save(S/'w_base_C.npy',wC)
print('WEIGHT_AUDIT_DONE')
