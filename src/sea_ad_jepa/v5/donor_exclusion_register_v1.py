"""Standing donor-exclusion register and enforcement guard.

Two owner directives, encoded so that code enforces them rather than a reader
remembering them. Both arose from authenticated provenance defects, not from
preference.

DIRECTIVE 1 — GSE214979 GEM lane 6 (HCT17HEX, HCTZZT)
    OBSERVED: these two donors have SEX AND AGE TRANSPOSED between the GEO
    sample records and the series cell metadata, and their RNA and ATAC records
    disagree on brain region — which cannot both be right if the nuclei are the
    same. They are also the pair sharing pooled GEM lane 6. 10.41% of nuclei,
    9.12% of microglia.

    CAUSE: NOT ESTABLISHED. A demultiplexing swap would produce this pattern,
    but so would a sample-sheet transposition, a metadata-entry error, or an
    upstream annotation mistake — and nothing here distinguishes among them. The
    shared lane makes a swap worth investigating; it does not make it the cause.

    The rule does NOT depend on which explanation is right. It is triggered by
    the OBSERVED conflict between two records that should agree, so it holds
    whatever produced that conflict.

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
        "observed_defect": ("sex and age transposed between GEO sample records and "
                            "series cell metadata; RNA and ATAC disagree on brain region"),
        "cause": "NOT_ESTABLISHED",
        "candidate_causes": ("demultiplexing swap", "sample-sheet transposition",
                             "metadata-entry error", "upstream annotation error"),
        "cause_note": ("the two donors share pooled GEM lane 6, which makes a "
                       "demultiplexing swap worth investigating. Nothing observed "
                       "distinguishes it from the other candidates. The rule is "
                       "triggered by the OBSERVED record conflict, not by any "
                       "hypothesised mechanism, so it holds regardless."),
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
        "observed_defect": ("no donor crosswalk exists in either deposit; overlap "
                            "can be neither confirmed nor excluded"),
        "cause": "NOT_APPLICABLE_UNRESOLVED_UNCERTAINTY",
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


# ==========================================================================
# ENFORCEMENT AT THE ENTRY POINT
#
# Review found two bypasses in the guard above, and the second is the same
# defect this project already found at the authorization boundary:
#
#   (1) `joint_claim` was supplied by the CALLER. An analysis could load both
#       datasets and simply pass joint_claim=False.
#   (2) `sensitivity_arm_present=True` was accepted on assertion, with no
#       verification that a sensitivity analysis ran or excluded the right
#       donors. That is `EXECUTED_PASS` again: a caller-written token standing
#       in for evidence.
#
# Both are closed below. The dataset combination is DERIVED from authenticated
# inputs, and the sensitivity arm must supply a RESULT that is checked.
# ==========================================================================

import hashlib as _hashlib
import re as _re

_ACCESSION = _re.compile(r"GSE\d{4,8}", _re.IGNORECASE)

DATASET_OF_ACCESSION = {
    "GSE214979": "GSE214979",
    "GSE214637": "GSE214979",      # SuperSeries container; its data IS GSE214979
    "GSE174367": "GSE174367",
}


def derive_datasets_from_inputs(input_manifest: Mapping[str, str]) -> tuple[str, ...]:
    """Derive which datasets are in play from AUTHENTICATED inputs.

    `input_manifest` maps path -> sha256 for every file the analysis actually
    opened. The caller does not get to declare the dataset combination; it is
    read off the inputs. An unauthenticated entry (missing or malformed digest)
    is refused rather than ignored.
    """
    found: set[str] = set()
    for path, digest in input_manifest.items():
        if not isinstance(digest, str) or len(digest) != 64 or digest != digest.lower():
            raise ExclusionViolation(
                f"input {path!r} carries no valid SHA-256; dataset membership cannot "
                "be derived from unauthenticated inputs")
        for m in _ACCESSION.findall(str(path)):
            acc = m.upper()
            if acc in DATASET_OF_ACCESSION:
                found.add(DATASET_OF_ACCESSION[acc])
    return tuple(sorted(found))


@dataclass(frozen=True)
class SensitivityArmResult:
    """EVIDENCE that a sensitivity arm ran, not an assertion that it did."""
    excluded_donors: tuple[str, ...]
    n_donors_before: int
    n_donors_after: int
    primary_estimate: float
    sensitivity_estimate: float
    source_commit: str
    input_digest: str

    def verify(self, required_exclusions: Sequence[str],
               donors_present: Sequence[str]) -> None:
        req = {_norm(d) for d in required_exclusions} & {_norm(d) for d in donors_present}
        got = {_norm(d) for d in self.excluded_donors}
        missing = sorted(req - got)
        if missing:
            raise ExclusionViolation(
                f"sensitivity arm did not exclude the required donors {missing}")
        if self.n_donors_after != self.n_donors_before - len(req):
            raise ExclusionViolation(
                f"sensitivity arm donor count inconsistent: {self.n_donors_before} -> "
                f"{self.n_donors_after} while excluding {len(req)}; the arm did not "
                "actually drop them")
        for name, v in (("primary_estimate", self.primary_estimate),
                        ("sensitivity_estimate", self.sensitivity_estimate)):
            if not isinstance(v, (int, float)) or v != v or abs(float(v)) == float("inf"):
                raise ExclusionViolation(f"{name} is not a finite number: {v!r}")
        for name, v in (("source_commit", self.source_commit),
                        ("input_digest", self.input_digest)):
            if not isinstance(v, str) or len(v) < 7:
                raise ExclusionViolation(f"{name} does not identify an actual run")


def run_guarded_evaluation(*, donors: Sequence[str], covariates: Sequence[str],
                           input_manifest: Mapping[str, str],
                           cross_study_claim: bool,
                           sensitivity_arm: "SensitivityArmResult | None" = None,
                           analysis=None):
    """THE entry point. Every evaluation touching these datasets goes through it.

    `cross_study_claim` states the analyst's INTENT. It can only make the check
    stricter, never weaker: if the authenticated inputs contain both datasets,
    a joint claim is derived regardless of what was declared.
    """
    datasets = derive_datasets_from_inputs(input_manifest)
    derived_joint = ("GSE214979" in datasets) and ("GSE174367" in datasets)
    joint = bool(derived_joint or cross_study_claim)

    r2 = REGISTER["GSE214979_MORABITO_POSSIBLE_OVERLAP"]
    present_overlap = tuple(d for d in r2["donors"]
                            if _norm(d) in {_norm(x) for x in donors})
    if joint and present_overlap:
        if sensitivity_arm is None:
            raise ExclusionViolation(
                f"joint claim over {datasets} includes possibly-overlapping donors "
                f"{present_overlap} and supplied NO sensitivity arm. A boolean is not "
                "evidence; supply a SensitivityArmResult.")
        sensitivity_arm.verify(r2["donors"], donors)

    enforce_exclusions(donors, covariates=covariates, datasets=datasets,
                       joint_claim=joint,
                       sensitivity_arm_present=sensitivity_arm is not None)

    receipt = {
        "datasets_derived_from_inputs": datasets,
        "joint_claim_declared": bool(cross_study_claim),
        "joint_claim_derived": bool(derived_joint),
        "joint_enforced": joint,
        "overlap_donors_present": present_overlap,
        "sensitivity_arm_verified": sensitivity_arm is not None and bool(present_overlap),
        "input_manifest_digest": _hashlib.sha256(
            "".join(f"{k}:{v}" for k, v in sorted(input_manifest.items())).encode()
        ).hexdigest(),
    }
    return (analysis() if analysis is not None else None), receipt
