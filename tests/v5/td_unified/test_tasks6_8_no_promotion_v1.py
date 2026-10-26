"""RED-first Task6-8 no-promotion interfaces on frozen accepted Task3."""
from __future__ import annotations
from copy import deepcopy
import pytest

from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from scripts.v5.td_unified.gate_registration_v1 import (
    GateRegistrationError, current_repaired_unit_descriptors, register_initial_repaired_units,
)
from scripts.v5.td_unified.target_bundle_v1 import (
    TargetBundleError, issue_target_none_fixture, verify_target_none_fixture,
    issue_selected_target_bundle,
)
from scripts.v5.td_unified.downstream_contract_v1 import (
    DownstreamContractError, certify_downstream_abstention,
)

def fixture():
    inputs={
      "manifest":{"object_role":"FIXTURE_MANIFEST","reader_partition":"reader_fit"},
      "registry":{"object_role":"FIXTURE_REGISTRY","status":"NO_QUALIFIED_TARGETS"},
      "controller":{"object_role":"FIXTURE_CONTROLLER","status":"NO_DECISION_PROMOTION"},
      "falsifier":{"object_role":"FIXTURE_FALSIFIER","failed_or_unresolved":["G6","G7","G8","R1"]},
    }
    keys={k:canonical_sha256(v) for k,v in inputs.items()}
    resolver={canonical_sha256(v):v for v in inputs.values()}
    bundle=issue_target_none_fixture(manifest_sha256=keys["manifest"],
        registry_sha256=keys["registry"],controller_sha256=keys["controller"],
        falsifier_sha256=keys["falsifier"],resolver=resolver.get)
    return inputs,keys,resolver,bundle

def test_t6_descriptor_roster_matches_plan_and_has_no_promoted_stage():
    units=current_repaired_unit_descriptors()
    assert len(units)==9
    assert {x["unit_id"] for x in units}=={
      "G8","G6","G9_S1_S2","R1","G2","G7","R4_C6_C4","G12","TD_SYSTEM_BATTERY_V3"}
    for unit in units:
        assert unit["max_unreviewed_stage"]=="FIXTURE_SAME_INTERFACE"
        assert unit["effective_stage"]=="SEMANTICS_ONLY"
        assert unit["externally_authenticated"] is False
        assert unit["required_missing_evidence"]
        assert unit["authority_effect"]=="NONE"

def test_t6_exact_head_identity_and_no_system_battery_promotion():
    units={x["unit_id"]:x for x in current_repaired_unit_descriptors()}
    assert units["G7"]["navigation_commit_sha"]=="5a711f9a4ea0328445a05dadc1e011efb16a3c13"
    assert "NO_INHERITED_GATE_PASS" in units["TD_SYSTEM_BATTERY_V3"]["restrictions"]
    proposal=register_initial_repaired_units()
    assert proposal["status"]=="REGISTRATION_BLOCKED_PENDING_AUTHENTICATED_UNIT_IDENTITIES"
    assert proposal["registry_mutated"] is False
    assert proposal["registered_qualification_units"]==[]
    assert proposal["authority_effect"]=="NONE"

@pytest.mark.parametrize("malicious",[
    {"unit_id":"G7","stage":"KNOWN_TRUTH_QUALIFIED"},
    {"unit_id":"G7","status":"PASS"},
    {"unit_id":"G7","code_sha":"f"*40},
])
def test_t6_caller_provided_promotion_cannot_register(malicious):
    with pytest.raises(GateRegistrationError):
        register_initial_repaired_units(caller_promotions=[malicious])

def test_t7_none_first_class_binds_all_inputs_and_is_not_scientific_pass():
    _,keys,resolver,bundle=fixture()
    assert bundle["target_selection"]=="NONE"
    assert bundle["schema"]=="TARGET_QUALIFICATION_BUNDLE_V1"
    assert bundle["scope"]=="DEVELOPMENT_FIXTURE_ONLY"
    assert bundle["manifest_sha256"]==keys["manifest"]
    assert bundle["negative_evidence_sha256"]==keys["falsifier"]
    assert bundle["training_authorized"] is False
    assert bundle["qualification_stage"]=="SEMANTICS_ONLY"
    assert bundle["target_bundle_sha256"]!=keys["registry"]
    assert verify_target_none_fixture(bundle,resolver.get)==bundle

