"""T0 input dependency contract, derived from the executable T0 consumers.

Why this module exists
----------------------
The T0 input contract was incomplete, and the incompleteness was found late. The
frozen V18/V20 adjudicator requires a donor-level `IMMUNE_FRACTION` column that
exists in no input file anywhere in the project, and requires a `technical_complete`
boolean that has no definition anywhere in the frozen package. Both were discovered
only after substantial input-materialization machinery had already been built
against an input list that had never been checked against the code that consumes it.

A prose contract would repeat that failure, because prose cannot notice a consumer
growing a new required column. So this contract is executable in both directions:

  forward   every quantity declared here must actually be referenced by the
            consumer module it is declared against;
  reverse   every donor-level quantity referenced by any consumer module must be
            declared here.

The reverse direction is the one that matters. It is the guard that turns "we
forgot an input" from a discovery made late into a test failure made immediately.

What this module is NOT
-----------------------
It declares dependencies, classifications and ordering. It computes no donor-level
quantity, reads no pathology value, and authorizes nothing.

`technical_complete` was an open specification slot here until the project owner
resolved it on 2026-09-08 as a THRESHOLD-FREE definedness and computability
predicate: it asks whether the frozen technical summaries are mathematically
defined on a lawfully authenticated substrate, and it carries no depth cutoff, no
detection cutoff and no newly invented cells-per-donor floor. The frozen 80-cell
threshold remains tail measurability only. `assert_technical_completeness_is_threshold_free`
guards that decision against later drift, because a plausible-sounding quality
floor added afterwards would quietly convert eligibility into a post-hoc donor
filter with no frozen threshold to appeal to.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA = "JEPA_T0_INPUT_DEPENDENCY_CONTRACT_V1"
NAMESPACE = "T0-INPUT-DEPENDENCY-V1"

STOP_UNDECLARED = "STOP_T0_INPUT_CONTRACT_UNDECLARED_DONOR_QUANTITY"
STOP_NOT_CONSUMED = "STOP_T0_INPUT_CONTRACT_DECLARED_QUANTITY_NOT_CONSUMED"
STOP_UNKNOWN_CLASS = "STOP_T0_INPUT_CONTRACT_UNKNOWN_CLASSIFICATION"
STOP_UNKNOWN_DEP = "STOP_T0_INPUT_CONTRACT_DEPENDENCY_NOT_DECLARED"
STOP_CYCLE = "STOP_T0_INPUT_CONTRACT_DEPENDENCY_CYCLE"
STOP_ORDER = "STOP_T0_INPUT_CONTRACT_STAGE_ORDER_VIOLATION"
STOP_PATHOLOGY = "STOP_T0_INPUT_CONTRACT_PATHOLOGY_CLASS_VIOLATION"
STOP_CONSUMER_ABSENT = "STOP_T0_INPUT_CONTRACT_CONSUMER_SOURCE_ABSENT"
STOP_FIELD_SCHEMA = "STOP_T0_INPUT_CONTRACT_FIELD_SCHEMA_VIOLATION"
STOP_THRESHOLD_INTRODUCED = "STOP_T0_INPUT_CONTRACT_TECHNICAL_COMPLETENESS_THRESHOLD_INTRODUCED"
STOP_DESIGN_NOT_EXECUTABLE = "STOP_T0_DESIGN_NOT_EXECUTABLE_UNDER_FROZEN_ELIGIBILITY"

# --- technical completeness, frozen by owner decision 2026-09-08 ------------
# Resolved as a THRESHOLD-FREE DEFINEDNESS/COMPUTABILITY predicate. It is not a
# biological-quality filter, not a depth cutoff, not a detection cutoff, and it
# may not remove a donor merely because that donor's data are "low quality".
# The frozen package contains no such thresholds, so inventing one now would
# violate the freeze discipline.
TECHNICAL_COMPLETENESS_SEMANTICS = "THRESHOLD_FREE_DEFINEDNESS_AND_COMPUTABILITY"

TECHNICAL_COMPLETENESS_CONJUNCTS: tuple[str, ...] = (
    "donor belongs to the accepted op31 candidate donor universe",
    "donor has at least one authenticated accepted cell",
    "the donor's accepted cells close correctly through the authenticated B2 substrate",
    "the required raw-count and source_library information is valid enough to "
    "compute the frozen technical summaries",
    "Q_DEPTH(donor) is computable and finite",
    "Q_DETECT(donor) is computable, finite, and within its lawful range",
)

# Cutoffs that must NEVER appear in the technical-completeness predicate. Listed
# so the prohibition is checkable rather than merely stated.
TECHNICAL_COMPLETENESS_FORBIDDEN_CUTOFFS: tuple[str, ...] = (
    "Q_DEPTH_MINIMUM",
    "Q_DETECT_MINIMUM",
    "CELLS_PER_DONOR_QC_FLOOR",
    "TAIL_MIN_CELLS_AS_ELIGIBILITY",
)

# The frozen 80-cell floor governs TAIL MEASURABILITY ONLY. The frozen role code
# says so in terms: tail measurability "must not influence the parent-state
# donor roles". It therefore may not enter technical_complete either.
TAIL_FLOOR_SCOPE = "TAIL_MEASURABILITY_ONLY__NEVER_ELIGIBILITY_OR_PARENT_ROLE"

# Reconciles the frozen V18 wording without rewriting V18 science.
V18_METADATA_ONLY_INTERPRETATION = (
    "Technical completeness is pathology-blind pre-outcome eligibility metadata "
    "derived deterministically from authenticated expression technical summaries. "
    "'Metadata-only' in V18 SS201 means no pathology magnitude and no "
    "discovery/confirmation outcome information is used; it does not mean the flag "
    "must originate as a literal column in a source metadata file."
)

# Fail-closed rule. Without this, eligibility becomes a loophole for dropping
# inconvenient donors: a provenance failure would silently reappear as a donor
# who is merely "technically incomplete".
AUTHORITY_FAILURE_IS_NOT_INCOMPLETENESS = (
    "technical_complete is evaluated ONLY on a lawfully authenticated substrate. "
    "A wrong source digest, a missing accepted membership cell, a donor/cell "
    "identity mismatch, a wrong source row, a wrong materialized row, a counts "
    "digest failure or a manifest inconsistency are B2 STOPs. They are never "
    "reasons to mark a donor technically incomplete. The predicate answers "
    "'are the required technical summaries defined?', not 'did provenance "
    "validation fail?'."
)

# If frozen eligibility leaves too few donors for the frozen design, that is a
# STOP. It is never an invitation to find a different cutoff.
ELIGIBILITY_SHORTFALL_RULE = (
    "If the frozen eligible universe falls below 18 CONFIRMATION + 18 minimum "
    "DISCOVERY donors, raise %s. Do not relax eligibility, do not introduce a "
    "cutoff, and do not alter the split." % STOP_DESIGN_NOT_EXECUTABLE
)

# Likewise for a degenerate design matrix on the actual deterministic split.
SINGLE_SEX_RULE = (
    "If the actual deterministic confirmation set is single-sex, nuisance_design "
    "refuses it and the role authority must fail loudly. This is a design "
    "failure, not a biological NOT_MEASURABLE, and the split must not be altered "
    "to rescue it."
)

# --- classifications, in dependency order -----------------------------------
# The index of a classification in this tuple is its stage. A quantity may only
# depend on quantities of the same or an earlier stage, which is what makes the
# graph checkable rather than merely drawn.
CLASSIFICATIONS: tuple[str, ...] = (
    "FROZEN_SOURCE_FIELD",          # read from a frozen source asset
    "AUTHENTICATED_EXPRESSION",     # per-cell, established by B2 authentication
    "DERIVED",                      # computed from authenticated expression
    "ELIGIBILITY",                  # defines the statistical population
    "ROLE_DEPENDENT",               # requires the frozen eligible set
    "DISCOVERY_ONLY",               # may only be computed on DISCOVERY donors
    "CONFIRMATION_ONLY",            # may only be computed on CONFIRMATION donors
)

PATHOLOGY_CLASSES: tuple[str, ...] = (
    "PATHOLOGY_VALUE",              # a numeric pathology measurement; gated
    "AVAILABILITY_PREDICATE",       # derived from pathology bytes, value-blind
    "PATHOLOGY_BLIND",              # no pathology dependence at all
)

DONOR_SCOPES: tuple[str, ...] = (
    "ALL_CANDIDATE_DONORS",         # the 46 candidates
    "ELIGIBLE_DONORS",              # after eligibility is frozen
    "DISCOVERY_DONORS",
    "CONFIRMATION_DONORS",
)

_REQUIRED_FIELDS = (
    "name", "classification", "pathology_class", "donor_scope",
    "authority", "depends_on", "consumed_by", "definition",
)


def _entry(
    name: str,
    classification: str,
    pathology_class: str,
    donor_scope: str,
    authority: str,
    depends_on: Sequence[str],
    consumed_by: Sequence[str],
    definition: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "classification": classification,
        "pathology_class": pathology_class,
        "donor_scope": donor_scope,
        "authority": authority,
        "depends_on": tuple(depends_on),
        "consumed_by": tuple(consumed_by),
        "definition": definition,
    }


# --- the contract -----------------------------------------------------------
# Every entry below was read off the consumer source, not off a handoff document.
# `consumed_by` names the module that requires the quantity; the forward check
# asserts the name really appears there.

CONTRACT: tuple[dict[str, Any], ...] = (
    # ---- frozen source fields
    _entry(
        "age", "FROZEN_SOURCE_FIELD", "PATHOLOGY_BLIND", "ALL_CANDIDATE_DONORS",
        "T0_DONOR_METADATA_AUTHORITY__PENDING",
        (),
        ("t0_donor_role_authority_v2", "t0_adjudicator_v1", "t0_discovery_fit_v2",
         "t0_execution_input_authority_v1"),
        "Frozen source column 'Age at Death'. Enters the nuisance design as a "
        "centred linear and quadratic term.",
    ),
    _entry(
        "sex", "FROZEN_SOURCE_FIELD", "PATHOLOGY_BLIND", "ALL_CANDIDATE_DONORS",
        "T0_DONOR_METADATA_AUTHORITY__PENDING",
        (),
        ("t0_donor_role_authority_v2", "t0_adjudicator_v1", "t0_discovery_fit_v2",
         "t0_execution_input_authority_v1"),
        "Frozen source column 'Sex'. Encoded to binary 0/1; nuisance_design "
        "refuses any set that is not complete binary, so a single-sex donor set "
        "is a hard build-time failure rather than a silent degeneracy.",
    ),
    _entry(
        "AT8", "FROZEN_SOURCE_FIELD", "PATHOLOGY_VALUE", "ELIGIBLE_DONORS",
        "GATED__REAL_T0_UNAUTHORIZED",
        (),
        ("t0_adjudicator_v1", "t0_discovery_fit_v2", "t0_discovery_provenance_v1",
         "t0_execution_input_authority_v1"),
        "Frozen source column 'percent AT8 positive area_Grey matter'. The "
        "response. No lane below real T0 execution may read this value.",
    ),

    # ---- availability predicate
    _entry(
        "AT8_available", "FROZEN_SOURCE_FIELD", "AVAILABILITY_PREDICATE",
        "ALL_CANDIDATE_DONORS",
        "T0_AT8_AVAILABILITY_AUTHORITY_V1",
        (),
        ("t0_donor_role_authority_v2", "t0_execution_input_authority_v1"),
        "Presence-and-non-missingness of the AT8 field after stripping and "
        "case-folding against the frozen missingness vocabulary. A measured zero "
        "is available. Value-blind by construction.",
    ),

    # ---- authenticated expression, per cell
    _entry(
        "donor_id", "AUTHENTICATED_EXPRESSION", "PATHOLOGY_BLIND",
        "ALL_CANDIDATE_DONORS",
        "T0_V20_ROW_COUNT_AUTHORITY_V1",
        (),
        ("t0_confirmation_raw_v1", "t0_donor_role_authority_v2", "t0_adjudicator_v1"),
        "Donor identity. Must agree between the accepted immune membership and "
        "the Phase2 block metadata; disagreement is a STOP.",
    ),
    _entry(
        "canonical_cell_id", "AUTHENTICATED_EXPRESSION", "PATHOLOGY_BLIND",
        "ALL_CANDIDATE_DONORS",
        "T0_V20_ROW_COUNT_AUTHORITY_V1",
        (),
        ("t0_v20_row_count_authority_v1",),
        "Cell identity, unique across the population closure.",
    ),
    _entry(
        "expression_row", "AUTHENTICATED_EXPRESSION", "PATHOLOGY_BLIND",
        "ALL_CANDIDATE_DONORS",
        "T0_V20_ROW_COUNT_AUTHORITY_V1",
        (),
        ("t0_v20_row_count_authority_v1",),
        "Row coordinate in the ORIGINAL H5 source matrix. Distinct from "
        "row_index; conflating the two is a row-selection defect.",
    ),
    _entry(
        "row_index", "AUTHENTICATED_EXPRESSION", "PATHOLOGY_BLIND",
        "ALL_CANDIDATE_DONORS",
        "T0_V20_ROW_COUNT_AUTHORITY_V1",
        (),
        ("t0_v20_row_count_authority_v1",),
        "Row coordinate WITHIN the materialized block-*.counts.npz payload. "
        "Distinct from expression_row.",
    ),
    _entry(
        "source_library", "AUTHENTICATED_EXPRESSION", "PATHOLOGY_BLIND",
        "ALL_CANDIDATE_DONORS",
        "T0_V20_ROW_COUNT_AUTHORITY_V1",
        (),
        ("t0_confirmation_raw_v1", "t0_v20_row_count_authority_v1"),
        "Integer sum of the FULL raw source row, computed before source-to-address "
        "projection. Never recomputable from the 41,238-address row or the 35,076 "
        "projection. Required strictly positive by the confirmation reader.",
    ),
    _entry(
        "stable_key", "AUTHENTICATED_EXPRESSION", "PATHOLOGY_BLIND",
        "ALL_CANDIDATE_DONORS",
        "T0_PRIMARY_MEMBERSHIP_SOURCE_AUTHORITY_V1",
        (),
        ("t0_confirmation_raw_v1",),
        "Exact integer cell key. Fixes within-donor cell ordering.",
    ),

    # ---- derived, pathology-blind
    _entry(
        "cells", "DERIVED", "PATHOLOGY_BLIND", "ALL_CANDIDATE_DONORS",
        "T0_IMMUNE_SUPPORT_COUNT_AUTHORITY_V1__PENDING",
        ("donor_id",),
        ("t0_donor_role_authority_v2", "t0_discovery_confirmation_split_v2",
         "t0_confirmation_raw_v1"),
        "Per-donor count of accepted IMMUNE support cells: 46 donors summing to "
        "exactly 20,804. This is the IMMUNE membership count, NOT the 638,150 "
        "all-op31 count -- the frozen 80-cell tail flag is evaluated against it, "
        "and against the all-op31 count every donor would clear the floor "
        "trivially. It deserves its own authority rather than being handed to the "
        "role builder as an informal frame. Gates tail measurability only; it does "
        "NOT influence parent-state donor roles.",
    ),
    _entry(
        "Q_DEPTH", "DERIVED", "PATHOLOGY_BLIND", "ALL_CANDIDATE_DONORS",
        "T0_TECHNICAL_COMPLETENESS_AUTHORITY_V1__PENDING",
        ("source_library", "donor_id"),
        ("t0_confirmation_raw_v1", "t0_adjudicator_v1"),
        "Donor mean of log1p(source_library) over that donor's authenticated "
        "cells. Recovered exactly from t0_confirmation_raw_v1, not inferred.",
    ),
    _entry(
        "Q_DETECT", "DERIVED", "PATHOLOGY_BLIND", "ALL_CANDIDATE_DONORS",
        "T0_TECHNICAL_COMPLETENESS_AUTHORITY_V1__PENDING",
        ("donor_id",),
        ("t0_confirmation_raw_v1", "t0_adjudicator_v1"),
        "Donor mean of (nonzero addresses / 35,076) over that donor's cells. "
        "Defined on ALL 35,076 scalar-measured addresses, not the 28,061 SCORING "
        "subset, so it depends on the B1 projection and not on raw rows alone. "
        "Recovered exactly from t0_confirmation_raw_v1, not inferred.",
    ),
    _entry(
        "IMMUNE_FRACTION", "DERIVED", "PATHOLOGY_BLIND", "ALL_CANDIDATE_DONORS",
        "T0_IMMUNE_FRACTION_AUTHORITY_V1__PENDING",
        ("donor_id",),
        ("t0_adjudicator_v1", "t0_execution_input_authority_v1"),
        "immune_n_donor / total_op31_n_donor, as exact integers over a common "
        "donor. Numerator from the accepted immune membership; denominator from "
        "the internally selected operator-31 subset of the frozen complete "
        "Phase2 manifest. Exists in NO input file; it must be derived. Consumed "
        "by the confirmation composition sensitivity only.",
    ),

    # ---- eligibility
    _entry(
        "technical_complete", "ELIGIBILITY", "PATHOLOGY_BLIND",
        "ALL_CANDIDATE_DONORS",
        "T0_TECHNICAL_COMPLETENESS_AUTHORITY_V1__PENDING",
        ("Q_DEPTH", "Q_DETECT", "source_library", "cells"),
        ("t0_donor_role_authority_v2", "t0_execution_input_authority_v1"),
        "Threshold-free definedness and computability predicate, frozen by owner "
        "decision on 2026-09-08. TRUE iff the donor is in the accepted op31 "
        "candidate universe, has at least one authenticated accepted cell, those "
        "cells close correctly through the authenticated B2 substrate, the raw-count "
        "and source_library information suffices to compute the frozen technical "
        "summaries, and Q_DEPTH and Q_DETECT are both computable and finite with "
        "Q_DETECT in its lawful range. It carries NO cutoffs: no Q_DEPTH minimum, "
        "no Q_DETECT minimum, and no newly invented cells-per-donor floor. The "
        "frozen 80-cell threshold is tail measurability only and never enters here. "
        "The dependency on `cells` is the at-least-one-cell existence check, not a "
        "floor. Authority failures are B2 STOPs and never appear as technical "
        "incompleteness.",
    ),
    _entry(
        "eligible", "ELIGIBILITY", "AVAILABILITY_PREDICATE", "ALL_CANDIDATE_DONORS",
        "T0_ELIGIBLE_DONOR_AUTHORITY_V1__PENDING",
        ("AT8_available", "technical_complete", "age", "sex"),
        ("t0_donor_role_authority_v2",),
        "AT8_available & technical_complete & isfinite(age) & sex non-empty. This "
        "is the statistical population, not an end-stage gate. Read verbatim off "
        "t0_donor_role_authority_v2. Each conjunct is a separate authority: B2 "
        "establishes technical definedness and has NO authority over AT8 "
        "availability, age or sex, so B2 does not and may not declare eligibility. "
        "Below 18 CONFIRMATION + 18 minimum DISCOVERY donors this is a design STOP, "
        "never an invitation to relax a conjunct.",
    ),

    # ---- role dependent
    _entry(
        "split_hash", "ROLE_DEPENDENT", "PATHOLOGY_BLIND", "ELIGIBLE_DONORS",
        "T0_DONOR_ROLE_AUTHORITY_V2__GATE_SHUT",
        ("donor_id",),
        ("t0_donor_role_authority_v2", "t0_discovery_confirmation_split_v2"),
        "sha256('T0-DISCOVERY-CONFIRM-V2|' + donor_id). Deterministic and "
        "outcome-independent.",
    ),
    _entry(
        "donor_role", "ROLE_DEPENDENT", "PATHOLOGY_BLIND", "ELIGIBLE_DONORS",
        "T0_DONOR_ROLE_AUTHORITY_V2__GATE_SHUT",
        ("eligible", "split_hash"),
        ("t0_donor_role_authority_v2",),
        "Eligible donors ordered by (split_hash, donor_id); the first 18 are "
        "CONFIRMATION and the remainder DISCOVERY. Deterministic once the eligible "
        "set is frozen, so after eligibility there is nothing probabilistic left "
        "to discuss: the split is computed and its design matrix tested.",
    ),
    _entry(
        "tail_measurable", "ROLE_DEPENDENT", "PATHOLOGY_BLIND", "ELIGIBLE_DONORS",
        "T0_DONOR_ROLE_AUTHORITY_V2__GATE_SHUT",
        ("cells",),
        ("t0_donor_role_authority_v2", "t0_discovery_confirmation_split_v2"),
        "cells >= 80. An outcome of the split, never an input to it.",
    ),

    # ---- discovery only
    _entry(
        "STATE_SCORE", "CONFIRMATION_ONLY", "PATHOLOGY_BLIND", "CONFIRMATION_DONORS",
        "T0_TARGET_SERIALIZER_V2__DOWNSTREAM",
        ("donor_role", "source_library"),
        ("t0_confirmation_raw_v1", "t0_adjudicator_v1"),
        "Donor mean of the frozen discovery-derived cell score. The scoring object "
        "must be frozen on DISCOVERY donors before any confirmation donor is "
        "scored with it.",
    ),
    _entry(
        "TAIL_MEASURABLE", "CONFIRMATION_ONLY", "PATHOLOGY_BLIND", "CONFIRMATION_DONORS",
        "T0_TAIL_AUTHORITY_V1__DOWNSTREAM",
        ("cells", "donor_role"),
        ("t0_confirmation_raw_v1",),
        "Whether this confirmation donor clears the 80-cell tail floor.",
    ),
    _entry(
        "TAIL_PREVALENCE", "CONFIRMATION_ONLY", "PATHOLOGY_BLIND", "CONFIRMATION_DONORS",
        "T0_TAIL_AUTHORITY_V1__DOWNSTREAM",
        ("STATE_SCORE", "TAIL_MEASURABLE"),
        ("t0_confirmation_raw_v1", "t0_adjudicator_v1"),
        "Fraction of the donor's cells whose centred score exceeds the frozen "
        "discovery-derived tail threshold.",
    ),
    _entry(
        "tail_cells", "CONFIRMATION_ONLY", "PATHOLOGY_BLIND", "CONFIRMATION_DONORS",
        "T0_TAIL_AUTHORITY_V1__DOWNSTREAM",
        ("TAIL_PREVALENCE",),
        ("t0_confirmation_raw_v1",),
        "Absolute count of tail cells; audit companion to TAIL_PREVALENCE.",
    ),
    _entry(
        "rest_cells", "CONFIRMATION_ONLY", "PATHOLOGY_BLIND", "CONFIRMATION_DONORS",
        "T0_TAIL_AUTHORITY_V1__DOWNSTREAM",
        ("TAIL_PREVALENCE",),
        ("t0_confirmation_raw_v1",),
        "Absolute count of non-tail cells; audit companion to TAIL_PREVALENCE.",
    ),
)

# Names that appear in consumer sources as donor-level quantities but are aliases
# or local encodings of a declared quantity rather than quantities in their own
# right. Declared explicitly so the reverse check stays honest instead of being
# quietly loosened.
ALIASES: Mapping[str, str] = {
    "sex_code": "sex",            # encode_binary_utf8(sex)
    "local_row": "row_index",     # Phase2 producer's name for the block-local row
    "AT8_field": "AT8",
    # t0_donor_role_authority_v2 computes the eligibility predicate into a local
    # named `complete`. The contract calls it `eligible`, because "complete"
    # describes the metadata fields while the predicate defines the statistical
    # population. Recorded rather than renamed: the frozen module is not ours
    # to rewrite.
    "complete": "eligible",
    # The role registry column is `role`; the contract name is `donor_role` to
    # keep it unambiguous in a graph that also has feature roles.
    "role": "donor_role",
}

# The consumer modules the reverse check scans. Every module here must exist in
# one of the supplied source roots. They span two roots deliberately: the frozen
# V20 package code, and the materialization modules on this branch.
CONSUMER_MODULES: tuple[str, ...] = (
    "t0_adjudicator_v1",
    "t0_confirmation_raw_v1",
    "t0_discovery_confirmation_split_v2",
    "t0_discovery_fit_v2",
    "t0_discovery_provenance_v1",
    "t0_donor_role_authority_v2",
    "t0_execution_input_authority_v1",
    "t0_tail_authority_v1",
    "t0_v20_row_count_authority_v1",
    "t0_v20_feature_projection_authority_v1",
)

# Names that appear inside consumer column-set literals but select a SOURCE or an
# OPERATOR rather than describing a donor. Declared here, in the contract, rather
# than accepted through a caller-supplied parameter: a caller-supplied allowlist
# is a way to silence exactly the finding this scan exists to raise.
NON_DONOR_SELECTORS: frozenset[str] = frozenset({
    "source",                    # dataset source, e.g. SEA_AD
    "operator_index",            # operator partition, 31 for MTG
    "matrix_id",                 # frozen matrix identity
    "molecular_address_index",   # feature-space coordinates, not donor-level
    "molecular_address_id",
    "symbol",
    "biotype",
})

# The stage ordering the architecture asserts, as an explicit sequence of gates.
#
# Two orderings here are load-bearing and were both learned the hard way.
# FEASIBILITY_A precedes B2 because it is metadata-only and cheap, and running it
# late is what let an undeclared required input survive until after the
# materialization machinery was built. And ELIGIBLE_DONOR_AUTHORITY is a stage of
# its own, separate from B2: B2 establishes technical definedness and holds no
# authority over AT8 availability, age or sex, so it must not declare eligibility.
STAGE_ORDER: tuple[str, ...] = (
    "FROZEN_OBSERVATIONAL_SOURCES",
    "ACCEPTED_CANDIDATE_DONOR_UNIVERSE",
    "FEASIBILITY_A__CANDIDATE_UNIVERSE_METADATA_ONLY",
    "B2_EXPRESSION_SUBSTRATE_AUTHENTICATION",
    "DERIVED_DONOR_QUANTITIES",
    "TECHNICAL_COMPLETENESS_AUTHORITY",
    "ELIGIBLE_DONOR_AUTHORITY",
    "DETERMINISTIC_V18_SPLIT",
    "FEASIBILITY_B__EXACT_ELIGIBLE_AND_ROLES_ESTIMABILITY",
    "ROLE_SCOPED_MATRICES",
    "DISCOVERY_FIT_AND_FREEZE",
    "CONFIRMATION_UNLOCK_AND_TEST",
    "T0_DECISION",
)


def contract_index() -> dict[str, dict[str, Any]]:
    """The contract keyed by name, with duplicate names refused."""
    index: dict[str, dict[str, Any]] = {}
    for entry in CONTRACT:
        name = entry["name"]
        if name in index:
            raise AssertionError("%s: %r declared twice" % (STOP_FIELD_SCHEMA, name))
        index[name] = entry
    return index


def assert_contract_wellformed() -> bool:
    """Field schema, classification vocabulary, dependency closure, stage order."""
    index = contract_index()
    for entry in CONTRACT:
        if tuple(sorted(entry)) != tuple(sorted(_REQUIRED_FIELDS)):
            raise AssertionError("%s: %r has fields %r"
                                 % (STOP_FIELD_SCHEMA, entry["name"],
                                    tuple(sorted(entry))))
        if entry["classification"] not in CLASSIFICATIONS:
            raise AssertionError("%s: %r has classification %r"
                                 % (STOP_UNKNOWN_CLASS, entry["name"],
                                    entry["classification"]))
        if entry["pathology_class"] not in PATHOLOGY_CLASSES:
            raise AssertionError("%s: %r has pathology class %r"
                                 % (STOP_PATHOLOGY, entry["name"],
                                    entry["pathology_class"]))
        if entry["donor_scope"] not in DONOR_SCOPES:
            raise AssertionError("%s: %r has donor scope %r"
                                 % (STOP_FIELD_SCHEMA, entry["name"],
                                    entry["donor_scope"]))
        if not isinstance(entry["authority"], str) or not entry["authority"]:
            raise AssertionError("%s: %r has no authority"
                                 % (STOP_FIELD_SCHEMA, entry["name"]))
        if not isinstance(entry["definition"], str) or len(entry["definition"]) < 16:
            raise AssertionError("%s: %r has no usable definition"
                                 % (STOP_FIELD_SCHEMA, entry["name"]))

    # Dependency closure and stage monotonicity in one pass.
    for entry in CONTRACT:
        own = CLASSIFICATIONS.index(entry["classification"])
        for dep in entry["depends_on"]:
            if dep not in index:
                raise AssertionError("%s: %r depends on undeclared %r"
                                     % (STOP_UNKNOWN_DEP, entry["name"], dep))
            other = CLASSIFICATIONS.index(index[dep]["classification"])
            if other > own:
                raise AssertionError(
                    "%s: %r (%s) depends on %r (%s), which is a later stage"
                    % (STOP_ORDER, entry["name"], entry["classification"],
                       dep, index[dep]["classification"]))

    # A same-stage dependency could still cycle, so check that separately.
    _assert_acyclic(index)

    # A pathology-blind quantity may not depend on a pathology value.
    for entry in CONTRACT:
        if entry["pathology_class"] != "PATHOLOGY_BLIND":
            continue
        for dep in entry["depends_on"]:
            if index[dep]["pathology_class"] == "PATHOLOGY_VALUE":
                raise AssertionError(
                    "%s: %r is declared pathology-blind but depends on the "
                    "pathology value %r" % (STOP_PATHOLOGY, entry["name"], dep))
    return True


def _assert_acyclic(index: Mapping[str, dict[str, Any]]) -> None:
    state: dict[str, int] = {}

    def visit(name: str, path: tuple[str, ...]) -> None:
        mark = state.get(name, 0)
        if mark == 1:
            raise AssertionError("%s: %s" % (STOP_CYCLE, " -> ".join(path + (name,))))
        if mark == 2:
            return
        state[name] = 1
        for dep in index[name]["depends_on"]:
            visit(dep, path + (name,))
        state[name] = 2

    for name in index:
        visit(name, ())


_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _as_roots(code_dirs: Path | str | Sequence[Path | str]) -> tuple[Path, ...]:
    if isinstance(code_dirs, (str, Path)):
        return (Path(code_dirs),)
    roots = tuple(Path(d) for d in code_dirs)
    if not roots:
        raise AssertionError("%s: no source root supplied" % STOP_CONSUMER_ABSENT)
    return roots


def _consumer_source(roots: Sequence[Path], module: str) -> str:
    """Resolve a consumer module across the supplied roots.

    Absence is a STOP rather than a skip. A verification that quietly passes
    because it could not find the code it was meant to read is worse than no
    verification, because it reports success.
    """
    for root in roots:
        path = Path(root) / ("%s.py" % module)
        if path.is_file():
            return path.read_text(encoding="utf-8")
    raise AssertionError("%s: %s.py not found under %s"
                         % (STOP_CONSUMER_ABSENT, module,
                            ", ".join(str(r) for r in roots)))


def collect_consumer_sources(
        code_dirs: Path | str | Sequence[Path | str]) -> dict[str, str]:
    """Read every consumer module's text from the supplied roots."""
    roots = _as_roots(code_dirs)
    return {m: _consumer_source(roots, m) for m in CONSUMER_MODULES}


