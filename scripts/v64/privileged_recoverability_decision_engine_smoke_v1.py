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


def _validation_metric_set_eligible(donors):
    donors=list(donors)
    if len(donors)!=4:
        raise ValueError("VALIDATION must contain exactly 4 donors")
    if not all(d["delta_r2"]>0 for d in donors):
        return False
    if float(np.median([d["delta_r2"] for d in donors])) < DELTA_MARGIN:
        return False
    return all(_validation_donor_pass(d) for d in donors)


def validation_rank_eligible(aggregate_donors, shell_donors):
    """A nested rank qualifies only if aggregate AND newly added shell qualify."""
    return bool(
        _validation_metric_set_eligible(aggregate_donors)
        and _validation_metric_set_eligible(shell_donors)
    )


def select_validation_rank(aggregate_by_rank, shell_by_rank):
    """Return largest contiguous rank whose aggregate and incremental shell both pass."""
    if set(aggregate_by_rank) != set(RANKS) or set(shell_by_rank) != set(RANKS):
        raise ValueError("aggregate and shell metrics must cover every frozen rank")
    selected=0
    for k in RANKS:
        if not validation_rank_eligible(aggregate_by_rank[k],shell_by_rank[k]):
            break
        selected=k
    return selected

def _test_metric_set_confirmed(validation_donors, test_donors):
    validation_donors=list(validation_donors)
    test_donors=list(test_donors)
    if len(validation_donors)!=4 or len(test_donors)!=4:
        raise ValueError("VALIDATION and TEST must each contain exactly 4 donors")
    if not all(_common_donor_pass(d) for d in test_donors):
        return False
    med_v=float(np.median([d["delta_r2"] for d in validation_donors]))
    med_t=float(np.median([d["delta_r2"] for d in test_donors]))
    return bool(med_t >= DELTA_MARGIN and med_t >= TEST_REPLICATION_FRACTION*med_v)


def test_confirmed(selected_rank, validation_aggregate_by_rank, test_aggregate_by_rank,
                   validation_shell_by_rank, test_shell_by_rank):
    """Confirm locked rank: selected aggregate plus every shell through that rank."""
    if selected_rank not in RANKS:
        return False
    if not _test_metric_set_confirmed(
            validation_aggregate_by_rank[selected_rank],
            test_aggregate_by_rank[selected_rank]):
        return False
    for k in RANKS:
        if k>selected_rank:
            break
        if not _test_metric_set_confirmed(
                validation_shell_by_rank[k],test_shell_by_rank[k]):
            return False
    return True


def classify(selected_rank, validation_aggregate_by_rank=None, test_aggregate_by_rank=None,
             validation_shell_by_rank=None, test_shell_by_rank=None):
    if selected_rank==0:
        return "UNQUALIFIED"
    if any(x is None for x in (
            validation_aggregate_by_rank,test_aggregate_by_rank,
            validation_shell_by_rank,test_shell_by_rank)):
        return "LOCKED_PENDING_TEST"
    if not test_confirmed(
            selected_rank,validation_aggregate_by_rank,test_aggregate_by_rank,
            validation_shell_by_rank,test_shell_by_rank):
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

    # Aggregate metrics deliberately look good at all ranks in the partial fixture.
    # The shell at rank 8 fails, proving lower-rank signal cannot carry higher rank.
    partial_agg={2:good2,4:good4,8:good4,16:good4}
    partial_shell={2:good2,4:good4,8:failgeom,16:failgeom}

    full_agg={2:good2,4:good4,8:good4,16:good4}
    full_shell={2:good2,4:good4,8:good4,16:good4}

    lower_fail_agg={2:good2,4:good4,8:good4,16:good4}
    lower_fail_shell={2:failgeom,4:good4,8:good4,16:good4}

    shortcut=_four(
        donor(.91,.905,.20), donor(.93,.925,.21), donor(.92,.915,.20), donor(.94,.935,.22)
    )
    shortcut_agg={k:shortcut for k in RANKS}
    shortcut_shell={k:shortcut for k in RANKS}

    weak=_four(
        donor(.20,.10,.17), donor(.21,.10,.18), donor(.19,.10,.17), donor(.20,.10,.18)
    )
    weak_agg={k:weak for k in RANKS}
    weak_shell={k:weak for k in RANKS}

    spectacular=_four(
        donor(.95,.05,.10), donor(.94,.05,.10), donor(.96,.05,.10), donor(.95,.05,.10)
    )
    spectacular_agg={k:spectacular for k in RANKS}
    spectacular_shell={k:spectacular for k in RANKS}

    return dict(
        partial=(partial_agg,partial_shell),
        full=(full_agg,full_shell),
        lower_fail=(lower_fail_agg,lower_fail_shell),
        shortcuts=(shortcut_agg,shortcut_shell),
        weak=(weak_agg,weak_shell),
        spectacular=(spectacular_agg,spectacular_shell),
    )


def run_smoke():
    sc=synthetic_scenarios()
    pA,pS=sc["partial"]
    fA,fS=sc["full"]
    lA,lS=sc["lower_fail"]
    sA,sS=sc["shortcuts"]
    wA,wS=sc["weak"]
    xA,xS=sc["spectacular"]

    r_partial=select_validation_rank(pA,pS)
    r_full=select_validation_rank(fA,fS)
    r_lower_fail=select_validation_rank(lA,lS)
    r_short=select_validation_rank(sA,sS)
    r_weak=select_validation_rank(wA,wS)

    # TEST confirmation fixture for selected partial rank.
    test_good=_four(
        donor(.36,.07,.16), donor(.35,.07,.15), donor(.34,.08,.15), donor(.37,.08,.16)
    )
    tA={k:test_good for k in RANKS}
    tS={k:test_good for k in RANKS}
    partial_class=classify(r_partial,pA,tA,pS,tS)

    # Explicit projector fixture: rank-2 shared target embedded in 4-D privileged state.
    rng=np.random.default_rng(6501)
    x=rng.normal(size=(1200,6))
    w=rng.normal(size=(6,2))
    shared=x@w
    private=rng.normal(size=(1200,2))
    z=np.column_stack([shared,private])
    zhat=np.column_stack([shared+0.02*rng.normal(size=shared.shape), np.zeros_like(private)])
    proj=target_projector(z,zhat,2)

    eye=np.eye(4)
    tie=target_projector(eye,eye,2,tie_tol=1e-12)

    out={
        "schema":"V65_PRIVILEGED_RECOVERABILITY_DECISION_ENGINE_SMOKE_V2",
        "status":"SYNTHETIC_SOFTWARE_QUALIFICATION_ONLY",
        "results":{
            "partial_contiguous_selected_rank":r_partial,
            "partial_classification":partial_class,
            "full_rank_selected":r_full,
            "lower_shell_failure_blocks_higher_ranks":r_lower_fail,
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
