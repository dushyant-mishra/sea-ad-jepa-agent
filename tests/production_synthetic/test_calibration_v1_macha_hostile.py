"""Macha independent hostile RED for production-synthetic Task 3 at 1f2b7f1f (PR #432).

Dummy fixtures only. Each test pins one blocking defect and must FAIL against
1f2b7f1fab7a952ffd4aee11d5ef7af827cf6b47. Tests are written to accept either a
CalibrationError or an explicitly non-authoritative result, so a repair is free
to choose its API, but may not keep presenting caller assertions as authority.

Original RED preserved at cdf0bc56 (CI run 40342119953: 11 failed). The repair
replaced the caller tuple ``excluded_donors`` with a per-role
``protected_partitions`` mapping, so ``firewall()`` below passes partitions;
every attack is unchanged (A2 still omits all protected partitions).
"""
from __future__ import annotations

import hashlib

import pytest

from scripts.production_synthetic import calibration_v1 as cal
from scripts.production_synthetic.calibration_v1 import (
    CalibrationArtifact, CalibrationError, NumericProvenance, RealismContract,
    RealismState, advance_realism_iteration, validate_address_universe_agnostic,
    validate_calibration_firewall,
)


def h(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


RAW = b"DUMMY_OBSERVATION_DEPTH_COUNTS_V1"
SHA = h(RAW)
FIT = ("DUMMY_F01", "DUMMY_F02", "DUMMY_F03")
PARTITIONS = {"VALIDATION": ("DUMMY_VALIDATION",), "ORACLE": ("DUMMY_ORACLE",),
              "RESERVED": ("DUMMY_RESERVED",), "DEVELOPMENT": ("DUMMY_DEV",)}


class EqAnyStr(str):
    """Canonical text is its own value, but it compares equal to anything."""
    __hash__ = str.__hash__

    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


def artifact(**over):
    p = dict(content_sha256=SHA, source_scope="DUMMY_RNA_COUNTS", donors=FIT,
             split_role="CALIBRATION_FIT", feature_family="OBSERVATION_DEPTH",
             stratification=(), provenance="AUTHENTICATED_EMPIRICAL_CALIBRATION")
    p.update(over)
    return CalibrationArtifact(**p)


def firewall(a, *, raw=RAW, pinned=SHA, eligible=FIT, partitions=None):
    return validate_calibration_firewall(
        a, raw_bytes=raw, independently_pinned_sha256=pinned,
        expected_source_scope="DUMMY_RNA_COUNTS",
        eligible_fit_donors=eligible,
        protected_partitions=PARTITIONS if partitions is None else partitions,
    )


# --- A. authentication and split isolation -------------------------------------------------

def test_A1_reader_oracle_split_lookalike_cannot_pass_firewall():
    with pytest.raises(CalibrationError):
        firewall(artifact(split_role=EqAnyStr("READER_ORACLE")))


def test_A1_forged_provenance_lookalike_cannot_pass_firewall():
    with pytest.raises(CalibrationError):
        firewall(artifact(provenance=EqAnyStr("BIOLOGICAL_TRUTH")))


def test_A2_protected_partitions_cannot_be_omitted_by_the_caller():
    # A caller that omits every protected role can list any donor as fit-eligible.
    with pytest.raises(CalibrationError):
        firewall(artifact(donors=("DUMMY_VALIDATION",)), eligible=("DUMMY_VALIDATION",), partitions={})


def test_A3_self_pinned_digest_is_not_authenticated_empirical_calibration():
    raw = b"any bytes the caller chooses"
    try:
        result = firewall(artifact(content_sha256=h(raw)), raw=raw, pinned=h(raw))
    except CalibrationError:
        return
    assert getattr(result, "provenance", None) != "AUTHENTICATED_EMPIRICAL_CALIBRATION", (
        "a digest the caller pinned for itself was returned as AUTHENTICATED_EMPIRICAL_CALIBRATION"
    )


# --- B. numeric provenance -----------------------------------------------------------------

def test_B_authenticated_label_with_unbound_identity_confers_no_authority():
    with pytest.raises(CalibrationError):
        NumericProvenance("DUMMY_LIMIT", 0.2, "AUTHENTICATED_EMPIRICAL_CALIBRATION", "0" * 64)


# --- C. address-universe eligibility -------------------------------------------------------

def test_C_identical_caller_values_and_self_matched_digest_are_not_proof():
    values = {"DUMMY_F01": 2.0, "DUMMY_F02": 3.0}
    digest = h(b"any digest the caller chooses")
    try:
        result = validate_address_universe_agnostic(
            "OBSERVATION_MEAN_DEPTH", values, dict(values),
            pilot_n_addresses=96, full_n_addresses=41238,
            full_universe_sha256=digest, expected_full_universe_sha256=digest,
        )
    except CalibrationError:
        return
    assert result is not True, "caller-supplied identical values returned bare True (eligibility)"


# --- D. realism freeze and stopping --------------------------------------------------------

def contract(max_iterations=1, bands=(("OBS_DEPTH", (0.25, 0.75)), ("DETECTION", (0.1, 0.4))),
             family=b"fixture-generator-v1"):
    parts = dict(metric_bands=bands, adjustable_observation_parameters=("OBS_DEPTH_SCALE",),
                 max_iterations=max_iterations, version_family_sha256=h(family),
                 authority_scope="SYNTH_DEBUG_ONLY")
    claim = h(repr(sorted(parts.items())).encode())
    try:
        return RealismContract(contract_sha256=claim, **parts)
    except CalibrationError:
        # A repaired contract may require its claim to equal its own content digest.
        probe = RealismContract.__new__(RealismContract)
        for key, value in dict(contract_sha256="0" * 64, **parts).items():
            object.__setattr__(probe, key, value)
        return RealismContract(contract_sha256=cal._contract_digest(probe), **parts)


FAIL = {"OBS_DEPTH": 0.9, "DETECTION": 0.2}
PASS = {"OBS_DEPTH": 0.5, "DETECTION": 0.2}


def test_D1_search_cannot_be_reset_after_exhaustion():
    c = contract(family=b"d1-family")
    s = advance_realism_iteration(c, RealismState.initial(c), version_sha256=h(b"d1-failed"), metrics=FAIL)
    assert s.status == "REALISM_NOT_QUALIFIED"
    with pytest.raises(CalibrationError):
        advance_realism_iteration(c, RealismState.initial(c), version_sha256=h(b"d1-retry"), metrics=PASS)


def test_D2_failed_version_cannot_be_replayed_in_a_fresh_search():
    c = contract(max_iterations=3, family=b"d2-family")
    advance_realism_iteration(c, RealismState.initial(c), version_sha256=h(b"d2-v1"), metrics=FAIL)
    with pytest.raises(CalibrationError):
        advance_realism_iteration(c, RealismState.initial(c), version_sha256=h(b"d2-v1"), metrics=PASS)


def test_D3_caller_constructed_state_cannot_reopen_an_exhausted_search():
    c = contract(family=b"d3-family")
    s = advance_realism_iteration(c, RealismState.initial(c), version_sha256=h(b"d3-failed"), metrics=FAIL)
    forged = RealismState(s.contract_state_sha256, s.contract_sha256, (), None, "SEARCHING")
    with pytest.raises(CalibrationError):
        advance_realism_iteration(c, forged, version_sha256=h(b"d3-new"), metrics=PASS)


def test_D4_relaxed_contract_cannot_restart_the_same_generator_family():
    c = contract(family=b"d4-family")
    advance_realism_iteration(c, RealismState.initial(c), version_sha256=h(b"d4-failed"), metrics=FAIL)
    relaxed = contract(max_iterations=5, bands=(("OBS_DEPTH", (0.0, 1.0)), ("DETECTION", (0.0, 1.0))),
                       family=b"d4-family")
    with pytest.raises(CalibrationError):
        advance_realism_iteration(relaxed, RealismState.initial(relaxed),
                                  version_sha256=h(b"d4-failed"), metrics=FAIL)


def test_D5_contract_identity_claim_must_equal_its_content():
    parts = dict(metric_bands=(("OBS_DEPTH", (0.25, 0.75)),),
                 adjustable_observation_parameters=("OBS_DEPTH_SCALE",), max_iterations=1,
                 version_family_sha256=h(b"d5-family"), authority_scope="SYNTH_DEBUG_ONLY")
    with pytest.raises(CalibrationError):
        RealismContract(contract_sha256=h(b"an arbitrary claimed identity"), **parts)