def _as_sources(
        code_dirs_or_sources: Path | str | Sequence[Path | str] | Mapping[str, str],
) -> dict[str, str]:
    """Accept either source roots on disk or an explicit module->text mapping.

    The mapping form exists so the regression suite can run against committed
    fixture bytes on any machine, instead of resolving a local package path and
    skipping when it is absent. A check that skips is not a check that ran.
    """
    if isinstance(code_dirs_or_sources, Mapping):
        sources = dict(code_dirs_or_sources)
        missing = [m for m in CONSUMER_MODULES if m not in sources]
        if missing:
            raise AssertionError("%s: no source supplied for %s"
                                 % (STOP_CONSUMER_ABSENT, ", ".join(missing)))
        for module, text in sources.items():
            if not isinstance(text, str) or not text:
                raise AssertionError("%s: %s source is empty"
                                     % (STOP_CONSUMER_ABSENT, module))
        return sources
    return collect_consumer_sources(code_dirs_or_sources)


def consumer_source_digests(
        code_dirs: Path | str | Sequence[Path | str]) -> dict[str, str]:
    """Digest of every consumer source the checks were run against.

    Binding these makes a later silent drift in a consumer visible: the contract
    was verified against specific bytes, and those bytes are named.
    """
    roots = _as_roots(code_dirs)
    return {m: hashlib.sha256(_consumer_source(roots, m).encode("utf-8")).hexdigest()
            for m in CONSUMER_MODULES}


