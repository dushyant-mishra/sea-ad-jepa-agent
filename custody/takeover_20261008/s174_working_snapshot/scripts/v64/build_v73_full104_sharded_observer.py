#!/usr/bin/env python3
"""FULL104-like RNA observer calibrated to authenticated operator-level QC summaries.

Biology controls relative gene programs. Frozen 50k source/operator QC summaries control
technical depth, measured support and structural availability. The 96-gene panel is a
projection of the measured 41,238-address library; full-library depths are never reported
as panel totals.

V74 closes a V73 defect where detected-feature and zero-fraction targets were decorative.
Depth and detected support are now consumed behaviorally. Their frozen within-operator
dependence summary is used only as a descriptive Gaussian-copula approximation; it does
not define any biological threshold or acceptance criterion.

V75 separates the immutable truth/operator-model seed from the stochastic measurement
realization seed. Omitting measurement_seed preserves V74 semantics.
"""
from __future__ import annotations
import argparse,csv,gzip,hashlib,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_v73_sharded_master_truth as T
import v73_full104_qc_calibration as Q

N_GENES=96; FULL_ADDRESSES=41238
GENES=np.array([f'ENSG_SYN_{i:05d}' for i in range(N_GENES)]); GENE_NAMES=np.array([f'GENE{i:03d}' for i in range(N_GENES)])


def sha256_file(path:Path,chunk:int=1<<20):
    h=hashlib.sha256()
    with open(path,'rb') as fh:
        for block in iter(lambda:fh.read(chunk),b''):h.update(block)
    return h.hexdigest()


def poisson_from_uniform(lam,u,max_k=80):
    """Backward-compatible stateless Poisson sampler used by paired-multiome V73."""
    lam=np.asarray(lam,dtype=np.float64); u=np.asarray(u,dtype=np.float64)
    pmf=np.exp(-lam); cdf=pmf.copy(); out=np.zeros(lam.shape,dtype=np.int16); active=u>cdf
    for k in range(1,max_k+1):
        if not active.any(): break
        pmf=pmf*lam/float(k); cdf+=pmf; hit=active&(u<=cdf); out[hit]=k; active&=~hit
    out[active]=max_k
    return out


def weights(seed):
    gid=np.arange(N_GENES,dtype=np.uint64)
    return np.stack([T.normal(seed+100,gid,200+j) for j in range(9)],axis=0).astype(np.float32)*np.float32(.22)


def normal_cdf(x):
    """Vectorised standard-normal CDF approximation; max error is negligible for ranks."""
    x=np.asarray(x,dtype=np.float64); ax=np.abs(x); t=1.0/(1.0+0.2316419*ax)
    poly=t*(0.319381530+t*(-0.356563782+t*(1.781477937+t*(-1.821255978+t*1.330274429))))
    tail=np.exp(-0.5*ax*ax)/np.sqrt(2.0*np.pi)*poly
    return np.where(x>=0,1.0-tail,tail)


def operator_availability(op_index,qc_by_op,operator_ids,seed):
    """Project authenticated measured-address support onto the 96-gene panel."""
    avail=np.ones((len(op_index),N_GENES),dtype=np.uint8); gid=np.arange(N_GENES,dtype=np.uint64)
    for op in np.unique(op_index):
        row=qc_by_op[operator_ids[int(op)]]
        measured=int(row.get('measured_scalar_addresses',round(FULL_ADDRESSES*(1-float(row['structural_missing_fraction'])-float(row.get('collision_unresolved_fraction',0.0))))))
        nmeasured=min(N_GENES,max(0,int(round(measured/FULL_ADDRESSES*N_GENES))))
        nunavailable=N_GENES-nmeasured
        if nunavailable:
            scores=T.u01(seed+811,gid,1100+int(op)); miss=np.argsort(scores,kind='stable')[:nunavailable]; rows=np.where(op_index==op)[0]
            avail[np.ix_(rows,miss)]=0
    return avail


