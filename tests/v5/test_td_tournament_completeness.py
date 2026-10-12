import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts' / 'v5'
sys.path.insert(0, str(SCRIPTS))

import td_target_tournament_evidence as ev
import td_target_tournament_scaffold as sc


def contract():
    return {
        'schema': sc.CONTRACT_SCHEMA,
        'fixture_only': True,
        'authority': {k: False for k in sc.EXPECTED_CONTRACT_AUTHORITY_KEYS},
        'candidate_ids': list(sc.EXPECTED_CANDIDATES),
        'foundation_candidate_ids': list(sc.EXPECTED_FOUNDATION),
        'optional_specialist_ids': list(sc.EXPECTED_SPECIALISTS),
        'mandatory_gates': list(sc.EXPECTED_GATES),
        'claim_boundary': sc.CLAIM_BOUNDARY,
        'candidate_specific_gates': {
            k: list(v) for k, v in sc.EXPECTED_CANDIDATE_SPECIFIC_GATES.items()
        },
    }


def bound_candidate(cid, *, status='PASS', evidence_status='PASS'):
    c = contract()
    gates = c['mandatory_gates'] + c['candidate_specific_gates'][cid]
    manifest = {
        'schema': ev.SCHEMA,
        'fixture': True,
        'candidate_id': cid,
        'gates': {
            g: {
                'status': evidence_status,
                'evidence_schema': ev.expected_evidence_schema(g),
                'evidence_sha256': 'a' * 64,
            }
            for g in gates
        },
        'authority': {k: False for k in ev.EXPECTED_AUTHORITY_KEYS},
    }
    receipt = {
        'schema': sc.RECEIPT_SCHEMA,
        'fixture': True,
        'candidate_id': cid,
        'status': status,
        'aggregate_score': 0.0,
        'gates': {g: evidence_status == 'PASS' for g in gates},
        'evidence_manifest_sha256': ev.canonical_manifest_sha256(manifest),
        'authority': {k: False for k in sc.EXPECTED_RECEIPT_AUTHORITY_KEYS},
    }
    return receipt, manifest


def adjudicate(rows):
    receipts = []
    manifests = {}
    for cid, status, evidence_status in rows:
        receipt, manifest = bound_candidate(
            cid, status=status, evidence_status=evidence_status
        )
        receipts.append(receipt)
        manifests[cid] = manifest
    return sc.adjudicate(contract(), receipts, manifests)


def test_single_passing_foundation_candidate_is_individually_eligible_but_tournament_incomplete():
    out = adjudicate([('C1_RELATIONAL_SHARED', 'PASS', 'PASS')])
    assert out['foundation_eligible'] == ['C1_RELATIONAL_SHARED']
    assert out['tournament_complete'] is False
    assert out['missing_foundation_candidates'] == [
        'C2_QUERY_MEASURED', 'C3_LEARNED_SHARED', 'C4_STRUCTURED_COMPOSITE'
    ]
    assert out['terminal'] == (
        'TOURNAMENT_INCOMPLETE__FOUNDATION_CANDIDATES_MISSING__NO_TARGET_AUTHORITY'
    )


def test_empty_tournament_is_incomplete_not_redesign_failure():
    out = sc.adjudicate(contract(), [], {})
    assert out['foundation_eligible'] == []
    assert out['tournament_complete'] is False
    assert out['missing_foundation_candidates'] == list(sc.EXPECTED_FOUNDATION)
    assert out['terminal'] == (
        'TOURNAMENT_INCOMPLETE__FOUNDATION_CANDIDATES_MISSING__NO_TARGET_AUTHORITY'
    )


def test_all_foundation_candidates_evaluated_and_failed_can_emit_redesign_terminal():
    rows = [(cid, 'FAIL', 'FAIL') for cid in sc.EXPECTED_FOUNDATION]
    out = adjudicate(rows)
    assert out['tournament_complete'] is True
    assert out['missing_foundation_candidates'] == []
    assert out['terminal'] == 'NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION'
