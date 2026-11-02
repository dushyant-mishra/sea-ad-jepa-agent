"""Independent A4 review of Macha #504 exact head b66c23e589249360.

No production source changes. Tests whole refusal objects, nested rights,
large lawful integer boundaries, positive-depth noninterference, and limits
outside the producer's declared exact integer domain. Fixture only.
"""
from copy import deepcopy
import json
import random

import pytest

from scripts.v5.td_unified import q_excluded_depth_v1 as Q

MS="MEASURED_SCALAR"
MCU="MEASURED_COLLISION_UNRESOLVED"
SU="STRUCTURALLY_UNMEASURED"


def make(base=0,ext=0,q=0,residual=0,*,base_state=MS,
         collision_outside=False):
    st={"B":base_state,"E":MCU if collision_outside else MS,"Q":MS,
        "Z":SU}
    counts={}
    if base_state==MS and base:counts["B"]=base
    if ext and not collision_outside:counts["E"]=ext
    if q:counts["Q"]=q
    return {
        "cells":[{"cell_id":"C","donor_id":"D","source_id":"S",
                  "operator_id":"O","library_total":base+ext+q+residual,
                  "counts":counts}],
        "address_rights":{"B":"BASE","E":"EXT","Q":"QUERY","Z":"QUERY"},
        "operator_states":{"O":st},
        "ladder":[
            {"level_id":"L0","evidence_rights":["BASE"]},
            {"level_id":"L1","evidence_rights":["BASE","EXT"]},
            {"level_id":"L2","evidence_rights":["BASE","EXT","QUERY"]},
        ],
    }


def outcome(w,level="L0"):
    try:
        v=Q.produce_rights_ladder_observations(**deepcopy(w))
    except Q.QExcludedObservationError as ex:
        return ("REFUSE",type(ex).__module__,type(ex).__name__,
                ex.args,ex.__cause__ is None,tuple(sorted(ex.__dict__.items())))
    lids=[z["level_id"] for z in v["levels"]]
    return ("VIEW",json.dumps({**v,"levels":v["levels"][:lids.index(level)+1]},
                              sort_keys=True,ensure_ascii=False))


@pytest.mark.parametrize("base_state",[MS,SU,MCU])
@pytest.mark.parametrize("residual",[0])
def test_zero_base_full_refusal_object_constant_at_arbitrary_exact_query_depth(base_state,residual):
    qs=(0,1,3,100,2**20,2**53-1)
    values=[outcome(make(q=q,base_state=base_state,residual=residual)) for q in qs]
    assert len(set(values))==1,values
    assert values[0][:3]==("REFUSE",Q.QExcludedDepthNotEstimable.__module__,
                          "QExcludedDepthNotEstimable")


def test_exact_numeric_domain_is_an_explicit_noninterference_boundary():
    okay=outcome(make(q=2**53-1))
    outside=outcome(make(q=2**53))
    assert okay[0]=="REFUSE" and okay[2]=="QExcludedDepthNotEstimable"
    assert outside[0]=="REFUSE" and outside[2]=="QExcludedObservationError"
    # This is a declared-domain limitation, not a proof of real q privacy.


def test_positive_base_is_identical_for_all_lawfully_hidden_query_values():
    for base in (1,3,23):
        for ext in (0,2):
            outputs=[outcome(make(base=base,ext=ext,q=q)) for q in (0,1,100,10000)]
            assert len(set(outputs))==1
            assert outputs[0][0]=="VIEW"
            visible=[outcome(make(base=base,ext=ext,q=q),level="L2")
                     for q in (0,1,100,10000)]
            assert len(set(visible))==4


def test_pooled_denominator_residual_equal_in_both_worlds_stays_fixed():
    for residual in (1,3,17):
        samples=[outcome(make(base=0,q=q,residual=residual)) for q in (0,1,17,200)]
        assert len(set(samples))==1
        assert samples[0][0]=="VIEW"  # original producer permits off-ledger residual
    # This positive acceptance is a SOURCE-PROVENANCE limitation: the
    # fixture cannot establish whether the residual hides a q alias.


def test_outside_base_collision_refusal_does_not_reveal_query_mass():
    vals=[outcome(make(base=0,q=q,collision_outside=True)) for q in (0,1,99,10000)]
    assert len(set(vals))==1
    assert vals[0][0]=="REFUSE"


def test_two_cell_order_and_second_cell_error_do_not_create_a4_leak():
    for order in (False,True):
        seen=[]
        for q in (0,1,5,100):
            w=make(base=0,q=q)
            good=make(base=4,ext=7,q=11)["cells"][0]
            good["cell_id"]="C2"
            w["cells"]=([good,*w["cells"]] if order else [*w["cells"],good])
            seen.append(outcome(w))
        assert len(set(seen))==1


def test_random_hidden_count_counterfactuals_across_all_restricted_levels():
    rng=random.Random(504125)
    for _ in range(500):
        base=rng.randint(1,50)
        ext=rng.randint(0,50)
        q1,q2=rng.randint(0,1000),rng.randint(0,1000)
        a=make(base=base,ext=ext,q=q1)
        b=make(base=base,ext=ext,q=q2)
        assert outcome(a,"L0")==outcome(b,"L0")
        assert outcome(a,"L1")==outcome(b,"L1")


def test_raw_source_coverage_mismatch_still_domain_refused():
    w=make(base=3,q=100)
    w["cells"][0]["library_total"]=2
    val=outcome(w)
    assert val[:3]==("REFUSE",Q.QExcludedObservationError.__module__,
                     "QExcludedObservationError")
