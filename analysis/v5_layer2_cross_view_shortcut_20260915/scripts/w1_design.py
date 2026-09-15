import numpy as np, pandas as pd, hashlib, json, pathlib
S=pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
SNS='JEPA_V5_MECHANICS_SCALE_MEASUREMENT_SCREEN_SAMPLE_V1'
rm=pd.read_csv(S/'rowmap.csv',usecols=['selection_row','donor_id','block_key','operator_index','source'])
fm=pd.read_csv(S/'final_manifest.csv',usecols=['selection_row','donor_id','block_key','operator_index','source','stratum'])
print('population rows %d  final rows %d'%(len(rm),len(fm)))
base=fm[fm.stratum=='BASE_MECHANICS']; stress=fm[fm.stratum!='BASE_MECHANICS']
print('BASE %d  STRESS %d  overlap_selection_rows %d'%(len(base),len(stress),
      len(set(base.selection_row)&set(stress.selection_row))))

# ---- reproduce the declared selection rule from block identifiers ONLY ----
blk=rm[['block_key','operator_index']].drop_duplicates()
def h(bk): return hashlib.sha256(f'{SNS}|{bk}'.encode()).hexdigest()
blk['hh']=[h(b) for b in blk.block_key]
repro=set()
Bo={}
for o,g in blk.groupby('operator_index'):
    Bo[int(o)]=len(g)
    repro|=set(g.sort_values('hh').block_key.head(12))
frozen=set(base.block_key.unique())
print()
print('=== BLOCK SELECTION RULE REPRODUCTION (inputs: namespace + block_key only) ===')
print('  population blocks %d  operators %d'%(len(blk),len(Bo)))
print('  frozen BASE blocks   %d'%len(frozen))
print('  reproduced blocks    %d'%len(repro))
print('  exact set match      %s'%(repro==frozen))
print('  missing from repro   %d   extra in repro %d'%(len(frozen-repro),len(repro-frozen)))

# ---- within-block completeness: are whole blocks taken? ----
popcnt=rm.groupby('block_key').size()
basecnt=base.groupby('block_key').size()
cmp=pd.DataFrame({'pop':popcnt.reindex(basecnt.index),'base':basecnt})
cmp['whole']=cmp.pop==cmp.base if False else (cmp['pop']==cmp['base'])
print()
print('=== WHOLE-BLOCK INCLUSION ===')
print('  selected blocks %d   taken whole %d   partial %d'%(len(cmp),int(cmp.whole.sum()),int((~cmp.whole).sum())))
if (~cmp.whole).any():
    print(cmp[~cmp.whole].head(10))

# ---- q_i ----
bo=pd.Series({o:min(12,B) for o,B in Bo.items()})
BoS=pd.Series(Bo)
q=(bo/BoS).rename('q')
print()
print('=== CELL INCLUSION PROBABILITY q_i = min(12,B_o)/B_o ===')
print('  operators with B_o<=12 (q=1): %d'%int((BoS<=12).sum()))
print('  q min %.6f  median %.6f  max %.6f  ratio %.1fx'%(q.min(),q.median(),q.max(),q.max()/q.min()))
Ns=rm.source.value_counts(); Ntot=len(rm)
print()
print('=== POPULATION ==='); print('  N_total %d'%Ntot)
for s,n in Ns.items(): print('    %-8s %8d  (%.4f)'%(s,n,n/Ntot))
np.save(S/'aud_Bo.npy',np.array([Bo[o] for o in sorted(Bo)]))
json.dump({'Bo':{str(k):int(v) for k,v in Bo.items()},'Ns':{k:int(v) for k,v in Ns.items()},
  'N_total':int(Ntot),'repro_exact':bool(repro==frozen),'whole_block':bool(cmp.whole.all()),
  'base_stress_overlap':int(len(set(base.selection_row)&set(stress.selection_row)))},
  open(S/'aud_design.json','w'),indent=2,sort_keys=True)
print('DESIGN_DONE')
