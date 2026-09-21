"""Phase III successor — non-estimability evidence contract, V2.

**Prospective design with a reference implementation. NOT wired into the
canonical attacker. No terminal aggregation policy is selected.**

Why V2 supersedes V1
--------------------
V1 was written in this lane; an independently written GPT-lane contract reached
the same conclusion about the underlying defect but enforced a different set of
safeguards. Diffing the two implementations found three real faults in V1, all
confirmed empirically before this rewrite:

1. **Half-enforced invariant.** V1 checked ``ESTIMABLE => finite`` but never the
   inverse. ``ScoreTerms(values=[0.0], states=[TARGET_NON_VARIABLE], ...)`` was
   legal and serialized as the JSON number ``0.0`` rather than ``null`` — exactly
   the collapse the contract exists to prevent, still reachable through the
   constructor and through deserialization.
2. **A collapsed state.** V1 claimed five irreducible states while mapping six
   real conditions onto them: when target *and* prediction were both
   non-variable, target took precedence and the prediction failure was erased.
3. **No impossibility check.** An ``ESTIMABLE`` term carrying ``|r| = 1.7`` was
   accepted. A correlation outside ``[-1, 1]`` is not a small numerical problem;
   it means the computation is wrong.

V2 adopts the GPT lane's joint state, NaN invariant, impossibility check, content
digest and immutable arrays, and keeps V1's fail-closed aggregation, policy
comparison, round trips and state-carrying resampling.

Six states, and why each is irreducible
---------------------------------------
``ESTIMABLE``                            a finite, admissible correlation
``TARGET_NON_VARIABLE``                  ``rss_y <= EPS``; the question could not be asked
``PREDICTION_NON_VARIABLE``              ``pred_ss <= EPS``; the attacker produced nothing
``TARGET_AND_PREDICTION_NON_VARIABLE``   both; neither failure may be erased
``MISSING``                              the donor contributed no rows
``INVALID_NUMERIC``                      non-finite, or ``|r| > 1``

Invariants, enforced at EVERY entry point
------------------------------------------
Validation lives in one place and runs from the constructor, both deserializers
and resampling — not only on the happy path:

* ``ESTIMABLE`` terms carry a finite value with ``|value| <= 1 + TOL``;
* **every** non-estimable term carries ``NaN``, with no exception;
* state codes are known;
* arrays are aligned, 1-D, and made read-only after validation.

The second invariant is the one V1 lacked. The direction of an invariant that is
forgotten is precisely the direction the defect walks back in.

Aggregation fails closed
------------------------
``aggregate`` refuses to return a number when non-estimable terms are present
unless a policy is named explicitly. There is no default, because the defect
being repaired *is* a silent default.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Sequence

import numpy as np

SCHEMA = "V5_SCORE_TERM_EVIDENCE_CONTRACT_V2"
EPS = 1e-12
#: Admissible slack on |r|. Backward-stable arithmetic can overshoot 1 by a few
#: ulp; anything beyond this is a computation error, not rounding.
CORRELATION_TOL = 1e-9

ESTIMABLE = 0
TARGET_NON_VARIABLE = 1
PREDICTION_NON_VARIABLE = 2
TARGET_AND_PREDICTION_NON_VARIABLE = 3
MISSING = 4
INVALID_NUMERIC = 5

STATE_NAMES = {
    ESTIMABLE: "ESTIMABLE",
    TARGET_NON_VARIABLE: "TARGET_NON_VARIABLE",
    PREDICTION_NON_VARIABLE: "PREDICTION_NON_VARIABLE",
    TARGET_AND_PREDICTION_NON_VARIABLE: "TARGET_AND_PREDICTION_NON_VARIABLE",
    MISSING: "MISSING",
    INVALID_NUMERIC: "INVALID_NUMERIC",
}
STATE_CODES = {v: k for k, v in STATE_NAMES.items()}
NON_ESTIMABLE_STATES = tuple(c for c in STATE_NAMES if c != ESTIMABLE)

P1 = "P1_PROSPECTIVE_ELIGIBILITY"
P2 = "P2_ABSTAIN_AND_REWEIGHT"
P3 = "P3_CONDITIONAL_WITH_MANDATORY_COVERAGE"
P4 = "P4_COVERAGE_GUARDED_CONDITIONAL"
POLICIES = (P1, P2, P3, P4)

NOT_ESTIMABLE = "NOT_ESTIMABLE"


class NonEstimableError(RuntimeError):
    """Raised when an aggregate is requested over non-estimable terms with no policy."""


class ContractViolation(ValueError):
    """Raised when the tagged-value invariants are broken at any entry point."""


def _validate(values: np.ndarray, states: np.ndarray, group: np.ndarray):
    v = np.asarray(values, dtype=np.float64).copy()
    s = np.asarray(states, dtype=np.int8).copy()
    g = np.asarray(group, dtype=np.int64).copy()

    if not (v.shape == s.shape == g.shape) or v.ndim != 1:
        raise ContractViolation("values, states and group must be aligned 1-D arrays")
    if s.size and (s.min() < 0 or s.max() > INVALID_NUMERIC):
        raise ContractViolation("unknown state code")

    est = s == ESTIMABLE
    bad_finite = est & ~np.isfinite(v)
    if bad_finite.any():
        raise ContractViolation(
            f"{int(bad_finite.sum())} ESTIMABLE terms carry non-finite values")
    out_of_range = est & (np.abs(v) > 1.0 + CORRELATION_TOL)
    if out_of_range.any():
        raise ContractViolation(
            f"{int(out_of_range.sum())} ESTIMABLE terms carry |r| > 1; a correlation "
            "outside [-1, 1] means the computation is wrong, not merely imprecise")

    # The invariant V1 lacked. Without it a non-estimable term can hold 0.0 and
    # serialize as a number, which is exactly the collapse this contract forbids.
    smuggled = (~est) & np.isfinite(v)
    if smuggled.any():
        offenders = {STATE_NAMES[int(c)]: int(((s == c) & np.isfinite(v)).sum())
                     for c in NON_ESTIMABLE_STATES
                     if ((s == c) & np.isfinite(v)).any()}
        raise ContractViolation(
            f"{int(smuggled.sum())} non-estimable terms carry a finite value {offenders}; "
            "an undefined term must never hold an ordinary number")

    v.setflags(write=False)
    s.setflags(write=False)
    g.setflags(write=False)
    return v, s, g


@dataclass(frozen=True)
class ScoreTerms:
    """Tagged per-donor score terms. Values are meaningful ONLY where ESTIMABLE."""

    values: np.ndarray
    states: np.ndarray
    group: np.ndarray

    def __post_init__(self) -> None:
        v, s, g = _validate(self.values, self.states, self.group)
        object.__setattr__(self, "values", v)
        object.__setattr__(self, "states", s)
        object.__setattr__(self, "group", g)

    # ---------------------------------------------------------------- helpers
    @property
    def estimable(self) -> np.ndarray:
        return self.states == ESTIMABLE

    def counts(self) -> dict[str, int]:
        return {name: int((self.states == code).sum()) for code, name in STATE_NAMES.items()}

    def has_non_estimable(self) -> bool:
        return bool((self.states != ESTIMABLE).any())

    def content_digest(self) -> str:
        """SHA-256 over the scientific state, so tampering is detectable.

        Values are rendered at full repr precision and non-estimable terms as the
        literal token ``NaN``, so a smuggled zero changes the digest.
        """
        parts = [SCHEMA]
        for v, s, g in zip(self.values, self.states, self.group):
            token = "NaN" if not np.isfinite(v) else repr(float(v))
            parts.append(f"{int(g)}|{STATE_NAMES[int(s)]}|{token}")
        return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()

    # ------------------------------------------------------------ construction
    @staticmethod
    def from_scorer_components(
        *, cov: Sequence[float], rss_y: Sequence[float], pred_ss: Sequence[float],
        group: Sequence[int], present: Sequence[bool] | None = None, eps: float = EPS,
    ) -> "ScoreTerms":
        """Classify terms from the frozen scorer's own components.

        This is the boundary where the defect currently occurs: instead of
        collapsing an undefined term to ``0.0``, the state is recorded. A joint
        target-and-prediction failure keeps BOTH facts.
        """
        cov = np.asarray(cov, dtype=np.float64)
        rss = np.asarray(rss_y, dtype=np.float64)
        pss = np.asarray(pred_ss, dtype=np.float64)
        grp = np.asarray(group, dtype=np.int64)
        n = cov.size
        present_arr = np.ones(n, bool) if present is None else np.asarray(present, bool)

        states = np.full(n, ESTIMABLE, dtype=np.int8)
        values = np.full(n, np.nan, dtype=np.float64)

        t_bad = present_arr & (rss <= eps)
        p_bad = present_arr & (pss <= eps)
        states[~present_arr] = MISSING
        states[t_bad & ~p_bad] = TARGET_NON_VARIABLE
        states[p_bad & ~t_bad] = PREDICTION_NON_VARIABLE
        states[t_bad & p_bad] = TARGET_AND_PREDICTION_NON_VARIABLE

        ok = states == ESTIMABLE
        den = np.sqrt(np.maximum(rss, 0.0) * np.maximum(pss, 0.0))
        with np.errstate(divide="ignore", invalid="ignore"):
            r = np.where(ok, cov / np.where(den > 0, den, 1.0), np.nan)
        impossible = ok & (~np.isfinite(r) | (np.abs(r) > 1.0 + CORRELATION_TOL))
        states[impossible] = INVALID_NUMERIC
        ok = states == ESTIMABLE
        values[ok] = np.clip(r[ok], -1.0, 1.0)      # within tolerance only
        return ScoreTerms(values=values, states=states, group=grp)

    # ----------------------------------------------------------- serialization
    def to_json(self) -> str:
        return json.dumps({
            "schema": SCHEMA,
            "values": [None if not np.isfinite(v) else float(v) for v in self.values],
            "states": [STATE_NAMES[int(s)] for s in self.states],
            "group": [int(g) for g in self.group],
            "content_digest": self.content_digest(),
        }, sort_keys=True)

    @staticmethod
    def from_json(text: str) -> "ScoreTerms":
        d = json.loads(text)
        if d.get("schema") != SCHEMA:
            raise ContractViolation("unknown score-term schema")
        unknown = [s for s in d["states"] if s not in STATE_CODES]
        if unknown:
            raise ContractViolation(f"unknown state names: {sorted(set(unknown))[:5]}")
        states = np.asarray([STATE_CODES[s] for s in d["states"]], dtype=np.int8)
        values = np.asarray([np.nan if v is None else float(v) for v in d["values"]],
                            dtype=np.float64)
        # _validate runs in __post_init__, so a hand-edited payload that attaches a
        # number to a non-estimable state is rejected here, not silently accepted.
        terms = ScoreTerms(values=values, states=states,
                           group=np.asarray(d["group"], dtype=np.int64))
        if "content_digest" in d and d["content_digest"] != terms.content_digest():
            raise ContractViolation("content digest does not match the payload")
        return terms

    def to_npz(self, path) -> None:
        np.savez_compressed(path, schema=np.array(SCHEMA), values=self.values,
                            states=self.states, group=self.group,
                            content_digest=np.array(self.content_digest()))

    @staticmethod
    def from_npz(path) -> "ScoreTerms":
        d = np.load(path, allow_pickle=True)
        if str(d["schema"]) != SCHEMA:
            raise ContractViolation("unknown score-term schema")
        terms = ScoreTerms(values=d["values"], states=d["states"], group=d["group"])
        if "content_digest" in d.files and str(d["content_digest"]) != terms.content_digest():
            raise ContractViolation("content digest does not match the payload")
        return terms


@dataclass(frozen=True)
class Aggregate:
    """An aggregate that carries its own conditionality and coverage."""

    policy: str
    status: str                       # ESTIMABLE | NOT_ESTIMABLE | EXCLUDED
    conditional_statistic: float | None
    full_estimand_point_estimated: bool
    terms_total: int
    terms_estimable: int
    state_counts: dict[str, int]
    group_status: dict[str, str]
    group_coverage: dict[str, float]
    quantity_name: str
    note: str

    def as_dict(self) -> dict:
        return {
            "policy": self.policy,
            "status": self.status,
            "conditional_statistic": self.conditional_statistic,
            "full_estimand_point_estimated": self.full_estimand_point_estimated,
            "terms_total": self.terms_total,
            "terms_estimable": self.terms_estimable,
            "coverage": (self.terms_estimable / self.terms_total
                         if self.terms_total else None),
            "state_counts": self.state_counts,
            "group_status": self.group_status,
            "group_coverage": self.group_coverage,
            "quantity_name": self.quantity_name,
            "note": self.note,
        }


def aggregate(terms: ScoreTerms, *, policy: str | None = None, square: bool = True,
              required_groups: Sequence[int] | None = None) -> Aggregate:
    """Group-balanced aggregate under an explicit policy. No default exists."""
    if policy is not None and policy not in POLICIES:
        raise ValueError(f"unknown policy {policy!r}; expected one of {POLICIES}")
    counts = terms.counts()
    groups = np.unique(terms.group) if terms.group.size else np.empty(0, np.int64)
    required = (np.asarray(required_groups, dtype=np.int64)
                if required_groups is not None else groups)
    est = terms.estimable

    if terms.has_non_estimable() and policy is None:
        raise NonEstimableError(
            f"{terms.states.size - int(est.sum())} of {terms.states.size} terms are "
            f"non-estimable ({counts}); name a policy from {POLICIES} rather than "
            "letting an undefined term become a number")

    group_status, group_cov, per_group = {}, {}, []
    for g in required:
        sel_all = terms.group == g
        sel_est = sel_all & est
        n_all = int(sel_all.sum())
        group_cov[str(int(g))] = float(sel_est.sum() / n_all) if n_all else 0.0
        if not sel_est.any():
            group_status[str(int(g))] = NOT_ESTIMABLE
            continue
        group_status[str(int(g))] = "ESTIMABLE"
        v = terms.values[sel_est]
        per_group.append(float(np.mean(v * v if square else v)))

    any_group_not_estimable = any(v == NOT_ESTIMABLE for v in group_status.values())
    base = dict(terms_total=int(terms.states.size), terms_estimable=int(est.sum()),
                state_counts=counts, group_status=group_status, group_coverage=group_cov)

    if not terms.has_non_estimable():
        return Aggregate(policy=policy or "NOT_REQUIRED", status="ESTIMABLE",
                         conditional_statistic=float(np.mean(per_group)),
                         full_estimand_point_estimated=True,
                         quantity_name="group-balanced mean of squared correlation",
                         note="all terms estimable; no policy was required.", **base)

    if policy == P1:
        return Aggregate(
            policy=P1, status="EXCLUDED", conditional_statistic=None,
            full_estimand_point_estimated=False,
            quantity_name="not computed",
            note="unit excluded: P1 requires every term estimable. The universe shrinks "
                 "and the excluded unit is reported, never silently dropped.", **base)

    if policy == P2:
        return Aggregate(
            policy=P2, status="NOT_ESTIMABLE" if not per_group else "ESTIMABLE",
            conditional_statistic=float(np.mean(per_group)) if per_group else None,
            full_estimand_point_estimated=False,
            quantity_name="conditional predictability among estimable donors",
            note="non-estimable terms abstain and the remainder is renormalized within "
                 "group. This CHANGES THE ESTIMAND: the reported number is a conditional "
                 "mean over estimable donors, not the intended all-donor quantity.", **base)

    if policy == P3:
        return Aggregate(
            policy=P3, status="NOT_ESTIMABLE" if not per_group else "ESTIMABLE",
            conditional_statistic=float(np.mean(per_group)) if per_group else None,
            full_estimand_point_estimated=False,
            quantity_name="conditional predictability among estimable donors",
            note="the FULL intended estimand is NOT point-estimated, because the number "
                 "is computed on the estimable subset. What is reportable is the "
                 "conditional statistic, and coverage is mandatory alongside it.", **base)

    # P4 -- coverage-guarded conditional. A required group with no estimable donor
    # yields NOT_ESTIMABLE for the whole aggregate: never PASS, never numeric zero.
    if any_group_not_estimable:
        return Aggregate(
            policy=P4, status=NOT_ESTIMABLE, conditional_statistic=None,
            full_estimand_point_estimated=False,
            quantity_name="conditional predictability among estimable donors",
            note="a required group has NO estimable donor, so its guardrail is "
                 "NOT_ESTIMABLE. The aggregate refuses rather than reporting a number "
                 "that a vacuous guardrail would make look clean.", **base)
    return Aggregate(
        policy=P4, status="ESTIMABLE",
        conditional_statistic=float(np.mean(per_group)) if per_group else None,
        full_estimand_point_estimated=False,
        quantity_name="conditional predictability among estimable donors",
        note="scored on estimable donors only; the intended target universe is "
             "preserved; coverage is reported; the full unconditional all-donor "
             "quantity is NOT claimed.", **base)


def resample_donors(terms: ScoreTerms, *, rng: np.random.Generator) -> ScoreTerms:
    """Bootstrap donors WITHIN group, carrying states and therefore coverage."""
    idx = np.empty(0, dtype=np.int64)
    for g in np.unique(terms.group):
        pos = np.flatnonzero(terms.group == g)
        idx = np.concatenate([idx, rng.choice(pos, size=pos.size, replace=True)])
    return ScoreTerms(values=terms.values[idx], states=terms.states[idx],
                      group=terms.group[idx])


def compare_policies(terms: ScoreTerms, *, square: bool = True,
                     required_groups: Sequence[int] | None = None) -> dict:
    """Report every policy's consequence side by side. Selects nothing."""
    out = {"schema": SCHEMA, "policy_selected": None,
           "content_digest": terms.content_digest(),
           "state_counts": terms.counts(), "policies": {}}
    for p in POLICIES:
        out["policies"][p] = aggregate(terms, policy=p, square=square,
                                       required_groups=required_groups).as_dict()
    try:
        out["no_policy"] = aggregate(terms, square=square,
                                     required_groups=required_groups).as_dict()
    except NonEstimableError as exc:
        out["no_policy"] = {"refused": True, "reason": str(exc)}
    return out
