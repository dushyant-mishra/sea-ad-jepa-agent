#!/usr/bin/env python3
"""Deterministic byte serialization for JEPA T0 learned target authority."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
import numpy as np


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def _write_f64le(path: Path, arr) -> None:
    a=np.asarray(arr,dtype='<f8')
    if not np.isfinite(a).all(): raise ValueError(f'nonfinite {path.name}')
    path.write_bytes(np.ascontiguousarray(a).tobytes(order='C'))


def serialize_target(outdir, fit: dict, address_rows: list[dict]) -> dict:
    out=Path(outdir)
    if out.exists() and any(out.iterdir()): raise ValueError('output directory must be absent or empty')
    out.mkdir(parents=True,exist_ok=True)
    beta=np.asarray(fit['beta']); mu=np.asarray(fit['mu']); sigma=np.asarray(fit['sigma']); mask=np.asarray(fit['decision_gene_mask']); cv=np.asarray(fit['cv_mse_by_multiplier']); exps=np.asarray(fit['multiplier_exponents'])
    if beta.ndim!=1: raise ValueError('beta must be 1-D')
    g=len(beta)
    if mu.shape!=(g,) or sigma.shape!=(g,) or mask.shape!=(g,): raise ValueError('target vector shape mismatch')
    if cv.ndim!=1 or exps.ndim!=1 or len(cv)!=len(exps) or len(cv)==0: raise ValueError('CV grid shape mismatch')
    if len(address_rows)!=g: raise ValueError('address row count mismatch')
    required=('molecular_address_index','molecular_address_id','symbol','biotype')
    seen=[]
    for r in address_rows:
        if any(k not in r for k in required): raise ValueError('address schema mismatch')
        seen.append(str(r['molecular_address_id']))
    if len(set(seen))!=len(seen): raise ValueError('duplicate address id')

    _write_f64le(out/'T0_TARGET_BETA_F64LE.bin',beta)
    _write_f64le(out/'T0_TARGET_MU_F64LE.bin',mu)
    _write_f64le(out/'T0_TARGET_SIGMA_F64LE.bin',sigma)
    (out/'T0_TARGET_DECISION_MASK_U8.bin').write_bytes(np.asarray(mask,dtype=np.uint8).tobytes())
    _write_f64le(out/'T0_TARGET_CV_MSE_F64LE.bin',cv)
    _write_f64le(out/'T0_TARGET_MULTIPLIER_EXPONENTS_F64LE.bin',exps)

    # CSV uses \n line endings and UTF-8, preserving supplied feature order.
    with (out/'T0_TARGET_ADDRESS_REGISTRY.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(required),lineterminator='\n')
        w.writeheader()
        for r in address_rows:
            w.writerow({k:r[k] for k in required})

    donors=[str(x) for x in np.asarray(fit['canonical_donor_order']).tolist()]
    meta={
        'schema':'JEPA_T0_TARGET_MODEL_V1',
        'numeric_dtype':'float64_little_endian',
        'array_order':'C',
        'features':g,
        'selected_multiplier_index':int(fit['selected_multiplier_index']),
        'selected_multiplier_exponent':float(fit['selected_multiplier_exponent']),
        'final_lambda':float(fit['final_lambda']),
        'final_trace_scale':float(fit['final_trace_scale']),
        'response_residual_sd':float(fit['response_residual_sd']),
        'discovery_age_center':float(fit['discovery_age_center']),
        'canonical_donor_order':donors,
        'nuisance':'intercept + centered_age + centered_age_squared + binary_sex_0_1',
        'learner':'donor_pseudobulk_nuisance_partialled_dual_ridge_LOODO_multiplier_v1',
    }
    (out/'T0_TARGET_METADATA.json').write_text(json.dumps(meta,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n',encoding='utf-8')

    members=[p for p in out.iterdir() if p.is_file() and p.name not in {'T0_TARGET_MANIFEST.csv','T0_TARGET_PACKAGE_ROOT_SHA256.txt'}]
    members=sorted(members,key=lambda p:p.name.encode('utf-8'))
    with (out/'T0_TARGET_MANIFEST.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f,lineterminator='\n'); w.writerow(['filename','bytes','sha256'])
        for p in members: w.writerow([p.name,p.stat().st_size,sha256_file(p)])
    root=sha256_file(out/'T0_TARGET_MANIFEST.csv')
    (out/'T0_TARGET_PACKAGE_ROOT_SHA256.txt').write_text(root+'\n',encoding='ascii')
    return {'package_root_sha256':root,'manifest_sha256':root,'files':len(members)}
