"""Adversarial firewall tests for the D1 full-fit population and gates.

Proves that the 50,000-cell auxiliary sample, the historical 4,540-cell biology
cohort, synthetic fixtures, and any protected partition cannot become a
production D1 parameter, and that no production artifact can be emitted while
the teacher gate is closed.

Five checks need the calibration bundle, which is multi-gigabyte and untracked
and therefore cannot be a package member. They are declared in
`AUTHORITY_DEPENDENT_TESTS` and skip loudly as NOT_MEASURABLE when the bundle is
absent. A skip is not a pass: under this project's precedence
`INVALID > FAIL > NOT_MEASURABLE > PASS` an authority-dependent check that did
not run has not been evaluated. Set `D1_AUTHORITY_ROOT` to a tree holding the
bundle, and `D1_REQUIRE_AUTHORITIES=1` to turn an unreachable authority into a
failure rather than a skip.
"""

from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "v4"
sys.path.insert(0, str(SCRIPTS))

import d1_real_data_derivation_core_v1 as core  # noqa: E402
import d1_full_fit_population_audit_v1 as audit  # noqa: E402
import d1_parameter_derivation_v1 as derivation  # noqa: E402
import d1_teacher_state_stream_v1 as teacher  # noqa: E402

CONFIG = ROOT / "configs" / "v4" / "d1_real_data_derivation_v1.yaml"
REQUIRE_AUTHORITIES = os.environ.get("D1_REQUIRE_AUTHORITIES") == "1"

AUTHORITY_DEPENDENT_TESTS = (
    "test_end_to_end_derivation_terminates_wait_healthy_trained_teacher",
    "test_real_full_fit_population_audit_passes_against_authority",
    "test_real_observation_state_authority_declares_measured_as_code_one",
    "test_real_teacher_readout_is_unresolved_and_gate_is_closed",
    "test_the_50k_auxiliary_archive_is_present_but_classified_auxiliary",
)


def _need_authority(relative: str) -> Path:
    if audit.authority_available(relative):
        return audit.resolve_authority(relative)
    message = ("NOT_MEASURABLE (not a pass): authority %s unreachable. Set "
               "D1_AUTHORITY_ROOT, or D1_REQUIRE_AUTHORITIES=1 to fail instead."
               % relative)
    if REQUIRE_AUTHORITIES:
        pytest.fail(message)
    pytest.skip(message)


# ------------------------------------------------- 7. the 50k auxiliary sample
def test_the_50k_sample_is_rejected_as_a_production_input() -> None:
    """Real data, but auxiliary: it cannot set a full-population parameter."""
    with pytest.raises(PermissionError, match="FORBIDDEN_PRODUCTION_INPUT"):
        audit.assert_not_forbidden_production_input(
            "exports/foundation_calibration_bundle_20260824/expression/"
            "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz")
    with pytest.raises(PermissionError, match="FORBIDDEN_PRODUCTION_INPUT"):
        audit.assert_not_forbidden_production_input(
            "somewhere/else/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv")
    # And a provenance carrying the 50k population is not production eligible,
    # even with the correct donor count, because 50,000 != 4,553,407.
    provenance = core.D1Provenance(
        statistic_id="D1-P009:D", population_class=core.AUXILIARY_REAL_50K,
        formula_version="v1", donors=104, cells=50000, operators=42)
    assert provenance.is_production_eligible() is False
    with pytest.raises(PermissionError, match="NOT_PRODUCTION_POPULATION"):
        core.emit_production_parameter(parameter_id="D1-P009:D", value=12,
                                       provenance=provenance, teacher_gate_open=True)


def test_a_full_fit_class_label_cannot_launder_a_50k_row_count() -> None:
    """Relabelling the population class is not enough; the counts are checked."""
    laundered = core.D1Provenance(
        statistic_id="D1-P009:D", population_class=core.PRODUCTION_FULL_FIT,
        formula_version="v1", donors=104, cells=50000, operators=42)
    assert laundered.is_production_eligible() is False
    with pytest.raises(PermissionError, match="NOT_PRODUCTION_POPULATION"):
        core.emit_production_parameter(parameter_id="D1-P009:D", value=12,
                                       provenance=laundered, teacher_gate_open=True)


