"""Append-only experimental-outcome exposure ledger; CPU/static authority V1.

Outcome exposure is tracked per study + assay/arm + outcome family; merely
authenticating an unopened assay is NOT an outcome inspection. Conversely,
looking at the GSE254205 bulk drug contrasts irrevocably disqualifies those
exact outcomes as untouched confirmation.

This ledger cannot prove that an experiment is truly untouched. Even a
DECLARED_UNINSPECTED value carries no independent-confirmation authorization
without a separately reviewed timestamped physical outcome-seal contract.
Never treat a self-digest or caller-declared date as independent audit evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

SCHEMA = "JEPA_PERTURBATION_OUTCOME_EXPOSURE_LEDGER_V1"
UNKNOWN = "UNKNOWN"
DECLARED_UNINSPECTED = "DECLARED_UNINSPECTED"
INSPECTED = "INSPECTED"
DEVELOPMENT = "DEVELOPMENT"
STATES = frozenset({UNKNOWN, DECLARED_UNINSPECTED, INSPECTED, DEVELOPMENT})
# These are HISTORICAL EXPOSURE FACTS from the September 23 producer records.
# No later user, branch or score may change them back to uninspected.
KNOWN_EXPOSED_FLOOR = frozenset({
    ("GSE301119", "CRISPRa", "target_engagement"),
    ("GSE301119", "CRISPRi", "target_engagement"),
    ("GSE293118", "HMC3_noncoding_CRISPRi", "target_engagement"),
    ("GSE254205", "bulk_GNE317", "AB_vs_NT"),
    ("GSE254205", "bulk_GNE317", "AB_GNE_vs_AB"),
    ("GSE254205", "bulk_GNE317", "AB_GNE_vs_NT"),
})


class ExposureError(ValueError):
    pass


def digest(body: object) -> str:
    return hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OutcomeKey:
    study: str
    arm: str
    outcome_family: str

    def validate(self) -> None:
        for name in (self.study, self.arm, self.outcome_family):
            if (not isinstance(name, str) or not name.strip()
                    or name != name.strip()):
                raise ExposureError("study, arm and outcome family must be nonempty exact strings")

    def tuple(self) -> tuple[str, str, str]:
        self.validate()
        return self.study, self.arm, self.outcome_family


@dataclass(frozen=True)
class ExposureEvent:
    key: OutcomeKey
    new_status: str
    reason: str
    evidence_ref: str

    def validate(self) -> None:
        self.key.validate()
        if self.new_status not in STATES or self.new_status == UNKNOWN:
            raise ExposureError("event status must be a declared non-UNKNOWN state")
        if len(self.reason.strip()) < 20:
            raise ExposureError("exposure event requires a substantive reason")
        if not self.evidence_ref.strip():
            raise ExposureError("exposure event requires a concrete historical/review reference")

    def body(self) -> dict:
        self.validate()
        return {
            "key": list(self.key.tuple()), "new_status": self.new_status,
            "reason": self.reason, "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True)
class FrozenLedger:
    events: tuple[ExposureEvent, ...]
    ledger_sha256: str

    def body(self) -> dict:
        return {"schema": SCHEMA, "events": [event.body() for event in self.events]}

    def current(self) -> dict[tuple[str, str, str], str]:
        status: dict[tuple[str, str, str], str] = {}
        for event in self.events:
            event.validate()
            key = event.key.tuple()
            old = status.get(key, INSPECTED if key in KNOWN_EXPOSED_FLOOR else UNKNOWN)
            # UNKNOWN may transition to declared-uninspected or inspected.
            # Never permit an already inspected outcome to become untouched.
            allowed = {
                UNKNOWN: {DECLARED_UNINSPECTED, INSPECTED, DEVELOPMENT},
                DECLARED_UNINSPECTED: {INSPECTED, DEVELOPMENT},
                INSPECTED: {INSPECTED, DEVELOPMENT},
                DEVELOPMENT: {DEVELOPMENT},
            }
            if event.new_status not in allowed[old]:
                raise ExposureError(
                    f"forbidden exposure regression for {key}: {old} -> {event.new_status}"
                )
            status[key] = event.new_status
        for key in KNOWN_EXPOSED_FLOOR:
            if status.get(key, INSPECTED) in (UNKNOWN, DECLARED_UNINSPECTED):
                raise ExposureError(f"historically inspected outcome was downgraded: {key}")
        return status

    def validate(self) -> None:
        self.current()
        if digest(self.body()) != self.ledger_sha256:
            raise ExposureError("exposure ledger has changed after freeze")

    def status(self, key: OutcomeKey) -> str:
        self.validate()
        target = key.tuple()
        return self.current().get(
            target, INSPECTED if target in KNOWN_EXPOSED_FLOOR else UNKNOWN,
        )

    def evaluation_scope(self, key: OutcomeKey) -> dict:
        """Fail-closed classification; NEVER certify independent confirmation."""
        status = self.status(key)
        return {
            "key": list(key.tuple()),
            "exposure_status": status,
            "historically_inspected": (
                key.tuple() in KNOWN_EXPOSED_FLOOR
                or status in (INSPECTED, DEVELOPMENT)
            ),
            "retrospective_reporting_allowed": status in (
                INSPECTED, DEVELOPMENT, DECLARED_UNINSPECTED
            ),
            "untouched_external_confirmation_authorized": False,
            "requires_separate_prospective_outcome_seal": True,
            "ledger_sha256": self.ledger_sha256,
        }


def freeze_ledger(events: Sequence[ExposureEvent]) -> FrozenLedger:
    """Mechanically freeze a reviewed event sequence; NOT evidence of independent review."""
    frozen = FrozenLedger(tuple(events), "")
    frozen.current()
    result = FrozenLedger(frozen.events, digest(frozen.body()))
    result.validate()
    return result


def append_event(ledger: FrozenLedger, event: ExposureEvent) -> FrozenLedger:
    ledger.validate()
    return freeze_ledger((*ledger.events, event))


def seed_historical_exposure() -> FrozenLedger:
    """Freeze exactly the inspected outcome families known on 2026-09-23.

    We cannot infer untouched status of any other outcome from this list;
    all absent (study, arm, outcome) triples default to UNKNOWN.
    """
    return freeze_ledger([
        ExposureEvent(
            OutcomeKey(*key), INSPECTED,
            "Observed target engagement or bulk contrast outputs inspected on 2026-09-23.",
            "PR77_20260923_EXPERIMENTAL_PRODUCER_EVIDENCE",
        ) for key in sorted(KNOWN_EXPOSED_FLOOR)
    ])