def empirical_targets(ids,op,avail,qc_by_op,operator_ids,qprobs,seed):
    """Generate coupled depth/support targets from sampled operator-level technical summaries."""
    ids_u=np.asarray(ids,dtype=np.uint64); z_depth=T.normal(seed+701,ids_u,951); z_ind=T.normal(seed+704,ids_u,954)
    u_depth=normal_cdf(z_depth)
    n=len(ids); lib=np.empty(n); detected_full=np.empty(n); zero_full=np.empty(n); projected_depth=np.empty(n); projected_detected=np.empty(n)
    avail_n=avail.sum(axis=1).astype(np.float64)
    for oi in np.unique(op):
        ix=np.where(op==oi)[0]; row=qc_by_op[operator_ids[int(oi)]]
        rho=float(row.get('log1p_library_vs_detected_pearson',0.0) or 0.0); rho=float(np.clip(rho,-0.98,0.98))
        z_support=rho*z_depth[ix]+np.sqrt(max(0.0,1.0-rho*rho))*z_ind[ix]
        u_support=normal_cdf(z_support)
        lib[ix]=Q.interp_quantiles(u_depth[ix],qprobs,row['rna_library_size_quantiles'])
        detected_full[ix]=Q.interp_quantiles(u_support,qprobs,row['rna_detected_feature_quantiles'])
        measured=max(1.0,float(row.get('measured_scalar_addresses',FULL_ADDRESSES*(1-float(row['structural_missing_fraction'])-float(row.get('collision_unresolved_fraction',0.0))))))
        detected_full[ix]=np.clip(detected_full[ix],0.0,measured)
        zero_full[ix]=1.0-detected_full[ix]/measured
        projected_depth[ix]=lib[ix]*avail_n[ix]/measured
        projected_detected[ix]=detected_full[ix]*avail_n[ix]/measured
    panel_count=np.maximum(0,np.rint(projected_depth).astype(np.int64))
    panel_detected=np.clip(np.rint(projected_detected).astype(np.int64),0,avail_n.astype(np.int64))
    panel_detected=np.where((panel_count>0)&(panel_detected==0)&(avail_n>0),1,panel_detected)
    panel_count=np.maximum(panel_count,panel_detected)
    return lib,detected_full,zero_full,projected_depth,projected_detected,panel_count,panel_detected


def exact_counts(rel,avail,ids,panel_count,panel_detected,seed):
    """Realise exact panel depth/support while retaining biology-driven feature preference."""
    n=len(ids); ids_u=np.asarray(ids,dtype=np.uint64); gid=np.arange(N_GENES,dtype=np.uint64)
    keys=ids_u[:,None]*np.uint64(1315423911)+gid[None,:]*np.uint64(2654435761)
    u_select=np.clip(T.u01(seed+510,keys,902),1e-12,1-1e-12)
    gumbel=-np.log(-np.log(u_select))
    score=np.log(np.maximum(rel,1e-30))+0.35*gumbel
    score[avail==0]=-np.inf
    support=np.zeros((n,N_GENES),dtype=bool)
    for kk in np.unique(panel_detected):
        kk=int(kk)
        if kk<=0: continue
        rows=np.where(panel_detected==kk)[0]
        top=np.argpartition(score[rows],-kk,axis=1)[:,-kk:]
        support[np.repeat(rows,kk),top.reshape(-1)]=True
    counts=support.astype(np.int64)
    remaining=panel_count-panel_detected
    u_alloc=T.u01(seed+511,keys,903)
    alloc_weight=rel*(0.75+0.5*u_alloc)*support
    denom=alloc_weight.sum(axis=1); denom=np.where(denom>0,denom,1.0)
    raw=alloc_weight/denom[:,None]*remaining[:,None]
    base=np.floor(raw).astype(np.int64); counts+=base
    residual=panel_count-counts.sum(axis=1)
    frac=raw-base; frac[~support]=-np.inf
    order=np.argsort(-frac,axis=1,kind='stable')
    extra_order=(np.arange(N_GENES)[None,:]<residual[:,None]).astype(np.int64)
    extra=np.zeros_like(counts); np.put_along_axis(extra,order,extra_order,axis=1); counts+=extra
    if not np.array_equal(counts.sum(axis=1),panel_count): raise RuntimeError('panel count target not realised exactly')
    if not np.array_equal(((counts>0)&(avail>0)).sum(axis=1),panel_detected): raise RuntimeError('detected support target not realised exactly')
    if np.any(counts[avail==0]): raise RuntimeError('unavailable feature received counts')
    if counts.max(initial=0)>np.iinfo(np.int16).max: raise RuntimeError('int16 count overflow')
    return counts.astype(np.int16)