# --------------------------------------------- 8. the historical 4,540 cohort
def test_the_4540_biology_cohort_is_rejected_as_a_production_input() -> None:
    with pytest.raises(PermissionError, match="FORBIDDEN_PRODUCTION_INPUT"):
        audit.assert_not_forbidden_production_input(
            "exports/foundation_calibration_bundle_20260824/splits/"
            "T1_BIOLOGY_EVALUATION_FREEZE.json")
    cohort = core.D1Provenance(
        statistic_id="D1-P017:tail_numeric_cutpoints",
        population_class=core.HISTORICAL_BIOLOGY_COHORT_4540,
        formula_version="v1", donors=104, cells=4540, operators=42)
    assert cohort.is_production_eligible() is False
    with pytest.raises(PermissionError, match="NOT_PRODUCTION_POPULATION"):
        core.emit_production_parameter(parameter_id="D1-P017:tail_numeric_cutpoints",
                                       value=1.96, provenance=cohort,
                                       teacher_gate_open=True)


# --------------------------- 9. protected populations STOP rather than filter
def test_protected_partition_rows_stop_rather_than_being_filtered() -> None:
    """The failure mode this prevents is a quiet population change.

    The authoritative per-cell table holds reader_validation and reader_oracle
    rows beside reader_fit, so dropping unexpected rows and continuing would
    silently redefine the population while still reporting success.
    """
    clean = ["reader_fit"] * 5
    assert audit.assert_no_protected_rows(clean)["protected_rows_delivered"] == 0
    for protected in ("reader_validation", "reader_oracle", "sealed_holdout",
                      "development", "pathology"):
        with pytest.raises(PermissionError, match="PROTECTED_POPULATION_ACCESS"):
            audit.assert_no_protected_rows(["reader_fit", protected, "reader_fit"])


def test_protected_paths_are_rejected_by_token_as_well_as_by_name() -> None:
    for path in ("data/reader_oracle/expression.npz",
                 "exports/sealed/holdout.csv",
                 "results/pathology_sidecar.parquet",
                 "data/development/rows.csv"):
        with pytest.raises(PermissionError, match="FORBIDDEN_PRODUCTION_INPUT"):
            audit.assert_not_forbidden_production_input(path)


def test_a_forbidden_protected_provenance_is_refused_first() -> None:
    protected = core.D1Provenance(
        statistic_id="D1-P009:D", population_class=core.FORBIDDEN_PROTECTED,
        formula_version="v1", donors=104, cells=4553407, operators=42)
    with pytest.raises(PermissionError, match="PROTECTED_POPULATION_ACCESS"):
        core.emit_production_parameter(parameter_id="D1-P009:D", value=3,
                                       provenance=protected, teacher_gate_open=True)


# -------------------- 10. no production artifact while the teacher gate is shut
def test_no_production_parameter_can_be_emitted_while_the_gate_is_closed() -> None:
    """Even complete provenance cannot emit with the gate closed.

    Provenance is deliberately complete here so that the teacher gate, and not
    a missing root, is what refuses. Counts alone would no longer be eligible.
    """
    provenance = core.D1Provenance(**_full_provenance_kwargs())
    assert provenance.is_production_eligible() is True
    with pytest.raises(PermissionError, match="TEACHER_GATE_CLOSED"):
        core.emit_production_parameter(
            parameter_id="D1-P009:D", value=9, provenance=provenance,
            teacher_gate_open=False, diagnostics={"D_PA": 9})
    # With the gate open the same call succeeds, so the test is discriminating
    # rather than passing because everything refuses.
    emitted = core.emit_production_parameter(
        parameter_id="D1-P009:D", value=9, provenance=provenance,
        teacher_gate_open=True, diagnostics={"D_PA": 9})
    assert emitted["value"] == 9
    assert emitted["provenance"]["population_class"] == core.PRODUCTION_FULL_FIT


def test_teacher_stream_refuses_production_states_while_unresolved() -> None:
    report = {"unique_authorized_cell_level_state": False,
              "healthy_trained_teacher_available": False,
              "conflicts": ["no representation contract"]}
    assert teacher.teacher_gate_open(report) is False
    with pytest.raises(PermissionError, match="TEACHER_READOUT_UNRESOLVED"):
        next(teacher.iter_teacher_states(population_class=core.PRODUCTION_FULL_FIT,
                                         report=report))
    # The gate opens only when BOTH conditions hold.
    for partial in ({"unique_authorized_cell_level_state": True,
                     "healthy_trained_teacher_available": False},
                    {"unique_authorized_cell_level_state": False,
                     "healthy_trained_teacher_available": True}):
        assert teacher.teacher_gate_open(partial) is False
    assert teacher.teacher_gate_open({"unique_authorized_cell_level_state": True,
                                      "healthy_trained_teacher_available": True}) is True