def assert_declared_quantities_are_consumed(
        code_dirs_or_sources: Path | str | Sequence[Path | str] | Mapping[str, str],
) -> bool:
    """Forward direction: each declared quantity appears in its declared consumer."""
    sources = _as_sources(code_dirs_or_sources)
    for entry in CONTRACT:
        for module in entry["consumed_by"]:
            text = sources.get(module)
            if text is None:
                # A consumer named on an entry but absent from CONSUMER_MODULES
                # would make the reverse scan incomplete, so refuse it.
                raise AssertionError(
                    "%s: %r names consumer %r, which is not in CONSUMER_MODULES"
                    % (STOP_FIELD_SCHEMA, entry["name"], module))
            # A consumer may spell a quantity differently. Every accepted
            # spelling is declared in ALIASES, so a divergence is recorded
            # rather than silently tolerated.
            spellings = [entry["name"]]
            spellings.extend(src for src, canonical in ALIASES.items()
                             if canonical == entry["name"])
            if not any(re.search(r"\b%s\b" % re.escape(s), text) for s in spellings):
                raise AssertionError(
                    "%s: %r (spellings %s) is not referenced in %s"
                    % (STOP_NOT_CONSUMED, entry["name"],
                       ", ".join(repr(s) for s in spellings), module))
    return True


