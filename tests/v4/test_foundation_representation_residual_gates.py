import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "sea_ad_jepa" / "v4" / "foundation_residual_gates.py"
SCRIPT = ROOT / "scripts" / "v4" / "audit_foundation_representation_residual_gates_v1.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("foundation_residual_gates", MODULE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


G = _load_module()
matrix_label_identifiability = G.matrix_label_identifiability
adjudicate_heldout_donor_evidence = G.adjudicate_heldout_donor_evidence
adjudicate_conditional_technology_imprint = G.adjudicate_conditional_technology_imprint
adjudicate_resource_benchmark = G.adjudicate_resource_benchmark
adjudicate_successor_donor_transfer = G.adjudicate_successor_donor_transfer
adjudicate_successor_matrix_transfer = G.adjudicate_successor_matrix_transfer
adjudicate_successor_conditional_technology = G.adjudicate_successor_conditional_technology


def test_matrix_identifiability_is_leave_one_matrix_out_and_reports_missing_broad_labels():
    rows = [
        {"matrix_id":"A","source":"S1","native_class":"x","broad_class":"B1"},
        {"matrix_id":"A","source":"S1","native_class":"unique","broad_class":"B2"},
        {"matrix_id":"B","source":"S1","native_class":"x","broad_class":"B1"},
        {"matrix_id":"C","source":"S2","native_class":"z","broad_class":""},
    ]
    out = {r["matrix_id"]: r for r in matrix_label_identifiability(rows)}
    assert out["A"]["native_cell_coverage_seen_elsewhere"] == pytest.approx(0.5)
    assert out["A"]["unseen_native_labels"] == ["unique"]
    assert out["C"]["broad_label_available_fraction"] == 0.0
    assert out["C"]["broad_label_identifiability"] == "UNAVAILABLE"


def test_heldout_donor_evidence_stays_non_authorizing_without_prefrozen_pass_threshold():
    rows = [
        {"checkpoint":"u205","representation":"rich_H","target":"source","evaluation":"45 heldout TRAIN donors","metric":"balanced_accuracy","value":"1.0","u205_minus_u0":"0"},
        {"checkpoint":"u205","representation":"rich_H","target":"operator","evaluation":"45 heldout TRAIN donors","metric":"balanced_accuracy","value":"0.763206","u205_minus_u0":"0.008"},
        {"checkpoint":"u205","representation":"rich_H","target":"support_measured_count","evaluation":"45 heldout TRAIN donors","metric":"R2","value":"0.9998","u205_minus_u0":"-0.0000045"},
        {"checkpoint":"u205","representation":"rich_H","target":"broad_annotation","evaluation":"45 heldout TRAIN donors","metric":"balanced_accuracy","value":"0.495018","u205_minus_u0":"0.004386729"},
    ]
    out = adjudicate_heldout_donor_evidence(rows)
    assert out["heldout_donors"] == 45
    assert out["source_balanced_accuracy"] == pytest.approx(1.0)
    assert out["broad_annotation_balanced_accuracy"] == pytest.approx(0.495018)
    assert out["donor_transfer_qualified"] is False
    assert out["terminal"] == "CURRENT_HELDOUT_DONOR_EVIDENCE_AVAILABLE__NO_PREFROZEN_PASS_THRESHOLD__NOT_FREEZE_QUALIFIED"


def test_conditional_technology_imprint_preserves_fit_population_scope_and_blocks_invariance_claim():
    out = adjudicate_conditional_technology_imprint({
        "scope":"AUTHENTICATED_84_CELL_TRUTH_TABLE__FIT_POPULATION_ONLY",
        "grouping":"DONOR_GROUPED_5_FOLD_CV",
        "raw_source_balanced_accuracy":1.0,
        "comparable_biology_cells":68,
        "broad_class_only_balanced_accuracy":0.5895833333333333,
        "broad_class_plus_state_balanced_accuracy":1.0,
        "within_shared_broad_class_balanced_accuracy":{"GABA":1.0,"GLUT":1.0,"NONNEURONAL":1.0},
    })
    assert out["residual_source_increment_over_broad_class"] == pytest.approx(0.4104166666666667)
    assert out["technology_invariance_qualified"] is False
    assert out["heldout_transfer_authority"] is False
    assert "FIT_POPULATION" in out["terminal"]


def test_cpu_resource_benchmark_cannot_satisfy_final_production_gpu_gate():
    out = adjudicate_resource_benchmark({
        "device":"cpu","vocabulary_size":41238,"width":160,"checkpoint_update":205,
        "measurements":[
            {"cells":1,"inference_seconds":1.03,"peak_rss_kib":771468},
            {"cells":4,"inference_seconds":4.52,"peak_rss_kib":1628044},
            {"cells":12,"inference_seconds":14.36,"peak_rss_kib":1733368},
        ]
    })
    assert out["bounded_cpu_resource_evidence"] is True
    assert out["final_production_resource_gate_pass"] is False
    assert out["recommended_cpu_batch_ceiling"] == 4
    assert out["training_authorized"] is False


