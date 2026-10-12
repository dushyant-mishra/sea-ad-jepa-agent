import json
import sys
from copy import deepcopy
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts' / 'v5'
sys.path.insert(0, str(SCRIPTS))

import td_target_tournament_contract_v2 as v2

CONTRACT_PATH = ROOT / 'custody' / 'takeover_20261011' / 'TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V2.json'


def contract():
    return json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))


def test_frozen_v2_contract_validates():
    v2.validate_contract(contract())


def test_v1_candidate_identity_drift_is_rejected():
    c = contract()
    c['candidate_ids'][0] = 'C1_RELATIONAL_SHARED'
    with pytest.raises(v2.ContractV2Error):
        v2.validate_contract(c)


def test_c2_cannot_drop_any_c1_gate():
    c = contract()
    gate = c['candidate_gate_sets']['C1_SHARED_EMERGENT'][-1]
    c['candidate_gate_sets']['C2_RELATIONAL_SHARED'].remove(gate)
    with pytest.raises(v2.ContractV2Error):
        v2.validate_contract(c)


def test_c4_cannot_drop_relational_gate():
    c = contract()
    c['candidate_gate_sets']['C4_STRUCTURED_COMPOSITE'].remove(
        'R1_SCALE_FREE_RELATIONAL_RECURRENCE'
    )
    with pytest.raises(v2.ContractV2Error):
        v2.validate_contract(c)


def test_c4_cannot_drop_q_count_only_defeat():
    c = contract()
    c['candidate_gate_sets']['C4_STRUCTURED_COMPOSITE'].remove(
        'Q4_Q_COUNT_ONLY_DEFEAT'
    )
    with pytest.raises(v2.ContractV2Error):
        v2.validate_contract(c)


def test_c4_must_be_exact_union_of_c2_c3_plus_increment():
    c = contract()
    c['candidate_gate_sets']['C4_STRUCTURED_COMPOSITE'].append(
        'FAKE_ESCAPE_GATE'
    )
    with pytest.raises(v2.ContractV2Error):
        v2.validate_contract(c)


def test_c3_measured_target_does_not_silently_gain_learned_teacher_gate():
    c = contract()
    c['candidate_gate_sets']['C3_QUERY_MEASURED'].append(
        'G9_LEARNED_TEACHER_CONTINUITY'
    )
    with pytest.raises(v2.ContractV2Error):
        v2.validate_contract(c)


def test_specialist_cannot_enter_foundation_partition():
    c = contract()
    c['foundation_candidate_ids'].append('C5_REGULATORY_SPECIALIST')
    c['optional_specialist_ids'] = []
    with pytest.raises(v2.ContractV2Error):
        v2.validate_contract(c)


def test_any_authority_true_is_rejected():
    for key in contract()['authority']:
        c = contract(); c['authority'][key] = True
        with pytest.raises(v2.ContractV2Error):
            v2.validate_contract(c)


def test_contract_rejects_extra_shadow_field():
    c = contract(); c['target_selected'] = True
    with pytest.raises(v2.ContractV2Error):
        v2.validate_contract(c)


def test_spec_blob_identity_is_frozen():
    c = contract(); c['spec_git_blob_sha'] = '0' * 40
    with pytest.raises(v2.ContractV2Error):
        v2.validate_contract(c)
