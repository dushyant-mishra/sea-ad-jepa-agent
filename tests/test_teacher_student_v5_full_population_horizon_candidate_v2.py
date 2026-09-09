import json
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'docs'/'agent'/'TEACHER_STUDENT_V5_FULL_POPULATION_HORIZON_CANDIDATE_V2.json'

def test_candidate_records_exact_conflict_and_does_not_authorize_training():
    obj=json.loads(PATH.read_text())
    assert obj['status']=='PROSPECTIVE_SUPERSESSION_CANDIDATE__NO_TRAINING_AUTHORITY'
    c=obj['v1_constraint_proven_incompatible_with_full_unique_cell_coverage']
    assert Fraction(c['dataset_and_cap_lower_bound_numerator'],c['dataset_and_cap_lower_bound_denominator'])==Fraction(58037,864)
    assert c['old_max_importance_weight_max_to_min_ratio']==64.0
    assert c['old_64x_rule_feasible'] is False
    assert c['minimum_integer_cell_cap_if_64x_were_retained']==34
    assert obj['training_authorized'] is False
    assert obj['successor_u0_authorized'] is False
    assert obj['td60_authorized'] is False

def test_candidate_keeps_science_mass_and_key_conditioning_constraints():
    obj=json.loads(PATH.read_text())
    assert obj['immutable_scientific_target']=='DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1'
    p=obj['v1_constraints_preserved']
    assert p['minimum_donor_operator_group_presentations']==16
    assert p['maximum_presentations_per_cell']==32
    assert p['minimum_importance_ess_fraction']==0.5
    assert p['exact_p_over_q_correction_required'] is True
    s=obj['candidate_horizon_semantics']
    assert s['checkpoint_outcomes_used_to_choose_schedule'] is False
    assert s['pathology_used_to_choose_schedule'] is False
    assert s['automatic_extension'] is False
