"""ChatGPT repair guards for PR #486 independent review #487.

Synthetic/fixture mechanics only. This closes R3/R4 without creating real
calibration, observation-operator semantics, Task4, target, or training authority.
"""
from dataclasses import replace
from hashlib import sha256

import pytest

from scripts.production_synthetic import calibration_v1 as cal
from scripts.production_synthetic import canonical_v1 as C


def _contract():
    return cal.RealismContract.frozen(
        metric_bands=(("OBS_DEPTH", (0.2, 0.8)),),
        adjustable_observation_parameters=("OBS_DEPTH_SCALE",),
        max_iterations=1,
        version_family_sha256=sha256(b"chatgpt-r3-r4-family").hexdigest(),
        authority_scope="SYNTH_DEBUG_ONLY",
    )


def test_r3_contract_binds_exact_observation_registry_identity():
    c = _contract()
    assert c.observation_parameter_registry_version == cal.OBSERVATION_PARAMETER_REGISTRY_VERSION
    assert c.observation_parameter_registry_sha256 == cal.OBSERVATION_PARAMETER_REGISTRY_SHA256

    parts = cal._contract_parts(c)
    assert parts["schema"] == "PRODUCTION_SYNTHETIC_REALISM_CONTRACT_V2"
    assert parts["observation_parameter_registry_version"] == cal.OBSERVATION_PARAMETER_REGISTRY_VERSION
    assert parts["observation_parameter_registry_sha256"] == cal.OBSERVATION_PARAMETER_REGISTRY_SHA256
    assert C.semantic_sha256(parts) == c.contract_sha256

    moved = dict(parts)
    moved["observation_parameter_registry_version"] = "PS_V3_1_1_OBSERVATION_PARAMETERS_V2"
    assert C.semantic_sha256(moved) != c.contract_sha256


def test_r3_old_contract_cannot_be_reinterpreted_under_other_registry_identity():
    c = _contract()
    with pytest.raises(cal.CalibrationError):
        replace(
            c,
            observation_parameter_registry_version="PS_V3_1_1_OBSERVATION_PARAMETERS_V2",
        )
    with pytest.raises(cal.CalibrationError):
        replace(c, observation_parameter_registry_sha256="0" * 64)


class _ListProbe(list):
    calls = []

    def __iter__(self):
        _ListProbe.calls.append("iter")
        raise RuntimeError("payload iterator executed")


class _TupleProbe(tuple):
    calls = []

    def __iter__(self):
        _TupleProbe.calls.append("iter")
        raise RuntimeError("payload iterator executed")


def test_r4_rejects_container_subclasses_before_payload_iteration():
    _ListProbe.calls.clear()
    with pytest.raises(cal.CalibrationError):
        cal.RealismContract.frozen(
            metric_bands=_ListProbe([("OBS_DEPTH", (0.2, 0.8))]),
            adjustable_observation_parameters=("OBS_DEPTH_SCALE",),
            max_iterations=1,
            version_family_sha256=sha256(b"list-probe").hexdigest(),
            authority_scope="SYNTH_DEBUG_ONLY",
        )
    assert _ListProbe.calls == []

    _TupleProbe.calls.clear()
    bad = _TupleProbe(("OBS_DEPTH_SCALE",))
    with pytest.raises(cal.CalibrationError):
        cal.RealismContract.frozen(
            metric_bands=(("OBS_DEPTH", (0.2, 0.8)),),
            adjustable_observation_parameters=bad,
            max_iterations=1,
            version_family_sha256=sha256(b"tuple-probe").hexdigest(),
            authority_scope="SYNTH_DEBUG_ONLY",
        )
    assert _TupleProbe.calls == []


def test_no_semantics_or_real_calibration_promotion():
    c = _contract()
    assert cal.OBSERVATION_PARAMETER_SEMANTICS_BOUND is False
    assert cal._AUTHENTICATED_CALIBRATION_REGISTRY == frozenset()
    assert c.authority_scope == "SYNTH_DEBUG_ONLY"