def test_the_streamer_refuses_to_fabricate_synthetic_states() -> None:
    """The streamer needs a supplied source; it never invents states."""
    with pytest.raises(PermissionError, match="TEACHER_READOUT_UNRESOLVED"):
        next(teacher.iter_teacher_states(population_class=core.MECHANICS_ONLY))


def test_defect_inherited_checkpoints_are_never_classified_healthy() -> None:
    assert set(teacher.DEFECT_INHERITED_UPDATES) == {10, 25, 50, 100, 200, 205}
    assert teacher.UNTRAINED_UPDATES == (0,)
    assert 205 in teacher.DEFECT_INHERITED_UPDATES


# ----------------------------- 11. the config holds no production adaptive value
def test_config_contains_no_hand_entered_production_value() -> None:
    out = derivation.validate_config_has_no_production_values(CONFIG)
    assert out["production_adaptive_values"] == 0
    assert out["prohibited_historical_values"] == 0
    assert out["keys_checked"] > 20


def test_config_validator_rejects_a_smuggled_production_value(tmp_path: Path) -> None:
    """Guard the validator: it must reject, not merely be run.

    A validator that accepted everything would let the real config pass for the
    wrong reason, so each prohibited shape is injected and required to fail.
    """
    base = CONFIG.read_text(encoding="utf-8")
    cases = {
        "production_d": "\nproduction_d: 12\n",
        "program_count": "\nprogram_count_K: 12\n",
        "neighborhood": "\nneighborhood_radius: 0.75\n",
        "tail_cut": "\ntail_score_cutpoint: 1.96\n",
        "stability_cut": "\nstability_cutoff: 0.8\n",
        "redundancy_cut": "\nredundancy_cutoff: 0.9\n",
        "svd": "\nsvd_components: 50\n",
        "candidate_rank": "\ncandidate_rank: 320\n",
        "sketch": "\nsketch_dimension: 512\n",
        "resamples": "\ndonor_resamples: 256\n",
    }
    for name, injection in cases.items():
        path = tmp_path / ("cfg_%s.yaml" % name)
        path.write_text(base + injection, encoding="utf-8")
        with pytest.raises(AssertionError) as excinfo:
            derivation.validate_config_has_no_production_values(path)
        assert ("PRODUCTION_ADAPTIVE_VALUE" in str(excinfo.value)
                or "PROHIBITED_HISTORICAL_VALUE" in str(excinfo.value)), name


def test_prohibited_historical_values_are_enumerated() -> None:
    values = set(core.PROHIBITED_HISTORICAL_VALUES.values())
    for prohibited in (50, 15, 30, 60, 120, 320, 512, 256):
        assert prohibited in values


def test_config_declares_no_hardcoded_D_anywhere_in_its_text() -> None:
    """A belt-and-braces textual check over the real config file."""
    text = CONFIG.read_text(encoding="utf-8")
    tree = [line.split("#", 1)[0] for line in text.splitlines()]
    body = "\n".join(tree)
    for forbidden in ("production_d:", "program_count_K:", "latent_dimension:",
                      "n_components:", "sketch_dimension:", "candidate_rank:"):
        assert forbidden not in body, forbidden


# ------------------------------------------- refusal-only defence at this layer
def test_the_firewall_accepts_lawful_input_as_well_as_refusing_unlawful() -> None:
    """A firewall that refused everything would be useless and must not pass.

    Each refusal above is paired with a lawful case that must succeed.
    """
    assert audit.assert_no_protected_rows(["reader_fit"])["protected_rows_delivered"] == 0
    audit.assert_not_forbidden_production_input(
        "exports/foundation_calibration_bundle_20260824/metadata/FOUNDATION_METADATA_DONOR.csv")
    lawful = core.D1Provenance(**dict(_full_provenance_kwargs(),
                                      statistic_id="D1-P002:donor_operator_cell_weights"))
    assert core.emit_production_parameter(
        parameter_id="D1-P002:donor_operator_cell_weights", value={"formula": "a_dc"},
        provenance=lawful, teacher_gate_open=True,
        diagnostics={"max_donor_mass_deviation": 4.44e-16})["parameter_id"].startswith("D1-P002")


