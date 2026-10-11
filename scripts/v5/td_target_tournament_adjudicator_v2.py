"""Fail-closed synthetic/metadata-only adjudicator for target-tournament V2.

This module creates no biological, target-selection, representation-selection,
TD60, Stage4, training, or real-value execution authority.
"""
from __future__ import annotations

import hashlib
import json
import math

import td_target_tournament_contract_v2 as c2


class AdjudicationV2Error(ValueError):
    pass


EVIDENCE_SCHEMA = 'JEPA_TD_TARGET_TOURNAMENT_GATE_EVIDENCE_MANIFEST_V2'
RECEIPT_SCHEMA = 'JEPA_TD_TARGET_TOURNAMENT_CANDIDATE_RECEIPT_V2'
ALLOWED_STATUS = {'PASS', 'FAIL', 'NOT_ESTIMABLE'}
AUTHORITY_KEYS = tuple(sorted(c2.AUTHORITY_KEYS))

_EVIDENCE_FIELDS = {
    'schema', 'fixture_only', 'candidate_id', 'prefreeze_manifest_sha256',
    'gates', 'authority',
}
_RECEIPT_FIELDS = {
    'schema', 'fixture_only', 'candidate_id', 'status', 'aggregate_score',
    'prefreeze_manifest_sha256', 'evidence_manifest_sha256', 'gates', 'authority',
}
_GATE_RECORD_FIELDS = {'status', 'evidence_schema', 'evidence_sha256'}


def _is_sha256(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in '0123456789abcdef' for ch in value)
    )


def canonical_sha256(value) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(',', ':'), ensure_ascii=False
    ).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def expected_evidence_schema(gate: str) -> str:
    if (
        not isinstance(gate, str)
        or not gate
        or any(not (ch.isalnum() or ch == '_') for ch in gate)
    ):
        raise AdjudicationV2Error('invalid gate identifier')
    return f'JEPA_TD_GATE_EVIDENCE_{gate}_V2'


def _validate_authority(authority, label):
    if not isinstance(authority, dict) or set(authority) != set(AUTHORITY_KEYS):
        raise AdjudicationV2Error(f'{label} authority keys must exactly match V2 contract')
    if any(value is not False for value in authority.values()):
        raise AdjudicationV2Error(f'{label} cannot carry authority')


def _derive_status(gates: dict) -> str:
    statuses = [record['status'] for record in gates.values()]
    if any(status == 'FAIL' for status in statuses):
        return 'FAIL'
    if any(status == 'NOT_ESTIMABLE' for status in statuses):
        return 'NOT_ESTIMABLE'
    return 'PASS'


def validate_evidence_manifest(
    manifest,
    contract,
    *,
    expected_prefreeze_manifest_sha256: str,
):
    try:
        c2.validate_contract(contract)
    except c2.ContractV2Error as exc:
        raise AdjudicationV2Error(str(exc)) from exc
    if not _is_sha256(expected_prefreeze_manifest_sha256):
        raise AdjudicationV2Error('external prefreeze SHA must be an exact lowercase SHA-256')
    if not isinstance(manifest, dict) or set(manifest) != _EVIDENCE_FIELDS:
        raise AdjudicationV2Error('evidence manifest fields must exactly match V2 schema')
    if manifest.get('schema') != EVIDENCE_SCHEMA:
        raise AdjudicationV2Error('wrong V2 evidence-manifest schema')
    if manifest.get('fixture_only') is not True:
        raise AdjudicationV2Error('V2 evidence manifest must remain fixture_only=true')
    cid = manifest.get('candidate_id')
    if cid not in c2.CANDIDATES:
        raise AdjudicationV2Error('unknown V2 candidate')
    if manifest.get('prefreeze_manifest_sha256') != expected_prefreeze_manifest_sha256:
        raise AdjudicationV2Error('evidence manifest external prefreeze binding mismatch')

    required = contract['candidate_gate_sets'][cid]
    gates = manifest.get('gates')
    if not isinstance(gates, dict) or set(gates) != set(required):
        raise AdjudicationV2Error('evidence manifest must contain the exact candidate gate set')
    for gate in required:
        record = gates[gate]
        if not isinstance(record, dict) or set(record) != _GATE_RECORD_FIELDS:
            raise AdjudicationV2Error(f'invalid gate evidence record shape: {gate}')
        if record.get('status') not in ALLOWED_STATUS:
            raise AdjudicationV2Error(f'invalid gate status: {gate}')
        if record.get('evidence_schema') != expected_evidence_schema(gate):
            raise AdjudicationV2Error(f'evidence-schema role mismatch: {gate}')
        if not _is_sha256(record.get('evidence_sha256')):
            raise AdjudicationV2Error(f'invalid gate evidence SHA-256: {gate}')
    _validate_authority(manifest.get('authority'), 'evidence manifest')
    return manifest


