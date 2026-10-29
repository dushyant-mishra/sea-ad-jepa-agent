"""Independent ChatGPT review probes for Macha PR #486 exact head.

Synthetic/fixture-only tests. These do not authenticate real calibration, human
biology, target truth, or training authority. The immutable #480 reviewer suite
remains the historical acceptance floor; this file adds attacks on the repair.
"""
from __future__ import annotations

from dataclasses import fields as dataclass_fields
from hashlib import sha256
import math

import pytest

from scripts.production_synthetic import calibration_v1 as cal
from scripts.production_synthetic import canonical_v1 as C


_U = sha256(b"chatgpt-486-independent-universe").hexdigest()


def _universe(pilot, full):
    return cal.validate_address_universe_agnostic(
        "OBSERVATION_MEAN_DEPTH",
        pilot,
        full,
        pilot_n_addresses=96,
        full_n_addresses=41238,
        full_universe_sha256=_U,
        expected_full_universe_sha256=_U,
    )


def _contract(*, version_family_sha256=None):
    return cal.RealismContract.frozen(
        metric_bands=(("OBS_DEPTH", (0.2, 0.8)),),
        adjustable_observation_parameters=("OBS_DEPTH_SCALE",),
        max_iterations=1,
        version_family_sha256=version_family_sha256 or sha256(b"family").hexdigest(),
        authority_scope="SYNTH_DEBUG_ONLY",
    )


def test_green_480_large_integer_alias_is_closed():
    with pytest.raises(cal.CalibrationError):
        _universe({"U": 2**53}, {"U": 2**53 + 1})


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, True, False])
def test_green_nonfinite_and_bool_universe_values_fail_closed(bad):
    with pytest.raises(cal.CalibrationError):
        _universe({"U": bad}, {"U": bad})


@pytest.mark.parametrize(
    "a,b,accepted",
    [
        (7, 7.0, True),
        (0.0, -0.0, True),
        (2**53, float(2**53), True),
        (2**53 + 1, float(2**53), False),
        (2**60, 2**60 + 1, False),
    ],
)
def test_green_cross_type_numeric_comparison_is_mathematical_not_binary64_alias(a, b, accepted):
    if accepted:
        assert _universe({"U": a}, {"U": b}).status == cal.UNIVERSE_FIXTURE_ONLY
    else:
        with pytest.raises(cal.CalibrationError):
            _universe({"U": a}, {"U": b})


class _Key(str):
    calls = []

    def __hash__(self):
        _Key.calls.append("hash")
        return str.__hash__(self)

    def __eq__(self, other):
        _Key.calls.append("eq")
        raise RuntimeError("payload key comparison executed")


def test_green_key_subclass_rejected_before_validator_hash_or_equality():
    pilot = {_Key("U"): 1}
    _Key.calls.clear()  # ignore dict construction
    try:
        _universe(pilot, {"U": 1})
        escaped = "returned"
    except cal.CalibrationError:
        escaped = None
    except BaseException as exc:  # noqa: BLE001 - escape itself is the finding
        escaped = type(exc).__qualname__
    assert escaped is None
    assert _Key.calls == []


def test_green_registry_rows_are_closed_versioned_and_self_hashed():
    rows = cal.OBSERVATION_PARAMETER_REGISTRY_ROWS
    expected = C.semantic_sha256(
        [{"name": n, "quantity_family": q, "spec_clause": s} for n, q, s in rows]
    )
    assert type(rows) is tuple
    assert cal.OBSERVATION_PARAMETER_REGISTRY_VERSION == "PS_V3_1_1_OBSERVATION_PARAMETERS_V1"
    assert cal.OBSERVATION_PARAMETER_REGISTRY_SHA256 == expected
    assert cal.OBSERVATION_PARAMETER_SEMANTICS_BOUND is False
    assert cal._AUTHENTICATED_CALIBRATION_REGISTRY == frozenset()


def test_red_r3_realism_contract_identity_must_bind_registry_identity():
    """A contract allowing named tunables must identify the registry that authorized them.

    #486 publishes registry VERSION/SHA constants, but RealismContract and its
    digest do not contain either. A later registry revision can therefore keep
    the same parameter name while changing its quantity-family/spec mapping
    without changing the old contract identity.
    """
    names = {f.name for f in dataclass_fields(cal.RealismContract)}
    assert {
        "observation_parameter_registry_version",
        "observation_parameter_registry_sha256",
    } <= names


class _PayloadClassProbe:
    calls = []

    @property
    def __class__(self):
        _PayloadClassProbe.calls.append("__class__")
        raise RuntimeError("payload-controlled __class__ executed")


def test_red_r4_frozen_constructor_must_validate_exact_types_before_canonicalization():
    """Public constructor must reject hostile payload types without executing payload code."""
    probe = _PayloadClassProbe()
    _PayloadClassProbe.calls.clear()
    try:
        _contract(version_family_sha256=probe)
        escaped = "returned"
    except cal.CalibrationError:
        escaped = None
    except BaseException as exc:  # noqa: BLE001 - escape itself is the finding
        escaped = type(exc).__qualname__

    if escaped is not None or _PayloadClassProbe.calls:
        pytest.fail(
            f"escape={escaped} payload_calls={_PayloadClassProbe.calls}",
            pytrace=False,
        )


def test_green_no_semantics_or_real_calibration_promotion_is_claimed():
    assert cal.OBSERVATION_PARAMETER_SEMANTICS_BOUND is False
    assert cal._AUTHENTICATED_CALIBRATION_REGISTRY == frozenset()
    c = _contract()
    assert c.authority_scope == "SYNTH_DEBUG_ONLY"
