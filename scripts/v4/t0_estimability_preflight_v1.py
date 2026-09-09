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
STOP_DONOR_ALIGNMENT = "STOP_T0_ESTIMABILITY_DONOR_IDENTITY_OR_ORDER_UNBOUND"
STOP_PARENT_AUTHORITY = "STOP_T0_ESTIMABILITY_PARENT_AUTHORITY_UNBOUND"
STOP_NUMERICAL_AUTHORITY = "STOP_T0_ESTIMABILITY_NUMERICAL_PRIMITIVE_AUTHORITY_UNBOUND"

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
    return [list(row) + [float(v) for v in more] for row, more in zip(base, extra)]


# --- Stage A ---------------------------------------------------------------

def stage_a_parent_nuisance(
        *,
        discovery: Mapping[str, Sequence[Any]],
        confirmation: Mapping[str, Sequence[Any]],
) -> dict[str, Any]:
    """Rank of the parent nuisance design on both roles and every LOODO fold.

    The LOODO folds matter because the frozen discovery fit refits with each
    donor held out. A design that is full rank on all 28 discovery donors can
    still be deficient in one fold, and that fold would fail during fitting
    rather than at preflight.
    """
    assert_no_forbidden_remedy_declared()
    results: dict[str, Any] = {"stage": STAGES[0], "checks": {}}

    for role, data in (("DISCOVERY", discovery), ("CONFIRMATION", confirmation)):
        design = nuisance_design(data["age"], data["sex"])
        results["checks"][role] = assert_full_rank(design, what="%s nuisance" % role)

    ages = list(discovery["age"])
    sexes = list(discovery["sex"])
    folds = {}
    for held_out in range(len(ages)):
        fold_ages = ages[:held_out] + ages[held_out + 1:]
        fold_sexes = sexes[:held_out] + sexes[held_out + 1:]
        design = nuisance_design(fold_ages, fold_sexes)
        folds[held_out] = assert_full_rank(
            design, what="DISCOVERY LOODO fold holding out donor index %d" % held_out)
    results["checks"]["DISCOVERY_LOODO_FOLDS"] = len(folds)
    results["loodo_ranks"] = folds
    return results


# --- Stage B ---------------------------------------------------------------

def stage_b_state_designs(
        *,
        confirmation: Mapping[str, Sequence[Any]],
        state_score: Sequence[Any],
        immune_fraction: Sequence[Any],
        q_depth: Sequence[Any],
        q_detect: Sequence[Any],
        response: Any = None,
) -> dict[str, Any]:
    """The three confirmation designs, checked before any AT8 access.

    `response` exists only to be refused. Rank is a property of the design
    matrix, so supplying the outcome to this check would be both unnecessary and
    a pathology-access violation.
    """
    if "donor_id" in confirmation:
        raise AssertionError(
            "%s: positional Stage B inputs are synthetic-only when donor IDs are "
            "present; use stage_b_state_designs_bound for production alignment"
            % STOP_DONOR_ALIGNMENT)
    if response is not None:
        raise AssertionError(
            "%s: estimability is a property of the design matrix; the response "
            "must not be supplied to a pathology-blind check"
            % STOP_RESPONSE_PRESENT)
    assert_no_forbidden_remedy_declared()

    n = len(list(confirmation["age"]))
    nuisance = nuisance_design(confirmation["age"], confirmation["sex"])
    state = [[v] for v in _column(state_score, what="STATE_SCORE", n=n)]
    immune = [[v] for v in _column(immune_fraction, what="IMMUNE_FRACTION", n=n)]
    depth = _column(q_depth, what="Q_DEPTH", n=n)
    detect = _column(q_detect, what="Q_DETECT", n=n)

    designs = {
        "primary": _augment(nuisance, state),
        "composition": _augment(_augment(nuisance, immune), state),
        "measurement": _augment(
            _augment(nuisance, [[d, t] for d, t in zip(depth, detect)]), state),
    }
    checks = {name: assert_full_rank(matrix, what="confirmation %s design" % name)
              for name, matrix in designs.items()}
    return {"stage": STAGES[1], "checks": checks,
            "residual_df": {name: n - len(designs[name][0]) for name in designs}}


# --- Stage C ---------------------------------------------------------------

