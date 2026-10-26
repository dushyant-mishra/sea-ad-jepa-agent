"""Task 3 hostile fixture tests. All calibration bytes/donors here are dummy.

No real reader-fit/validation/oracle data, target outcomes or withheld controller
parameters are present. These tests must be RED before calibration_v1 exists.
"""
from __future__ import annotations

import hashlib
import pytest

from scripts.production_synthetic.calibration_v1 import (
    CalibrationError, CalibrationArtifact, NumericProvenance,
    RealismContract, RealismState, PrecisionTarget,
    validate_calibration_firewall, validate_address_universe_agnostic,
    derive_budget_from_precision, advance_realism_iteration,
)

def h(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

RAW = b"DUMMY_OBSERVATION_DEPTH_COUNTS_V1"
SHA = h(RAW)
FIT = ("DUMMY_F01", "DUMMY_F02", "DUMMY_F03")
BLOCKED = ("DUMMY_VALIDATION", "DUMMY_ORACLE", "DUMMY_RESERVED", "DUMMY_DEV")

def artifact(**over):
    p = dict(content_sha256=SHA, source_scope="DUMMY_RNA_COUNTS",
             donors=FIT, split_role="CALIBRATION_FIT",
             feature_family="OBSERVATION_DEPTH", stratification=(),
             provenance="AUTHENTICATED_EMPIRICAL_CALIBRATION")
    p.update(over)
    return CalibrationArtifact(**p)

def validate(a=None, **over):
    return validate_calibration_firewall(
        a if a is not None else artifact(), raw_bytes=RAW,
        independently_pinned_sha256=SHA, expected_source_scope="DUMMY_RNA_COUNTS",
        eligible_fit_donors=FIT, excluded_donors=BLOCKED, **over
    )

def test_real_calibration_requires_pinned_bytes_scope_and_fit_split():
    assert validate().content_sha256 == SHA
    with pytest.raises(CalibrationError):
        validate(artifact(content_sha256="0"*64))
    with pytest.raises(CalibrationError):
        validate(artifact(source_scope="DIFFERENT_SOURCE"))
    with pytest.raises(CalibrationError):
        validate(artifact(split_role="READER_ORACLE"))
    with pytest.raises(CalibrationError):
        validate_calibration_firewall(artifact(), raw_bytes=RAW,
                                     independently_pinned_sha256="f"*64,
                                     expected_source_scope="DUMMY_RNA_COUNTS",
                                     eligible_fit_donors=FIT, excluded_donors=BLOCKED)

@pytest.mark.parametrize("name", ["DUMMY_VALIDATION", "DUMMY_ORACLE", "DUMMY_RESERVED", "DUMMY_DEV"])
def test_every_protected_role_overlap_fails(name):
    with pytest.raises(CalibrationError):
        validate(artifact(donors=("DUMMY_F01", name)))

@pytest.mark.parametrize("family", ["DIAGNOSIS", "PATHOLOGY", "DISEASE_PREVALENCE",
                                     "TARGET_TRUTH", "SCENIC_REGULON_TRUTH", "BIOLOGICAL_EFFECT"])
def test_biology_proxy_stratification_cannot_be_authenticated(family):
    with pytest.raises(CalibrationError):
        validate(artifact(feature_family=family))

def test_source_as_pathology_proxy_is_rejected():
    with pytest.raises(CalibrationError):
        validate(artifact(stratification=("SOURCE_AS_DIAGNOSIS_PROXY",)))

def test_duplicate_or_unapproved_donors_fail():
    with pytest.raises(CalibrationError):
        validate(artifact(donors=("DUMMY_F01", "DUMMY_F01")))
    with pytest.raises(CalibrationError):
        validate(artifact(donors=("DUMMY_NEW",)))

def test_decision_numbers_have_exact_provenance():
    p=NumericProvenance(name="DUMMY_OBSERVATION_DEPTH_LIMIT",value=0.2,
       category="PROSPECTIVE_CONVENTION",identity_sha256=h(b"prospectively frozen"))
    assert p.category == "PROSPECTIVE_CONVENTION"
    for bad in ["UNKNOWN", "EMPIRICAL", "BIOLOGICAL_TRUTH"]:
        with pytest.raises(CalibrationError):
            NumericProvenance("x",0.2,bad,h(b"x"))
    with pytest.raises(CalibrationError):
        NumericProvenance("x", float("nan"),"PROSPECTIVE_CONVENTION",h(b"x"))
    with pytest.raises(CalibrationError):
        NumericProvenance("x", True,"PROSPECTIVE_CONVENTION",h(b"x"))

def test_96_gene_envelopes_do_not_auto_qualify_41238():
    a={"DUMMY_F01":2.0,"DUMMY_F02":3.0}
    with pytest.raises(CalibrationError):
        validate_address_universe_agnostic(
            "DETECTED_FEATURE_COUNT",a,a,
            pilot_n_addresses=96,full_n_addresses=41238,
            full_universe_sha256=h(b"full-address-universe"),
            expected_full_universe_sha256=h(b"full-address-universe"))
    with pytest.raises(CalibrationError):
        validate_address_universe_agnostic(
            "OBSERVATION_MEAN_DEPTH",a,{"DUMMY_F01":2.0,"DUMMY_F02":4.0},
            pilot_n_addresses=96,full_n_addresses=41238,
            full_universe_sha256=h(b"full-address-universe"),
            expected_full_universe_sha256=h(b"full-address-universe"))
    assert validate_address_universe_agnostic(
        "OBSERVATION_MEAN_DEPTH",a,a,
        pilot_n_addresses=96,full_n_addresses=41238,
        full_universe_sha256=h(b"full-address-universe"),
        expected_full_universe_sha256=h(b"full-address-universe")) is True

def contract(max_iterations=2):
    return RealismContract(
        contract_sha256=h(b"realism-contract-v1"),
        metric_bands=(("OBS_DEPTH",(0.25,0.75)),("DETECTION",(0.1,0.4))),
        adjustable_observation_parameters=("OBS_DEPTH_SCALE","OBS_DETECTION_SCALE"),
        max_iterations=max_iterations, version_family_sha256=h(b"fixture-generator-v1"),
        authority_scope="SYNTH_DEBUG_ONLY",
    )

def test_first_joint_pass_stops_and_cannot_be_shopped():
    c=contract()
    s=RealismState.initial(c)
    s=advance_realism_iteration(c,s,version_sha256=h(b"v1"),metrics={"OBS_DEPTH":0.50,"DETECTION":0.5})
    assert s.status == "SEARCHING" and s.first_passing_version is None
    s=advance_realism_iteration(c,s,version_sha256=h(b"v2"),metrics={"OBS_DEPTH":0.5,"DETECTION":0.3})
    assert s.status=="FIRST_JOINT_PASS_FROZEN" and s.first_passing_version==h(b"v2")
    with pytest.raises(CalibrationError):
        advance_realism_iteration(c,s,version_sha256=h(b"v3"),metrics={"OBS_DEPTH":0.5,"DETECTION":0.2})

def test_exhaustion_is_not_qualified_and_does_not_choose_best_failed():
    c=contract(max_iterations=1)
    s=advance_realism_iteration(c,RealismState.initial(c),
        version_sha256=h(b"failed"),metrics={"OBS_DEPTH":0.2,"DETECTION":0.3})
    assert s.status == "REALISM_NOT_QUALIFIED"
    assert s.first_passing_version is None
    with pytest.raises(CalibrationError):
        advance_realism_iteration(c,s,version_sha256=h(b"retry"),metrics={"OBS_DEPTH":0.5,"DETECTION":0.2})

def test_realism_blocks_changed_contract_duplicate_version_and_extra_metric():
    c=contract()
    s=RealismState.initial(c)
    with pytest.raises(CalibrationError):
        advance_realism_iteration(c,s,version_sha256=h(b"x"),metrics={"OBS_DEPTH":.5,"DETECTION":.2,"OUTCOME":.9})
    s=advance_realism_iteration(c,s,version_sha256=h(b"x"),metrics={"OBS_DEPTH":.9,"DETECTION":.2})
    with pytest.raises(CalibrationError):
        advance_realism_iteration(c,s,version_sha256=h(b"x"),metrics={"OBS_DEPTH":.5,"DETECTION":.2})
    with pytest.raises(CalibrationError):
        advance_realism_iteration(contract(max_iterations=3),s,
             version_sha256=h(b"y"),metrics={"OBS_DEPTH":.5,"DETECTION":.2})

def test_precision_budgets_are_maths_only_and_frozen():
    p={
        "donors":PrecisionTarget(epsilon=0.1,alpha=0.01),
        "worlds":PrecisionTarget(epsilon=0.2,alpha=0.02),
        "nulls":PrecisionTarget(epsilon=0.05,alpha=0.01),
    }
    budgets=derive_budget_from_precision(p)
    assert budgets["nulls"]>budgets["donors"]>budgets["worlds"]>0
    for name in ("donors","worlds","nulls"):
        assert isinstance(budgets[name],int)
    with pytest.raises(CalibrationError):
        derive_budget_from_precision({"donors":PrecisionTarget(epsilon=0,alpha=.01)})
    with pytest.raises(CalibrationError):
        derive_budget_from_precision({"donors":PrecisionTarget(epsilon=.1,alpha=1)})
