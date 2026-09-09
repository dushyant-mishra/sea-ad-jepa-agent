import json
from pathlib import Path

PATH=Path(__file__).resolve().parents[1]/"docs"/"agent"/"v5_anticheat"/"results"/"V5_GROUP_PRESENTATION_FLOOR_RELEVANCE_DIAGNOSTIC_V1.json"
OBJ=json.loads(PATH.read_text())

def test_full_coverage_makes_zero_hit_rationale_obsolete():
    assert OBJ["population"]["minimum_unique_cells_per_group"]==1
    assert OBJ["population"]["groups_with_fewer_than_16_unique_cells"]==192
    assert "zero probability" in OBJ["new_full_coverage_fact"]

def test_repeats_are_not_independent_biology():
    assert "one unique biological cell" in OBJ["independence_warning"]
    assert OBJ["real_schedule_comparison"]["extra_presentations_due_to_retaining_floor16_at_final_optimum"]==334
    assert OBJ["decision_boundary"]["floor16_remains_training_authority"] is False
    assert OBJ["synthetic_data_used"] is False