def stage_c_tail_designs(
        *,
        tail_donors: Mapping[str, Sequence[Any]],
        state_score: Sequence[Any],
        tail_prevalence: Sequence[Any],
        immune_fraction: Sequence[Any],
        q_depth: Sequence[Any],
        q_detect: Sequence[Any],
        response: Any = None,
) -> dict[str, Any]:
    """The tail designs, carrying frozen STATE_SCORE and TAIL_PREVALENCE.

    The tail arm is evaluated on the tail-measurable subset of the confirmation
    donors, whose size the frozen contract restricts to 17 or 18, so this stage
    takes its own donor set rather than reusing the full confirmation one.
    """
    if "donor_id" in tail_donors:
        raise AssertionError(
            "%s: positional Stage C inputs are synthetic-only when donor IDs are "
            "present; use stage_c_tail_designs_bound for production alignment"
            % STOP_DONOR_ALIGNMENT)
    if response is not None:
        raise AssertionError(
            "%s: estimability is a property of the design matrix; the response "
            "must not be supplied to a pathology-blind check"
            % STOP_RESPONSE_PRESENT)
    assert_no_forbidden_remedy_declared()

    n = len(list(tail_donors["age"]))
    nuisance = nuisance_design(tail_donors["age"], tail_donors["sex"])
    state = _column(state_score, what="tail STATE_SCORE", n=n)
    tail = _column(tail_prevalence, what="TAIL_PREVALENCE", n=n)
    immune = _column(immune_fraction, what="tail IMMUNE_FRACTION", n=n)
    depth = _column(q_depth, what="tail Q_DEPTH", n=n)
    detect = _column(q_detect, what="tail Q_DETECT", n=n)

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
    return {"stage": STAGES[2], "checks": checks,
            "tail_inference_n": n,
            "residual_df": {name: n - len(designs[name][0]) for name in designs}}



def _hex64(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(ch in "0123456789abcdef" for ch in value))


def _bound_donor_order(data: Mapping[str, Sequence[Any]], *, what: str,
                       expected_n: int | None = None) -> tuple[str, ...]:
    if "donor_id" not in data:
        raise AssertionError("%s: %s lacks donor_id" % (STOP_DONOR_ALIGNMENT, what))
    donors = tuple(str(v) for v in data["donor_id"])
    if not donors or any(not donor for donor in donors):
        raise AssertionError("%s: %s has blank donor identity"
                             % (STOP_DONOR_ALIGNMENT, what))
    if len(set(donors)) != len(donors):
        raise AssertionError("%s: %s has duplicate donor identity"
                             % (STOP_DONOR_ALIGNMENT, what))
    if expected_n is not None and len(donors) != int(expected_n):
        raise AssertionError("%s: %s has %d donors, expected %d"
                             % (STOP_DONOR_ALIGNMENT, what, len(donors),
                                int(expected_n)))
    if len(data.get("age", ())) != len(donors) or len(data.get("sex", ())) != len(donors):
        raise AssertionError("%s: %s age/sex lengths do not match donor order"
                             % (STOP_DONOR_ALIGNMENT, what))
    return donors


def _bound_values(values_by_donor: Mapping[str, Any], donors: Sequence[str],
                  *, what: str) -> list[float]:
    keys = {str(key) for key in values_by_donor}
    expected = set(donors)
    if keys != expected:
        raise AssertionError(
            "%s: %s donor set mismatch; values-only=%r donors-only=%r"
            % (STOP_DONOR_ALIGNMENT, what, sorted(keys - expected),
               sorted(expected - keys)))
    return _column([values_by_donor[donor] for donor in donors],
                   what=what, n=len(donors))


def _bind_authority_roots(authority_roots: Mapping[str, str],
                          required: Sequence[str]) -> list[list[str]]:
    missing = [name for name in required if name not in authority_roots]
    if missing:
        raise AssertionError("%s: missing %r"
                             % (STOP_PARENT_AUTHORITY, missing))
    bound = []
    for name in required:
        value = authority_roots[name]
        if not _hex64(value):
            raise AssertionError("%s: %s is not a lowercase SHA-256"
                                 % (STOP_PARENT_AUTHORITY, name))
        bound.append([str(name), str(value)])
    return bound


