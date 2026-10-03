#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, json, zlib
from pathlib import Path
import numpy as np

AUTHORITY=Path('results/v64/V73_FULL104_RNA_QC_CALIBRATION_AUTHORITY_50K_V1.json')

def sha256_file(path:Path): return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path:Path=AUTHORITY):
    meta=json.loads(path.read_text())
    if meta.get('status')!='QUALIFIED_SAMPLED_QC_AUTHORITY': raise ValueError('QC authority not qualified')
    enc=''.join(Path(p).read_text().strip() for p in meta['payload_parts']); comp=base64.b64decode(enc)
    if hashlib.sha256(comp).hexdigest()!=meta['payload_compressed_sha256']: raise ValueError('QC compressed digest mismatch')
    raw=zlib.decompress(comp)
    if hashlib.sha256(raw).hexdigest()!=meta['payload_canonical_json_sha256']: raise ValueError('QC canonical digest mismatch')
    qc=json.loads(raw)
    if qc['sample_total_cells']!=meta['sample_total_cells'] or qc['population_total_cells']!=meta['population_total_cells']:
        raise ValueError('QC authority totals disagree')
    return meta,qc

def by_operator(path:Path=AUTHORITY):
    meta,qc=load(path); return meta,{r['operator_id']:r for r in qc['strata']}

def interp_quantiles(u,probs,values):
    return np.interp(np.asarray(u,dtype=np.float64),np.asarray(probs,dtype=np.float64),np.asarray(values,dtype=np.float64))
