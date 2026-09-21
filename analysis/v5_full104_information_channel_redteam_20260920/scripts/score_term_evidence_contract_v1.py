"""Phase III — PROPOSED evidence contract for non-estimable score terms.

**This is a prospective design with a reference implementation. It is NOT wired
into the canonical attacker and changes no current authority.**

The defect it addresses
-----------------------
The frozen scorer reduces every per-donor term through::

    den = sqrt(max(rss_y, 0) * max(pred_ss, 0))
    r   = 0.0 if den <= _EPS else cov / den

so a term that is *mathematically undefined* — because the target does not vary
within that donor — becomes ``r = 0``, hence ``r² = 0``: the **best attainable
value**. Phase II measured the consequence on the authenticated substrate:
30,451 of 1,773,512 held-out terms (1.7170%) are undefined yet scored as perfect,
affecting 39.01% of targets, and leaving a whole source guardrail vacuous for 202
targets.

The contract
------------
A score term is a **tagged value**, not a float. Five states are kept distinct,
and no arithmetic may collapse them:

``ESTIMABLE``                a finite correlation was computed
``TARGET_NON_VARIABLE``      ``rss_y <= EPS``; the correlation is undefined
``PREDICTION_NON_VARIABLE``  ``pred_ss <= EPS``; undefined for a different reason
``MISSING``                  the donor contributed no rows at all
``INVALID``                  non-finite or otherwise unusable

``TARGET_NON_VARIABLE`` and ``PREDICTION_NON_VARIABLE`` are kept apart because
they are scientifically different failures: the first says the question could not
be asked of this donor, the second says the attacker produced no signal to
correlate against. Collapsing them would hide which one occurred.

Representation
--------------
Values and states travel together as two aligned arrays — ``float64`` values and
``int8`` state codes. NaN alone is rejected as a representation: it cannot
distinguish the four non-estimable states from each other, and it silently
propagates through most reductions.

Round-tripping through JSON and NPZ is part of the contract and is tested,
because a representation that loses its states at the serialization boundary is
not a representation.

Aggregation fails closed
------------------------
``aggregate`` **refuses** to return a number when non-estimable terms are present
unless an explicit policy is named. There is no default policy. This is the whole
point: the current defect is a silent default, and replacing it with a different
silent default would not be an improvement.

Three policies are implemented so their consequences can be compared. **None is
selected here**, and the choice must not be made by observing which produces a
preferred masking outcome.

``P1_PROSPECTIVE_ELIGIBILITY``
    Terms must all be estimable; otherwise the unit is excluded from the
    analysis entirely and reported as excluded. Shrinks the universe.

``P2_ABSTAIN_AND_REWEIGHT``
    Non-estimable terms abstain; the remaining terms are renormalized within
    their group. Changes the estimand — the reported quantity becomes a
    conditional mean over estimable donors.

``P3_REPORT_CONDITIONALITY``
    The estimand is unchanged and non-estimable terms are still excluded from the
    mean, but the aggregate carries its own conditionality: how many terms were
    estimable, and over what fraction of the intended support. Changes nothing
    numerically versus P2 for the point estimate; changes what may be *claimed*.

P2 and P3 can coincide numerically while differing in what they license. That is
deliberate and is the clearest illustration that this is a reporting contract as
much as an arithmetic one.

Resampling
----------
``resample_donors`` carries states through bootstrap resampling. A resample that
draws only non-estimable terms yields a non-estimable aggregate, not zero and not
silence.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

SCHEMA = "V5_SCORE_TERM_EVIDENCE_CONTRACT_V1"
EPS = 1e-12

ESTIMABLE = 0
TARGET_NON_VARIABLE = 1
PREDICTION_NON_VARIABLE = 2
MISSING = 3
INVALID = 4

STATE_NAMES = {
    ESTIMABLE: "ESTIMABLE",
    TARGET_NON_VARIABLE: "TARGET_NON_VARIABLE",
    PREDICTION_NON_VARIABLE: "PREDICTION_NON_VARIABLE",
    MISSING: "MISSING",
    INVALID: "INVALID",
}
STATE_CODES = {v: k for k, v in STATE_NAMES.items()}
NON_ESTIMABLE_STATES = (TARGET_NON_VARIABLE, PREDICTION_NON_VARIABLE, MISSING, INVALID)

POLICIES = ("P1_PROSPECTIVE_ELIGIBILITY", "P2_ABSTAIN_AND_REWEIGHT",
            "P3_REPORT_CONDITIONALITY")


class NonEstimableError(RuntimeError):
    """Raised when an aggregate is requested over non-estimable terms with no policy."""


@dataclass(frozen=True)
class ScoreTerms:
    """Tagged per-donor score terms. Values are meaningful ONLY where ESTIMABLE."""

    values: np.ndarray          # float64
    states: np.ndarray          # int8
    group: np.ndarray           # int64, e.g. source code, for two-level means

    def __post_init__(self) -> None:
        v = np.asarray(self.values, dtype=np.float64)
        s = np.asarray(self.states, dtype=np.int8)
        g = np.asarray(self.group, dtype=np.int64)
        if not (v.shape == s.shape == g.shape) or v.ndim != 1:
            raise ValueError("values, states and group must be aligned 1-D arrays")
        if s.size and (s.min() < 0 or s.max() > INVALID):
            raise ValueError("unknown state code")
        # A value that is not finite may only appear on a non-estimable term.
        bad = (s == ESTIMABLE) & ~np.isfinite(v)
        if bad.any():
            raise ValueError(f"{int(bad.sum())} ESTIMABLE terms carry non-finite values")
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

    # ------------------------------------------------------------ construction
    @staticmethod
    def from_scorer_components(
        *, cov: Sequence[float], rss_y: Sequence[float], pred_ss: Sequence[float],
        group: Sequence[int], present: Sequence[bool] | None = None, eps: float = EPS,
    ) -> "ScoreTerms":
        """Classify terms from the frozen scorer's own components.

        This is the boundary where the defect currently occurs: instead of
        collapsing an undefined term to ``0.0``, the state is recorded.
        """
        cov = np.asarray(cov, dtype=np.float64)
        rss = np.asarray(rss_y, dtype=np.float64)
        pss = np.asarray(pred_ss, dtype=np.float64)
        grp = np.asarray(group, dtype=np.int64)
        n = cov.size
        present_arr = np.ones(n, bool) if present is None else np.asarray(present, bool)

        states = np.full(n, ESTIMABLE, dtype=np.int8)
        values = np.zeros(n, dtype=np.float64)

        states[~present_arr] = MISSING
        # Target non-variability is checked first and reported as such, because it
        # is the failure Phase II measured. A term can fail both ways; naming the
        # target first is a declared convention, not an arithmetic claim.
        states[present_arr & (rss <= eps)] = TARGET_NON_VARIABLE
        states[present_arr & (rss > eps) & (pss <= eps)] = PREDICTION_NON_VARIABLE

        ok = states == ESTIMABLE
        den = np.sqrt(np.maximum(rss, 0.0) * np.maximum(pss, 0.0))
        with np.errstate(divide="ignore", invalid="ignore"):
            values[ok] = cov[ok] / den[ok]
        nonfinite = ok & ~np.isfinite(values)
        states[nonfinite] = INVALID
        values[states != ESTIMABLE] = np.nan      # never a usable number
        return ScoreTerms(values=values, states=states, group=grp)

    # ----------------------------------------------------------- serialization
    def to_json(self) -> str:
        return json.dumps({
            "schema": SCHEMA,
            "values": [None if not np.isfinite(v) else float(v) for v in self.values],
            "states": [STATE_NAMES[int(s)] for s in self.states],
            "group": [int(g) for g in self.group],
        }, sort_keys=True)

    @staticmethod
    def from_json(text: str) -> "ScoreTerms":
        d = json.loads(text)
        if d.get("schema") != SCHEMA:
            raise ValueError("unknown score-term schema")
        states = np.asarray([STATE_CODES[s] for s in d["states"]], dtype=np.int8)
        values = np.asarray([np.nan if v is None else float(v) for v in d["values"]],
                            dtype=np.float64)
        return ScoreTerms(values=values, states=states,
                          group=np.asarray(d["group"], dtype=np.int64))

    def to_npz(self, path) -> None:
        np.savez_compressed(path, schema=np.array(SCHEMA), values=self.values,
                            states=self.states, group=self.group)

    @staticmethod
    def from_npz(path) -> "ScoreTerms":
        d = np.load(path, allow_pickle=True)
        if str(d["schema"]) != SCHEMA:
            raise ValueError("unknown score-term schema")
        return ScoreTerms(values=d["values"], states=d["states"], group=d["group"])


@dataclass(frozen=True)
class Aggregate:
    """An aggregate that carries its own conditionality."""

    value: float | None
    policy: str
    terms_total: int
    terms_estimable: int
    state_counts: dict[str, int]
    groups_total: int
    groups_with_any_estimable: int
    excluded: bool
    note: str

    def as_dict(self) -> dict:
        return {
            "value": self.value, "policy": self.policy,
            "terms_total": self.terms_total, "terms_estimable": self.terms_estimable,
            "estimable_fraction": (self.terms_estimable / self.terms_total
                                   if self.terms_total else None),
            "state_counts": self.state_counts,
            "groups_total": self.groups_total,
            "groups_with_any_estimable": self.groups_with_any_estimable,
            "excluded": self.excluded, "note": self.note,
        }


def aggregate(terms: ScoreTerms, *, policy: str | None = None, square: bool = True) -> Aggregate:
    """Group-balanced mean of (squared) estimable terms, under an explicit policy.

    With ``policy=None`` this REFUSES when any term is non-estimable. That refusal
    is the contract: the current defect is a silent default, and a different
    silent default would not be an improvement.
    """
    if policy is not None and policy not in POLICIES:
        raise ValueError(f"unknown policy {policy!r}; expected one of {POLICIES}")
    counts = terms.counts()
    groups = np.unique(terms.group) if terms.group.size else np.empty(0, np.int64)
    est = terms.estimable
    groups_any = int(sum(1 for g in groups if est[terms.group == g].any()))

    if terms.has_non_estimable() and policy is None:
        raise NonEstimableError(
            f"{terms.states.size - int(est.sum())} of {terms.states.size} terms are "
            f"non-estimable ({counts}); name a policy from {POLICIES} rather than "
            "letting an undefined term become a number")

    def group_mean() -> float | None:
        per_group = []
        for g in groups:
            sel = (terms.group == g) & est
            if not sel.any():
                continue
            v = terms.values[sel]
            per_group.append(float(np.mean(v * v if square else v)))
        return float(np.mean(per_group)) if per_group else None

    if policy == "P1_PROSPECTIVE_ELIGIBILITY" and terms.has_non_estimable():
        return Aggregate(
            value=None, policy=policy, terms_total=int(terms.states.size),
            terms_estimable=int(est.sum()), state_counts=counts,
            groups_total=int(groups.size), groups_with_any_estimable=groups_any,
            excluded=True,
            note="unit excluded: P1 requires every term estimable. The universe shrinks; "
                 "the excluded unit is reported, never silently dropped.")

    value = group_mean()
    if policy == "P2_ABSTAIN_AND_REWEIGHT":
        note = ("non-estimable terms abstain and the remainder is renormalized within "
                "group. This CHANGES THE ESTIMAND: the result is a conditional mean "
                "over estimable donors, not over the intended support.")
    elif policy == "P3_REPORT_CONDITIONALITY":
        note = ("estimand unchanged; the aggregate carries its conditionality so a "
                "reader can see over how much of the intended support it was actually "
                "computed. Numerically this may equal P2 while licensing different claims.")
    else:
        note = "all terms estimable; no policy was required."

    return Aggregate(
        value=value, policy=policy or "NOT_REQUIRED",
        terms_total=int(terms.states.size), terms_estimable=int(est.sum()),
        state_counts=counts, groups_total=int(groups.size),
        groups_with_any_estimable=groups_any, excluded=False, note=note)


def resample_donors(terms: ScoreTerms, *, rng: np.random.Generator) -> ScoreTerms:
    """Bootstrap donors WITHIN group, carrying states.

    A resample that happens to draw only non-estimable terms must yield a
    non-estimable aggregate, not a zero and not a crash.
    """
    idx = np.empty(0, dtype=np.int64)
    for g in np.unique(terms.group):
        pos = np.flatnonzero(terms.group == g)
        idx = np.concatenate([idx, rng.choice(pos, size=pos.size, replace=True)])
    return ScoreTerms(values=terms.values[idx], states=terms.states[idx],
                      group=terms.group[idx])


def compare_policies(terms: ScoreTerms, *, square: bool = True) -> dict:
    """Report every policy's consequence side by side. Selects nothing."""
    out = {"schema": SCHEMA, "policy_selected": None,
           "state_counts": terms.counts(), "policies": {}}
    for p in POLICIES:
        out["policies"][p] = aggregate(terms, policy=p, square=square).as_dict()
    try:
        out["no_policy"] = aggregate(terms, square=square).as_dict()
    except NonEstimableError as exc:
        out["no_policy"] = {"refused": True, "reason": str(exc)}
    return out
