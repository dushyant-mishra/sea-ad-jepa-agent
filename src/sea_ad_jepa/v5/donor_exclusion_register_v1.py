"""Standing donor-exclusion register and enforcement guard.

Two owner directives, encoded so that code enforces them rather than a reader
remembering them. Both arose from authenticated provenance defects, not from
preference.

DIRECTIVE 1 — GSE214979 GEM lane 6 (HCT17HEX, HCTZZT)
    These two donors have SEX AND AGE TRANSPOSED between the GEO sample records
    and the series cell metadata, and their RNA and ATAC records disagree on
    brain region — impossible if the nuclei are the same. They are precisely the
    pair sharing pooled GEM lane 6, so a demultiplexing swap is the most
    parsimonious explanation. 10.41% of nuclei, 9.12% of microglia.

    RULE: exclude from any single-nucleus analysis in which donor demographics
    (sex, age, exact region) are PRIMARY MODEL COVARIATES. The directive is
    scoped: an analysis that does not condition on those covariates is not
    automatically invalidated, but it must say so explicitly.

DIRECTIVE 2 — potential Morabito / GSE214979 donor overlap (1224, 1230, 1238)
    GSE214979 draws these three from repository UCI; Morabito GSE174367 is a UC
    Irvine dataset with pseudonymised donors. No crosswalk exists in either
    deposit, so overlap can be neither confirmed nor excluded.

    RULE: either dataset may be used ALONE. Any claim resting on AGREEMENT
    between them must run a sensitivity analysis excluding these three, because
    unmodelled sample duplication inflates apparent cross-study consistency —
    the same donor agreeing with itself is not replication.

The register is data; `enforce_exclusions` is the part that binds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

# --------------------------------------------------------------------------
REGISTER: Mapping[str, Mapping] = {
    "GSE214979_GEM_LANE_6_IDENTITY_CONFLICT": {
        "dataset": "GSE214979",
        "donors": ("HCT17HEX", "HCTZZT"),
        "shared_unit": "pooled GEM lane 6",
        "defect": ("sex and age transposed between GEO sample records and series "
                   "cell metadata; RNA and ATAC disagree on brain region"),
        "affected_nuclei_fraction": 0.1041,
        "affected_microglia_fraction": 0.0912,
        "scope": "DEMOGRAPHIC_COVARIATE_ANALYSES",
        "trigger_covariates": ("sex", "age", "region", "brain_region", "age_at_death"),
        "action": "EXCLUDE",
        "resolution_requires": "a corrected donor-identity mapping from the depositor",
    },
    "GSE214979_MORABITO_POSSIBLE_OVERLAP": {
        "dataset": "GSE214979+GSE174367",
        "donors": ("1224", "1230", "1238"),
        "shared_unit": "repository UCI / UC Irvine",
        "defect": ("no donor crosswalk exists in either deposit; overlap can be "
                   "neither confirmed nor excluded"),
        "scope": "JOINT_OR_CROSS_STUDY_CLAIMS",
        "action": "SENSITIVITY_ANALYSIS_REQUIRED",
        "single_dataset_use": "PERMITTED without exclusion",
        "resolution_requires": "donor metadata neither deposit contains",
    },
}


class ExclusionViolation(Exception):
    """An analysis proceeded into a scope the register forbids."""


@dataclass(frozen=True)
class ExclusionDecision:
    rule_id: str
    triggered: bool
    excluded_donors: tuple[str, ...]
    reason: str
    requires_sensitivity_arm: bool = False


def _norm(d) -> str:
    return str(d).strip().upper().replace("-", "").replace("_", "")


def enforce_exclusions(donors: Iterable[str], *, covariates: Sequence[str] = (),
                       datasets: Sequence[str] = (),
                       joint_claim: bool = False,
                       sensitivity_arm_present: bool = False
                       ) -> list[ExclusionDecision]:
    """Apply both directives. Raises when a rule is violated rather than warning.

    `joint_claim` means the analysis rests on AGREEMENT between GSE214979 and
    Morabito. Using one alone is not a joint claim.
    """
    present = {_norm(d) for d in donors}
    decisions: list[ExclusionDecision] = []
    cov = {c.strip().lower() for c in covariates}

    r1 = REGISTER["GSE214979_GEM_LANE_6_IDENTITY_CONFLICT"]
    hit1 = tuple(d for d in r1["donors"] if _norm(d) in present)
    trig1 = bool(hit1) and bool(cov & set(r1["trigger_covariates"]))
    if trig1:
        raise ExclusionViolation(
            f"GEM lane 6 donors {hit1} are present while demographic covariates "
            f"{sorted(cov & set(r1['trigger_covariates']))} are in the model. Their sex "
            "and age are transposed between GEO and the series metadata. Exclude them "
            "or remove those covariates.")
    decisions.append(ExclusionDecision(
        "GSE214979_GEM_LANE_6_IDENTITY_CONFLICT", bool(hit1), hit1,
        "present but no demographic covariate in use" if hit1 and not trig1
        else ("absent" if not hit1 else "violation")))

    r2 = REGISTER["GSE214979_MORABITO_POSSIBLE_OVERLAP"]
    hit2 = tuple(d for d in r2["donors"] if _norm(d) in present)
    both = len({x for x in datasets if "214979" in x}) > 0 and \
           len({x for x in datasets if "174367" in x}) > 0
    if joint_claim and hit2 and not sensitivity_arm_present:
        raise ExclusionViolation(
            f"joint GSE214979/Morabito claim includes possibly-overlapping donors "
            f"{hit2} with no sensitivity arm excluding them. The same donor agreeing "
            "with itself is not cross-study replication.")
    decisions.append(ExclusionDecision(
        "GSE214979_MORABITO_POSSIBLE_OVERLAP", bool(hit2) and (joint_claim or both),
        hit2, "joint claim with sensitivity arm" if joint_claim and sensitivity_arm_present
        else ("single-dataset use, permitted" if not joint_claim else "absent"),
        requires_sensitivity_arm=bool(hit2) and joint_claim))
    return decisions


def excluded_for(scope: str) -> tuple[str, ...]:
    """Donors to drop for a given scope, for callers building a cohort."""
    out: list[str] = []
    for rule in REGISTER.values():
        if rule["scope"] == scope:
            out.extend(rule["donors"])
    return tuple(out)
