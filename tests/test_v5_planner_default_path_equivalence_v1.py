"""The frozen planner and its successor must compute identical Audit-B numbers.

Phase-IV binds ``full104_masking_streaming_executor_v1.py`` by SHA-256. PR #144
changed those bytes, so the binding broke. A successor binding may only be
issued if the change is genuinely a version change rather than a change of what
the planner computes, and that question is settled by execution, not by reading
the diff.

Every test here has a counterpart that must fail, because an equivalence suite
with no mutation control proves nothing: if the comparison were blind, "equal"
would be the answer to every question.

Nothing here opens FULL104 expression, pathology, a terminal masking outcome,
D_shared or G5, and nothing authorizes training or Audit-B execution.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from sea_ad_jepa.v5 import planner_default_path_equivalence_v1 as E

ROOT = Path(__file__).resolve().parents[1]

SMALL = {
    "n_donors": 12,
    "cells_per_donor": 4,
    "n_addresses": 8,
    "n_folds": 3,
    "n_sources": 2,
    "seed": 0,
}


@pytest.fixture(scope="module")
def planners():
    frozen = E.load_planner(
        E.FROZEN_PLANNER_COPY,
        expected_sha256=E.FROZEN_PLANNER_SHA256,
        module_name="_frozen_planner_test",
    )
    successor = E.load_planner(
        E.SUCCESSOR_PLANNER_PATH,
        expected_sha256=E.SUCCESSOR_PLANNER_SHA256,
        module_name="_successor_planner_test",
    )
    return frozen, successor


# --------------------------------------------------------------------------- #
# The preserved original
# --------------------------------------------------------------------------- #


def test_the_original_frozen_planner_is_preserved_byte_for_byte():
    """The bytes Phase-IV bound are still recoverable, unmodified, in the repo."""
    assert E.FROZEN_PLANNER_COPY.is_file()
    assert E.sha256_file(E.FROZEN_PLANNER_COPY) == E.FROZEN_PLANNER_SHA256
    assert E.FROZEN_PLANNER_SHA256.startswith("143645becff6")


def test_the_preserved_copy_cannot_be_imported_or_collected_by_accident():
    """It is deliberately not a .py file, so no import or test collector sees it."""
    assert E.FROZEN_PLANNER_COPY.suffix == ".pysrc"


def test_loading_a_planner_with_the_wrong_expected_digest_is_refused():
    with pytest.raises(ValueError, match="planner digest mismatch"):
        E.load_planner(
            E.FROZEN_PLANNER_COPY,
            expected_sha256="0" * 64,
            module_name="_never_loaded",
        )


def test_the_successor_planner_is_pinned_to_the_exact_reviewed_bytes():
    """A further planner edit must re-run this check, not inherit its verdict."""
    assert E.sha256_file(E.SUCCESSOR_PLANNER_PATH) == E.SUCCESSOR_PLANNER_SHA256
    assert E.SUCCESSOR_PLANNER_SHA256.startswith("de2f019e2867")
    assert E.SUCCESSOR_PLANNER_SHA256 != E.FROZEN_PLANNER_SHA256


# --------------------------------------------------------------------------- #
# POSITIVE CONTROL: the real comparison
# --------------------------------------------------------------------------- #


def test_default_path_is_bitwise_identical(tmp_path, planners):
    frozen, successor = planners
    parameters, budget = E.default_parameters_and_budget()
    materials = E.build_stream_materials(tmp_path / "equal", **SMALL)
    result = E.compare_default_path(
        frozen=frozen,
        successor=successor,
        materials=materials,
        parameters=parameters,
        evidence_budget=budget,
        global_seed=20260926,
    )
    assert result["problems"] == []
    assert result["equivalent"] is True
    # A comparison of nothing would also report no problems.
    assert result["rows_compared"] > 0
    assert result["ridge_partner_calls_compared"] > 0
    assert sum(result["folds_compared"].values()) > 0


def test_the_shipped_receipt_matches_a_fresh_run(tmp_path, planners):
    """The committed receipt is reproducible, not a one-off artifact."""
    import json

    receipt_path = ROOT / (
        "analysis/v5_lane_c_planner_freeze_repair_20260926/evidence/"
        "PLANNER_DEFAULT_PATH_EQUIVALENCE_V1.json"
    )
    shipped = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert shipped["equivalent"] is True
    assert shipped["frozen_planner_sha256"] == E.FROZEN_PLANNER_SHA256
    assert shipped["successor_planner_sha256"] == E.SUCCESSOR_PLANNER_SHA256
    assert shipped["evidence_class"].startswith("SYNTHETIC_FIXTURE")
    assert shipped["full104_expression_read"] is False
    assert shipped["training_authorized"] is False

    fresh = E.run_equivalence(tmp_path / "fresh", geometries=(SMALL,))
    assert fresh["equivalent"] is True
    shipped_case = next(
        c for c in shipped["cases"] if c["geometry"] == SMALL
    )
    assert fresh["cases"][0]["rows_compared"] == shipped_case["rows_compared"]
    assert (
        fresh["cases"][0]["ridge_partner_calls_compared"]
        == shipped_case["ridge_partner_calls_compared"]
    )


# --------------------------------------------------------------------------- #
# MUTATION CONTROL: prove the comparison can see a difference
# --------------------------------------------------------------------------- #


def test_the_comparison_detects_a_real_numerical_change(tmp_path, planners):
    """Run the successor against itself under the opt-in G3 objective.

    If the comparison could not distinguish a genuinely different fit, the
    bitwise-equality result above would be worthless. The G3 objective changes
    donor fit mass from cell-weighted to uniform-per-donor, so the emitted rows
    must differ. If this test ever passes-by-equality, the harness is blind.
    """
    _frozen, successor = planners
    parameters, budget = E.default_parameters_and_budget()
    materials = E.build_stream_materials(tmp_path / "mutated", **SMALL)

    baseline = successor.run_all_primary_folds_streaming(
        stream=E._stream_for(successor, materials),
        parameters=parameters,
        evidence_budget=budget,
        global_seed=20260926,
    )
    perturbed = successor.run_all_primary_folds_streaming(
        stream=E._stream_for(successor, materials),
        parameters=parameters,
        evidence_budget=budget,
        global_seed=20260926,
        g3_fit_objective="PRODUCTION_OBJECTIVE_MATCHED",
    )
    problems = E._diff_rows(baseline, perturbed)
    assert problems, (
        "the row comparison could not distinguish the opt-in G3 fit objective "
        "from the historical default; the equivalence result is not meaningful"
    )


def test_the_comparison_detects_a_changed_partner_selection(tmp_path, planners):
    """A different partner tuple must surface as a diff, not be silently equal."""
    frozen, _successor = planners
    parameters, budget = E.default_parameters_and_budget()
    materials = E.build_stream_materials(tmp_path / "partners", **SMALL)
    rows = frozen.run_all_primary_folds_streaming(
        stream=E._stream_for(frozen, materials),
        parameters=parameters,
        evidence_budget=budget,
        global_seed=20260926,
    )
    assert rows, "fixture produced no rows to perturb"
    tampered = [dict(r) for r in rows]
    key = next(
        k
        for k, v in tampered[0].items()
        if isinstance(v, (int, float)) and not isinstance(v, bool)
    )
    tampered[0][key] = type(tampered[0][key])(tampered[0][key]) + 1
    assert E._diff_rows(rows, tampered), "a perturbed row compared equal"


def test_a_dropped_row_is_detected():
    left = [{"a": 1.0}, {"a": 2.0}]
    right = [{"a": 1.0}]
    problems = E._diff_rows(left, right)
    assert problems and "row count differs" in problems[0]


def test_a_renamed_field_is_detected():
    problems = E._diff_rows([{"a": 1.0}], [{"b": 1.0}])
    assert problems and "key set differs" in problems[0]


def test_float_comparison_is_exact_not_approximate():
    """One ulp apart must be reported as different."""
    import math

    value = 0.1
    nudged = math.nextafter(value, math.inf)
    assert value != nudged
    assert E._diff_rows([{"score": value}], [{"score": nudged}])


# --------------------------------------------------------------------------- #
# The opt-in itself
# --------------------------------------------------------------------------- #


def test_the_successor_rejects_an_unknown_fit_objective(tmp_path, planners):
    _frozen, successor = planners
    parameters, budget = E.default_parameters_and_budget()
    materials = E.build_stream_materials(tmp_path / "unknown", **SMALL)
    with pytest.raises(ValueError, match="unknown explicit G3 fit objective"):
        successor.run_all_primary_folds_streaming(
            stream=E._stream_for(successor, materials),
            parameters=parameters,
            evidence_budget=budget,
            global_seed=20260926,
            g3_fit_objective="NOT_A_REAL_OBJECTIVE",
        )


def test_the_frozen_planner_has_no_g3_parameter_at_all(planners):
    """The old planner could not have taken the opt-in even by accident."""
    import inspect

    frozen, successor = planners
    assert "g3_fit_objective" not in inspect.signature(
        frozen.run_all_primary_folds_streaming
    ).parameters
    assert "g3_fit_objective" in inspect.signature(
        successor.run_all_primary_folds_streaming
    ).parameters


def test_the_opt_in_defaults_to_the_historical_path(planners):
    """The new parameter's default is None, so no caller gets G3 implicitly."""
    import inspect

    _frozen, successor = planners
    for name in ("run_primary_fold_streaming", "run_all_primary_folds_streaming"):
        sig = inspect.signature(getattr(successor, name))
        assert sig.parameters["g3_fit_objective"].default is None, name
    for name in ("_fit_ridge_weights", "_ridge_primary_score", "_ridge_partners"):
        sig = inspect.signature(getattr(successor, name))
        assert sig.parameters["fit_objective"].default is None, name


def test_no_audit_b_call_site_supplies_a_g3_objective():
    """Static guard: the Audit-B planners must use the historical default."""
    for relative in (
        "src/sea_ad_jepa/v5/audit_b_n1_cached_planner_v1.py",
        "src/sea_ad_jepa/v5/audit_b_n1_crossfold_planner_v1.py",
        "analysis/v5_full104_information_channel_redteam_20260920/scripts/"
        "audit_b_mask_plan_generator_20260920.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "g3_fit_objective" not in source, relative
        assert "fit_objective" not in source, relative
