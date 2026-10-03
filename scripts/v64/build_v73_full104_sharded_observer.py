#!/usr/bin/env python3
"""FULL104-like RNA observer calibrated to authenticated operator-level QC summaries.

Biology controls relative gene programs. Frozen 50k source/operator QC summaries control
technical depth, sparsity targets and structural support. A 96-gene panel is treated as a
projection of the measured 41,238-address library; full-library depths are not misreported
as 96-gene totals.
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
    h=hashlib.sha256();
    with open(path,'rb') as fh:
        for block in iter(lambda:fh.read(chunk),b''):h.update(block)
    return h.hexdigest()

def poisson_from_uniform(lam,u,max_k=80):
    lam=np.asarray(lam,dtype=np.float64); u=np.asarray(u,dtype=np.float64); pmf=np.exp(-lam); cdf=pmf.copy(); out=np.zeros(lam.shape,dtype=np.int16); active=u>cdf
    for k in range(1,max_k+1):
        if not active.any():break
        pmf=pmf*lam/float(k); cdf+=pmf; hit=active&(u<=cdf); out[hit]=k; active&=~hit
    out[active]=max_k; return out

def weights(seed):
    gid=np.arange(N_GENES,dtype=np.uint64); return np.stack([T.normal(seed+100,gid,200+j) for j in range(9)],axis=0).astype(np.float32)*np.float32(.22)

def operator_availability(op_index,qc_by_op,operator_ids,seed):
    avail=np.ones((len(op_index),N_GENES),dtype=np.uint8); gid=np.arange(N_GENES,dtype=np.uint64)
    for op in np.unique(op_index):
        row=qc_by_op[operator_ids[int(op)]]; frac=float(row['structural_missing_fraction']); nmiss=min(N_GENES,max(0,int(round(frac*N_GENES))))
        if nmiss:
            scores=T.u01(seed+811,gid,1100+int(op)); miss=np.argsort(scores,kind='stable')[:nmiss]; rows=np.where(op_index==op)[0]
            avail[np.ix_(rows,miss)]=0
    return avail

def observe(root:Path,seed:int=7302)->dict:
    truth_root=root/'hidden_truth'; obs=root/'observable_raw'/'FULL104_like_sharded'; obs.mkdir(parents=True,exist_ok=True)
    tm=json.loads((truth_root/'TRUTH_MANIFEST.json').read_text())
    if int(tm['seed'])!=int(seed):raise ValueError('observer seed must equal master-truth seed')
    qmeta,qc_by_op=Q.by_operator(); qprobs=np.array(qmeta['quantile_probabilities'],dtype=float); operator_ids=tm['operator_ids']; W=weights(seed); out_shards=[]; total_cells=0; realised_sources=np.zeros(3,dtype=np.int64)
    for s in tm['shards']:
        tp=truth_root/s['file']
        if sha256_file(tp)!=s['sha256']:raise RuntimeError('truth shard digest mismatch: '+s['file'])
        z=np.load(tp,allow_pickle=False); ids=z['global_cell_index'].astype(np.int64); src=z['source_index'].astype(np.int8); op=z['operator_index'].astype(np.int16); realised_sources+=np.bincount(src,minlength=3)
        latent=np.c_[z['z_global'],z['z_query'],z['z_reg_shared']].astype(np.float32); eta=latent@W; rel=np.exp(np.clip(eta,-3,3)).astype(np.float64)
        avail=operator_availability(op,qc_by_op,operator_ids,seed); rel*=avail
        qlib=T.u01(seed+701,ids.astype(np.uint64),951); qzero=T.u01(seed+702,ids.astype(np.uint64),952); qdet=T.u01(seed+703,ids.astype(np.uint64),953)
        lib=np.empty(len(ids)); ztarget=np.empty(len(ids)); dtarget=np.empty(len(ids)); projected=np.empty(len(ids))
        for oi in np.unique(op):
            ix=np.where(op==oi)[0]; row=qc_by_op[operator_ids[int(oi)]]
            lib[ix]=Q.interp_quantiles(qlib[ix],qprobs,row['rna_library_size_quantiles']); ztarget[ix]=Q.interp_quantiles(qzero[ix],qprobs,row['rna_zero_fraction_quantiles']); dtarget[ix]=Q.interp_quantiles(qdet[ix],qprobs,row['rna_detected_feature_quantiles'])
            effective=max(1.0,FULL_ADDRESSES*(1-float(row['structural_missing_fraction'])-float(row.get('collision_unresolved_fraction',0.0))))
            projected[ix]=lib[ix]*avail[ix].sum(axis=1)/effective
        rowsum=rel.sum(axis=1); rowsum[rowsum<=0]=1; lam=rel/rowsum[:,None]*projected[:,None]
        gid=np.arange(N_GENES,dtype=np.uint64); keys=ids.astype(np.uint64)[:,None]*np.uint64(1315423911)+gid[None,:]*np.uint64(2654435761)
        counts=poisson_from_uniform(lam,T.u01(seed+500,keys,900)).T.astype(np.int16); availability=avail.T; counts[availability==0]=0
        donor=z['donor_index'].astype(np.int16); cell_ids=z['cell_id']; start,stop=int(ids[0]),int(ids[-1])+1; opath=obs/f'RNA_{start:09d}_{stop:09d}.npz'
        np.savez(opath,counts=counts,availability=availability,genes=GENES,gene_names=GENE_NAMES,global_cell_index=ids,cell_id=cell_ids,
                 empirical_full_library_size_target=lib.astype(np.float32),empirical_projected_panel_depth_target=projected.astype(np.float32),empirical_measured_zero_fraction_target=ztarget.astype(np.float32),empirical_detected_feature_target=dtarget.astype(np.float32))
        mpath=obs/f'META_{start:09d}_{stop:09d}.csv.gz'; source_names=np.array(T.SOURCE_NAMES)
        with gzip.open(mpath,'wt',newline='') as fh:
            w=csv.writer(fh); w.writerow(['global_cell_index','cell_id','donor','source','operator'])
            for i in range(len(ids)):w.writerow([int(ids[i]),str(cell_ids[i]),tm['donor_ids'][int(donor[i])],str(source_names[int(src[i])]),operator_ids[int(op[i])]])
        out_shards.append(dict(start=start,stop=stop,cells=len(ids),rna_file=opath.name,rna_sha256=sha256_file(opath),metadata_file=mpath.name,metadata_sha256=sha256_file(mpath))); total_cells+=len(ids)
    source_counts=dict(zip(T.SOURCE_NAMES,realised_sources.tolist()))
    if source_counts!=tm['source_counts']:raise RuntimeError('observer source counts disagree with truth')
    manifest=dict(schema='V73_FULL104_SHARDED_OBSERVER_MANIFEST_V3_EMPIRICAL_QC_CALIBRATED_SUBPANEL',seed=seed,n_cells=total_cells,n_genes=N_GENES,n_donors=104,n_operators=42,source_counts=source_counts,structural_missingness=True,hidden_truth_path_exposed=False,
      donor_assignment_status=tm['donor_assignment_status'],operator_assignment_status=tm['operator_assignment_status'],empirical_qc_calibration=dict(authority_path=str(Q.AUTHORITY),authority_sha256=Q.sha256_file(Q.AUTHORITY),sampling_frame=qmeta['sampling_frame'],qualification='operator-level full-library QC quantiles drive a 96-gene per-measured-address projection; not a claim that panel totals equal full-library totals'),master_truth_digest_binding=[dict(file=x['file'],sha256=x['sha256']) for x in tm['shards']],count_randomization='stateless inverse-CDF Poisson keyed by global_cell_index x gene identity',shards=out_shards)
    (obs/'FULL104_SHARDED_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n'); return manifest

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--seed',type=int,default=7302);a=ap.parse_args();m=observe(Path(a.root),a.seed);print(json.dumps(dict(status='PASS',cells=m['n_cells'],shards=len(m['shards']),source_counts=m['source_counts']),indent=2))
if __name__=='__main__':main()
