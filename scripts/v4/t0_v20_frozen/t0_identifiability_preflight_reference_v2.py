#!/usr/bin/env python3
"""Fail-closed metadata-only donor-level identifiability preflight for JEPA T0.

This is a reference implementation. It reads metadata only; no expression/model/F1 data.
Key invariants:
- source_col, when supplied, is always part of the nuisance/base design;
- reduced/full ranks are compared on exactly the same complete donor rows;
- a rank-deficient nuisance design is terminal rather than silently tolerated;
- target residual variation after nuisance projection is reported, not threshold-tuned.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd


def _is_numeric(s: pd.Series) -> bool:
    if s.dropna().empty:
        return False
    try:
        pd.to_numeric(s.dropna(), errors="raise")
        return True
    except Exception:
        return False


def donor_table(df: pd.DataFrame, donor: str, cols: list[str]) -> pd.DataFrame:
    missing=[c for c in [donor,*cols] if c not in df.columns]
    if missing:
        raise RuntimeError("STOP_MISSING_COLUMNS__"+"__".join(missing))
    rows=[]
    for did,g in df.groupby(donor,sort=True,dropna=False):
        if pd.isna(did):
            raise RuntimeError("STOP_MISSING_DONOR_ID")
        row={donor:did}
        for c in cols:
            vals=g[c].dropna().unique()
            if len(vals)==0:
                row[c]=np.nan
            elif len(vals)==1:
                row[c]=vals[0]
            else:
                raise RuntimeError(f"STOP_WITHIN_DONOR_NONCONSTANT__{c}__{did}")
        row["_cells"]=len(g)
        rows.append(row)
    return pd.DataFrame(rows)


def encode_complete(s: pd.Series, prefix: str) -> tuple[np.ndarray,list[str]]:
    """Encode a complete (no missing) donor-level series."""
    if s.isna().any():
        raise ValueError("encode_complete received missing values")
    if _is_numeric(s) and s.nunique(dropna=False)>2:
        return pd.to_numeric(s,errors="raise").to_numpy(float)[:,None],[prefix]
    cats=sorted(map(str,s.unique()))
    if len(cats)<=1:
        return np.empty((len(s),0),float),[]
    ss=s.astype(str)
    arr=[]; names=[]
    for cat in cats[1:]:
        arr.append((ss==cat).to_numpy(float)); names.append(f"{prefix}[{cat}]")
    return np.stack(arr,axis=1),names


def design(donors: pd.DataFrame, cols: list[str]) -> tuple[np.ndarray,list[str]]:
    blocks=[np.ones((len(donors),1),float)]; names=["intercept"]
    for c in cols:
        x,n=encode_complete(donors[c],c)
        blocks.append(x); names.extend(n)
    X=np.concatenate(blocks,axis=1)
    if not np.isfinite(X).all():
        raise RuntimeError("STOP_NONFINITE_DESIGN")
    return X,names


def matrix_rank(X: np.ndarray) -> int:
    if X.ndim!=2:
        raise ValueError("X must be 2-D")
    s=np.linalg.svd(X,compute_uv=False)
    tol=max(X.shape)*np.finfo(float).eps*(s[0] if len(s) else 0.0)
    return int((s>tol).sum())


def residual_fraction(X0: np.ndarray, T: np.ndarray) -> float:
    """Frobenius residual variation / centered total variation, report-only."""
    if T.size==0:
        return 0.0
    coef=np.linalg.lstsq(X0,T,rcond=None)[0]
    resid=T-X0@coef
    centered=T-T.mean(axis=0,keepdims=True)
    den=float(np.sum(centered*centered))
    num=float(np.sum(resid*resid))
    if den<=0:
        return 0.0
    return num/den


def evaluate(df: pd.DataFrame, donor_col: str, target_col: str,
             source_col: str|None=None, covariates: list[str]|None=None) -> dict:
    covariates=list(covariates or [])
    base=[]
    if source_col and source_col not in base:
        base.append(source_col)
    for c in covariates:
        if c not in base:
            base.append(c)
    cols=[]
    for c in [*base,target_col]:
        if c not in cols: cols.append(c)
    donors=donor_table(df,donor_col,cols)

    # One common complete-case donor set for reduced and full models.
    complete=donors[[*base,target_col]].notna().all(axis=1)
    d=donors.loc[complete].reset_index(drop=True)
    if len(d)==0:
        return _doc("NOT_IDENTIFIABLE_NO_COMPLETE_DONORS",donors,d,base,target_col,source_col)

    X0,n0=design(d,base)
    X1,n1=design(d,[*base,target_col])
    r0=matrix_rank(X0); r1=matrix_rank(X1)
    p0=X0.shape[1]; p1=X1.shape[1]
    target_cols=n1[len(n0):]
    inc=r1-r0

    if r0 < p0:
        terminal="NOT_IDENTIFIABLE_NUISANCE_RANK_DEFICIENT"
    elif not target_cols:
        terminal="NOT_IDENTIFIABLE_TARGET_CONSTANT"
    elif r1 < p1:
        terminal="NOT_IDENTIFIABLE_FULL_RANK_DEFICIENT"
    elif inc != len(target_cols):
        terminal="NOT_IDENTIFIABLE_TARGET_ALIASED"
    elif len(d) <= p1:
        terminal="NOT_IDENTIFIABLE_NO_RESIDUAL_DF"
    else:
        terminal="IDENTIFIABLE"

    T=X1[:,len(n0):] if target_cols else np.empty((len(d),0),float)
    frac=residual_fraction(X0,T)

    source_support={}
    if source_col:
        for src,g in d.groupby(source_col,sort=True):
            source_support[str(src)]={
                "donors":int(len(g)),
                "target_unique":int(g[target_col].nunique(dropna=True)),
            }

    return {
        "schema":"T0_IDENTIFIABILITY_PREFLIGHT_REFERENCE_V2",
        "terminal":terminal,
        "donors_total":int(len(donors)),
        "donors_complete":int(len(d)),
        "base_terms":base,
        "nuisance_columns":n0,
        "nuisance_rank":r0,
        "nuisance_column_count":p0,
        "full_columns":n1,
        "full_rank":r1,
        "full_column_count":p1,
        "target_encoded_columns":target_cols,
        "target_rank_increment":inc,
        "target_residual_variation_fraction_report_only":float(frac),
        "residual_df":int(len(d)-r1),
        "source_target_support":source_support,
        "firewall":{"expression_read":False,"model_output_read":False,"f1_outcome_read":False},
    }


def _doc(term, donors, d, base, target, source):
    return {
        "schema":"T0_IDENTIFIABILITY_PREFLIGHT_REFERENCE_V2",
        "terminal":term,
        "donors_total":int(len(donors)),"donors_complete":int(len(d)),
        "base_terms":base,"target_encoded_columns":[],"target_rank_increment":0,
        "target_residual_variation_fraction_report_only":0.0,
        "source_target_support":{},
        "firewall":{"expression_read":False,"model_output_read":False,"f1_outcome_read":False},
    }


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--metadata",type=Path,required=True)
    ap.add_argument("--donor-col",default="donor_id")
    ap.add_argument("--target-col",required=True)
    ap.add_argument("--source-col",default=None)
    ap.add_argument("--covariate",action="append",default=[])
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    doc=evaluate(pd.read_csv(a.metadata),a.donor_col,a.target_col,a.source_col,a.covariate)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n")
    print(json.dumps(doc,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
