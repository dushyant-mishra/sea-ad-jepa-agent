"""Standalone V29 precommit/checkpoint MECHANICAL evidence verifier (no training).

Requires physically supplied per-tensor values and byte-complete checkpoint parts.
It does not create a current V5 training authority, authenticate real CUDA tensors,
or install itself in a live trainer. Existing inline gradient gate remains primary.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile

SCHEMA="V29_INACTIVE_MECHANICAL_POSTSTEP_EVIDENCE_V1"
REQUIRED_PARTS=("online.state","teacher.state","predictor.state","optimizer.state",
                "rng.state","cursor.state","telemetry.state","authority.state")
GRAD_KEYS=("missing","nonfinite","exact_zero","teacher_gradients")

def _finite(v,where):
    if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(float(v)):
        raise ValueError("STOP_NONFINITE_OR_NONNUMERIC_"+where)
    return float(v)
def _vector(v,where):
    if not isinstance(v,list) or not v:
        raise ValueError("STOP_MISSING_VECTOR_"+where)
    return tuple(_finite(x,where) for x in v)
def _positive(v,where):
    x=_finite(v,where)
    if x<=0:raise ValueError("STOP_NONPOSITIVE_"+where)
    return x
def digest(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def _canon(d):return json.dumps(d,sort_keys=True,separators=(",",":"),allow_nan=False).encode()

def validate_precommit(e:dict)->dict:
    if not isinstance(e,dict) or e.get("schema")!=SCHEMA:
        raise ValueError("STOP_WRONG_MECHANICAL_EVIDENCE_SCHEMA")
    if e.get("training_authorized") is not False or e.get("execution_authorized") is not False:
        raise ValueError("STOP_FAKE_TRAINING_OR_EXECUTION_AUTHORITY")
    g=e.get("gradient")
    if not isinstance(g,dict) or set(g)!=set(GRAD_KEYS)|{"max_abs_gradient","per_parameter_observations","inline_before_step"}:
        raise ValueError("STOP_MISSING_OR_MALFORMED_GRADIENT_REPORT")
    if g["inline_before_step"] is not True:
        raise ValueError("STOP_NO_INLINE_GRADIENT_GATE_PROVENANCE")
    for k in GRAD_KEYS:
        if type(g[k]) is not int or g[k]!=0:raise ValueError("STOP_GRADIENT_GATE_"+k)
    _positive(g["max_abs_gradient"],"GRADIENT_MAX")
    before=e.get("online_before")
    after=e.get("online_after")
    moments=e.get("optimizer_moments_after")
    observed=g.get("per_parameter_observations")
    if not all(isinstance(x,dict) and x for x in (before,after,moments,observed)):
        raise ValueError("STOP_MISSING_PROTECTED_PARAMETER_OR_MOMENT_MAP")
    keys=set(before)
    if not(keys==set(after)==set(moments)==set(observed)):
        raise ValueError("STOP_PROTECTED_PARAMETER_SET_MISMATCH")
    if type(e.get("optimizer_step_before")) is not int or type(e.get("optimizer_step_after")) is not int:
        raise ValueError("STOP_OPTIMIZER_STEP_MISSING")
    if e["optimizer_step_after"]!=e["optimizer_step_before"]+1:
        raise ValueError("STOP_OPTIMIZER_STEP_SKIPPED_OR_REPEATED")
    if type(e.get("cursor_before")) is not int or type(e.get("cursor_after")) is not int:
        raise ValueError("STOP_CURSOR_MISSING")
    if e["cursor_after"]!=e["cursor_before"]+1 or e["cursor_before"]!=e["optimizer_step_before"]:
        raise ValueError("STOP_CURSOR_SKIPPED_OR_NOT_ALIGNED")
    p=e.get("accepted_scientific_presentations")
    if type(p) is not int or p<=0:
        raise ValueError("STOP_ZERO_OR_UNCOUNTED_PRESENTATIONS")
    lr=_positive(e.get("learning_rate"),"LR")
    wd=_finite(e.get("weight_decay"),"WEIGHT_DECAY")
    if wd<0:raise ValueError("STOP_NEGATIVE_WEIGHT_DECAY")
    moved=0.
    for name in sorted(keys):
        if not isinstance(name,str) or not name.strip():raise ValueError("STOP_EMPTY_PARAM_NAME")
        b=_vector(before[name],name+"_BEFORE")
        a=_vector(after[name],name+"_AFTER")
        if len(b)!=len(a):raise ValueError("STOP_PARAMETER_SHAPE_DRIFT")
        gr=observed[name]
        if not isinstance(gr,dict) or set(gr)!={"finite","nonzero","max_abs"}:
            raise ValueError("STOP_MISSING_GRADIENT_PER_PARAMETER_"+name)
        if gr["finite"] is not True or gr["nonzero"] is not True or _positive(gr["max_abs"],"GRADIENT_"+name)<=0:
            raise ValueError("STOP_INVALID_PROTECTED_GRADIENT_"+name)
        m=moments[name]
        if not isinstance(m,dict) or set(m)!={"exp_avg","exp_avg_sq","step"}:
            raise ValueError("STOP_MISSING_ADAM_MOMENT_"+name)
        avg=_vector(m["exp_avg"],name+"_ADAM_AVG")
        sq=_vector(m["exp_avg_sq"],name+"_ADAM_SQ")
        if len(avg)!=len(b) or len(sq)!=len(b) or any(v<0 for v in sq):
            raise ValueError("STOP_ADAM_STATE_SHAPE_OR_NEGATIVE_VARIANCE_"+name)
        if not any(v!=0 for v in avg) or not any(v>0 for v in sq):
            raise ValueError("STOP_EMPTY_ADAM_FIRST_OR_SECOND_MOMENT_"+name)
        if type(m["step"]) is not int or m["step"]!=e["optimizer_step_after"]:
            raise ValueError("STOP_ADAM_STEP_CHRONOLOGY_"+name)
        moved=max(moved,max(abs(y-x*(1-lr*wd)) for x,y in zip(b,a)))
    if moved<=0:raise ValueError("STOP_DECAY_ONLY_OR_NO_PARAMETER_UPDATE")
    tb=e.get("teacher_before")
    tm=e.get("teacher_preema")
    ta=e.get("teacher_after_ema")
    if not all(isinstance(v,dict) and set(v)==keys for v in (tb,tm,ta)):
        raise ValueError("STOP_TEACHER_PARAMETER_SET_MISMATCH")
    h=_positive(e.get("ema_half_life_presentations"),"EMA_HALF_LIFE")
    m=math.exp(math.log(.5)*p/h)
    for name in sorted(keys):
        b=_vector(tb[name],name+"_TEACHER_BEFORE")
        pre=_vector(tm[name],name+"_TEACHER_PREEMA")
        final=_vector(ta[name],name+"_TEACHER_POSTEMA")
        online=_vector(after[name],name+"_ONLINE_POSTSTEP")
        if len(b)!=len(pre) or len(b)!=len(final) or len(b)!=len(online):
            raise ValueError("STOP_EMA_SHAPE_MISMATCH")
        if pre!=b:raise ValueError("STOP_TEACHER_UPDATED_BEFORE_PROVED_STEP")
        for prev,new,actual in zip(b,online,final):
            if not math.isclose(actual,m*prev+(1-m)*new,rel_tol=1e-12,abs_tol=1e-12):
                raise ValueError("STOP_EMA_DID_NOT_FOLLOW_PROVED_STEP")
    return {"schema":"V29_POSTSTEP_MECHANICAL_PREFLIGHT_V1","status":"STRUCTURAL_AND_NUMERIC_EVIDENCE_CHECK_ONLY",
            "parameter_count":len(keys),"max_beyond_decay_change":moved,
            "optimizer_step":e["optimizer_step_after"],"next_cursor":e["cursor_after"],
            "accepted_presentations":p,"training_authorized":False,"execution_authorized":False}

def validate_parts(directory:Path,manifest:dict)->dict:
    if not isinstance(manifest,dict) or set(manifest)!=set(REQUIRED_PARTS):
        raise ValueError("STOP_INCOMPLETE_CHECKPOINT_MANIFEST")
    for name in REQUIRED_PARTS:
        row=manifest[name]
        if not isinstance(row,dict) or set(row)!={"sha256","size"}:
            raise ValueError("STOP_MALFORMED_CHECKPOINT_MANIFEST_"+name)
        if type(row["size"]) is not int or row["size"]<=0:
            raise ValueError("STOP_EMPTY_OR_BAD_CHECKPOINT_PART_"+name)
        if not isinstance(row["sha256"],str) or len(row["sha256"])!=64:
            raise ValueError("STOP_BAD_CHECKPOINT_DIGEST_"+name)
        p=directory/name
        if not p.is_file() or p.is_symlink():
            raise ValueError("STOP_MISSING_OR_UNSAFE_CHECKPOINT_PART_"+name)
        with p.open("rb") as fh:
            b=fh.read()
        if len(b)!=row["size"] or digest(b)!=row["sha256"]:
            raise ValueError("STOP_PARTIAL_OR_TAMPERED_CHECKPOINT_PART_"+name)
    return {"part_count":len(REQUIRED_PARTS),"manifest_digest":digest(_canon(manifest))}

def publish_toy_checkpoint(directory:Path,evidence:dict,manifest:dict)->dict:
    """Synthetic/Linux atomic publication pattern; NEVER a live current-V5 checkpoint."""
    result=validate_precommit(evidence)
    files=validate_parts(directory,manifest)
    marker=directory/"COMMIT.json"
    if marker.exists():raise ValueError("STOP_REFUSE_CHECKPOINT_OVERWRITE")
    entry={**result,**files,"all_parts_reopened_and_hashed":True,
           "role":"SYNTHETIC_CHECKPOINT_PUBLICATION_ONLY__NO_TRAINING"}
    entry["receipt_digest"]=digest(_canon(entry))
    # Hardlink is an atomic exclusive no-clobber publication on the SAME filesystem.
    fd,tmp=tempfile.mkstemp(prefix=".commit-partial-",dir=str(directory))
    try:
        with os.fdopen(fd,"wb") as out:
            out.write(_canon(entry)+b"\n")
            out.flush();os.fsync(out.fileno())
        try:os.link(tmp,marker)
        except FileExistsError as exc:raise ValueError("STOP_CHECKPOINT_COMMIT_RACE") from exc
        dirfd=os.open(directory,os.O_RDONLY)
        try:os.fsync(dirfd)
        finally:os.close(dirfd)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return entry
