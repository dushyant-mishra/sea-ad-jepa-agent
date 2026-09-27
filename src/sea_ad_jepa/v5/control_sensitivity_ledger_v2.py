"""Control sensitivity ledger V2 — repairs four defects found in V1.

V1 (`control_sensitivity_ledger_v1.py`) is retained unchanged as the immutable
prior version. This is a versioned successor, not an edit.

WHAT V1 GOT WRONG, and why each matters
--------------------------------------
1A  STRICT LEG CLASSIFICATION. V1's `classify` tested `healthy.outcome == FIRED`
    and fell through to SENSITIVE otherwise. A healthy leg returning
    REFUSED_DEGENERATE therefore scored SENSITIVE — a control that could not
    even evaluate its healthy case was being certified. Each leg now requires
    its exact outcome.

1B  REFUSAL REASON AND MACHINE STATE. V1's gate probe treated ANY RuntimeError
    as successful detection. A shape mismatch, a bad fixture or an unrelated
    bug would have counted as "the gate fired". A refusal now qualifies only if
    the reason matches the expected cause AND no optimizer step, Adam state,
    EMA update or cursor advance occurred.

1C  CANONICAL IDENTITY, NOT `repr`. V1 hashed `repr(obj)`. NumPy TRUNCATES
    repr: `repr(np.arange(10000))` renders as `[0 1 2 ... 9997 9998 9999]`, so
    two arrays differing only in the elided middle hash identically. A
    distinctness detector that cannot see the middle of an array is itself the
    vacuity defect it exists to catch. Identity now uses shape, dtype and full
    bytes, with canonical ordering for set-like structures.

1D  INVALID vs INCONCLUSIVE. V1 raised DegenerateConfiguration when a
    confidence interval spanned zero, conflating "this experiment cannot
    resolve a direction" with "this experiment is invalid". A valid, well-run
    comparison that happens to be inconclusive is evidence, not a broken
    control. These are now separate verdicts.

    This matters for the record: Stage73R's corrected context-vs-target-shuffled
    delta was -0.008366 with 95% CI [-0.019597, +0.000169]. That is
    INCONCLUSIVE_DIRECTION on a VALID experiment — no established graph-specific
    advantage, and NOT a demonstrated loss.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

# ---- leg outcomes ---------------------------------------------------------
FIRED = "FIRED"
QUIET = "QUIET"
REFUSED_DEGENERATE = "REFUSED_DEGENERATE"
_OUTCOMES = (FIRED, QUIET, REFUSED_DEGENERATE)
_REQUIRED = {"healthy": QUIET, "planted": FIRED, "degenerate": REFUSED_DEGENERATE}

# ---- control verdicts (1A) ------------------------------------------------
SENSITIVE = "SENSITIVE"
VACUOUS_DID_NOT_FIRE = "VACUOUS_DID_NOT_FIRE"
FALSE_POSITIVE_ON_HEALTHY = "FALSE_POSITIVE_ON_HEALTHY"
HEALTHY_LEG_UNEVALUABLE = "HEALTHY_LEG_UNEVALUABLE"
SCORED_A_DEGENERATE_CONFIG = "SCORED_A_DEGENERATE_CONFIG"
DEGENERATE_LEG_FIRED = "DEGENERATE_LEG_FIRED"
INCOMPLETE_LEGS = "INCOMPLETE_LEGS"
MISLABELLED_LEG = "MISLABELLED_LEG"

# ---- evidence verdicts, distinct from control validity (1D) ---------------
EVIDENCE_INVALID = "INVALID_EXPERIMENT"
EVIDENCE_INCONCLUSIVE = "INCONCLUSIVE_DIRECTION"
EVIDENCE_POSITIVE = "DEMONSTRATED_POSITIVE_EFFECT"
EVIDENCE_NEGATIVE = "DEMONSTRATED_NEGATIVE_EFFECT"


class DegenerateConfiguration(Exception):
    """The configuration cannot yield an informative answer. Correct behaviour."""


# ---------------------------------------------------------------------------
# 1C — canonical identity
# ---------------------------------------------------------------------------
def canonical_digest(obj: Any) -> str:
    """Content digest that cannot be fooled by an elided repr.

    Arrays contribute shape, dtype and FULL bytes. Set-like structures are
    canonically ordered so that presentation order does not masquerade as a
    structural difference.
    """
    h = hashlib.sha256()

    def feed(o):
        if hasattr(o, "shape") and hasattr(o, "dtype") and hasattr(o, "tobytes"):
            h.update(b"ARRAY")
            h.update(str(tuple(o.shape)).encode())
            h.update(str(o.dtype).encode())
            h.update(bytes(memoryview(o.copy(order="C")).cast("B")))  # full bytes
        elif isinstance(o, (set, frozenset)):
            h.update(b"SET")
            for x in sorted(canonical_digest(v) for v in o):
                h.update(x.encode())
        elif isinstance(o, Mapping):
            h.update(b"MAP")
            for k in sorted(o, key=lambda k: canonical_digest(k)):
                h.update(canonical_digest(k).encode())
                h.update(canonical_digest(o[k]).encode())
        elif isinstance(o, (list, tuple)):
            h.update(b"SEQ")
            for v in o:
                h.update(canonical_digest(v).encode())
        else:
            h.update(b"LIT")
            h.update(json.dumps(o, sort_keys=True, default=repr).encode())
    feed(obj)
    return h.hexdigest()


def canonical_edge_digest(edges: Sequence[tuple]) -> str:
    """Structural digest of a graph: canonical edge multiset, order-independent."""
    norm = sorted(tuple(canonical_digest(x) for x in e) for e in edges)
    return canonical_digest(norm)


def require_structurally_distinct(a: Any, b: Any, *, label: str) -> None:
    """Refuse when two arms are STRUCTURALLY identical.

    Structural identity is the disqualifier, not identical outcomes: two genuinely
    different graphs may legitimately yield the same predictions, and that is a
    result. Two identically-structured arms wearing different labels is not.
    """
    if a is b:
        raise DegenerateConfiguration(f"{label}: both arms are the same object")
    da, db = canonical_digest(a), canonical_digest(b)
    if da == db:
        raise DegenerateConfiguration(
            f"{label}: arms are structurally identical ({da[:12]}…); "
            "a different label does not make a different arm")


def require_intervention_effective(before: Any, after: Any, *, label: str) -> None:
    """Refuse an intervention that did not actually change the thing intervened on."""
    if canonical_digest(before) == canonical_digest(after):
        raise DegenerateConfiguration(
            f"{label}: intervention left the structure unchanged; nothing was varied")


def require_comparator_capacity(capacity: int, needed: int, *, label: str) -> None:
    if capacity < needed:
        raise DegenerateConfiguration(
            f"{label}: comparator capacity {capacity} < {needed} required; "
            "a quiet result here would be uninformative, not a pass")


# ---------------------------------------------------------------------------
# 1D — evidence classification, separate from control validity
# ---------------------------------------------------------------------------
def classify_evidence(mean_delta: float, ci_lower: float, ci_upper: float,
                      *, experiment_valid: bool) -> str:
    """An inconclusive interval is EVIDENCE, not a broken control."""
    if not experiment_valid:
        return EVIDENCE_INVALID
    if ci_lower > ci_upper:
        raise ValueError("ci_lower exceeds ci_upper")
    if ci_lower <= 0.0 <= ci_upper:
        return EVIDENCE_INCONCLUSIVE
    return EVIDENCE_POSITIVE if mean_delta > 0 else EVIDENCE_NEGATIVE


# ---------------------------------------------------------------------------
# legs and strict classification (1A)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LegResult:
    leg: str
    outcome: str
    detail: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.leg not in _REQUIRED:
            raise ValueError(f"unknown leg {self.leg!r}")
        if self.outcome not in _OUTCOMES:
            raise ValueError(f"unknown outcome {self.outcome!r}")


def run_leg(fn: Callable[[], bool], leg: str) -> LegResult:
    if leg not in _REQUIRED:
        raise ValueError(f"unknown leg {leg!r}")
    try:
        fired = bool(fn())
    except DegenerateConfiguration as exc:
        return LegResult(leg, REFUSED_DEGENERATE, {"reason": str(exc)})
    return LegResult(leg, FIRED if fired else QUIET, {})


def classify(healthy: LegResult | None, planted: LegResult | None,
             degenerate: LegResult | None) -> str:
    """Every leg must produce its EXACT required outcome. No fall-through."""
    legs = {"healthy": healthy, "planted": planted, "degenerate": degenerate}
    if any(v is None for v in legs.values()):
        return INCOMPLETE_LEGS
    for name, res in legs.items():
        if res.leg != name:
            return MISLABELLED_LEG
    if planted.outcome != FIRED:
        return VACUOUS_DID_NOT_FIRE          # the defect this module exists for
    if healthy.outcome == FIRED:
        return FALSE_POSITIVE_ON_HEALTHY
    if healthy.outcome == REFUSED_DEGENERATE:
        return HEALTHY_LEG_UNEVALUABLE       # 1A: V1 scored this SENSITIVE
    if degenerate.outcome == FIRED:
        return DEGENERATE_LEG_FIRED
    if degenerate.outcome != REFUSED_DEGENERATE:
        return SCORED_A_DEGENERATE_CONFIG
    assert healthy.outcome == QUIET and degenerate.outcome == REFUSED_DEGENERATE
    return SENSITIVE


@dataclass
class ControlSensitivityLedgerV2:
    entries: dict[str, dict[str, Any]] = field(default_factory=dict)

    def record(self, control_id: str, *, healthy: LegResult | None,
               planted: LegResult | None, degenerate: LegResult | None,
               source: str, notes: str = "") -> str:
        if control_id in self.entries:
            raise ValueError(f"control {control_id!r} recorded twice")
        verdict = classify(healthy, planted, degenerate)
        self.entries[control_id] = {
            "control_id": control_id, "source": source, "verdict": verdict,
            "healthy": None if healthy is None else {"outcome": healthy.outcome, **dict(healthy.detail)},
            "planted": None if planted is None else {"outcome": planted.outcome, **dict(planted.detail)},
            "degenerate": None if degenerate is None else {"outcome": degenerate.outcome, **dict(degenerate.detail)},
            "notes": notes,
        }
        return verdict

    def summary(self) -> dict[str, Any]:
        if not self.entries:
            raise ValueError("refusing to summarise an empty ledger")
        counts: dict[str, int] = {}
        for e in self.entries.values():
            counts[e["verdict"]] = counts.get(e["verdict"], 0) + 1
        payload = {
            "schema": "V5_CONTROL_SENSITIVITY_LEDGER_V2",
            "supersedes": "V5_CONTROL_SENSITIVITY_LEDGER_V1",
            "controls": len(self.entries),
            "verdict_counts": counts,
            "all_sensitive": counts.get(SENSITIVE, 0) == len(self.entries),
            "not_sensitive": sorted(k for k, v in self.entries.items()
                                    if v["verdict"] != SENSITIVE),
            "entries": [self.entries[k] for k in sorted(self.entries)],
            "training_authorized": False,
        }
        payload["ledger_digest"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True).encode()).hexdigest()
        return payload