# --------------------------------------------------------- authority-dependent
def test_real_full_fit_population_audit_passes_against_authority() -> None:
    """104 donors, 4,553,407 cells, 42 operators, 41,238 addresses, from authority."""
    _need_authority(audit.CELL_METADATA_REL)
    report = audit.audit_full_fit_population(open_molecular=True)
    assert report["terminal"] == audit.TERMINAL_PASS
    assert report["observed"]["donors"] == 104
    assert report["observed"]["cells"] == 4553407
    assert report["observed"]["operators"] == 42
    assert report["observed"]["donor_operator_pairs"] == 1400
    assert report["source_cells"] == {"HVS": 198718, "NPH52": 236476, "SEA_AD": 4118213}
    assert report["molecular"]["addresses"] == 41238
    assert report["molecular"]["observation_state_shape"] == [42, 41238]
    # Protected partitions are never queried, not even for a count. Their
    # existence is known from the donor-level frozen split authority instead.
    assert report["firewall"]["protected_rows_delivered"] == 0
    assert report["firewall"]["protected_per_cell_rows_queried"] is False
    assert report["firewall"]["protected_partition_metadata_queried"] is False
    assert report["firewall"]["expression_opened"] is False
    declared = report["population_identity"]["declared_partition_donor_counts"]
    assert declared["reader_fit"] == 104
    assert set(declared) == {"reader_fit", "reader_validation", "reader_oracle"}
    # Population identity, not just totals.
    assert report["population_identity"]["delivered_donor_set_equals_frozen_roster"] is True
    assert report["source_cells"] == report["expected_source_cells"]
    # Normalization is proven from the loader implementation, not asserted.
    assert report["normalization"]["proven_from"] == "loader implementation source"
    assert report["normalization"]["applied_times"] == 1
    assert "np.maximum(library, 1.0)" in report["normalization"]["scale_site"]
    # Every controlling authority is bound by content digest.
    assert "cell_metadata_sqlite_bytes" not in report["authority_sha256"]
    assert len(report["authority_sha256"]["cell_metadata_sqlite"]) == 64
    # Donor-primary weighting holds on the real population.
    assert report["donor_primary_weighting"]["max_donor_mass_deviation"] < 1e-12
    assert report["donor_primary_weighting"]["max_operator_mass_deviation"] < 1e-12


def test_real_observation_state_authority_declares_measured_as_code_one() -> None:
    """Bind the measured/unmeasured code mapping to the authority's own names."""
    path = _need_authority(audit.AUTHORITY_FILES["support_observation_state"])
    with np.load(path, allow_pickle=False) as archive:
        names = [str(s) for s in archive["state_names"]]
        states = archive["states"]
    codes = core.load_observation_state_codes(names)
    assert codes["MEASURED_SCALAR"] == core.MEASURED_SCALAR == 1
    assert codes["STRUCTURALLY_UNMEASURED"] == core.STRUCTURALLY_UNMEASURED == 0
    # Cross-check against the recurrence CSV, which counts measured operators.
    recurrence = _need_authority(audit.AUTHORITY_FILES["support_address_recurrence"])
    import csv as _csv
    with open(recurrence, newline="", encoding="utf-8") as handle:
        rows = [next(_csv.DictReader(handle)) for _ in range(1)] if False else list(
            _csv.DictReader(handle))[:200]
    for row in rows:
        column = states[:, int(row["molecular_address_index"])]
        assert int((column == core.MEASURED_SCALAR).sum()) == int(row["operators_measured_scalar"])
        assert int((column == core.STRUCTURALLY_UNMEASURED).sum()) == int(
            row["operators_structurally_unmeasured"])


def test_real_teacher_readout_is_unresolved_and_gate_is_closed() -> None:
    """The honest Phase 1 outcome, with its conflicts named."""
    _need_authority(audit.CELL_METADATA_REL)
    report = teacher.resolve_teacher_readout()
    assert report["terminal"] == teacher.STOP_READOUT_UNRESOLVED
    assert report["unique_authorized_cell_level_state"] is False
    assert report["healthy_trained_teacher_available"] is False
    assert report["teacher_gate_terminal"] == teacher.WAIT_HEALTHY_TEACHER
    assert teacher.teacher_gate_open(report) is False
    ids = {c["candidate_id"] for c in report["candidates"]}
    assert "encoder_cell_state" in ids
    # A multi-slot candidate exists, which is why no collapse may be invented.
    assert any(c["multi_slot"] for c in report["candidates"])
    assert report["frozen_representation_contract"] is None
    assert len(report["conflicts"]) >= 3
    statuses = {c["status"] for c in report["checkpoints"]}
    assert statuses <= {"UNTRAINED_U0", "TRAINING_MECHANICS_DEFECT_INHERITED"}


