#!/usr/bin/env python3
"""Acquire and structurally subset public GSE214979 for external SCENIC+ development.

No disease/pathology values are used to choose features, cells, topics or regulators.
Possible Morabito-overlap donors 1224/1230/1238 are excluded from the DEFAULT
development subset prospectively; an all-microglia subset is also retained for audit.

This script downloads only the filtered 10x multiome matrix + metadata. The 59.3-GB
fragment file is deliberately not required for the first submitted-peak-matrix route.
"""
from __future__ import annotations
import gzip, hashlib, json, os, re, subprocess
from pathlib import Path
import h5py, numpy as np, pandas as pd
from scipy import sparse

BASE="https://ftp.ncbi.nlm.nih.gov/geo/series/GSE214nnn/GSE214979/suppl"
FILES={
 "metadata":"GSE214979_cell_metadata.csv.gz",
 "matrix":"GSE214979_filtered_feature_bc_matrix.h5",
}
OVERLAP_DONORS={"1224","1230","1238"}

def sh(cmd):
    subprocess.run(cmd, check=True)

def sha256(path, chunk=8<<20):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        while True:
            b=f.read(chunk)
            if not b: break
            h.update(b)
    return h.hexdigest()

def download(url,out):
    if Path(out).exists() and Path(out).stat().st_size>0:
        return
    sh(["curl","-L","--fail","--retry","5","--retry-delay","3","-o",str(out),url])

def dec(a):
    return np.array([x.decode() if isinstance(x,(bytes,np.bytes_)) else str(x) for x in a],dtype=object)

def read_10x_h5(path):
    with h5py.File(path,"r") as h:
        g=h["matrix"]
        shape=tuple(int(x) for x in g["shape"][:])
        data=g["data"][:]
        indices=g["indices"][:]
        indptr=g["indptr"][:]
        barcodes=dec(g["barcodes"][:])
        fg=g["features"]
        names=dec(fg["name"][:])
        ids=dec(fg["id"][:])
        ftypes=dec(fg["feature_type"][:]) if "feature_type" in fg else np.array(["UNKNOWN"]*len(names),dtype=object)
        genome=dec(fg["genome"][:]) if "genome" in fg else np.array(["UNKNOWN"]*len(names),dtype=object)
    mat=sparse.csc_matrix((data,indices,indptr),shape=shape)
    return mat,barcodes,names,ids,ftypes,genome

def normalize_barcode(x):
    s=str(x)
    # preserve exact first, then common prefixed forms are handled by suffix candidate.
    return s

def best_barcode_column(df, barcodes):
    bset=set(map(str,barcodes))
    candidates=[]
    barcode_re=re.compile(r"^[ACGT]+-[0-9]+$")
    for c in df.columns:
        s=df[c].astype(str)
        head=s.head(100).tolist()
        regex_hits=sum(bool(barcode_re.match(v)) for v in head)
        exact=int(s.isin(bset).sum())
        candidates.append((exact,regex_hits,c))
    candidates.sort(reverse=True)
    exact,regex_hits,c=candidates[0]
    if exact < min(1000, int(0.5*len(df))):
        raise RuntimeError(
            f"No credible barcode column by exact 10x match. "
            f"Top candidates: {candidates[:10]}; columns={list(df.columns)}"
        )
    return c,candidates[:10]

def celltype_candidates(df):
    out=[]
    if "predicted.id" in df.columns:
        s=df["predicted.id"].astype(str)
        n=int((s=="Microglia").sum())
        if n:
            out.append((10**9,n,"predicted.id",["Microglia"]))
    pat=re.compile(r"microgl",re.I)
    for c in df.columns:
        s=df[c].astype(str)
        n=int(s.str.contains(pat,na=False).sum())
        if n:
            uniq=sorted(s[s.str.contains(pat,na=False)].unique().tolist())[:30]
            score=(100 if re.search(r"cell.*type|celltype|annotation|cluster|predicted",c,re.I) else 0)+n
            out.append((score,n,c,uniq))
    out.sort(reverse=True)
    if not out: raise RuntimeError("No metadata column contains a microglia-like label")
    return out

def donor_candidates(df):
    out=[]
    for c in df.columns:
        s=df[c].astype(str)
        hits=sum(int((s==d).sum()) for d in OVERLAP_DONORS)
        score=(1000 if re.search(r"donor|subject|individual",c,re.I) else 0)+hits
        if hits or re.search(r"donor|subject|individual",c,re.I):
            out.append((score,hits,c,sorted(s.unique().tolist())[:50]))
    out.sort(reverse=True)
    if not out: raise RuntimeError("No donor/subject metadata column found")
    return out

def metadata_barcode_values(df,col,barcodes):
    bset=set(map(str,barcodes))
    vals=df[col].astype(str).tolist()
    return np.array([v if v in bset else None for v in vals],dtype=object)

