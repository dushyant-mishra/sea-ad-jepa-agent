"""Independent-of-physical-total D1 source-edge mechanics; no real authority.

Synthetic only. Specifically demonstrates that new path does not need hidden
count, collision residual or library_total, while old V2 does.
"""
import inspect
from copy import deepcopy

import pytest

from scripts.v5.td_unified import observation_d1_base_only_student_fixture_v1 as P
from scripts.v5.td_unified import observation_v2b_public_student_gate_v1 as S
from scripts.v5.td_unified import observation_normalization_view_v2_fixture as OLD
from scripts.v5.td_unified import observation_normalization_view_v2_bound_content_v1 as B
from scripts.v5.td_unified.q_excluded_depth_v1 import (
    QExcludedObservationError, QExcludedDepthNotEstimable,
)

MS="MEASURED_SCALAR"
SU="STRUCTURALLY_UNMEASURED"
MCU="MEASURED_COLLISION_UNRESOLVED"
WITHHELD="WITHHELD_BY_EVIDENCE_RIGHTS"


def w():
    roster=[{"cell_id":f"D1_ROSTER_{i}","donor_id":f"D{i}",
             "source_id":"SYNTHETIC_SRC","operator_id":"O"} for i in range(2)]
    rights={"B":"RNA:BASE","B2":"RNA:BASE","E":"RNA:EXT",
            "Q":"RNA:QUERY","U":"RNA:EXT","V":"RNA:QUERY"}
    return {
        "query_address_id":"Q",
        "base_evidence_rights":["RNA:BASE"],
        "address_rights":rights,
        "operator_states":{"O":{"B":MS,"B2":MS,"E":MS,"Q":MS,"U":MCU,"V":SU}},
        "cell_roster":roster,
    }


def base():
    return [{"cell_id":f"D1_ROSTER_{i}","base_counts":{"B":3+i,"B2":2}}
            for i in range(2)]


def produce(p=None,o=None):
    return P.produce_d1_base_only_student_fixture(
        expected_policy=w() if p is None else p,
        base_observations=base() if o is None else o)


def test_no_total_teacher_query_or_residual_inputs_exist_and_public_v2b_validates():
    allowed=set(inspect.signature(P.produce_d1_base_only_student_fixture).parameters)
    assert allowed=={"expected_policy","base_observations"}
    v=produce()
    assert v["schema"]==B._SCHEMA and v["view_kind"]=="STUDENT_BASE_RIGHTS"
    assert S.validate_public_student_v2b(
        student_view=v,expected_policy=w())["status"]==S.RESULT_STATUS
    assert v["real_training_authorized"] is False
    assert v["source_authenticated"] is False
    assert "library_total" not in repr(v) and "library_size" not in repr(v)
    assert all(k not in v for k in ("teacher_view","teacher_digest","teacher_sha256"))
    assert len(v["rows"])==12
    for cid,d in [("D1_ROSTER_0",5),("D1_ROSTER_1",6)]:
        rows={r["address_id"]:r for r in v["rows"] if r["cell_id"]==cid}
        assert (rows["B"]["state"],rows["B"]["base_rights_normalization_depth"])==(MS,d)
        assert (rows["Q"]["state"],rows["Q"]["count"],rows["Q"]["base_rights_normalization_depth"])==(WITHHELD,None,None)
        assert (rows["E"]["state"],rows["E"]["count"])==(WITHHELD,None)
        assert (rows["U"]["state"],rows["U"]["count"])==(MCU,None)
        assert (rows["V"]["state"],rows["V"]["count"])==(SU,None)


@pytest.mark.parametrize("q",[0,1,5,7,23,100,2**20])
@pytest.mark.parametrize("offledger_residual",[0,1,19,99999])
@pytest.mark.parametrize("collision_residual",[0,2,70])
def test_student_view_is_constant_across_hidden_query_and_all_residual_mass(
        q,offledger_residual,collision_residual):
    # All three are intentionally absent from input; changing their *real*
    # quantities cannot change this function's output. This does NOT certify
    # the external filter selected a q-independent roster.
    synthetic_world={
        "cells":[{
            "cell_id":f"D1_ROSTER_{i}",
            "physical_total":3+i+2+4+q+offledger_residual+collision_residual,
            "all_source_counts":{"B":3+i,"B2":2,"E":4,"Q":q},
            "unmapped_source_residual":offledger_residual,
            "unresolved_collision_residual":collision_residual,
        } for i in range(2)],
    }
    # This explicit helper models an upstream redactor but is NOT the
    # authenticated upstream source producer or depositor's QC selection.
    redacted=[
        {"cell_id":cell["cell_id"],
         "base_counts":{a:n for a,n in cell["all_source_counts"].items()
                        if w()["address_rights"][a] in w()["base_evidence_rights"]}}
        for cell in synthetic_world["cells"]
    ]
    assert redacted==base()
    view=produce(o=redacted)
    assert view==produce()
    assert all("physical_total" not in str(row) for row in view["rows"])