def test_the_50k_auxiliary_archive_is_present_but_classified_auxiliary() -> None:
    """It is real, it is reachable, and it still cannot set a production value."""
    path = _need_authority(audit.FORBIDDEN_PRODUCTION_INPUTS["auxiliary_50k_expression"])
    assert path.is_file()
    with pytest.raises(PermissionError, match="FORBIDDEN_PRODUCTION_INPUT"):
        audit.assert_not_forbidden_production_input(path)


def test_end_to_end_derivation_terminates_wait_healthy_trained_teacher() -> None:
    _need_authority(audit.CELL_METADATA_REL)
    report = derivation.derive(config_path=CONFIG, open_molecular=False)
    assert report["terminal"] == teacher.WAIT_HEALTHY_TEACHER
    assert report["production_parameter_emitted"] is False
    assert "TEACHER_GATE_CLOSED" in report["production_refusal"]
    # Provenance is honestly incomplete: no qualified healthy teacher exists, so
    # the teacher checkpoint root is absent. An earlier revision reported this
    # as production_provenance_ready=true, which was wrong.
    assert report["production_provenance_ready"] is False
    assert "teacher_checkpoint_root" in report["production_provenance_missing"]
    assert report["production_derivation_attempted"] is False
    assert "production_parameter" not in report
    assert report["no_synthetic_or_auxiliary_production_value_written"] is True
    assert len(report["teacher_dependent_parameters_withheld"]) >= 20


# ============================================================================
# Regressions for the defects found in external adversarial review
# ============================================================================
def _full_provenance_kwargs() -> dict:
    return dict(
        statistic_id="D1-P009:D", population_class=core.PRODUCTION_FULL_FIT,
        formula_version="v1", donors=104, cells=4553407, operators=42,
        teacher_checkpoint_root="a" * 64,
        teacher_readout_contract_hash="b" * 64,
        input_roots={"population_audit_root": "c" * 64,
                     "cell_metadata_authority_root": "d" * 64,
                     "loader_manifest_root": "e" * 64,
                     "split_registry_root": "f" * 64},
        firewall_evidence={"protected_rows_delivered": 0,
                           "lawful_partition": "reader_fit",
                           "donor_roster_verified": True})


def test_production_provenance_requires_every_mandatory_element() -> None:
    """Counts alone are not provenance.

    An earlier revision reported production_provenance_ready=true while the
    teacher checkpoint root was null and no frozen readout contract existed.
    Each mandatory element is removed in turn and must be named as missing.
    """
    full = _full_provenance_kwargs()
    assert core.D1Provenance(**full).is_production_eligible() is True

    for field, broken in (("teacher_checkpoint_root", None),
                          ("teacher_readout_contract_hash", None),
                          ("firewall_evidence", {})):
        partial = dict(full)
        partial[field] = broken
        provenance = core.D1Provenance(**partial)
        assert provenance.is_production_eligible() is False, field
        assert any(field in m for m in provenance.missing_production_provenance())

    for key in ("population_audit_root", "cell_metadata_authority_root",
                "loader_manifest_root", "split_registry_root"):
        partial = dict(full)
        roots = dict(partial["input_roots"])
        roots.pop(key)
        partial["input_roots"] = roots
        assert core.D1Provenance(**partial).is_production_eligible() is False, key

    # A root must be a real 64-hex digest, not a placeholder or a byte count.
    for bogus in ("2709786624", "not-a-hash", "A" * 63, ""):
        partial = dict(full)
        partial["teacher_checkpoint_root"] = bogus
        assert core.D1Provenance(**partial).is_production_eligible() is False, bogus

    # Firewall evidence that admits protected rows is refused.
    partial = dict(full)
    partial["firewall_evidence"] = {"protected_rows_delivered": 3,
                                    "lawful_partition": "reader_fit",
                                    "donor_roster_verified": True}
    assert core.D1Provenance(**partial).is_production_eligible() is False


