#!/usr/bin/env python3
"""V65 synthetic qualification for the privileged recoverability decision engine.

Software semantics only. No real NIH-CARD RNA/ATAC values are read.
No biological claim and no execution authority are created.
"""
from __future__ import annotations

import json
import numpy as np

RANKS=(2,4,8,16)
DELTA_MARGIN=0.05
TECH_CLOSE_MARGIN=0.01
TEST_REPLICATION_FRACTION=0.5


def target_projector(z_true_train, z_pred_train, k, tie_tol=1e-10):
    zt=np.asarray(z_true_train,float)
    zp=np.asarray(z_pred_train,float)
    if zt.shape != zp.shape or zt.ndim != 2:
        raise ValueError("TRAIN true/predicted states must be aligned 2-D arrays")
    if not (1 <= k <= zt.shape[1]):
        raise ValueError("invalid rank")
    zt=zt-zt.mean(axis=0,keepdims=True)
    zp=zp-zp.mean(axis=0,keepdims=True)
    c=zt.T@zp
    u,s,_=np.linalg.svd(c,full_matrices=False)
    # A rank-k projector is not unique if the boundary singular value is tied.
    if k < len(s):
        scale=max(1.0,abs(float(s[k-1])),abs(float(s[k])))
        if abs(float(s[k-1]-s[k])) <= tie_tol*scale:
            return {"qualified":False,"reason":"SINGULAR_VALUE_TIE_AT_SELECTION_BOUNDARY"}
    uk=u[:,:k]
    p=uk@uk.T
    return {"qualified":True,"projector":p,"singular_values":s}


def _common_donor_pass(m):
    """Per-donor gates shared by VALIDATION and TEST."""
    return bool(
        m["delta_r2"] > 0
        and m["candidate_r2"] > 0
        and m["permutation_pass"]
        and m["geometry_pass"]
    )


def _validation_donor_pass(m):
    """VALIDATION-only donor gate adds the frozen technical-baseline margin."""
    return bool(
        _common_donor_pass(m)
        and (m["candidate_r2"]-m["technical_r2"]) > TECH_CLOSE_MARGIN
    )


def validation_rank_eligible(donors):
    donors=list(donors)
    if len(donors)!=4:
        raise ValueError("VALIDATION must contain exactly 4 donors")
    # The contract requires all positive, median >= margin, all gates, and
    # no technical baseline within 0.01 of candidate.
    if not all(d["delta_r2"]>0 for d in donors):
        return False
    if float(np.median([d["delta_r2"] for d in donors])) < DELTA_MARGIN:
        return False
    return all(_validation_donor_pass(d) for d in donors)


def select_validation_rank(metrics_by_rank):
    """Return the largest contiguous eligible rank from 2 upward, else 0.

    Candidate ranks are nested. A failed lower rank breaks the chain; higher ranks
    may not be used to skip over unstable lower-rank geometry. TEST is intentionally
    not an input.
    """
    selected=0
    for k in RANKS:
        if not validation_rank_eligible(metrics_by_rank[k]):
            break
        selected=k
    return selected


def test_confirmed(validation_donors, test_donors):
    validation_donors=list(validation_donors)
    test_donors=list(test_donors)
    if len(validation_donors)!=4 or len(test_donors)!=4:
        raise ValueError("VALIDATION and TEST must each contain exactly 4 donors")
    if not all(_common_donor_pass(d) for d in test_donors):
        return False
    med_v=float(np.median([d["delta_r2"] for d in validation_donors]))
    med_t=float(np.median([d["delta_r2"] for d in test_donors]))
    return bool(med_t >= DELTA_MARGIN and med_t >= TEST_REPLICATION_FRACTION*med_v)


def classify(selected_rank, validation_donors=None, test_donors=None):
    if selected_rank==0:
        return "UNQUALIFIED"
    if validation_donors is None or test_donors is None:
        return "LOCKED_PENDING_TEST"
    if not test_confirmed(validation_donors,test_donors):
        return "UNQUALIFIED"
    return "RNA_RECOVERABLE" if selected_rank==16 else "PARTIALLY_RNA_RECOVERABLE"


def donor(candidate_r2, technical_r2, global_rna_r2, permutation=True, geometry=True):
    base=max(technical_r2,global_rna_r2)
    return {
        "candidate_r2":float(candidate_r2),
        "technical_r2":float(technical_r2),
        "global_rna_r2":float(global_rna_r2),
        "delta_r2":float(candidate_r2-base),
        "permutation_pass":bool(permutation),
        "geometry_pass":bool(geometry),
    }


def _four(*xs):
    assert len(xs)==4
    return list(xs)


