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
    return {"age": ages, "sex": sexes}


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
    result = pf._stage_a_from_arrays(discovery=_roles(28),
                                        confirmation=_roles(18))
    assert result["stage"] == "A_PARENT_NUISANCE"
    assert result["checks"]["DISCOVERY"] == 4
    assert result["checks"]["CONFIRMATION"] == 4
    # One fold per discovery donor, which is where a deficiency can hide.
    assert result["checks"]["DISCOVERY_LOODO_FOLDS"] == 28
    assert len(result["loodo_ranks"]) == 28


def test_stage_a_refuses_a_single_sex_confirmation_set() -> None:
    with pytest.raises(AssertionError) as excinfo:
        pf._stage_a_from_arrays(discovery=_roles(28),
                                   confirmation=_roles(18, single_sex=True))
    assert pf.STOP_SEX_NOT_BINARY in str(excinfo.value)


def test_stage_a_catches_a_fold_that_becomes_single_sex() -> None:
    """A design can be full rank overall and deficient in one fold.

    Removing the only male donor leaves a single-sex training set, and that fold
    would otherwise fail during discovery fitting rather than at preflight.
    """
    discovery = {"age": [80, 84, 88, 92, 96, 100],
                 "sex": [0, 0, 0, 0, 0, 1]}
    # Full rank on the whole set, because both sexes are present.
    assert pf.assert_full_rank(
        pf.nuisance_design(discovery["age"], discovery["sex"]),
        what="whole discovery set") == 4
    with pytest.raises(AssertionError) as excinfo:
        pf._stage_a_from_arrays(discovery=discovery, confirmation=_roles(18))
    assert pf.STOP_SEX_NOT_BINARY in str(excinfo.value)


# --- Stage B ----------------------------------------------------------------

