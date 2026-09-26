"""V29 adversarial tests: no real data or training, class conflict cannot become false green."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import pytest
from scripts.v5.v29_class_compatibility_audit import audit, CLOSURE, LEDGER, VALIDATOR

REPO = Path(__file__).resolve().parents[1]
def baseline():
    return audit(REPO)
def closure_text():
    return (REPO / CLOSURE).read_text()
def validator_text():
    return (REPO / VALIDATOR).read_text()
def ledger():
    return json.loads((REPO / LEDGER).read_text())

def test_original_positive_six_candidates_and_zero_closure():
    result = baseline()
    assert result["own_schema_candidates"] == 6
    assert result["class_conflicts"] == 2 and result["fully_closed_roots"] == 0
    assert result["training_authorized"] is False and result["closure_ready"] is False

def test_exact_two_v3_v1_incompatibilities():
    bad = {x["root"]: (x["candidate_class"], x["closure_required_class"])
           for x in baseline()["rows"] if not x["class_compatible"]}
    assert bad == {
        "masking_rng_replay_authority_sha256": ("MaskingRngReplayAuthorityV3", "MaskingRngReplayAuthorityV1"),
        "masking_qualification_parameters_authority_sha256": ("MaskingQualificationParametersAuthorityV3", "MaskingQualificationParametersAuthorityV1"),
    }

def test_raw_digest_slots_are_not_missing_dataclasses():
    a = baseline()
    assert a["raw_sha_arguments"] == [
        "full104_substrate_sha256", "observation_gradient_firewall_authority_sha256"]
    assert a["full104_substrate_physically_rehashed_by_this_audit"] is False

@pytest.mark.parametrize("role", ["masking_rng_replay", "masking_qualification_parameters"])
def test_invented_v3_annotated_only_without_real_import_fails(role):
    source = closure_text()
    old = ("MaskingRngReplayAuthorityV1" if role == "masking_rng_replay"
           else "MaskingQualificationParametersAuthorityV1")
    mutated = source.replace(role + ": " + old, role + ": " + old[:-2] + "V3")
    with pytest.raises(ValueError, match="CLASS_IMPORT_MISSING"):
        audit(REPO, closure_source=mutated)

def test_pretending_a_schema_rename_repairs_closure_is_rejected():
    content = validator_text().replace(
        '"V5_MASKING_RNG_REPLAY_AUTHORITY_V3", MaskingRngReplayAuthorityV3)',
        '"V5_MASKING_RNG_REPLAY_AUTHORITY_V1", MaskingRngReplayAuthorityV3)')
    with pytest.raises(ValueError, match="SCHEMA_SPILLOVER"):
        audit(REPO, validator_source=content)

def test_removed_33rd_slot_fails_closed():
    state = ledger()
    state["rows"].pop()
    with pytest.raises(ValueError, match="ROOT_ORDER"):
        audit(REPO, ledger_data=state)

def test_fabricated_one_closed_root_fails_closed():
    state = ledger()
    state["fully_closed_roots"] = 1
    with pytest.raises(ValueError, match="FALSE_V27_CLOSURE"):
        audit(REPO, ledger_data=state)

def test_false_training_flag_fails_closed():
    state = ledger()
    state["rows"][1]["current_closure_validated"] = True
    with pytest.raises(ValueError, match="PREMATURE_CLOSURE"):
        audit(REPO, ledger_data=state)

def test_raw_sha_arguments_cannot_be_promoted_to_nonexistent_class():
    state = ledger()
    state["rows"][0]["classification"] = "CANDIDATE_VALIDATED_BY_CURRENT_OWN_CLASS"
    with pytest.raises(ValueError, match="RAW_ROLE_CLASS_FORGERY"):
        audit(REPO, ledger_data=state)

def test_extra_candidate_role_requires_independent_reaudit():
    content = validator_text().replace(
        "CANDIDATES = {", 'CANDIDATES = {"forged_authority": ("fake.json", "FAKE", Foo),', 1)
    with pytest.raises(ValueError, match="SIX_ROOT"):
        audit(REPO, validator_source=content)

def test_matching_class_is_not_equivalent_to_full_authority():
    # Even if the class seams are prospectively repaired, no parent-source validation or
    # B1 training contract is supplied by this audit.
    a = baseline()
    assert all(not row["fully_closed"] for row in a["rows"])
    assert a["reader_fit_training_contract_issued"] is False
    assert a["upstream_parent_bytes_authenticated_by_this_audit"] is False
