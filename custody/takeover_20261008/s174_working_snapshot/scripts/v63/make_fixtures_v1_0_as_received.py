import numpy as np, pandas as pd, anndata as ad, scipy.sparse as sp
rng=np.random.default_rng(1)
def build(prefix, n_per_donor, mg_per_donor, raw_in_x, atac_sep="_", mismatch=True, frac_shared=0.9):
    donors=[f"D{i:02d}" for i in range(len(n_per_donor))]
    cohorts=["NABEC" if i%2==0 else "HBCC" for i in range(len(donors))]
    obs=[]
    for d,c,n,m in zip(donors,cohorts,n_per_donor,mg_per_donor):
        ct=["MG"]*m+list(rng.choice(["ExN","InN","Oligo","Astro","OPC","VC"],n-m))
        for j,t in enumerate(ct): obs.append((f"{d}_{j:06d}",t,d,c))
    obs=pd.DataFrame(obs,columns=["bc","cell_type","sample_id","cohort"]).set_index("bc")
    obs["age"]=rng.integers(15,100,len(obs)); obs["sex"]=rng.choice(["M","F"],len(obs)); obs["PMI"]=rng.uniform(5,40,len(obs)); obs["seq_batch"]="b1"
    for c in ["cell_type","sample_id","cohort","sex"]: obs[c]=obs[c].astype("category")
    counts=sp.random(len(obs),300,density=0.05,format="csr",random_state=1,data_rvs=lambda k: rng.integers(1,20,k)).astype(np.float32)
    rna=ad.AnnData(X=counts.copy(),obs=obs.copy(),var=pd.DataFrame(index=[f"GENE{i}" for i in range(300)]))
    if not raw_in_x:
        lib=np.asarray(counts.sum(1)).ravel(); lib[lib==0]=1
        norm=sp.diags(1e6/lib)@counts; norm.data=np.log1p(norm.data)
        rna.X=norm.astype(np.float32); rna.layers["counts"]=counts
    keep=rng.random(len(obs))<frac_shared
    aobs=obs[keep].copy()
    if atac_sep!="_": aobs.index=[i.replace("_",atac_sep) for i in aobs.index]
    if mismatch and atac_sep=="_":
        aobs["sample_id"]=aobs["sample_id"].astype(str); aobs.iloc[0,aobs.columns.get_loc("sample_id")]="WRONG"; aobs["sample_id"]=aobs["sample_id"].astype("category")
    peaks=sp.random(len(aobs),500,density=0.03,format="csr",random_state=2,data_rvs=lambda k: rng.integers(1,4,k)).astype(np.float32)
    atac=ad.AnnData(X=peaks,obs=aobs,var=pd.DataFrame(index=[f"chr1:{i*1000}-{i*1000+500}" for i in range(500)]))
    rna.write_h5ad(f"{prefix}_rna.h5ad"); atac.write_h5ad(f"{prefix}_atac.h5ad")
    truth={"n_rna":len(obs),"n_atac":int(keep.sum()),"shared":int(keep.sum()) if atac_sep=="_" else 0,
           "mg_total":int(sum(mg_per_donor)),"mg_paired":int(((obs.cell_type=="MG").values & keep).sum()),
           "mg_per_donor":dict(zip(donors,mg_per_donor))}
    return truth
import json
tA=build("A",[400,300,500,250],[40,0,75,12],raw_in_x=False)
tB=build("B",[200,200],[10,30],raw_in_x=True,atac_sep="#",mismatch=False)
json.dump({"A":tA,"B":tB},open("truth.json","w"),indent=1); print(json.dumps({"A":tA,"B":tB}))