def observe(root:Path,seed:int=7302,measurement_seed:int|None=None)->dict:
    truth_root=root/'hidden_truth'; obs=root/'observable_raw'/'FULL104_like_sharded'; obs.mkdir(parents=True,exist_ok=True)
    tm=json.loads((truth_root/'TRUTH_MANIFEST.json').read_text())
    if int(tm['seed'])!=int(seed):raise ValueError('observer seed must equal master-truth seed')
    measurement_seed=int(seed if measurement_seed is None else measurement_seed)
    qmeta,qc_by_op=Q.by_operator(); qprobs=np.array(qmeta['quantile_probabilities'],dtype=float); operator_ids=tm['operator_ids']; W=weights(seed); out_shards=[]; total_cells=0; realised_sources=np.zeros(3,dtype=np.int64)
    for s in tm['shards']:
        tp=truth_root/s['file']
        if sha256_file(tp)!=s['sha256']:raise RuntimeError('truth shard digest mismatch: '+s['file'])
        z=np.load(tp,allow_pickle=False); ids=z['global_cell_index'].astype(np.int64); src=z['source_index'].astype(np.int8); op=z['operator_index'].astype(np.int16); realised_sources+=np.bincount(src,minlength=3)
        latent=np.c_[z['z_global'],z['z_query'],z['z_reg_shared']].astype(np.float32); eta=latent@W; rel=np.exp(np.clip(eta,-3,3)).astype(np.float64)
        avail=operator_availability(op,qc_by_op,operator_ids,seed); rel*=avail
        lib,dtarget,ztarget,projected,pdet,panel_count,panel_detected=empirical_targets(ids,op,avail,qc_by_op,operator_ids,qprobs,measurement_seed)
        counts=exact_counts(rel,avail,ids,panel_count,panel_detected,measurement_seed).T; availability=avail.T
        donor=z['donor_index'].astype(np.int16); cell_ids=z['cell_id']; start,stop=int(ids[0]),int(ids[-1])+1; opath=obs/f'RNA_{start:09d}_{stop:09d}.npz'
        np.savez(opath,counts=counts,availability=availability,genes=GENES,gene_names=GENE_NAMES,global_cell_index=ids,cell_id=cell_ids,
                 empirical_full_library_size_target=lib.astype(np.float32),empirical_projected_panel_depth_target=projected.astype(np.float32),
                 empirical_measured_zero_fraction_target=ztarget.astype(np.float32),empirical_detected_feature_target=dtarget.astype(np.float32),
                 empirical_projected_detected_feature_target_float=pdet.astype(np.float32),
                 empirical_projected_detected_feature_target_int=panel_detected.astype(np.int16),
                 empirical_projected_panel_count_target_int=panel_count.astype(np.int32))
        mpath=obs/f'META_{start:09d}_{stop:09d}.csv.gz'; source_names=np.array(T.SOURCE_NAMES)
        with gzip.open(mpath,'wt',newline='') as fh:
            w=csv.writer(fh); w.writerow(['global_cell_index','cell_id','donor','source','operator'])
            for i in range(len(ids)):w.writerow([int(ids[i]),str(cell_ids[i]),tm['donor_ids'][int(donor[i])],str(source_names[int(src[i])]),operator_ids[int(op[i])]])
        out_shards.append(dict(start=start,stop=stop,cells=len(ids),rna_file=opath.name,rna_sha256=sha256_file(opath),metadata_file=mpath.name,metadata_sha256=sha256_file(mpath))); total_cells+=len(ids)
    source_counts=dict(zip(T.SOURCE_NAMES,realised_sources.tolist()))
    if source_counts!=tm['source_counts']:raise RuntimeError('observer source counts disagree with truth')
    manifest=dict(schema='V75_FULL104_SHARDED_OBSERVER_MANIFEST_V5_MEASUREMENT_SEED_SEPARATED',seed=seed,truth_seed=seed,measurement_seed=measurement_seed,n_cells=total_cells,n_genes=N_GENES,n_donors=104,n_operators=42,source_counts=source_counts,structural_missingness=True,hidden_truth_path_exposed=False,
      donor_assignment_status=tm['donor_assignment_status'],operator_assignment_status=tm['operator_assignment_status'],
      empirical_qc_calibration=dict(authority_path=str(Q.AUTHORITY),authority_sha256=Q.sha256_file(Q.AUTHORITY),sampling_frame=qmeta['sampling_frame'],
          qualification='sampled operator-level technical QC marginals shape a 96-gene per-measured-address projection; sampled QC is descriptive and does not define biological thresholds',
          depth_and_detected_support_are_consumed=True,
          support_depth_dependence='GAUSSIAN_COPULA_FROM_FROZEN_OPERATOR_SUMMARY',
          dependence_parameter_note='within-operator log1p-library-vs-detected Pearson is used as an approximate Gaussian-copula rho; this is a transparent synthetic dependence approximation, not a claim of exact real joint-distribution recovery',
          measured_zero_is_derived_from_detected_support=True,
          sampled_qc_is_descriptive_not_biological_threshold=True),
      master_truth_digest_binding=[dict(file=x['file'],sha256=x['sha256']) for x in tm['shards']],
      observation_operator_seed=seed,
      measurement_realization_seed=measurement_seed,
      count_randomization='stateless biology-weighted support selection plus exact integer allocation keyed by global_cell_index x gene identity and measurement realization seed; realised panel depth and support equal stored technical targets',shards=out_shards)
    (obs/'FULL104_SHARDED_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n'); return manifest


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--seed',type=int,default=7302);ap.add_argument('--measurement-seed',type=int,default=None);a=ap.parse_args();m=observe(Path(a.root),a.seed,a.measurement_seed);print(json.dumps(dict(status='PASS',cells=m['n_cells'],shards=len(m['shards']),source_counts=m['source_counts'],truth_seed=m['truth_seed'],measurement_seed=m['measurement_seed']),indent=2))
if __name__=='__main__':main()
