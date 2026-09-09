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
STOP_POSITIONAL = "STOP_T0_ESTIMABILITY_POSITIONAL_ARRAYS_REFUSED"
STOP_DONOR_SET = "STOP_T0_ESTIMABILITY_DONOR_SET_MISMATCH"
STOP_DONOR_ORDER = "STOP_T0_ESTIMABILITY_DONOR_ORDER_NOT_AUTHORITATIVE"
STOP_RECORDS_ROOT = "STOP_T0_ESTIMABILITY_RECORDS_ROOT_MISMATCH"
STOP_FIELD_ABSENT = "STOP_T0_ESTIMABILITY_DONOR_RECORD_FIELD_ABSENT"

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

def _stage_a_from_arrays(
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

def _stage_b_from_arrays(
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

def _stage_c_from_arrays(
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


def _preflight_root_from_rank_only_fixture(
        results: Sequence[Mapping[str, Any]]) -> str:
    """Fixture-only legacy root; production must bind donor-record identities."""
    parts = [_typed(DOMAIN_TAG), _typed("RANK_ONLY_FIXTURE"),
             _typed(len(results))]
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


# ---------------------------------------------------------------------------
# Donor-keyed stages.
#
# The array-based primitives above take independent sequences for age, sex,
# STATE_SCORE, IMMUNE_FRACTION, Q_DEPTH, Q_DETECT and TAIL_PREVALENCE, aligned
# only by position. An external review pointed out the consequence: permuting one
# covariate is structurally valid and changes matrix rank, so a design that is
# genuinely NOT_ESTIMABLE can be made full rank by shuffling a column, and
# nothing in the preflight would notice.
#
# Values are therefore keyed by donor here, the donor order comes from the role
# authority rather than from the caller's array indices, and the whole record set
# is bound by a digest. A permutation reassigns values across donors, which moves
# that digest, so it is refused rather than silently accepted.
# ---------------------------------------------------------------------------

STAGE_B_FIELDS = ("age", "sex", "STATE_SCORE", "IMMUNE_FRACTION",
                  "Q_DEPTH", "Q_DETECT")
STAGE_C_FIELDS = ("age", "sex", "STATE_SCORE", "TAIL_PREVALENCE",
                  "IMMUNE_FRACTION", "Q_DEPTH", "Q_DETECT")


def refuse_positional_arrays(**kwargs: Any) -> None:
    """Explicit refusal so the positional parameters cannot quietly return."""
    offending = sorted(k for k in kwargs
                       if k in ("state_score", "immune_fraction", "q_depth",
                                "q_detect", "tail_prevalence", "confirmation",
                                "discovery", "tail_donors"))
    if offending:
        raise AssertionError(
            "%s: %s may not be supplied as positional arrays; estimability "
            "inputs are keyed by donor so a permutation cannot change rank while "
            "staying structurally valid" % (STOP_POSITIONAL, ", ".join(offending)))


def _fixed(value: float, places: int = 12) -> str:
    """Exact IEEE-754 text for the value the design matrix actually consumes.

    The previous 12-decimal rounding let distinct design matrices share a
    records root. `places` remains only for backward call compatibility and is
    deliberately ignored.
    """
    import math

    number = float(value)
    if not math.isfinite(number):
        raise AssertionError("%s: %r is not finite" % (STOP_INPUT_SHAPE, value))
    return number.hex()


def records_root(donor_order: Sequence[str],
                 records: Mapping[str, Mapping[str, Any]],
                 fields: Sequence[str]) -> str:
    """Digest binding every (donor, field, value) triple in authoritative order.

    This is what makes a permutation detectable. Reassigning values across
    donors changes the triples, so it changes the root; positional arrays had no
    such property because the donor was never part of the datum.
    """
    parts = [_typed(DOMAIN_TAG), _typed("DONOR_RECORDS"),
             _typed(list(fields)), _typed(len(donor_order))]
    for donor in donor_order:
        row = records[str(donor)]
        parts.append(_typed(str(donor)))
        for field in fields:
            if field not in row:
                raise AssertionError("%s: %s lacks %r"
                                     % (STOP_FIELD_ABSENT, donor, field))
            parts.append(_typed([field, _fixed(row[field])]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def _bind_records(donor_order: Sequence[str],
                  records: Mapping[str, Mapping[str, Any]],
                  fields: Sequence[str],
                  expected_records_root_sha256: str) -> tuple[str, ...]:
    """Check the donor set, the order and the record digest before use."""
    order = [str(d) for d in donor_order]
    if len(order) != len(set(order)):
        duplicates = sorted({d for d in order if order.count(d) > 1})
        raise AssertionError("%s: the donor order repeats %s"
                             % (STOP_DONOR_ORDER, duplicates))
    supplied = {str(d) for d in records}
    if supplied != set(order):
        raise AssertionError(
            "%s: records-only %s, order-only %s"
            % (STOP_DONOR_SET, sorted(supplied - set(order)),
               sorted(set(order) - supplied)))
    actual = records_root(order, records, fields)
    if actual != str(expected_records_root_sha256):
        raise AssertionError(
            "%s: the donor records digest is %s, externally expected %s; a "
            "reassignment of values across donors moves this digest"
            % (STOP_RECORDS_ROOT, actual, expected_records_root_sha256))
    return tuple(order)


def _donor_column(order: Sequence[str],
                  records: Mapping[str, Mapping[str, Any]],
                  field: str) -> list[float]:
    """Build a column by walking the authoritative donor order.

    Named distinctly from the positional `_column` above: an earlier revision of
    this patch reused that name and shadowed it, which broke `nuisance_design`.
    """
    return [float(records[str(donor)][field]) for donor in order]


def stage_a_parent_nuisance(
        *,
        discovery_order: Sequence[str],
        discovery_records: Mapping[str, Mapping[str, Any]],
        expected_discovery_records_root_sha256: str,
        confirmation_order: Sequence[str],
        confirmation_records: Mapping[str, Mapping[str, Any]],
        expected_confirmation_records_root_sha256: str,
) -> dict[str, Any]:
    """Stage A over donor-keyed records."""
    fields = ("age", "sex")
    discovery = _bind_records(discovery_order, discovery_records, fields,
                              expected_discovery_records_root_sha256)
    confirmation = _bind_records(confirmation_order, confirmation_records, fields,
                                 expected_confirmation_records_root_sha256)
    result = _stage_a_from_arrays(
        discovery={"age": _donor_column(discovery, discovery_records, "age"),
                   "sex": _donor_column(discovery, discovery_records, "sex")},
        confirmation={"age": _donor_column(confirmation, confirmation_records, "age"),
                      "sex": _donor_column(confirmation, confirmation_records, "sex")})
    result["donor_bound"] = True
    result["discovery_records_root_sha256"] = str(
        expected_discovery_records_root_sha256)
    result["confirmation_records_root_sha256"] = str(
        expected_confirmation_records_root_sha256)
    result["discovery_order"] = list(discovery)
    result["confirmation_order"] = list(confirmation)
    return result


def stage_b_state_designs(
        *,
        confirmation_order: Sequence[str],
        records: Mapping[str, Mapping[str, Any]],
        expected_records_root_sha256: str,
        response: Any = None,
) -> dict[str, Any]:
    """Stage B over donor-keyed records."""
    if response is not None:
        raise AssertionError(
            "%s: estimability is a property of the design matrix; the response "
            "must not be supplied to a pathology-blind check"
            % STOP_RESPONSE_PRESENT)
    order = _bind_records(confirmation_order, records, STAGE_B_FIELDS,
                          expected_records_root_sha256)
    result = _stage_b_from_arrays(
        confirmation={"age": _donor_column(order, records, "age"),
                      "sex": _donor_column(order, records, "sex")},
        state_score=_donor_column(order, records, "STATE_SCORE"),
        immune_fraction=_donor_column(order, records, "IMMUNE_FRACTION"),
        q_depth=_donor_column(order, records, "Q_DEPTH"),
        q_detect=_donor_column(order, records, "Q_DETECT"))
    result["donor_bound"] = True
    result["records_root_sha256"] = str(expected_records_root_sha256)
    result["confirmation_order"] = list(order)
    return result


def stage_c_tail_designs(
        *,
        tail_order: Sequence[str],
        records: Mapping[str, Mapping[str, Any]],
        expected_records_root_sha256: str,
        response: Any = None,
) -> dict[str, Any]:
    """Stage C over donor-keyed records."""
    if response is not None:
        raise AssertionError(
            "%s: estimability is a property of the design matrix; the response "
            "must not be supplied to a pathology-blind check"
            % STOP_RESPONSE_PRESENT)
    order = _bind_records(tail_order, records, STAGE_C_FIELDS,
                          expected_records_root_sha256)
    result = _stage_c_from_arrays(
        tail_donors={"age": _donor_column(order, records, "age"),
                     "sex": _donor_column(order, records, "sex")},
        state_score=_donor_column(order, records, "STATE_SCORE"),
        tail_prevalence=_donor_column(order, records, "TAIL_PREVALENCE"),
        immune_fraction=_donor_column(order, records, "IMMUNE_FRACTION"),
        q_depth=_donor_column(order, records, "Q_DEPTH"),
        q_detect=_donor_column(order, records, "Q_DETECT"))
    result["donor_bound"] = True
    result["records_root_sha256"] = str(expected_records_root_sha256)
    result["tail_order"] = list(order)
    return result

def preflight_root(results: Sequence[Mapping[str, Any]]) -> str:
    """Bind the exact donor-bound designs that were checked, not ranks alone."""
    assert_stage_order(results)
    parts = [_typed(DOMAIN_TAG), _typed(SCHEMA), _typed(NAMESPACE),
             _typed(list(FORBIDDEN_REMEDIES)), _typed(len(results))]
    for result in results:
        if result.get("donor_bound") is not True:
            raise AssertionError(
                "%s: stage %r is not a donor-bound production result"
                % (STOP_POSITIONAL, result.get("stage")))
        stage = str(result["stage"])
        checks = result["checks"]
        parts.append(_typed(stage))
        parts.append(_typed(
            [[str(k), int(checks[k])] for k in sorted(checks)]))

        if stage == STAGES[0]:
            for field in ("discovery_records_root_sha256",
                          "confirmation_records_root_sha256"):
                value = str(result.get(field, ""))
                if len(value) != 64:
                    raise AssertionError(
                        "%s: Stage A lacks %s" % (STOP_RECORDS_ROOT, field))
                parts.append(_typed([field, value]))
            discovery_order = [str(x) for x in result.get("discovery_order", ())]
            confirmation_order = [str(x) for x in result.get("confirmation_order", ())]
            if not discovery_order or not confirmation_order:
                raise AssertionError(
                    "%s: Stage A donor orders are absent" % STOP_DONOR_ORDER)
            parts.append(_typed(["discovery_order", discovery_order]))
            parts.append(_typed(["confirmation_order", confirmation_order]))
            loodo = result.get("loodo_ranks", {})
            parts.append(_typed([
                "loodo_ranks",
                [[str(k), int(loodo[k])] for k in sorted(
                    loodo, key=lambda value: int(value))],
            ]))
        elif stage == STAGES[1]:
            root = str(result.get("records_root_sha256", ""))
            order = [str(x) for x in result.get("confirmation_order", ())]
            if len(root) != 64 or not order:
                raise AssertionError(
                    "%s: Stage B records root/order absent" % STOP_RECORDS_ROOT)
            parts.append(_typed(["records_root_sha256", root]))
            parts.append(_typed(["confirmation_order", order]))
            residual = result.get("residual_df", {})
            parts.append(_typed([
                "residual_df",
                [[str(k), int(residual[k])] for k in sorted(residual)],
            ]))
        elif stage == STAGES[2]:
            root = str(result.get("records_root_sha256", ""))
            order = [str(x) for x in result.get("tail_order", ())]
            if len(root) != 64 or not order:
                raise AssertionError(
                    "%s: Stage C records root/order absent" % STOP_RECORDS_ROOT)
            parts.append(_typed(["records_root_sha256", root]))
            parts.append(_typed(["tail_order", order]))
            parts.append(_typed(["tail_inference_n",
                                 int(result["tail_inference_n"])]))
            residual = result.get("residual_df", {})
            parts.append(_typed([
                "residual_df",
                [[str(k), int(residual[k])] for k in sorted(residual)],
            ]))
        else:
            raise AssertionError(
                "%s: unknown stage %r" % (STOP_STAGE_ORDER, stage))
    return hashlib.sha256(b"".join(parts)).hexdigest()

