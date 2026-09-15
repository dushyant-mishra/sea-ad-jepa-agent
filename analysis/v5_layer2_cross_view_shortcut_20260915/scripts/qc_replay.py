# Deterministic RE-DERIVATION of post-intervention QC from the SAME frozen realization.
# Reproduces screen.py's exact RNG call sequence; emits detected-address counts (not saved
# by screen.py) and library totals (which MUST match frozen lib_p* bit-for-bit).
import numpy as np, pandas as pd, csv, hashlib, json, pathlib, time, os
os.chdir(r'D:/Jepa project')
S=pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
ROOT=pathlib.Path('outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4')
MAN=pathlib.Path(r'D:/jepa_v5_run_20260913/docs/history/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/PHASE2_EXPRESSION_BLOCK_MANIFEST.csv')
THIN_NS='JEPA_V5_SAME_CELL_THINNING_V1'
PS=[1.00,0.90,0.75,0.50,0.25]
COND=[0.25, 0.25/0.75, 0.25/0.50, 0.15/0.25]
final=pd.read_csv(S/'final_manifest.csv')
want=dict(zip(final.selection_row,final.index))
blocks=sorted(final.block_idx.unique())
rows=list(csv.DictReader(MAN.open(newline='')))
N=len(final)
DET={p:np.full(N,-1,np.int64) for p in PS}      # detected addresses in ledger, post-intervention
LIB={p:np.full(N,-1,np.int64) for p in PS}      # library total incl. outside-ledger
LEDG=np.full(N,-1,np.int64); OUT=np.full(N,-1,np.int64)
nest_viol=0; seen=np.zeros(N,bool)
t0=time.time()
for bn,bi in enumerate(blocks):
    r=rows[bi]; z=np.load(ROOT/r['counts_path'],allow_pickle=False)
    indptr,indices,data=z['indptr'],z['indices'],z['data'].astype(np.int64)
    nr=len(indptr)-1
    md=list(csv.DictReader((ROOT/r['meta_path']).open(newline='')))
    sr=np.array([int(x['selection_row']) for x in md]); cid=[x['canonical_cell_id'] for x in md]
    lib=np.array([int(float(x['source_library'])) for x in md],np.int64)
    for i in range(nr):
        gi=want.get(int(sr[i]))
        if gi is None: continue
        a,b=indptr[i],indptr[i+1]
        ct=data[a:b]
        ledger=int(ct.sum()); outside=int(lib[i])-ledger
        LEDG[gi]=ledger; OUT[gi]=outside
        sd=int.from_bytes(hashlib.sha256('|'.join(map(str,(THIN_NS,cid[i]))).encode()).digest()[:8],'big')
        g=np.random.Generator(np.random.Philox(sd))
        rem=ct.copy(); cum=[]; tot=np.zeros(len(ct),np.int64)
        for q in COND:
            d_=g.binomial(rem,q); tot=tot+d_; cum.append(tot.copy()); rem=rem-d_
        sdo=int.from_bytes(hashlib.sha256('|'.join(map(str,(THIN_NS,cid[i],'OUTSIDE_LEDGER_TOTAL',outside))).encode()).digest()[:8],'big')
        go=np.random.Generator(np.random.Philox(sdo))
        orem=outside; ocum=[]; otot=0
        for q in COND:
            od=int(go.binomial(orem,q)); otot+=od; ocum.append(otot); orem-=od
        levels={0.25:(cum[0],ocum[0]),0.50:(cum[1],ocum[1]),0.75:(cum[2],ocum[2]),0.90:(cum[3],ocum[3]),1.00:(ct,outside)}
        # ascending-nesting check (the orientation screen.py got backwards)
        for k in range(3):
            if not (cum[k]<=cum[k+1]).all(): nest_viol+=1
        if len(ct) and not (cum[3]<=ct).all(): nest_viol+=1
        for p in PS:
            tc,to=levels[p]
            LIB[p][gi]=int(tc.sum())+int(to)
            DET[p][gi]=int((tc>0).sum())
        seen[gi]=True
    if (bn+1)%300==0: print('  %d/%d blocks %.1f min'%(bn+1,len(blocks),(time.time()-t0)/60),flush=True)
print('cells %d/%d  nesting_violations %d  wall %.1f min'%(int(seen.sum()),N,nest_viol,(time.time()-t0)/60),flush=True)
np.savez_compressed(S/'qc_post.npz',**{f'det_p{int(p*100)}':DET[p] for p in PS},
    **{f'lib_p{int(p*100)}':LIB[p] for p in PS},ledger=LEDG,outside=OUT,seen=seen,
    nest_violations=np.array([nest_viol]))
print('QC_REPLAY_DONE')
