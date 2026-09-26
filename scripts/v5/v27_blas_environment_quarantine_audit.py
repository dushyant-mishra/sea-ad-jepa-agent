#!/usr/bin/env python3
"""Read-only per-environment NumPy/torch BLAS invocation-condition diagnostic.

The original Sept20 qualified environment REQUIRES <env>/Library/bin on PATH.
An absent DLL search path is an invocation failure, NOT a defective env.
Runs independent child processes so a native Windows 0xc06d007f crash cannot
terminate the parent or masquerade as a Python exception. Does not mutate or
reinstall either environment. DOES NOT classify any historical receipt without
its recorded producer environment and actual NumPy-linear-algebra dependency.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, subprocess, sys, time

CHILD=r'''
import json, sys
out={"python":sys.version.split()[0],"executable":sys.executable}
try:
    import numpy as np
    out["numpy"]=np.__version__
    out["numpy_config"]={}
    # NumPy's .show() may expose full paths; collect only top-level BLAS labels.
    try:
        d=np.__config__.show(mode="dicts")
        out["numpy_blas_names"]=sorted(k for k in d if "blas" in k.lower())
    except Exception as e: out["numpy_config_error"]=type(e).__name__
    a=np.arange(9,dtype=np.float64).reshape(3,3)
    b=(a.T @ a)
    out["numpy_3x3_ok"]=bool(np.allclose(b,[[45,54,63],[54,66,78],[63,78,93]]))
except BaseException as e:
    out["numpy_exception"]=type(e).__name__+": "+str(e)
try:
    import torch
    out["torch"]=torch.__version__
    out["torch_cuda_available"]=bool(torch.cuda.is_available())
    a=torch.arange(9,dtype=torch.float64).reshape(3,3)
    out["torch_3x3_ok"]=bool(torch.allclose(a.T@a,torch.tensor([[45.,54.,63.],[54.,66.,78.],[63.,78.,93.]],dtype=torch.float64)))
except BaseException as e:
    out["torch_exception"]=type(e).__name__+": "+str(e)
print("V27_ENV_PROBE_JSON="+json.dumps(out,sort_keys=True),flush=True)
'''
PRECHECK=r'''
import os,sys,json
p=os.path.normcase(os.path.normpath(os.path.join(sys.prefix,'Library','bin')))
paths={os.path.normcase(os.path.normpath(x)) for x in os.environ.get('PATH','').split(os.pathsep) if x}
print('V27_ENV_PATH='+json.dumps({'platform':sys.platform,'library_bin_on_path':p in paths,'expected_library_bin':p}),flush=True)
'''
def run_one(name,cmd,seconds=60):
    t=time.monotonic()
    try:
        env_check=subprocess.run(cmd+["-c",PRECHECK],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=seconds,check=False)
        hits=[x.split('V27_ENV_PATH=',1)[1] for x in env_check.stdout.splitlines() if x.startswith('V27_ENV_PATH=')]
        invocation=json.loads(hits[-1]) if hits else None
        p=subprocess.run(cmd+[ "-c", CHILD ],text=True,stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,timeout=seconds,check=False)
        marker=[s.partition("V27_ENV_PROBE_JSON=")[2] for s in p.stdout.splitlines() if s.startswith("V27_ENV_PROBE_JSON=")]
        payload=json.loads(marker[-1]) if marker else None
        success=p.returncode==0 and payload and payload.get("numpy_3x3_ok") is True and payload.get("torch_3x3_ok") is True
        if success:status="PASS_VALID_INVOCATION"
        elif invocation and invocation.get("platform")=="win32" and invocation.get("library_bin_on_path") is False:
            status="STOP_REQUIRED_LIBRARY_BIN_MISSING__NOT_AN_ENV_DEFECT"
        else:status="INCOMPLETE_OR_FAILED_PROBE__DO_NOT_INFER_ENV_DEFECT"
        return {"name":name,"status":status,"returncode":p.returncode,
                "returncode_hex":hex(p.returncode & 0xFFFFFFFF),
                "invocation_path_precheck":invocation,"payload":payload, "stdout_tail":p.stdout[-2500:],"stderr_tail":p.stderr[-2500:],
                "wall_seconds":round(time.monotonic()-t,2)}
    except subprocess.TimeoutExpired as e:
        return {"name":name,"status":"INCOMPLETE_TIMEOUT_NOT_ENV_DEFECT","seconds":seconds,
                "stdout_tail":str(e.stdout)[-400:],"stderr_tail":str(e.stderr)[-400:]}
    except (OSError,ValueError) as e:
        return {"name":name,"status":"INCOMPLETE_LAUNCH_FAILURE_NOT_ENV_DEFECT","error":str(e)}
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--conda",default="conda")
    a.add_argument("--environment",action="append",default=[],help="Explicit isolated conda env (repeat)")
    a.add_argument("--local-python",action="store_true",help="Test current Python only; NOT a substitute for Windows CUDA laptop")
    a.add_argument("--out",required=True)
    x=a.parse_args()
    if not x.environment and not x.local_python:
        a.error("pass --environment sea-ad-jepa --environment sea-ad-jepa-v3, or --local-python")
    rows=[]
    for name in x.environment:
        rows.append(run_one(name,[x.conda,"run","--no-capture-output","-n",name,"python"]))
    if x.local_python:rows.append(run_one("LOCAL_CONTROL_NOT_GPU_ENV",[sys.executable]))
    result={"schema":"V27_ISOLATED_BLAS_ENV_AUDIT_V1","status":"READ_ONLY_ENV_DIAGNOSTIC__NO_SCIENTIFIC_RESULT",
            "observed_at_utc":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "training_authorized":False,"rows":rows,
            "limitations":["Local Linux control is not the Windows GPU laptop environment",
                "Sept20 prior authority already qualifies sea-ad-jepa CONDITIONAL on Library/bin on PATH; S9 broken-environment claim was retracted Sept26",
                "Do not rerun prior science on the basis of a missing invocation DLL path",
                "Subprocess crash returncodes are preserved, not hidden by a Python try/except"]}
    path=pathlib.Path(x.out)
    if path.exists():raise SystemExit("STOP_EXISTING_ENV_RECEIPT")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"receipt":str(path),"results":[(r["name"],r["status"],r.get("returncode_hex")) for r in rows]}))
if __name__=="__main__":main()