def _numerical_authority_root(value: str) -> str:
    if not _hex64(value):
        raise AssertionError(
            "%s: production preflight requires an externally frozen authority "
            "for the exact accepted V20 nuisance/rank primitives or a separately "
            "proven equivalent implementation"
            % STOP_NUMERICAL_AUTHORITY)
    return str(value)


def stage_a_parent_nuisance_bound(
        *,
        discovery: Mapping[str, Sequence[Any]],
        confirmation: Mapping[str, Sequence[Any]],
        authority_roots: Mapping[str, str],
        numerical_primitive_authority_root_sha256: str,
) -> dict[str, Any]:
    """Donor-bound Stage A; positional Stage A remains a synthetic primitive."""
    disc_donors = _bound_donor_order(discovery, what="DISCOVERY")
    conf_donors = _bound_donor_order(confirmation, what="CONFIRMATION",
                                     expected_n=18)
    roots = _bind_authority_roots(
        authority_roots,
        ("eligible_donor_authority_root_sha256",
         "donor_role_authority_root_sha256",
         "donor_metadata_authority_root_sha256"))
    numerical = _numerical_authority_root(
        numerical_primitive_authority_root_sha256)
    result = stage_a_parent_nuisance(
        discovery={"age": discovery["age"], "sex": discovery["sex"]},
        confirmation={"age": confirmation["age"], "sex": confirmation["sex"]})
    result["donor_order"] = {
        "DISCOVERY": list(disc_donors), "CONFIRMATION": list(conf_donors)}
    result["authority_roots"] = roots
    result["numerical_primitive_authority_root_sha256"] = numerical
    result["design_columns"] = ["INTERCEPT", "AGE_CENTERED",
                                "AGE_CENTERED_SQUARED", "SEX_BINARY"]
    return result


def stage_b_state_designs_bound(
        *,
        confirmation: Mapping[str, Sequence[Any]],
        state_score_by_donor: Mapping[str, Any],
        immune_fraction_by_donor: Mapping[str, Any],
        q_depth_by_donor: Mapping[str, Any],
        q_detect_by_donor: Mapping[str, Any],
        authority_roots: Mapping[str, str],
        numerical_primitive_authority_root_sha256: str,
        response: Any = None,
) -> dict[str, Any]:
    """Join every Stage B covariate by donor identity before rank evaluation."""
    if response is not None:
        raise AssertionError("%s: response supplied to blind Stage B"
                             % STOP_RESPONSE_PRESENT)
    donors = _bound_donor_order(confirmation, what="CONFIRMATION",
                                expected_n=18)
    roots = _bind_authority_roots(
        authority_roots,
        ("eligible_donor_authority_root_sha256",
         "donor_role_authority_root_sha256",
         "donor_metadata_authority_root_sha256",
         "immune_fraction_authority_root_sha256",
         "technical_completeness_authority_root_sha256",
         "state_score_authority_root_sha256"))
    numerical = _numerical_authority_root(
        numerical_primitive_authority_root_sha256)
    state = _bound_values(state_score_by_donor, donors, what="STATE_SCORE")
    immune = _bound_values(immune_fraction_by_donor, donors,
                           what="IMMUNE_FRACTION")
    depth = _bound_values(q_depth_by_donor, donors, what="Q_DEPTH")
    detect = _bound_values(q_detect_by_donor, donors, what="Q_DETECT")
    result = stage_b_state_designs(
        confirmation={"age": confirmation["age"], "sex": confirmation["sex"]},
        state_score=state, immune_fraction=immune,
        q_depth=depth, q_detect=detect)
    result["donor_order"] = list(donors)
    result["authority_roots"] = roots
    result["numerical_primitive_authority_root_sha256"] = numerical
    result["design_columns"] = {
        "primary": ["NUISANCE", "STATE_SCORE"],
        "composition": ["NUISANCE", "IMMUNE_FRACTION", "STATE_SCORE"],
        "measurement": ["NUISANCE", "Q_DEPTH", "Q_DETECT", "STATE_SCORE"],
    }
    return result


