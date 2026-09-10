"""V2 must be the one authorized change, and nothing more.

The owner froze exactly one move: `final_trace_scale` from exact-scalar equality
to at most one float64 ULP, on the algebraic ground that `final_lambda` is that
value times an exact power of ten and already carried the one-ULP class. Every
other rule is inherited.

A policy module is the easiest place for an unauthorized second change to hide,
because a widened tolerance produces a report that looks exactly like an
authorized one. So these tests check the derivation itself, that V2 did not
widen the class it joined, and that V1 still refuses what it refused before.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np
import pytest

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts" / "v4"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import t0_replay_equivalence_v1 as v1  # noqa: E402
import t0_replay_equivalence_v2 as v2  # noqa: E402

MOVED = "final_trace_scale"


def _fit():
    """The frozen fit shape, with the real observed trace scale."""
    return {
        "beta": np.array([1.0, -2.0, 1e-12], dtype=np.float64),
        "mu": np.array([0.1, 0.2, 0.3], dtype=np.float64),
        "sigma": np.array([0.8, 1.2, 2.0], dtype=np.float64),
        "decision_gene_mask": np.array([True, False, True]),
        "cv_mse_by_multiplier": np.linspace(0.1, 1.7, 17, dtype=np.float64),
        "multiplier_exponents": np.linspace(-6.0, 2.0, 17, dtype=np.float64),
        "canonical_donor_order": np.array(["d1", "d2", "d3"], dtype=object),
        "selected_multiplier_index": 16,
        "selected_multiplier_exponent": 2.0,
        "final_lambda": np.float64(2360764.285714286),
        "final_trace_scale": np.float64(23607.64285714286),
        "response_residual_sd": np.float64(1.2245513389820333),
        "discovery_age_center": np.float64(80.0),
    }


# --- the derivation --------------------------------------------------------

def test_v2_is_exactly_one_authorized_change():
    report = v2.verify_single_policy_change()
    assert report["authorized_change_count"] == 1
    assert report["reclassified_fields"] == [MOVED]
    assert report["authorized_change"] == {
        "field": MOVED, "from": "exact_scalar",
        "to": "at_most_n_ulp", "max_ulp": 1}
    assert report["every_other_policy_element_identical_to_v1"] is True
    assert report["classified_field_set_unchanged"] is True


def test_v2_inherits_every_other_policy_element():
    assert v2.FLOAT_POLICY == v1.FLOAT_POLICY
    assert v2.EXACT_ARRAY_FIELDS == tuple(v1.EXACT_ARRAY_FIELDS)
    assert v2.REQUIRED_FLOAT_DTYPE == v1.REQUIRED_FLOAT_DTYPE
    assert v2.STATE_PRIMARY_FLOAT_RTOL == v1.STATE_PRIMARY_FLOAT_RTOL
    assert v2.STATE_PRIMARY_EXACT_FIELDS == tuple(v1.STATE_PRIMARY_EXACT_FIELDS)
    # The one-ULP budgets V1 already had are unchanged in value.
    for field, budget in v1.ULP_POLICY.items():
        assert v2.ULP_POLICY[field] == budget


def test_v1_is_not_mutated_by_importing_v2():
    """V1 and its STOP have to stay exactly what they were."""
    assert MOVED in v1.EXACT_SCALAR_FIELDS
    assert MOVED not in v1.ULP_POLICY


def test_the_policy_digest_binds_the_tolerances():
    assert len(v2.policy_digest()) == 64
    assert v2.verify_single_policy_change()["policy_sha256"] == v2.policy_digest()


# --- the moved field -------------------------------------------------------

def test_v2_accepts_one_ulp_on_the_moved_field():
    """The observed V1 STOP, now inside the authorized class."""
    a = _fit(); b = copy.deepcopy(a)
    b[MOVED] = np.nextafter(a[MOVED], np.inf)
    report = v2.compare_fit_equivalence(a, b)
    assert report["equivalent"] is True
    assert report["observed_ulp_distance"][MOVED] == 1


def test_v2_still_refuses_two_ulp_on_the_moved_field():
    """V2 joins the one-ULP class; it does not widen it."""
    a = _fit(); b = copy.deepcopy(a)
    stepped = np.nextafter(np.nextafter(a[MOVED], np.inf), np.inf)
    b[MOVED] = stepped
    with pytest.raises(v2.ReplayEquivalenceError):
        v2.compare_fit_equivalence(a, b)


def test_v1_still_refuses_one_ulp_on_the_moved_field():
    """The preserved V1 STOP must remain reproducible from V1 itself."""
    a = _fit(); b = copy.deepcopy(a)
    b[MOVED] = np.nextafter(a[MOVED], np.inf)
    with pytest.raises(v1.ReplayEquivalenceError) as caught:
        v1.compare_fit_equivalence(a, b)
    assert MOVED in str(caught.value)


# --- everything V1 refused, V2 still refuses -------------------------------

def test_v2_keeps_the_dtype_guard():
    a = _fit(); b = copy.deepcopy(a)
    b["beta"] = a["beta"].astype(np.float32)
    with pytest.raises(v2.ReplayEquivalenceError) as caught:
        v2.compare_fit_equivalence(a, b)
    assert "declared dtype differs" in str(caught.value)


def test_v2_keeps_the_dtype_guard_on_the_moved_field():
    """Now budgeted, so it must also require float64."""
    a = _fit(); b = copy.deepcopy(a)
    b[MOVED] = np.float32(a[MOVED])
    with pytest.raises(v2.ReplayEquivalenceError):
        v2.compare_fit_equivalence(a, b)


def test_v2_keeps_the_beta_budget():
    a = _fit(); b = copy.deepcopy(a)
    b["beta"] = a["beta"] * (1.0 + 1e-9)
    with pytest.raises(v2.ReplayEquivalenceError) as caught:
        v2.compare_fit_equivalence(a, b)
    assert "beta" in str(caught.value)


def test_v2_keeps_the_remaining_exact_scalars_exact():
    for field in ("selected_multiplier_index", "selected_multiplier_exponent",
                  "discovery_age_center"):
        a = _fit(); b = copy.deepcopy(a)
        b[field] = np.nextafter(np.float64(a[field]), np.inf) \
            if isinstance(a[field], float) else a[field] + 1
        with pytest.raises(v2.ReplayEquivalenceError):
            v2.compare_fit_equivalence(a, b)


def test_v2_keeps_the_exact_arrays_exact():
    a = _fit(); b = copy.deepcopy(a)
    # One ULP on a single element. A relative nudge of 1e-16 would have been
    # below float64 epsilon and left the array untouched, which is how this
    # test first passed without testing anything.
    perturbed = a["mu"].copy()
    perturbed[0] = np.nextafter(perturbed[0], np.inf)
    assert not np.array_equal(perturbed, a["mu"])
    b["mu"] = perturbed
    with pytest.raises(v2.ReplayEquivalenceError):
        v2.compare_fit_equivalence(a, b)


# --- an unauthorized second change must be refused -------------------------

def test_a_second_reclassification_is_refused(monkeypatch):
    """The check has to be able to fail, or it certifies anything."""
    tampered = tuple(f for f in v2.EXACT_SCALAR_FIELDS
                     if f != "discovery_age_center")
    monkeypatch.setattr(v2, "EXACT_SCALAR_FIELDS", tampered)
    monkeypatch.setattr(v2, "ULP_POLICY",
                        {**v2.ULP_POLICY, "discovery_age_center": 1})
    with pytest.raises(v2.ReplayEquivalenceError) as caught:
        v2.verify_single_policy_change()
    assert "more than one field" in str(caught.value) \
        or "reclassified fields" in str(caught.value)


def test_a_widened_ulp_budget_is_refused(monkeypatch):
    monkeypatch.setattr(v2, "ULP_POLICY", {**v2.ULP_POLICY, MOVED: 4})
    with pytest.raises(v2.ReplayEquivalenceError) as caught:
        v2.verify_single_policy_change()
    assert "max_ulp" in str(caught.value)


def test_a_widened_float_budget_is_refused(monkeypatch):
    widened = {f: dict(p) for f, p in v2.FLOAT_POLICY.items()}
    widened["beta"]["rtol"] = 1e-6
    monkeypatch.setattr(v2, "FLOAT_POLICY", widened)
    with pytest.raises(v2.ReplayEquivalenceError) as caught:
        v2.verify_single_policy_change()
    assert "float policy changed" in str(caught.value)


def test_dropping_the_field_instead_of_moving_it_is_refused(monkeypatch):
    """Removing coverage would also produce a passing replay."""
    monkeypatch.setattr(v2, "ULP_POLICY", dict(v1.ULP_POLICY))
    with pytest.raises(v2.ReplayEquivalenceError) as caught:
        v2.verify_single_policy_change()
    assert "classified fields changed" in str(caught.value) \
        or "does not carry max_ulp" in str(caught.value)
