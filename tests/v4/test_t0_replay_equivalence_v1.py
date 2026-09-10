import copy
import numpy as np
import pytest

import sys
from pathlib import Path

# The lane's modules import one another by bare name, the way the frozen V20
# package does, so `scripts/v4` has to be importable. Resolved here rather than
# left to an ambient PYTHONPATH: without it a clean clone reports collection
# errors instead of running these tests, which is the failure mode where a
# suite looks absent rather than red.
_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts" / "v4"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from t0_replay_equivalence_v1 import (
    compare_fit_equivalence,
    compare_decision_equivalence,
    ReplayEquivalenceError,
)


def _fit():
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
        "final_trace_scale": np.float64(123.0),
        "response_residual_sd": np.float64(1.2245513389820333),
        "discovery_age_center": np.float64(80.0),
    }


def _decision():
    return {
        "state_terminal": "BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL",
        "tail_terminal": "RARE_TAIL_UNDERDETERMINED_MEASUREMENT",
        "state_primary": {
            "beta": 124.94507515835764,
            "estimable": True,
            "hc3_se": 65.48932245523241,
            "n": 18,
            "p_full": 5,
            "p_lower": 0.9791,
            "p_reduced": 4,
            "p_upper": 0.021,
            "permutations": 9999,
            "residual_df": 13,
            "t_observed": 1.9078694125102356,
            "null_t": "[frozen-string-representation]",
        },
    }


def test_fit_accepts_documented_cross_stack_scale_but_reports_it():
    a = _fit(); b = copy.deepcopy(a)
    b["beta"] = a["beta"] * (1.0 + 2.8e-12)
    b["sigma"] = a["sigma"] * (1.0 + 8.2e-16)
    b["cv_mse_by_multiplier"] = a["cv_mse_by_multiplier"] * (1.0 + 2.6e-15)
    b["final_lambda"] = np.nextafter(a["final_lambda"], np.inf)
    b["response_residual_sd"] = np.nextafter(a["response_residual_sd"], np.inf)
    report = compare_fit_equivalence(a, b)
    assert report["equivalent"] is True
    assert report["float_policy"]["beta"]["rtol"] == 1e-11
    assert report["float_policy"]["sigma"]["rtol"] == 1e-14
    assert report["float_policy"]["cv_mse_by_multiplier"]["rtol"] == 1e-14
    assert report["ulp_policy"]["final_lambda"] == 1
    assert report["ulp_policy"]["response_residual_sd"] == 1


def test_fit_rejects_beta_outside_frozen_budget():
    a = _fit(); b = copy.deepcopy(a)
    b["beta"] = a["beta"].copy(); b["beta"][0] *= 1.0 + 2e-11
    with pytest.raises(ReplayEquivalenceError, match="beta"):
        compare_fit_equivalence(a, b)


def test_fit_rejects_two_ulp_scalar_move():
    a = _fit(); b = copy.deepcopy(a)
    x = np.nextafter(a["final_lambda"], np.inf)
    b["final_lambda"] = np.nextafter(x, np.inf)
    with pytest.raises(ReplayEquivalenceError, match="final_lambda"):
        compare_fit_equivalence(a, b)


def test_fit_requires_exact_discrete_and_exact_mu():
    a = _fit(); b = copy.deepcopy(a)
    b["decision_gene_mask"][1] = True
    with pytest.raises(ReplayEquivalenceError, match="decision_gene_mask"):
        compare_fit_equivalence(a, b)
    b = copy.deepcopy(a); b["mu"][0] = np.nextafter(b["mu"][0], np.inf)
    with pytest.raises(ReplayEquivalenceError, match="mu"):
        compare_fit_equivalence(a, b)


def test_fit_rejects_nan_even_if_both_sides_nan():
    a = _fit(); b = copy.deepcopy(a)
    a["sigma"][0] = np.nan; b["sigma"][0] = np.nan
    with pytest.raises(ReplayEquivalenceError, match="finite"):
        compare_fit_equivalence(a, b)


def test_decision_requires_exact_terminals_and_discrete_fields():
    a = _decision(); b = copy.deepcopy(a)
    b["state_terminal"] = "OTHER"
    with pytest.raises(ReplayEquivalenceError, match="state_terminal"):
        compare_decision_equivalence(a, b)
    b = copy.deepcopy(a); b["state_primary"]["n"] = 17
    with pytest.raises(ReplayEquivalenceError, match="state_primary.n"):
        compare_decision_equivalence(a, b)


