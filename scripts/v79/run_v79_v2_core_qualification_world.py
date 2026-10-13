#!/usr/bin/env python3
"""Fit one opaque V79 V2_CORE qualification world in a fresh process."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import numpy as np

import v79_v2_core_fit_contract as FC
import v79_v2_core_fit_outputs as O
import v79_v2_core_fit_runner as R
import v79_v2_core_fit_surface as F
import v79_v2_core_identified_summary as I
import v79_v2_core_qualification_custody as C
import v79_v2_core_resource_monitor as RM
import v79_v2_core_runtime as RT
import v79_v2_core_runtime_lock as RL
import run_v79_v2_core_qualification as Q

class QualificationWorldRefused(RuntimeError): pass

def _refuse(msg:str): raise QualificationWorldRefused(f"REFUSED V2_CORE qualification world: {msg}")
def _sha(path:Path)->str: return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _git_head(root:Path)->str: return subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
def _require_clean(root:Path)->None:
    if subprocess.check_output(["git","status","--porcelain"],cwd=root,text=True).strip(): _refuse("repository working tree is not clean")

def _one_attempt(contract,model,seed,stage,*,post_state=None,previous_ta=None):
    started=datetime.now(timezone.utc).isoformat()
    with RM.ResourceMonitor() as mon:
        run=R.run_nuts_attempt(contract=contract,model=model,seed=seed,stage=stage,post_warmup_state=post_state,previous_target_accept=previous_ta)
    ended=datetime.now(timezone.utc).isoformat(); diag,samples=R.attempt_diagnostics(run); rec=dict(run["spec"]); rec.update(diag)
    rec.update({"seed":int(seed),"started_at_utc":started,"ended_at_utc":ended,"wall_seconds":float(mon.wall_seconds),
                "process_cpu_seconds":float(mon.process_cpu_seconds),"peak_working_set_bytes":int(mon.peak_rss)})
    import jax
    rec["jax_devices"]=[str(x) for x in jax.devices()]; return rec,samples,run["mcmc"]

def _active_lineage_index(attempts:list[Mapping])->int:
    esc=[i for i,a in enumerate(attempts) if a.get("stage")=="ESCALATION"]; return esc[-1] if esc else 0

def _write_npz_once(path:Path,**arrays)->str:
    if path.exists(): _refuse(f"refusing to overwrite posterior artifact {path.name}")
    tmp=path.with_name(path.name+f".tmp.{os.getpid()}")
    if tmp.exists(): _refuse(f"stale posterior artifact temp exists: {tmp.name}")
    path.parent.mkdir(parents=True,exist_ok=True)
    with tmp.open("wb") as f: np.savez(f,**arrays)
    os.replace(tmp,path); return _sha(path)

def _heldout_predictive(active_samples:Mapping[str,np.ndarray], world:F.BlindedWorld, *, gene_index:int, part:str)->dict:
    import v79_v2_core_fit_predictive as P
    same=F.load_gene_inputs(world,gene_index=gene_index,replicate="same_donor")
    new=F.load_gene_inputs(world,gene_index=gene_index,replicate="new_donor")
    if part=="detection":
        return {
            "same_donor":P.detection_heldout_metrics(active_samples,design=world.design,detected=np.asarray(same.detected),
                measured_mask=np.asarray(same.detection_mask),new_donor=False,posterior_draws=200,calibration_bins=10,gh_nodes=40),
            "new_donor":P.detection_heldout_metrics(active_samples,design=world.design,detected=np.asarray(new.detected),
                measured_mask=np.asarray(new.detection_mask),new_donor=True,posterior_draws=200,calibration_bins=10,gh_nodes=40),
        }
    if part=="positive":
        return {
            "same_donor":P.positive_heldout_metrics(active_samples,design=world.design,observed=np.asarray(same.observed),
                positive_mask=np.asarray(same.positive_mask),new_donor=False,posterior_draws=200,gh_nodes=40),
            "new_donor":P.positive_heldout_metrics(active_samples,design=world.design,observed=np.asarray(new.observed),
                positive_mask=np.asarray(new.positive_mask),new_donor=True,posterior_draws=200,gh_nodes=40),
        }
    _refuse(f"unknown fit part for heldout prediction: {part}")

def _fit_one(*,fit_view:Mapping,world:F.BlindedWorld,item:Mapping,seed:int,code_sha:str,result_dir:Path,model_module,custody:C.QualificationCustody)->None:
    fid=str(item["fit_id"]); receipt_path=result_dir/f"fit_{fid}.json"; artifact_path=result_dir/f"donor_effect_draws_{fid}.npz"
    if receipt_path.exists(): Q._validate_existing_receipt(receipt_path,item,expected_code_sha=code_sha,expected_seed=seed); return
    if artifact_path.exists(): _refuse(f"orphan posterior artifact exists without receipt: {artifact_path.name}")
    gene=F.load_gene_inputs(world,gene_index=int(item["gene_index"]),replicate="train")
    model=model_module.build_detection_model(fit_view,gene) if item["part"]=="detection" else model_module.build_positive_model(fit_view,gene)
    frec=R.new_fit_receipt(execution_mode="QUALIFICATION",fit_id=fid,opaque_world_id=world.opaque_world_id,gene_index=int(item["gene_index"]),
        part=str(item["part"]),input_manifest_sha=world.manifest_sha256,contract_sha=FC.SOURCE_CONTRACT_SHA256,code_sha=code_sha)
    attempts=[]; active_samples=None; last_mcmc=None; previous_ta=None; stage="PRIMARY"
    while True:
        arec,samples,mcmc=_one_attempt(fit_view,model,seed,stage,
            post_state=(last_mcmc.last_state if stage=="EXTENSION" and last_mcmc is not None else None),previous_ta=previous_ta)
        attempts.append(arec)
        if stage=="EXTENSION" and active_samples is not None:
            active_samples=R.combine_samples(active_samples,samples); active_attempts=attempts[_active_lineage_index(attempts):]
            diag=R.diagnostics_from_samples(active_samples,divergences=sum(int(a["divergences"]) for a in active_attempts),
                mean_tree_steps=float(np.mean([float(a["mean_tree_steps"]) for a in active_attempts])))
        else:
            active_samples=samples; diag={k:arec[k] for k in ("divergences","worst_rhat","worst_ess_bulk","worst_ess_tail","mean_tree_steps")}
        action=R.next_recovery_action(fit_view,attempts,diag)
        if action in {"COMPLETE","NOT_DIAGNOSED"}:
            frec["final_diagnosis"]=action; frec["attempts"]=attempts; frec["final_diagnostics"]=diag; break
        previous_ta=float(arec["target_accept"]); last_mcmc=mcmc; stage="ESCALATION" if action=="ESCALATE" else "EXTENSION"
    if active_samples is None: _refuse("fit produced no posterior samples")
    data=model.v79_data; donor_basis=np.asarray(data["donor_basis_by_donor"],dtype=float)
    summary=R.posterior_summary(active_samples); summary["donor_effects"]=O.full_donor_effect_summary(active_samples,donor_basis); frec["posterior_summary"]=summary
    frec["scoring_summary"]=I.scoring_ready_summary(active_samples,data,part=str(item["part"]))
    ppc_draws=int(custody.receipt["ppc_draws"])
    if item["part"]=="detection":
        frec["ppc"]=O.posterior_predictive_detection(active_samples,data,fit_id=fid,world_log_lib=np.asarray(world.design["log_lib"]),
            measured_mask=np.asarray(gene.detection_mask),draws=ppc_draws)
    else:
        frec["ppc"]=O.posterior_predictive_positive(active_samples,data,fit_id=fid,world_log_lib=np.asarray(world.design["log_lib"]),
            positive_mask=np.asarray(gene.positive_mask),draws=ppc_draws)
    frec["heldout_predictive"]=_heldout_predictive(active_samples,world,gene_index=int(item["gene_index"]),part=str(item["part"]))
    compact=O.compact_donor_effect_draws(active_samples,donor_basis,stored_draws=int(custody.receipt["donor_draws_stored"]))
    asha=_write_npz_once(artifact_path,donor_effect_draws=compact); frec["posterior_artifacts"]={"donor_effect_draws":{"path":artifact_path.name,"sha256":asha}}
    R.write_receipt_atomic(receipt_path,frec)

def execute_world(root:Path,custody_dir:Path,result_dir:Path,*,expected_custody_receipt_sha256:str,opaque_world_id:str)->dict:
    root=Path(root); custody_dir=Path(custody_dir); result_dir=Path(result_dir); _require_clean(root)
    custody=C.load_qualification_custody(custody_dir,expected_receipt_sha256=expected_custody_receipt_sha256); code_sha=_git_head(root)
    if custody.receipt.get("executor_code_head")!=code_sha: _refuse("qualification custody was prepared for a different code head")
    items=[x for x in custody.queue if x["opaque_world_id"]==opaque_world_id]
    if not items or len(items)!=88: _refuse("opaque world does not contain frozen 88 fits")
    prefix=Q.completed_prefix(result_dir,list(custody.queue),expected_code_sha=code_sha,seed_by_fit_id=custody.seed_by_fit_id); first_missing=list(custody.queue)[prefix] if prefix<len(custody.queue) else None
    if first_missing is None: return {"opaque_world_id":opaque_world_id,"completed":0,"already_complete":True}
    if first_missing["opaque_world_id"]!=opaque_world_id: _refuse("world worker does not own the first missing checkpoint")
    RL.validate_runtime(root,require_windows=True,required_cpu_devices=None); RT.configure_before_jax_import(custody.fit_contract)
    import jax
    RT.validate_imported_jax(custody.fit_contract)
    import v79_v2_core_fit_model as M
    world=F.load_blinded_world(custody.blinded_index,opaque_world_id); completed=0
    with RM.single_heavy_fit_lock(result_dir/"HEAVY_FIT.lock"):
        for item in items:
            p=result_dir/f"fit_{item['fit_id']}.json"; seed=int(custody.seed_by_fit_id[item["fit_id"]])
            if p.exists(): Q._validate_existing_receipt(p,item,expected_code_sha=code_sha,expected_seed=seed); continue
            _fit_one(fit_view=custody.fit_contract,world=world,item=item,seed=seed,code_sha=code_sha,result_dir=result_dir,model_module=M,custody=custody); completed+=1
    return {"opaque_world_id":opaque_world_id,"completed":completed,"already_complete":False}

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("root"); p.add_argument("custody_dir"); p.add_argument("result_dir"); p.add_argument("expected_custody_receipt_sha256"); p.add_argument("opaque_world_id")
    a=p.parse_args(argv); print(json.dumps(execute_world(Path(a.root),Path(a.custody_dir),Path(a.result_dir),expected_custody_receipt_sha256=a.expected_custody_receipt_sha256,opaque_world_id=a.opaque_world_id),indent=2))
if __name__=="__main__": main()