def validate_candidate_receipt(
    receipt,
    contract,
    evidence_manifest,
    *,
    expected_prefreeze_manifest_sha256: str,
):
    validate_evidence_manifest(
        evidence_manifest,
        contract,
        expected_prefreeze_manifest_sha256=expected_prefreeze_manifest_sha256,
    )
    if not isinstance(receipt, dict) or set(receipt) != _RECEIPT_FIELDS:
        raise AdjudicationV2Error('candidate receipt fields must exactly match V2 schema')
    if receipt.get('schema') != RECEIPT_SCHEMA:
        raise AdjudicationV2Error('wrong V2 candidate-receipt schema')
    if receipt.get('fixture_only') is not True:
        raise AdjudicationV2Error('V2 candidate receipt must remain fixture_only=true')
    cid = receipt.get('candidate_id')
    if cid != evidence_manifest.get('candidate_id'):
        raise AdjudicationV2Error('candidate receipt/manifest candidate mismatch')
    if receipt.get('prefreeze_manifest_sha256') != expected_prefreeze_manifest_sha256:
        raise AdjudicationV2Error('candidate receipt external prefreeze binding mismatch')
    if receipt.get('evidence_manifest_sha256') != canonical_sha256(evidence_manifest):
        raise AdjudicationV2Error('candidate receipt evidence-manifest SHA binding mismatch')

    score = receipt.get('aggregate_score')
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
        raise AdjudicationV2Error('aggregate_score must be an exact finite JSON number')

    required = contract['candidate_gate_sets'][cid]
    expected_projection = {
        gate: evidence_manifest['gates'][gate]['status'] == 'PASS'
        for gate in required
    }
    if receipt.get('gates') != expected_projection:
        raise AdjudicationV2Error('candidate receipt gate projection differs from evidence manifest')

    derived = _derive_status(evidence_manifest['gates'])
    if receipt.get('status') != derived:
        raise AdjudicationV2Error('declared candidate status differs from gate-derived status')
    _validate_authority(receipt.get('authority'), 'candidate receipt')
    return {
        'candidate_id': cid,
        'status': derived,
        'failed_gates': [g for g in required if evidence_manifest['gates'][g]['status'] == 'FAIL'],
        'not_estimable_gates': [g for g in required if evidence_manifest['gates'][g]['status'] == 'NOT_ESTIMABLE'],
    }


def adjudicate(
    contract,
    receipts,
    manifests,
    *,
    expected_prefreeze_manifest_sha256: str,
):
    try:
        c2.validate_contract(contract)
    except c2.ContractV2Error as exc:
        raise AdjudicationV2Error(str(exc)) from exc
    if not _is_sha256(expected_prefreeze_manifest_sha256):
        raise AdjudicationV2Error('external prefreeze SHA must be an exact lowercase SHA-256')
    if not isinstance(receipts, list) or not isinstance(manifests, dict):
        raise AdjudicationV2Error('receipts must be a list and manifests a candidate map')

    by_candidate = {}
    for receipt in receipts:
        if not isinstance(receipt, dict):
            raise AdjudicationV2Error('candidate receipt must be an object')
        cid = receipt.get('candidate_id')
        if cid in by_candidate:
            raise AdjudicationV2Error(f'duplicate candidate receipt: {cid}')
        if cid not in c2.CANDIDATES:
            raise AdjudicationV2Error(f'unknown candidate receipt: {cid}')
        if cid not in manifests:
            raise AdjudicationV2Error(f'missing evidence manifest for receipt: {cid}')
        by_candidate[cid] = validate_candidate_receipt(
            receipt,
            contract,
            manifests[cid],
            expected_prefreeze_manifest_sha256=expected_prefreeze_manifest_sha256,
        )

    if set(manifests) != set(by_candidate):
        extras = sorted(set(manifests) - set(by_candidate))
        raise AdjudicationV2Error(f'evidence manifests without matching receipts: {extras}')

    missing_foundation = [cid for cid in c2.FOUNDATION if cid not in by_candidate]
    tournament_complete = not missing_foundation

    eligible = []
    rejected = {}
    for cid in c2.FOUNDATION:
        if cid not in by_candidate:
            continue
        rec = dict(by_candidate[cid])
        blocked = []
        if cid == 'C4_STRUCTURED_COMPOSITE':
            for parent in ('C2_RELATIONAL_SHARED', 'C3_QUERY_MEASURED'):
                parent_rec = by_candidate.get(parent)
                if parent_rec is None or parent_rec['status'] != 'PASS':
                    blocked.append(parent)
        if rec['status'] == 'PASS' and not blocked:
            eligible.append(cid)
        else:
            rec['blocked_by_constituents'] = blocked
            rejected[cid] = rec

    specialist_eligible = [
        cid for cid in c2.SPECIALISTS
        if cid in by_candidate and by_candidate[cid]['status'] == 'PASS'
    ]

    if not tournament_complete:
        terminal = 'TOURNAMENT_INCOMPLETE__FOUNDATION_CANDIDATES_MISSING__NO_TARGET_AUTHORITY'
    elif any(by_candidate[cid]['status'] == 'NOT_ESTIMABLE' for cid in c2.FOUNDATION):
        terminal = 'NO_TARGET_WINNER__FOUNDATION_EVIDENCE_NOT_ESTIMABLE__NO_TARGET_AUTHORITY'
    elif len(eligible) == len(c2.FOUNDATION):
        terminal = 'CANDIDATES_ELIGIBLE_FOR_TARGET_SELECTION__NO_TARGET_AUTHORITY'
    else:
        terminal = 'NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION'

    return {
        'schema': 'JEPA_TD_TARGET_TOURNAMENT_ADJUDICATION_V2',
        'fixture_only': True,
        'prefreeze_manifest_sha256': expected_prefreeze_manifest_sha256,
        'tournament_complete': tournament_complete,
        'missing_foundation_candidates': missing_foundation,
        'foundation_eligible': eligible,
        'optional_specialists_eligible': specialist_eligible,
        'rejected': rejected,
        'terminal': terminal,
        'target_selected': False,
        'representation_selected': False,
        'td60_authorized': False,
        'stage4_authorized': False,
        'training_authorized': False,
        'real_tournament_authorized': False,
        'value_read_authorized': False,
    }
