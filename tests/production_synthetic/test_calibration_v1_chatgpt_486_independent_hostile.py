"""Independent ChatGPT-hostile continuation on Macha PR #486 exact code head.

Synthetic fixture only. This tests numerical identity, type dispatch, name
registry, and refusal of false empirical authority. No source issuer or human
observations are introduced. The original #480 reviewer suite is unchanged.
"""
from hashlib import sha256
import math

import numpy as np
import pytest

from scripts.production_synthetic import calibration_v1 as cal


def h(data):
    return sha256(data).hexdigest()


def universe(pilot, full):
    digest = h(b"independent synthetic address universe")
    return cal.validate_address_universe_agnostic(
        "OBSERVATION_MEAN_DEPTH", {"cell": pilot}, {"cell": full},
        pilot_n_addresses=96, full_n_addresses=41238,
        full_universe_sha256=digest, expected_full_universe_sha256=digest,
    )


@pytest.mark.parametrize("a,b", [
    (2**53, 2**53+1),
    (2**60, 2**60+1),
    (2**53+1, float(2**53)),
    (0.1+0.2, 0.3),
    (0, 1),
    (1, 1.0000000000000002),
])
def test_r1_distinct_exact_numeric_values_are_refused(a, b):
    with pytest.raises(cal.CalibrationError):
        universe(a, b)


@pytest.mark.parametrize("a,b", [
    (2**53, float(2**53)), (1, 1.0), (0.0, -0.0),
    (-2**53, float(-2**53)), (0.25, 0.25),
])
def test_r1_int_float_exact_mathematical_equality_is_allowed_only_as_fixture(a,b):
    result = universe(a,b)
    assert result.status == cal.UNIVERSE_FIXTURE_ONLY
    assert result.calibration_eligible is False


@pytest.mark.parametrize("number", [
    float("nan"), float("inf"), float("-inf"), 10**400,
    np.int64(1), np.float64(1.0), np.uintc(1), np.intc(1),
    True, False,
])
def test_nonfinite_or_non_exact_builtin_numbers_fail_closed(number):
    with pytest.raises(cal.CalibrationError):
        universe(number, 1)
    with pytest.raises(cal.CalibrationError):
        universe(1, number)


class HostileMeta(type):
    calls = 0

    def __eq__(cls, other):
        HostileMeta.calls += 1
        raise RuntimeError("payload metaclass escaped")

    __hash__ = type.__hash__


class HostileNumeric(metaclass=HostileMeta):
    def __float__(self):
        raise RuntimeError("payload float escaped")


def test_numeric_type_dispatch_invokes_no_hostile_metaclass_or_float():
    HostileMeta.calls = 0
    with pytest.raises(cal.CalibrationError):
        universe(HostileNumeric(), 1)
    assert HostileMeta.calls == 0


class TrapKey(str):
    hash_calls = 0
    eq_calls = 0

    def __hash__(self):
        TrapKey.hash_calls += 1
        return str.__hash__(self)

    def __eq__(self, other):
        TrapKey.eq_calls += 1
        raise RuntimeError("unexpected key comparison")


def test_malicious_dict_key_is_type_checked_before_hash_or_eq():
    digest=h(b"independent synthetic address universe")
    pilot={TrapKey("cell"):1}
    full={"cell":1}
    TrapKey.hash_calls=0
    TrapKey.eq_calls=0
    with pytest.raises(cal.CalibrationError):
        cal.validate_address_universe_agnostic(
            "OBSERVATION_MEAN_DEPTH", pilot, full,
            pilot_n_addresses=96, full_n_addresses=41238,
            full_universe_sha256=digest, expected_full_universe_sha256=digest,
        )
    assert (TrapKey.hash_calls, TrapKey.eq_calls)==(0,0)


def contract(name):
    return cal.RealismContract.frozen(
        metric_bands=(("OBS_DEPTH",(0.2,0.8)),),
        adjustable_observation_parameters=(name,),
        max_iterations=1,
        version_family_sha256=h(b"independent synthetic family"),
        authority_scope="SYNTH_DEBUG_ONLY",
    )


@pytest.mark.parametrize("bad", [
    "OBS_DISEASE_PREVALENCE","OBS_TARGET_WINNER",
    "OBS_LATENT_REGULATORY_TRUTH","OBS_BIOLOGICAL_PROGRAM_SCALE",
    "OBS_DEPTH","OBS_DEPTH_SCALE ","obs_depth_scale",
    "OBS_DEPTH_SCALE\u200b", "OBS_", True, 1,
])
def test_unregistered_or_semantic_spoof_name_rejected(bad):
    with pytest.raises(cal.CalibrationError):
        contract(bad)


def test_closed_registry_names_only_and_semantics_still_unbound():
    names=cal.OBSERVATION_PARAMETER_REGISTRY
    assert type(names) is frozenset
    assert len(names)==7
    assert "OBS_DEPTH_SCALE" in names
    assert "OBS_DISEASE_PREVALENCE" not in names
    assert cal.OBSERVATION_PARAMETER_SEMANTICS_BOUND is False
    assert type(cal.OBSERVATION_PARAMETER_REGISTRY_VERSION) is str
    assert len(cal.OBSERVATION_PARAMETER_REGISTRY_SHA256)==64
    for name in sorted(names):
        assert contract(name).authority_scope=="SYNTH_DEBUG_ONLY"


def test_self_pinned_digest_cannot_issue_authenticated_calibration():
    raw=b"independent synthetic calibration bytes"
    digest=h(raw)
    artifact=cal.CalibrationArtifact(
        digest,"SYNTH_ONLY",("FIT_SYNTH",),"CALIBRATION_FIT",
        "OBSERVATION_DEPTH",(),cal.AUTHENTICATED,
    )
    result=cal.validate_calibration_firewall(
        artifact,raw_bytes=raw,independently_pinned_sha256=digest,
        expected_source_scope="SYNTH_ONLY",eligible_fit_donors=("FIT_SYNTH",),
        protected_partitions={
            "VALIDATION":("VAL_SYNTH",),
            "ORACLE":("ORACLE_SYNTH",),
            "RESERVED":("RESERVED_SYNTH",),
            "DEVELOPMENT":("DEVELOPMENT_SYNTH",),
        },
    )
    assert result.status==cal.UNAUTHENTICATED_FIXTURE
    assert result.authenticated is False
    assert cal.verify_calibration_check(result) is result
    assert cal._AUTHENTICATED_CALIBRATION_REGISTRY == frozenset()
    assert cal.HOSTILE_SAME_PROCESS_PROTECTION is False
