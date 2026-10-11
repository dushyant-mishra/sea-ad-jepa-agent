import importlib.util
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / 'scripts/v5/td_target_tournament_scaffold.py'
sys.path.insert(0, str(MOD.parent))
import td_target_tournament_evidence as ev
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
        'candidate_specific_gates': {
            'C1_RELATIONAL_SHARED': ['R1_SCALE_FREE_RELATIONAL_RECURRENCE','R2_FINE_LOCALITY_NOT_PRIMARY','R3_MATCHED_WRONG_CELL_DEFEAT'],
            'C2_QUERY_MEASURED': ['Q1_Q_SCALAR_STUDENT_ABSENT','Q2_Q_EXCLUDED_TEACHER_ABLATION','Q3_TARGET_NORMALIZATION_Q_FREE','Q4_Q_COUNT_ONLY_DEFEAT','Q5_Q_ADDRESS_ONLY_DEFEAT'],
            'C3_LEARNED_SHARED': ['L1_LEARNED_TEACHER_VIEW_CONTINUITY','L2_CONDITIONAL_TECHNOLOGY_IMPRINT','L3_EVIDENCE_RESPONSE','L4_MEASUREMENT_DEPTH_RESPONSE','L5_COLLAPSE_SHORTCUT_DEFEAT','L6_IDENTITY_SUPPORT_BASELINE_DEFEAT'],
            'C4_STRUCTURED_COMPOSITE': ['C4_INCREMENT_OVER_CONSTITUENTS','L1_LEARNED_TEACHER_VIEW_CONTINUITY','L2_CONDITIONAL_TECHNOLOGY_IMPRINT','Q1_Q_SCALAR_STUDENT_ABSENT','Q2_Q_EXCLUDED_TEACHER_ABLATION','Q3_TARGET_NORMALIZATION_Q_FREE','Q5_Q_ADDRESS_ONLY_DEFEAT','L6_IDENTITY_SUPPORT_BASELINE_DEFEAT'],
            'C5_REGULATORY_SPECIALIST': ['M1_CIRCULARITY_CONTROL','M2_INDEPENDENT_PROVENANCE','M3_CAUSAL_CLAIM_FALSE','M4_SUPPORT_ABSTENTION'],
        },
    }


def required_gates(c, cid):
    return c['mandatory_gates'] + c['candidate_specific_gates'][cid]


def receipt(cid, *, status='PASS', score=1.0, gate_value=True):
    c = contract()
    return {
        'schema': 'JEPA_TD_TARGET_TOURNAMENT_CANDIDATE_RECEIPT_V1',
        'fixture': True,
        'candidate_id': cid,
        'status': status,
        'aggregate_score': score,
        'gates': {g: gate_value for g in required_gates(c, cid)},
        'authority': {
            'target_selected': False,
            'representation_selected': False,
            'stage4_authorized': False,
            'training_authorized': False,
            'value_read_authorized': False,
        },
    }


def evidence_manifest(c, r):
    cid = r['candidate_id']
    return {
        'schema': 'JEPA_TD_TARGET_TOURNAMENT_GATE_EVIDENCE_MANIFEST_V1',
        'fixture': True,
        'candidate_id': cid,
        'gates': {
            g: {
                'status': 'PASS' if r['gates'][g] else 'FAIL',
                'evidence_schema': ev.expected_evidence_schema(g),
                'evidence_sha256': (f'{i+1:x}' * 64)[:64],
            }
            for i, g in enumerate(required_gates(c, cid))
        },
        'authority': {
            'target_selected': False,
            'representation_selected': False,
            'stage4_authorized': False,
            'training_authorized': False,
            'value_read_authorized': False,
        },
    }


def bind(c, r, manifest=None):
    manifest = evidence_manifest(c, r) if manifest is None else manifest
    r['evidence_manifest_sha256'] = ev.canonical_manifest_sha256(manifest)
    return manifest


def adjudicate(c, rs, manifests=None):
    if manifests is None:
        manifests = {}
        for r in rs:
            mf = bind(c, r)
            manifests[r['candidate_id']] = mf
    return m.adjudicate(c, rs, manifests)


def test_contract_rejects_authority_true():
    c = contract(); c['authority']['training_authorized'] = True
    with pytest.raises(m.ContractError): m.validate_contract(c)


def test_contract_requires_exact_candidate_ids():
    c = contract(); c['candidate_ids'] = c['candidate_ids'][:-1]
    with pytest.raises(m.ContractError): m.validate_contract(c)


def test_mandatory_gate_failure_rejects_even_with_high_score():
    c = contract(); r = receipt('C1_RELATIONAL_SHARED', score=999.0); r['gates']['G3_SHORTCUT_DEFEAT'] = False
    out = adjudicate(c, [r])
    assert 'C1_RELATIONAL_SHARED' not in out['foundation_eligible']
    assert out['rejected']['C1_RELATIONAL_SHARED']['failed_gates'] == ['G3_SHORTCUT_DEFEAT']


def test_c5_is_never_foundation_candidate():
    c = contract(); out = adjudicate(c, [receipt('C5_REGULATORY_SPECIALIST')])
    assert out['foundation_eligible'] == []
    assert out['optional_specialists_eligible'] == ['C5_REGULATORY_SPECIALIST']
    assert out['target_selected'] is False


def test_no_passing_foundation_candidate_emits_redesign_terminal():
    c = contract(); rs = [receipt(cid, status='FAIL') for cid in c['foundation_candidate_ids']]
    out = adjudicate(c, rs)
    assert out['terminal'] == 'NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION'
    assert out['target_selected'] is False


