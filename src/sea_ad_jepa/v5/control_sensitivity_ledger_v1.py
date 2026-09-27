"""Control sensitivity ledger — prove each control can actually fail.

WHY THIS EXISTS
    Four independent instances of the same defect were found in one cycle:

      1. the inline gradient gate was asserted with `is not None`, and later with
         four counters that are hard-coded literals on the healthy path;
      2. Lane A's GLOBAL_CONTEXT_ONLY stayed silent on the exact failure it was
         written to catch;
      3. three of Agent 5's eight controls failed their own firing proofs;
      4. Stage73's context, gene-label-permuted and target-shuffled conditions
         were BIT-IDENTICAL at 0.3236108129998988 — the "controls" were the same
         computation and could not fail.

    A control that cannot fail is not evidence. This module makes that property
    measurable instead of assumed.

THE THREE LEGS
    Every control must be exercised in three configurations:

      HEALTHY     a reproducible good input. The control MUST stay quiet.
                  Firing here is a false positive.
      PLANTED     the specific failure the control exists to catch, deliberately
                  introduced. The control MUST fire. Staying quiet here is the
                  vacuity defect above.
      DEGENERATE  a configuration in which the control CANNOT be informative —
                  an under-capacity comparator, a collapsed reference, identical
                  arms. The control MUST REFUSE TO SCORE.

    The third leg is the one usually missing, and it is why Stage73 passed
    review: identical arms produce a clean-looking number. A control that
    returns a score on a degenerate configuration is reporting noise as
    evidence, so `REFUSED_DEGENERATE` is a REQUIRED outcome, never a failure.

VERDICTS
    A control earns SENSITIVE only with all three: quiet on healthy, fired on
    planted, refused on degenerate. Anything else is named explicitly —
    VACUOUS_DID_NOT_FIRE is the serious one.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

FIRED = "FIRED"
QUIET = "QUIET"
REFUSED_DEGENERATE = "REFUSED_DEGENERATE"
_OUTCOMES = (FIRED, QUIET, REFUSED_DEGENERATE)

SENSITIVE = "SENSITIVE"
VACUOUS_DID_NOT_FIRE = "VACUOUS_DID_NOT_FIRE"
FALSE_POSITIVE_ON_HEALTHY = "FALSE_POSITIVE_ON_HEALTHY"
SCORED_A_DEGENERATE_CONFIG = "SCORED_A_DEGENERATE_CONFIG"
INCOMPLETE_LEGS = "INCOMPLETE_LEGS"


class DegenerateConfiguration(Exception):
    """Raised by a control asked to score a configuration it cannot resolve.

    This is the correct behaviour, not an error condition. Catching it and
    returning a score would convert "I cannot tell" into "it passed".
    """


@dataclass(frozen=True)
class LegResult:
    leg: str
    outcome: str
    detail: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.leg not in ("healthy", "planted", "degenerate"):
            raise ValueError(f"unknown leg {self.leg!r}")
        if self.outcome not in _OUTCOMES:
            raise ValueError(f"unknown outcome {self.outcome!r}")


def run_leg(fn: Callable[[], bool], leg: str) -> LegResult:
    """Execute one leg. A DegenerateConfiguration is recorded, never swallowed."""
    try:
        fired = bool(fn())
    except DegenerateConfiguration as exc:
        return LegResult(leg, REFUSED_DEGENERATE, {"reason": str(exc)})
    return LegResult(leg, FIRED if fired else QUIET, {})


def classify(healthy: LegResult, planted: LegResult,
             degenerate: LegResult | None) -> str:
    if degenerate is None:
        return INCOMPLETE_LEGS
    if planted.outcome != FIRED:
        # the defect this whole module exists for
        return VACUOUS_DID_NOT_FIRE
    if healthy.outcome == FIRED:
        return FALSE_POSITIVE_ON_HEALTHY
    if degenerate.outcome != REFUSED_DEGENERATE:
        return SCORED_A_DEGENERATE_CONFIG
    return SENSITIVE


@dataclass
class ControlSensitivityLedger:
    """Accumulates per-control results and refuses to summarise a partial run."""
    entries: dict[str, dict[str, Any]] = field(default_factory=dict)

    def record(self, control_id: str, *, healthy: LegResult, planted: LegResult,
               degenerate: LegResult | None, source: str, notes: str = "") -> str:
        if control_id in self.entries:
            raise ValueError(f"control {control_id!r} recorded twice")
        verdict = classify(healthy, planted, degenerate)
        self.entries[control_id] = {
            "control_id": control_id,
            "source": source,
            "healthy": {"outcome": healthy.outcome, **dict(healthy.detail)},
            "planted": {"outcome": planted.outcome, **dict(planted.detail)},
            "degenerate": (None if degenerate is None
                           else {"outcome": degenerate.outcome, **dict(degenerate.detail)}),
            "verdict": verdict,
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
            "schema": "V5_CONTROL_SENSITIVITY_LEDGER_V1",
            "controls": len(self.entries),
            "verdict_counts": counts,
            "all_sensitive": counts.get(SENSITIVE, 0) == len(self.entries),
            "vacuous_controls": sorted(
                k for k, v in self.entries.items()
                if v["verdict"] == VACUOUS_DID_NOT_FIRE),
            "entries": [self.entries[k] for k in sorted(self.entries)],
            "training_authorized": False,
        }
        payload["ledger_digest"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True).encode("utf-8")).hexdigest()
        return payload


# ---------------------------------------------------------------------------
# Degeneracy detectors — the reusable part
# ---------------------------------------------------------------------------
def require_distinct_arms(a: Any, b: Any, *, label: str) -> None:
    """Refuse to score two arms that are the same object or byte-identical.

    This is exactly the Stage73 defect: context, gene-label-permuted and
    target-shuffled were bit-identical at 0.3236108129998988, so the comparison
    could only ever report "no difference". Identical arms are unresolvable,
    not passing.
    """
    if a is b:
        raise DegenerateConfiguration(f"{label}: both arms are the same object")
    da = hashlib.sha256(repr(a).encode("utf-8")).hexdigest()
    db = hashlib.sha256(repr(b).encode("utf-8")).hexdigest()
    if da == db:
        raise DegenerateConfiguration(
            f"{label}: arms are byte-identical ({da[:12]}…); comparison cannot resolve")


def require_comparator_capacity(capacity: int, needed: int, *, label: str) -> None:
    """Refuse to score a comparator too weak to express the failure.

    Lane A observed that an under-capacity summary never fires in ANY regime.
    Such a comparator produces a quiet result that looks like a pass, so
    capacity matching is a precondition for the control being informative.
    """
    if capacity < needed:
        raise DegenerateConfiguration(
            f"{label}: comparator capacity {capacity} < {needed} required; "
            "a quiet result here would be uninformative, not a pass")


def require_effect_resolvable(ci_lower: float, ci_upper: float, *, label: str) -> None:
    """Refuse to call a direction when the interval spans zero.

    Stage73R's corrected context-vs-target-shuffled delta was -0.008366 with a
    95% interval of [-0.019597, +0.000169], which INCLUDES ZERO. The supported
    statement is failure to establish an advantage — not an established loss.
    """
    if ci_lower <= 0.0 <= ci_upper:
        raise DegenerateConfiguration(
            f"{label}: interval [{ci_lower:.6g}, {ci_upper:.6g}] includes zero; "
            "direction is not resolvable from this comparison")