def test_a_placeholder_production_value_is_refused_even_with_the_gate_open() -> None:
    """The exact future fail-open the review identified.

    With the gate forced open and complete provenance, emitting value=None must
    still fail. Previously that combination would have produced D=None and a
    terminal claiming the derivation was complete.
    """
    provenance = core.D1Provenance(**_full_provenance_kwargs())
    assert provenance.is_production_eligible() is True
    for bad in (None, float("nan"), float("inf"), [], ()):
        with pytest.raises(ValueError, match="VALUE_NOT_DERIVED"):
            core.emit_production_parameter(
                parameter_id="D1-P009:D", value=bad, provenance=provenance,
                teacher_gate_open=True, diagnostics={"D_PA": 3})
    # Diagnostics are mandatory: a bare number with no uncertainty is refused.
    with pytest.raises(ValueError, match="DIAGNOSTICS_MISSING"):
        core.emit_production_parameter(
            parameter_id="D1-P009:D", value=3, provenance=provenance,
            teacher_gate_open=True, diagnostics={})
    # The lawful case still succeeds, so this is discriminating.
    ok = core.emit_production_parameter(
        parameter_id="D1-P009:D", value=3, provenance=provenance,
        teacher_gate_open=True, diagnostics={"D_PA": 5, "separation_flags": [True]})
    assert ok["value"] == 3


def test_no_d1_source_emits_a_production_parameter_with_a_literal_none() -> None:
    """Structural guard so the placeholder path cannot be reintroduced."""
    for name in ("d1_parameter_derivation_v1.py", "d1_real_data_derivation_core_v1.py",
                 "d1_teacher_state_stream_v1.py", "d1_full_fit_population_audit_v1.py"):
        tree = ast.parse((SCRIPTS / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "emit_production_parameter"):
                for keyword in node.keywords:
                    if keyword.arg == "value":
                        assert not (isinstance(keyword.value, ast.Constant)
                                    and keyword.value.value is None), name


def test_an_unqualified_checkpoint_is_never_classified_healthy() -> None:
    """Unknown must not mean healthy.

    An earlier revision labelled any checkpoint outside the hardcoded
    prohibited/untrained update sets as UNCLASSIFIED and appended it to the
    healthy list, so dropping a new checkpoint into the manifest would have
    opened the gate with no review at all.
    """
    authority = teacher.load_teacher_qualification_authority()
    assert authority["present"] is False
    assert authority["qualified_checkpoint_roots"] == []
    assert authority["terminal"] == teacher.STOP_NO_QUALIFICATION_AUTHORITY
    report = teacher.resolve_teacher_readout()
    statuses = {c["status"] for c in report["checkpoints"]}
    assert "UNCLASSIFIED" not in statuses
    assert "QUALIFIED_HEALTHY" not in statuses
    assert statuses <= {"UNTRAINED_U0", "TRAINING_MECHANICS_DEFECT_INHERITED",
                        "UNQUALIFIED_NOT_HEALTHY"}
    assert report["healthy_trained_teacher_available"] is False


def test_qualification_entries_need_a_pass_terminal_and_a_readout_contract(
        tmp_path: Path, monkeypatch) -> None:
    """A digest alone cannot qualify a teacher."""
    payload = {"schema": "d1-teacher-qualification-v1", "qualified_teachers": [
        {"checkpoint_sha256": "1" * 64},
        {"checkpoint_sha256": "2" * 64, "review_terminal": "STOP_X",
         "readout_contract_hash": "9" * 64},
        {"checkpoint_sha256": "3" * 64, "review_terminal": "PASS_REVIEW"},
        {"checkpoint_sha256": "4" * 64, "review_terminal": "PASS_REVIEW",
         "readout_contract_hash": "9" * 64},
    ]}
    target = tmp_path / "docs" / "agent"
    target.mkdir(parents=True)
    (target / "D1_TEACHER_QUALIFICATION_AUTHORITY.json").write_text(
        json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(teacher, "AUTHORITY_ROOTS", (tmp_path,))
    authority = teacher.load_teacher_qualification_authority()
    assert authority["present"] is True
    assert authority["qualified_checkpoint_roots"] == ["4" * 64]
    assert len(authority["rejected_entries"]) == 3


def test_the_production_readout_seam_refuses_rather_than_guessing() -> None:
    report = teacher.resolve_teacher_readout()
    with pytest.raises(PermissionError, match="TEACHER_READOUT_UNRESOLVED"):
        derivation.resolve_production_readout(report)


def test_roster_identity_mismatch_stops(tmp_path: Path) -> None:
    """Totals alone would admit a different 104-donor population."""
    path = tmp_path / "roster.csv"
    rows = ["donor_id,reader_partition"]
    rows += ["D%03d,reader_fit" % i for i in range(103)]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="FIT_DONOR_ROSTER_MISMATCH"):
        audit.read_frozen_reader_roster(path)


def test_normalization_proof_rejects_a_tampered_loader() -> None:
    """The transform is proven from the loader, not asserted in the output."""
    genuine = ("library = x\n"
               "normalized = matrix.multiply((10_000.0 / np.maximum(library, 1.0))[:, None]).tocsr()\n"
               "normalized.data = np.log1p(normalized.data)\n")
    digest = core.LOADER_SOURCE_SHA256
    with pytest.raises(AssertionError, match="NOT_PROVEN_FROM_LOADER"):
        core.verify_normalization_from_loader_source(genuine, source_sha256="0" * 64)
    doubled = genuine + "normalized.data = np.log1p(normalized.data)\n"
    with pytest.raises(AssertionError, match="log1p appears 2 times"):
        core.verify_normalization_from_loader_source(doubled, source_sha256=digest)
    dense = genuine.replace("normalized.data = np.log1p(normalized.data)",
                            "normalized = np.log1p(normalized.todense())")
    with pytest.raises(AssertionError, match="sparse"):
        core.verify_normalization_from_loader_source(dense, source_sha256=digest)
    unguarded = genuine.replace("np.maximum(library, 1.0)", "library")
    with pytest.raises(AssertionError, match="library divisor guard"):
        core.verify_normalization_from_loader_source(unguarded, source_sha256=digest)
    assert core.verify_normalization_from_loader_source(
        genuine, source_sha256=digest)["applied_times"] == 1


def test_missing_mandatory_authority_stops(tmp_path: Path, monkeypatch) -> None:
    """A controlling authority may not simply vanish from the report.

    An earlier revision hashed each authority only if it happened to be
    available, so a missing loader manifest or split registry disappeared from
    the output while the audit still returned PASS.
    """
    monkeypatch.setattr(audit, "AUTHORITY_ROOTS", (tmp_path,))
    with pytest.raises(FileNotFoundError, match="AUTHORITY_UNREACHABLE"):
        audit.verify_mandatory_authorities(include_molecular=False)


def test_present_but_wrong_authority_is_a_digest_stop(tmp_path: Path, monkeypatch) -> None:
    for relative, _expected in audit.MANDATORY_AUTHORITIES.values():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"tampered")
    monkeypatch.setattr(audit, "AUTHORITY_ROOTS", (tmp_path,))
    with pytest.raises(AssertionError, match="AUTHORITY_DIGEST_MISMATCH"):
        audit.verify_mandatory_authorities(include_molecular=False)