def test_successor_donor_contract_uses_prefrozen_permutation_envelopes_not_posthoc_numeric_margin():
    rec = {
        "contract_frozen_before_candidate_evaluation": True,
        "scope": "HELDOUT_TRAIN_DONORS",
        "biology_observed": 0.61,
        "biology_permutation_q95": 0.42,
        "source_residual_observed": 0.08,
        "source_residual_permutation_q95": 0.10,
        "operator_residual_observed": 0.09,
        "operator_residual_permutation_q95": 0.11,
        "support_residual_observed": 0.02,
        "support_residual_permutation_q95": 0.03,
    }
    out = adjudicate_successor_donor_transfer(rec)
    assert out["donor_transfer_qualified"] is True
    assert out["training_authorized"] is False
    rec["source_residual_observed"] = 0.2
    assert adjudicate_successor_donor_transfer(rec)["donor_transfer_qualified"] is False


def test_successor_donor_contract_refuses_retrospective_freeze():
    with pytest.raises(ValueError, match="must be frozen before"):
        adjudicate_successor_donor_transfer({"contract_frozen_before_candidate_evaluation": False})


def test_successor_matrix_contract_reports_identifiability_and_requires_every_evaluable_matrix_to_beat_null_without_identity_leakage():
    rows = [
        {"matrix_id":"A","total_cells":100,"eligible_cells":90,"biology_observed":0.7,"biology_permutation_q95":0.4,"matrix_residual_observed":0.08,"matrix_residual_permutation_q95":0.1},
        {"matrix_id":"B","total_cells":100,"eligible_cells":50,"biology_observed":0.6,"biology_permutation_q95":0.45,"matrix_residual_observed":0.07,"matrix_residual_permutation_q95":0.09},
        {"matrix_id":"C","total_cells":100,"eligible_cells":0,"biology_observed":None,"biology_permutation_q95":None,"matrix_residual_observed":None,"matrix_residual_permutation_q95":None},
    ]
    out = adjudicate_successor_matrix_transfer(rows, contract_frozen_before_candidate_evaluation=True)
    assert out["identifiable_cell_fraction"] == pytest.approx(140/300)
    assert out["evaluable_matrices"] == 2
    assert out["nonidentifiable_matrices"] == ["C"]
    assert out["matrix_transfer_qualified"] is True
    rows[1]["biology_observed"] = 0.3
    assert adjudicate_successor_matrix_transfer(rows, contract_frozen_before_candidate_evaluation=True)["matrix_transfer_qualified"] is False


def test_successor_conditional_technology_contract_requires_heldout_scope_and_no_state_increment_beyond_permutation_envelope():
    rec = {
        "contract_frozen_before_candidate_evaluation": True,
        "scope": "HELDOUT_DONORS_OR_HELDOUT_MATRICES",
        "biology_observed": 0.65,
        "biology_permutation_q95": 0.44,
        "biology_control_source_score": 0.58,
        "biology_plus_state_source_score": 0.60,
        "source_increment_permutation_q95": 0.03,
    }
    out = adjudicate_successor_conditional_technology(rec)
    assert out["residual_source_increment"] == pytest.approx(0.02)
    assert out["technology_invariance_qualified"] is True
    rec["biology_plus_state_source_score"] = 0.75
    assert adjudicate_successor_conditional_technology(rec)["technology_invariance_qualified"] is False


def _load_cli():
    spec = importlib.util.spec_from_file_location("foundation_residual_cli", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_residual_cli_hash_binds_inputs_and_refuses_authority(tmp_path: Path):
    m = _load_cli()
    sample = tmp_path / "sample.csv"
    sample.write_text("matrix_id,source,native_class,broad_class,donor_id\nA,S1,x,B1,d1\nB,S1,x,B1,d2\n", encoding="utf-8")
    atlas = tmp_path / "atlas.csv"
    atlas.write_text(
        "checkpoint,representation,target,evaluation,metric,value,u205_minus_u0\n"
        "u205,rich_H,source,45 heldout TRAIN donors,balanced_accuracy,1.0,0\n"
        "u205,rich_H,operator,45 heldout TRAIN donors,balanced_accuracy,0.76,0.01\n"
        "u205,rich_H,support_measured_count,45 heldout TRAIN donors,R2,0.99,0\n"
        "u205,rich_H,broad_annotation,45 heldout TRAIN donors,balanced_accuracy,0.49,0.004\n",
        encoding="utf-8",
    )
    tech = tmp_path / "tech.json"; tech.write_text(json.dumps({"scope":"AUTHENTICATED_84_CELL_TRUTH_TABLE__FIT_POPULATION_ONLY","broad_class_only_balanced_accuracy":0.59,"broad_class_plus_state_balanced_accuracy":1.0}), encoding="utf-8")
    resource = tmp_path / "resource.json"; resource.write_text(json.dumps({"device":"cpu","measurements":[{"cells":1},{"cells":4},{"cells":12}]}), encoding="utf-8")
    out = tmp_path / "out.json"; matrix = tmp_path / "matrix.csv"
    rec = m.run(sample, atlas, tech, resource, out, matrix)
    assert rec["training_authorized"] is False
    assert rec["representation_freeze_authorized"] is False
    assert rec["input_sha256"]["sample_freeze"] == m.sha256_file(sample)
    assert matrix.exists()
    with pytest.raises(FileExistsError):
        m.run(sample, atlas, tech, resource, out, matrix)
