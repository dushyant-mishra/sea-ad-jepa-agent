#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

import pandas as pd

from sea_ad_jepa.v5.scientific_estimand_v1 import (
    EstimandPolicy,
    GroupCount,
    group_masses,
    importance_diagnostics,
)

EXPECTED_SQLITE_SHA256="a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(8<<20),b""):
            h.update(chunk)
    return h.hexdigest()


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--metadata-sqlite",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    observed=sha256(args.metadata_sqlite)
    if observed!=EXPECTED_SQLITE_SHA256:
        raise SystemExit(f"metadata authority mismatch: {observed}")
    con=sqlite3.connect(args.metadata_sqlite)
    try:
        frame=pd.read_sql_query(
            """select source, donor_id donor, operator_index operator, count(*) cells
               from cells
               where partition='reader_fit'
               group by source, donor_id, operator_index
               order by source, donor_id, operator_index""",
            con,
        )
    finally:
        con.close()
    rows=[
        GroupCount(r.source,r.donor,int(r.operator),int(r.cells))
        for r in frame.itertuples(index=False)
    ]
    source_names=sorted(frame.source.unique())
    policies={}
    for policy in EstimandPolicy:
        masses=group_masses(rows,policy)
        source_mass={
            source:sum(m for m,row in zip(masses,rows) if row.source==source)
            for source in source_names
        }
        policies[policy.value]={
            "source_mass":source_mass,
            "vs_cell_uniform_proposal":importance_diagnostics(
                rows,target=policy,proposal=EstimandPolicy.CELL_UNIFORM
            ),
        }
    artifact={
        "schema":"READER_FIT_ESTIMAND_DIAGNOSTICS_V1",
        "population":"reader_fit",
        "reader_fit_cells":int(frame.cells.sum()),
        "donor_operator_groups":int(len(frame)),
        "metadata_sqlite_sha256":observed,
        "candidate_policies":policies,
        "selected_target_policy":None,
        "selected_proposal_policy":None,
        "interpretation":[
            "No scientific target distribution is selected by this diagnostic artifact.",
            "Raw cell-uniform proposal is variance-inefficient for donor-balanced targets; proposal q should be designed close to any selected target p rather than relying on extreme p/q correction.",
            "Scientific target p(cell), proposal q(cell), and compute microbatch packing are distinct authorities.",
        ],
        "training_authorized":False,
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(artifact,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"out":str(args.out),"sha256":sha256(args.out)},sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