def test_decision_allows_only_tight_numeric_drift_in_state_primary():
    a = _decision(); b = copy.deepcopy(a)
    b["state_primary"]["beta"] *= 1.0 + 8e-13
    b["state_primary"]["hc3_se"] *= 1.0 - 8e-13
    b["state_primary"]["t_observed"] *= 1.0 + 8e-13
    report = compare_decision_equivalence(a, b)
    assert report["equivalent"] is True
    assert report["state_primary_float_rtol"] == 1e-12


def test_decision_rejects_numeric_drift_beyond_one_e_minus_12():
    a = _decision(); b = copy.deepcopy(a)
    b["state_primary"]["beta"] *= 1.0 + 2e-12
    with pytest.raises(ReplayEquivalenceError, match="state_primary.beta"):
        compare_decision_equivalence(a, b)


def test_fit_rejects_key_set_drift():
    a = _fit(); b = copy.deepcopy(a)
    b["unexpected"] = 1
    with pytest.raises(ReplayEquivalenceError, match="key set differs"):
        compare_fit_equivalence(a, b)


def test_beta_near_zero_uses_tiny_absolute_budget_only():
    a = _fit(); b = copy.deepcopy(a)
    # At exactly zero relative tolerance cannot help. A perturbation below the
    # frozen 1e-20 absolute budget is allowed; a larger one is not.
    a["beta"][2] = 0.0
    b["beta"][2] = 0.5e-20
    assert compare_fit_equivalence(a, b)["equivalent"] is True
    b["beta"][2] = 2.0e-20
    with pytest.raises(ReplayEquivalenceError, match="beta"):
        compare_fit_equivalence(a, b)


def test_decision_p_values_are_exact_not_tolerant():
    a = _decision(); b = copy.deepcopy(a)
    b["state_primary"]["p_upper"] = np.nextafter(np.float64(a["state_primary"]["p_upper"]), np.inf).item()
    with pytest.raises(ReplayEquivalenceError, match="state_primary.p_upper"):
        compare_decision_equivalence(a, b)


def test_decision_rejects_state_primary_key_drift():
    a = _decision(); b = copy.deepcopy(a)
    del b["state_primary"]["residual_df"]
    with pytest.raises(ReplayEquivalenceError, match="key set differs"):
        compare_decision_equivalence(a, b)


def test_target_wrapper_requires_exact_provenance(monkeypatch):
    import sys
    import types
    from t0_replay_equivalence_v1 import verify_target_v2_replay_equivalent

    frozen = {"fit": _fit(), "provenance": {"root_sha256": "A"}, "package_root_sha256": "P"}
    recomputed = {"fit": _fit(), "provenance": {"root_sha256": "B"}, "package_root_sha256": "Q"}

    fake_frozen_mod = types.SimpleNamespace(
        load_target_v2=lambda target_dir, feature_split_csv: frozen,
        fit_discovery_target_v2=lambda **kwargs: recomputed,
    )
    fake_stage2a = types.SimpleNamespace(_frozen=lambda name: fake_frozen_mod)
    monkeypatch.setitem(sys.modules, "t0_stage2a_pre_at8_gate_v1", fake_stage2a)

    with pytest.raises(ReplayEquivalenceError, match="provenance"):
        verify_target_v2_replay_equivalent("unused", feature_split_csv="unused.csv")


def test_target_wrapper_emits_provenance_roots_when_equivalent(monkeypatch):
    import sys
    import types
    from t0_replay_equivalence_v1 import verify_target_v2_replay_equivalent

    frozen = {"fit": _fit(), "provenance": {"root_sha256": "A"}, "package_root_sha256": "P"}
    recomputed = {"fit": copy.deepcopy(frozen["fit"]), "provenance": {"root_sha256": "A"}, "package_root_sha256": "IGNORED"}
    fake_frozen_mod = types.SimpleNamespace(
        load_target_v2=lambda target_dir, feature_split_csv: frozen,
        fit_discovery_target_v2=lambda **kwargs: recomputed,
    )
    fake_stage2a = types.SimpleNamespace(_frozen=lambda name: fake_frozen_mod)
    monkeypatch.setitem(sys.modules, "t0_stage2a_pre_at8_gate_v1", fake_stage2a)

    result = verify_target_v2_replay_equivalent("unused", feature_split_csv="unused.csv")
    assert result["verified"] is True
    assert result["package_root_sha256"] == "P"
    assert result["discovery_provenance_root"] == "A"


# --- the dtype guard -------------------------------------------------------
# A tolerance is only meaningful between arrays of the same precision. Before
# the guard, `_as_finite_float_array` coerced with `np.asarray(x, dtype=float64)`,
# so a lower-precision recomputation was upcast before anything looked at it.

