"""Regressions for the T0 input dependency contract.

The suite runs against a committed fixture of consumer declaration lines, so it
does not resolve any local package path and never skips. One additional test
compares the fixture against the frozen V20 package when that package happens to
be present, but the contract checks themselves do not depend on it: a check that
skips when its inputs are absent is not a check that ran.

The centrepiece is `test_reverse_scan_catches_a_missing_required_input`. The
contract exists because `IMMUNE_FRACTION` and `technical_complete` were required
by the consumers and declared nowhere, and were found late. That test proves the
guard discriminates by removing each of them and requiring the scan to name it.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts" / "v4"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import t0_input_dependency_contract_v1 as C  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "t0_consumer_declarations_v1.json"


@pytest.fixture(scope="module")
def fixture_payload() -> dict:
    # Absence is a failure, not a skip. The fixture is committed; if it is gone
    # the suite must say so rather than quietly certify nothing.
    assert FIXTURE.is_file(), "committed fixture missing: %s" % FIXTURE
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sources(fixture_payload: dict) -> dict[str, str]:
    return {module: "\n".join(entry["declaration_lines"])
            for module, entry in fixture_payload["modules"].items()}


# --- shape of the contract itself -------------------------------------------

def test_contract_is_wellformed():
    assert C.assert_contract_wellformed() is True


def test_no_duplicate_quantity_names():
    names = [e["name"] for e in C.CONTRACT]
    assert len(names) == len(set(names))


def test_every_alias_resolves_to_a_declared_quantity():
    declared = {e["name"] for e in C.CONTRACT}
    for source_name, canonical in C.ALIASES.items():
        assert canonical in declared, "alias %r -> undeclared %r" % (source_name, canonical)


def test_non_donor_selectors_do_not_shadow_declared_quantities():
    declared = {e["name"] for e in C.CONTRACT}
    assert not (declared & C.NON_DONOR_SELECTORS)


def test_contract_root_is_deterministic():
    assert C.contract_root() == C.contract_root()
    assert len(C.contract_root()) == 64
    assert all(ch in "0123456789abcdef" for ch in C.contract_root())


def test_contract_root_moves_when_a_definition_changes():
    before = C.contract_root()
    original = C.CONTRACT
    try:
        mutated = []
        for entry in original:
            copy = dict(entry)
            if copy["name"] == "Q_DEPTH":
                copy["definition"] = copy["definition"] + " (perturbed for this test)"
            mutated.append(copy)
        C.CONTRACT = tuple(mutated)
        assert C.contract_root() != before
    finally:
        C.CONTRACT = original


# --- the two directions -----------------------------------------------------

def test_declared_quantities_are_actually_consumed(sources):
    assert C.assert_declared_quantities_are_consumed(sources) is True


def test_no_undeclared_donor_quantities(sources):
    assert C.undeclared_donor_quantities(sources) == ()
    assert C.assert_no_undeclared_donor_quantities(sources) is True


def test_full_verification_passes(sources):
    summary = C.verify_contract(sources)
    assert summary["schema"] == C.SCHEMA
    assert summary["declared_quantities"] == len(C.CONTRACT)
    assert summary["consumer_modules"] == len(C.CONSUMER_MODULES)
    assert summary["real_execution_ready"] is False


@pytest.mark.parametrize("quantity", ["IMMUNE_FRACTION", "technical_complete"])
def test_reverse_scan_catches_a_missing_required_input(sources, quantity):
    """The defect this contract was built for, reproduced in both instances.

    Both quantities are required by the frozen consumers and were declared
    nowhere. If the reverse scan cannot notice their absence from the contract,
    the contract is decorative.
    """
    original = C.CONTRACT
    try:
        C.CONTRACT = tuple(e for e in original if e["name"] != quantity)
        with pytest.raises(AssertionError) as excinfo:
            C.assert_no_undeclared_donor_quantities(sources)
        assert C.STOP_UNDECLARED in str(excinfo.value)
        assert quantity in str(excinfo.value)
    finally:
        C.CONTRACT = original


def test_forward_check_catches_a_quantity_declared_against_the_wrong_consumer(sources):
    original = C.CONTRACT
    try:
        mutated = []
        for entry in original:
            copy = dict(entry)
            if copy["name"] == "IMMUNE_FRACTION":
                # Not consumed by the split module; claiming so must be refused.
                copy["consumed_by"] = ("t0_discovery_confirmation_split_v2",)
            mutated.append(copy)
        C.CONTRACT = tuple(mutated)
        with pytest.raises(AssertionError) as excinfo:
            C.assert_declared_quantities_are_consumed(sources)
        assert C.STOP_NOT_CONSUMED in str(excinfo.value)
    finally:
        C.CONTRACT = original


# --- absent or incomplete inputs are STOPs, never skips ---------------------

def test_absent_source_root_is_a_stop():
    with pytest.raises(AssertionError) as excinfo:
        C.verify_contract(Path("/definitely-not-a-real-root-for-t0"))
    assert C.STOP_CONSUMER_ABSENT in str(excinfo.value)


def test_incomplete_source_mapping_is_a_stop(sources):
    partial = dict(sources)
    partial.pop("t0_adjudicator_v1")
    with pytest.raises(AssertionError) as excinfo:
        C.verify_contract(partial)
    assert C.STOP_CONSUMER_ABSENT in str(excinfo.value)
    assert "t0_adjudicator_v1" in str(excinfo.value)


def test_empty_source_text_is_a_stop(sources):
    blanked = dict(sources)
    blanked["t0_adjudicator_v1"] = ""
    with pytest.raises(AssertionError) as excinfo:
        C.verify_contract(blanked)
    assert C.STOP_CONSUMER_ABSENT in str(excinfo.value)


def test_no_source_root_supplied_is_a_stop():
    with pytest.raises(AssertionError) as excinfo:
        C.assert_declared_quantities_are_consumed([])
    assert C.STOP_CONSUMER_ABSENT in str(excinfo.value)


# --- graph invariants -------------------------------------------------------

def test_dependency_on_a_later_stage_is_refused():
    original = C.CONTRACT
    try:
        mutated = []
        for entry in original:
            copy = dict(entry)
            if copy["name"] == "cells":
                # DERIVED may not depend on a ROLE_DEPENDENT quantity.
                copy["depends_on"] = ("donor_role",)
            mutated.append(copy)
        C.CONTRACT = tuple(mutated)
        with pytest.raises(AssertionError) as excinfo:
            C.assert_contract_wellformed()
        assert C.STOP_ORDER in str(excinfo.value)
    finally:
        C.CONTRACT = original


def test_undeclared_dependency_is_refused():
    original = C.CONTRACT
    try:
        mutated = []
        for entry in original:
            copy = dict(entry)
            if copy["name"] == "Q_DEPTH":
                copy["depends_on"] = ("a_quantity_that_does_not_exist",)
            mutated.append(copy)
        C.CONTRACT = tuple(mutated)
        with pytest.raises(AssertionError) as excinfo:
            C.assert_contract_wellformed()
        assert C.STOP_UNKNOWN_DEP in str(excinfo.value)
    finally:
        C.CONTRACT = original


def test_same_stage_cycle_is_refused():
    """Stage monotonicity permits same-stage edges, so cycles need their own check."""
    original = C.CONTRACT
    try:
        mutated = []
        for entry in original:
            copy = dict(entry)
            if copy["name"] == "Q_DEPTH":
                copy["depends_on"] = ("Q_DETECT",)
            elif copy["name"] == "Q_DETECT":
                copy["depends_on"] = ("Q_DEPTH",)
            mutated.append(copy)
        C.CONTRACT = tuple(mutated)
        with pytest.raises(AssertionError) as excinfo:
            C.assert_contract_wellformed()
        assert C.STOP_CYCLE in str(excinfo.value)
    finally:
        C.CONTRACT = original


def test_pathology_blind_quantity_may_not_depend_on_the_pathology_value():
    original = C.CONTRACT
    try:
        mutated = []
        for entry in original:
            copy = dict(entry)
            if copy["name"] == "Q_DEPTH":
                copy["depends_on"] = ("AT8",)
            mutated.append(copy)
        C.CONTRACT = tuple(mutated)
        with pytest.raises(AssertionError) as excinfo:
            C.assert_contract_wellformed()
        assert C.STOP_PATHOLOGY in str(excinfo.value)
    finally:
        C.CONTRACT = original


def test_unknown_classification_is_refused():
    original = C.CONTRACT
    try:
        mutated = []
        for entry in original:
            copy = dict(entry)
            if copy["name"] == "cells":
                copy["classification"] = "SOMETHING_ELSE"
            mutated.append(copy)
        C.CONTRACT = tuple(mutated)
        with pytest.raises(AssertionError) as excinfo:
            C.assert_contract_wellformed()
        assert C.STOP_UNKNOWN_CLASS in str(excinfo.value)
    finally:
        C.CONTRACT = original


def test_duplicate_quantity_declaration_is_refused():
    original = C.CONTRACT
    try:
        C.CONTRACT = original + (original[0],)
        with pytest.raises(AssertionError) as excinfo:
            C.contract_index()
        assert C.STOP_FIELD_SCHEMA in str(excinfo.value)
    finally:
        C.CONTRACT = original


def test_missing_field_is_refused():
    original = C.CONTRACT
    try:
        stripped = dict(original[0])
        stripped.pop("definition")
        C.CONTRACT = (stripped,) + original[1:]
        with pytest.raises(AssertionError) as excinfo:
            C.assert_contract_wellformed()
        assert C.STOP_FIELD_SCHEMA in str(excinfo.value)
    finally:
        C.CONTRACT = original


# --- governance facts the contract must keep stating ------------------------

def test_no_open_specification_slots_remain():
    """The owner resolved technical_complete on 2026-09-08, so nothing is open."""
    assert C.open_specification_slots() == ()


def test_technical_completeness_is_frozen_as_threshold_free_definedness():
    assert C.assert_technical_completeness_is_threshold_free() is True
    assert C.TECHNICAL_COMPLETENESS_SEMANTICS == \
        "THRESHOLD_FREE_DEFINEDNESS_AND_COMPUTABILITY"
    assert len(C.TECHNICAL_COMPLETENESS_CONJUNCTS) == 6
    entry = C.contract_index()["technical_complete"]
    assert entry["classification"] == "ELIGIBILITY"
    assert entry["pathology_class"] == "PATHOLOGY_BLIND"


@pytest.mark.parametrize("cutoff_text", [
    "Q_DEPTH >= 3.0 is required",
    "donors with Q_DETECT <= 0.01 are incomplete",
    "a donor must have at least 80 cells",
])
def test_introducing_a_quality_cutoff_is_refused(cutoff_text):
    """Guard on the owner decision: the predicate may not acquire a threshold.

    The realistic failure is not a deliberate change but drift -- someone adding
    a plausible quality floor later. V18 freezes no depth or detection threshold,
    so any such floor would be invented after the fact, and eligibility would
    quietly become a post-hoc donor filter.
    """
    original = C.CONTRACT
    try:
        mutated = []
        for entry in original:
            copy = dict(entry)
            if copy["name"] == "technical_complete":
                copy["definition"] = copy["definition"] + " " + cutoff_text
            mutated.append(copy)
        C.CONTRACT = tuple(mutated)
        with pytest.raises(AssertionError) as excinfo:
            C.assert_technical_completeness_is_threshold_free()
        assert C.STOP_THRESHOLD_INTRODUCED in str(excinfo.value)
    finally:
        C.CONTRACT = original


def test_widening_the_tail_floor_scope_is_refused():
    original = C.TAIL_FLOOR_SCOPE
    try:
        C.TAIL_FLOOR_SCOPE = "ELIGIBILITY_AND_TAIL"
        with pytest.raises(AssertionError) as excinfo:
            C.assert_technical_completeness_is_threshold_free()
        assert C.STOP_THRESHOLD_INTRODUCED in str(excinfo.value)
    finally:
        C.TAIL_FLOOR_SCOPE = original


def test_changing_the_semantics_label_is_refused():
    original = C.TECHNICAL_COMPLETENESS_SEMANTICS
    try:
        C.TECHNICAL_COMPLETENESS_SEMANTICS = "QUALITY_FILTER"
        with pytest.raises(AssertionError) as excinfo:
            C.assert_technical_completeness_is_threshold_free()
        assert C.STOP_THRESHOLD_INTRODUCED in str(excinfo.value)
    finally:
        C.TECHNICAL_COMPLETENESS_SEMANTICS = original


@pytest.mark.parametrize("forbidden", ["AT8_available", "age", "sex", "IMMUNE_FRACTION"])
def test_technical_completeness_may_not_absorb_another_conjunct(forbidden):
    """Each eligibility conjunct is a separate authority.

    B2 establishes technical definedness and holds no authority over AT8
    availability, age or sex, so it must not declare eligibility.
    IMMUNE_FRACTION is a nuisance covariate for the composition sensitivity, not
    an eligibility input.
    """
    original = C.CONTRACT
    try:
        mutated = []
        for entry in original:
            copy = dict(entry)
            if copy["name"] == "technical_complete":
                copy["depends_on"] = copy["depends_on"] + (forbidden,)
            mutated.append(copy)
        C.CONTRACT = tuple(mutated)
        with pytest.raises(AssertionError):
            C.assert_eligibility_conjuncts_stay_separate()
    finally:
        C.CONTRACT = original


def test_eligibility_conjuncts_stay_separate():
    assert C.assert_eligibility_conjuncts_stay_separate() is True


def test_authority_failure_is_not_recorded_as_technical_incompleteness():
    """The fail-closed rule must be stated, and must name the failure modes."""
    text = C.AUTHORITY_FAILURE_IS_NOT_INCOMPLETENESS
    assert "B2 STOPs" in text
    for mode in ("source digest", "identity mismatch", "counts digest",
                 "manifest inconsistency"):
        assert mode in text, mode


def test_eligibility_shortfall_is_a_stop_not_a_relaxation():
    text = C.ELIGIBILITY_SHORTFALL_RULE
    assert C.STOP_DESIGN_NOT_EXECUTABLE in text
    assert "Do not relax eligibility" in text
    assert "do not alter the split" in text


def test_single_sex_confirmation_is_a_loud_design_failure():
    text = C.SINGLE_SEX_RULE
    assert "fail loudly" in text
    assert "not a biological NOT_MEASURABLE" in text
    assert "must not be altered" in text


def test_v18_metadata_only_wording_is_interpreted_not_rewritten():
    text = C.V18_METADATA_ONLY_INTERPRETATION
    assert "pathology-blind" in text
    assert "does not mean the flag" in text


def test_at8_value_is_classified_as_a_gated_pathology_value():
    entry = C.contract_index()["AT8"]
    assert entry["pathology_class"] == "PATHOLOGY_VALUE"
    assert entry["authority"] == "GATED__REAL_T0_UNAUTHORIZED"


def test_at8_availability_is_value_blind_and_separate_from_the_value():
    entry = C.contract_index()["AT8_available"]
    assert entry["pathology_class"] == "AVAILABILITY_PREDICATE"
    assert "AT8" not in entry["depends_on"]


def test_eligibility_predicate_matches_the_frozen_role_authority():
    entry = C.contract_index()["eligible"]
    assert set(entry["depends_on"]) == {"AT8_available", "technical_complete",
                                        "age", "sex"}


def test_donor_role_depends_on_frozen_eligibility_not_the_other_way_round():
    role = C.contract_index()["donor_role"]
    assert "eligible" in role["depends_on"]
    assert "donor_role" not in C.contract_index()["eligible"]["depends_on"]


def test_tail_measurability_never_feeds_the_parent_role():
    """The frozen rule records tail measurability as an outcome of the split."""
    assert "tail_measurable" not in C.contract_index()["donor_role"]["depends_on"]
    assert C.contract_index()["tail_measurable"]["depends_on"] == ("cells",)


def test_q_detect_depends_on_the_projection_not_only_on_raw_rows():
    """Q_DETECT is defined on all 35,076 scalar addresses, so B1 is a prerequisite."""
    entry = C.contract_index()["Q_DETECT"]
    assert "35,076" in entry["definition"]
    assert "SCORING" in entry["definition"]


def test_immune_fraction_is_declared_derived_with_no_input_file():
    entry = C.contract_index()["IMMUNE_FRACTION"]
    assert entry["classification"] == "DERIVED"
    assert "NO input file" in entry["definition"]


def test_expression_row_and_row_index_are_distinct_quantities():
    index = C.contract_index()
    assert "ORIGINAL H5" in index["expression_row"]["definition"]
    assert "counts.npz" in index["row_index"]["definition"]
    assert index["expression_row"]["name"] != index["row_index"]["name"]


def test_pending_authorities_are_reported_rather_than_hidden():
    """What is still unbuilt must stay visible, and what is built must drop out.

    IMMUNE_FRACTION, cells and the age/sex demographics now have real
    authorities, so they are no longer pending. Q_DEPTH, Q_DETECT,
    technical_complete and eligible still are.
    """
    pending = set(C.pending_authorities())
    assert {"Q_DEPTH", "Q_DETECT", "technical_complete", "eligible"} <= pending
    assert "IMMUNE_FRACTION" not in pending
    assert "cells" not in pending
    assert "age" not in pending and "sex" not in pending


def test_stage_order_places_eligibility_before_roles_and_matrices():
    order = list(C.STAGE_ORDER)
    at = order.index
    assert at("ELIGIBLE_DONOR_AUTHORITY") < at("DETERMINISTIC_V18_SPLIT")
    assert at("DETERMINISTIC_V18_SPLIT") < at("ROLE_SCOPED_MATRICES")
    assert at("B2_EXPRESSION_SUBSTRATE_AUTHENTICATION") < at("ELIGIBLE_DONOR_AUTHORITY")
    assert at("FEASIBILITY_B__EXACT_ELIGIBLE_AND_ROLES_ESTIMABILITY") < \
        at("DISCOVERY_FIT_AND_FREEZE")
    assert at("DISCOVERY_FIT_AND_FREEZE") < at("CONFIRMATION_UNLOCK_AND_TEST")


def test_cheap_feasibility_pass_precedes_expensive_materialization():
    """The ordering error that let an undeclared required input survive.

    FEASIBILITY_A is metadata-only and cheap. Running it after the materialization
    machinery was built is exactly how a required covariate went unnoticed, so the
    contract asserts the order rather than merely recommending it.
    """
    order = list(C.STAGE_ORDER)
    assert order.index("FEASIBILITY_A__CANDIDATE_UNIVERSE_METADATA_ONLY") < \
        order.index("B2_EXPRESSION_SUBSTRATE_AUTHENTICATION")


def test_b2_does_not_declare_eligibility():
    """Eligibility is its own stage, downstream of technical completeness.

    B2 authenticates the expression substrate and holds no authority over AT8
    availability, age or sex, so eligibility cannot be a B2 output.
    """
    order = list(C.STAGE_ORDER)
    at = order.index
    assert at("B2_EXPRESSION_SUBSTRATE_AUTHENTICATION") < \
        at("TECHNICAL_COMPLETENESS_AUTHORITY") < at("ELIGIBLE_DONOR_AUTHORITY")
    assert at("DERIVED_DONOR_QUANTITIES") < at("TECHNICAL_COMPLETENESS_AUTHORITY")


# --- framing injectivity ----------------------------------------------------

def test_typed_framing_separates_types():
    assert C._typed(1) != C._typed("1")
    assert C._typed(True) != C._typed(1)
    assert C._typed(False) != C._typed(0)
    assert C._typed("") != C._typed(0)


def test_typed_framing_is_injective_over_concatenation():
    """The delimiter collision class that broke earlier authority roots."""
    assert C._typed(["a|b"]) != C._typed(["a", "b"])
    assert C._typed(["a", "bc"]) != C._typed(["ab", "c"])
    assert C._typed([["a"], ["b"]]) != C._typed([["a", "b"]])


def test_typed_framing_refuses_an_unsupported_type():
    with pytest.raises(AssertionError) as excinfo:
        C._typed(1.5)
    assert C.STOP_FIELD_SCHEMA in str(excinfo.value)


# --- fixture fidelity -------------------------------------------------------

def test_fixture_records_a_digest_for_every_consumer(fixture_payload):
    modules = fixture_payload["modules"]
    assert set(modules) == set(C.CONSUMER_MODULES)
    for module, entry in modules.items():
        assert len(entry["source_sha256"]) == 64
        assert entry["declaration_lines"], module
        assert entry["root"] in ("V20_PACKAGE", "BRANCH_SCRIPTS")


def test_fixture_matches_the_branch_modules_it_claims(fixture_payload):
    """For consumers that live on this branch, verify the bound digest exactly.

    These are our own modules, always present, so this comparison is
    unconditional. It is what makes a silent drift in our own consumer visible.
    """
    checked = 0
    for module, entry in fixture_payload["modules"].items():
        if entry["root"] != "BRANCH_SCRIPTS":
            continue
        path = SCRIPTS / ("%s.py" % module)
        assert path.is_file(), path
        actual = hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
        assert actual == entry["source_sha256"], (
            "%s drifted from the digest the contract was verified against" % module)
        checked += 1
    assert checked >= 2


# ---------------------------------------------------------------------------
# The R6 provenance-label condition, enforced rather than conventional.
#
# The external reviewer accepted the waiver with ALLOWS_NEW_FALSE_LABELS=False.
# A convention would not hold that across future modules; these pin it.
# ---------------------------------------------------------------------------

def test_the_accurate_byte_semantics_constant_is_what_new_artifacts_use() -> None:
    assert C.ACCURATE_CODE_BYTE_SEMANTICS == (
        "SHA256_OVER_LF_NORMALIZED_FILE_CONTENT"
        "__NOT_GIT_BLOB_FRAMED_AND_NOT_WORKTREE_BYTES")
    assert "GIT_BLOB_BYTES__NOT_WORKTREE_BYTES" != (
        C.ACCURATE_CODE_BYTE_SEMANTICS)


def test_the_waiver_set_is_frozen_and_cannot_grow() -> None:
    assert C.assert_provenance_waiver_set_unchanged() is True
    assert len(C.PROVENANCE_LABEL_WAIVER_MODULES) == 6
    assert C.PROVENANCE_LABEL_WAIVER_ALLOWS_NEW_FALSE_LABELS is False
    with pytest.raises(AssertionError) as excinfo:
        C.assert_provenance_waiver_set_unchanged(expected_count=7)
    assert C.STOP_WAIVER_SET_GREW in str(excinfo.value)


def test_a_waived_legacy_module_may_keep_the_false_label() -> None:
    for name in C.PROVENANCE_LABEL_WAIVER_MODULES:
        assert C.assert_byte_semantics_label_lawful(
            name, C.WAIVED_FALSE_CODE_BYTE_SEMANTICS) is True


def test_a_new_module_carrying_the_false_label_is_refused() -> None:
    """The condition that matters for the real-T0 run."""
    for name in ("t0_real_run_v1.py", "t0_confirmation_raw_v1.py",
                 "scripts/v4/t0_anything_new_v1.py"):
        with pytest.raises(AssertionError) as excinfo:
            C.assert_byte_semantics_label_lawful(
                name, C.WAIVED_FALSE_CODE_BYTE_SEMANTICS)
        assert C.STOP_FALSE_BYTE_SEMANTICS in str(excinfo.value)


def test_an_unrecognised_byte_semantics_string_is_refused() -> None:
    for bad in ("", "WORKTREE_BYTES", "GIT_BLOB", "sha256", None):
        with pytest.raises(AssertionError):
            C.assert_byte_semantics_label_lawful("t0_new_v1.py", bad)


def test_a_new_module_declaring_the_accurate_label_is_accepted() -> None:
    assert C.assert_byte_semantics_label_lawful(
        "t0_real_run_v1.py", C.ACCURATE_CODE_BYTE_SEMANTICS) is True


def test_the_audit_classifies_every_t0_module_and_refuses_none_today() -> None:
    report = C.audit_byte_semantics_labels()
    assert set(report["waived_legacy"]) == set(
        C.PROVENANCE_LABEL_WAIVER_MODULES)
    assert "t0_eligible_donor_authority_v1.py" in report["accurate"]
    assert "t0_estimability_preflight_production_run_v1.py" in report["accurate"]
    assert report["allows_new_false_labels"] is False


def test_the_audit_matches_declaration_sites_not_the_bare_label() -> None:
    """The contract module names the legacy constant without declaring it.

    Substring-scanning for the label flagged this very module, which is the same
    crude-guard error that earlier refused an `age_present` header and a
    report's own `at8_availability_root_sha256`.
    """
    report = C.audit_byte_semantics_labels()
    assert "t0_input_dependency_contract_v1.py" not in report["waived_legacy"]
    assert "t0_input_dependency_contract_v1.py" not in report["accurate"]


def test_the_audit_covers_declarations_made_through_a_constant() -> None:
    """The R7 readiness modules declare via ACCURATE_CODE_BYTE_SEMANTICS.

    A literal-only check classified neither of them, so the guard silently did
    not cover the modules R7 had just added. Both forms must count.
    """
    report = C.audit_byte_semantics_labels()
    for name in ("t0_execution_input_readiness_authority_v1.py",
                 "t0_execution_input_readiness_run_v1.py",
                 "t0_estimability_preflight_production_run_v1.py"):
        assert name in report["accurate"], name


def test_the_audit_ignores_comments_and_docstrings() -> None:
    """Prose about a declaration is not a declaration.

    Three text-based versions of this check were wrong in the same way. The AST
    fixes the class: only a real dict key in a real expression counts.
    """
    assert C._declared_byte_semantics(
        '# "code_byte_semantics": WAIVED_FALSE_CODE_BYTE_SEMANTICS\n') == ()
    assert C._declared_byte_semantics(
        '"""Explains "code_byte_semantics": "GIT_BLOB_BYTES__NOT_WORKTREE_BYTES"'
        '"""\n') == ()
    # A real declaration, as a literal and as a constant reference.
    assert C._declared_byte_semantics(
        'x = {"code_byte_semantics": "GIT_BLOB_BYTES__NOT_WORKTREE_BYTES"}'
    ) == (C.WAIVED_FALSE_CODE_BYTE_SEMANTICS,)
    assert C._declared_byte_semantics(
        'x = {"derivation_code_byte_semantics": ACCURATE_CODE_BYTE_SEMANTICS}'
    ) == (C.ACCURATE_CODE_BYTE_SEMANTICS,)
    # Implicit and explicit concatenation of the accurate constant's two halves.
    assert C._declared_byte_semantics(
        'x = {"code_byte_semantics": ("SHA256_OVER_LF_NORMALIZED_FILE_CONTENT"'
        ' + "__NOT_GIT_BLOB_FRAMED_AND_NOT_WORKTREE_BYTES")}'
    ) == (C.ACCURATE_CODE_BYTE_SEMANTICS,)


def test_the_audit_does_not_classify_the_module_that_defines_the_constants(
) -> None:
    report = C.audit_byte_semantics_labels()
    for bucket in ("accurate", "waived_legacy"):
        assert "t0_input_dependency_contract_v1.py" not in report[bucket]
