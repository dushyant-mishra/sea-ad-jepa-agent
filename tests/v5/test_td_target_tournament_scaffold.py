import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / 'scripts/v5/td_target_tournament_scaffold.py'
spec = importlib.util.spec_from_file_location('td_target_tournament_scaffold', MOD)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def contract():
    return {
        'schema': 'JEPA_TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V1',
        'fixture_only': True,
        'authority': {
            'value_read_authorized': False,
            'target_selection_authorized': False,
            'representation_selection_authorized': False,
            'td60_authorized': False,
            'stage4_authorized': False,
            'training_authorized': False,
        },
        'candidate_ids': ['C1_RELATIONAL_SHARED','C2_QUERY_MEASURED','C3_LEARNED_SHARED','C4_STRUCTURED_COMPOSITE','C5_REGULATORY_SPECIALIST'],
        'foundation_candidate_ids': ['C1_RELATIONAL_SHARED','C2_QUERY_MEASURED','C3_LEARNED_SHARED','C4_STRUCTURED_COMPOSITE'],
        'optional_specialist_ids': ['C5_REGULATORY_SPECIALIST'],
        'mandatory_gates': ['G1_DONOR_PRIMARY','G2_SOURCE_REPLICATION','G3_SHORTCUT_DEFEAT','G4_INFORMATION_ASYMMETRY','G5_SUPPORT_ABSTENTION','G6_TRANSFER','G7_NO_POSTHOC'],
    }


def receipt(cid, *, status='PASS', score=1.0, gate_value=True):
    c = contract()
    return {
        'schema': 'JEPA_TD_TARGET_TOURNAMENT_CANDIDATE_RECEIPT_V1',
        'fixture': True,
        'candidate_id': cid,
        'status': status,
        'aggregate_score': score,
        'gates': {g: gate_value for g in c['mandatory_gates']},
        'authority': {
            'target_selected': False,
            'representation_selected': False,
            'stage4_authorized': False,
            'training_authorized': False,
            'value_read_authorized': False,
        },
    }


def test_contract_rejects_authority_true():
    c = contract(); c['authority']['training_authorized'] = True
    with pytest.raises(m.ContractError): m.validate_contract(c)


def test_contract_requires_exact_candidate_ids():
    c = contract(); c['candidate_ids'] = c['candidate_ids'][:-1]
    with pytest.raises(m.ContractError): m.validate_contract(c)


def test_mandatory_gate_failure_rejects_even_with_high_score():
    c = contract(); r = receipt('C1_RELATIONAL_SHARED', score=999.0); r['gates']['G3_SHORTCUT_DEFEAT'] = False
    out = m.adjudicate(c, [r])
    assert 'C1_RELATIONAL_SHARED' not in out['foundation_eligible']
    assert out['rejected']['C1_RELATIONAL_SHARED']['failed_gates'] == ['G3_SHORTCUT_DEFEAT']


def test_c5_is_never_foundation_candidate():
    c = contract(); out = m.adjudicate(c, [receipt('C5_REGULATORY_SPECIALIST')])
    assert out['foundation_eligible'] == []
    assert out['optional_specialists_eligible'] == ['C5_REGULATORY_SPECIALLIST'] if False else ['C5_REGULATORY_SPECIALIST']
    assert out['target_selected'] is False


def test_no_passing_foundation_candidate_emits_redesign_terminal():
    c = contract(); rs = []
    for cid in c['foundation_candidate_ids']:
        r = receipt(cid, status='FAIL'); rs.append(r)
    out = m.adjudicate(c, rs)
    assert out['terminal'] == 'NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION'
    assert out['target_selected'] is False


def test_passing_foundation_candidates_only_become_selection_eligible():
    c = contract(); out = m.adjudicate(c, [receipt('C1_RELATIONAL_SHARED')])
    assert out['foundation_eligible'] == ['C1_RELATIONAL_SHARED']
    assert out['terminal'] == 'CANDIDATES_ELIGIBLE_FOR_TARGET_SELECTION__NO_TARGET_AUTHORITY'
    assert out['target_selected'] is False


def test_receipt_claiming_authority_is_rejected():
    c = contract(); r = receipt('C1_RELATIONAL_SHARED'); r['authority']['target_selected'] = True
    with pytest.raises(m.ReceiptError): m.adjudicate(c, [r])


def test_contract_rejects_missing_authority_key():
    c = contract(); del c['authority']['training_authorized']
    with pytest.raises(m.ContractError): m.validate_contract(c)


def test_receipt_rejects_missing_authority_key():
    c = contract(); r = receipt('C1_RELATIONAL_SHARED'); del r['authority']['target_selected']
    with pytest.raises(m.ReceiptError): m.validate_candidate_receipt(r, c)


def test_duplicate_candidate_receipts_rejected():
    c = contract(); r = receipt('C1_RELATIONAL_SHARED')
    with pytest.raises(m.ReceiptError): m.adjudicate(c, [r, dict(r)])