def test_a_float32_recomputation_inside_the_budget_is_refused():
    """The masquerade the guard exists to stop.

    These float32 values fall well inside the frozen beta budget, so without a
    dtype check this would be reported as an acceptable float64 replay of a
    computation that was never done at float64.
    """
    a = _fit(); b = copy.deepcopy(a)
    b["beta"] = a["beta"].astype(np.float32)
    with pytest.raises(ReplayEquivalenceError) as caught:
        compare_fit_equivalence(a, b)
    assert "declared dtype differs" in str(caught.value)
    assert "float32" in str(caught.value)


def test_matching_but_lower_precision_dtypes_are_still_refused():
    """Equal dtypes are not enough when the budget was measured at float64.

    Two float32 arrays agreeing within 1e-11 relative say nothing about a
    float64 replay, so the budgeted fields require float64 rather than merely
    agreement.
    """
    a = _fit(); b = copy.deepcopy(a)
    a["sigma"] = a["sigma"].astype(np.float32)
    b["sigma"] = b["sigma"].astype(np.float32)
    with pytest.raises(ReplayEquivalenceError) as caught:
        compare_fit_equivalence(a, b)
    assert "must be float64" in str(caught.value)


def test_an_exact_array_of_a_different_dtype_with_equal_values_is_refused():
    """`np.array_equal` compares values, so the mask needs its own dtype check."""
    a = _fit(); b = copy.deepcopy(a)
    b["decision_gene_mask"] = a["decision_gene_mask"].astype(np.float64)
    assert np.array_equal(np.asarray(a["decision_gene_mask"]),
                          np.asarray(b["decision_gene_mask"]))
    with pytest.raises(ReplayEquivalenceError) as caught:
        compare_fit_equivalence(a, b)
    assert "declared dtype differs" in str(caught.value)


def test_an_exact_scalar_of_a_different_dtype_is_refused():
    a = _fit(); b = copy.deepcopy(a)
    b["selected_multiplier_index"] = np.int32(a["selected_multiplier_index"])
    assert a["selected_multiplier_index"] == b["selected_multiplier_index"]
    with pytest.raises(ReplayEquivalenceError):
        compare_fit_equivalence(a, b)


def test_a_one_ulp_scalar_of_a_different_dtype_is_refused():
    a = _fit(); b = copy.deepcopy(a)
    b["final_lambda"] = np.float32(a["final_lambda"])
    with pytest.raises(ReplayEquivalenceError):
        compare_fit_equivalence(a, b)


def test_the_report_records_the_declared_dtypes():
    """The guard must be visible in the record, not merely enforced."""
    a = _fit(); b = copy.deepcopy(a)
    report = compare_fit_equivalence(a, b)
    guard = report["dtype_guard"]
    assert guard["required_float_dtype"] == "float64"
    assert guard["declared_dtypes_matched"] is True
    assert guard["exact_array_dtypes"]["decision_gene_mask"] == "bool"
    assert guard["exact_scalar_dtypes"]["selected_multiplier_index"] == "int64"
    assert report["observed"]["beta"]["dtype"] == "float64"


# --- null_t: a verdict rather than a traceback -----------------------------
# The committed record stores `null_t` as NumPy's truncated repr, because the
# decision writer serialises with `default=str`. A live replay holds the array.
# Comparing those directly evaluates elementwise and raises.

def test_a_live_array_null_t_returns_a_verdict_instead_of_raising():
    committed = _decision()
    live = copy.deepcopy(committed)
    null = np.array([-0.96497236, -0.08234167, -0.93844393])
    committed["state_primary"]["null_t"] = str(null)
    live["state_primary"]["null_t"] = null
    report = compare_decision_equivalence(committed, live)
    assert report["equivalent"] is True
    assert report["exact_fields_compared_in_record_form"] is True


def test_a_null_t_that_differs_in_record_form_is_refused():
    committed = _decision()
    live = copy.deepcopy(committed)
    committed["state_primary"]["null_t"] = str(np.array([-0.96, -0.08]))
    live["state_primary"]["null_t"] = np.array([-0.96, 0.42])
    with pytest.raises(ReplayEquivalenceError) as caught:
        compare_decision_equivalence(committed, live)
    assert "null_t" in str(caught.value)


def test_the_null_representation_limitation_is_stated_in_the_report():
    """The check cannot see values the artifact never recorded; say so."""
    report = compare_decision_equivalence(_decision(), _decision())
    assert "truncated repr" in report["null_representation_limitation"]
