from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_v2_reaffirms_base_target_but_removes_operator_equal_mass_from_relational_target():
    p=json.loads((ROOT/'docs/agent/TEACHER_STUDENT_V5_SCIENTIFIC_TARGET_AUTHORITY_V2.json').read_text())
    assert p['status']=='SCIENTIFIC_TARGET_REPAIRED__PROPOSAL_AND_EXECUTION_UNFROZEN'
    assert p['base_jepa']['policy_id']=='DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1'
    assert p['base_jepa']['operator_sets_base_scientific_mass'] is False
    r=p['relational']
    assert r['policy_id']=='DONOR_UNIFORM__ELIGIBLE_ANCHOR_CELL_UNIFORM__SAME_OPERATOR_COMPARATOR_PAIR_UNIFORM_V2'
    assert r['operator_role']=='ADMISSIBILITY_BOUNDARY_ONLY__NOT_EQUAL_SCIENTIFIC_MASS'
    assert r['group_mass']=='eligible_cells_in_group / eligible_cells_in_donor'
    assert r['triplet_capacity_weighting']=='NONE_BEYOND_LINEAR_ANCHOR_PREVALENCE'
    assert r['triplet_budget'] is None
    assert p['training_authorized'] is False and p['execution_authorized'] is False


def test_operator_semantics_profile_proves_operator_is_not_common_scientific_axis():
    p=json.loads((ROOT/'docs/agent/READER_FIT_OPERATOR_SEMANTICS_PROFILE_V1.json').read_text())
    assert p['cells']==4_553_407 and p['donors']==104 and p['operators']==42
    assert p['cross_source_operator_semantics']['common_scientific_axis_established'] is False
    h=p['source_profiles']['HVS']; n=p['source_profiles']['NPH52']; s=p['source_profiles']['SEA_AD']
    assert h['operator_native_class_counts']['0']==1.0 and h['operator_native_class_counts']['1']==1.0
    assert n['operator_native_class_counts']['0']==1.0 and n['operator_native_class_counts']['1']==1.0
    assert s['operator_native_class_counts']['0']>=17.0 and s['operator_native_class_counts']['1']>=17.0
    assert p['eligible_cell_fraction'] > .99998
    assert p['per_donor_eligible_cell_fraction']['0'] > .998
    assert p['relational_weighting_diagnostic']['max_equal_group_upweight_vs_anchor'] > 100.0


def test_historical_td57b_td59_td60_qualification_is_not_rewritten_by_v2():
    p=json.loads((ROOT/'docs/agent/TEACHER_STUDENT_V5_SCIENTIFIC_TARGET_AUTHORITY_V2.json').read_text())
    q=p['qualification_boundary']
    assert q['TD57B']['executor_sha256']=='20ec39dcb00e781aff4149f97df8ad37d050e00c97cdb450bc1207a75d40af87'
    assert q['TD57B']['changed_by_v2'] is False
    assert q['TD59']['prospective_screen_sha256']=='ca356e6de74aecf1e486772ffd869796e2b5b68b79de86c53f499f6341dc061e'
    assert q['TD59']['changed_by_v2'] is False
    assert q['TD60']['uses_exact_frozen_TD57B_TD59_triplets'] is True and q['TD60']['changed_by_v2'] is False


def test_v1_target_remains_as_superseded_history_not_current_authority():
    old=json.loads((ROOT/'docs/agent/TEACHER_STUDENT_V5_SCIENTIFIC_TARGET_AUTHORITY_V1.json').read_text())
    new=json.loads((ROOT/'docs/agent/TEACHER_STUDENT_V5_SCIENTIFIC_TARGET_AUTHORITY_V2.json').read_text())
    assert new['supersedes'].endswith('TEACHER_STUDENT_V5_SCIENTIFIC_TARGET_AUTHORITY_V1.json')
    assert old['relational']['policy_id'] != new['relational']['policy_id']


def test_common_core_anchor_is_data_supported_but_numeric_schedule_unfrozen():
    p=json.loads((ROOT/'docs/agent/TEACHER_STUDENT_V5_COMMON_CORE_ANCHOR_CANDIDATE_V1.json').read_text())
    assert p['common_core']['addresses']==17186
    assert p['common_core']['csv_sha256']=='8aa8dfebb481aa2e60b12ab0f581ba1a36063b6c12dc2d8514d5fe7a20ad07ac'
    assert p['student_view_families']['COMMON_CORE_ANCHOR']['visible_gene_count'] is None
    assert p['student_view_families']['NATIVE_SUPPORT_COVERAGE']['visible_gene_count'] is None
    assert p['view_family_weights'] is None and p['views_per_family'] is None
    assert not (ROOT/'docs/agent/READER_FIT_COMMON_MEASURED_CORE_V1.csv').exists()
