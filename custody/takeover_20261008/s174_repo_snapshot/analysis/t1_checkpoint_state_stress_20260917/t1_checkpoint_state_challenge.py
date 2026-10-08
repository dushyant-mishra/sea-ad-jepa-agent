#!/usr/bin/env python3
"""Exploratory state-level stress test of historical T1 checkpoints.

This is NOT gene-expression prediction.  The scalar shortcut models are used only
upstream to select co-masked evidence.  The model score here is teacher/student
latent-state agreement for a queried molecular address, plus global cell-state
stability, under burden-matched masks.

Status: exploratory / no training authority / no protected outcomes.
"""
from __future__ import annotations
import argparse, codecs, hashlib, math, re, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.sparse as sp
import torch
import torch.nn.functional as F


def parse_args():
    p=argparse.ArgumentParser()
    p.add_argument('--checkpoint', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--burden', type=float, default=0.15)
    p.add_argument('--targets', default='0,1,2,3,4,5,6,7')
    p.add_argument('--methods', default='UNIFORM,TOP8,RIDGE8,PREFIX3')
    p.add_argument('--historical-package-root', default='/mnt/data/t1_historical_code')
    p.add_argument('--data-root', default='/mnt/data/jepa_spike_work')
    p.add_argument('--cells', default='/mnt/data/t1_checkpoint_state_challenge_cells.csv')
    p.add_argument('--mask-sets', default='/mnt/data/t1_checkpoint_state_challenge_mask_sets.csv')
    p.add_argument('--target-cols', default='/mnt/data/outer5200_targets_cols.npy')
    return p.parse_args()


def safe_load_checkpoint(path: Path):
    safe=[(np._core.multiarray._reconstruct,'numpy.core.multiarray._reconstruct'),np.ndarray,np.dtype,codecs.encode]
    for name in dir(np.dtypes):
        obj=getattr(np.dtypes,name)
        if isinstance(obj,type): safe.append(obj)
    with torch.serialization.safe_globals(safe):
        return torch.load(path,map_location='cpu',weights_only=True)


def keyed_seed(payload: str) -> int:
    return int.from_bytes(hashlib.sha256(payload.encode()).digest()[:8],'big')


def make_mask(n_genes:int, target_local:int, fold:int, target_index:int, targeted:list[int], burden:float)->set[int]:
    count=max(2,int(round(float(burden)*n_genes)))
    pool=np.delete(np.arange(n_genes,dtype=int),target_local)
    seed=keyed_seed(f'JEPA_SCALE_MASK|{n_genes}|{fold}|{target_index}')
    base=list(map(int,np.random.default_rng(seed).choice(pool,size=count-1,replace=False)))
    mask=set(base+[int(target_local)])
    add=[int(a) for a in targeted if int(a)!=target_local and int(a) not in mask]
    removable=sorted([a for a in base if a not in targeted],key=lambda a:hashlib.sha256(f'REMOVE|{fold}|{target_index}|{a}'.encode()).digest())
    for a,r in zip(add,removable):
        mask.discard(r); mask.add(a)
    if len(mask)!=count or target_local not in mask:
        raise RuntimeError('burden/target invariant failed')
    return mask


def query_prediction(predictor, identity_embedding, query_gene_ids, student_gene_states, student_cell_state, student_valid):
    identities=identity_embedding(query_gene_ids)
    queries=predictor.identity_projection(identities)[:,None,:] + predictor.block_mask
    memory=torch.cat((student_cell_state[:,None],student_gene_states),dim=1)
    valid=torch.cat((torch.ones(len(memory),1,dtype=torch.bool),student_valid),dim=1)
    attended,_=predictor.cross_attention(queries,memory,memory,key_padding_mask=~valid,need_weights=False)
    state=queries+attended
    return predictor.output_norm(state+predictor.ffn(predictor.norm(state)))[:,0,:]


def main():
    a=parse_args()
    sys.path.insert(0,a.historical_package_root)
    from pkg.ipb_jepa import IPBEncoder, BlockPredictor

    ck=safe_load_checkpoint(Path(a.checkpoint))
    online=IPBEncoder(vocabulary_size=41238,width=160,heads=4,blocks=6,gradient_checkpointing=False)
    target=IPBEncoder(vocabulary_size=41238,width=160,heads=4,blocks=6,gradient_checkpointing=False)
    predictor=BlockPredictor(width=160,heads=4)
    online.load_state_dict(ck['online_encoder'],strict=True)
    target.load_state_dict({k.removeprefix('encoder.'):v for k,v in ck['target_encoder'].items()},strict=True)
    predictor.load_state_dict(ck['predictor'],strict=True)
    online.eval(); target.eval(); predictor.eval()

    root=Path(a.data_root)
    X=sp.load_npz(root/'X_common6000.npz').tocsr()
    addr=np.load(root/'selected6000_sorted.npy').astype(np.int64)
    target_cols=np.load(a.target_cols).astype(int)
    cells=pd.read_csv(a.cells)
    mask_sets=pd.read_csv(a.mask_sets).fillna('')
    expr_rows=cells.expression_row.to_numpy(int)
    expression=torch.from_numpy(X[expr_rows].toarray().astype(np.float32))
    measurement=torch.ones_like(expression,dtype=torch.bool)
    gene_ids=torch.from_numpy(np.tile(addr,(len(cells),1)))
    zeros=torch.zeros_like(measurement)
    methods=[x.strip() for x in a.methods.split(',') if x.strip()]
    selected_targets=[int(x) for x in a.targets.split(',') if x.strip()]
    update=int(re.search(r'u(\d+)',Path(a.checkpoint).stem).group(1))

    with torch.inference_mode():
        teacher=target(gene_ids,expression,measurement,zeros,'target')

    rows=[]
    for ti in selected_targets:
        tcol=int(target_cols[ti]); qid=int(addr[tcol])
        teacher_query=F.layer_norm(teacher.gene_states[:,tcol,:],(teacher.gene_states.shape[-1],))
        for method in methods:
            hidden=torch.zeros_like(measurement)
            effective=[]
            hashes=[]
            for ri,cell in cells.iterrows():
                fi=int(cell['fold'])
                if method=='UNIFORM':
                    targeted=[]
                else:
                    r=mask_sets[(mask_sets.fold==fi)&(mask_sets.target_index==ti)&(mask_sets.method==method)]
                    if len(r)!=1: raise RuntimeError(f'mask-set lookup failure fold={fi} target={ti} method={method}')
                    txt=str(r.iloc[0].targeted_local_cols)
                    targeted=[] if not txt else [int(x) for x in txt.split(';') if x]
                mask=make_mask(X.shape[1],tcol,fi,ti,targeted,a.burden)
                hidden[ri,list(mask)]=True
                effective.append(len([x for x in targeted if x in mask and x!=tcol]))
                hashes.append(hashlib.sha256(np.packbits(hidden[ri].numpy(),bitorder='little').tobytes()).hexdigest())
            with torch.inference_mode():
                student=online(gene_ids,expression,measurement,hidden,'student')
                query_ids=torch.full((len(cells),),qid,dtype=torch.long)
                pred=query_prediction(predictor,online.tokenizer.gene_identity,query_ids,student.gene_states,student.cell_state,measurement & ~hidden)
                qcos=F.cosine_similarity(pred,teacher_query,dim=-1)
                qmse=(pred-teacher_query).square().mean(dim=-1)
                ccos=F.cosine_similarity(student.cell_state,teacher.cell_state,dim=-1)
            for ri,cell in cells.iterrows():
                rows.append({
                    'update':update,'burden':a.burden,'target_index':ti,'target_local_col':tcol,'target_address_id':qid,
                    'method':method,'fold':int(cell['fold']),'source':cell['source'],'donor_id':cell['donor_id'],
                    'expression_row':int(cell['expression_row']),'effective_targeted_n':int(effective[ri]),'mask_sha256':hashes[ri],
                    'query_cosine_similarity':float(qcos[ri]),'query_cosine_error':float(1-qcos[ri]),
                    'query_native_mse':float(qmse[ri]),'global_cell_cosine_similarity':float(ccos[ri]),
                    'global_cell_cosine_error':float(1-ccos[ri]),
                })
            del student,pred,qcos,qmse,ccos,hidden
    out=pd.DataFrame(rows)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    out.to_csv(a.output,index=False)
    if not np.isfinite(out[['query_cosine_error','query_native_mse','global_cell_cosine_error']].to_numpy()).all():
        raise RuntimeError('nonfinite state score')
    print(f'SAVED {a.output} rows={len(out)} update={update} burden={a.burden}',flush=True)
    print(out.groupby('method').agg(query_error=('query_cosine_error','mean'),global_error=('global_cell_cosine_error','mean'),mse=('query_native_mse','mean')).to_string(),flush=True)

if __name__=='__main__': main()