def test_stage_b_checks_the_three_confirmation_designs() -> None:
    n = 18
    result = pf._stage_b_from_arrays(
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
        pf._stage_b_from_arrays(
            confirmation=_roles(n), state_score=_covariate(n),
            immune_fraction=_covariate(n, 0.01, 0.002, shape=1),
            q_depth=_covariate(n, 9.0, 0.05, shape=2), q_detect=_covariate(n, 0.2, 0.01, shape=3),
            response=[1.0] * n)
    assert pf.STOP_RESPONSE_PRESENT in str(excinfo.value)


def test_stage_b_catches_a_state_score_collinear_with_a_covariate() -> None:
    n = 18
    depth = _covariate(n, 9.0, 0.05)
    with pytest.raises(AssertionError) as excinfo:
        pf._stage_b_from_arrays(
            confirmation=_roles(n), state_score=depth,
            immune_fraction=_covariate(n, 0.01, 0.002, shape=1),
            q_depth=depth, q_detect=_covariate(n, 0.2, 0.01, shape=3))
    assert pf.STOP_NOT_ESTIMABLE in str(excinfo.value)
    assert "measurement" in str(excinfo.value)


def test_stage_b_catches_a_constant_state_score() -> None:
    """A constant predictor is collinear with the intercept."""
    n = 18
    with pytest.raises(AssertionError) as excinfo:
        pf._stage_b_from_arrays(
            confirmation=_roles(n), state_score=[0.5] * n,
            immune_fraction=_covariate(n, 0.01, 0.002, shape=1),
            q_depth=_covariate(n, 9.0, 0.05, shape=2), q_detect=_covariate(n, 0.2, 0.01, shape=3))
    assert pf.STOP_NOT_ESTIMABLE in str(excinfo.value)


def test_stage_b_refuses_a_covariate_of_the_wrong_length() -> None:
    n = 18
    with pytest.raises(AssertionError) as excinfo:
        pf._stage_b_from_arrays(
            confirmation=_roles(n), state_score=_covariate(n - 1),
            immune_fraction=_covariate(n, 0.01, 0.002, shape=1),
            q_depth=_covariate(n, 9.0, 0.05, shape=2), q_detect=_covariate(n, 0.2, 0.01, shape=3))
    assert pf.STOP_INPUT_SHAPE in str(excinfo.value)


# --- Stage C ----------------------------------------------------------------

@pytest.mark.parametrize("n", [17, 18])
def test_stage_c_checks_the_tail_designs_at_both_allowed_n(n) -> None:
    """The frozen contract allows a tail inference n of 17 or 18."""
    result = pf._stage_c_from_arrays(
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
        pf._stage_c_from_arrays(
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
        pf._stage_c_from_arrays(
            tail_donors=_roles(n), state_score=state, tail_prevalence=state,
            immune_fraction=_covariate(n, 0.01, 0.002, shape=1),
            q_depth=_covariate(n, 9.0, 0.05, shape=2), q_detect=_covariate(n, 0.2, 0.01, shape=3))
    assert pf.STOP_NOT_ESTIMABLE in str(excinfo.value)


def test_stage_c_catches_a_constant_tail_prevalence() -> None:
    """Every tail donor sharing one prevalence carries no information."""
    n = 18
    with pytest.raises(AssertionError) as excinfo:
        pf._stage_c_from_arrays(
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
        pf._stage_a_from_arrays(discovery=_roles(28),
                                   confirmation=_roles(n_conf)),
        pf._stage_b_from_arrays(
            confirmation=_roles(n_conf), state_score=_covariate(n_conf),
            immune_fraction=_covariate(n_conf, 0.01, 0.002, shape=1),
            q_depth=_covariate(n_conf, 9.0, 0.05, shape=2),
            q_detect=_covariate(n_conf, 0.2, 0.01, shape=3)),
        pf._stage_c_from_arrays(
            tail_donors=_roles(n_tail), state_score=_covariate(n_tail),
            tail_prevalence=_covariate(n_tail, 0.05, 0.011, shape=4),
            immune_fraction=_covariate(n_tail, 0.01, 0.002, shape=1),
            q_depth=_covariate(n_tail, 9.0, 0.05, shape=2),
            q_detect=_covariate(n_tail, 0.2, 0.01, shape=3)),
    ]
    assert pf.assert_stage_order(results) is True
    assert len(pf.preflight_root(results)) == 64


# ---------------------------------------------------------------------------
# Donor-keyed inputs.
#
# The array primitives align covariates only by position, so permuting one is
# structurally valid and changes matrix rank. A design that is genuinely
# NOT_ESTIMABLE can therefore be made full rank by shuffling a column, and
# nothing in a positional preflight would notice. The production stages key
# values by donor and bind the whole record set with a digest, so a reassignment
# across donors moves the digest and is refused.
# ---------------------------------------------------------------------------

def _records(donors, *, collinear: bool = False):
    """Donor-keyed records in generic position, or deliberately collinear."""
    out = {}
    for index, donor in enumerate(donors):
        depth = _covariate(len(donors), 9.0, 0.05, shape=2)[index]
        out[donor] = {
            "age": float(70 + (index * 3) % 27),
            "sex": float(index % 2),
            # When collinear, STATE_SCORE is exactly Q_DEPTH, which makes the
            # measurement design rank deficient for the correctly aligned data.
            "STATE_SCORE": depth if collinear else _covariate(len(donors))[index],
            "IMMUNE_FRACTION": _covariate(len(donors), 0.01, 0.002, shape=1)[index],
            "Q_DEPTH": depth,
            "Q_DETECT": _covariate(len(donors), 0.2, 0.01, shape=3)[index],
            "TAIL_PREVALENCE": _covariate(len(donors), 0.05, 0.011, shape=4)[index],
        }
    return out


def _donors(n: int):
    return ["D%02d" % i for i in range(n)]


def test_the_donor_keyed_stage_b_accepts_bound_records() -> None:
    donors = _donors(18)
    records = _records(donors)
    root = pf.records_root(donors, records, pf.STAGE_B_FIELDS)
    result = pf.stage_b_state_designs(
        confirmation_order=donors, records=records,
        expected_records_root_sha256=root)
    assert result["donor_bound"] is True
    assert result["residual_df"] == {"primary": 13, "composition": 12,
                                     "measurement": 11}


def test_permuting_a_covariate_cannot_rescue_a_non_estimable_design() -> None:
    """The exact attack. Aligned data is NOT_ESTIMABLE; a permutation is refused.

    With STATE_SCORE exactly equal to Q_DEPTH the measurement design is rank
    deficient, which is the truth about this design. Reassigning STATE_SCORE
    across donors breaks that collinearity and would make the design full rank,
    so a positional preflight would report PASS. Here the reassignment moves the
    bound records digest and is refused instead.
    """
    donors = _donors(18)
    aligned = _records(donors, collinear=True)
    aligned_root = pf.records_root(donors, aligned, pf.STAGE_B_FIELDS)

    # The truth about the correctly aligned design.
    with pytest.raises(AssertionError) as excinfo:
        pf.stage_b_state_designs(confirmation_order=donors, records=aligned,
                                 expected_records_root_sha256=aligned_root)
    assert pf.STOP_NOT_ESTIMABLE in str(excinfo.value)
    assert "measurement" in str(excinfo.value)

    # Reassign STATE_SCORE across donors by one position.
    permuted = {donor: dict(row) for donor, row in aligned.items()}
    rotated = [aligned[d]["STATE_SCORE"] for d in donors]
    rotated = rotated[1:] + rotated[:1]
    for donor, value in zip(donors, rotated):
        permuted[donor]["STATE_SCORE"] = value

    # It would now be full rank, which is precisely why it must be refused.
    assert pf.assert_full_rank(
        [row + [permuted[d]["Q_DEPTH"], permuted[d]["Q_DETECT"],
                permuted[d]["STATE_SCORE"]]
         for row, d in zip(pf.nuisance_design(
             [permuted[d]["age"] for d in donors],
             [permuted[d]["sex"] for d in donors]), donors)],
        what="permuted measurement design") == 7

    with pytest.raises(AssertionError) as excinfo:
        pf.stage_b_state_designs(confirmation_order=donors, records=permuted,
                                 expected_records_root_sha256=aligned_root)
    assert pf.STOP_RECORDS_ROOT in str(excinfo.value)


def test_the_records_root_moves_when_two_donors_swap_a_value() -> None:
    donors = _donors(6)
    records = _records(donors)
    baseline = pf.records_root(donors, records, pf.STAGE_B_FIELDS)
    swapped = {donor: dict(row) for donor, row in records.items()}
    swapped["D00"]["STATE_SCORE"], swapped["D01"]["STATE_SCORE"] = (
        records["D01"]["STATE_SCORE"], records["D00"]["STATE_SCORE"])
    assert pf.records_root(donors, swapped, pf.STAGE_B_FIELDS) != baseline


def test_the_records_root_depends_on_the_donor_order() -> None:
    """The order is the role authority's, not the caller's array indices."""
    donors = _donors(6)
    records = _records(donors)
    assert pf.records_root(donors, records, pf.STAGE_B_FIELDS) != \
        pf.records_root(list(reversed(donors)), records, pf.STAGE_B_FIELDS)


def test_a_donor_set_mismatch_is_refused() -> None:
    donors = _donors(6)
    records = _records(donors)
    root = pf.records_root(donors, records, pf.STAGE_B_FIELDS)
    with pytest.raises(AssertionError) as excinfo:
        pf.stage_b_state_designs(confirmation_order=donors + ["D99"],
                                 records=records,
                                 expected_records_root_sha256=root)
    assert pf.STOP_DONOR_SET in str(excinfo.value)
    assert "D99" in str(excinfo.value)


def test_a_repeated_donor_in_the_order_is_refused() -> None:
    donors = _donors(6)
    records = _records(donors)
    root = pf.records_root(donors, records, pf.STAGE_B_FIELDS)
    with pytest.raises(AssertionError) as excinfo:
        pf.stage_b_state_designs(confirmation_order=donors + [donors[0]],
                                 records=records,
                                 expected_records_root_sha256=root)
    assert pf.STOP_DONOR_ORDER in str(excinfo.value)


def test_a_missing_record_field_is_refused() -> None:
    donors = _donors(6)
    records = _records(donors)
    stripped = {donor: dict(row) for donor, row in records.items()}
    stripped["D00"].pop("Q_DETECT")
    with pytest.raises(AssertionError) as excinfo:
        pf.records_root(donors, stripped, pf.STAGE_B_FIELDS)
    assert pf.STOP_FIELD_ABSENT in str(excinfo.value)


def test_positional_arrays_are_explicitly_refused() -> None:
    with pytest.raises(AssertionError) as excinfo:
        pf.refuse_positional_arrays(state_score=[1.0], q_depth=[2.0])
    assert pf.STOP_POSITIONAL in str(excinfo.value)


def test_the_array_primitives_are_private() -> None:
    """They may remain for unit testing, but production must not reach them."""
    for name in ("_stage_a_from_arrays", "_stage_b_from_arrays",
                 "_stage_c_from_arrays"):
        assert hasattr(pf, name)
    for name in ("stage_a_parent_nuisance", "stage_b_state_designs",
                 "stage_c_tail_designs"):
        assert hasattr(pf, name)


def test_the_donor_keyed_stage_a_binds_both_role_record_sets() -> None:
    discovery = _donors(28)
    confirmation = ["C%02d" % i for i in range(18)]
    dr = _records(discovery)
    cr = _records(confirmation)
    result = pf.stage_a_parent_nuisance(
        discovery_order=discovery, discovery_records=dr,
        expected_discovery_records_root_sha256=pf.records_root(
            discovery, dr, ("age", "sex")),
        confirmation_order=confirmation, confirmation_records=cr,
        expected_confirmation_records_root_sha256=pf.records_root(
            confirmation, cr, ("age", "sex")))
    assert result["donor_bound"] is True
    assert result["checks"]["DISCOVERY_LOODO_FOLDS"] == 28


def test_the_donor_keyed_stage_a_refuses_a_wrong_records_root() -> None:
    discovery = _donors(28)
    confirmation = ["C%02d" % i for i in range(18)]
    dr = _records(discovery)
    cr = _records(confirmation)
    with pytest.raises(AssertionError) as excinfo:
        pf.stage_a_parent_nuisance(
            discovery_order=discovery, discovery_records=dr,
            expected_discovery_records_root_sha256="f" * 64,
            confirmation_order=confirmation, confirmation_records=cr,
            expected_confirmation_records_root_sha256=pf.records_root(
                confirmation, cr, ("age", "sex")))
    assert pf.STOP_RECORDS_ROOT in str(excinfo.value)


@pytest.mark.parametrize("n", [17, 18])
def test_the_donor_keyed_stage_c_accepts_bound_records(n) -> None:
    donors = _donors(n)
    records = _records(donors)
    root = pf.records_root(donors, records, pf.STAGE_C_FIELDS)
    result = pf.stage_c_tail_designs(
        tail_order=donors, records=records,
        expected_records_root_sha256=root)
    assert result["donor_bound"] is True
    assert result["tail_inference_n"] == n


def test_the_donor_keyed_stages_still_refuse_the_response() -> None:
    donors = _donors(18)
    records = _records(donors)
    for stage, kwargs in (
            (pf.stage_b_state_designs,
             {"confirmation_order": donors, "records": records,
              "expected_records_root_sha256": pf.records_root(
                  donors, records, pf.STAGE_B_FIELDS)}),
            (pf.stage_c_tail_designs,
             {"tail_order": donors, "records": records,
              "expected_records_root_sha256": pf.records_root(
                  donors, records, pf.STAGE_C_FIELDS)})):
        with pytest.raises(AssertionError) as excinfo:
            stage(response=[1.0] * 18, **kwargs)
        assert pf.STOP_RESPONSE_PRESENT in str(excinfo.value)


# ---------------------------------------------------------------------------
# The preflight root must bind every decision-bearing stage output.
#
# External review found it hashed only stage names and rank results, so two
# stages over different donor-bound record sets with identical ranks produced
# the same root. Ranks are the least distinguishing thing a stage produces.
# ---------------------------------------------------------------------------

def _stage_result(**overrides):
    result = {
        "stage": "B_STATE_DESIGNS",
        "checks": {"primary": 5, "composition": 6, "measurement": 7},
        "records_root_sha256": "a" * 64,
        "donor_bound": True,
        "residual_df": {"primary": 13, "composition": 12, "measurement": 11},
    }
    result.update(overrides)
    return result


def test_the_preflight_root_binds_the_records_root() -> None:
    """Identical ranks over different records must be different authorities."""
    a = _stage_result()
    b = _stage_result(records_root_sha256="b" * 64)
    assert a["checks"] == b["checks"]
    assert pf.preflight_root([a]) != pf.preflight_root([b])


def test_the_preflight_root_binds_the_residual_degrees_of_freedom() -> None:
    a = _stage_result()
    b = _stage_result(residual_df={"primary": 12, "composition": 12,
                                   "measurement": 11})
    assert pf.preflight_root([a]) != pf.preflight_root([b])


def test_the_preflight_root_binds_the_tail_inference_size() -> None:
    """n=17 and n=18 are different studies even at the same ranks."""
    a = _stage_result(stage="C_TAIL_DESIGNS", tail_inference_n=17)
    b = _stage_result(stage="C_TAIL_DESIGNS", tail_inference_n=18)
    assert pf.preflight_root([a]) != pf.preflight_root([b])


def test_the_preflight_root_binds_the_donor_bound_flag() -> None:
    """A positional run and a donor-bound run must not share a root."""
    a = _stage_result()
    b = _stage_result(donor_bound=False)
    assert pf.preflight_root([a]) != pf.preflight_root([b])


def test_the_preflight_root_binds_both_stage_a_records_roots() -> None:
    """Stage A binds one record set per role, and both must count."""
    base = {
        "stage": "A_PARENT_NUISANCE",
        "checks": {"DISCOVERY": 4, "CONFIRMATION": 4,
                   "DISCOVERY_LOODO_FOLDS": 28},
        "donor_bound": True,
        "discovery_records_root_sha256": "c" * 64,
        "confirmation_records_root_sha256": "d" * 64,
    }
    moved_discovery = dict(base, discovery_records_root_sha256="e" * 64)
    moved_confirmation = dict(base, confirmation_records_root_sha256="e" * 64)
    roots = {pf.preflight_root([base]), pf.preflight_root([moved_discovery]),
             pf.preflight_root([moved_confirmation])}
    assert len(roots) == 3


def test_the_preflight_root_binds_the_loodo_fold_ranks() -> None:
    a = _stage_result(stage="A_PARENT_NUISANCE", loodo_ranks={0: 4, 1: 4})
    b = _stage_result(stage="A_PARENT_NUISANCE", loodo_ranks={0: 4, 1: 3})
    assert pf.preflight_root([a]) != pf.preflight_root([b])


def test_the_preflight_root_is_deterministic() -> None:
    a = _stage_result()
    assert pf.preflight_root([a]) == pf.preflight_root([_stage_result()])
