#!/usr/bin/env python3
"""Freeze an outcome-blind donor split for the V64 paired NIH-CARD subset.

The split depends only on donor IDs and a fixed seed. It does not inspect RNA or
ATAC values and therefore cannot be outcome-adaptive.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np

def make_split(donors:list[str], seed:int=20260930)->dict:
    uniq=sorted(set(map(str,donors)))
    if len(uniq)!=24:
        raise ValueError(f"expected 24 donors, got {len(uniq)}")
    order=sorted(uniq,key=lambda x:hashlib.sha256(f"{seed}|{x}".encode()).hexdigest())
    return {
        "seed":seed,
        "rule":"sort unique donor IDs by sha256('<seed>|<donor_id>'); first 16 TRAIN, next 4 VALIDATION, last 4 TEST",
        "train":order[:16],
        "validation":order[16:20],
        "test":order[20:24],
    }

def main(argv=None)->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--npz",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args(argv)
    z=np.load(args.npz,allow_pickle=True)
    split=make_split(z["donor_id"].tolist())
    donors=np.asarray(z["donor_id"],dtype=str)
    split["nuclei_per_split"]={
        k:int(np.isin(donors,v).sum()) for k,v in
        [("train",split["train"]),("validation",split["validation"]),("test",split["test"])]
    }
    split["training_authorized"]=False
    split["stage4_correspondence_authorized"]=False
    args.output.write_text(json.dumps(split,indent=2,sort_keys=True)+"\n")
    print(json.dumps(split,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
