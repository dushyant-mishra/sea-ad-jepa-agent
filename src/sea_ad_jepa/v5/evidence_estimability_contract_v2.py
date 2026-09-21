"""Integrated V5 score-term estimability contract, V2.

This successor reconciles the PR #35 matrix/status representation with Claude's
group-aware V2 evidence contract. It is deliberately evidence-only: it does not
change the canonical attacker and does not select P1/P2/P3/P4.

Core invariant
--------------
A finite numeric correlation exists if and only if the term is ESTIMABLE.
Every non-estimable scientific state carries NaN. Undefined is never numeric zero.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np

DEFAULT_EPS = 1.0e-12
CORRELATION_TOL = 1.0e-9
SCHEMA_ID = "V5_SCORE_TERM_ESTIMABILITY_EVIDENCE_V2"

P1 = "P1_PROSPECTIVE_ELIGIBILITY"
P2 = "P2_ABSTAIN_AND_REWEIGHT"
P3 = "P3_CONDITIONAL_WITH_MANDATORY_COVERAGE"
P4 = "P4_COVERAGE_GUARDED_CONDITIONAL"
POLICIES = (P1, P2, P3, P4)
NOT_ESTIMABLE = "NOT_ESTIMABLE"


class ScoreTermStatus(IntEnum):
    ESTIMABLE = 0
    TARGET_NONVARIABLE = 1
    PREDICTION_NONVARIABLE = 2
    TARGET_AND_PREDICTION_NONVARIABLE = 3
    MISSING = 4
    INVALID_NUMERIC = 5


_STATUS_VALUES = {int(x) for x in ScoreTermStatus}
_STATUS_NAMES = {int(x): x.name for x in ScoreTermStatus}
_STATUS_CODES = {x.name: int(x) for x in ScoreTermStatus}


class NonEstimableError(RuntimeError):
    """Raised when an aggregate is requested without an explicit consequence policy."""


class ContractViolation(ValueError):
    """Raised when tagged scientific evidence violates the V2 contract."""


def _digest_array(role: str, value: np.ndarray) -> str:
    arr = np.ascontiguousarray(value)
    header = json.dumps(
        {"role": role, "dtype": arr.dtype.str, "shape": list(arr.shape)},
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    h = hashlib.sha256()
    h.update(header)
    h.update(b"\0")
    h.update(arr.tobytes(order="C"))
    return h.hexdigest()


def _validate_eps(eps: float) -> float:
    e = float(eps)
    if not np.isfinite(e) or e < 0:
        raise ContractViolation("eps must be finite and nonnegative")
    return e


def _validate_correlation_state(
    correlation: Any,
    status: Any,
    *,
    ndim: int,
) -> tuple[np.ndarray, np.ndarray]:
    value = np.array(correlation, dtype=np.float64, order="C", copy=True)
    state = np.array(status, dtype=np.uint8, order="C", copy=True)
    if value.ndim != ndim or value.size == 0:
        raise ContractViolation(f"correlation must be a nonempty {ndim}-D array")
    if state.shape != value.shape:
        raise ContractViolation("status must align exactly with correlation")
    unknown = sorted(set(map(int, np.unique(state))) - _STATUS_VALUES)
    if unknown:
        raise ContractViolation(f"unknown status codes: {unknown}")
    estimable = state == int(ScoreTermStatus.ESTIMABLE)
    if not np.all(np.isfinite(value[estimable])):
        raise ContractViolation("ESTIMABLE terms must contain finite correlations")
    if np.any(np.abs(value[estimable]) > 1.0 + CORRELATION_TOL):
        raise ContractViolation("ESTIMABLE terms carry |r| > 1 beyond tolerance")
    if np.any(np.isfinite(value[~estimable])):
        raise ContractViolation("non-estimable terms must serialize correlation as NaN")
    value[estimable] = np.clip(value[estimable], -1.0, 1.0)
    value.flags.writeable = False
    state.flags.writeable = False
    return value, state


def _classify_arrays(
    *,
    rss_y: np.ndarray,
    pred_ss: np.ndarray,
    cov: np.ndarray,
    available: np.ndarray,
    eps: float,
) -> tuple[np.ndarray, np.ndarray]:
    if not (rss_y.shape == pred_ss.shape == cov.shape == available.shape):
        raise ContractViolation("rss_y, pred_ss, cov, and availability must align")
    status = np.full(rss_y.shape, int(ScoreTermStatus.ESTIMABLE), dtype=np.uint8)
    correlation = np.full(rss_y.shape, np.nan, dtype=np.float64)

    status[~available] = int(ScoreTermStatus.MISSING)
    finite = np.isfinite(rss_y) & np.isfinite(pred_ss) & np.isfinite(cov)
    status[available & ~finite] = int(ScoreTermStatus.INVALID_NUMERIC)

    candidate = available & finite
    invalid_ss = candidate & ((rss_y < -eps) | (pred_ss < -eps))
    status[invalid_ss] = int(ScoreTermStatus.INVALID_NUMERIC)
    candidate &= ~invalid_ss

    y_bad = candidate & (rss_y <= eps)
    p_bad = candidate & (pred_ss <= eps)
    status[y_bad & ~p_bad] = int(ScoreTermStatus.TARGET_NONVARIABLE)
    status[p_bad & ~y_bad] = int(ScoreTermStatus.PREDICTION_NONVARIABLE)
    status[y_bad & p_bad] = int(ScoreTermStatus.TARGET_AND_PREDICTION_NONVARIABLE)

    estimable = candidate & ~y_bad & ~p_bad
    denom = np.sqrt(rss_y[estimable] * pred_ss[estimable])
    r = cov[estimable] / denom
    gross = ~np.isfinite(r) | (np.abs(r) > 1.0 + CORRELATION_TOL)

    flat_est = np.flatnonzero(estimable)
    flat_status = status.reshape(-1)
    flat_corr = correlation.reshape(-1)
    flat_status[flat_est[gross]] = int(ScoreTermStatus.INVALID_NUMERIC)
    keep = ~gross
    flat_corr[flat_est[keep]] = np.clip(r[keep], -1.0, 1.0)
    return correlation, status


@dataclass(frozen=True)
class ScoreObservationMatrixV2:
    """Target x donor correlation evidence with lossless per-term status."""

    correlation: Any
    status: Any
    eps: float = DEFAULT_EPS
    schema_id: str = SCHEMA_ID

    def __post_init__(self) -> None:
        corr, state = _validate_correlation_state(self.correlation, self.status, ndim=2)
        eps = _validate_eps(self.eps)
        if self.schema_id != SCHEMA_ID:
            raise ContractViolation("estimability schema drifted")
        object.__setattr__(self, "correlation", corr)
        object.__setattr__(self, "status", state)
        object.__setattr__(self, "eps", eps)

    @property
    def estimable_mask(self) -> np.ndarray:
        out = self.status == int(ScoreTermStatus.ESTIMABLE)
        out.flags.writeable = False
        return out

    @property
    def score(self) -> np.ndarray:
        out = np.full(self.correlation.shape, np.nan, dtype=np.float64)
        mask = self.estimable_mask
        out[mask] = np.square(self.correlation[mask])
        out.flags.writeable = False
        return out

    def status_counts(self) -> dict[str, int]:
        return {
            state.name: int(np.count_nonzero(self.status == int(state)))
            for state in ScoreTermStatus
        }

    def require_all_estimable(self) -> None:
        bad = int(self.status.size - np.count_nonzero(self.estimable_mask))
        if bad:
            raise NonEstimableError(
                "all terms must be estimable for this operation; "
                f"found {bad} non-estimable terms with counts={self.status_counts()}"
            )

    def canonical_digest(self) -> str:
        payload = {
            "schema": self.schema_id,
            "eps": self.eps,
            "correlation": _digest_array("correlation", self.correlation),
            "status": _digest_array("status", self.status),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()

    def to_terms(self, donor_group: Any) -> "ScoreTermsV2":
        groups = np.asarray(donor_group, dtype=np.int64)
        if groups.ndim != 1 or groups.size != self.correlation.shape[1]:
            raise ContractViolation("donor_group must align matrix columns")
        tiled = np.broadcast_to(groups, self.correlation.shape).reshape(-1)
        return ScoreTermsV2(
            values=self.correlation.reshape(-1),
            states=self.status.reshape(-1),
            group=tiled,
        )

    def to_json(self) -> str:
        payload = {
            "schema": self.schema_id,
            "eps": self.eps,
            "shape": list(self.correlation.shape),
            "correlation": [
                None if not np.isfinite(v) else float(v)
                for v in self.correlation.reshape(-1)
            ],
            "status": [
                _STATUS_NAMES[int(s)] for s in self.status.reshape(-1)
            ],
            "content_digest": self.canonical_digest(),
        }
        return json.dumps(payload, sort_keys=True, allow_nan=False)

    @staticmethod
    def from_json(text: str) -> "ScoreObservationMatrixV2":
        d = json.loads(text)
        if d.get("schema") != SCHEMA_ID:
            raise ContractViolation("unknown score-term matrix schema")
        shape = tuple(int(x) for x in d.get("shape", []))
        if len(shape) != 2 or min(shape, default=0) <= 0:
            raise ContractViolation("matrix shape must contain two positive dimensions")
        names = d.get("status", [])
        unknown = [x for x in names if x not in _STATUS_CODES]
        if unknown:
            raise ContractViolation(f"unknown status names: {sorted(set(unknown))[:5]}")
        corr = np.asarray(
            [np.nan if v is None else float(v) for v in d.get("correlation", [])],
            dtype=np.float64,
        )
        state = np.asarray([_STATUS_CODES[x] for x in names], dtype=np.uint8)
        if corr.size != int(np.prod(shape)) or state.size != corr.size:
            raise ContractViolation("serialized matrix length does not match shape")
        obj = ScoreObservationMatrixV2(
            correlation=corr.reshape(shape),
            status=state.reshape(shape),
            eps=float(d.get("eps", DEFAULT_EPS)),
        )
        if "content_digest" in d and d["content_digest"] != obj.canonical_digest():
            raise ContractViolation("content digest does not match matrix payload")
        return obj

    def to_npz(self, path: str | Path) -> None:
        np.savez_compressed(
            path,
            schema=np.array(SCHEMA_ID),
            eps=np.array(self.eps),
            correlation=self.correlation,
            status=self.status,
            content_digest=np.array(self.canonical_digest()),
        )

    @staticmethod
    def from_npz(path: str | Path) -> "ScoreObservationMatrixV2":
        with np.load(path, allow_pickle=False) as d:
            if str(d["schema"]) != SCHEMA_ID:
                raise ContractViolation("unknown score-term matrix schema")
            obj = ScoreObservationMatrixV2(
                correlation=d["correlation"],
                status=d["status"],
                eps=float(d["eps"]),
            )
            if "content_digest" in d.files and str(d["content_digest"]) != obj.canonical_digest():
                raise ContractViolation("content digest does not match matrix payload")
        return obj


def classify_correlation_terms(
    *,
    rss_y: Any,
    pred_ss: Any,
    cov: Any,
    available: Any | None = None,
    eps: float = DEFAULT_EPS,
) -> ScoreObservationMatrixV2:
    y = np.asarray(rss_y, dtype=np.float64)
    p = np.asarray(pred_ss, dtype=np.float64)
    c = np.asarray(cov, dtype=np.float64)
    if y.ndim != 2 or y.size == 0 or p.shape != y.shape or c.shape != y.shape:
        raise ContractViolation("rss_y, pred_ss, and cov must be aligned nonempty matrices")
    e = _validate_eps(eps)
    if available is None:
        avail = np.ones(y.shape, dtype=bool)
    else:
        avail = np.asarray(available, dtype=bool)
        if avail.shape != y.shape:
            raise ContractViolation("available must align with score terms")
    corr, status = _classify_arrays(rss_y=y, pred_ss=p, cov=c, available=avail, eps=e)
    return ScoreObservationMatrixV2(correlation=corr, status=status, eps=e)


@dataclass(frozen=True)
class ScoreTermsV2:
    """Tagged 1-D score terms for group-aware reporting and resampling."""

    values: Any
    states: Any
    group: Any

    def __post_init__(self) -> None:
        values, states = _validate_correlation_state(self.values, self.states, ndim=1)
        group = np.array(self.group, dtype=np.int64, order="C", copy=True)
        if group.shape != values.shape:
            raise ContractViolation("group must align score terms")
        group.flags.writeable = False
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "states", states)
        object.__setattr__(self, "group", group)

    @property
    def estimable(self) -> np.ndarray:
        out = self.states == int(ScoreTermStatus.ESTIMABLE)
        out.flags.writeable = False
        return out

    def counts(self) -> dict[str, int]:
        return {
            state.name: int(np.count_nonzero(self.states == int(state)))
            for state in ScoreTermStatus
        }

    def has_non_estimable(self) -> bool:
        return bool(np.any(~self.estimable))

    def content_digest(self) -> str:
        payload = {
            "schema": SCHEMA_ID,
            "values": _digest_array("correlation", self.values),
            "states": _digest_array("status", self.states),
            "group": _digest_array("group", self.group),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def from_scorer_components(
        *,
        cov: Sequence[float],
        rss_y: Sequence[float],
        pred_ss: Sequence[float],
        group: Sequence[int],
        present: Sequence[bool] | None = None,
        eps: float = DEFAULT_EPS,
    ) -> "ScoreTermsV2":
        c = np.asarray(cov, dtype=np.float64)
        y = np.asarray(rss_y, dtype=np.float64)
        p = np.asarray(pred_ss, dtype=np.float64)
        g = np.asarray(group, dtype=np.int64)
        if c.ndim != 1 or c.size == 0 or y.shape != c.shape or p.shape != c.shape or g.shape != c.shape:
            raise ContractViolation("cov, rss_y, pred_ss, and group must be aligned nonempty vectors")
        e = _validate_eps(eps)
        if present is None:
            avail = np.ones(c.shape, dtype=bool)
        else:
            avail = np.asarray(present, dtype=bool)
            if avail.shape != c.shape:
                raise ContractViolation("present must align score terms")
        values, states = _classify_arrays(
            rss_y=y, pred_ss=p, cov=c, available=avail, eps=e
        )
        return ScoreTermsV2(values=values, states=states, group=g)

    def to_json(self) -> str:
        return json.dumps(
            {
                "schema": SCHEMA_ID,
                "values": [None if not np.isfinite(v) else float(v) for v in self.values],
                "states": [_STATUS_NAMES[int(s)] for s in self.states],
                "group": [int(g) for g in self.group],
                "content_digest": self.content_digest(),
            },
            sort_keys=True,
            allow_nan=False,
        )

    @staticmethod
    def from_json(text: str) -> "ScoreTermsV2":
        d = json.loads(text)
        if d.get("schema") != SCHEMA_ID:
            raise ContractViolation("unknown score-term schema")
        names = d.get("states", [])
        unknown = [x for x in names if x not in _STATUS_CODES]
        if unknown:
            raise ContractViolation(f"unknown state names: {sorted(set(unknown))[:5]}")
        values = np.asarray(
            [np.nan if v is None else float(v) for v in d.get("values", [])],
            dtype=np.float64,
        )
        states = np.asarray([_STATUS_CODES[x] for x in names], dtype=np.uint8)
        group = np.asarray(d.get("group", []), dtype=np.int64)
        obj = ScoreTermsV2(values=values, states=states, group=group)
        if "content_digest" in d and d["content_digest"] != obj.content_digest():
            raise ContractViolation("content digest does not match the payload")
        return obj

    def to_npz(self, path: str | Path) -> None:
        np.savez_compressed(
            path,
            schema=np.array(SCHEMA_ID),
            values=self.values,
            states=self.states,
            group=self.group,
            content_digest=np.array(self.content_digest()),
        )

    @staticmethod
    def from_npz(path: str | Path) -> "ScoreTermsV2":
        with np.load(path, allow_pickle=False) as d:
            if str(d["schema"]) != SCHEMA_ID:
                raise ContractViolation("unknown score-term schema")
            obj = ScoreTermsV2(values=d["values"], states=d["states"], group=d["group"])
            if "content_digest" in d.files and str(d["content_digest"]) != obj.content_digest():
                raise ContractViolation("content digest does not match the payload")
        return obj


ScoreTerms = ScoreTermsV2
ESTIMABLE = int(ScoreTermStatus.ESTIMABLE)
TARGET_NON_VARIABLE = int(ScoreTermStatus.TARGET_NONVARIABLE)
PREDICTION_NON_VARIABLE = int(ScoreTermStatus.PREDICTION_NONVARIABLE)
TARGET_AND_PREDICTION_NON_VARIABLE = int(ScoreTermStatus.TARGET_AND_PREDICTION_NONVARIABLE)
MISSING = int(ScoreTermStatus.MISSING)
INVALID_NUMERIC = int(ScoreTermStatus.INVALID_NUMERIC)
SCHEMA = SCHEMA_ID
EPS = DEFAULT_EPS


@dataclass(frozen=True)
class AggregateV2:
    policy: str
    status: str
    conditional_statistic: float | None
    full_estimand_point_estimated: bool
    terms_total: int
    terms_estimable: int
    state_counts: dict[str, int]
    group_status: dict[str, str]
    group_coverage: dict[str, float]
    quantity_name: str
    note: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "policy": self.policy,
            "status": self.status,
            "conditional_statistic": self.conditional_statistic,
            "full_estimand_point_estimated": self.full_estimand_point_estimated,
            "terms_total": self.terms_total,
            "terms_estimable": self.terms_estimable,
            "coverage": self.terms_estimable / self.terms_total,
            "state_counts": self.state_counts,
            "group_status": self.group_status,
            "group_coverage": self.group_coverage,
            "quantity_name": self.quantity_name,
            "note": self.note,
        }


Aggregate = AggregateV2


def aggregate(
    terms: ScoreTermsV2,
    *,
    policy: str | None = None,
    square: bool = True,
    required_groups: Sequence[int] | None = None,
) -> AggregateV2:
    """Return an explicitly conditional group-balanced statistic.

    No missing-data consequence policy is selected by default. If any term is
    non-estimable, callers must name a policy. Required groups with zero terms or
    zero estimable terms are never silently dropped.
    """
    if policy is not None and policy not in POLICIES:
        raise ValueError(f"unknown policy {policy!r}; expected one of {POLICIES}")
    if required_groups is None:
        required = np.unique(terms.group)
    else:
        required = np.asarray(required_groups, dtype=np.int64)
        if required.ndim != 1 or required.size == 0:
            raise ContractViolation("required_groups must be a nonempty vector")
        if np.unique(required).size != required.size:
            raise ContractViolation("required_groups must not contain duplicates")

    est = terms.estimable
    counts = terms.counts()
    if terms.has_non_estimable() and policy is None:
        raise NonEstimableError(
            f"{terms.states.size - int(est.sum())} of {terms.states.size} terms are "
            f"non-estimable ({counts}); name an explicit consequence policy"
        )

    group_status: dict[str, str] = {}
    group_coverage: dict[str, float] = {}
    per_group: list[float] = []
    for raw_group in required:
        g = int(raw_group)
        sel_all = terms.group == g
        n_all = int(np.count_nonzero(sel_all))
        sel_est = sel_all & est
        n_est = int(np.count_nonzero(sel_est))
        group_coverage[str(g)] = float(n_est / n_all) if n_all else 0.0
        if n_all == 0 or n_est == 0:
            group_status[str(g)] = NOT_ESTIMABLE
            continue
        group_status[str(g)] = "ESTIMABLE"
        v = terms.values[sel_est]
        per_group.append(float(np.mean(np.square(v) if square else v)))

    any_group_not_estimable = any(x == NOT_ESTIMABLE for x in group_status.values())
    base = dict(
        terms_total=int(terms.states.size),
        terms_estimable=int(np.count_nonzero(est)),
        state_counts=counts,
        group_status=group_status,
        group_coverage=group_coverage,
    )
    quantity = (
        "group-balanced mean of squared correlation"
        if square
        else "group-balanced mean correlation"
    )

    if not terms.has_non_estimable() and not any_group_not_estimable:
        return AggregateV2(
            policy=policy or "NOT_REQUIRED",
            status="ESTIMABLE",
            conditional_statistic=float(np.mean(per_group)),
            full_estimand_point_estimated=True,
            quantity_name=quantity,
            note="all terms and required groups are estimable; no consequence policy was required.",
            **base,
        )

    if any_group_not_estimable and policy is None:
        raise NonEstimableError(
            f"one or more required groups have no estimable terms: {group_status}"
        )

    if policy == P1:
        return AggregateV2(
            policy=P1,
            status="EXCLUDED",
            conditional_statistic=None,
            full_estimand_point_estimated=False,
            quantity_name="not computed",
            note="P1 excludes the unit unless every term and required group is estimable.",
            **base,
        )

    if policy in (P2, P3):
        value = float(np.mean(per_group)) if per_group else None
        label = (
            "non-estimable terms abstain and the remainder is renormalized within group. "
            "This CHANGES THE ESTIMAND: the number is conditional on estimability."
            if policy == P2
            else "the FULL intended estimand is NOT point-estimated. The reportable number "
            "is conditional on estimability and must carry coverage."
        )
        return AggregateV2(
            policy=policy,
            status="ESTIMABLE" if value is not None else NOT_ESTIMABLE,
            conditional_statistic=value,
            full_estimand_point_estimated=False,
            quantity_name="conditional predictability among estimable donors",
            note=label,
            **base,
        )

    if any_group_not_estimable:
        return AggregateV2(
            policy=P4,
            status=NOT_ESTIMABLE,
            conditional_statistic=None,
            full_estimand_point_estimated=False,
            quantity_name="conditional predictability among estimable donors",
            note="a required group has no estimable term; P4 refuses the aggregate rather than scoring a vacuous guardrail.",
            **base,
        )
    return AggregateV2(
        policy=P4,
        status="ESTIMABLE",
        conditional_statistic=float(np.mean(per_group)),
        full_estimand_point_estimated=False,
        quantity_name="conditional predictability among estimable donors",
        note="all required groups retain coverage, but the statistic is conditional on estimability; the full unconditional estimand is not claimed.",
        **base,
    )


def resample_donors(terms: ScoreTermsV2, *, rng: np.random.Generator) -> ScoreTermsV2:
    """Bootstrap terms within group while carrying scientific state and coverage."""
    pieces: list[np.ndarray] = []
    for g in np.unique(terms.group):
        pos = np.flatnonzero(terms.group == g)
        pieces.append(rng.choice(pos, size=pos.size, replace=True).astype(np.int64))
    idx = np.concatenate(pieces)
    return ScoreTermsV2(
        values=terms.values[idx],
        states=terms.states[idx],
        group=terms.group[idx],
    )


def compare_policies(
    terms: ScoreTermsV2,
    *,
    square: bool = True,
    required_groups: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Report consequences of P1-P4 side-by-side. Selects nothing."""
    out: dict[str, Any] = {
        "schema": SCHEMA_ID,
        "policy_selected": None,
        "content_digest": terms.content_digest(),
        "state_counts": terms.counts(),
        "policies": {},
    }
    for policy in POLICIES:
        out["policies"][policy] = aggregate(
            terms,
            policy=policy,
            square=square,
            required_groups=required_groups,
        ).as_dict()
    try:
        out["no_policy"] = aggregate(
            terms,
            square=square,
            required_groups=required_groups,
        ).as_dict()
    except NonEstimableError as exc:
        out["no_policy"] = {"refused": True, "reason": str(exc)}
    return out
