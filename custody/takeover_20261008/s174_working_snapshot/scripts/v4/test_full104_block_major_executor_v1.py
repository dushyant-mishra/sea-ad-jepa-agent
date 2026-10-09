#!/usr/bin/env python3
"""Targeted parity/resume/adversarial tests for block-major ALL execution."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import full104_refit_null_sensitivity_core_v1 as core
import run_full104_refit_null_block_major_v1 as block
import run_full104_refit_null_sensitivity_v1 as sequential


def synthetic(seed=17):
    rng=np.random.default_rng(seed); donors=[f"D{i}" for i in range(4)]; records=[]; values=[]; row=0
    for donor in donors:
        for operator in range(2):
            n=5+operator; values.append(rng.normal(size=(n,4,12)).astype(np.float32))
            logical_rows=row+np.roll(np.arange(n),1)
            for local in range(n): records.append({"row_index":int(logical_rows[local]),"selection_row":int(logical_rows[local]),"donor_id":donor,"operator_index":operator,"stratum_n":n,"stratum_m":n,"sample_rank":local,"within_donor_weight":1/(2*n),"global_weight":1/(8*n)})
            row+=n
    return np.concatenate(values),pd.DataFrame(records),donors


def parity_for_views(views,plan,donors,key,sketch,replicates,device):
    sequential=[]; maps=[]
    for rep in replicates:
        value,mapping=core.null_between_one(views,plan,donors,"ALL",sketch,rep,key,device);sequential.append(value);maps.append(mapping)
    batched,batch_maps,_=block.block_major_null_between_batch(views,plan,donors,sketch,replicates,key,device)
    return bool(np.array_equal(np.asarray(sequential),batched) and maps==[batch_maps[x] for x in replicates]),float(np.max(np.abs(np.asarray(sequential)-batched)))


def unsorted_block_major(views,plan,donors,key,sketch,replicates,device,reverse_strata=False,mapping_sketch=None,return_maps=False):
    import torch
    donor_ix={d:i for i,d in enumerate(donors)};dim=views.shape[-1];total=np.zeros((len(replicates),len(donors),dim,dim),np.float64);comp=np.zeros_like(total)
    groups=list(enumerate(plan.groupby(["donor_id","operator_index"],sort=True)));groups=groups[::-1] if reverse_strata else groups;map_records=[]
    for original_stratum,((donor,_operator),group) in groups:
        d=donor_ix[str(donor)];indices=group.row_index.to_numpy(np.int64);n=len(indices);base=torch.as_tensor(np.asarray(views[indices],np.float32),device=device).double();positions=np.arange(n);weight=float(group.within_donor_weight.iloc[0])
        for local,replicate in enumerate(replicates):
            _,_,order,offsets=core.null_stratum_mapping(n,key,"ALL",mapping_sketch or sketch,original_stratum,replicate);map_records.append((original_stratum,replicate,hashlib.sha256(order.tobytes()+offsets.tobytes()).hexdigest()));x=base[torch.as_tensor(order,device=device)];shifted=[x[torch.as_tensor((positions+offsets[v])%n,device=device),v] for v in range(core.VIEWS)];cross=torch.zeros((dim,dim),dtype=torch.float64,device=device)
            for v in range(core.VIEWS):
                for w in range(v+1,core.VIEWS):product=shifted[v].T@shifted[w];cross+=product+product.T
            core.kahan_add(total[local],comp[local],weight*cross.cpu().numpy()/(core.VIEWS*(core.VIEWS-1)),d)
    return (total,dict(((s,r),h) for s,r,h in map_records)) if return_maps else total


def restoration_fixture(views, logical_indices, device, label):
    import torch
    logical=np.asarray(logical_indices,np.int64);direct=np.asarray(views[logical],np.float32)
    restored,hashes,_read,_restore,_h2d=block.sorted_physical_read_restore(views,logical,device)
    actual=restored.to(dtype=torch.float32).cpu().numpy();rng=np.random.default_rng(991)
    sampled=np.unique(np.concatenate(([0,len(logical)-1],rng.integers(0,len(logical),size=min(16,len(logical))))))
    return {"fixture":label,"rows":len(logical),**hashes,"array_equal":bool(np.array_equal(direct,actual)),
            "byte_equal":bool(direct.tobytes()==actual.tobytes()),"sampled_positions_equal":bool(np.array_equal(direct[sampled],actual[sampled]))}


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--matrix",required=True);parser.add_argument("--plan-dir",required=True);parser.add_argument("--out",required=True);parser.add_argument("--device",default="cuda")
    args=parser.parse_args();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False);key="fixture-key"
    views,plan,donors=synthetic();results=[]
    for sketch,local in (("A",views),("B",views[:, :, ::-1].copy())):
        passed,diff=parity_for_views(local,plan,donors,key,sketch,[0,1,2,3],args.device);results.append({"test":f"synthetic_{sketch}_old_vs_new","pass":passed,"max_abs":diff})
        restore=restoration_fixture(local,plan.row_index.to_numpy(),args.device,f"synthetic_{sketch}");results.append({"test":f"synthetic_{sketch}_sorted_restore","pass":all(restore[x] for x in ("array_equal","byte_equal","sampled_positions_equal")),"details":restore})
    reference,_,_=block.block_major_null_between_batch(views,plan,donors,"A",[0],key,args.device)
    for ids,position in (([0,1],0),([0,1,2,3,4,5,6,7],0),([0,1,2],0)):
        candidate,_,_=block.block_major_null_between_batch(views,plan,donors,"A",ids,key,args.device);results.append({"test":f"batch_invariance_K{len(ids)}","pass":bool(np.array_equal(reference[0],candidate[position]))})
    mid,_,_=block.block_major_null_between_batch(views,plan,donors,"A",[4,0] if False else [0,4],key,args.device);results.append({"test":"same_replicate_first","pass":bool(np.array_equal(reference[0],mid[0]))})
    last,_,_=block.block_major_null_between_batch(views,plan,donors,"A",[0,1,2,3,4],key,args.device);solo4,_,_=block.block_major_null_between_batch(views,plan,donors,"A",[4],key,args.device);results.append({"test":"same_replicate_last","pass":bool(np.array_equal(last[4],solo4[0]))})
    middle,_,_=block.block_major_null_between_batch(views,plan,donors,"A",[0,1,4,5,6],key,args.device);middle2,_,_=block.block_major_null_between_batch(views,plan,donors,"A",[2,3,4,7],key,args.device);results.append({"test":"same_replicate_middle_and_companion_invariance","pass":bool(np.array_equal(middle[2],solo4[0]) and np.array_equal(middle2[2],solo4[0]))})

    # Forced interruption after half the strata, exact accumulator reload, resume.
    checkpoint=out/"resume_checkpoint";identity=block.batch_identity("fp","gate","matrix","A",[0,1],2,4,{"plan_sha256":"p","plan_semantic_sha256":"s"})
    identity["accumulator_shape"]=[2,len(donors),views.shape[-1],views.shape[-1]]
    maps={r:core.null_mapping_sha256(plan,"ALL","A",r,key) for r in [0,1]}
    class Interrupted(Exception): pass
    def callback(position,b,c): block.save_batch_checkpoint(checkpoint,identity,position,b,c,maps);raise Interrupted()
    try: block.block_major_null_between_batch(views,plan,donors,"A",[0,1],key,args.device,checkpoint_every=4,checkpoint_callback=callback)
    except Interrupted: pass
    restored=block.load_batch_checkpoint(checkpoint,identity,maps)
    resumed,_,_=block.block_major_null_between_batch(
        views,plan,donors,"A",[0,1],key,args.device,
        start_stratum=restored[0],between=restored[1],compensation=restored[2])
    uninterrupted,_,_=block.block_major_null_between_batch(views,plan,donors,"A",[0,1],key,args.device);results.append({"test":"forced_interruption_resume","pass":bool(np.array_equal(resumed,uninterrupted))})
    snapshot=out/"snapshot_failure_checkpoint";zero=np.zeros((2,len(donors),views.shape[-1],views.shape[-1]),np.float64);one=np.ones_like(zero)
    block.save_batch_checkpoint(snapshot,identity,2,zero,zero,maps)
    crash_results={}
    for point in ("between","compensation","generation","pointer"):
        try:block.save_batch_checkpoint(snapshot,identity,4,one,one,maps,fail_after=point)
        except RuntimeError:pass
        restored_after=block.load_batch_checkpoint(snapshot,identity,maps);cleanup=block.cleanup_stale_checkpoint_artifacts(snapshot,identity,maps);crash_results[point]=bool(restored_after[0]==2 and np.array_equal(restored_after[1],zero) and np.array_equal(restored_after[2],zero) and cleanup["current"] is not None and not any(p.name.endswith(".staging") for p in snapshot.iterdir()))
    block.save_batch_checkpoint(snapshot,identity,4,one,one,maps);advanced=block.load_batch_checkpoint(snapshot,identity,maps);crash_results["successful_advance"]=bool(advanced[0]==4 and np.array_equal(advanced[1],one) and np.array_equal(advanced[2],one));results.append({"test":"snapshot_crash_matrix_and_advance","pass":all(crash_results.values()),"details":crash_results})

    # Production cadence 1400 equals the complete stratum count, so it must
    # create no intermediate snapshot and completed-batch cleanup must safely
    # no-op without masking any other path or identity error.
    zero_snapshot_dir=out/"batch_checkpoints"/"A_000_001";callbacks=[]
    zero_result,_,_=block.block_major_null_between_batch(
        views,plan,donors,"A",[0,1],key,args.device,
        checkpoint_every=1400,checkpoint_callback=lambda *values: callbacks.append(values))
    block.remove_completed_batch_checkpoint(zero_snapshot_dir,out)
    results.append({"test":"no_in_batch_checkpoint_absent_cleanup_and_continuation","pass":bool(not callbacks and not zero_snapshot_dir.exists() and np.array_equal(zero_result,uninterrupted))})

    # Real FULL104 representative strata: small, median-ish and largest.
    matrix=Path(args.matrix).resolve();plan_dir=Path(args.plan_dir).resolve();z=np.load(plan_dir/"NESTED_WEIGHTED_SELECTION.npz",allow_pickle=False);full=pd.DataFrame({name:z[name] for name in z.files});groups=full.groupby(["donor_id","operator_index"],sort=True);sizes=groups.size();targets=[sizes.idxmin(),(sizes-sizes.median()).abs().idxmin(),(sizes-np.quantile(sizes,0.9)).abs().idxmin()]
    # Bounded expression fixtures are min/median/~90th percentile; the true
    # largest stratum is permutation-integrity-only below.
    real=pd.concat([full[(full.donor_id==d)&(full.operator_index==o)].head(256) for d,o in targets],ignore_index=True);real_donors=sorted(real.donor_id.unique())
    for sketch in "AB":
        mmap=np.load(matrix/f"{sketch}_views.npy",mmap_mode="r");passed,diff=parity_for_views(mmap,real,real_donors,"real-subset-key",sketch,[0,1],args.device);results.append({"test":f"real_subset_{sketch}_old_vs_new","pass":passed,"max_abs":diff,"rows":len(real)})
        prior=unsorted_block_major(mmap,real,real_donors,"real-subset-key",sketch,[0,1],args.device);sorted_result,_,_=block.block_major_null_between_batch(mmap,real,real_donors,sketch,[0,1],"real-subset-key",args.device);results.append({"test":f"real_{sketch}_sorted_vs_prior_unsorted_block_major","pass":bool(np.array_equal(prior,sorted_result)),"max_abs":float(np.max(np.abs(prior-sorted_result)))})
        for index,target in enumerate(targets):
            logical=full[(full.donor_id==target[0])&(full.operator_index==target[1])].row_index.to_numpy()[:256]
            restore=restoration_fixture(mmap,logical,args.device,f"real_{sketch}_{index}");results.append({"test":f"real_{sketch}_restore_{index}","pass":all(restore[x] for x in ("array_equal","byte_equal","sampled_positions_equal")),"details":restore})
    largest_key=sizes.idxmax();largest=full[(full.donor_id==largest_key[0])&(full.operator_index==largest_key[1])].row_index.to_numpy(np.int64);perm=np.argsort(largest,kind="stable");inverse=np.empty(len(largest),np.int64);inverse[perm]=np.arange(len(largest));largest_ok=bool(np.array_equal(largest[perm][inverse],largest) and len(np.unique(largest))==len(largest))
    results.append({"test":"largest_stratum_permutation_integrity_no_expression_read","pass":largest_ok,"rows":len(largest),"logical_row_order_sha256":hashlib.sha256(largest.tobytes()).hexdigest(),"physical_read_order_sha256":hashlib.sha256(largest[perm].tobytes()).hexdigest()})
    b_mmap=np.load(matrix/"B_views.npy",mmap_mode="r");legitimate_b,_,_=block.block_major_null_between_batch(b_mmap,real,real_donors,"B",[0],"real-subset-key",args.device);forced_a=unsorted_block_major(b_mmap,real,real_donors,"real-subset-key","B",[0],args.device,mapping_sketch="A");a_map=core.null_mapping_sha256(real,"ALL","A",0,"real-subset-key");b_map=core.null_mapping_sha256(real,"ALL","B",0,"real-subset-key");results.append({"test":"real_A_map_on_B_changes_result_and_mapping","pass":bool(not np.array_equal(legitimate_b,forced_a) and a_map!=b_map)})
    a_mmap=np.load(matrix/"A_views.npy",mmap_mode="r");normal,normal_maps=unsorted_block_major(a_mmap,real,real_donors,"real-subset-key","A",[0],args.device,return_maps=True);reversed_result,reversed_maps=unsorted_block_major(a_mmap,real,real_donors,"real-subset-key","A",[0],args.device,reverse_strata=True,return_maps=True);results.append({"test":"real_stratum_order_attack_preserves_maps_and_is_identity_bound","pass":bool(normal_maps==reversed_maps),"bitwise_result_equal":bool(np.array_equal(normal,reversed_result))})

    adversarial={}
    try:block.block_major_null_between_batch(views,plan,donors,"A",[0,0],key,args.device);adversarial["duplicate_replicate"]=False
    except RuntimeError:adversarial["duplicate_replicate"]=True
    attacks={"wrong_batch":dict(identity,batch_size=8),"missing_replicate":dict(identity,replicate_ids=[0]),"wrong_sketch":dict(identity,sketch="B"),"stale_fingerprint":dict(identity,implementation_fingerprint="old"),"block_order":dict(identity,stratum_order="changed")}
    for name,bad in attacks.items():
        try:block.load_batch_checkpoint(checkpoint,bad,maps);adversarial[name]=False
        except RuntimeError:adversarial[name]=True
    wrong_maps=dict(maps);wrong_maps[0]="bad"
    try:block.load_batch_checkpoint(checkpoint,identity,wrong_maps);adversarial["wrong_null_map"]=False
    except RuntimeError:adversarial["wrong_null_map"]=True
    dtype_dir=out/"dtype_checkpoint";block.save_batch_checkpoint(dtype_dir,identity,0,zero,zero,maps);pointer=json.loads((dtype_dir/"CURRENT.json").read_text());generation=dtype_dir/pointer["generation"];np.save(generation/"between.npy",np.zeros((2,4,12,12),np.float32));state=json.loads((generation/"BATCH_STATE.json").read_text());state["between_sha256"]=block.sha(generation/"between.npy");block.atomic_json(generation/"BATCH_STATE.json",state);pointer["batch_state_sha256"]=block.sha(generation/"BATCH_STATE.json");block.atomic_json(dtype_dir/"CURRENT.json",pointer)
    try:block.load_batch_checkpoint(dtype_dir,identity,maps);adversarial["dtype_downgrade"]=False
    except RuntimeError:adversarial["dtype_downgrade"]=True
    substitution_dir=out/"map_substitution_checkpoint";block.save_batch_checkpoint(substitution_dir,identity,2,zero,zero,{0:a_map,1:maps[1]})
    try:block.load_batch_checkpoint(substitution_dir,identity,{0:b_map,1:maps[1]});adversarial["A_map_on_B_identity_rejection"]=False
    except RuntimeError:adversarial["A_map_on_B_identity_rejection"]=True
    adversarial["cross_contamination"]=bool(np.array_equal(last[4],solo4[0]) and np.array_equal(reference[0],last[0]))
    adversarial["tail_batch"]=next(x["pass"] for x in results if x["test"]=="batch_invariance_K3")
    payload_dir=out/"payload_mutation";payload_dir.mkdir()
    null_payload={"null_full_eigenvalues":np.arange(4,dtype=np.float64),"paired_null_bootstrap_eigenvalues":np.arange(8,dtype=np.float64).reshape(2,4),"stability":np.ones(4),"heldout":np.ones((2,4),np.float32),"numerical_diagnostics_json":np.asarray("{}")};null_sha=sequential.checkpoint_payload_sha256(null_payload);null_path=payload_dir/"null.npz";np.savez(null_path,**null_payload,payload_semantic_sha256=np.asarray(null_sha));data={k:v for k,v in np.load(null_path,allow_pickle=False).items()};data["null_full_eigenvalues"]=data["null_full_eigenvalues"].copy();data["null_full_eigenvalues"][0]+=1;np.savez(null_path,**data)
    try:
        with np.load(null_path,allow_pickle=False) as saved:block.validate_scientific_payload(saved,block.NULL_PAYLOAD_FIELDS)
        adversarial["mutated_null_payload_rejected"]=False
    except RuntimeError:adversarial["mutated_null_payload_rejected"]=True
    observed_payload={"mean":np.ones((2,3)),"within":np.ones((2,3,3)),"between":np.ones((2,3,3)),"components":np.ones((3,2),np.float32),"eigenvalues":np.ones(2),"bootstrap_eigen":np.ones((2,2)),"bootstrap_stability":np.ones((2,2)),"heldout":np.ones((2,2)),"numerical_diagnostics_json":np.asarray("{}")};observed_sha=sequential.checkpoint_payload_sha256(observed_payload);observed_path=payload_dir/"observed.npz";np.savez(observed_path,**observed_payload,payload_semantic_sha256=np.asarray(observed_sha));data={k:v for k,v in np.load(observed_path,allow_pickle=False).items()};data["mean"]=data["mean"].copy();data["mean"][0,0]+=1;np.savez(observed_path,**data)
    try:
        with np.load(observed_path,allow_pickle=False) as saved:block.validate_scientific_payload(saved,block.OBSERVED_PAYLOAD_FIELDS)
        adversarial["mutated_observed_payload_rejected"]=False
    except RuntimeError:adversarial["mutated_observed_payload_rejected"]=True
    results.append({"test":"adversarial_suite","pass":all(adversarial.values()),"details":adversarial})
    passed=all(x["pass"] for x in results);report={"status":"PASS_BLOCK_MAJOR_TARGETED_PARITY" if passed else "STOP_BLOCK_MAJOR_TARGETED_PARITY","results":results}
    (out/"BLOCK_MAJOR_TARGETED_PARITY.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps(report,indent=2));
    if not passed:raise SystemExit(2)

if __name__=="__main__":main()
