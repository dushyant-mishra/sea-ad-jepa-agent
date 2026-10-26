"""Author self-audit RED (Macha) for the Task 3 repair at c128e43e — not independent review.

Round 1: caller-held objects built by hand or mutated after issuance.
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


class EqAnyStr(str):
    __hash__ = str.__hash__

    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


class AlwaysWithinFloat(float):
    """JSON/repr bytes are its own value, but every comparison says 'inside the band'."""
    def __le__(self, other):
        return True

    def __ge__(self, other):
        return True


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


def test_R1a_hand_built_check_cannot_claim_authentication():
    try:
        forged = cal.CalibrationCheck(artifact(), cal.AUTHENTICATED)
    except (cal.CalibrationError, TypeError):
        return
    assert forged.authenticated is False and forged.provenance != cal.AUTHENTICATED


def test_R1b_artifact_mutated_after_construction_cannot_pass_firewall():
    a = artifact()
    object.__setattr__(a, "split_role", EqAnyStr("READER_ORACLE"))
    with pytest.raises(cal.CalibrationError):
        firewall(a)


def test_R1c_contract_bands_mutated_after_issuance_cannot_force_a_pass():
    c = cal.RealismContract.frozen(
        metric_bands=(("OBS_DEPTH", (0.25, 0.75)),), adjustable_observation_parameters=("OBS_DEPTH_SCALE",),
        max_iterations=1, version_family_sha256=hashlib.sha256(b"r1c").hexdigest(), authority_scope="SYNTH_DEBUG_ONLY")
    s = cal.RealismState.initial(c)
    object.__setattr__(c, "metric_bands", (("OBS_DEPTH", (AlwaysWithinFloat(0.25), AlwaysWithinFloat(0.75))),))
    try:
        s = cal.advance_realism_iteration(c, s, version_sha256=hashlib.sha256(b"far-outside").hexdigest(),
                                          metrics={"OBS_DEPTH": 99.0})
    except cal.CalibrationError:
        return
    assert s.status != "FIRST_JOINT_PASS_FROZEN", "a JSON-identical mutated band forced a joint pass"


def test_R1d_provenance_mutated_after_construction_fails_revalidation():
    p = cal.NumericProvenance("DUMMY_LIMIT", 0.2, "PROSPECTIVE_CONVENTION", SHA)
    object.__setattr__(p, "category", "AUTHENTICATED_EMPIRICAL_CALIBRATION")
    with pytest.raises(cal.CalibrationError):
        cal.validate_numeric_provenance(p)


def test_R1e_protected_roles_must_be_disjoint():
    with pytest.raises(cal.CalibrationError):
        firewall(protected_partitions=dict(PARTITIONS, ORACLE=("DUMMY_VALIDATION",)))


def test_R1f_universe_check_status_cannot_be_forged():
    with pytest.raises((cal.CalibrationError, TypeError)):
        cal.UniverseCheck("OBSERVATION_MEAN_DEPTH", 2, "CALIBRATION_ELIGIBLE")


def test_R1g_mutated_issued_check_is_not_verified():
    checked = firewall()
    object.__setattr__(checked, "status", cal.AUTHENTICATED)
    with pytest.raises(cal.CalibrationError):
        cal.verify_calibration_check(checked)


# --- Round 2: attacks on the round-1 fixes and remaining surfaces -------------------------

def _contract(family, max_iterations=2):
    return cal.RealismContract.frozen(
        metric_bands=(("OBS_DEPTH", (0.25, 0.75)),), adjustable_observation_parameters=("OBS_DEPTH_SCALE",),
        max_iterations=max_iterations, version_family_sha256=hashlib.sha256(family).hexdigest(),
        authority_scope="SYNTH_DEBUG_ONLY")


def test_R2a_forged_terminal_realism_state_fails_public_verification():
    c = _contract(b"r2a")
    s = cal.RealismState.initial(c)
    forged = cal.RealismState(s.contract_state_sha256, s.contract_sha256, (hashlib.sha256(b"x").hexdigest(),),
                              hashlib.sha256(b"x").hexdigest(), "FIRST_JOINT_PASS_FROZEN")
    with pytest.raises(cal.CalibrationError):
        cal.verify_realism_state(forged)


def test_R2a_lawful_terminal_state_verifies():
    c = _contract(b"r2a-lawful")
    s = cal.RealismState.initial(c)
    s = cal.advance_realism_iteration(c, s, version_sha256=hashlib.sha256(b"p").hexdigest(), metrics={"OBS_DEPTH": 0.5})
    assert cal.verify_realism_state(s).status == "FIRST_JOINT_PASS_FROZEN"


def test_R2b_precision_target_mutated_after_construction_is_a_calibration_error():
    t = cal.PrecisionTarget(epsilon=0.1, alpha=0.01)
    object.__setattr__(t, "epsilon", 0.0)
    with pytest.raises(cal.CalibrationError):
        cal.derive_budget_from_precision({"donors": t, "worlds": cal.PrecisionTarget(0.1, 0.01),
                                          "nulls": cal.PrecisionTarget(0.1, 0.01)})


def test_R2c_huge_integer_band_is_a_calibration_error():
    with pytest.raises(cal.CalibrationError):
        cal.RealismContract.frozen(
            metric_bands=(("OBS_DEPTH", (0, 10 ** 400)),), adjustable_observation_parameters=("OBS_DEPTH_SCALE",),
            max_iterations=1, version_family_sha256=hashlib.sha256(b"r2c").hexdigest(), authority_scope="SYNTH_DEBUG_ONLY")


def test_R2d_hand_built_check_is_not_authenticated_even_when_digest_is_pinned(monkeypatch):
    monkeypatch.setattr(cal, "_AUTHENTICATED_CALIBRATION_REGISTRY", frozenset({SHA}))
    forged = cal.CalibrationCheck(artifact(donors=("DUMMY_ORACLE",)), cal.AUTHENTICATED)
    assert forged.authenticated is False
    with pytest.raises(cal.CalibrationError):
        cal.verify_calibration_check(forged)


def test_R2e_token_swapped_check_is_refused():
    a = firewall()
    b = firewall()
    object.__setattr__(a, "_token", object.__getattribute__(b, "_token"))
    with pytest.raises(cal.CalibrationError):
        cal.verify_calibration_check(a)


# --- Round 3: verifiers must never hand out the private copy -------------------------------

def test_R3a_verified_realism_state_is_detached_from_private_custody():
    c = _contract(b"r3a", max_iterations=1)
    s = cal.RealismState.initial(c)
    s = cal.advance_realism_iteration(c, s, version_sha256=hashlib.sha256(b"f").hexdigest(), metrics={"OBS_DEPTH": 0.9})
    assert s.status == "REALISM_NOT_QUALIFIED"
    v = cal.verify_realism_state(s)
    for obj in {id(v): v, id(s): s}.values():
        object.__setattr__(obj, "status", "SEARCHING")
        object.__setattr__(obj, "versions_tested", ())
    with pytest.raises(cal.CalibrationError):
        cal.advance_realism_iteration(c, s, version_sha256=hashlib.sha256(b"g").hexdigest(), metrics={"OBS_DEPTH": 0.5})


def test_R3b_verified_check_is_detached_from_private_custody():
    checked = firewall()
    v = cal.verify_calibration_check(checked)
    for obj in {id(v.artifact): v.artifact, id(checked.artifact): checked.artifact}.values():
        object.__setattr__(obj, "donors", ("DUMMY_ORACLE",))
    with pytest.raises(cal.CalibrationError):
        cal.verify_calibration_check(checked)
