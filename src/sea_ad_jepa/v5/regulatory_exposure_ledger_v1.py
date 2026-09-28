#!/usr/bin/env python3
"""Regulatory independence / exposure ledger — fail-closed provenance.

WHAT THIS IS FOR

  A regulatory hypothesis is "independent" of a dataset only if its DEFINITION
  did not consume that dataset. The project has already been bitten by the
  opposite: Stage75F's TF-target edges were derived from the same Morabito RNA
  pseudobulk they would have been used to score, which makes them an answer key
  written from the answers.

  This ledger records, per regulatory object, exactly which sources went into
  its definition, and refuses — at call time, with an exception — to let an
  analysis describe it as confirmation in a source it already consumed.

WHAT IT IS NOT

  Not training authority. Not a scientific claim. Not a substitute for the
  outcome-exposure ledger governing protected biological outcomes; this one
  governs REGULATORY OBJECT provenance and is deliberately narrower.

THE CONSERVATISM RULE

  UNKNOWN is a valid and preferred value. An object whose provenance has not
  been established is NOT eligible for confirmation anywhere, because an
  unproven independence claim is exactly the failure this file exists to stop.
  Eligibility must be earned by recorded provenance, never inherited by
  silence.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum


class Contribution(str, Enum):
    """Did this source contribute to the object's DEFINITION?"""
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"          # conservative default: blocks confirmation


class Derivation(str, Enum):
    FULL104_RNA_DERIVED = "FULL104_RNA_DERIVED"
    MORABITO_RNA_DERIVED = "MORABITO_RNA_DERIVED"
    MORABITO_ATAC_DIRECT = "MORABITO_ATAC_DIRECT"
    GSE214979_MULTIOME_DERIVED = "GSE214979_MULTIOME_DERIVED"
    GSE272082_MULTIOME_DERIVED = "GSE272082_MULTIOME_DERIVED"
    SEAAD_ATAC_DERIVED = "SEAAD_ATAC_DERIVED"
    EXTERNAL_REFERENCE_DERIVED = "EXTERNAL_REFERENCE_DERIVED"
    LITERATURE_HYPOTHESIS = "LITERATURE_HYPOTHESIS"
    UNKNOWN = "UNKNOWN"


class ExposureState(str, Enum):
    UNOPENED = "UNOPENED"
    DEVELOPMENT_EXPOSED = "DEVELOPMENT_EXPOSED"
    HISTORICALLY_EXPOSED = "HISTORICALLY_EXPOSED"
    PERTURBATION_EXPOSED = "PERTURBATION_EXPOSED"
    CONFIRMATORY_ELIGIBLE = "CONFIRMATORY_ELIGIBLE"
    SPATIAL_UNAUDITED = "SPATIAL_UNAUDITED"
    UNKNOWN = "UNKNOWN"


# Every dataset an object may be evaluated in. Adding one here without adding
# it to each object's contribution map leaves it UNKNOWN, which blocks.
DATASETS = ("FULL104_RNA", "MORABITO_RNA", "MORABITO_ATAC",
            "GSE214979_MULTIOME", "GSE272082_MULTIOME", "SEAAD_MTG_ATAC",
            "SEAAD_SPATIAL", "GSE301119_PERTURBATION", "GSE289721_PERTURBATION")


class ConfirmationRefused(Exception):
    """Raised when an analysis calls an object independent where it is not."""


@dataclass
class RegulatoryObject:
    object_id: str
    version: str
    regulator: str | None                 # TF or None for TF-free modules
    regions: str                          # description/id of the region set
    targets: str                          # target/module description
    method: str
    derivation: Derivation
    cohort_lab: str
    donors_used: int | None
    contributions: dict = field(default_factory=dict)   # dataset -> Contribution
    rna_contributed: Contribution = Contribution.UNKNOWN
    atac_contributed: Contribution = Contribution.UNKNOWN
    full104_contributed: Contribution = Contribution.UNKNOWN
    stage75_member: bool = False
    used_for_development: bool = False
    exposure: ExposureState = ExposureState.UNKNOWN
    notes: str = ""

    def contribution_to(self, dataset: str) -> Contribution:
        if dataset not in DATASETS:
            raise ValueError(f"unknown dataset {dataset!r}; add it to DATASETS "
                             "so every object must declare a value for it")
        return self.contributions.get(dataset, Contribution.UNKNOWN)

    def confirmation_eligible_in(self, dataset: str) -> tuple[bool, str]:
        c = self.contribution_to(dataset)
        if c is Contribution.YES:
            return False, (f"{self.object_id} was DEFINED using {dataset}; it "
                           "cannot confirm itself there")
        if c is Contribution.UNKNOWN:
            return False, (f"{self.object_id} has UNKNOWN contribution from "
                           f"{dataset}. Unproven independence is not "
                           "independence; establish provenance first.")
        if self.derivation is Derivation.UNKNOWN:
            return False, (f"{self.object_id} has UNKNOWN derivation; its "
                           "definition sources are not established")
        return True, "eligible"


