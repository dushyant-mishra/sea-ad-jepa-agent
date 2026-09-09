"""Stagewise pathology-blind estimability preflight for T0.

Why this exists
---------------
`t0_donor_role_authority_v2` tests the rank of the parent nuisance design at role
construction, and nothing tests the designs that come later. So a study could be
found non-estimable only at the point where confirmation AT8 values were already
being interpreted, which is exactly the wrong moment: by then a rank failure looks
like an outcome rather than a design fact.

This module runs the checks in three stages, all before any numeric confirmation
AT8 access, and each stage runs as soon as its inputs exist.

    Stage A   immediately after donor roles are frozen
              rank of [1, age_c, age_c^2, sex] for DISCOVERY, for CONFIRMATION,
              and for every discovery leave-one-donor-out fold

    Stage B   after STATE_SCORE is frozen, before confirmation AT8 access
              primary      nuisance + STATE_SCORE
              composition  nuisance + IMMUNE_FRACTION + STATE_SCORE
              measurement  nuisance + Q_DEPTH + Q_DETECT + STATE_SCORE

    Stage C   after TAIL_PREVALENCE exists, before the tail AT8 test
              the corresponding tail designs, carrying frozen STATE_SCORE and
              TAIL_PREVALENCE

The response is never touched. Every design here is built from covariates only,
so the preflight is pathology-blind by construction: rank is a property of the
design matrix, not of the outcome.

What a failure means, and what it does not license
--------------------------------------------------
A failure is a loud STOP / NOT_ESTIMABLE. It is a statement about the design, not
about the biology, and it must never be answered by changing the split, the donor
eligibility, a threshold, the covariate set, or an alpha. Those are all frozen,
and adjusting any of them to recover rank would convert a pre-registered design
into a fitted one. `FORBIDDEN_REMEDIES` records that explicitly so the rule is
checkable rather than merely stated.
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence

SCHEMA = "JEPA_T0_ESTIMABILITY_PREFLIGHT_V1"
NAMESPACE = "T0-ESTIMABILITY-PREFLIGHT-V1"
DOMAIN_TAG = "T0-ESTIMABILITY-PREFLIGHT-V1-TYPED-LENGTH-PREFIXED"

STOP_NOT_ESTIMABLE = "STOP_T0_DESIGN_NOT_ESTIMABLE"
STOP_SEX_NOT_BINARY = "STOP_T0_ESTIMABILITY_SEX_NOT_COMPLETE_BINARY"
STOP_STAGE_ORDER = "STOP_T0_ESTIMABILITY_STAGE_RUN_OUT_OF_ORDER"
STOP_INPUT_SHAPE = "STOP_T0_ESTIMABILITY_INPUT_SHAPE_INVALID"
STOP_RESPONSE_PRESENT = "STOP_T0_ESTIMABILITY_RESPONSE_SUPPLIED_TO_A_BLIND_CHECK"
STOP_FIELD_SCHEMA = "STOP_T0_ESTIMABILITY_FIELD_SCHEMA_VIOLATION"
STOP_REMEDY = "STOP_T0_ESTIMABILITY_FORBIDDEN_REMEDY_ATTEMPTED"
STOP_DONOR_ALIGNMENT = "STOP_T0_ESTIMABILITY_DONOR_ALIGNMENT_MISMATCH"

STAGES = ("A_PARENT_NUISANCE", "B_STATE_DESIGNS", "C_TAIL_DESIGNS")

# Frozen: none of these may be altered to recover rank.
FORBIDDEN_REMEDIES = (
    "ALTER_THE_DETERMINISTIC_SPLIT",
    "ALTER_DONOR_ELIGIBILITY",
    "ALTER_A_THRESHOLD",
    "ALTER_THE_COVARIATE_SET",
    "ALTER_AN_ALPHA",
)

FAILURE_SEMANTICS = (
    "A rank failure is a loud STOP / NOT_ESTIMABLE about the DESIGN. It is not a "
    "biological NOT_MEASURABLE, and it may not be answered by changing the split, "
    "eligibility, a threshold, the covariate set or an alpha."
)


def _typed(value: Any) -> bytes:
    if isinstance(value, bool):
        tag, payload = b"b", (b"1" if value else b"0")
    elif isinstance(value, int):
        tag, payload = b"i", str(int(value)).encode("ascii")
    elif isinstance(value, str):
        tag, payload = b"s", value.encode("utf-8")
    elif isinstance(value, (tuple, list)):
        tag = b"l"
        payload = b"%d:%s" % (len(value), b"".join(_typed(v) for v in value))
    else:
        raise AssertionError("%s: cannot frame %r" % (STOP_FIELD_SCHEMA, type(value)))
    return b"%s%d:%s" % (tag, len(payload), payload)


def assert_no_forbidden_remedy_declared() -> bool:
    """The prohibition list must stay intact."""
    if tuple(FORBIDDEN_REMEDIES) != (
            "ALTER_THE_DETERMINISTIC_SPLIT", "ALTER_DONOR_ELIGIBILITY",
            "ALTER_A_THRESHOLD", "ALTER_THE_COVARIATE_SET", "ALTER_AN_ALPHA"):
        raise AssertionError("%s: the forbidden-remedy list was edited"
                             % STOP_REMEDY)
    return True


def _column(values: Sequence[Any], *, what: str, n: int | None = None) -> list[float]:
    import math
    series = [float(v) for v in values]
    if n is not None and len(series) != n:
        raise AssertionError("%s: %s has %d values, expected %d"
                             % (STOP_INPUT_SHAPE, what, len(series), n))
    if not series:
        raise AssertionError("%s: %s is empty" % (STOP_INPUT_SHAPE, what))
    for index, value in enumerate(series):
        if not math.isfinite(value):
            raise AssertionError("%s: %s position %d is %r"
                                 % (STOP_INPUT_SHAPE, what, index, value))
    return series


def nuisance_design(age: Sequence[Any], sex: Sequence[Any]) -> list[list[float]]:
    """`[1, age_c, age_c^2, sex]`, matching the frozen construction exactly.

    Age is centred on its own mean and enters linearly and quadratically. Sex must
    be complete binary 0/1: a single-sex donor set is refused here, as it is in
    the frozen role authority, because it makes the sex column collinear with the
    intercept.
    """
    ages = _column(age, what="age")
    sexes = _column(sex, what="sex", n=len(ages))
    unique = sorted(set(sexes))
    if unique != [0.0, 1.0]:
        raise AssertionError(
            "%s: sex takes values %r; the frozen design requires complete binary "
            "0/1, so a single-sex donor set is a design failure rather than a "
            "biological NOT_MEASURABLE" % (STOP_SEX_NOT_BINARY, unique))
    centre = sum(ages) / len(ages)
    centred = [value - centre for value in ages]
    return [[1.0, c, c * c, s] for c, s in zip(centred, sexes)]


def _rank(matrix: Sequence[Sequence[float]]) -> int:
    import numpy as np
    return int(np.linalg.matrix_rank(np.asarray(matrix, dtype=float)))


def assert_full_rank(matrix: Sequence[Sequence[float]], *, what: str) -> int:
    """Full column rank, or a loud NOT_ESTIMABLE naming the design."""
    if not matrix:
        raise AssertionError("%s: %s is empty" % (STOP_INPUT_SHAPE, what))
    columns = len(matrix[0])
    rows = len(matrix)
    for index, row in enumerate(matrix):
        if len(row) != columns:
            raise AssertionError("%s: %s row %d has %d columns, expected %d"
                                 % (STOP_INPUT_SHAPE, what, index, len(row),
                                    columns))
    if rows < columns:
        raise AssertionError(
            "%s: %s has %d donors for %d parameters, so it cannot be estimated. %s"
            % (STOP_NOT_ESTIMABLE, what, rows, columns, FAILURE_SEMANTICS))
    rank = _rank(matrix)
    if rank != columns:
        raise AssertionError(
            "%s: %s has rank %d for %d columns. %s"
            % (STOP_NOT_ESTIMABLE, what, rank, columns, FAILURE_SEMANTICS))
    return rank


def _augment(base: Sequence[Sequence[float]],
             extra: Sequence[Sequence[float]]) -> list[list[float]]:
    if len(base) != len(extra):
        raise AssertionError(
            "%s: cannot augment %d design rows with %d covariate rows"
            % (STOP_INPUT_SHAPE, len(base), len(extra)))
    return [list(row) + [float(v) for v in more] for row, more in zip(base, extra)]


def _donor_ids(data: Mapping[str, Sequence[Any]], *, what: str) -> list[str]:
    """Require an explicit, unique donor identity for every design row."""
    if "donor_id" not in data:
        raise AssertionError(
            "%s: %s lacks donor_id; positional covariate alignment is forbidden"
            % (STOP_DONOR_ALIGNMENT, what))
    donor_ids = [str(value) for value in data["donor_id"]]
    if not donor_ids:
        raise AssertionError("%s: %s donor_id is empty"
                             % (STOP_DONOR_ALIGNMENT, what))
    if len(set(donor_ids)) != len(donor_ids):
        raise AssertionError("%s: %s donor_id contains duplicates"
                             % (STOP_DONOR_ALIGNMENT, what))
    for field in ("age", "sex"):
        if field not in data:
            raise AssertionError("%s: %s lacks %s"
                                 % (STOP_INPUT_SHAPE, what, field))
        if len(data[field]) != len(donor_ids):
            raise AssertionError(
                "%s: %s %s has %d values for %d donors"
                % (STOP_INPUT_SHAPE, what, field, len(data[field]),
                   len(donor_ids)))
    return donor_ids


def _bind_by_donor(values: Mapping[str, Any], donor_ids: Sequence[str], *,
                   what: str) -> list[float]:
    """Join one covariate to an authority-defined donor order by donor ID."""
    if not isinstance(values, Mapping):
        raise AssertionError(
            "%s: %s must be donor-keyed; positional arrays are forbidden"
            % (STOP_DONOR_ALIGNMENT, what))
    normalised: dict[str, Any] = {}
    for key, value in values.items():
        donor = str(key)
        if donor in normalised:
            raise AssertionError(
                "%s: %s has duplicate donor key after string normalisation: %r"
                % (STOP_DONOR_ALIGNMENT, what, donor))
        normalised[donor] = value
    expected = set(map(str, donor_ids))
    actual = set(normalised)
    if actual != expected:
        raise AssertionError(
            "%s: %s donor set differs; extra=%s missing=%s"
            % (STOP_DONOR_ALIGNMENT, what,
               sorted(actual - expected), sorted(expected - actual)))
    return _column([normalised[str(donor)] for donor in donor_ids],
                   what=what, n=len(donor_ids))


def _design_root(name: str, donor_ids: Sequence[str],
                 matrix: Sequence[Sequence[float]]) -> str:
    """Bind donor order and every numeric design entry, not only the rank."""
    if len(donor_ids) != len(matrix):
        raise AssertionError(
            "%s: %s has %d donor IDs for %d matrix rows"
            % (STOP_DONOR_ALIGNMENT, name, len(donor_ids), len(matrix)))
    parts = [_typed(DOMAIN_TAG), _typed("DESIGN"), _typed(str(name)),
             _typed(len(donor_ids))]
    for donor, row in zip(donor_ids, matrix):
        parts.append(_typed(str(donor)))
        parts.append(_typed([float(value).hex() for value in row]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


# --- Stage A ---------------------------------------------------------------

def stage_a_parent_nuisance(
        *,
        discovery: Mapping[str, Sequence[Any]],
        confirmation: Mapping[str, Sequence[Any]],
) -> dict[str, Any]:
    """Rank parent nuisance designs with donor identity bound at every row."""
    assert_no_forbidden_remedy_declared()
    results: dict[str, Any] = {
        "stage": STAGES[0], "checks": {}, "donor_order": {},
        "design_roots": {},
    }

    role_cache: dict[str, tuple[list[str], list[Any], list[Any]]] = {}
    for role, data in (("DISCOVERY", discovery), ("CONFIRMATION", confirmation)):
        donor_ids = _donor_ids(data, what=role)
        ages = list(data["age"])
        sexes = list(data["sex"])
        design = nuisance_design(ages, sexes)
        results["checks"][role] = assert_full_rank(
            design, what="%s nuisance" % role)
        results["donor_order"][role] = donor_ids
        results["design_roots"][role] = _design_root(
            "%s nuisance" % role, donor_ids, design)
        role_cache[role] = (donor_ids, ages, sexes)

    donor_ids, ages, sexes = role_cache["DISCOVERY"]
    folds = {}
    fold_roots = {}
    for held_out, held_out_donor in enumerate(donor_ids):
        fold_ids = donor_ids[:held_out] + donor_ids[held_out + 1:]
        fold_ages = ages[:held_out] + ages[held_out + 1:]
        fold_sexes = sexes[:held_out] + sexes[held_out + 1:]
        design = nuisance_design(fold_ages, fold_sexes)
        folds[str(held_out_donor)] = assert_full_rank(
            design, what="DISCOVERY LOODO fold holding out donor %s"
            % held_out_donor)
        fold_roots[str(held_out_donor)] = _design_root(
            "DISCOVERY LOODO holdout %s" % held_out_donor,
            fold_ids, design)
    results["checks"]["DISCOVERY_LOODO_FOLDS"] = len(folds)
    results["loodo_ranks"] = folds
    results["design_roots"]["DISCOVERY_LOODO_FOLDS"] = fold_roots
    return results


# --- Stage B ---------------------------------------------------------------

def stage_b_state_designs(
        *,
        confirmation: Mapping[str, Sequence[Any]],
        state_score: Mapping[str, Any],
        immune_fraction: Mapping[str, Any],
        q_depth: Mapping[str, Any],
        q_detect: Mapping[str, Any],
        response: Any = None,
) -> dict[str, Any]:
    """Check confirmation designs after donor-keyed covariate joins.

    A covariate array with the right length is insufficient: a permutation can
    change rank while preserving shape.  Every covariate is therefore joined by
    donor_id to the confirmation authority's exact donor order.
    """
    if response is not None:
        raise AssertionError(
            "%s: estimability is a property of the design matrix; the response "
            "must not be supplied to a pathology-blind check"
            % STOP_RESPONSE_PRESENT)
    assert_no_forbidden_remedy_declared()

    donor_ids = _donor_ids(confirmation, what="CONFIRMATION")
    n = len(donor_ids)
    nuisance = nuisance_design(confirmation["age"], confirmation["sex"])
    state_values = _bind_by_donor(state_score, donor_ids, what="STATE_SCORE")
    immune_values = _bind_by_donor(
        immune_fraction, donor_ids, what="IMMUNE_FRACTION")
    depth_values = _bind_by_donor(q_depth, donor_ids, what="Q_DEPTH")
    detect_values = _bind_by_donor(q_detect, donor_ids, what="Q_DETECT")

    state = [[v] for v in state_values]
    immune = [[v] for v in immune_values]
    designs = {
        "primary": _augment(nuisance, state),
        "composition": _augment(_augment(nuisance, immune), state),
        "measurement": _augment(
            _augment(nuisance, [[d, t] for d, t in
                                zip(depth_values, detect_values)]), state),
    }
    checks = {name: assert_full_rank(matrix, what="confirmation %s design" % name)
              for name, matrix in designs.items()}
    roots = {name: _design_root("confirmation %s design" % name,
                                donor_ids, matrix)
             for name, matrix in designs.items()}
    return {
        "stage": STAGES[1],
        "checks": checks,
        "residual_df": {name: n - len(designs[name][0]) for name in designs},
        "donor_order": list(donor_ids),
        "design_roots": roots,
    }


# --- Stage C ---------------------------------------------------------------

def stage_c_tail_designs(
        *,
        tail_donors: Mapping[str, Sequence[Any]],
        state_score: Mapping[str, Any],
        tail_prevalence: Mapping[str, Any],
        immune_fraction: Mapping[str, Any],
        q_depth: Mapping[str, Any],
        q_detect: Mapping[str, Any],
        response: Any = None,
) -> dict[str, Any]:
    """Check tail designs after exact donor-keyed joins."""
    if response is not None:
        raise AssertionError(
            "%s: estimability is a property of the design matrix; the response "
            "must not be supplied to a pathology-blind check"
            % STOP_RESPONSE_PRESENT)
    assert_no_forbidden_remedy_declared()

    donor_ids = _donor_ids(tail_donors, what="TAIL")
    n = len(donor_ids)
    nuisance = nuisance_design(tail_donors["age"], tail_donors["sex"])
    state = _bind_by_donor(state_score, donor_ids, what="tail STATE_SCORE")
    tail = _bind_by_donor(
        tail_prevalence, donor_ids, what="TAIL_PREVALENCE")
    immune = _bind_by_donor(
        immune_fraction, donor_ids, what="tail IMMUNE_FRACTION")
    depth = _bind_by_donor(q_depth, donor_ids, what="tail Q_DEPTH")
    detect = _bind_by_donor(q_detect, donor_ids, what="tail Q_DETECT")

    with_state = _augment(nuisance, [[s] for s in state])
    designs = {
        "tail_primary": _augment(with_state, [[t] for t in tail]),
        "tail_composition": _augment(_augment(with_state, [[i] for i in immune]),
                                     [[t] for t in tail]),
        "tail_measurement": _augment(
            _augment(with_state, [[d, q] for d, q in zip(depth, detect)]),
            [[t] for t in tail]),
    }
    checks = {name: assert_full_rank(matrix, what="%s design" % name)
              for name, matrix in designs.items()}
    roots = {name: _design_root("%s design" % name, donor_ids, matrix)
             for name, matrix in designs.items()}
    return {
        "stage": STAGES[2],
        "checks": checks,
        "tail_inference_n": n,
        "residual_df": {name: n - len(designs[name][0]) for name in designs},
        "donor_order": list(donor_ids),
        "design_roots": roots,
    }



def _fixture_key_by_donor(donor_ids: Sequence[str], values: Sequence[Any], *,
                          what: str) -> dict[str, Any]:
    """Fixture-only bridge for legacy positional tests."""
    if len(values) != len(donor_ids):
        raise AssertionError(
            "%s: %s has %d values for %d donors"
            % (STOP_INPUT_SHAPE, what, len(values), len(donor_ids)))
    return {str(donor): value for donor, value in zip(donor_ids, values)}


def _stage_b_state_designs_positional_fixture(
        *,
        confirmation: Mapping[str, Sequence[Any]],
        state_score: Sequence[Any],
        immune_fraction: Sequence[Any],
        q_depth: Sequence[Any],
        q_detect: Sequence[Any],
        response: Any = None,
) -> dict[str, Any]:
    """Fixture-only adapter; production stage_b_state_designs forbids arrays."""
    donor_ids = _donor_ids(confirmation, what="CONFIRMATION")
    return stage_b_state_designs(
        confirmation=confirmation,
        state_score=_fixture_key_by_donor(
            donor_ids, state_score, what="STATE_SCORE"),
        immune_fraction=_fixture_key_by_donor(
            donor_ids, immune_fraction, what="IMMUNE_FRACTION"),
        q_depth=_fixture_key_by_donor(donor_ids, q_depth, what="Q_DEPTH"),
        q_detect=_fixture_key_by_donor(donor_ids, q_detect, what="Q_DETECT"),
        response=response,
    )


def _stage_c_tail_designs_positional_fixture(
        *,
        tail_donors: Mapping[str, Sequence[Any]],
        state_score: Sequence[Any],
        tail_prevalence: Sequence[Any],
        immune_fraction: Sequence[Any],
        q_depth: Sequence[Any],
        q_detect: Sequence[Any],
        response: Any = None,
) -> dict[str, Any]:
    """Fixture-only adapter; production stage_c_tail_designs forbids arrays."""
    donor_ids = _donor_ids(tail_donors, what="TAIL")
    return stage_c_tail_designs(
        tail_donors=tail_donors,
        state_score=_fixture_key_by_donor(
            donor_ids, state_score, what="tail STATE_SCORE"),
        tail_prevalence=_fixture_key_by_donor(
            donor_ids, tail_prevalence, what="TAIL_PREVALENCE"),
        immune_fraction=_fixture_key_by_donor(
            donor_ids, immune_fraction, what="tail IMMUNE_FRACTION"),
        q_depth=_fixture_key_by_donor(
            donor_ids, q_depth, what="tail Q_DEPTH"),
        q_detect=_fixture_key_by_donor(
            donor_ids, q_detect, what="tail Q_DETECT"),
        response=response,
    )


def preflight_root(results: Sequence[Mapping[str, Any]]) -> str:
    """Digest stages, ranks, donor order and exact design identities."""
    parts = [_typed(DOMAIN_TAG), _typed(SCHEMA), _typed(NAMESPACE),
             _typed(list(FORBIDDEN_REMEDIES)), _typed(len(results))]
    for result in results:
        checks = result["checks"]
        parts.append(_typed([str(result["stage"]),
                             [[str(k), int(checks[k])] for k in sorted(checks)]]))
        donor_order = result.get("donor_order", [])
        if isinstance(donor_order, Mapping):
            serial_donors = [[str(k), [str(x) for x in donor_order[k]]]
                             for k in sorted(donor_order)]
        else:
            serial_donors = [str(x) for x in donor_order]
        parts.append(_typed(["donor_order", serial_donors]))
        design_roots = result.get("design_roots", {})
        serial_roots = []
        for key in sorted(design_roots):
            value = design_roots[key]
            if isinstance(value, Mapping):
                serial_roots.append([
                    str(key),
                    [[str(k), str(value[k])] for k in sorted(value)],
                ])
            else:
                serial_roots.append([str(key), str(value)])
        parts.append(_typed(["design_roots", serial_roots]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def assert_stage_order(results: Sequence[Mapping[str, Any]]) -> bool:
    """Stages must be recorded in order and without gaps.

    Running Stage B before Stage A would mean the state designs were checked on a
    role assignment whose own nuisance design had never been verified.
    """
    seen = [str(result["stage"]) for result in results]
    if seen != list(STAGES[:len(seen)]):
        raise AssertionError("%s: stages ran as %r, expected the prefix %r"
                             % (STOP_STAGE_ORDER, seen,
                                list(STAGES[:len(seen)])))
    return True
