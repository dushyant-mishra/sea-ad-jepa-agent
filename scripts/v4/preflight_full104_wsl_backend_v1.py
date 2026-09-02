#!/usr/bin/env python3
"""Fail-closed provenance capture for the WSL FULL104 compute backend."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import torch


def sha(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(8<<20),b""):digest.update(chunk)
    return digest.hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--project",required=True);parser.add_argument("--matrix",required=True);parser.add_argument("--plan",required=True);parser.add_argument("--out",required=True)
    args=parser.parse_args();project=Path(args.project).resolve();matrix=Path(args.matrix).resolve();plan=Path(args.plan).resolve();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False)
    if not str(project).startswith("/mnt/d/") or not str(matrix).startswith(str(project)) or not str(plan).startswith(str(project)):raise RuntimeError("WSL canonical mount gate failed")
    scripts=project/"scripts/v4";sources={name:scripts/name for name in ("full104_refit_null_sensitivity_core_v1.py","run_full104_refit_null_sensitivity_v1.py","run_full104_refit_null_block_major_v1.py","derive_full104_phase2_shared_state.py")}
    buffer=io.StringIO()
    with contextlib.redirect_stdout(buffer):np.show_config();scipy.show_config()
    gpu=torch.cuda.get_device_properties(0) if torch.cuda.is_available() else None
    report={"status":"PASS_WSL_BACKEND_PREFLIGHT" if torch.cuda.is_available() else "STOP_WSL_CUDA_UNAVAILABLE",
            "project_realpath":str(project),"same_canonical_windows_volume_via_mnt_d":True,"python":sys.version,
            "platform":platform.platform(),"numpy":np.__version__,"scipy":scipy.__version__,"pandas":pd.__version__,
            "torch":torch.__version__,"torch_cuda":torch.version.cuda,"cuda_available":torch.cuda.is_available(),
            "gpu":None if gpu is None else {"name":gpu.name,"total_memory":gpu.total_memory,"compute_capability":[gpu.major,gpu.minor]},
            "blas_lapack_config":buffer.getvalue(),"source_sha256":{name:sha(path) for name,path in sources.items()},
            "matrix_manifest_sha256":sha(matrix/"PHASE2_FEATURE_MATRIX_MANIFEST.csv"),"all_plan_sha256":sha(plan/"NESTED_WEIGHTED_SELECTION.npz"),
            "filesystem_devices":{"project":os.stat(project).st_dev,"matrix":os.stat(matrix).st_dev,"plan":os.stat(plan).st_dev}}
    (out/"WSL_BACKEND_PREFLIGHT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="blas_lapack_config"},indent=2))
    if not report["status"].startswith("PASS_"):raise SystemExit(2)


if __name__=="__main__":main()