def undeclared_donor_quantities(
        code_dirs_or_sources: Path | str | Sequence[Path | str] | Mapping[str, str],
) -> tuple[str, ...]:
    """Reverse direction: donor-level names in the consumers that we do not declare.

    This is the check that exists because `IMMUNE_FRACTION` and
    `technical_complete` were missed. It scans the declared column-set literals
    of each consumer module -- the places a consumer states what it requires --
    and reports any name that the contract does not account for.

    It takes no caller-supplied allowlist on purpose. Everything excluded is
    excluded by a declaration in this module, where it can be reviewed.
    """
    sources = _as_sources(code_dirs_or_sources)
    index = contract_index()
    known = set(index) | set(ALIASES) | set(NON_DONOR_SELECTORS)
    found: set[str] = set()
    for module in CONSUMER_MODULES:
        text = sources[module]
        # Column-set literals: base_cols=[...], req=[...], req={...},
        # reqs={...}, *_COLUMNS=[...]. These are the self-declared requirements.
        for match in re.finditer(
                r"(?:base_cols|req|reqs|required|[A-Z_]*COLUMNS)\s*=\s*[\[{]([^\]}]*)[\]}]",
                text):
            for literal in re.finditer(r"['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]",
                                       match.group(1)):
                found.add(literal.group(1))
    return tuple(sorted(n for n in found if n not in known))