def save_subset(prefix, mat, sel_cols, barcodes, names, ids, ftypes, genome):
    sm=mat[:,sel_cols].tocsc()
    sparse.save_npz(prefix+".npz",sm,compressed=True)
    pd.DataFrame({"barcode":barcodes[sel_cols]}).to_csv(prefix+".barcodes.csv.gz",index=False)
    pd.DataFrame({"feature_index":np.arange(len(names)),"id":ids,"name":names,"feature_type":ftypes,"genome":genome}).to_csv(prefix+".features.csv.gz",index=False)
    return {"shape":[int(x) for x in sm.shape],"nnz":int(sm.nnz),"npz_sha256":sha256(prefix+".npz"),"npz_bytes":Path(prefix+".npz").stat().st_size}

def main():
    out=Path(os.environ.get("OUT_DIR","gse214979_acquisition")); out.mkdir(parents=True,exist_ok=True)
    for k,n in FILES.items(): download(f"{BASE}/{n}",out/n)
    meta_path=out/FILES["metadata"]; h5_path=out/FILES["matrix"]
    df=pd.read_csv(meta_path,compression="gzip")
    mat,barcodes,names,ids,ftypes,genome=read_10x_h5(h5_path)
    bc_col,bc_diag=best_barcode_column(df,barcodes)
    ct_diag=celltype_candidates(df); ct_col=ct_diag[0][2]
    donor_diag=donor_candidates(df); donor_col=donor_diag[0][2]
    mapped=metadata_barcode_values(df,bc_col,barcodes)
    micro_mask=(df[ct_col].astype(str)=="Microglia").to_numpy() if ct_col=="predicted.id" else df[ct_col].astype(str).str.contains("microgl",case=False,na=False).to_numpy()
    donor_vals=df[donor_col].astype(str).to_numpy()
    development_mask=micro_mask & ~np.isin(donor_vals,list(OVERLAP_DONORS))
    pos={b:i for i,b in enumerate(barcodes)}
    def cols(mask):
        v=[mapped[i] for i in np.flatnonzero(mask) if mapped[i] is not None and mapped[i] in pos]
        return np.array([pos[x] for x in v],dtype=int)
    all_cols=cols(micro_mask); dev_cols=cols(development_mask)
    if len(dev_cols)<100:
        raise RuntimeError(f"Development microglia subset implausibly small: {len(dev_cols)}")
    fcounts={str(x):int((ftypes==x).sum()) for x in sorted(set(ftypes))}
    all_rec=save_subset(str(out/"GSE214979_microglia_all_feature_bc"),mat,all_cols,barcodes,names,ids,ftypes,genome)
    dev_rec=save_subset(str(out/"GSE214979_microglia_dev_no_morabito_overlap_feature_bc"),mat,dev_cols,barcodes,names,ids,ftypes,genome)
    # diagnosis/pathology columns are enumerated only by NAME and never read into selection logic.
    forbidden_name_cols=[c for c in df.columns if re.search(r"diagn|patholog|braak|cerad|disease|case|control|ad\b",c,re.I)]
    receipt={
      "schema":"V69_GSE214979_SCENICPLUS_ACQUISITION_RECEIPT_V1",
      "source":"GEO GSE214979",
      "source_urls":{k:f"{BASE}/{n}" for k,n in FILES.items()},
      "source_sha256":{k:sha256(out/n) for k,n in FILES.items()},
      "source_bytes":{k:(out/n).stat().st_size for k,n in FILES.items()},
      "matrix_shape_features_by_cells":[int(x) for x in mat.shape],
      "matrix_nnz":int(mat.nnz),
      "feature_type_counts":fcounts,
      "metadata_rows":int(len(df)),
      "barcode_column":bc_col,
      "barcode_match_diagnostics":bc_diag,
      "celltype_column":ct_col,
      "microglia_label_diagnostics":ct_diag[:10],
      "donor_column":donor_col,
      "donor_diagnostics":donor_diag[:10],
      "all_microglia_cells":int(len(all_cols)),
      "default_development_microglia_cells":int(len(dev_cols)),
      "prospectively_excluded_possible_morabito_overlap_donors":sorted(OVERLAP_DONORS),
      "diagnosis_pathology_columns_not_used_for_selection":forbidden_name_cols,
      "all_microglia_subset":all_rec,
      "development_subset":dev_rec,
      "fragments_file":{
        "url":f"{BASE}/GSE214979_atac_fragments.tsv.gz",
        "geo_reported_size":"59.3 GB",
        "downloaded":False,
        "reason":"first-pass SCENIC+ route uses submitted filtered gene+peak matrix; fragment-level consensus-peak recaller remains an optional sensitivity route"
      },
      "status":"PASS_STRUCTURAL_ACQUISITION__NO_DISEASE_OR_PATHOLOGY_SELECTION"
    }
    rp=out/"V69_GSE214979_SCENICPLUS_ACQUISITION_RECEIPT_V1.json"
    rp.write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))
if __name__=="__main__":
    main()
