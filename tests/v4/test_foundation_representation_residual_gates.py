import json
from pathlib import Path

import pytest

from sea_ad_jepa.v4.foundation_residual_gates import (
    adjudicate_conditional_technology_imprint,
    adjudicate_heldout_donor_evidence,
    adjudicate_resource_benchmark,
    matrix_label_identifiability,
)


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