def test_the_sqlite_authority_is_bound_by_content_digest_not_byte_count() -> None:
    """Its content identity is what establishes the 4.55-million-cell population."""
    expected = audit.MANDATORY_AUTHORITIES["cell_metadata_sqlite"][1]
    assert len(expected) == 64
    assert all(c in "0123456789abcdef" for c in expected)


def test_the_streaming_source_refuses_unlawful_strata_and_bad_shapes() -> None:
    counts = {("A", 0): 20, ("A", 1): 10, ("B", 0): 15}

    def readout(donor, operator, n):
        return np.zeros((n, 3))

    source = teacher.LawfulFitStrataSource(
        donor_operator_counts=counts, readout=readout,
        population_class=core.MECHANICS_ONLY, dimension=3)
    assert source.total_cells() == 45
    assert source.strata() == [("A", 0), ("A", 1), ("B", 0)]
    states, weights = source.load("A", 1)
    # Donor A has two operators, so a_dc = 1/(2 * 10) for operator 1.
    assert states.shape == (10, 3)
    assert float(weights[0]) == pytest.approx(1.0 / (2 * 10))
    with pytest.raises(PermissionError, match="PROTECTED_POPULATION_ACCESS"):
        source.load("C", 0)

    def wrong_shape(donor, operator, n):
        return np.zeros((n, 5))

    bad = teacher.LawfulFitStrataSource(
        donor_operator_counts=counts, readout=wrong_shape,
        population_class=core.MECHANICS_ONLY, dimension=3)
    with pytest.raises(ValueError, match="READOUT_SHAPE"):
        bad.load("A", 0)


