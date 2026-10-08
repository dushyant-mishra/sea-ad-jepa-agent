import numpy as np, json, pathlib, glob
R = pathlib.Path("D:/jepa_v77_synthetic_custody_20261005/regen/v75_100k/controls/measurement_null_a")
T = sorted((R/"hidden_truth").glob("TRUTH_*.npz"))
O = sorted((R/"observable_raw/FULL104_like_sharded").glob("RNA_*.npz"))
M = sorted((R/"observable_raw/PAIRED_MULTIOME_like_sharded").glob("MULTIOME_*.npz"))
print("shards: truth=%d full104=%d multiome=%d" % (len(T),len(O),len(M)))

BLOCKS = {"z_global":4,"z_query":2,"z_reg_shared":3,"z_reg_private":2,"technical_latents":3}
acc={k:[] for k in BLOCKS}; donor=[]; op=[]; src=[]; gidx=[]
for t in T:
    z=np.load(t,allow_pickle=False)
    for k in BLOCKS: acc[k].append(z[k])
    donor.append(z["donor_index"]); op.append(z["operator_index"]); src.append(z["source_index"])
    gidx.append(z["global_cell_index"])
for k in BLOCKS: acc[k]=np.concatenate(acc[k],0)
donor=np.concatenate(donor); op=np.concatenate(op); src=np.concatenate(src); gidx=np.concatenate(gidx)
n=len(donor); print("cells=%d donors=%d operators=%d sources=%d"%(n,len(np.unique(donor)),len(np.unique(op)),len(np.unique(src))))

Z=np.concatenate([acc[k] for k in BLOCKS],1).astype(np.float64)
NAMES=[f"{k}[{j}]" for k in BLOCKS for j in range(BLOCKS[k])]
print("\ntruth latent dims = %d  (names: %s)"%(Z.shape[1], ", ".join(NAMES)))

def icc(x, g):
    """between-group variance fraction = ICC"""
    gs=np.unique(g); gm=np.array([x[g==q].mean() for q in gs]); cnt=np.array([(g==q).sum() for q in gs])
    grand=x.mean()
    between=(cnt*(gm-grand)**2).sum()/n
    total=x.var()
    return between/total if total>0 else np.nan

print("\n=== ICC of each planted latent by grouping (0 => no group structure) ===")
print("%-22s %10s %10s %10s" % ("latent","donor","operator","source"))
for j,nm in enumerate(NAMES):
    print("%-22s %10.6f %10.6f %10.6f" % (nm, icc(Z[:,j],donor), icc(Z[:,j],op), icc(Z[:,j],src)))

print("\n=== marginal shape of planted latents (rare-state / mixture check) ===")
print("%-22s %8s %8s %8s %8s %10s" % ("latent","mean","sd","skew","kurt","|z|>3 frac"))
for j,nm in enumerate(NAMES):
    x=Z[:,j]; m=x.mean(); s=x.std()
    sk=((x-m)**3).mean()/s**3; ku=((x-m)**4).mean()/s**4
    print("%-22s %8.4f %8.4f %8.4f %8.4f %10.5f" % (nm,m,s,sk,ku,(np.abs((x-m)/s)>3).mean()))
print("  reference: standard normal has skew 0, kurtosis 3.0, |z|>3 fraction 0.00270")

# cross-latent independence
C=np.corrcoef(Z.T)
off=C[~np.eye(len(NAMES),dtype=bool)]
print("\nmax |corr| between distinct planted latents: %.5f" % np.abs(off).max())

# ---- observables ----
cnt=[]; avail=[]; depth=[]; det=[]
for o in O:
    z=np.load(o,allow_pickle=False)
    cnt.append(z["counts"].T); avail.append(z["availability"].T)
    depth.append(z["empirical_projected_panel_count_target_int"])
    det.append(z["empirical_projected_detected_feature_target_int"])
cnt=np.concatenate(cnt,0); avail=np.concatenate(avail,0)
depth=np.concatenate(depth).astype(np.float64); det=np.concatenate(det).astype(np.float64)
print("\nFULL104 counts matrix:",cnt.shape," availability:",avail.shape)
print("availability ICC by operator: %.6f   by donor: %.6f" % (icc(avail.sum(1).astype(float),op), icc(avail.sum(1).astype(float),donor)))
print("panel depth ICC by operator : %.6f   by donor: %.6f" % (icc(depth,op), icc(depth,donor)))

print("\n=== does measurement depend on BIOLOGY? (biology x operator interaction test) ===")
print("%-22s %12s %12s" % ("latent","corr w/ depth","corr w/ n_avail"))
na=avail.sum(1).astype(float)
for j,nm in enumerate(NAMES):
    print("%-22s %12.6f %12.6f" % (nm, np.corrcoef(Z[:,j],depth)[0,1], np.corrcoef(Z[:,j],na)[0,1]))

# ---- multiome ----
ra=[]; aa=[]
for m in M:
    z=np.load(m,allow_pickle=False); ra.append(z["rna_counts"].T); aa.append(z["atac_counts"].T)
ra=np.concatenate(ra,0).astype(np.float64); aa=np.concatenate(aa,0).astype(np.float64)
print("\nmultiome rna:",ra.shape," atac:",aa.shape)

def r2_from_latents(Y, X, k=20):
    """mean R2 of predicting first k features of Y from latents X (linear, closed form)"""
    X1=np.c_[np.ones(len(X)),X]
    B=np.linalg.lstsq(X1,Y[:,:k],rcond=None)[0]
    P=X1@B
    ss=((Y[:,:k]-P)**2).sum(0); tt=((Y[:,:k]-Y[:,:k].mean(0))**2).sum(0)
    return float(np.mean(1-ss/np.where(tt>0,tt,1)))

idx={}
c=0
for k,w in BLOCKS.items():
    idx[k]=list(range(c,c+w)); c+=w

print("\n=== linear recoverability of observables from each planted block (mean R2, first 20 features) ===")
L=np.log1p(cnt.astype(np.float64))
LR=np.log1p(ra); LA=np.log1p(aa)
for k in BLOCKS:
    X=Z[:,idx[k]]
    print("  %-20s FULL104 %7.4f   multiRNA %7.4f   multiATAC %7.4f"
          % (k, r2_from_latents(L,X), r2_from_latents(LR,X), r2_from_latents(LA,X)))
Xall=Z
print("  %-20s FULL104 %7.4f   multiRNA %7.4f   multiATAC %7.4f"
      % ("ALL 14", r2_from_latents(L,Xall), r2_from_latents(LR,Xall), r2_from_latents(LA,Xall)))
