import numpy as np, pathlib, json
R = pathlib.Path("D:/jepa_v77_synthetic_custody_20261005/regen/v75_100k/controls/measurement_null_a")
BLOCKS = {"z_global":4,"z_query":2,"z_reg_shared":3,"z_reg_private":2,"technical_latents":3}
acc={k:[] for k in BLOCKS}
for t in sorted((R/"hidden_truth").glob("TRUTH_*.npz")):
    z=np.load(t,allow_pickle=False)
    for k in BLOCKS: acc[k].append(z[k])
Z=np.concatenate([np.concatenate(acc[k],0) for k in BLOCKS],1).astype(np.float64)
NAMES=[f"{k}[{j}]" for k in BLOCKS for j in range(BLOCKS[k])]

cnt=[];avail=[]
for o in sorted((R/"observable_raw/FULL104_like_sharded").glob("RNA_*.npz")):
    z=np.load(o,allow_pickle=False); cnt.append(z["counts"].T); avail.append(z["availability"].T)
cnt=np.concatenate(cnt,0).astype(np.float64); avail=np.concatenate(avail,0).astype(np.float64)
ra=[];aa=[]
for m in sorted((R/"observable_raw/PAIRED_MULTIOME_like_sharded").glob("MULTIOME_*.npz")):
    z=np.load(m,allow_pickle=False); ra.append(z["rna_counts"].T); aa.append(z["atac_counts"].T)
ra=np.concatenate(ra,0).astype(np.float64); aa=np.concatenate(aa,0).astype(np.float64)

def cpm_log(X):
    s=X.sum(1,keepdims=True); s=np.where(s>0,s,1.0)
    return np.log1p(X/s*1e4)

VIEWS={
 "FULL104_RNA_only (the permitted partial-RNA view)": cpm_log(cnt),
 "FULL104_RNA + availability mask":                   np.c_[cpm_log(cnt),avail],
 "multiome_RNA_only":                                 cpm_log(ra),
 "multiome_ATAC_only":                                cpm_log(aa),
 "RNA(FULL104)+RNA(multi) both RNA views":            np.c_[cpm_log(cnt),cpm_log(ra)],
 "ALL modalities incl ATAC":                          np.c_[cpm_log(cnt),avail,cpm_log(ra),cpm_log(aa)],
}

rng=np.random.default_rng(20261005)
n=len(Z); perm=rng.permutation(n); tr,te=perm[:n//2],perm[n//2:]

def r2(X,y):
    X1=np.c_[np.ones(len(X)),X]
    B,*_=np.linalg.lstsq(X1[tr],y[tr],rcond=None)
    p=X1[te]@B
    ss=((y[te]-p)**2).sum(); tt=((y[te]-y[te].mean())**2).sum()
    return 1-ss/tt

out={}
print("HELD-OUT R2 of recovering each planted latent (50/50 split, linear oracle probe)\n")
hdr="%-22s"%"latent"+"".join("%14s"%v.split()[0][:13] for v in VIEWS)
print("%-22s %13s %13s %13s %13s %13s %13s"%("latent","FULL104","FULL104+mask","multiRNA","multiATAC","bothRNA","ALL"))
for j,nm in enumerate(NAMES):
    row=[r2(X,Z[:,j]) for X in VIEWS.values()]
    out[nm]={k:float(v) for k,v in zip(VIEWS,row)}
    print("%-22s %13.5f %13.5f %13.5f %13.5f %13.5f %13.5f"%(nm,*row))

print("\nblock means:")
c=0
blockmeans={}
for k,w in BLOCKS.items():
    vals=np.array([[out[NAMES[j]][v] for v in VIEWS] for j in range(c,c+w)]).mean(0)
    blockmeans[k]={kk:float(vv) for kk,vv in zip(VIEWS,vals)}
    print("%-22s %13.5f %13.5f %13.5f %13.5f %13.5f %13.5f"%(k,*vals))
    c+=w
json.dump({"per_latent":out,"per_block":blockmeans},
          open("C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad/reverse_r2.json","w"),indent=2)
