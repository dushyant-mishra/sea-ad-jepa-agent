import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts' / 'v5'
sys.path.insert(0, str(SCRIPTS))

import td_target_tournament_evidence as ev
import td_target_tournament_scaffold as sc
import td_target_tournament_prefreeze as pf


def contract():
    return {
        'schema': 'JEPA_TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V1',
        'fixture_only': True,
        'authority': {k: False for k in sc.EXPECTED_CONTRACT_AUTHORITY_KEYS},
        'candidate_ids': list(sc.EXPECTED_CANDIDATES),
        'foundation_candidate_ids': list(sc.EXPECTED_FOUNDATION),
        'optional_specialist_ids': list(sc.EXPECTED_SPECIALISTS),
        'mandatory_gates': list(sc.EXPECTED_GATES),
        'claim_boundary': 'SYNTHETIC_SCAFFOLD_ONLY__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY',
        'candidate_specific_gates': {k: list(v) for k, v in sc.EXPECTED_CANDIDATE_SPECIFIC_GATES.items()},
    }


def evidence_manifest(cid='C1_RELATIONAL_SHARED'):
    c = contract()
    gates = c['mandatory_gates'] + c['candidate_specific_gates'][cid]
    return {
        'schema': ev.SCHEMA,
        'fixture': True,
        'candidate_id': cid,
        'gates': {
            g: {
                'status': 'PASS',
                'evidence_schema': ev.expected_evidence_schema(g),
                'evidence_sha256': 'a' * 64,
            }
            for g in gates
        },
        'authority': {k: False for k in ev.EXPECTED_AUTHORITY_KEYS},
    }


def receipt(cid='C1_RELATIONAL_SHARED', score=1.0):
    c = contract()
    mf = evidence_manifest(cid)
    gates = c['mandatory_gates'] + c['candidate_specific_gates'][cid]
    return c, mf, {
        'schema': sc.RECEIPT_SCHEMA,
        'fixture': True,
        'candidate_id': cid,
        'status': 'PASS',
        'aggregate_score': score,
        'gates': {g: True for g in gates},
        'evidence_manifest_sha256': ev.canonical_manifest_sha256(mf),
        'authority': {k: False for k in sc.EXPECTED_RECEIPT_AUTHORITY_KEYS},
    }


def test_contract_rejects_extra_shadow_authority_field():
    c = contract(); c['target_selected'] = True
    with pytest.raises(sc.ContractError):
        sc.validate_contract(c)


def test_contract_claim_boundary_is_frozen_exactly():
    c = contract(); c['claim_boundary'] = 'REAL_TARGET_AUTHORITY'
    with pytest.raises(sc.ContractError):
        sc.validate_contract(c)


def test_evidence_manifest_rejects_extra_shadow_authority_field():
    mf = evidence_manifest(); mf['target_selected'] = True
    with pytest.raises(ev.EvidenceManifestError):
        ev.validate_evidence_manifest(
            mf,
            candidate_id='C1_RELATIONAL_SHARED',
            required_gates=list(mf['gates']),
        )


def test_candidate_receipt_rejects_extra_shadow_claim_field():
    c, mf, r = receipt(); r['target_winner'] = True
    with pytest.raises(sc.ReceiptError):
        sc.validate_candidate_receipt(r, c, mf)


def test_candidate_receipt_score_must_be_finite_exact_number():
    for bad in ('1.0', True, float('nan'), float('inf')):
        c, mf, r = receipt(score=bad)
        with pytest.raises(sc.ReceiptError):
            sc.validate_candidate_receipt(r, c, mf)


def test_prefreeze_contract_validator_rejects_shadow_claim_field():
    c = contract(); c['target_selected'] = True
    with pytest.raises(pf.PrefreezeError):
        pf.canonical_tournament_contract_sha256(c)


def test_prefreeze_contract_validator_freezes_claim_boundary():
    c = contract(); c['claim_boundary'] = 'REAL_TARGET_AUTHORITY'
    with pytest.raises(pf.PrefreezeError):
        pf.canonical_tournament_contract_sha256(c)
