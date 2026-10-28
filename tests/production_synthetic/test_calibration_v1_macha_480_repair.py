"""Macha author repair of ChatGPT #480 R1/R2 on PS Task 3 (#437): self-audit cases.

Synthetic only. The #480 reviewer file stays byte-identical and is the
acceptance criterion; these cases attack the repair itself. Passing them is
mechanics, not calibration authority: the registry names observation-side
quantity families from the frozen V3.1.1 text, it does not bind a generator's
operator semantics (PS Task 4 is absent).
"""
from __future__ import annotations

from hashlib import sha256

import pytest

from scripts.production_synthetic import calibration_v1 as cal
from scripts.production_synthetic import canonical_v1 as C

_U = sha256(b"synthetic-universe").hexdigest()


def _universe(pilot, full):
    return cal.validate_address_universe_agnostic(
        "OBSERVATION_MEAN_DEPTH", pilot, full, pilot_n_addresses=96, full_n_addresses=41238,
        full_universe_sha256=_U, expected_full_universe_sha256=_U)


@pytest.mark.parametrize("a,b", [(2**60, 2**60 + 1), (0.1 + 0.2, 0.3), (2**53 + 1, float(2**53))])
def test_distinct_numbers_are_never_equal_witnesses(a, b):
    with pytest.raises(cal.CalibrationError):
        _universe({"U": a}, {"U": b})


@pytest.mark.parametrize("a,b", [(7, 7), (1, 1.0), (0.0, -0.0), (2**53, float(2**53)), (0.25, 0.25)])
def test_mathematically_equal_numbers_remain_equal_witnesses(a, b):
    assert _universe({"U": a}, {"U": b}).status == cal.UNIVERSE_FIXTURE_ONLY


class _Meta(type):
    calls: list = []

    def __eq__(cls, other):
        _Meta.calls.append("eq")
        raise RuntimeError("payload-chosen exception")

    __hash__ = type.__hash__


class _Hostile(metaclass=_Meta):
    pass


def test_numeric_check_runs_no_payload_type_code():
    """`type(x) not in (int, float)` compares the payload's type and runs a
    payload metaclass __eq__; identity dispatch does not."""
    _Meta.calls.clear()
    try:
        _universe({"U": _Hostile()}, {"U": 1})
        escaped = "returned"
    except cal.CalibrationError:
        escaped = None
    except BaseException as exc:  # noqa: BLE001 - the escape is the finding
        escaped = type(exc).__qualname__
    if escaped or _Meta.calls:
        pytest.fail(f"escape={escaped} payload_calls={len(_Meta.calls)}", pytrace=False)


class _KeyEq(str):
    """Round 2: a str-subclass key whose hash/eq run during set() or dict lookup."""

    calls: list = []

    def __hash__(self):
        _KeyEq.calls.append("hash")
        return str.__hash__(self)

    def __eq__(self, other):
        _KeyEq.calls.append("eq")
        raise RuntimeError("payload-chosen exception")


@pytest.mark.parametrize("side", ["pilot", "full"])
def test_round2_universe_keys_are_type_checked_before_any_hash_or_comparison(side):
    pilot, full = {"U": 1}, {"U": 1}
    target = pilot if side == "pilot" else full
    del target["U"]
    target[_KeyEq("U")] = 1  # insertion itself hashes the key; count only the validator's calls
    _KeyEq.calls.clear()
    try:
        _universe(pilot, full)
        escaped = "returned"
    except cal.CalibrationError:
        escaped = None
    except BaseException as exc:  # noqa: BLE001 - the escape is the finding
        escaped = type(exc).__qualname__
    if escaped or _KeyEq.calls:
        pytest.fail(f"escape={escaped} payload_calls={len(_KeyEq.calls)}", pytrace=False)


def _firewall_call(protected):
    raw = b"fixture-observation-statistics-not-real-human-data"
    h = sha256(raw).hexdigest()
    artifact = cal.CalibrationArtifact(
        h, "SYNTH_ONLY", ("FAKE_FIT_A",), "CALIBRATION_FIT",
        "OBSERVATION_DEPTH", (), "AUTHENTICATED_EMPIRICAL_CALIBRATION")
    return lambda: cal.validate_calibration_firewall(
        artifact, raw_bytes=raw, independently_pinned_sha256=h, expected_source_scope="SYNTH_ONLY",
        eligible_fit_donors=("FAKE_FIT_A",), protected_partitions=protected)