def test_old_v2_rejects_nonzero_residual_new_base_only_path_accepts():
    old_world={
        "cells":[{"cell_id":"D1_ROSTER_0","donor_id":"D0",
                  "source_id":"SYNTHETIC_SRC","operator_id":"O",
                  "library_total":3+2+7+4+33,
                  "counts":{"B":3,"B2":2,"E":4,"Q":7}}],
        "address_rights":w()["address_rights"],
        "operator_states":w()["operator_states"],
        "ladder":[{"level_id":"L0","evidence_rights":["RNA:BASE"]},
                  {"level_id":"L1","evidence_rights":["RNA:BASE","RNA:EXT","RNA:QUERY"]}],
        "query_address_id":"Q",
    }
    # Make the collision address structurally absent in THIS old-path probe,
    # so the observed refusal is specifically the conservation requirement.
    old_world["operator_states"]["O"]["U"]=SU
    with pytest.raises(QExcludedDepthNotEstimable,match="unmapped or unresolved"):
        OLD.produce_fixture_student_view_v2(**old_world)
    # No unsafe 'physical total equals mapped' exception in the new D1.
    assert produce()["authority_effect"]=="NONE"


def test_base_only_noninterference_tamper_positive_controls():
    original=produce()
    o=base()
    o[0]["base_counts"]["B"]=4
    assert produce(o=o)!=original
    p=w()
    p["query_address_id"]="E"
    assert produce(p=p)!=original


@pytest.mark.parametrize("fault",[
    "query_promoted","nonbase_scalar","unknown_count_address",
    "collision_scalar","structural_scalar","duplicate_source_cell",
    "missing_source_cell","unknown_source_cell","missing_roster",
    "extra_count_bool","negative_count","float_count","depth_zero",
    "unknown_operator","missing_operator_state","missing_address_state",
    "malformed_right","malformed_q",
])
def test_exact_fail_closed_input_corruptions(fault):
    p,o=w(),base()
    if fault=="query_promoted":
        p["address_rights"]["Q"]="RNA:BASE"
    elif fault=="nonbase_scalar":
        o[0]["base_counts"]["Q"]=7
    elif fault=="unknown_count_address":
        o[0]["base_counts"]["OFFLEDGER"]=8
    elif fault=="collision_scalar":
        o[0]["base_counts"]["U"]=5
        p["address_rights"]["U"]="RNA:BASE"
    elif fault=="structural_scalar":
        o[0]["base_counts"]["V"]=5
        p["address_rights"]["V"]="RNA:BASE"
    elif fault=="duplicate_source_cell":
        o.append(deepcopy(o[0]))
    elif fault=="missing_source_cell":
        o.pop()
    elif fault=="unknown_source_cell":
        o[0]["cell_id"]="WRONG"
    elif fault=="missing_roster":
        p["cell_roster"].pop()
    elif fault=="extra_count_bool":
        o[0]["base_counts"]["B"]=True
    elif fault=="negative_count":
        o[0]["base_counts"]["B"]=-1
    elif fault=="float_count":
        o[0]["base_counts"]["B"]=1.5
    elif fault=="depth_zero":
        for item in o:item["base_counts"]={}
    elif fault=="unknown_operator":
        p["cell_roster"][0]["operator_id"]="WRONG"
    elif fault=="missing_operator_state":
        p["operator_states"]={}
    elif fault=="missing_address_state":
        del p["operator_states"]["O"]["Q"]
    elif fault=="malformed_right":
        p["address_rights"]["Q"]=" "
    elif fault=="malformed_q":
        p["query_address_id"]="Q "
    with pytest.raises(QExcludedObservationError):
        produce(p=p,o=o)


def test_sum_preserving_swap_still_accepted_and_untrusted_as_source_content():
    # Proves the source integrity boundary remains unresolved. The self-supplied
    # rights policy and derived D1 do not bind exact deposited count values.
    o=base()
    o[0]["base_counts"]={"B":1,"B2":4}  # same D1=5, different content
    modified=produce(o=o)
    original=produce()
    assert modified!=original
    assert S.validate_public_student_v2b(
        student_view=modified,expected_policy=w())["source_rights_issuer_authenticated"] is False


def test_forbidden_extra_source_total_argument_cannot_enter_producer():
    with pytest.raises(TypeError):
        P.produce_d1_base_only_student_fixture(
            expected_policy=w(),base_observations=base(),
            library_total=7)


def test_hostile_metaclass_is_rejected_before_any_execution():
    class Meta(type):
        called=0
        def __eq__(cls,other):
            Meta.called+=1
            raise RuntimeError("executed payload")
        __hash__=type.__hash__
    class Bomb(metaclass=Meta):pass
    o=base()
    o[0]["base_counts"]["B"]=Bomb()
    with pytest.raises(QExcludedObservationError):
        produce(o=o)
    assert Meta.called==0


def test_zero_base_refusal_is_identical_in_all_absent_hidden_worlds():
    o=base()
    for item in o:item["base_counts"]={}
    outputs=[]
    for hidden in (0,1,5,100,9999):
        # hidden cannot appear in inputs. Full observable refusal is fixed.
        assert hidden>=0
        with pytest.raises(QExcludedDepthNotEstimable) as ex:
            produce(o=o)
        outputs.append((type(ex.value),ex.value.args,ex.value.__cause__))
    assert len(set(outputs))==1
