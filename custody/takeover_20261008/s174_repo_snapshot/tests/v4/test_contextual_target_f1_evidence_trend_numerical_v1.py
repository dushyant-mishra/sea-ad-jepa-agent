from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = Path("D:/Jepa project")


def load(relative: str, name: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def baseline():
    path = AUTHORITY / "outputs/contextual_teacher_target_v1_f1_hc3_15c_decision_integration_20260902/F1_15C_SYNTHETIC_BASELINE.json"
    if not path.exists():
        pytest.skip("frozen synthetic authority not installed")
    return json.loads(path.read_text(encoding="utf-8"))


def test_exact_flat_rows_return_positive_zero_exactly():
    production = load("scripts/v4/contextual_target_f1_evidence_slope_v1.py", "evidence_slope_flat")
    for value in (1.0, 0.28, 0.0, -0.31):
        result = production.paired_difference_slope([value] * 5)
        assert result == 0.0
        assert np.signbit(result) is np.bool_(False)


def test_known_linear_rows_have_exact_expected_sign_and_value():
    production = load("scripts/v4/contextual_target_f1_evidence_slope_v1.py", "evidence_slope_linear")
    assert production.paired_difference_slope([0, 1, 2, 3, 4]) == 5.0
    assert production.paired_difference_slope([4, 3, 2, 1, 0]) == -5.0


@pytest.mark.parametrize("row", ([1, 2, 3, 4], [[1, 2, 3, 4, 5]], [1, 2, np.nan, 4, 5], [1, 2, np.inf, 4, 5], [1, 2, -np.inf, 4, 5]))
def test_malformed_or_nonfinite_rows_fail_closed(row):
    production = load("scripts/v4/contextual_target_f1_evidence_slope_v1.py", "evidence_slope_bad")
    with pytest.raises(ValueError):
        production.paired_difference_slope(row)


def test_independent_reference_is_separate_and_agrees():
    production = load("scripts/v4/contextual_target_f1_evidence_slope_v1.py", "evidence_slope_prod")
    independent = load("scripts/v4/validate_contextual_target_f1_evidence_trend_v1.py", "evidence_slope_ind")
    source = (ROOT / "scripts/v4/validate_contextual_target_f1_evidence_trend_v1.py").read_text(encoding="utf-8")
    assert "contextual_target_f1_evidence_slope_v1" not in source
    rows = np.random.default_rng(20260903).normal(size=(104, 5))
    actual = production.paired_difference_slopes(rows)
    expected = independent.independent_slopes(rows)
    assert np.allclose(actual, expected, rtol=0, atol=64 * np.finfo(np.float64).eps * np.maximum(1, np.max(np.abs(rows), axis=1)))
    assert np.array_equal(np.signbit(actual), np.signbit(expected))


def test_replace_layer_changes_only_evidence_report_gate_and_qualified():
    layer = load("scripts/v4/contextual_target_f1_evidence_trend_decision_v1.py", "evidence_layer_replace")
    accepted = {
        "qualified": False,
        "gates": {"legal_provenance": True, "evidence_trend_one_sided_positive": False, "hc3_nuisance_positive": True},
        "reports": {"evidence_slope": {"legacy": True}, "nuisance": {"method": "REDUCED_QR_TRIANGULAR_SOLVE_HC3"}, "other": {"kept": True}},
        "conclusion_bearing_hc3_method": "REDUCED_QR_TRIANGULAR_SOLVE_HC3",
    }
    evidence = np.column_stack([np.linspace(0.1, 0.2, 104) + j for j in range(5)])
    repaired = layer.replace_evidence_trend_only(accepted, evidence)
    assert repaired["gates"]["legal_provenance"] is True
    assert repaired["gates"]["hc3_nuisance_positive"] is True
    assert repaired["reports"]["nuisance"] == accepted["reports"]["nuisance"]
    assert repaired["reports"]["other"] == accepted["reports"]["other"]
    assert repaired["reports"]["evidence_slope"].get("legacy") is None
    assert repaired["qualified"] is all(repaired["gates"].values())


def test_full_layer_preserves_accepted_hc3_and_every_non_evidence_field():
    layer = load("scripts/v4/contextual_target_f1_evidence_trend_decision_v1.py", "evidence_layer_full")
    hc3 = load("scripts/v4/contextual_target_f1_hc3_15c_adapter_v2.py", "accepted_hc3_for_test")
    item = baseline()
    accepted = hc3.qualify_synthetic(item["payload"], authority_root=AUTHORITY, repo_root=ROOT)
    repaired = layer.qualify_synthetic(item["payload"], authority_root=AUTHORITY, repo_root=ROOT)
    for key in accepted["gates"]:
        if key != "evidence_trend_one_sided_positive":
            assert repaired["gates"][key] is accepted["gates"][key]
    for key in accepted["reports"]:
        if key != "evidence_slope":
            assert repaired["reports"][key] == accepted["reports"][key]
    assert repaired["reports"]["nuisance"] == accepted["reports"]["nuisance"]
    assert repaired["conclusion_bearing_hc3_method"] == "REDUCED_QR_TRIANGULAR_SOLVE_HC3"


def test_caller_supplied_evidence_gate_is_rejected():
    layer = load("scripts/v4/contextual_target_f1_evidence_trend_decision_v1.py", "evidence_layer_forged")
    item = copy.deepcopy(baseline()["payload"])
    item["evidence_trend_one_sided_positive"] = True
    with pytest.raises(ValueError):
        layer.qualify_synthetic(item, authority_root=AUTHORITY, repo_root=ROOT)


def test_flat_donor_varying_fixture_removes_legacy_defect():
    production = load("scripts/v4/contextual_target_f1_evidence_slope_v1.py", "evidence_slope_defect")
    values = np.linspace(0.1, 1.1, 104)
    rows = np.repeat(values[:, None], 5, axis=1)
    repaired = production.paired_difference_slopes(rows)
    assert np.array_equal(repaired, np.zeros(104))
    report = production.donor_trend_report(rows)
    assert report["estimable"] is False
    assert report["gate"] is False


def test_synthetic_runner_emits_complete_required_package_evidence():
    import shutil
    import tempfile

    runner = load("scripts/v4/run_contextual_target_f1_evidence_trend_repair_v1.py", "evidence_runner")
    scratch = ROOT / ".tmp"
    scratch.mkdir(exist_ok=True)
    frozen = ROOT / "outputs/contextual_teacher_target_v1_f1_evidence_trend_numerical_repair_20260903"
    with tempfile.TemporaryDirectory(prefix="evidence_trend_", dir=scratch) as temporary:
        out = Path(temporary)
        for name in ("F1_EVIDENCE_TREND_REPAIR_AUTHORITY_BINDING.json", "F1_EVIDENCE_TREND_REPAIR_HISTORICAL_HASH_BINDING.json"):
            shutil.copy2(frozen / name, out / name)
        result = runner.run(out, authority_root=AUTHORITY, repo_root=ROOT)
        required = {
            "F1_EVIDENCE_TREND_REPAIRED_SLOPE_RESULTS.json",
            "F1_EVIDENCE_TREND_INDEPENDENT_REFERENCE_RESULTS.json",
            "F1_EVIDENCE_TREND_NUMERICAL_COMPARISON.json",
            "F1_EVIDENCE_TREND_EXACT_FLAT_FIXTURE_BINDING.json",
            "F1_EVIDENCE_TREND_LINEAR_FIXTURE_BINDING.json",
            "F1_EVIDENCE_TREND_NEAR_BOUNDARY_FIXTURE_BINDING.json",
            "F1_EVIDENCE_TREND_LEGACY_DEFECT_DEMONSTRATION.json",
            "F1_EVIDENCE_TREND_COMPLETE_GATE_VECTOR_COMPARISON.json",
            "F1_EVIDENCE_TREND_REGRESSION_RESULTS.json",
            "F1_EVIDENCE_TREND_REPAIR_FIREWALL_AUDIT.json",
        }
        assert required <= {path.name for path in out.iterdir()}
        assert result["status"] == "PASS_F1_EVIDENCE_TREND_NUMERICAL_REPAIR"
        comparison = json.loads((out / "F1_EVIDENCE_TREND_NUMERICAL_COMPARISON.json").read_text())
        gates = json.loads((out / "F1_EVIDENCE_TREND_COMPLETE_GATE_VECTOR_COMPARISON.json").read_text())
        assert comparison["near_boundary"]["positive"]["production_gate"] is True
        assert comparison["near_boundary"]["negative"]["production_gate"] is False
        assert comparison["complete_gate_vector_exact"] is True
        assert gates["independent_gate_construction"] == "FROM_RAW_FROZEN_ENDPOINTS"
        assert gates["copied_production_gate_count"] == 0
        assert len(gates["gate_comparisons"]) == 11
        assert all(gates["gate_comparisons"].values())
        assert all(gates["deliberate_flipped_gate_attacks_detected"].values())
        assert len(gates["truth_table_attack_reconstruction"]) == 14
        assert gates["accepted_hc3_authority_reused"] is True
        assert gates["static_independence_audit"] == {
            "forbidden_construction_hits": [],
            "pass": True,
        }


def test_finalizer_builds_hash_bound_review_package():
    import shutil
    import tempfile

    runner = load("scripts/v4/run_contextual_target_f1_evidence_trend_repair_v1.py", "evidence_runner_finalize")
    finalizer = load("scripts/v4/finalize_contextual_target_f1_evidence_trend_repair_v1.py", "evidence_finalizer")
    scratch = ROOT / ".tmp"
    scratch.mkdir(exist_ok=True)
    frozen = ROOT / "outputs/contextual_teacher_target_v1_f1_evidence_trend_numerical_repair_20260903"
    with tempfile.TemporaryDirectory(prefix="evidence_finalize_", dir=scratch) as temporary:
        out = Path(temporary)
        for name in ("F1_EVIDENCE_TREND_REPAIR_AUTHORITY_BINDING.json", "F1_EVIDENCE_TREND_REPAIR_HISTORICAL_HASH_BINDING.json"):
            shutil.copy2(frozen / name, out / name)
        runner.run(out, authority_root=AUTHORITY, repo_root=ROOT)
        manifest_sha = finalizer.finalize(out, repo_root=ROOT)
        assert len(manifest_sha) == 64
        assert (out / "F1_EVIDENCE_TREND_REPAIR_SOURCE_MANIFEST.csv").exists()
        assert (out / "F1_EVIDENCE_TREND_REPAIR_MANIFEST.csv").exists()
        assert (out / "F1_EVIDENCE_TREND_REPAIR_PACKAGE_ROOT_SHA256.txt").read_text().split()[0] == manifest_sha
        handoff = (out / "F1_EVIDENCE_TREND_REPAIR_EXTERNAL_REVIEW_HANDOFF.md").read_text()
        assert "PASS_F1_EVIDENCE_TREND_NUMERICAL_REPAIR_AWAITING_EXTERNAL_REVIEW" in handoff
        assert "FROM_RAW_FROZEN_ENDPOINTS" in handoff
        assert "Copied production gates: `0`" in handoff
        assert "all 11" in handoff
        assert "flipped-gate attacks" in handoff


def test_authority_binding_verification_accepts_only_newline_transport_change():
    import tempfile

    runner = load("scripts/v4/run_contextual_target_f1_evidence_trend_repair_v1.py", "evidence_runner_crlf")
    scratch = ROOT / ".tmp"
    scratch.mkdir(exist_ok=True)
    frozen = ROOT / "outputs/contextual_teacher_target_v1_f1_evidence_trend_numerical_repair_20260903"
    with tempfile.TemporaryDirectory(prefix="evidence_crlf_", dir=scratch) as temporary:
        out = Path(temporary)
        for name in ("F1_EVIDENCE_TREND_REPAIR_AUTHORITY_BINDING.json", "F1_EVIDENCE_TREND_REPAIR_HISTORICAL_HASH_BINDING.json"):
            data = (frozen / name).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            (out / name).write_bytes(data)
        runner._verify_authorities(out, ROOT)


def test_complete_independent_adjudication_is_unchanged_by_flipped_production_gates():
    """Catches construction of independent gates by copying the accepted decision."""
    independent = load("scripts/v4/validate_contextual_target_f1_evidence_trend_v1.py", "evidence_complete_independent")
    hc3 = load("scripts/v4/contextual_target_f1_hc3_15c_adapter_v2.py", "evidence_complete_hc3")
    item = baseline()
    schema, _, _ = hc3.load_frozen_effective_design(AUTHORITY)
    accepted = hc3.qualify_synthetic(item["payload"], authority_root=AUTHORITY, repo_root=ROOT)
    expected = independent.independent_complete_adjudication(
        item["payload"],
        schema["donor_order"],
        accepted_hc3_report=accepted["reports"]["nuisance"],
        accepted_hc3_method=accepted["conclusion_bearing_hc3_method"],
    )
    assert len(expected["gates"]) == 11
    for gate in expected["gates"]:
        if gate == "evidence_trend_one_sided_positive":
            continue
        attacked = copy.deepcopy(accepted)
        attacked["gates"][gate] = not attacked["gates"][gate]
        repeated = independent.independent_complete_adjudication(
            item["payload"],
            schema["donor_order"],
            accepted_hc3_report=accepted["reports"]["nuisance"],
            accepted_hc3_method=accepted["conclusion_bearing_hc3_method"],
        )
        assert repeated == expected
        comparison = independent.compare_complete_adjudications(repeated, attacked)
        assert comparison["all_11_gate_comparisons"] is False
        assert comparison["gate_comparisons"][gate] is False


def _truth_payload_to_raw_synthetic(payload, donor_order):
    fields = (
        "overall_A", "program_A", "program_delta", "evidence_A", "qid_margin",
        "qid_win_minus_half", "program_qid_margin", "draw0", "draw1",
    )
    records = {}
    for index, donor in enumerate(donor_order):
        record = {}
        for field in fields:
            value = payload[field]
            if field.startswith("program_"):
                record[field] = {program: value[program][index] for program in value}
            else:
                record[field] = value[index]
        records[donor] = record
    return {"donor_records": records, "legal": payload["legal"]}


def test_independent_reconstruction_covers_all_applicable_frozen_truth_attacks():
    """Catches a validator that covers baseline but not the frozen attack surface."""
    independent = load("scripts/v4/validate_contextual_target_f1_evidence_trend_v1.py", "evidence_truth_independent")
    layer = load("scripts/v4/contextual_target_f1_evidence_trend_decision_v1.py", "evidence_truth_production")
    hc3 = load("scripts/v4/contextual_target_f1_hc3_15c_adapter_v2.py", "evidence_truth_hc3")
    truth = load("scripts/v4/test_contextual_target_f1_decision_truth_table_v2.py", "evidence_truth_authority")
    truth.v4.V1_SHA = truth.v4.sha(truth.v4.V1)
    truth.component.FROZEN_ASSIGNMENT_PATH = AUTHORITY / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv"
    frozen = truth.attacks()
    schema, _, _ = hc3.load_frozen_effective_design(AUTHORITY)
    donor_order = schema["donor_order"]
    baseline_raw = _truth_payload_to_raw_synthetic(frozen["base_payload"], donor_order)
    baseline_hc3 = hc3.qualify_synthetic(baseline_raw, authority_root=AUTHORITY, repo_root=ROOT)
    checked = []
    for attack in frozen["attacks"]:
        name = attack["attack"]
        if name == "G_hc3_nuisance":
            # Historical free-form nuisance columns were superseded by frozen 15C design.
            continue
        raw = _truth_payload_to_raw_synthetic(attack["payload"], donor_order)
        try:
            production = layer.qualify_synthetic(raw, authority_root=AUTHORITY, repo_root=ROOT)
        except (TypeError, ValueError):
            with pytest.raises((TypeError, ValueError)):
                independent.independent_complete_adjudication(
                    raw,
                    donor_order,
                    accepted_hc3_report=baseline_hc3["reports"]["nuisance"],
                    accepted_hc3_method=baseline_hc3["conclusion_bearing_hc3_method"],
                )
        else:
            result = independent.independent_complete_adjudication(
                raw,
                donor_order,
                accepted_hc3_report=production["reports"]["nuisance"],
                accepted_hc3_method=production["conclusion_bearing_hc3_method"],
            )
            comparison = independent.compare_complete_adjudications(result, production)
            assert comparison["all_11_gate_comparisons"] is True, name
            assert comparison["qualified_comparison"] is True, name
        checked.append(name)
    assert len(checked) == 13