def stage_c_tail_designs_bound(
        *,
        tail_donors: Mapping[str, Sequence[Any]],
        state_score_by_donor: Mapping[str, Any],
        tail_prevalence_by_donor: Mapping[str, Any],
        immune_fraction_by_donor: Mapping[str, Any],
        q_depth_by_donor: Mapping[str, Any],
        q_detect_by_donor: Mapping[str, Any],
        authority_roots: Mapping[str, str],
        numerical_primitive_authority_root_sha256: str,
        response: Any = None,
) -> dict[str, Any]:
    """Join every Stage C covariate by exact tail-donor identity."""
    if response is not None:
        raise AssertionError("%s: response supplied to blind Stage C"
                             % STOP_RESPONSE_PRESENT)
    donors = _bound_donor_order(tail_donors, what="TAIL_CONFIRMATION")
    if len(donors) not in (17, 18):
        raise AssertionError("%s: tail donor count %d is outside frozen {17,18}"
                             % (STOP_INPUT_SHAPE, len(donors)))
    roots = _bind_authority_roots(
        authority_roots,
        ("eligible_donor_authority_root_sha256",
         "donor_role_authority_root_sha256",
         "donor_metadata_authority_root_sha256",
         "immune_fraction_authority_root_sha256",
         "technical_completeness_authority_root_sha256",
         "state_score_authority_root_sha256",
         "tail_authority_root_sha256"))
    numerical = _numerical_authority_root(
        numerical_primitive_authority_root_sha256)
    state = _bound_values(state_score_by_donor, donors, what="TAIL STATE_SCORE")
    tail = _bound_values(tail_prevalence_by_donor, donors,
                         what="TAIL_PREVALENCE")
    immune = _bound_values(immune_fraction_by_donor, donors,
                           what="TAIL IMMUNE_FRACTION")
    depth = _bound_values(q_depth_by_donor, donors, what="TAIL Q_DEPTH")
    detect = _bound_values(q_detect_by_donor, donors, what="TAIL Q_DETECT")
    result = stage_c_tail_designs(
        tail_donors={"age": tail_donors["age"], "sex": tail_donors["sex"]},
        state_score=state, tail_prevalence=tail,
        immune_fraction=immune, q_depth=depth, q_detect=detect)
    result["donor_order"] = list(donors)
    result["authority_roots"] = roots
    result["numerical_primitive_authority_root_sha256"] = numerical
    result["design_columns"] = {
        "tail_primary": ["NUISANCE", "STATE_SCORE", "TAIL_PREVALENCE"],
        "tail_composition": ["NUISANCE", "STATE_SCORE", "IMMUNE_FRACTION",
                             "TAIL_PREVALENCE"],
        "tail_measurement": ["NUISANCE", "STATE_SCORE", "Q_DEPTH", "Q_DETECT",
                             "TAIL_PREVALENCE"],
    }
    return result


def bound_preflight_root(results: Sequence[Mapping[str, Any]]) -> str:
    """Root over exact stages, donor order, authority roots and design columns."""
    parts = [_typed(DOMAIN_TAG), _typed(SCHEMA), _typed(NAMESPACE),
             _typed("BOUND_PREFLIGHT_V1"), _typed(len(results))]
    for result in results:
        parts.append(_typed(str(result["stage"])))
        donor_order = result.get("donor_order")
        if isinstance(donor_order, Mapping):
            for role in sorted(donor_order):
                parts.append(_typed([str(role)] + [str(v) for v in donor_order[role]]))
        else:
            parts.append(_typed([str(v) for v in donor_order]))
        for name, value in result.get("authority_roots", []):
            parts.append(_typed([str(name), str(value)]))
        parts.append(_typed(str(
            result["numerical_primitive_authority_root_sha256"])))
        checks = result["checks"]
        for name in sorted(checks):
            parts.append(_typed([str(name), int(checks[name])]))
    return hashlib.sha256(b"".join(parts)).hexdigest()

def preflight_root(results: Sequence[Mapping[str, Any]]) -> str:
    """Digest over the stages actually run and their outcomes."""
    parts = [_typed(DOMAIN_TAG), _typed(SCHEMA), _typed(NAMESPACE),
             _typed(list(FORBIDDEN_REMEDIES)), _typed(len(results))]
    for result in results:
        checks = result["checks"]
        parts.append(_typed([str(result["stage"]),
                             [[str(k), int(checks[k])] for k in sorted(checks)]]))
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