class RegulatoryExposureLedger:
    def __init__(self):
        self._objects: dict[str, RegulatoryObject] = {}

    def register(self, obj: RegulatoryObject) -> None:
        if obj.object_id in self._objects:
            raise ValueError(f"duplicate object_id {obj.object_id!r}; "
                             "versions must be distinct ids")
        self._objects[obj.object_id] = obj

    def get(self, object_id: str) -> RegulatoryObject:
        if object_id not in self._objects:
            raise KeyError(f"{object_id!r} is not registered. An unregistered "
                           "object has no provenance and cannot be used.")
        return self._objects[object_id]

    def assert_confirmation_eligible(self, object_id: str, dataset: str) -> None:
        """FAIL CLOSED. Call this before describing a result as confirmation."""
        ok, why = self.get(object_id).confirmation_eligible_in(dataset)
        if not ok:
            raise ConfirmationRefused(why)

    def to_json(self) -> str:
        return json.dumps(
            {"schema": "V5_REGULATORY_EXPOSURE_LEDGER_V1",
             "datasets": list(DATASETS),
             "conservatism_rule": (
                 "UNKNOWN blocks confirmation. Eligibility is earned by "
                 "recorded provenance, never inherited by silence."),
             "objects": {k: asdict(v) for k, v in self._objects.items()}},
            indent=2, default=str)


def seed_known_objects() -> RegulatoryExposureLedger:
    """Only what the repository record actually establishes.

    Anything not established is left UNKNOWN on purpose, which blocks it.
    """
    L = RegulatoryExposureLedger()

    # --- Stage75F: the canonical cautionary case (PR #164)
    for tf in ("STAT1", "ELF1", "SPI1", "IRF8", "BACH1",
               "CEBPA", "RELA", "MITF", "NRF1", "STAT3"):
        L.register(RegulatoryObject(
            object_id=f"STAGE75F_{tf}_V1", version="stage75f",
            regulator=tf, regions="motif-screened restricted region set",
            targets="subset of 96 TF-target rows", method="motif screen",
            derivation=Derivation.MORABITO_RNA_DERIVED,
            cohort_lab="Morabito GSE174367", donors_used=None,
            contributions={
                "MORABITO_RNA": Contribution.YES,      # the definition source
                "MORABITO_ATAC": Contribution.NO,      # matrix unused by 75F
                "FULL104_RNA": Contribution.NO,
                "GSE214979_MULTIOME": Contribution.NO,
                "GSE272082_MULTIOME": Contribution.NO,
                "SEAAD_MTG_ATAC": Contribution.NO,
                "SEAAD_SPATIAL": Contribution.UNKNOWN,
                "GSE301119_PERTURBATION": Contribution.UNKNOWN,
                "GSE289721_PERTURBATION": Contribution.UNKNOWN},
            rna_contributed=Contribution.YES,
            atac_contributed=Contribution.NO,
            full104_contributed=Contribution.NO,
            stage75_member=True, used_for_development=True,
            exposure=ExposureState.HISTORICALLY_EXPOSED,
            notes=("PR #164: 10 regulators, 96 TF-target rows, motif-screened "
                   "hypothesis package. NOT a validated eRegulon network and "
                   "NOT causal. Edges derived from the same Morabito RNA "
                   "pseudobulk, so they cannot be an answer key for an "
                   "RNA-based state. Tier A/B/C are not validated strength.")))

    # --- the three FULL104 RNA programs
    for prog in ("APOE_LIPID", "P2RY12_HOMEOSTATIC", "HLA_DRA_ANTIGEN"):
        L.register(RegulatoryObject(
            object_id=f"FULL104_PROGRAM_{prog}_V1", version="r8",
            regulator=None, regions="n/a — RNA panel, not a region set",
            targets="query + 4 partners", method="predeclared RNA panel",
            derivation=Derivation.FULL104_RNA_DERIVED,
            cohort_lab="FULL104 (HVS + NPH52 + SEA-AD)", donors_used=104,
            contributions={
                "FULL104_RNA": Contribution.YES,
                "MORABITO_RNA": Contribution.NO,
                "MORABITO_ATAC": Contribution.NO,
                "GSE214979_MULTIOME": Contribution.NO,
                "GSE272082_MULTIOME": Contribution.NO,
                "SEAAD_MTG_ATAC": Contribution.NO,
                "SEAAD_SPATIAL": Contribution.UNKNOWN,
                "GSE301119_PERTURBATION": Contribution.UNKNOWN,
                "GSE289721_PERTURBATION": Contribution.UNKNOWN},
            rna_contributed=Contribution.YES,
            atac_contributed=Contribution.NO,
            full104_contributed=Contribution.YES,
            stage75_member=False, used_for_development=True,
            exposure=ExposureState.DEVELOPMENT_EXPOSED,
            notes=("SEA-AD contributed to FULL104 target discovery, so a "
                   "SEA-AD result is INTERNAL_INDEPENDENT_MODALITY_SUPPORT, "
                   "never independent cohort confirmation.")))

    return L
