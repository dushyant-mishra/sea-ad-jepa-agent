"""Repair-side tests for the Macha-authored Task 3 repair (PS3-B1..B4).

Positive controls prove the fail-closed paths are not vacuous, and sibling
routes of each blocker are pinned. Dummy fixtures only.
"""
from __future__ import annotations

import hashlib

import pytest

from scripts.production_synthetic import calibration_v1 as cal

RAW = b"DUMMY_OBSERVATION_DEPTH_COUNTS_V1"
SHA = hashlib.sha256(RAW).hexdigest()
FIT = ("DUMMY_F01", "DUMMY_F02")
PARTITIONS = {"VALIDATION": ("DUMMY_VALIDATION",), "ORACLE": ("DUMMY_ORACLE",),
              "RESERVED": ("DUMMY_RESERVED",), "DEVELOPMENT": ("DUMMY_DEV",)}


def artifact(**over):
    p = dict(content_sha256=SHA, source_scope="DUMMY_RNA_COUNTS", donors=FIT,
             split_role="CALIBRATION_FIT", feature_family="OBSERVATION_DEPTH",
             stratification=(), provenance="AUTHENTICATED_EMPIRICAL_CALIBRATION")
    p.update(over)
    return cal.CalibrationArtifact(**p)


def firewall(a=None, **over):
    kw = dict(raw_bytes=RAW, independently_pinned_sha256=SHA, expected_source_scope="DUMMY_RNA_COUNTS",
              eligible_fit_donors=FIT, protected_partitions=PARTITIONS)
    kw.update(over)
    return cal.validate_calibration_firewall(a if a is not None else artifact(), **kw)


def test_caller_pinned_digest_is_consistent_but_unauthenticated():
    checked = firewall()
    assert checked.status == cal.UNAUTHENTICATED_FIXTURE
    assert checked.provenance != "AUTHENTICATED_EMPIRICAL_CALIBRATION"
    assert checked.authenticated is False


def test_authentication_is_reachable_only_through_the_code_pinned_registry(monkeypatch):
    monkeypatch.setattr(cal, "_AUTHENTICATED_CALIBRATION_REGISTRY", frozenset({SHA}))
    checked = firewall()
    assert checked.status == cal.AUTHENTICATED and checked.authenticated
    p = cal.NumericProvenance("DUMMY_DEPTH_LIMIT", 0.2, "AUTHENTICATED_EMPIRICAL_CALIBRATION", SHA)
    assert p.category == "AUTHENTICATED_EMPIRICAL_CALIBRATION"


def test_each_protected_role_is_required():
    for missing in PARTITIONS:
        partial = {k: v for k, v in PARTITIONS.items() if k != missing}
        with pytest.raises(cal.CalibrationError):
            firewall(protected_partitions=partial)
    with pytest.raises(cal.CalibrationError):
        firewall(protected_partitions=dict(PARTITIONS, ORACLE=()))


def test_fit_eligible_donors_may_not_overlap_a_protected_partition():
    with pytest.raises(cal.CalibrationError):
        firewall(eligible_fit_donors=FIT + ("DUMMY_ORACLE",))


def test_huge_integer_is_a_calibration_error_not_an_overflow():
    with pytest.raises(cal.CalibrationError):
        cal.NumericProvenance("x", 10 ** 400, "PROSPECTIVE_CONVENTION", SHA)


def contract(family):
    return cal.RealismContract.frozen(
        metric_bands=(("OBS_DEPTH", (0.25, 0.75)),),
        adjustable_observation_parameters=("OBS_DEPTH_SCALE",), max_iterations=2,
        version_family_sha256=hashlib.sha256(family).hexdigest(), authority_scope="SYNTH_DEBUG_ONLY")


def test_mutated_issued_realism_state_is_refused():
    c = contract(b"mut-family")
    s = cal.RealismState.initial(c)
    s = cal.advance_realism_iteration(c, s, version_sha256=hashlib.sha256(b"v1").hexdigest(), metrics={"OBS_DEPTH": 0.9})
    object.__setattr__(s, "versions_tested", ())
    with pytest.raises(cal.CalibrationError):
        cal.advance_realism_iteration(c, s, version_sha256=hashlib.sha256(b"v1").hexdigest(), metrics={"OBS_DEPTH": 0.5})


def test_stale_realism_state_cannot_fork_the_search():
    c = contract(b"stale-family")
    s0 = cal.RealismState.initial(c)
    cal.advance_realism_iteration(c, s0, version_sha256=hashlib.sha256(b"a").hexdigest(), metrics={"OBS_DEPTH": 0.9})
    with pytest.raises(cal.CalibrationError):
        cal.advance_realism_iteration(c, s0, version_sha256=hashlib.sha256(b"b").hexdigest(), metrics={"OBS_DEPTH": 0.5})


def test_first_joint_pass_is_still_reachable_lawfully():
    c = contract(b"lawful-family")
    s = cal.RealismState.initial(c)
    s = cal.advance_realism_iteration(c, s, version_sha256=hashlib.sha256(b"fail").hexdigest(), metrics={"OBS_DEPTH": 0.9})
    s = cal.advance_realism_iteration(c, s, version_sha256=hashlib.sha256(b"pass").hexdigest(), metrics={"OBS_DEPTH": 0.5})
    assert s.status == "FIRST_JOINT_PASS_FROZEN" and s.first_passing_version == hashlib.sha256(b"pass").hexdigest()
