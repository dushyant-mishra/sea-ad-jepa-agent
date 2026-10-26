"""RED-first unified Task5 fixture handoff tests. No sealed challenges or human access."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import pytest

from scripts.v5.td_unified.casebundle_v1 import (
    CaseBundleError, validate_casebundle, validate_truth_separation,
    freeze_fixture_td_output,
)
from scripts.v5.td_unified.mode_equivalence_v1 import (
    PathEquivalenceError, FixtureStage, trace_scientific_path,
    certify_mode_path_equivalence, SCIENTIFIC_ROLES
)

H=lambda b: hashlib.sha256(b).hexdigest()
SHA=H(b"fixture-authentication-is-not-identity")
def case():
    return {
        "schema":"KNOWN_TRUTH_CASEBUNDLE_V1",
        "case_id":"SYNTHETIC_FIXTURE_CELLPAIR",
        "authority_scope":"FIXTURE_ONLY",
        "manifest_sha256":H(b"fixture-manifest"),
        "population_access_policy_sha256":H(b"fixture-population"),
        "address_universe_sha256":H(b"fixture-41238-id"),
        "reader_partition":"reader_fit",
        "observations":[
            {"cell_id":"CELL-1","donor_id":"DONOR-A","source_id":"SRC-A",
             "operator_id":"OP-1","address_id":"ADDR-1","state":"MEASURED_SCALAR",
             "count":0,"library_size":44,"evidence_right":"RNA:CORE"},
            {"cell_id":"CELL-1","donor_id":"DONOR-A","source_id":"SRC-A",
             "operator_id":"OP-1","address_id":"ADDR-2","state":"STRUCTURALLY_UNMEASURED",
             "count":None,"library_size":None,"evidence_right":"RNA:CORE"},
            {"cell_id":"CELL-1","donor_id":"DONOR-A","source_id":"SRC-A",
             "operator_id":"OP-1","address_id":"ADDR-3","state":"MEASURED_COLLISION_UNRESOLVED",
             "count":None,"library_size":None,"evidence_right":"RNA:EXTENDED"},
            {"cell_id":"CELL-2","donor_id":"DONOR-B","source_id":"SRC-B",
             "operator_id":"OP-2","address_id":"ADDR-1","state":"WITHHELD_BY_EVIDENCE_RIGHTS",
             "count":None,"library_size":None,"evidence_right":"RNA:CORE"},
        ]
    }

def truth():
    return {"schema":"TRUTH_BUNDLE_V1","case_id":"SYNTHETIC_FIXTURE_CELLPAIR",
            "authority_scope":"CONTROLLER_FIXTURE_ONLY",
            "expected_outcome":"PLANTED_FIXTURE_ONLY",
            "latent_truth":{"CELL-1":"LATENT-DUMMY"}}

def _step(label):
    def fn(obj):
        # Only deterministic fixture operations; no secret/truth input.
        return {"stage":label,"input_hash":H(repr(obj).encode())}
    return fn

def stages():
    return tuple(FixtureStage(role=role, handler=_step(role)) for role in SCIENTIFIC_ROLES)

def test_casebundle_measured_zero_and_four_states_are_preserved():
    v=validate_casebundle(case())
    assert v["status"]=="CASEBUNDLE_FIXTURE_VALIDATED_NO_AUTHORITY"
    assert v["observations"][0]["count"]==0
    assert [r["state"] for r in v["observations"]]==[
        "MEASURED_SCALAR","STRUCTURALLY_UNMEASURED",
        "MEASURED_COLLISION_UNRESOLVED","WITHHELD_BY_EVIDENCE_RIGHTS"]
    assert v["authority_effect"]=="NONE"
    assert v["same_code_path_authorized"] is False

@pytest.mark.parametrize("field",["expected_outcome","target_truth","verdict",
    "controller_nonce","planted_mechanisms","truth_bundle","latent_truth"])
def test_truth_field_cannot_be_smuggled_into_observable_tree(field):
    c=case()
    c["observations"][0][field]="SECRET"
    with pytest.raises(CaseBundleError):validate_casebundle(c)
    c=case()
    c[field]={"payload":field}
    with pytest.raises(CaseBundleError):validate_casebundle(c)

@pytest.mark.parametrize("mutation",["count_negative","zero_as_absent","structural_as_zero",
    "withheld_with_value","library_lt_count","duplicate_atom","wrong_partition"])
def test_invalid_observation_or_partition_fails_closed(mutation):
    c=case()
    a=c["observations"]
    if mutation=="count_negative": a[0]["count"]=-1
    if mutation=="zero_as_absent": a[0].update(state="STRUCTURALLY_UNMEASURED",count=0)
    if mutation=="structural_as_zero": a[1].update(state="MEASURED_SCALAR",count=0,library_size=0)
    if mutation=="withheld_with_value": a[3]["count"]=0
    if mutation=="library_lt_count": a[0].update(count=45,library_size=44)
    if mutation=="duplicate_atom": a.append(deepcopy(a[0]))
    if mutation=="wrong_partition": c["reader_partition"]="reader_oracle"
    with pytest.raises(CaseBundleError):validate_casebundle(c)

def test_truth_is_separate_and_not_consulted_before_output_freeze():
    c=case(); t=truth()
    with pytest.raises(CaseBundleError):
        validate_truth_separation(c,t,td_output_frozen=False)
    completed=freeze_fixture_td_output({"status":"NOT_ESTIMABLE","outcome":None})
    receipt=validate_truth_separation(c,t,td_output_frozen=completed)
    assert receipt["status"]=="EXTERNAL_FIXTURE_TRUTH_SEPARATED_NO_AUTHORITY"
    assert "latent_truth" not in str(receipt)
    assert "expected_outcome" not in str(receipt)
    assert receipt["authority_effect"]=="NONE"

def test_case_payload_is_immutable_snapshot_and_cannot_change_by_mutation():
    c=case()
    original=validate_casebundle(c)
    c["observations"][0]["count"]=13
    assert original["observations"][0]["count"]==0

def test_same_observable_and_same_scientific_functions_have_identical_traces():
    c=case()
    left=trace_scientific_path(mode="KNOWN_TRUTH",case_payload=c,stages=stages())
    right=trace_scientific_path(mode="HUMAN_SEALED",case_payload=c,stages=stages())
    certificate=certify_mode_path_equivalence(left,right)
    assert certificate["status"]=="MODE_PATH_EQUIVALENCE_FIXTURE_ONLY_NO_AUTHORITY"
    assert certificate["authority_effect"]=="NONE"
    assert certificate["same_code_path_authorized"] is False
    assert left["scientific_trace_sha256"]==right["scientific_trace_sha256"]
    assert left["scientific_output_sha256"]==right["scientific_output_sha256"]

def test_different_scientific_metric_stage_is_rejected():
    c=case()
    base=trace_scientific_path(mode="KNOWN_TRUTH",case_payload=c,stages=stages())
    changed=list(stages())
    changed[-2]=FixtureStage(role=SCIENTIFIC_ROLES[-2],handler=lambda obj:{"fake":99})
    other=trace_scientific_path(mode="HUMAN_SEALED",case_payload=c,stages=tuple(changed))
    with pytest.raises(PathEquivalenceError):
        certify_mode_path_equivalence(base,other)

def test_changed_operator_observations_cannot_certify_same_execution():
    a=trace_scientific_path(mode="KNOWN_TRUTH",case_payload=case(),stages=stages())
    c=case()
    c["observations"][0]["library_size"]=37
    b=trace_scientific_path(mode="HUMAN_SEALED",case_payload=c,stages=stages())
    with pytest.raises(PathEquivalenceError):
        certify_mode_path_equivalence(a,b)

def test_wrong_stage_roster_and_truth_entrypoint_rejected():
    c=case(); stage=stages()
    with pytest.raises(PathEquivalenceError):
        trace_scientific_path(mode="KNOWN_TRUTH",case_payload=c,stages=stage[:-1])
    with pytest.raises(PathEquivalenceError):
        trace_scientific_path(mode="KNOWN_TRUTH",case_payload=c,stages=stage[:-1] +
        (FixtureStage(role=SCIENTIFIC_ROLES[-1],handler=lambda obj:{"truth":1}),))

def test_mode_cannot_be_implicit_scientific_input():
    with pytest.raises(PathEquivalenceError):
        trace_scientific_path(mode="CANONICAL_TRUTH_ORACLE",case_payload=case(),stages=stages())

def test_fixture_receipt_cannot_assert_promoted_authority():
    a=trace_scientific_path(mode="KNOWN_TRUTH",case_payload=case(),stages=stages())
    b=trace_scientific_path(mode="HUMAN_SEALED",case_payload=case(),stages=stages())
    r=certify_mode_path_equivalence(a,b)
    assert r["known_truth_qualified"] is False
    assert r["real_reference_ready"] is False
    assert r["training_authorized"] is False

def test_one_cell_cannot_change_donor_source_or_operator_between_addresses():
    for field,new_value in [
        ("donor_id","DONOR-IMPOSTOR"),("source_id","SRC-OTHER"),
        ("operator_id","OP-OTHER")
    ]:
        c=case()
        c["observations"][1][field]=new_value
        with pytest.raises(CaseBundleError):
            validate_casebundle(c)

def test_sum_of_measured_gene_counts_must_fit_physical_library():
    c=case()
    c["observations"].append({
        "cell_id":"CELL-1","donor_id":"DONOR-A","source_id":"SRC-A",
        "operator_id":"OP-1","address_id":"ADDR-4","state":"MEASURED_SCALAR",
        "count":40,"library_size":44,"evidence_right":"RNA:CORE"})
    c["observations"][0]["count"]=9
    with pytest.raises(CaseBundleError):
        validate_casebundle(c)

def test_cannot_forge_fixture_same_code_path_receipt_via_trace_digest_change():
    c=case()
    first=trace_scientific_path(mode="KNOWN_TRUTH",case_payload=c,stages=stages())
    second=trace_scientific_path(mode="HUMAN_SEALED",case_payload=c,stages=stages())
    second["scientific_trace"][0]["code_identity"]="f"*64
    with pytest.raises(PathEquivalenceError):
        certify_mode_path_equivalence(first,second)