def assert_no_undeclared_donor_quantities(
        code_dirs_or_sources: Path | str | Sequence[Path | str] | Mapping[str, str],
) -> bool:
    missing = undeclared_donor_quantities(code_dirs_or_sources)
    if missing:
        raise AssertionError(
            "%s: the consumers require %s, which this contract does not declare"
            % (STOP_UNDECLARED, ", ".join(repr(m) for m in missing)))
    return True


def _typed(value: Any) -> bytes:
    """Type-tagged, length-prefixed framing. Injective over the declared types."""
    if isinstance(value, bool):
        tag, payload = b"b", (b"1" if value else b"0")
    elif isinstance(value, int):
        tag, payload = b"i", str(int(value)).encode("ascii")
    elif isinstance(value, str):
        tag, payload = b"s", value.encode("utf-8")
    elif isinstance(value, (tuple, list)):
        tag = b"l"
        inner = b"".join(_typed(v) for v in value)
        payload = b"%d:%s" % (len(value), inner)
    else:
        raise AssertionError("%s: cannot frame %r" % (STOP_FIELD_SCHEMA, type(value)))
    return b"%s%d:%s" % (tag, len(payload), payload)


def contract_root() -> str:
    """Digest of the contract itself, over injectively framed bytes."""
    parts = [_typed(SCHEMA), _typed(NAMESPACE),
             _typed(list(CLASSIFICATIONS)), _typed(list(PATHOLOGY_CLASSES)),
             _typed(list(DONOR_SCOPES)), _typed(list(STAGE_ORDER)),
             _typed(list(CONSUMER_MODULES)),
             _typed([[k, ALIASES[k]] for k in sorted(ALIASES)]),
             _typed(sorted(NON_DONOR_SELECTORS)),
             _typed(TECHNICAL_COMPLETENESS_SEMANTICS),
             _typed(list(TECHNICAL_COMPLETENESS_CONJUNCTS)),
             _typed(list(TECHNICAL_COMPLETENESS_FORBIDDEN_CUTOFFS)),
             _typed(TAIL_FLOOR_SCOPE),
             _typed(V18_METADATA_ONLY_INTERPRETATION),
             _typed(AUTHORITY_FAILURE_IS_NOT_INCOMPLETENESS),
             _typed(ELIGIBILITY_SHORTFALL_RULE),
             _typed(SINGLE_SEX_RULE)]
    for entry in sorted(CONTRACT, key=lambda e: e["name"]):
        parts.append(_typed([
            entry["name"], entry["classification"], entry["pathology_class"],
            entry["donor_scope"], entry["authority"],
            list(entry["depends_on"]), list(entry["consumed_by"]),
            entry["definition"],
        ]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def open_specification_slots() -> tuple[str, ...]:
    """Quantities whose authority is not yet decided. Must be reported, not hidden."""
    return tuple(sorted(e["name"] for e in CONTRACT
                        if e["authority"].startswith("OPEN__")))


def assert_technical_completeness_is_threshold_free() -> bool:
    """The predicate must stay a definedness test, never acquire a cutoff.

    This is the guard on the owner's 2026-09-08 decision. The risk it addresses
    is drift: a plausible-sounding quality floor added later would silently turn
    eligibility into a post-hoc donor filter, and V18 freezes no such threshold
    to appeal to.
    """
    if TECHNICAL_COMPLETENESS_SEMANTICS != "THRESHOLD_FREE_DEFINEDNESS_AND_COMPUTABILITY":
        raise AssertionError("%s: semantics changed to %r"
                             % (STOP_THRESHOLD_INTRODUCED,
                                TECHNICAL_COMPLETENESS_SEMANTICS))
    entry = contract_index()["technical_complete"]
    text = entry["definition"]
    # A comparison operator against either technical summary would be a cutoff.
    for token in (">=", "<=", " > ", " < ", "minimum of", "at least 80"):
        if token in text:
            raise AssertionError("%s: definition contains %r"
                                 % (STOP_THRESHOLD_INTRODUCED, token))
    if "80-cell" in text and "tail measurability only" not in text:
        raise AssertionError(
            "%s: the 80-cell floor is referenced without confining it to tail "
            "measurability" % STOP_THRESHOLD_INTRODUCED)
    if TAIL_FLOOR_SCOPE != "TAIL_MEASURABILITY_ONLY__NEVER_ELIGIBILITY_OR_PARENT_ROLE":
        raise AssertionError("%s: tail floor scope widened to %r"
                             % (STOP_THRESHOLD_INTRODUCED, TAIL_FLOOR_SCOPE))
    if len(TECHNICAL_COMPLETENESS_CONJUNCTS) != 6:
        raise AssertionError("%s: the frozen predicate has %d conjuncts, expected 6"
                             % (STOP_THRESHOLD_INTRODUCED,
                                len(TECHNICAL_COMPLETENESS_CONJUNCTS)))
    return True


def assert_eligibility_conjuncts_stay_separate() -> bool:
    """Each eligibility conjunct is its own authority; none may absorb another.

    In particular technical_complete may not depend on AT8 availability, age or
    sex, and it may not depend on IMMUNE_FRACTION -- that is a nuisance covariate
    for the composition sensitivity, not an eligibility input.
    """
    tech = contract_index()["technical_complete"]
    for forbidden in ("AT8_available", "AT8", "age", "sex", "IMMUNE_FRACTION"):
        if forbidden in tech["depends_on"]:
            raise AssertionError(
                "%s: technical_complete must not depend on %r; it is a separate "
                "eligibility conjunct or a nuisance covariate"
                % (STOP_PATHOLOGY if forbidden.startswith("AT8") else STOP_UNKNOWN_DEP,
                   forbidden))
    eligible = contract_index()["eligible"]
    if set(eligible["depends_on"]) != {"AT8_available", "technical_complete",
                                       "age", "sex"}:
        raise AssertionError(
            "%s: eligibility conjuncts are %r, expected exactly the four frozen ones"
            % (STOP_UNKNOWN_DEP, eligible["depends_on"]))
    return True


def pending_authorities() -> tuple[str, ...]:
    """Quantities whose producing authority does not exist yet."""
    return tuple(sorted(e["name"] for e in CONTRACT
                        if e["authority"].endswith("__PENDING")))


def verify_contract(
        code_dirs_or_sources: Path | str | Sequence[Path | str] | Mapping[str, str],
) -> dict[str, Any]:
    """Full verification. Raises on any violation; returns the summary otherwise."""
    sources = _as_sources(code_dirs_or_sources)
    assert_contract_wellformed()
    assert_technical_completeness_is_threshold_free()
    assert_eligibility_conjuncts_stay_separate()
    assert_declared_quantities_are_consumed(sources)
    assert_no_undeclared_donor_quantities(sources)
    return {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "contract_root_sha256": contract_root(),
        "declared_quantities": len(CONTRACT),
        "consumer_modules": len(CONSUMER_MODULES),
        "consumer_source_sha256": {
            m: hashlib.sha256(sources[m].encode("utf-8")).hexdigest()
            for m in CONSUMER_MODULES},
        "open_specification_slots": open_specification_slots(),
        "pending_authorities": pending_authorities(),
        "stage_order": STAGE_ORDER,
        "technical_completeness_semantics": TECHNICAL_COMPLETENESS_SEMANTICS,
        "technical_completeness_conjuncts": TECHNICAL_COMPLETENESS_CONJUNCTS,
        "tail_floor_scope": TAIL_FLOOR_SCOPE,
        "real_execution_ready": False,
    }
