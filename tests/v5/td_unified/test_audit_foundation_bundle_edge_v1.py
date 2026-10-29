"""Contract hostiles for read-only August archive auditor; no private archive in CI."""
from copy import deepcopy
import math

import pytest

from scripts.v5.td_unified import audit_foundation_bundle_edge_v1 as A


def source():
    support=[
        {"matrix_id":"M","molecular_address_id":"B","measured_address":"True"},
        {"matrix_id":"M","molecular_address_id":"C","measured_address":"True"},
        {"matrix_id":"M","molecular_address_id":"U","measured_address":"True"},
        {"matrix_id":"M","molecular_address_id":"N","measured_address":"False"},
    ]
    ledger=[{
        "matrix_id":"M","molecular_address_id":"C",
        "scalar_materialization_status":"MEASURED_COLLISION_UNRESOLVED",
    },{
        "matrix_id":"M","molecular_address_id":"C",
        "scalar_materialization_status":"MEASURED_COLLISION_UNRESOLVED",
    }]
    supplement=[{
        "matrix_id":"M","molecular_address_id":"U",
        "unregistered_source_rows":"2",
    }]
    return support,ledger,supplement


def test_union_overrides_measured_status_and_does_not_promote():
    s,l,u=source()
    result=A.summarize_collision_contract(s,l,u,address_count=4,operator_count=1)
    assert result["registered_collision_pairs"]==1
    assert result["supplemental_collision_pairs"]==1
    assert result["registered_collision_source_rows"]==2
    assert result["combined_collision_pairs"]==2
    assert result["all_supplemental_pairs_finally_unresolved"] is True
    assert result["final_state_counts"]=={
        "MEASURED_SCALAR":1,"MEASURED_COLLISION_UNRESOLVED":2,
        "STRUCTURALLY_UNMEASURED":1,
    }
    assert result["source_feature_alias_closure_authenticated"] is False


@pytest.mark.parametrize("fault",[
    "duplicate_support","missing_support","missing_operator",
    "collision_state_wrong","supplement_unmeasured",
    "supplement_below_two","supplement_duplicate","ledger_overlap",
    "noncanonical_measured",
])
def test_fail_closed_contract_corruptions(fault):
    s,l,u=deepcopy(source())
    if fault=="duplicate_support":s.append(deepcopy(s[0]))
    elif fault=="missing_support":s.pop()
    elif fault=="missing_operator":pass
    elif fault=="collision_state_wrong":l[0]["scalar_materialization_status"]="MEASURED_SCALAR"
    elif fault=="supplement_unmeasured":s[2]["measured_address"]="False"
    elif fault=="supplement_below_two":u[0]["unregistered_source_rows"]="1"
    elif fault=="supplement_duplicate":u.append(deepcopy(u[0]))
    elif fault=="ledger_overlap":u[0]["molecular_address_id"]="C"
    elif fault=="noncanonical_measured":s[0]["measured_address"]=True
    with pytest.raises(ValueError):
        A.summarize_collision_contract(
            s,l,u,address_count=4,
            operator_count=2 if fault=="missing_operator" else 1,
        )


def test_missing_supplement_is_undetectable_from_remaining_records():
    # Positive limitation: without an independent source-feature census, a
    # missing supplemental collision is mistakenly scalar-mappable.
    s,l,_=source()
    result=A.summarize_collision_contract(s,l,[],address_count=4,operator_count=1)
    assert result["final_state_counts"]["MEASURED_SCALAR"]==2
    assert result["combined_collision_pairs"]==1
    assert result["source_feature_alias_closure_authenticated"] is False


def test_conditional_full_source_denominator_leaks_query_to_fixed_base():
    w=A.source_library_counterfactual(3,7,100)
    assert w["base_value_changed_due_to_denominator"] is True
    assert w["log1p_cp10k_base_low"] == pytest.approx(math.log1p(3000))
    assert w["log1p_cp10k_base_high"] == pytest.approx(math.log1p(30000/103))
    # This is an analytic demonstration, not data about a real cell.


@pytest.mark.parametrize("bad",[False,1.5,-1])
def test_synthetic_witness_refuses_malformed_counts(bad):
    with pytest.raises(ValueError):
        A.source_library_counterfactual(base_count=bad)


def test_frozen_index_address_identity_detects_hidden_namespace_substitution():
    s,l,u=deepcopy(source())
    frozen={i:row["molecular_address_id"] for i,row in enumerate(s)}
    for i,row in enumerate(s):
        row["molecular_address_index"]=str(i)
    result=A.summarize_collision_contract(
        s,l,u,address_count=4,operator_count=1,expected_index_to_id=frozen)
    assert result["combined_collision_pairs"]==2
    bad=deepcopy(s)
    # Maintain row count, distinct IDs and digest-free plausible shape.
    bad[0]["molecular_address_index"]="1"
    with pytest.raises(ValueError,match="index disagrees"):
        A.summarize_collision_contract(
            bad,l,u,address_count=4,operator_count=1,expected_index_to_id=frozen)
    bad=deepcopy(s)
    bad[0]["molecular_address_index"]="00"
    with pytest.raises(ValueError,match="index disagrees"):
        A.summarize_collision_contract(
            bad,l,u,address_count=4,operator_count=1,expected_index_to_id=frozen)
