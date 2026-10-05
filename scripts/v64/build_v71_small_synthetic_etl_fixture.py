#!/usr/bin/env python3
from __future__ import annotations
import csv, gzip, hashlib, json
from pathlib import Path
import numpy as np

def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def build(root: Path, seed: int=7101):
    rng=np.random.default_rng(seed)
    raw=root/"observable_raw"; truth=root/"hidden_truth"
    raw.mkdir(parents=True,exist_ok=True); truth.mkdir(parents=True,exist_ok=True)
    n_cells,n_genes,n_peaks=120,24,30
    barcodes=np.array([f"CELL{i:04d}-1" for i in range(n_cells)],dtype="U16")
    genes=np.array([f"ENSG_SYN_{i:05d}" for i in range(n_genes)],dtype="U32")
    peaks=np.array([f"chr1:{1000+i*100}-{1050+i*100}" for i in range(n_peaks)],dtype="U40")
    features=np.concatenate([genes,peaks])
    feature_types=np.array(["Gene Expression"]*n_genes+["Peaks"]*n_peaks,dtype="U20")
    donor=np.array([f"D{i%8:02d}" for i in range(n_cells)],dtype="U4")
    source=np.array(["SEA_AD" if i<80 else "NPH52" if i<105 else "HVS" for i in range(n_cells)],dtype="U8")
    # latent truth never written to observable root
    z_global=rng.normal(size=(n_cells,3))
    z_shared=rng.normal(size=(n_cells,2))
    z_private=rng.normal(size=(n_cells,2))
    depth=rng.lognormal(mean=7.5,sigma=.45,size=n_cells)
    Wg=rng.normal(scale=.25,size=(5,n_genes))
    Wa=rng.normal(scale=.25,size=(7,n_peaks))
    eta_g=np.c_[z_global,z_shared]@Wg + np.log1p(depth)[:,None]*.08
    eta_a=np.c_[z_global,z_shared,z_private]@Wa + np.log1p(depth)[:,None]*.08
    rna=rng.poisson(np.exp(np.clip(eta_g,-3,3))).astype(np.int32)
    atac=rng.poisson(np.exp(np.clip(eta_a,-3,3))).astype(np.int32)
    # structural missing block for HVS: last six genes unavailable; encode with availability mask, not zeros-as-measured.
    avail=np.ones((len(features),n_cells),dtype=np.uint8)
    hvs=np.where(source=="HVS")[0]
    avail[n_genes-6:n_genes,hvs]=0
    matrix=np.vstack([rna.T,atac.T])
    matrix[avail==0]=0
    np.savez_compressed(raw/"multiome_like_matrix.npz",matrix=matrix,features=features,feature_types=feature_types,barcodes=barcodes,availability=avail)
    with gzip.open(raw/"cell_metadata.csv.gz","wt",newline="") as f:
        w=csv.writer(f); w.writerow(["barcode","donor","source","cell_type","Diagnosis","Braak"])
        for i,b in enumerate(barcodes):
            # protected-like columns present, not used in generation of selection
            w.writerow([b,donor[i],source[i],"Microglia","SYNTHETIC_PROTECTED",int(i%7)])
    observable={
      "schema":"V71_SMALL_CI_OBSERVABLES_V1","challenge_version":"small-ci-v1",
      "matrix_file":"multiome_like_matrix.npz","metadata_file":"cell_metadata.csv.gz",
      "n_cells":n_cells,"n_features":len(features),"n_genes":n_genes,"n_peaks":n_peaks,
      "genome_build":"hg38","synthetic":True,
      "forbidden_selection_fields":["Diagnosis","Braak"]
    }
    (raw/"OBSERVABLES.json").write_text(json.dumps(observable,indent=2)+"\n")
    truth_obj={
      "schema":"V71_SMALL_CI_HIDDEN_TRUTH_V1","seed":seed,
      "z_global":z_global.tolist(),"z_reg_shared":z_shared.tolist(),"z_reg_private":z_private.tolist(),
      "structural_missing_cells":hvs.tolist(),"structural_missing_gene_indices":list(range(n_genes-6,n_genes))
    }
    (truth/"TRUTH.json").write_text(json.dumps(truth_obj)+"\n")
    manifest={}
    for p in sorted(raw.iterdir()):
        manifest[p.name]={"bytes":p.stat().st_size,"sha256":sha256(p)}
    (raw/"MANIFEST.json").write_text(json.dumps({"schema":"V71_SMALL_CI_RAW_MANIFEST_V1","files":manifest},indent=2)+"\n")
    return root

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--seed",type=int,default=7101)
    a=ap.parse_args(); build(Path(a.out),a.seed); print(Path(a.out).resolve())
