#!/usr/bin/env python3
"""Reproduce metadata-only V43 historical 84-cell original support receipt.

READ-ONLY. Requires locally available ORIGINAL 410MB calibration ZIP, NumPy.
Never prints any private cell/donor identifiers, runs a neural model or changes
an audited original. The physical original binary is NOT committed to GitHub.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
RECEIPT=ROOT/"docs/agent/JEPA_V43_ORIGINAL_HISTORICAL_84_CELL_SUPPORT_RECEIPT_20260926.json"

def hash_bytes(b: bytes)->str:
    return hashlib.sha256(b).hexdigest()

def hash_file(p: Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(8<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def run(bundle:Path,receipt:dict)->dict:
    source=receipt["source"]
    if not bundle.is_file() or bundle.stat().st_size!=source["bytes"] or hash_file(bundle)!=source["sha256"]:
        raise ValueError("original bundle bytes or SHA256 mismatch; do not substitute an archive")
    with zipfile.ZipFile(bundle) as z:
        exact={}
        for key,rec in receipt["members"].items():
            names=[n for n in z.namelist() if n.endswith("/"+rec["suffix"])]
            if len(names)!=1:
                raise ValueError("ambiguous or absent original member: "+key)
            b=z.read(names[0])
            if len(b)!=rec["bytes"] or hash_bytes(b)!=rec["sha256"]:
                raise ValueError("original member SHA/size mismatch: "+key)
            exact[key]=b
    n=np.load(io.BytesIO(exact["truth_npz"]),allow_pickle=False)
    obs=n["observation_state"]
    mask=n["measured_mask"]
    hidden=n["hidden_mask"]
    visible=n["final_encoder_value_input"]
    expr=n["expression_log1p10k"]
    operator=n["operator_index"]
    rows=list(csv.DictReader(io.StringIO(exact["metadata_csv"].decode("utf-8-sig"))))
    if len(rows)!=len(operator) or not np.array_equal(np.array([int(r["operator_index"]) for r in rows]),operator):
        raise ValueError("original metadata rows or operator identities mismatch")
    unique,counts=np.unique(operator,return_counts=True)
    stats={
        "rows":int(len(operator)),
        "distinct_operators":int(len(unique)),
        "cells_per_operator":int(counts[0]) if len(set(counts.tolist()))==1 else None,
        "canonical_gene_width":int(mask.shape[1]),
        "measured_addresses_per_row_min":int(mask.sum(axis=1).min()),
        "measured_addresses_per_row_max":int(mask.sum(axis=1).max()),
        "all_42_operator_common_measured_addresses":int(np.all(mask,axis=0).sum()),
        "union_measured_addresses_any_sampled_operator":int(np.any(mask,axis=0).sum()),
        "observation_state_counts_opaque_codes":{str(k):int(np.count_nonzero(obs==k)) for k in sorted(np.unique(obs).tolist())},
        "observation_state_measured_counts_opaque_codes":{str(k):int(np.count_nonzero((obs==k)&mask)) for k in sorted(np.unique(obs).tolist())},
        "same_support_within_operator":all(np.array_equal(mask[operator==o],np.broadcast_to(mask[operator==o][0],mask[operator==o].shape)) for o in unique),
        "hidden_unmeasured_entries":int(np.count_nonzero(hidden & ~mask[:,None,:])),
        "nonzero_hidden_encoder_inputs":int(np.count_nonzero(visible[hidden])),
        "nonhidden_encoder_input_expression_unequal_entries":int(np.count_nonzero(visible[~hidden]!=np.broadcast_to(expr[:,None,:],visible.shape)[~hidden])),
        "canonical_address_6186_measured_rows":int(mask[:,6186].sum()),
        "canonical_address_12469_measured_rows":int(mask[:,12469].sum()),
    }
    if stats!=receipt["physical_measurements"]:
        raise ValueError("original physical measurement diverges from V43 receipt: "+repr({k:(v,stats.get(k)) for k,v in receipt["physical_measurements"].items() if stats.get(k)!=v}))
    if receipt["scientific_authority"]!={"training_authorized":False,"protection_opened":False,"audit_b_n1_opened":False}:
        raise ValueError("receipt wrongly elevates original historical mechanics sample")
    return stats

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--original-bundle",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,default=RECEIPT)
    a=ap.parse_args()
    receipt=json.loads(a.receipt.read_text())
    stats=run(a.original_bundle,receipt)
    print("V43_PHYSICAL_ORIGINAL_84_CELL_42_OPERATOR_SUPPORT_REPLAY_EXACT")
    print("V43_HISTORICAL_COMMON_CORE_17186__NO_FULL104_SCIENTIFIC_PROMOTION")
    print("V43_HIDDEN_VALUES_ZERO_ONLY_WHERE_ACTUALLY_MASKED_AND_MEASURED")
    print(json.dumps({"rows":stats["rows"],"operators":stats["distinct_operators"],"common_core":stats["all_42_operator_common_measured_addresses"]},sort_keys=True))
if __name__=="__main__":
    main()
