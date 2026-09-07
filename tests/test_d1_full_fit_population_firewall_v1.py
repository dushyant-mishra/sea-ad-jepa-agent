"""Adversarial firewall tests for the D1 full-fit population and gates.

Proves that the 50,000-cell auxiliary sample, the historical 4,540-cell biology
cohort, synthetic fixtures, and any protected partition cannot become a
production D1 parameter, and that no production artifact can be emitted while
the teacher gate is closed.

Four checks need the calibration bundle, which is multi-gigabyte and untracked
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
    """Even a perfect production population cannot emit with the gate closed."""
    provenance = core.D1Provenance(
        statistic_id="D1-P009:D", population_class=core.PRODUCTION_FULL_FIT,
        formula_version="v1", donors=104, cells=4553407, operators=42)
    assert provenance.is_production_eligible() is True
    with pytest.raises(PermissionError, match="TEACHER_GATE_CLOSED"):
        core.emit_production_parameter(parameter_id="D1-P009:D", value=9,
                                       provenance=provenance, teacher_gate_open=False)
    # With the gate open the same call succeeds, so the test is discriminating
    # rather than passing because everything refuses.
    emitted = core.emit_production_parameter(parameter_id="D1-P009:D", value=9,
                                             provenance=provenance, teacher_gate_open=True)
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
    with pytest.raises(NotImplementedError):
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
    lawful = core.D1Provenance(
        statistic_id="D1-P002:donor_operator_cell_weights",
        population_class=core.PRODUCTION_FULL_FIT, formula_version="v1",
        donors=104, cells=4553407, operators=42)
    assert core.emit_production_parameter(
        parameter_id="D1-P002:donor_operator_cell_weights", value={"formula": "a_dc"},
        provenance=lawful, teacher_gate_open=True)["parameter_id"].startswith("D1-P002")


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
    # The protected partitions exist in the same authority and were not consumed.
    assert set(report["firewall"]["protected_partitions_present_in_authority"]) == {
        "reader_oracle", "reader_validation"}
    assert report["firewall"]["protected_rows_delivered"] == 0
    assert report["firewall"]["expression_opened"] is False
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
    # The population itself was production-eligible, so the teacher gate -- not
    # a population defect -- is what withheld the value.
    assert report["production_provenance_ready"] is True
    assert report["no_synthetic_or_auxiliary_production_value_written"] is True
    assert len(report["teacher_dependent_parameters_withheld"]) >= 20


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