def synthetic_scenarios():
    good2=_four(
        donor(.42,.08,.18), donor(.40,.07,.17), donor(.38,.08,.16), donor(.41,.09,.18)
    )
    good4=_four(
        donor(.45,.08,.19), donor(.43,.07,.18), donor(.41,.08,.17), donor(.44,.09,.19)
    )
    failgeom=_four(
        donor(.42,.08,.18,geometry=False), donor(.40,.07,.17,geometry=False),
        donor(.38,.08,.16,geometry=False), donor(.41,.09,.18,geometry=False)
    )

    # Partial fixture: 2 and 4 pass, 8 fails. Even if 16 passes, it cannot skip 8.
    partial={2:good2,4:good4,8:failgeom,16:good4}

    # Fully recoverable monotone fixture: every nested rank passes -> select 16.
    full={2:good2,4:good4,8:good4,16:good4}

    # Rank-2 fails while higher ranks pass -> fail closed at rank 0.
    lower_fail={2:failgeom,4:good4,8:good4,16:good4}

    # Candidate is highly predictable but technical baseline is essentially identical.
    shortcut=_four(
        donor(.91,.905,.20), donor(.93,.925,.21), donor(.92,.915,.20), donor(.94,.935,.22)
    )
    shortcuts={k:shortcut for k in RANKS}

    # Validation fails; even spectacular TEST must never rescue a rank.
    weak=_four(
        donor(.20,.10,.17), donor(.21,.10,.18), donor(.19,.10,.17), donor(.20,.10,.18)
    )
    weak_all={k:weak for k in RANKS}
    spectacular=_four(
        donor(.95,.05,.10), donor(.94,.05,.10), donor(.96,.05,.10), donor(.95,.05,.10)
    )

    return partial,full,lower_fail,shortcuts,weak_all,spectacular


def run_smoke():
    partial,full,lower_fail,shortcuts,weak_all,spectacular=synthetic_scenarios()
    r_partial=select_validation_rank(partial)
    r_full=select_validation_rank(full)
    r_lower_fail=select_validation_rank(lower_fail)
    r_short=select_validation_rank(shortcuts)
    r_weak=select_validation_rank(weak_all)

    partial_test=_four(
        donor(.36,.07,.16), donor(.35,.07,.15), donor(.34,.08,.15), donor(.37,.08,.16)
    )
    partial_class=classify(r_partial,partial[r_partial],partial_test)

    # Explicit projector fixture: rank-2 shared target embedded in 4-D privileged state.
    rng=np.random.default_rng(6501)
    x=rng.normal(size=(1200,6))
    w=rng.normal(size=(6,2))
    shared=x@w
    private=rng.normal(size=(1200,2))
    z=np.column_stack([shared,private])
    zhat=np.column_stack([shared+0.02*rng.normal(size=shared.shape), np.zeros_like(private)])
    proj=target_projector(z,zhat,2)

    # Exact tie fixture: C = identity gives equal singular values; selecting rank 2 of 4 is non-unique.
    eye=np.eye(4)
    tie=target_projector(eye,eye,2,tie_tol=1e-12)

    out={
        "schema":"V65_PRIVILEGED_RECOVERABILITY_DECISION_ENGINE_SMOKE_V1",
        "status":"SYNTHETIC_SOFTWARE_QUALIFICATION_ONLY",
        "results":{
            "partial_contiguous_selected_rank":r_partial,
            "partial_classification":partial_class,
            "full_rank_selected":r_full,
            "lower_rank_failure_blocks_higher_ranks":r_lower_fail,
            "technical_shortcut_selected_rank":r_short,
            "validation_failure_locked_rank":r_weak,
            "spectacular_test_cannot_rescue_validation_failure":r_weak==0,
            "target_projector_rank":None if not proj["qualified"] else int(np.linalg.matrix_rank(proj["projector"])),
            "tie_fails_closed":not tie["qualified"],
        },
        "pass":bool(
            r_partial==4
            and partial_class=="PARTIALLY_RNA_RECOVERABLE"
            and r_full==16
            and r_lower_fail==0
            and r_short==0
            and r_weak==0
            and proj["qualified"]
            and np.linalg.matrix_rank(proj["projector"])==2
            and not tie["qualified"]
        ),
        "test_values_used_for_rank_selection":False,
        "privileged_private_assignable":False,
        "training_authorized":False,
        "real_paired_outcome_opened":False,
    }
    return out


def main():
    out=run_smoke()
    print(json.dumps(out,sort_keys=True,indent=2))
    return 0 if out["pass"] else 1


if __name__=="__main__":
    raise SystemExit(main())