def _realism_call(metrics):
    c = _contract(("OBS_DEPTH_SCALE",))
    s = cal.RealismState.initial(c)
    return lambda: cal.advance_realism_iteration(
        c, s, version_sha256=sha256(b"round3").hexdigest(), metrics=metrics)


def _round3(route):
    if route == "protected_partitions":
        roles = {"VALIDATION": ("FAKE_V",), "ORACLE": ("FAKE_O",), "RESERVED": ("FAKE_R",)}
        roles[_KeyEq("DEVELOPMENT")] = ("FAKE_D",)
        return _firewall_call(roles)
    if route == "precision_targets":
        t = cal.PrecisionTarget(epsilon=0.1, alpha=0.01)
        targets = {_KeyEq("donors"): t, "worlds": t, "nulls": t}  # built (and hashed) before the call
        return lambda: cal.derive_budget_from_precision(targets)
    return _realism_call({_KeyEq("OBS_DEPTH"): 0.5})


@pytest.mark.parametrize("route", ["protected_partitions", "precision_targets", "realism_metrics"])
def test_round3_other_caller_mappings_check_key_types_before_hashing(route):
    """Same class as round 2 on the module's other caller-keyed mappings:
    set(mapping) hashes and compares keys before any exact-str check."""
    call = _round3(route)
    _KeyEq.calls.clear()
    try:
        call()
        escaped = "returned"
    except cal.CalibrationError:
        escaped = None
    except BaseException as exc:  # noqa: BLE001 - the escape is the finding
        escaped = type(exc).__qualname__
    if escaped or _KeyEq.calls:
        pytest.fail(f"escape={escaped} payload_calls={len(_KeyEq.calls)}", pytrace=False)


def _contract(params):
    return cal.RealismContract.frozen(
        metric_bands=(("OBS_DEPTH", (0.2, 0.8)),), adjustable_observation_parameters=params,
        max_iterations=1, version_family_sha256=sha256(repr(params).encode()).hexdigest(),
        authority_scope="SYNTH_DEBUG_ONLY")


def test_every_registered_observation_parameter_is_accepted():
    for name in sorted(cal.OBSERVATION_PARAMETER_REGISTRY):
        assert _contract((name,)).adjustable_observation_parameters == (name,)
    assert _contract(tuple(sorted(cal.OBSERVATION_PARAMETER_REGISTRY)))


class _StrSub(str):
    pass


@pytest.mark.parametrize("name", [
    "OBS_DISEASE_PREVALENCE", "OBS_TARGET_WINNER", "OBS_LATENT_PROGRAM_EFFECT",
    "OBS_RARE_STATE_FRACTION", "OBS_DEPTH",  # a realism metric name, not a parameter
    "OBS_DEPTH_SCALE ", " OBS_DEPTH_SCALE", "obs_depth_scale", "OBS_DEPTH_SCALE​",
    "OBS_DEPTH_SCALE\n", "OBS_",
])
def test_unregistered_or_near_miss_names_are_refused(name):
    with pytest.raises(cal.CalibrationError):
        _contract((name,))


def test_registered_name_as_str_subclass_is_refused():
    with pytest.raises(cal.CalibrationError):
        _contract((_StrSub("OBS_DEPTH_SCALE"),))


def test_registry_is_closed_source_bound_and_identified():
    reg, rows = cal.OBSERVATION_PARAMETER_REGISTRY, cal.OBSERVATION_PARAMETER_REGISTRY_ROWS
    assert type(reg) is frozenset and type(rows) is tuple
    assert [r[0] for r in rows] == sorted(reg) and len(rows) == len(reg) == 7
    clause = ("docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-"
              "v3-1-consolidated-corrective-amendment.md#L78")
    assert all(type(r) is tuple and len(r) == 3 and r[2] == clause for r in rows)
    assert {"OBS_DEPTH_SCALE", "OBS_DETECTION_SCALE"} <= reg
    digest_rows = [{"name": n, "quantity_family": q, "spec_clause": s} for n, q, s in rows]
    assert cal.OBSERVATION_PARAMETER_REGISTRY_SHA256 == C.semantic_sha256(digest_rows)
    assert cal.OBSERVATION_PARAMETER_REGISTRY_VERSION == "PS_V3_1_1_OBSERVATION_PARAMETERS_V1"
    assert cal.OBSERVATION_PARAMETER_SEMANTICS_BOUND is False
