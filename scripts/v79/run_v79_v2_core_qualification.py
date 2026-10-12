#!/usr/bin/env python3
"""Identity-blind V79 V2_CORE qualification campaign orchestrator."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Mapping

import v79_v2_core_fit_contract as FC
import v79_v2_core_qualification_custody as C

SOURCE_CONTRACT_SHA256=FC.SOURCE_CONTRACT_SHA256
CAMPAIGN_RECEIPT_NAME="V79_V2_CORE_QUALIFICATION_CAMPAIGN_RECEIPT_V1.json"
WORLD_WORKER="run_v79_v2_core_qualification_world.py"

class QualificationRunRefused(RuntimeError): pass

def _refuse(msg:str): raise QualificationRunRefused(f"REFUSED V2_CORE qualification run: {msg}")
def _canonical(obj:Mapping)->bytes: return (json.dumps(dict(obj),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode("utf-8")
def _sha(path:Path)->str: return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def group_queue_by_world(queue:list[Mapping])->list[tuple[str,list[Mapping]]]:
    out=[]; current=None; rows=[]
    for item in queue:
        oid=str(item.get("opaque_world_id",""))
        if not re.fullmatch(r"[0-9a-f]{12}",oid): _refuse("queue contains non-opaque world id")
        if current is None: current=oid
        if oid!=current: out.append((current,rows)); current=oid; rows=[]
        rows.append(item)
    if current is not None: out.append((current,rows))
    if len({oid for oid,_ in out})!=len(out): _refuse("queue world order is non-contiguous")
    for oid,items in out:
        expected=sorted(items,key=lambda x:(int(x["gene_index"]),0 if x["part"]=="detection" else 1))
        if list(items)!=expected: _refuse(f"within-world fit order differs for {oid}")
    return out

def _validate_quantity_summary(q:Mapping,name:str)->None:
    required={"labels","mean","sd","q05","q50","q95"}
    if not isinstance(q,Mapping) or set(q)!=required: _refuse(f"scoring quantity {name} schema differs")
    labels=q["labels"]
    if not isinstance(labels,list) or any(not isinstance(x,str) for x in labels): _refuse(f"scoring quantity {name} labels differ")
    n=len(labels)
    for k in ("mean","sd","q05","q50","q95"):
        vals=q[k]
        if not isinstance(vals,list) or len(vals)!=n or any(not isinstance(x,(int,float)) for x in vals): _refuse(f"scoring quantity {name}.{k} differs")

def _validate_scoring_summary(summary:Mapping,part:str)->None:
    if not isinstance(summary,Mapping) or summary.get("schema")!="V79_V2_CORE_IDENTIFIED_POSTERIOR_SUMMARY_V1" or summary.get("part")!=part:
        _refuse("identified scoring summary schema/part differs")
    identification=summary.get("identification"); quantities=summary.get("quantities")
    if not isinstance(identification,Mapping) or set(identification)!={"class","source","donor_codes"}: _refuse("identification metadata differs")
    for factor in ("class","source"):
        rec=identification[factor]
        if not isinstance(rec,Mapping) or rec.get("mode") not in {"helmert","level_differences"} or not isinstance(rec.get("observed_levels"),list):
            _refuse(f"{factor} identification differs")
    expected={"intercept","depth1","depth2","class","source","donor_sd","donor_effects"}|({"sigma"} if part=="positive" else set())
    if not isinstance(quantities,Mapping) or set(quantities)!=expected: _refuse("identified quantity set differs")
    for name,q in quantities.items(): _validate_quantity_summary(q,name)

def _validate_existing_receipt(path:Path,item:Mapping)->Mapping:
    try: raw=path.read_bytes(); r=json.loads(raw.decode("utf-8"))
    except Exception as exc: _refuse(f"unreadable existing fit receipt {path.name}: {exc}")
    if _canonical(r)!=raw: _refuse(f"existing fit receipt not canonical: {path.name}")
    required={"schema":"V79_V2_CORE_FIT_RECORD_V1","execution_mode":"QUALIFICATION","fit_id":item["fit_id"],
              "opaque_world_id":item["opaque_world_id"],"gene_index":int(item["gene_index"]),"part":item["part"],
              "input_manifest_sha256":item["world_manifest_sha256"],"contract_sha256":SOURCE_CONTRACT_SHA256,
              "benchmark_run":False,"qualification_fits_run":1,"scoring_run":False,"truth_accessed":False,"training_authorized":False}
    for k,v in required.items():
        if r.get(k)!=v: _refuse(f"existing fit receipt mismatch {path.name}: {k}")
    if r.get("final_diagnosis") not in {"COMPLETE","NOT_DIAGNOSED"}: _refuse(f"existing fit is not terminal: {path.name}")
    diag=r.get("final_diagnostics")
    if not isinstance(diag,Mapping) or not {"divergences","worst_rhat","worst_ess_bulk","worst_ess_tail","mean_tree_steps"}<=set(diag): _refuse("final diagnostics missing")
    _validate_scoring_summary(r.get("scoring_summary"),str(item["part"]))
    ppc=r.get("ppc")
    if not isinstance(ppc,list) or not ppc: _refuse("PPC table missing")
    for row in ppc:
        if not isinstance(row,Mapping) or set(row)!={"name","observed","p_value"} or not isinstance(row["name"],str) or not isinstance(row["p_value"],(int,float)) or not (0.0<=float(row["p_value"])<=1.0):
            _refuse("PPC row differs")
    artifacts=r.get("posterior_artifacts",{})
    if not isinstance(artifacts,Mapping) or set(artifacts)!={"donor_effect_draws"}: _refuse("posterior artifact set differs")
    for rec in artifacts.values():
        if not isinstance(rec,Mapping) or set(rec)!={"path","sha256"}: _refuse("posterior artifact record differs")
        rel=Path(str(rec["path"]))
        if rel.is_absolute() or len(rel.parts)!=1 or rel.name!=str(rec["path"]): _refuse("posterior artifact path must be a result-root basename")
        ap=path.parent/rel
        if not ap.is_file() or _sha(ap)!=rec["sha256"]: _refuse(f"posterior artifact missing/hash mismatch: {ap.name}")
    return r

def completed_prefix(result_dir:Path,queue:list[Mapping])->int:
    result_dir=Path(result_dir)
    if not result_dir.exists(): return 0
    count=0; missing=False
    known={f"fit_{x['fit_id']}.json" for x in queue}; actual_fit={p.name for p in result_dir.glob("fit_*.json")}
    if actual_fit-known: _refuse(f"unknown fit receipts present: {sorted(actual_fit-known)[:3]}")
    for item in queue:
        p=result_dir/f"fit_{item['fit_id']}.json"
        if p.is_file():
            if missing: _refuse("checkpoint is not a contiguous qualification prefix")
            _validate_existing_receipt(p,item); count+=1
        else: missing=True
    return count

def campaign_receipt_skeleton(*,code_sha:str,custody_receipt_sha:str,fit_count:int)->dict:
    return {"schema":"V79_V2_CORE_QUALIFICATION_CAMPAIGN_RECEIPT_V1","code_sha":code_sha,"custody_receipt_sha256":custody_receipt_sha,
            "planned_fit_count":int(fit_count),"fit_records":[],"qualification_fits_run":0,"benchmark_run":False,
            "scoring_run":False,"truth_accessed":False,"training_authorized":False}

def finalize_campaign(result_dir:Path,queue:list[Mapping],*,code_sha:str,custody_receipt_sha:str)->dict:
    result_dir=Path(result_dir)
    if completed_prefix(result_dir,queue)!=len(queue): _refuse("cannot finalize incomplete campaign")
    rec=campaign_receipt_skeleton(code_sha=code_sha,custody_receipt_sha=custody_receipt_sha,fit_count=len(queue))
    for item in queue:
        p=result_dir/f"fit_{item['fit_id']}.json"; _validate_existing_receipt(p,item)
        rec["fit_records"].append({"fit_id":item["fit_id"],"path":p.name,"sha256":_sha(p)})
    rec["qualification_fits_run"]=len(queue); raw=_canonical(rec); rp=result_dir/CAMPAIGN_RECEIPT_NAME
    if rp.exists():
        if rp.read_bytes()!=raw: _refuse("existing campaign receipt differs from deterministic reconstruction")
    else: rp.write_bytes(raw)
    return rec

def _git_head(root:Path)->str: return subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
def _require_clean(root:Path)->None:
    if subprocess.check_output(["git","status","--porcelain"],cwd=root,text=True).strip(): _refuse("repository working tree is not clean")

def execute_campaign(root:Path,custody_dir:Path,result_dir:Path,*,expected_custody_receipt_sha256:str)->dict:
    root=Path(root); custody_dir=Path(custody_dir); result_dir=Path(result_dir); _require_clean(root)
    custody=C.load_qualification_custody(custody_dir,expected_receipt_sha256=expected_custody_receipt_sha256); code_sha=_git_head(root)
    if custody.receipt.get("executor_code_head")!=code_sha: _refuse("qualification custody was prepared for a different code head")
    queue=list(custody.queue); groups=group_queue_by_world(queue)
    if len(groups)!=int(custody.fit_contract["resources"]["qualification_world_count"]): _refuse("opaque world count differs from fit contract")
    done=completed_prefix(result_dir,queue)
    if not result_dir.exists(): result_dir.mkdir(parents=True,exist_ok=False)
    if done==len(queue): return finalize_campaign(result_dir,queue,code_sha=code_sha,custody_receipt_sha=custody.receipt_sha256)
    worker=root/"scripts/v79"/WORLD_WORKER
    if not worker.is_file(): _refuse("qualification world worker is missing")
    settle=float(custody.fit_contract["resources"]["settle_seconds_between_worlds"]); cumulative=0
    for oid,items in groups:
        end=cumulative+len(items)
        if done>=end: cumulative=end; continue
        proc=subprocess.run([sys.executable,str(worker),str(root),str(custody_dir),str(result_dir),expected_custody_receipt_sha256,oid],cwd=root,check=False)
        if proc.returncode!=0: _refuse(f"world worker failed for opaque world {oid} with exit {proc.returncode}")
        now=completed_prefix(result_dir,queue)
        if now<end: _refuse(f"world worker exited without completing its opaque world {oid}")
        done=now; cumulative=end
        if done<len(queue): time.sleep(settle)
    if done!=len(queue): _refuse("campaign ended before all frozen fits completed")
    return finalize_campaign(result_dir,queue,code_sha=code_sha,custody_receipt_sha=custody.receipt_sha256)

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("root"); p.add_argument("custody_dir"); p.add_argument("result_dir"); p.add_argument("expected_custody_receipt_sha256")
    a=p.parse_args(argv); print(json.dumps(execute_campaign(Path(a.root),Path(a.custody_dir),Path(a.result_dir),expected_custody_receipt_sha256=a.expected_custody_receipt_sha256),indent=2))
if __name__=="__main__": main()
