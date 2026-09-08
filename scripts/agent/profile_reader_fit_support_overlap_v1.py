#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

EXPECTED_OBSERVATION_SHA256="852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
EXPECTED_RECURRENCE_SHA256="8f90c91e333eba6b58c39767069addef72bb4d9d6015ad8de14e7ff383c092da"
VOCABULARY_SIZE=41_238


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(8<<20),b""):
            h.update(chunk)
    return h.hexdigest()


def source_for_matrix(matrix_id:str)->str:
    if matrix_id.startswith("HVS::"):
        return "HVS"
    if matrix_id.startswith("NPH52::"):
        return "NPH52"
    return "SEA_AD"


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--operator-observation-state",type=Path,required=True)
    parser.add_argument("--support-recurrence",type=Path,required=True)
    parser.add_argument("--profile-out",type=Path,required=True)
    parser.add_argument("--core-csv-out",type=Path,required=True)
    args=parser.parse_args()

    observed_state=sha256(args.operator_observation_state)
    observed_recurrence=sha256(args.support_recurrence)
    if observed_state!=EXPECTED_OBSERVATION_SHA256:
        raise SystemExit(f"operator observation authority mismatch: {observed_state}")
    if observed_recurrence!=EXPECTED_RECURRENCE_SHA256:
        raise SystemExit(f"support recurrence authority mismatch: {observed_recurrence}")

    bundle=np.load(args.operator_observation_state,allow_pickle=False)
    state_names=[str(x) for x in bundle["state_names"]]
    if state_names!=[
        "STRUCTURALLY_UNMEASURED",
        "MEASURED_SCALAR",
        "MEASURED_COLLISION_UNRESOLVED",
    ]:
        raise RuntimeError(f"unexpected observation-state registry: {state_names}")
    states=bundle["states"]
    if states.shape!=(42,VOCABULARY_SIZE):
        raise RuntimeError(f"unexpected observation-state shape: {states.shape}")
    if not np.array_equal(bundle["molecular_address_index"],np.arange(VOCABULARY_SIZE)):
        raise RuntimeError("canonical address indices are not exact 0..41237")

    measured=states==state_names.index("MEASURED_SCALAR")
    sources=np.array([source_for_matrix(str(x)) for x in bundle["matrix_id"]])
    expected_counts={"HVS":24,"NPH52":7,"SEA_AD":11}
    if {s:int((sources==s).sum()) for s in expected_counts}!=expected_counts:
        raise RuntimeError("operator source counts do not match reader-fit authority")

    common=measured.all(axis=0)
    recurrence=pd.read_csv(args.support_recurrence)
    if len(recurrence)!=VOCABULARY_SIZE:
        raise RuntimeError("support recurrence row count mismatch")
    if not np.array_equal(recurrence["molecular_address_index"].to_numpy(),np.arange(VOCABULARY_SIZE)):
        raise RuntimeError("support recurrence is not in canonical address order")
    core=recurrence.loc[
        common,["molecular_address_index","molecular_address_id","symbol"]
    ].copy()
    args.core_csv_out.parent.mkdir(parents=True,exist_ok=True)
    core.to_csv(args.core_csv_out,index=False,lineterminator="\n")
    core_sha=sha256(args.core_csv_out)

    profile={
        "schema":"READER_FIT_SUPPORT_OVERLAP_PROFILE_V1",
        "operator_observation_state_sha256":observed_state,
        "support_recurrence_sha256":observed_recurrence,
        "operators":42,
        "vocabulary_size":VOCABULARY_SIZE,
        "all_42_operators_measured_scalar":int(common.sum()),
        "all_42_fraction_of_universe":float(common.mean()),
        "source_support":{},
        "common_core_materialization":{
            "rows":int(len(core)),
            "csv_sha256":core_sha,
            "checked_in":False,
            "generator":"scripts/agent/profile_reader_fit_support_overlap_v1.py",
        },
        "candidate_use_only":True,
        "training_authorized":False,
        "interpretation":[
            "The all-42 common measured core is outcome-blind support geometry, not a training objective.",
            "Native-support views may retain all operator-specific measured addresses; a future reviewed common-core view may use this exact support to equalize molecular availability across operators.",
            "No mask fraction, visible-gene budget, block size, or loss weight is frozen here.",
        ],
    }
    for source,count in expected_counts.items():
        group=measured[sources==source]
        all_support=group.all(axis=0)
        any_support=group.any(axis=0)
        profile["source_support"][source]={
            "operators":count,
            "measured_by_all_source_operators":int(all_support.sum()),
            "measured_by_any_source_operator":int(any_support.sum()),
            "common_core_fraction_of_source_all_support":float(common.sum()/all_support.sum()),
        }

    args.profile_out.parent.mkdir(parents=True,exist_ok=True)
    args.profile_out.write_text(
        json.dumps(profile,indent=2,sort_keys=True)+"\n",encoding="utf-8"
    )
    print(json.dumps({
        "profile_sha256":sha256(args.profile_out),
        "core_csv_sha256":core_sha,
        "core_rows":int(len(core)),
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
