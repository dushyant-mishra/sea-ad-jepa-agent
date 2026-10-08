from __future__ import annotations

import json
from pathlib import Path


def test_t1_trajectory_review_binds_full_update_range_and_loss_drop():
    root = Path(__file__).resolve().parents[2]
    data = json.loads((root / 'docs' / 'agent' / 'v5_anticheat' / 'results' / 'T1_TRAJECTORY_JSON_REVIEW_V1.json').read_text())
    assert data['input_schema'] == 'prod41k-t1-trajectory-v2'
    assert data['update_count'] == 205
    assert data['first_update'] == 1
    assert data['last_update'] == 205
    assert data['loss']['u1_to_u205_pct_reduction'] > 0.99
    assert data['loss']['u205'] < data['loss']['u1']


def test_t1_trajectory_review_refuses_loss_only_authority():
    root = Path(__file__).resolve().parents[2]
    data = json.loads((root / 'docs' / 'agent' / 'v5_anticheat' / 'results' / 'T1_TRAJECTORY_JSON_REVIEW_V1.json').read_text())
    decision = data['authority_decision']
    assert decision['historical_u10_to_u205_resume_authority'] is False
    assert decision['historical_u10_to_u205_biological_teacher_authority'] is False
    assert decision['loss_decrease_is_not_biological_qualification'] is True
    assert decision['requires_48_tensor_elementwise_gradient_and_moment_gate'] is True


def test_t1_trajectory_review_records_aggregate_gradient_limitation():
    root = Path(__file__).resolve().parents[2]
    data = json.loads((root / 'docs' / 'agent' / 'v5_anticheat' / 'results' / 'T1_TRAJECTORY_JSON_REVIEW_V1.json').read_text())
    surface = data['gradient_component_surface']
    assert surface['missing_parameter_tensors_total'] == 0
    assert surface['nonfinite_parameter_tensors_total'] == 0
    assert 'cannot prove the 48 protected attention-routing tensors were live elementwise' in surface['limitation']