def test_the_streamer_requires_a_source_and_matching_population_class() -> None:
    counts = {("A", 0): 8}

    def readout(donor, operator, n):
        return np.zeros((n, 2))

    source = teacher.LawfulFitStrataSource(
        donor_operator_counts=counts, readout=readout,
        population_class=core.MECHANICS_ONLY, dimension=2)
    with pytest.raises(PermissionError, match="TEACHER_READOUT_UNRESOLVED"):
        next(teacher.iter_teacher_states(population_class=core.MECHANICS_ONLY, source=None))
    with pytest.raises(PermissionError, match="POPULATION_CLASS_MISMATCH"):
        next(teacher.iter_teacher_states(population_class=core.PRODUCTION_FULL_FIT,
                                         source=source,
                                         report={"unique_authorized_cell_level_state": True,
                                                 "healthy_trained_teacher_available": True}))
    chunks = list(teacher.iter_teacher_states(
        population_class=core.MECHANICS_ONLY, chunk_size=3, source=source))
    assert [c[0].shape[0] for c in chunks] == [3, 3, 2]


def test_a_production_strata_source_cannot_be_built_while_the_gate_is_closed() -> None:
    with pytest.raises(PermissionError, match="TEACHER_READOUT_UNRESOLVED"):
        teacher.build_production_strata_source(
            donor_operator_counts={("A", 0): 4},
            readout=lambda d, o, n: np.zeros((n, 2)), dimension=2)


def test_config_validation_fails_closed_on_an_incomplete_parse(tmp_path: Path) -> None:
    """A validator that parsed almost nothing must not report a clean result.

    The fallback parser exists so the config can be checked without PyYAML, and
    a fallback that mis-parsed would fail open precisely here.
    """
    stub = tmp_path / "tiny.yaml"
    stub.write_text("schema: d1\npopulation:\n  expected_fit_donors: 104\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="NOT_FULLY_PARSED"):
        derivation.validate_config_has_no_production_values(stub)
    # The genuine config parses completely and names every required section.
    out = derivation.validate_config_has_no_production_values(CONFIG)
    assert out["keys_checked"] >= 30
    assert "monte_carlo" in out["sections_present"]


def test_the_production_derivation_fails_closed_on_an_unresolved_dimension() -> None:
    """Even with a forced-open gate the derivation cannot proceed on guesses."""
    forced = {"unique_authorized_cell_level_state": True,
              "healthy_trained_teacher_available": True,
              "conflicts": [], "readout_contract_hash": "a" * 64}
    with pytest.raises(AssertionError, match="READOUT_DIMENSION_UNRESOLVED"):
        derivation.run_production_D_derivation(
            audit={"observed": {"donors": 104, "cells": 4553407, "operators": 42}},
            readout=forced, config_path=CONFIG)


def test_a_collision_unresolved_address_does_not_count_as_measured() -> None:
    """Only MEASURED_SCALAR is a lawful measured value.

    An address whose operator state is MEASURED_COLLISION_UNRESOLVED has no
    unambiguous scalar, so it must contribute no measured mass rather than
    being treated as a measured zero.
    """
    n = 40
    scores = np.linspace(-1.0, 1.0, n).reshape(n, 1)
    expression = np.full((n, 1), 3.0)
    state = np.full((n, 1), core.COLLISION_UNRESOLVED, dtype=np.uint8)
    acc = core.MolecularAssociationAccumulator(programs=1, addresses=1)
    acc.update(scores=scores, expression=expression, observation_state=state,
               weights=np.ones(n))
    out = acc.effects()
    assert out["measured_mass"][0][0] == 0.0
    assert bool(out["not_estimable"][0][0]) is True
    assert np.isnan(out["effect"][0][0])


# ------------------------------------------------------------------ meta-test
def test_authority_dependent_declaration_matches_the_ast() -> None:
    """The declared NOT_MEASURABLE set must match reality, or a reader miscounts."""
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    actual = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            for inner in ast.walk(node):
                if (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name)
                        and inner.func.id == "_need_authority"):
                    actual.add(node.name)
    assert actual == set(AUTHORITY_DEPENDENT_TESTS), {
        "undeclared": sorted(actual - set(AUTHORITY_DEPENDENT_TESTS)),
        "declared_but_independent": sorted(set(AUTHORITY_DEPENDENT_TESTS) - actual),
    }
