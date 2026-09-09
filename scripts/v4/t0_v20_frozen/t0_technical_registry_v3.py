from __future__ import annotations
from t0_technical_registry_v2 import build_technical_registry, load_technical_registry
RESERVED={'donor_id','AT8','age','sex','IMMUNE_FRACTION','STATE_SCORE','TAIL_PREVALENCE'}

def build_technical_registry_v3(outdir,blocks,source_authority_hashes,audit_note):
    for b in blocks:
        if any(c in RESERVED for c in b.get('columns',[])): raise ValueError('outcome/nuisance/composition/state fields cannot be declared as extra technical covariates')
    return build_technical_registry(outdir,blocks,source_authority_hashes,audit_note)

def load_technical_registry_v3(outdir):
    r=load_technical_registry(outdir)
    for cols in r['blocks'].values():
        if any(c in RESERVED for c in cols): raise ValueError('stored technical registry contains reserved scientific field')
    return r
