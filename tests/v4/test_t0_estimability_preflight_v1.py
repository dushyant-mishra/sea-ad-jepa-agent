"""Adversarial cases for the stagewise estimability preflight.

The preflight exists so a non-estimable design is found before any confirmation
AT8 value is touched, rather than during interpretation where a rank failure
would look like an outcome.

Three properties are checked here. The nuisance construction must match the
frozen `[1, age_c, age_c^2, sex]` design and refuse a single-sex donor set, since
that is a design failure and not a biological NOT_MEASURABLE. Every stage must be
pathology-blind, so supplying the response is refused outright. And a rank failure
must be a loud STOP that names the design, never something a caller could answer
by altering the split, eligibility, a threshold, the covariates or an alpha.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "v4") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_estimability_preflight_v1 as pf  # noqa: E402


def _roles(n: int, *, single_sex: bool = False):
    """A donor set with varied ages and, by default, both sexes present."""
    ages = [70 + (i * 3) % 27 for i in range(n)]
    sexes = [0] * n if single_sex else [i % 2 for i in range(n)]
    return {"donor_id": ["D%03d" % i for i in range(n)], "age": ages, "sex": sexes}


def _covariate(n: int, start: float = 0.1, step: float = 0.017, *, shape: int = 0):
    """A covariate in generic position with respect to the others.

    Structured series turned out to be a trap: an arithmetic sequence in the row
    index is an affine transform of every other one, and periodic integer
    patterns can alias against the centred-age and squared-age columns. Both
    produce a genuine rank deficiency that has nothing to do with the design
    under test, so the fixture would fail for the wrong reason.

    A deterministic hash per (shape, index) gives values in generic position
    while staying exactly reproducible. The deliberate-collinearity cases below
    construct that condition explicitly instead of inheriting it by accident.
    """
    import hashlib

    values = []
    for index in range(n):
        seed = ("t0-preflight|%d|%d" % (shape, index)).encode("utf-8")
        draw = int.from_bytes(hashlib.sha256(seed).digest()[:6], "big")
        values.append(start + step * (draw / float(1 << 48)) * 10.0)
    return values


# --- the frozen nuisance construction ---------------------------------------

def test_the_nuisance_design_is_intercept_age_age_squared_sex() -> None:
    design = pf.nuisance_design([80, 84, 88, 92], [0, 1, 0, 1])
    assert len(design) == 4
    assert len(design[0]) == 4
    assert all(row[0] == 1.0 for row in design)
    # Age is centred on its own mean, and the third column is its square.
    assert design[0][1] == pytest.approx(80 - 86)
    assert design[0][2] == pytest.approx((80 - 86) ** 2)
    assert [row[3] for row in design] == [0.0, 1.0, 0.0, 1.0]


def test_a_single_sex_donor_set_is_refused() -> None:
    """Collinear with the intercept, so it is a design failure.

    The frozen role authority raises the same way. The point of surfacing it here
    is that it must not be recorded as a biological NOT_MEASURABLE, and the split
    must not be altered to rescue it.
    """
    with pytest.raises(AssertionError) as excinfo:
        pf.nuisance_design([80, 84, 88], [1, 1, 1])
    assert pf.STOP_SEX_NOT_BINARY in str(excinfo.value)
    assert "design failure" in str(excinfo.value)


def test_a_sex_encoding_outside_zero_one_is_refused() -> None:
    with pytest.raises(AssertionError) as excinfo:
        pf.nuisance_design([80, 84], [1, 2])
    assert pf.STOP_SEX_NOT_BINARY in str(excinfo.value)


def test_mismatched_covariate_lengths_are_refused() -> None:
    with pytest.raises(AssertionError) as excinfo:
        pf.nuisance_design([80, 84, 88], [0, 1])
    assert pf.STOP_INPUT_SHAPE in str(excinfo.value)


def test_a_nonfinite_age_is_refused() -> None:
    with pytest.raises(AssertionError) as excinfo:
        pf.nuisance_design([80, float("nan")], [0, 1])
    assert pf.STOP_INPUT_SHAPE in str(excinfo.value)


# --- rank checking ----------------------------------------------------------

def test_full_rank_passes_and_reports_the_rank() -> None:
    design = pf.nuisance_design([80, 84, 88, 92, 96], [0, 1, 0, 1, 0])
    assert pf.assert_full_rank(design, what="test design") == 4


def test_a_rank_deficient_design_is_a_loud_not_estimable() -> None:
    """A duplicated column is the clearest possible deficiency."""
    design = [[1.0, 2.0, 2.0], [1.0, 3.0, 3.0], [1.0, 5.0, 5.0], [1.0, 7.0, 7.0]]
    with pytest.raises(AssertionError) as excinfo:
        pf.assert_full_rank(design, what="duplicated-column design")
    message = str(excinfo.value)
    assert pf.STOP_NOT_ESTIMABLE in message
    assert "duplicated-column design" in message
    assert "not a biological NOT_MEASURABLE" in message


def test_more_parameters_than_donors_is_a_loud_not_estimable() -> None:
    design = [[1.0, 2.0, 3.0, 4.0, 5.0], [1.0, 3.0, 4.0, 5.0, 6.0]]
    with pytest.raises(AssertionError) as excinfo:
        pf.assert_full_rank(design, what="over-parameterised design")
    assert pf.STOP_NOT_ESTIMABLE in str(excinfo.value)
    assert "2 donors for 5 parameters" in str(excinfo.value)


def test_a_ragged_design_is_refused() -> None:
    with pytest.raises(AssertionError) as excinfo:
        pf.assert_full_rank([[1.0, 2.0], [1.0]], what="ragged")
    assert pf.STOP_INPUT_SHAPE in str(excinfo.value)


# --- Stage A ----------------------------------------------------------------

def test_stage_a_checks_both_roles_and_every_loodo_fold() -> None:
    result = pf.stage_a_parent_nuisance(discovery=_roles(28),
                                        confirmation=_roles(18))
    assert result["stage"] == "A_PARENT_NUISANCE"
    assert result["checks"]["DISCOVERY"] == 4
    assert result["checks"]["CONFIRMATION"] == 4
    # One fold per discovery donor, which is where a deficiency can hide.
    assert result["checks"]["DISCOVERY_LOODO_FOLDS"] == 28
    assert len(result["loodo_ranks"]) == 28


def test_stage_a_refuses_a_single_sex_confirmation_set() -> None:
    with pytest.raises(AssertionError) as excinfo:
        pf.stage_a_parent_nuisance(discovery=_roles(28),
                                   confirmation=_roles(18, single_sex=True))
    assert pf.STOP_SEX_NOT_BINARY in str(excinfo.value)


def test_stage_a_catches_a_fold_that_becomes_single_sex() -> None:
    """A design can be full rank overall and deficient in one fold.

    Removing the only male donor leaves a single-sex training set, and that fold
    would otherwise fail during discovery fitting rather than at preflight.
    """
    discovery = {"donor_id": ["D0", "D1", "D2", "D3", "D4", "D5"],
                 "age": [80, 84, 88, 92, 96, 100],
                 "sex": [0, 0, 0, 0, 0, 1]}
    # Full rank on the whole set, because both sexes are present.
    assert pf.assert_full_rank(
        pf.nuisance_design(discovery["age"], discovery["sex"]),
        what="whole discovery set") == 4
    with pytest.raises(AssertionError) as excinfo:
        pf.stage_a_parent_nuisance(discovery=discovery, confirmation=_roles(18))
    assert pf.STOP_SEX_NOT_BINARY in str(excinfo.value)


# --- Stage B ----------------------------------------------------------------

def test_stage_b_checks_the_three_confirmation_designs() -> None:
    n = 18
    result = pf._stage_b_state_designs_positional_fixture(
        confirmation=_roles(n), state_score=_covariate(n),
        immune_fraction=_covariate(n, 0.01, 0.002, shape=1),
        q_depth=_covariate(n, 9.0, 0.05, shape=2), q_detect=_covariate(n, 0.2, 0.01, shape=3))
    assert result["stage"] == "B_STATE_DESIGNS"
    assert set(result["checks"]) == {"primary", "composition", "measurement"}
    # 4 nuisance columns plus the predictors: 5, 6 and 7 parameters.
    assert result["residual_df"] == {"primary": 13, "composition": 12,
                                     "measurement": 11}


def test_stage_b_refuses_the_response() -> None:
    """Rank is a property of the design, so the outcome must not be supplied."""
    n = 18
    with pytest.raises(AssertionError) as excinfo:
        pf._stage_b_state_designs_positional_fixture(
            confirmation=_roles(n), state_score=_covariate(n),
            immune_fraction=_covariate(n, 0.01, 0.002, shape=1),
            q_depth=_covariate(n, 9.0, 0.05, shape=2), q_detect=_covariate(n, 0.2, 0.01, shape=3),
            response=[1.0] * n)
    assert pf.STOP_RESPONSE_PRESENT in str(excinfo.value)


def test_stage_b_catches_a_state_score_collinear_with_a_covariate() -> None:
    n = 18
    depth = _covariate(n, 9.0, 0.05)
    with pytest.raises(AssertionError) as excinfo:
        pf._stage_b_state_designs_positional_fixture(
            confirmation=_roles(n), state_score=depth,
            immune_fraction=_covariate(n, 0.01, 0.002, shape=1),
            q_depth=depth, q_detect=_covariate(n, 0.2, 0.01, shape=3))
    assert pf.STOP_NOT_ESTIMABLE in str(excinfo.value)
    assert "measurement" in str(excinfo.value)


def test_stage_b_catches_a_constant_state_score() -> None:
    """A constant predictor is collinear with the intercept."""
    n = 18
    with pytest.raises(AssertionError) as excinfo:
        pf._stage_b_state_designs_positional_fixture(
            confirmation=_roles(n), state_score=[0.5] * n,
            immune_fraction=_covariate(n, 0.01, 0.002, shape=1),
            q_depth=_covariate(n, 9.0, 0.05, shape=2), q_detect=_covariate(n, 0.2, 0.01, shape=3))
    assert pf.STOP_NOT_ESTIMABLE in str(excinfo.value)


def test_stage_b_refuses_a_covariate_of_the_wrong_length() -> None:
    n = 18
    with pytest.raises(AssertionError) as excinfo:
        pf._stage_b_state_designs_positional_fixture(
            confirmation=_roles(n), state_score=_covariate(n - 1),
            immune_fraction=_covariate(n, 0.01, 0.002, shape=1),
            q_depth=_covariate(n, 9.0, 0.05, shape=2), q_detect=_covariate(n, 0.2, 0.01, shape=3))
    assert pf.STOP_INPUT_SHAPE in str(excinfo.value)


# --- Stage C ----------------------------------------------------------------

@pytest.mark.parametrize("n", [17, 18])
def test_stage_c_checks_the_tail_designs_at_both_allowed_n(n) -> None:
    """The frozen contract allows a tail inference n of 17 or 18."""
    result = pf._stage_c_tail_designs_positional_fixture(
        tail_donors=_roles(n), state_score=_covariate(n),
        tail_prevalence=_covariate(n, 0.05, 0.011, shape=4),
        immune_fraction=_covariate(n, 0.01, 0.002, shape=1),
        q_depth=_covariate(n, 9.0, 0.05, shape=2), q_detect=_covariate(n, 0.2, 0.01, shape=3))
    assert result["stage"] == "C_TAIL_DESIGNS"
    assert result["tail_inference_n"] == n
    assert set(result["checks"]) == {"tail_primary", "tail_composition",
                                     "tail_measurement"}
    # 4 nuisance + state + tail = 6, then 7 and 8 parameters.
    assert result["residual_df"] == {"tail_primary": n - 6,
                                     "tail_composition": n - 7,
                                     "tail_measurement": n - 8}


def test_stage_c_refuses_the_response() -> None:
    n = 18
    with pytest.raises(AssertionError) as excinfo:
        pf._stage_c_tail_designs_positional_fixture(
            tail_donors=_roles(n), state_score=_covariate(n),
            tail_prevalence=_covariate(n, 0.05, 0.011, shape=4),
            immune_fraction=_covariate(n, 0.01, 0.002, shape=1),
            q_depth=_covariate(n, 9.0, 0.05, shape=2), q_detect=_covariate(n, 0.2, 0.01, shape=3),
            response=[1.0] * n)
    assert pf.STOP_RESPONSE_PRESENT in str(excinfo.value)


def test_stage_c_catches_a_tail_prevalence_collinear_with_the_state_score() -> None:
    n = 18
    state = _covariate(n)
    with pytest.raises(AssertionError) as excinfo:
        pf._stage_c_tail_designs_positional_fixture(
            tail_donors=_roles(n), state_score=state, tail_prevalence=state,
            immune_fraction=_covariate(n, 0.01, 0.002, shape=1),
            q_depth=_covariate(n, 9.0, 0.05, shape=2), q_detect=_covariate(n, 0.2, 0.01, shape=3))
    assert pf.STOP_NOT_ESTIMABLE in str(excinfo.value)


def test_stage_c_catches_a_constant_tail_prevalence() -> None:
    """Every tail donor sharing one prevalence carries no information."""
    n = 18
    with pytest.raises(AssertionError) as excinfo:
        pf._stage_c_tail_designs_positional_fixture(
            tail_donors=_roles(n), state_score=_covariate(n),
            tail_prevalence=[0.1] * n,
            immune_fraction=_covariate(n, 0.01, 0.002, shape=1),
            q_depth=_covariate(n, 9.0, 0.05, shape=2), q_detect=_covariate(n, 0.2, 0.01, shape=3))
    assert pf.STOP_NOT_ESTIMABLE in str(excinfo.value)


# --- governance -------------------------------------------------------------

def test_the_forbidden_remedies_are_declared_and_intact() -> None:
    assert pf.assert_no_forbidden_remedy_declared() is True
    assert "ALTER_THE_DETERMINISTIC_SPLIT" in pf.FORBIDDEN_REMEDIES
    assert "ALTER_AN_ALPHA" in pf.FORBIDDEN_REMEDIES
    assert "ALTER_DONOR_ELIGIBILITY" in pf.FORBIDDEN_REMEDIES


def test_editing_the_forbidden_remedy_list_is_refused() -> None:
    original = pf.FORBIDDEN_REMEDIES
    try:
        pf.FORBIDDEN_REMEDIES = ("ALTER_THE_DETERMINISTIC_SPLIT",)
        with pytest.raises(AssertionError) as excinfo:
            pf.assert_no_forbidden_remedy_declared()
        assert pf.STOP_REMEDY in str(excinfo.value)
    finally:
        pf.FORBIDDEN_REMEDIES = original


def test_the_failure_semantics_are_stated() -> None:
    assert "not a biological NOT_MEASURABLE" in pf.FAILURE_SEMANTICS
    assert "may not be answered by changing" in pf.FAILURE_SEMANTICS


def test_stages_must_run_in_order() -> None:
    """Checking the state designs before the roles were verified is out of order."""
    assert pf.assert_stage_order([{"stage": "A_PARENT_NUISANCE", "checks": {}}]) is True
    with pytest.raises(AssertionError) as excinfo:
        pf.assert_stage_order([{"stage": "B_STATE_DESIGNS", "checks": {}}])
    assert pf.STOP_STAGE_ORDER in str(excinfo.value)


def test_the_preflight_root_is_deterministic_and_moves_with_the_stages() -> None:
    a = [{"stage": "A_PARENT_NUISANCE", "checks": {"DISCOVERY": 4}}]
    b = [{"stage": "A_PARENT_NUISANCE", "checks": {"DISCOVERY": 3}}]
    assert pf.preflight_root(a) == pf.preflight_root(a)
    assert pf.preflight_root(a) != pf.preflight_root(b)


def test_all_three_stages_run_in_order_end_to_end() -> None:
    n_conf, n_tail = 18, 17
    results = [
        pf.stage_a_parent_nuisance(discovery=_roles(28),
                                   confirmation=_roles(n_conf)),
        pf._stage_b_state_designs_positional_fixture(
            confirmation=_roles(n_conf), state_score=_covariate(n_conf),
            immune_fraction=_covariate(n_conf, 0.01, 0.002, shape=1),
            q_depth=_covariate(n_conf, 9.0, 0.05, shape=2),
            q_detect=_covariate(n_conf, 0.2, 0.01, shape=3)),
        pf._stage_c_tail_designs_positional_fixture(
            tail_donors=_roles(n_tail), state_score=_covariate(n_tail),
            tail_prevalence=_covariate(n_tail, 0.05, 0.011, shape=4),
            immune_fraction=_covariate(n_tail, 0.01, 0.002, shape=1),
            q_depth=_covariate(n_tail, 9.0, 0.05, shape=2),
            q_detect=_covariate(n_tail, 0.2, 0.01, shape=3)),
    ]
    assert pf.assert_stage_order(results) is True
    assert len(pf.preflight_root(results)) == 64



# R4 donor-identity alignment attacks ---------------------------------------

def _keyed(role_data, values):
    return {donor: value for donor, value in zip(role_data["donor_id"], values)}


def test_production_stage_b_refuses_positional_covariate_arrays() -> None:
    confirmation = _roles(18)
    with pytest.raises(AssertionError) as excinfo:
        pf.stage_b_state_designs(
            confirmation=confirmation,
            state_score=_covariate(18),
            immune_fraction=_keyed(
                confirmation, _covariate(18, 0.01, 0.002, shape=1)),
            q_depth=_keyed(
                confirmation, _covariate(18, 9.0, 0.05, shape=2)),
            q_detect=_keyed(
                confirmation, _covariate(18, 0.2, 0.01, shape=3)),
        )
    assert pf.STOP_DONOR_ALIGNMENT in str(excinfo.value)


def test_mapping_insertion_order_cannot_change_stage_b_design() -> None:
    """The same donor->value mapping must yield the same design regardless of order."""
    confirmation = _roles(18)
    state = _keyed(confirmation, _covariate(18, shape=7))
    immune = _keyed(confirmation, _covariate(18, 0.01, 0.002, shape=1))
    depth = _keyed(confirmation, _covariate(18, 9.0, 0.05, shape=2))
    detect = _keyed(confirmation, _covariate(18, 0.2, 0.01, shape=3))
    reversed_state = dict(reversed(list(state.items())))

    a = pf.stage_b_state_designs(
        confirmation=confirmation,
        state_score=state,
        immune_fraction=immune,
        q_depth=depth,
        q_detect=detect,
    )
    b = pf.stage_b_state_designs(
        confirmation=confirmation,
        state_score=reversed_state,
        immune_fraction=immune,
        q_depth=depth,
        q_detect=detect,
    )
    assert a["checks"] == b["checks"]
    assert a["design_roots"] == b["design_roots"]
    assert pf.preflight_root([a]) == pf.preflight_root([b])


def test_stage_b_design_root_moves_when_a_value_moves_between_donors() -> None:
    confirmation = _roles(18)
    state = _keyed(confirmation, _covariate(18, shape=7))
    immune = _keyed(confirmation, _covariate(18, 0.01, 0.002, shape=1))
    depth = _keyed(confirmation, _covariate(18, 9.0, 0.05, shape=2))
    detect = _keyed(confirmation, _covariate(18, 0.2, 0.01, shape=3))
    swapped = dict(state)
    d0, d1 = confirmation["donor_id"][:2]
    swapped[d0], swapped[d1] = swapped[d1], swapped[d0]

    a = pf.stage_b_state_designs(
        confirmation=confirmation,
        state_score=state,
        immune_fraction=immune,
        q_depth=depth,
        q_detect=detect,
    )
    b = pf.stage_b_state_designs(
        confirmation=confirmation,
        state_score=swapped,
        immune_fraction=immune,
        q_depth=depth,
        q_detect=detect,
    )
    assert a["design_roots"]["primary"] != b["design_roots"]["primary"]
    assert pf.preflight_root([a]) != pf.preflight_root([b])


def test_stage_a_requires_explicit_unique_donor_ids() -> None:
    discovery = _roles(28)
    discovery.pop("donor_id")
    with pytest.raises(AssertionError) as excinfo:
        pf.stage_a_parent_nuisance(
            discovery=discovery,
            confirmation=_roles(18),
        )
    assert pf.STOP_DONOR_ALIGNMENT in str(excinfo.value)
