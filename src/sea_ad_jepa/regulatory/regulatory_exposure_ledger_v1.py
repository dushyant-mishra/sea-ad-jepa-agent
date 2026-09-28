"""Append-only regulatory outcome exposure ledger V1.

Exposure is tracked at the exact (source, modality, outcome_family) level.
Dataset-wide labels are prohibited because structural authentication, RNA use,
ATAC use, pathology metadata, and target-state correspondence have different
histories.

This ledger is deliberately NON-AUTHORIZING. It can prove that an outcome is
already exposed, but it cannot prove that an absent/UNKNOWN outcome is pristine.
Any prospective confirmation claim still requires a separately reviewed,
physically pinned outcome-seal contract.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

SCHEMA = "JEPA_REGULATORY_OUTCOME_EXPOSURE_LEDGER_V1"
UNKNOWN = "UNKNOWN"
STRUCTURAL_ONLY = "STRUCTURAL_ONLY"
INSPECTED = "INSPECTED"
DEVELOPMENT = "DEVELOPMENT"
STATES = frozenset({UNKNOWN, STRUCTURAL_ONLY, INSPECTED, DEVELOPMENT})

ROLE_DEVELOPMENT = "DEVELOPMENT"
ROLE_RETROSPECTIVE = "RETROSPECTIVE"
ROLE_CONFIRMATION_CANDIDATE = "PROSPECTIVE_CONFIRMATION_CANDIDATE"
ROLES = frozenset({ROLE_DEVELOPMENT, ROLE_RETROSPECTIVE, ROLE_CONFIRMATION_CANDIDATE})


class RegulatoryExposureError(ValueError):
    pass


def digest(body: object) -> str:
    return hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


@dataclass(frozen=True, order=True)
class RegulatoryOutcomeKey:
    source: str
    modality: str
    outcome_family: str

    def validate(self) -> None:
        for x in (self.source, self.modality, self.outcome_family):
            if not isinstance(x, str) or not x.strip() or x != x.strip():
                raise RegulatoryExposureError("key fields must be exact nonempty strings")

    def tuple(self) -> tuple[str, str, str]:
        self.validate()
        return self.source, self.modality, self.outcome_family


@dataclass(frozen=True)
class ExposureEvent:
    key: RegulatoryOutcomeKey
    new_status: str
    reason: str
    evidence_ref: str

    def validate(self) -> None:
        self.key.validate()
        if self.new_status not in STATES or self.new_status == UNKNOWN:
            raise RegulatoryExposureError("events require a declared non-UNKNOWN state")
        if len(self.reason.strip()) < 20:
            raise RegulatoryExposureError("reason must be substantive")
        if not self.evidence_ref.strip():
            raise RegulatoryExposureError("evidence_ref required")

    def body(self) -> dict:
        self.validate()
        return {
            "key": list(self.key.tuple()),
            "new_status": self.new_status,
            "reason": self.reason,
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True)
class FrozenRegulatoryLedger:
    events: tuple[ExposureEvent, ...]
    ledger_sha256: str

    def body(self) -> dict:
        return {"schema": SCHEMA, "events": [x.body() for x in self.events]}

    def current(self) -> dict[tuple[str, str, str], str]:
        state: dict[tuple[str, str, str], str] = {}
        allowed = {
            UNKNOWN: {STRUCTURAL_ONLY, INSPECTED, DEVELOPMENT},
            STRUCTURAL_ONLY: {STRUCTURAL_ONLY, INSPECTED, DEVELOPMENT},
            INSPECTED: {INSPECTED, DEVELOPMENT},
            DEVELOPMENT: {DEVELOPMENT},
        }
        for event in self.events:
            event.validate()
            k = event.key.tuple()
            old = state.get(k, UNKNOWN)
            if event.new_status not in allowed[old]:
                raise RegulatoryExposureError(
                    f"forbidden exposure regression for {k}: {old} -> {event.new_status}"
                )
            state[k] = event.new_status
        return state

    def validate(self) -> None:
        self.current()
        if digest(self.body()) != self.ledger_sha256:
            raise RegulatoryExposureError("ledger content changed after freeze")

    def status(self, key: RegulatoryOutcomeKey) -> str:
        self.validate()
        return self.current().get(key.tuple(), UNKNOWN)

    def scope(self, key: RegulatoryOutcomeKey) -> dict:
        """Describe exposure without ever certifying prospective confirmation."""
        status = self.status(key)
        return {
            "key": list(key.tuple()),
            "exposure_status": status,
            "outcome_values_known_exposed": status in (INSPECTED, DEVELOPMENT),
            "used_for_development": status == DEVELOPMENT,
            "structural_only": status == STRUCTURAL_ONLY,
            "prospective_confirmation_authorized": False,
            "requires_separate_physical_outcome_seal": True,
            "ledger_sha256": self.ledger_sha256,
        }


def freeze_ledger(events: Sequence[ExposureEvent]) -> FrozenRegulatoryLedger:
    first = FrozenRegulatoryLedger(tuple(events), "")
    first.current()
    result = FrozenRegulatoryLedger(first.events, digest(first.body()))
    result.validate()
    return result


def append_event(ledger: FrozenRegulatoryLedger, event: ExposureEvent) -> FrozenRegulatoryLedger:
    ledger.validate()
    return freeze_ledger((*ledger.events, event))


def guard_role(ledger: FrozenRegulatoryLedger, key: RegulatoryOutcomeKey, requested_role: str) -> dict:
    """Fail closed; prospective confirmation is never authorized by this ledger alone."""
    if requested_role not in ROLES:
        raise RegulatoryExposureError("unknown requested role")
    status = ledger.status(key)
    if requested_role == ROLE_CONFIRMATION_CANDIDATE:
        return {
            **ledger.scope(key),
            "requested_role": requested_role,
            "role_state": (
                "BLOCKED_ALREADY_EXPOSED" if status in (INSPECTED, DEVELOPMENT)
                else "REQUIRES_SEPARATE_PHYSICAL_OUTCOME_SEAL"
            ),
        }
    if requested_role == ROLE_RETROSPECTIVE and status == UNKNOWN:
        raise RegulatoryExposureError("retrospective interpretation requires documented exposure provenance")
    return {
        **ledger.scope(key),
        "requested_role": requested_role,
        "role_state": "ALLOWED_AS_NONCONFIRMATORY_USE",
    }


@dataclass(frozen=True)
class RegulatoryObjectProvenance:
    object_id: str
    method: str
    construction_sources: tuple[RegulatoryOutcomeKey, ...]
    uses_full104: bool
    uses_same_nucleus_pairing: bool
    uses_pathology_or_diagnosis: bool

    def validate(self) -> None:
        if not self.object_id.strip() or not self.method.strip():
            raise RegulatoryExposureError("object id and method required")
        if not self.construction_sources:
            raise RegulatoryExposureError("regulatory object must name construction sources")
        for k in self.construction_sources:
            k.validate()

    def assessment_against(self, source: str) -> dict:
        self.validate()
        same_source = any(k.source == source for k in self.construction_sources)
        return {
            "object_id": self.object_id,
            "candidate_source": source,
            "same_source_as_construction": same_source,
            "independent_confirmation_authorized": False,
            "state": (
                "NOT_INDEPENDENT__CONSTRUCTION_SOURCE" if same_source
                else "REQUIRES_SEPARATE_INDEPENDENCE_AND_OUTCOME_SEAL_AUDIT"
            ),
        }


CROSS_SOURCE_RULES = {
    tuple(sorted(("GSE214979", "GSE174367_MORABITO"))): {
        "determination": "UNDETERMINED_POSSIBLE_UCI_DONOR_OVERLAP",
        "binding_rule": "agreement claim must exclude GSE214979 donors 1224,1230,1238 or carry explicit caveat",
        "evidence_ref": "PR182",
    },
    tuple(sorted(("GSE214979", "GSE272082"))): {
        "determination": "INDEPENDENT_BY_CURRENT_AUDIT",
        "evidence_ref": "PR182",
    },
    tuple(sorted(("FULL104", "GSE174367_MORABITO"))): {
        "determination": "INDEPENDENT_DONORS_BY_CURRENT_AUDIT",
        "evidence_ref": "PR164",
    },
    tuple(sorted(("FULL104", "SEAAD_PUBLIC_MULTIOME"))): {
        "determination": "NOT_INDEPENDENT__SEAAD_IS_FULL104_SOURCE",
        "evidence_ref": "V50_PR189",
    },
}


def cross_source_rule(a: str, b: str) -> dict:
    if a == b:
        return {"determination": "SAME_SOURCE", "independent_confirmation_authorized": False}
    rule = CROSS_SOURCE_RULES.get(tuple(sorted((a, b))))
    if rule is None:
        return {"determination": "UNKNOWN_REQUIRES_AUDIT", "independent_confirmation_authorized": False}
    return {**rule, "independent_confirmation_authorized": False}


def seed_historical_regulatory_exposure() -> FrozenRegulatoryLedger:
    """Seed only evidence-backed exposure facts; absent keys remain UNKNOWN."""
    E = ExposureEvent
    K = RegulatoryOutcomeKey
    return freeze_ledger([
        E(K("FULL104", "RNA", "RELATIONAL_STATE_TD56_TD59"), DEVELOPMENT,
          "Relational RNA state was discovered and repeatedly evaluated in the historical target-discovery sequence.",
          "V50_PR189_TD56_TD59"),
        E(K("GSE174367_MORABITO", "RNA", "MICROGLIA_PSEUDOBULK_TF_TARGET_COACTIVITY"), DEVELOPMENT,
          "Stage75F candidate TF-target edges use Spearman coactivity from the same 18-sample Morabito RNA pseudobulk.",
          "PR164_STAGE75F_CIRCULARITY"),
        E(K("GSE174367_MORABITO", "ATAC", "MARGINAL_ACCESSIBILITY_AND_COVERAGE"), INSPECTED,
          "Morabito ATAC values were used for accessibility and feature-support auditing, not target-state correspondence.",
          "PR164_PR175_ATAC_COVERAGE"),
        E(K("GSE214979", "METADATA", "PAIRING_CELLTYPE_DONOR_CENSUS"), INSPECTED,
          "Pairing, donor, cell-type and microglia census metadata were inspected during paired-Multiome authentication.",
          "PR182_LANE_PM"),
        E(K("GSE214979", "METADATA", "DIAGNOSIS_GROUP_LABELS_FOR_DESIGN"), INSPECTED,
          "AD/control group labels were used for design and power accounting; molecular regulatory outcomes were not evaluated.",
          "PR182_LANE_PM"),
        E(K("GSE272082", "METADATA", "DONOR_REGION_AND_LABEL_AUTHENTICATION"), INSPECTED,
          "Donor reconstruction, region structure and disease-label conflicts were inspected without acquiring molecular matrices.",
          "PR182_LANE_PM"),
        E(K("SEAAD_PUBLIC_MULTIOME", "METADATA", "EXACT_PAIRING_AND_MYELOID_CENSUS"), INSPECTED,
          "Exact public RNA/ATAC pairing and myeloid donor/cell counts were structurally audited without target correspondence.",
          "V51_REPORTED_PAIRING_CUSTODY"),
        E(K("SEAAD_PUBLIC_MULTIOME", "RNA", "FULL104_RELATIONAL_STATE_CONTRIBUTION"), DEVELOPMENT,
          "SEA-AD RNA is part of FULL104 and therefore contributes to the historical RNA target/discovery substrate.",
          "V50_PR189_FULL104_SOURCE"),
        E(K("SEAAD_SPATIAL", "METADATA", "PANEL_CELLTYPE_DONOR_STRUCTURE"), INSPECTED,
          "R4 inspected spatial panel identities, cell types and donor/section structure where available.",
          "V52_R4_RECOVERY"),
        E(K("SEAAD_SPATIAL", "TECHNICAL", "DETECTION_AND_SEGMENTATION_METRICS"), INSPECTED,
          "R4 inspected transcript-count, detected-gene and segmentation asymmetries as technical feasibility evidence.",
          "V52_R4_RECOVERY"),
        E(K("STAGE75F", "DERIVED_OBJECT", "TF_TIER_AND_TARGET_HYPOTHESES"), DEVELOPMENT,
          "Historical Stage75F regulator tiers and target hypotheses were constructed, inspected and later specificity-audited.",
          "PR164_V52_R2_CLOSEOUT"),
    ])