def test_passing_foundation_candidates_only_become_selection_eligible():
    c = contract(); out = adjudicate(c, [receipt('C1_RELATIONAL_SHARED')])
    assert out['foundation_eligible'] == ['C1_RELATIONAL_SHARED']
    assert out['terminal'] == 'CANDIDATES_ELIGIBLE_FOR_TARGET_SELECTION__NO_TARGET_AUTHORITY'
    assert out['target_selected'] is False


def test_receipt_claiming_authority_is_rejected():
    c = contract(); r = receipt('C1_RELATIONAL_SHARED'); mf = bind(c, r); r['authority']['target_selected'] = True
    with pytest.raises(m.ReceiptError): m.adjudicate(c, [r], {'C1_RELATIONAL_SHARED': mf})


def test_contract_rejects_missing_authority_key():
    c = contract(); del c['authority']['training_authorized']
    with pytest.raises(m.ContractError): m.validate_contract(c)


def test_receipt_rejects_missing_authority_key():
    c = contract(); r = receipt('C1_RELATIONAL_SHARED'); mf = bind(c, r); del r['authority']['target_selected']
    with pytest.raises(m.ReceiptError): m.validate_candidate_receipt(r, c, mf)


def test_duplicate_candidate_receipts_rejected():
    c = contract(); r = receipt('C1_RELATIONAL_SHARED'); mf = bind(c, r)
    with pytest.raises(m.ReceiptError): m.adjudicate(c, [r, dict(r)], {'C1_RELATIONAL_SHARED': mf})


def test_learned_candidate_requires_conditional_technology_imprint_gate():
    c = contract(); r = receipt('C3_LEARNED_SHARED'); del r['gates']['L2_CONDITIONAL_TECHNOLOGY_IMPRINT']
    mf = evidence_manifest(c, receipt('C3_LEARNED_SHARED'))
    r['evidence_manifest_sha256'] = ev.canonical_manifest_sha256(mf)
    with pytest.raises(m.ReceiptError): m.validate_candidate_receipt(r, c, mf)


def test_query_candidate_specific_gate_failure_blocks_promotion():
    c = contract(); r = receipt('C2_QUERY_MEASURED', score=999.0); r['gates']['Q2_Q_EXCLUDED_TEACHER_ABLATION'] = False
    out = adjudicate(c, [r])
    assert 'C2_QUERY_MEASURED' not in out['foundation_eligible']
    assert out['rejected']['C2_QUERY_MEASURED']['failed_gates'] == ['Q2_Q_EXCLUDED_TEACHER_ABLATION']


def test_composite_requires_increment_over_constituents():
    c = contract(); r = receipt('C4_STRUCTURED_COMPOSITE'); r['gates']['C4_INCREMENT_OVER_CONSTITUENTS'] = False
    out = adjudicate(c, [r])
    assert 'C4_STRUCTURED_COMPOSITE' not in out['foundation_eligible']


def test_specialist_requires_independent_provenance():
    c = contract(); r = receipt('C5_REGULATORY_SPECIALIST'); r['gates']['M2_INDEPENDENT_PROVENANCE'] = False
    out = adjudicate(c, [r])
    assert out['optional_specialists_eligible'] == []


def test_query_candidate_requires_q_address_only_defeat():
    c = contract(); r = receipt('C2_QUERY_MEASURED'); r['gates']['Q5_Q_ADDRESS_ONLY_DEFEAT'] = False
    out = adjudicate(c, [r])
    assert 'C2_QUERY_MEASURED' not in out['foundation_eligible']


def test_learned_candidate_requires_identity_support_baseline_defeat():
    c = contract(); r = receipt('C3_LEARNED_SHARED'); r['gates']['L6_IDENTITY_SUPPORT_BASELINE_DEFEAT'] = False
    out = adjudicate(c, [r])
    assert 'C3_LEARNED_SHARED' not in out['foundation_eligible']


def test_receipt_requires_bound_evidence_manifest_sha():
    c = contract(); r = receipt('C1_RELATIONAL_SHARED'); mf = evidence_manifest(c, r)
    with pytest.raises(m.ReceiptError): m.validate_candidate_receipt(r, c, mf)


def test_missing_candidate_evidence_manifest_rejected():
    c = contract(); r = receipt('C1_RELATIONAL_SHARED'); bind(c, r)
    with pytest.raises(m.ReceiptError): m.adjudicate(c, [r], {})


def test_altered_evidence_manifest_after_binding_rejected():
    c = contract(); r = receipt('C1_RELATIONAL_SHARED'); mf = bind(c, r)
    first = required_gates(c, r['candidate_id'])[0]
    mf['gates'][first]['evidence_sha256'] = 'f' * 64
    with pytest.raises(m.ReceiptError): m.adjudicate(c, [r], {r['candidate_id']: mf})


def test_gate_boolean_must_match_evidence_status():
    c = contract(); r = receipt('C1_RELATIONAL_SHARED'); mf = bind(c, r)
    first = required_gates(c, r['candidate_id'])[0]
    mf['gates'][first]['status'] = 'FAIL'
    r['evidence_manifest_sha256'] = ev.canonical_manifest_sha256(mf)
    with pytest.raises(m.ReceiptError): m.adjudicate(c, [r], {r['candidate_id']: mf})


def test_not_estimable_evidence_cannot_project_to_passing_gate():
    c = contract(); r = receipt('C1_RELATIONAL_SHARED'); mf = evidence_manifest(c, r)
    first = required_gates(c, r['candidate_id'])[0]
    mf['gates'][first]['status'] = 'NOT_ESTIMABLE'
    r['gates'][first] = False
    r['evidence_manifest_sha256'] = ev.canonical_manifest_sha256(mf)
    out = m.adjudicate(c, [r], {r['candidate_id']: mf})
    assert r['candidate_id'] not in out['foundation_eligible']
    assert first in out['rejected'][r['candidate_id']]['failed_gates']
