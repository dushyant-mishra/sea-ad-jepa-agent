#!/usr/bin/env python3
"""Synthetic-only qualification of the V65 recoverability rank decision.

No real NIH-CARD matrix values are read. This harness operates on synthetic donor-level
metric fixtures to test the decision semantics themselves.

The key negative control is a monotone fully-recoverable fixture: ranks 2,4,8,16 all
satisfy every frozen gate. Under the current SMALLEST_ELIGIBLE rule, it selects rank 2,
making RNA_RECOVERABLE practically unreachable for a nested factor. That is a design
defect, not a biological result.
"""
from __future__ import annotations
import json
from pathlib import Path

RANKS=(2,4,8,16)


def donor(pass_delta=True, pass_r2=True, pass_perm=True, pass_geom=True,
          delta=0.12, candidate_r2=0.50, tech_r2=0.10, global_r2=0.20):
    if not pass_delta:
        delta=-0.01
    if not pass_r2:
        candidate_r2=-0.02
    return dict(delta_r2=delta, candidate_r2=candidate_r2,
                technical_r2=tech_r2, global_rna_r2=global_r2,
                permutation_gate=pass_perm, geometry_gate=pass_geom)


def rank_eligible(ds):
    deltas=[d["delta_r2"] for d in ds]
    sr=sorted(deltas)
    median=(sr[1]+sr[2])/2
    return (
        all(x>0 for x in deltas)
        and median>=0.05
        and all(d["candidate_r2"]>0 for d in ds)
        and all(d["permutation_gate"] for d in ds)
        and all(d["geometry_gate"] for d in ds)
        and all(d["candidate_r2"]-d["technical_r2"]>0.01 for d in ds)
    )


def choose(metrics, policy):
    eligible=[k for k in RANKS if rank_eligible(metrics[k])]
    if not eligible:
        return 0
    if policy=="SMALLEST_ELIGIBLE_NONZERO_RANK":
        return min(eligible)
    if policy=="LARGEST_ELIGIBLE_NONZERO_RANK":
        return max(eligible)
    raise ValueError(policy)


def classify(k):
    if k==16:
        return "RNA_RECOVERABLE"
    if k in (2,4,8):
        return "PARTIALLY_RNA_RECOVERABLE"
    return "UNQUALIFIED"


def main():
    full={k:[donor() for _ in range(4)] for k in RANKS}
    partial={k:[donor() for _ in range(4)] for k in RANKS}
    # Only ranks <=4 pass in partial fixture.
    for k in (8,16):
        partial[k][0]=donor(pass_delta=False)

    shortcut={k:[donor(candidate_r2=.50, tech_r2=.495, global_r2=.20)
                 for _ in range(4)] for k in RANKS}
    null={k:[donor(pass_perm=False) for _ in range(4)] for k in RANKS}

    out={
      "schema":"V65_RECOVERABILITY_DECISION_SYNTHETIC_QUALIFICATION_V1",
      "uses_real_biology":False,
      "fixtures":{
        "FULLY_RECOVERABLE":{
          "smallest":choose(full,"SMALLEST_ELIGIBLE_NONZERO_RANK"),
          "largest":choose(full,"LARGEST_ELIGIBLE_NONZERO_RANK")},
        "PARTIAL_RANK4":{
          "largest":choose(partial,"LARGEST_ELIGIBLE_NONZERO_RANK")},
        "TECHNICAL_SHORTCUT":{
          "largest":choose(shortcut,"LARGEST_ELIGIBLE_NONZERO_RANK")},
        "PAIRING_NULL_FAIL":{
          "largest":choose(null,"LARGEST_ELIGIBLE_NONZERO_RANK")}
      }
    }
    assert out["fixtures"]["FULLY_RECOVERABLE"]["smallest"]==2
    assert classify(out["fixtures"]["FULLY_RECOVERABLE"]["smallest"])=="PARTIALLY_RNA_RECOVERABLE"
    assert out["fixtures"]["FULLY_RECOVERABLE"]["largest"]==16
    assert classify(out["fixtures"]["FULLY_RECOVERABLE"]["largest"])=="RNA_RECOVERABLE"
    assert out["fixtures"]["PARTIAL_RANK4"]["largest"]==4
    assert out["fixtures"]["TECHNICAL_SHORTCUT"]["largest"]==0
    assert out["fixtures"]["PAIRING_NULL_FAIL"]["largest"]==0
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