@pytest.mark.parametrize("field",["manifest_sha256","registry_sha256","controller_sha256","negative_evidence_sha256"])
def test_t7_target_none_requires_exact_recomputable_parent_bytes(field):
    _,_,resolver,bundle=fixture()
    bad=deepcopy(bundle)
    bad[field]="9"*64
    with pytest.raises(TargetBundleError):
        verify_target_none_fixture(bad,resolver.get)

def test_t7_target_none_changed_body_breaks_bundle_content_digest():
    _,_,resolver,bundle=fixture()
    bad=deepcopy(bundle)
    bad["negative_obligations"].append("DISABLE_QUERY_LEAKAGE_CONTROL")
    with pytest.raises(TargetBundleError):
        verify_target_none_fixture(bad,resolver.get)

def test_t7_no_self_issued_selection_from_fixture_pass_string():
    _,_,resolver,bundle=fixture()
    with pytest.raises(TargetBundleError):
        issue_selected_target_bundle(candidate_id="C1",status="PASS",fixture_parent_bundle=bundle)
    with pytest.raises(TargetBundleError):
        verify_target_none_fixture({**bundle,"target_selection":"C1"},resolver.get)

def test_t7_rejects_caller_forged_external_scope():
    _,_,resolver,bundle=fixture()
    for field,value in [
      ("scope","HUMAN_EXECUTABLE"),("qualification_stage","KNOWN_TRUTH_QUALIFIED"),
      ("training_authorized",True),("real_reference_ready",True)]:
        bad={**bundle,field:value}
        with pytest.raises(TargetBundleError):
            verify_target_none_fixture(bad,resolver.get)

def test_t7_external_source_substitution_refused_even_with_matching_digest_claim():
    _,keys,resolver,bundle=fixture()
    def false_resolver(sha):
        if sha==keys["registry"]:
            return {"object_role":"FIXTURE_REGISTRY","status":"PASS"}
        return resolver.get(sha)
    with pytest.raises(TargetBundleError):
        verify_target_none_fixture(bundle,false_resolver)

def test_t8_no_target_abstention_exercises_no_teacher_or_training():
    _,_,resolver,bundle=fixture()
    rec=certify_downstream_abstention(bundle,resolver=resolver.get)
    assert rec["schema"]=="DOWNSTREAM_CERTIFICATION_RECEIPT_V1"
    assert rec["status"]=="NO_TARGET__DOWNSTREAM_ABSTAIN"
    assert rec["target_bundle_sha256"]==bundle["target_bundle_sha256"]
    assert rec["teacher_constructed"] is False
    assert rec["ema_updates"]==0
    assert rec["training_authorized"] is False
    assert rec["downstream_certified"] is False
    assert rec["authority_effect"]=="NONE"

@pytest.mark.parametrize("kwargs",[
    {"teacher_executed":True},
    {"student_executed":True},
    {"optimizer_steps":1},
    {"ema_updates":1},
    {"selected_candidate":"C1"},
    {"downstream_obligation_receipts":[{"status":"PASS"}]},
])
def test_t8_abstention_cannot_hide_work_or_fake_receipts(kwargs):
    _,_,resolver,bundle=fixture()
    with pytest.raises(DownstreamContractError):
        certify_downstream_abstention(bundle,resolver=resolver.get,**kwargs)

def test_t8_invalid_bundle_receipt_rejected():
    _,_,resolver,bundle=fixture()
    evil={**bundle,"target_bundle_sha256":"1"*64}
    with pytest.raises(DownstreamContractError):
        certify_downstream_abstention(evil,resolver=resolver.get)

def test_t8_consumer_does_not_modify_any_verified_inputs():
    inputs,_,resolver,bundle=fixture()
    snapshot=deepcopy(bundle)
    first=certify_downstream_abstention(bundle,resolver=resolver.get)
    second=certify_downstream_abstention(bundle,resolver=resolver.get)
    assert first==second
    assert bundle==snapshot
    assert inputs["registry"]["status"]=="NO_QUALIFIED_TARGETS"
