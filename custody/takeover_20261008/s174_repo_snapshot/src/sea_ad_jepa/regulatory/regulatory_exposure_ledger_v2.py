"""Regulatory outcome exposure ledger, VERSION 2 — versioned successor to V1.

V1 (`regulatory_exposure_ledger_v1.py`) is NOT modified. Its schema string,
state lattice, seed function and cross-source rules are left exactly as they
are, and this module imports them. Historical snapshots computed against V1
therefore remain reproducible.

WHY A SUCCESSOR IS NEEDED

V1's exposure lattice is

    UNKNOWN -> STRUCTURAL_ONLY -> INSPECTED -> DEVELOPMENT

and it conflates two things the V63 work requires to be separate:

  1. HOW MUCH of an outcome family has been seen. V1 has no state for
     "I have read the abstract's claims but have not inspected the data".
     Recording McQuade/GSE335887 as INSPECTED would overstate the exposure;
     recording it as STRUCTURAL_ONLY would understate it.

  2. WHETHER THE RESOURCE IS EVEN OBTAINABLE. Access terms are orthogonal to
     exposure. Kosoy Hi-C is access-required AND essentially unexposed; DS010 is
     embargoed AND its AD-vs-control outcomes are exposed through the preprint.
     Encoding access as an exposure state would make one imply the other, which
     is false in both directions.

V2 therefore:
  - inserts ABSTRACT_LEVEL between STRUCTURAL_ONLY and INSPECTED, preserving
    monotonicity (exposure may only increase);
  - adds an ACCESS_CLASS axis that is recorded per source and never mixed into
    the exposure state;
  - adds cross-source determinations including PROBABLE_SHARED_DONORS, which is
    explicitly weaker than proven identity.

TRAINING=OFF. TD60=BLOCKED.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .regulatory_exposure_ledger_v1 import (  # noqa: F401  (re-exported on purpose)
    DEVELOPMENT,
    INSPECTED,
    STRUCTURAL_ONLY,
    UNKNOWN,
    ExposureEvent,
    RegulatoryExposureError,
    RegulatoryOutcomeKey,
    digest,
)
from . import regulatory_exposure_ledger_v1 as V1

SCHEMA = "JEPA_REGULATORY_OUTCOME_EXPOSURE_LEDGER_V2"
SUPERSEDES = V1.SCHEMA

# ---------------------------------------------------------------- exposure axis
ABSTRACT_LEVEL = "ABSTRACT_LEVEL"
STATES_V2 = frozenset({UNKNOWN, STRUCTURAL_ONLY, ABSTRACT_LEVEL, INSPECTED, DEVELOPMENT})

# Monotone: exposure may increase, never decrease. ABSTRACT_LEVEL sits between
# STRUCTURAL_ONLY and INSPECTED because knowing an abstract's claims is more than
# knowing a dataset's shape and less than having inspected its values.
ALLOWED_TRANSITIONS = {
    UNKNOWN: {STRUCTURAL_ONLY, ABSTRACT_LEVEL, INSPECTED, DEVELOPMENT},
    STRUCTURAL_ONLY: {STRUCTURAL_ONLY, ABSTRACT_LEVEL, INSPECTED, DEVELOPMENT},
    ABSTRACT_LEVEL: {ABSTRACT_LEVEL, INSPECTED, DEVELOPMENT},
    INSPECTED: {INSPECTED, DEVELOPMENT},
    DEVELOPMENT: {DEVELOPMENT},
}
ORDER = {UNKNOWN: 0, STRUCTURAL_ONLY: 1, ABSTRACT_LEVEL: 2, INSPECTED: 3, DEVELOPMENT: 4}

# ------------------------------------------------------------------ access axis
OPEN_PUBLIC = "OPEN_PUBLIC"
EMBARGOED = "EMBARGOED"
CONTROLLED_OR_ACCESS_REQUIRED = "CONTROLLED_OR_ACCESS_REQUIRED"
ACCESS_CLASSES = frozenset({UNKNOWN, OPEN_PUBLIC, EMBARGOED, CONTROLLED_OR_ACCESS_REQUIRED})

#: Access classes that may never carry a load-bearing qualification claim.
NOT_LOAD_BEARING = frozenset({EMBARGOED, CONTROLLED_OR_ACCESS_REQUIRED, UNKNOWN})


@dataclass(frozen=True)
class AccessRecord:
    source: str
    access_class: str
    evidence_ref: str
    note: str = ""
    #: release date for EMBARGOED, ISO yyyy-mm-dd, else ""
    scheduled_release: str = ""

    def validate(self) -> None:
        if not self.source.strip():
            raise RegulatoryExposureError("source required")
        if self.access_class not in ACCESS_CLASSES:
            raise RegulatoryExposureError(f"unknown access class {self.access_class!r}")
        if not self.evidence_ref.strip():
            raise RegulatoryExposureError("evidence_ref required")
        if self.access_class == EMBARGOED and not self.scheduled_release.strip():
            raise RegulatoryExposureError("EMBARGOED requires scheduled_release")

    def load_bearing_allowed(self) -> bool:
        """Whether this source may carry a load-bearing qualification claim.

        Deliberately fail-closed: anything that is not affirmatively OPEN_PUBLIC
        is refused, including UNKNOWN. 'We have not checked the terms' is not a
        licence to rely on something.
        """
        self.validate()
        return self.access_class == OPEN_PUBLIC

    def body(self) -> dict:
        self.validate()
        return {"source": self.source, "access_class": self.access_class,
                "evidence_ref": self.evidence_ref, "note": self.note,
                "scheduled_release": self.scheduled_release,
                "load_bearing_allowed": self.load_bearing_allowed()}


@dataclass(frozen=True)
class ExposureEventV2:
    key: RegulatoryOutcomeKey
    new_status: str
    reason: str
    evidence_ref: str

    def validate(self) -> None:
        self.key.validate()
        if self.new_status not in STATES_V2 or self.new_status == UNKNOWN:
            raise RegulatoryExposureError("events require a declared non-UNKNOWN state")
        if len(self.reason.strip()) < 20:
            raise RegulatoryExposureError("reason must be substantive")
        if not self.evidence_ref.strip():
            raise RegulatoryExposureError("evidence_ref required")

    def body(self) -> dict:
        self.validate()
        return {"key": list(self.key.tuple()), "new_status": self.new_status,
                "reason": self.reason, "evidence_ref": self.evidence_ref}


@dataclass(frozen=True)
class FrozenLedgerV2:
    events: tuple[ExposureEventV2, ...]
    access: tuple[AccessRecord, ...]
    ledger_sha256: str

    def body(self) -> dict:
        return {"schema": SCHEMA, "supersedes": SUPERSEDES,
                "events": [e.body() for e in self.events],
                "access": [a.body() for a in self.access]}

    def current(self) -> dict[tuple[str, str, str], str]:
        state: dict[tuple[str, str, str], str] = {}
        for ev in self.events:
            ev.validate()
            k = ev.key.tuple()
            old = state.get(k, UNKNOWN)
            if ev.new_status not in ALLOWED_TRANSITIONS[old]:
                raise RegulatoryExposureError(
                    f"forbidden exposure regression for {k}: {old} -> {ev.new_status}")
            state[k] = ev.new_status
        return state

    def access_for(self, source: str) -> AccessRecord | None:
        for a in self.access:
            if a.source == source:
                return a
        return None

    def may_be_load_bearing(self, source: str) -> dict:
        """Fail-closed gate on using a source as load-bearing evidence."""
        rec = self.access_for(source)
        if rec is None:
            return {"source": source, "allowed": False,
                    "reason": "NO_ACCESS_RECORD__FAIL_CLOSED"}
        return {"source": source, "allowed": rec.load_bearing_allowed(),
                "access_class": rec.access_class,
                "reason": ("OPEN_PUBLIC" if rec.load_bearing_allowed()
                           else f"NOT_LOAD_BEARING__{rec.access_class}")}


def freeze_ledger_v2(events: Sequence[ExposureEventV2],
                     access: Sequence[AccessRecord]) -> FrozenLedgerV2:
    evs = tuple(events)
    acc = tuple(access)
    for e in evs:
        e.validate()
    for a in acc:
        a.validate()
    seen = set()
    for a in acc:
        if a.source in seen:
            raise RegulatoryExposureError(f"duplicate access record for {a.source}")
        seen.add(a.source)
    body = {"schema": SCHEMA, "supersedes": SUPERSEDES,
            "events": [e.body() for e in evs], "access": [a.body() for a in acc]}
    led = FrozenLedgerV2(evs, acc, digest(body))
    led.current()  # raises on a forbidden regression at construction time
    return led


# ------------------------------------------------------- cross-source rules V2
CROSS_SOURCE_RULES_V2 = dict(V1.CROSS_SOURCE_RULES)
CROSS_SOURCE_RULES_V2.update({
    tuple(sorted(("TIAN_LI", "SILETTI"))): {
        "determination": "PROBABLE_SHARED_DONORS",
        "binding_rule": (
            "PROBABLE is strictly weaker than PROVEN. Do not treat these as the same "
            "donors and do not treat them as disjoint. Any claim spanning both must "
            "state the overlap as unresolved, per the standing rule that donor "
            "identity is resolved through stable key layers and never inferred from "
            "institution or demographics alone."),
        "evidence_ref": "V63_TASK9",
    },
    tuple(sorted(("NIH_CARD", "FULL104"))): {
        "determination": "UNKNOWN_REQUIRES_AUDIT",
        "binding_rule": "no donor-level crosswalk attempted; do not assert independence",
        "evidence_ref": "V63_TASK9",
    },
})


def cross_source_rule_v2(a: str, b: str) -> dict:
    if a == b:
        return {"determination": "SAME_SOURCE", "independent_confirmation_authorized": False}
    rule = CROSS_SOURCE_RULES_V2.get(tuple(sorted((a, b))))
    if rule is None:
        return {"determination": "UNKNOWN_REQUIRES_AUDIT",
                "independent_confirmation_authorized": False}
    return {**rule, "independent_confirmation_authorized": False}


def seed_v63_exposure() -> FrozenLedgerV2:
    """V63 exposure facts. Additive: nothing from V1 is contradicted."""
    E, K = ExposureEventV2, RegulatoryOutcomeKey
    events = [
        E(K("DS010_WANG2025", "SNM3C_CONTACT", "AD_VS_CONTROL_LOOP_AND_COMPARTMENT"),
          DEVELOPMENT,
          "The preprint's AD-vs-control 3D-genome findings (region-specific compartment, "
          "TAD-boundary and loop reorganization) were read during the V63 source audit. "
          "This outcome family is therefore development-exposed and must never be used "
          "to select or weight E2 edges.",
          "V63_TASK4;PMC12621709"),
        E(K("DS010_WANG2025", "METHYLATION", "AD_VS_CONTROL_DIFFERENTIAL_METHYLATION"),
          DEVELOPMENT,
          "The preprint's region-specific hyper/hypomethylation contrasts were read in "
          "the same pass. Same restriction: not usable for edge selection or weighting.",
          "V63_TASK4;PMC12621709"),
        E(K("DS010_WANG2025", "COHORT", "DONOR_DIAGNOSIS_APOE_BRAAK"),
          INSPECTED,
          "The public SuperSeries table GSE308132_supplementary_table.txt.gz exposes "
          "donor-level diagnosis, sex, age, APOE genotype and Braak stage for all 20 "
          "donors. Cohort description, not a molecular outcome, but recorded because it "
          "is donor-level pathology metadata.",
          "V63_TASK4;GSE308132"),
        E(K("GSE335887_MCQUADE", "UNSPECIFIED", "PUBLISHED_ABSTRACT_CLAIMS"),
          ABSTRACT_LEVEL,
          "Exposure is limited to abstract-level claims. No data were inspected and no "
          "values were read. Recorded at the new ABSTRACT_LEVEL state precisely because "
          "INSPECTED would overstate and STRUCTURAL_ONLY would understate it.",
          "V63_TASK9"),
        E(K("NIH_CARD_CATCHING2026", "MULTIOME", "SCHEMA_AND_COUNTS"),
          STRUCTURAL_ONLY,
          "Only schema, barcode namespace, donor labels, covariate column presence and "
          "microglia counts are being read, by an outcome-blind probe that computes no "
          "RNA-ATAC relationship. No biological outcome is opened by this.",
          "V63_TASK3;h5ad_schema_probe_v2"),
        E(K("NIH_CARD_CATCHING2026", "MULTIOME", "AGING_ASSOCIATED_GENES_AND_PEAKS"),
          ABSTRACT_LEVEL,
          "The publication's aging-associated gene and peak findings are known at "
          "abstract level from the source audit. Not inspected. This outcome family must "
          "not steer E2 construction or threshold choice.",
          "V63_TASK3;Cell Reports 2026"),
        E(K("KOSOY2022", "HIC_CONTACT", "MICROGLIA_REGULOME_LOOPS"),
          STRUCTURAL_ONLY,
          "Construction properties are known from the published record only. The "
          "distributed Hi-C artifact has never been obtained or inspected, because it is "
          "access-required and the no-DUA rule is binding.",
          "V59_KOSOY_PROVENANCE;V63_TASK6"),
        E(K("NOTT2019", "PLACSEQ_CONTACT", "CELLTYPE_LOOP_CALLS"),
          STRUCTURAL_ONLY,
          "Assay design, donor count, cell source and genome build are known from the "
          "published record. The processed interaction table has NOT been obtained: PMC "
          "serves a proof-of-work interstitial and Europe PMC returns an error. No loop "
          "value has been read.",
          "V63_TASK6;PMC7028213"),
    ]
    access = [
        AccessRecord("NOTT2019_PROCESSED_LOOPS", OPEN_PUBLIC,
                     "V63_TASK6;PMC7028213 supplementary Table S5",
                     "Published open-access supplementary table. Open in TERMS; not "
                     "retrievable in this environment because of a download gate. "
                     "Obtainability and licence are different questions and only the "
                     "licence is recorded here."),
        AccessRecord("NOTT2019_RAW", CONTROLLED_OR_ACCESS_REQUIRED,
                     "V63_TASK6;dbGaP phs001373.v2.p1",
                     "Raw PLAC-seq is dbGaP-controlled. Excluded by the no-DUA rule."),
        AccessRecord("DS010_WANG2025_CONTACT", EMBARGOED,
                     "V63_TASK4;GSE308668,GSE308906",
                     "Both SubSeries are private. GEO verbatim: 'currently private and "
                     "is scheduled to be released on Feb 01, 2027'.",
                     scheduled_release="2027-02-01"),
        AccessRecord("DS010_COMPANION_MULTIOME", EMBARGOED,
                     "V63_TASK5;GSE308668/GSE308906",
                     "The companion 10x Multiome is one of the two private SubSeries; "
                     "which one is not publicly determinable.",
                     scheduled_release="2027-02-01"),
        AccessRecord("KOSOY2022_HIC", CONTROLLED_OR_ACCESS_REQUIRED,
                     "V59_KOSOY_PROVENANCE;AD Knowledge Portal",
                     "SUPPORTING_ONLY. Rediscovered copies on GitHub, Zenodo or "
                     "elsewhere do NOT make this open unless the data owners released "
                     "it under open terms."),
        AccessRecord("KOSOY2022_ATAC", UNKNOWN,
                     "V63_TASK6",
                     "Terms NOT verified. V59 established Kosoy has no NCBI deposit at "
                     "all, so any open distribution must be located and its licence read "
                     "before use. UNKNOWN is fail-closed: not usable as load-bearing."),
        AccessRecord("YANG_GSE173316", OPEN_PUBLIC,
                     "V63_TASK6;GSE173316",
                     "Series is public, but the pcHi-C interaction artifact was NOT "
                     "located in it: the series RAW tar holds only RSEM gene results and "
                     "CRISPR count matrices. Open terms, artifact unlocated."),
        AccessRecord("NIH_CARD_CATCHING2026", OPEN_PUBLIC,
                     "V63_TASK3;Zenodo 10.5281/zenodo.20834804",
                     "CC-BY 4.0. final_rna_data.h5ad 18.4 GB, final_atac_data.h5ad "
                     "14.5 GB. Validation candidate ONLY."),
    ]
    return freeze_ledger_v2(events, access)


#: Construction prohibitions that are about ROLE rather than exposure or access.
CONSTRUCTION_PROHIBITIONS = {
    "NIH_CARD_CATCHING2026": (
        "VALIDATION CANDIDATE ONLY. Its derived co-accessibility and peak-gene links "
        "must NEVER enter E2 construction. Its consensus peak universe may be used only "
        "as a measurement-support restriction applied IDENTICALLY to matched linked and "
        "unlinked pairs, which is not construction evidence."),
    "DS010_WANG2025": (
        "Published AD-vs-control loop and methylation outcomes are development-exposed "
        "and must not select or weight edges. A controls-only sensitivity arm is "
        "permissible; the primary contact geometry must ignore diagnosis labels."),
    "KOSOY2022_HIC": (
        "Not load-bearing while access-required."),
    "SEAAD_MORABITO_GSE214979_GSE272082": (
        "Validation-cohort accessibility must not construct the edge set."),
}
