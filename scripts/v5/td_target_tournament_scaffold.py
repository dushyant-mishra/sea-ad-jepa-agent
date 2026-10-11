"""Synthetic-fixture-only target tournament adjudication.

This module intentionally does not read biological matrices and cannot emit target authority.
"""

import math
import td_target_tournament_evidence as evidence

EXPECTED_CANDIDATES = [
    'C1_RELATIONAL_SHARED',
    'C2_QUERY_MEASURED',
    'C3_LEARNED_SHARED',
    'C4_STRUCTURED_COMPOSITE',
    'C5_REGULATORY_SPECIALIST',
]
EXPECTED_FOUNDATION = EXPECTED_CANDIDATES[:4]
EXPECTED_SPECIALISTS = ['C5_REGULATORY_SPECIALIST']
EXPECTED_GATES = [
    'G1_DONOR_PRIMARY',
    'G2_SOURCE_REPLICATION',
    'G3_SHORTCUT_DEFEAT',
    'G4_INFORMATION_ASYMMETRY',
    'G5_SUPPORT_ABSTENTION',
    'G6_TRANSFER',
    'G7_NO_POSTHOC',
]
EXPECTED_CANDIDATE_SPECIFIC_GATES = {
    'C1_RELATIONAL_SHARED': [
        'R1_SCALE_FREE_RELATIONAL_RECURRENCE',
        'R2_FINE_LOCALITY_NOT_PRIMARY',
        'R3_MATCHED_WRONG_CELL_DEFEAT',
    ],
    'C2_QUERY_MEASURED': [
        'Q1_Q_SCALAR_STUDENT_ABSENT',
        'Q2_Q_EXCLUDED_TEACHER_ABLATION',
        'Q3_TARGET_NORMALIZATION_Q_FREE',
        'Q4_Q_COUNT_ONLY_DEFEAT',
        'Q5_Q_ADDRESS_ONLY_DEFEAT',
    ],
    'C3_LEARNED_SHARED': [
        'L1_LEARNED_TEACHER_VIEW_CONTINUITY',
        'L2_CONDITIONAL_TECHNOLOGY_IMPRINT',
        'L3_EVIDENCE_RESPONSE',
        'L4_MEASUREMENT_DEPTH_RESPONSE',
        'L5_COLLAPSE_SHORTCUT_DEFEAT',
        'L6_IDENTITY_SUPPORT_BASELINE_DEFEAT',
    ],
    'C4_STRUCTURED_COMPOSITE': [
        'C4_INCREMENT_OVER_CONSTITUENTS',
        'L1_LEARNED_TEACHER_VIEW_CONTINUITY',
        'L2_CONDITIONAL_TECHNOLOGY_IMPRINT',
        'Q1_Q_SCALAR_STUDENT_ABSENT',
        'Q2_Q_EXCLUDED_TEACHER_ABLATION',
        'Q3_TARGET_NORMALIZATION_Q_FREE',
        'Q5_Q_ADDRESS_ONLY_DEFEAT',
        'L6_IDENTITY_SUPPORT_BASELINE_DEFEAT',
    ],
    'C5_REGULATORY_SPECIALIST': [
        'M1_CIRCULARITY_CONTROL',
        'M2_INDEPENDENT_PROVENANCE',
        'M3_CAUSAL_CLAIM_FALSE',
        'M4_SUPPORT_ABSTENTION',
    ],
}
CONTRACT_SCHEMA = 'JEPA_TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V1'
RECEIPT_SCHEMA = 'JEPA_TD_TARGET_TOURNAMENT_CANDIDATE_RECEIPT_V1'
CLAIM_BOUNDARY = 'SYNTHETIC_SCAFFOLD_ONLY__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY'
CONTRACT_FIELDS = {
    'schema', 'fixture_only', 'authority', 'candidate_ids',
    'foundation_candidate_ids', 'optional_specialist_ids', 'mandatory_gates',
    'claim_boundary', 'candidate_specific_gates',
}
RECEIPT_FIELDS = {
    'schema', 'fixture', 'candidate_id', 'status', 'aggregate_score', 'gates',
    'evidence_manifest_sha256', 'authority',
}
EXPECTED_CONTRACT_AUTHORITY_KEYS = {
    'value_read_authorized',
    'target_selection_authorized',
    'representation_selection_authorized',
    'td60_authorized',
    'stage4_authorized',
    'training_authorized',
}
EXPECTED_RECEIPT_AUTHORITY_KEYS = {
    'target_selected',
    'representation_selected',
    'stage4_authorized',
    'training_authorized',
    'value_read_authorized',
}


class ContractError(ValueError):
    pass


class ReceiptError(ValueError):
    pass


def _assert_all_false(mapping, exc_type, label):
    for key, value in mapping.items():
        if value is not False:
            raise exc_type(f'{label}.{key} must be false')


def _finite_exact_number(value, label):
    if isinstance(value, bool) or type(value) not in (int, float):
        raise ReceiptError(f'{label} must be an exact JSON numeric value')
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ReceiptError(f'{label} must be finite')
    return numeric


def validate_contract(contract):
    if not isinstance(contract, dict) or set(contract) != CONTRACT_FIELDS:
        raise ContractError('contract fields must exactly match frozen scaffold')
    if contract.get('schema') != CONTRACT_SCHEMA:
        raise ContractError('wrong contract schema')
    if contract.get('fixture_only') is not True:
        raise ContractError('scaffold contract must remain fixture_only=true')
    if contract.get('claim_boundary') != CLAIM_BOUNDARY:
        raise ContractError('claim_boundary differs from frozen scaffold')
    if contract.get('candidate_ids') != EXPECTED_CANDIDATES:
        raise ContractError('candidate_ids differ from frozen scaffold')
    if contract.get('foundation_candidate_ids') != EXPECTED_FOUNDATION:
        raise ContractError('foundation_candidate_ids differ from frozen scaffold')
    if contract.get('optional_specialist_ids') != EXPECTED_SPECIALISTS:
        raise ContractError('optional_specialist_ids differ from frozen scaffold')
    if contract.get('mandatory_gates') != EXPECTED_GATES:
        raise ContractError('mandatory_gates differ from frozen scaffold')
    if contract.get('candidate_specific_gates') != EXPECTED_CANDIDATE_SPECIFIC_GATES:
        raise ContractError('candidate_specific_gates differ from frozen scaffold')
    auth = contract.get('authority')
    if not isinstance(auth, dict):
        raise ContractError('authority object required')
    if set(auth) != EXPECTED_CONTRACT_AUTHORITY_KEYS:
        raise ContractError('authority keys differ from frozen scaffold')
    _assert_all_false(auth, ContractError, 'authority')


def validate_candidate_receipt(receipt, contract, evidence_manifest):
    validate_contract(contract)
    if not isinstance(receipt, dict) or set(receipt) != RECEIPT_FIELDS:
        raise ReceiptError('receipt fields must exactly match frozen scaffold')
    if receipt.get('schema') != RECEIPT_SCHEMA:
        raise ReceiptError('wrong receipt schema')
    if receipt.get('fixture') is not True:
        raise ReceiptError('scaffold accepts synthetic fixture receipts only')
    _finite_exact_number(receipt.get('aggregate_score'), 'aggregate_score')
    cid = receipt.get('candidate_id')
    if cid not in contract['candidate_ids']:
        raise ReceiptError('unknown candidate_id')
    gates = receipt.get('gates')
    required_gates = contract['mandatory_gates'] + contract['candidate_specific_gates'][cid]
    if not isinstance(gates, dict) or set(gates) != set(required_gates):
        raise ReceiptError('receipt gates must exactly match frozen candidate gate set')
    if any(type(gates[g]) is not bool for g in required_gates):
        raise ReceiptError('gate values must be boolean')
    try:
        manifest_sha = evidence.validate_evidence_manifest(
            evidence_manifest, candidate_id=cid, required_gates=required_gates
        )
    except evidence.EvidenceManifestError as exc:
        raise ReceiptError(f'invalid evidence manifest for {cid}: {exc}') from exc
    if receipt.get('evidence_manifest_sha256') != manifest_sha:
        raise ReceiptError('candidate receipt evidence-manifest SHA binding mismatch')
    projection = evidence.gate_boolean_projection(evidence_manifest)
    if gates != projection:
        raise ReceiptError('candidate gate booleans do not match evidence-manifest statuses')
    auth = receipt.get('authority')
    if not isinstance(auth, dict):
        raise ReceiptError('receipt authority object required')
    if set(auth) != EXPECTED_RECEIPT_AUTHORITY_KEYS:
        raise ReceiptError('receipt authority keys differ from frozen scaffold')
    _assert_all_false(auth, ReceiptError, 'receipt.authority')
    if receipt.get('status') not in {'PASS', 'FAIL', 'NOT_ESTIMABLE'}:
        raise ReceiptError('unsupported status')


def adjudicate(contract, receipts, evidence_manifests):
    validate_contract(contract)
    if not isinstance(evidence_manifests, dict):
        raise ReceiptError('candidate evidence manifests must be supplied as a mapping')
    seen = set()
    candidate_ids = []
    for receipt in receipts:
        if not isinstance(receipt, dict):
            raise ReceiptError('candidate receipt must be an object')
        cid = receipt.get('candidate_id')
        if cid not in contract['candidate_ids']:
            raise ReceiptError('unknown candidate_id')
        if cid in seen:
            raise ReceiptError(f'duplicate candidate receipt: {cid}')
        seen.add(cid)
        candidate_ids.append(cid)
    if set(evidence_manifests) != set(candidate_ids):
        raise ReceiptError('evidence-manifest candidate set must exactly match candidate receipts')

    foundation_eligible = []
    optional_specialists_eligible = []
    rejected = {}
    for receipt in receipts:
        cid = receipt['candidate_id']
        manifest = evidence_manifests[cid]
        validate_candidate_receipt(receipt, contract, manifest)
        required_gates = contract['mandatory_gates'] + contract['candidate_specific_gates'][cid]
        evidence_status = {g: manifest['gates'][g]['status'] for g in required_gates}
        failed_gates = [g for g in required_gates if evidence_status[g] == 'FAIL']
        not_estimable_gates = [g for g in required_gates if evidence_status[g] == 'NOT_ESTIMABLE']
        unresolved_gates = [g for g in required_gates if evidence_status[g] != 'PASS']
        eligible = receipt['status'] == 'PASS' and not unresolved_gates
        if eligible and cid in contract['foundation_candidate_ids']:
            foundation_eligible.append(cid)
        elif eligible and cid in contract['optional_specialist_ids']:
            optional_specialists_eligible.append(cid)
        else:
            rejected[cid] = {
                'status': receipt['status'],
                'failed_gates': failed_gates,
                'not_estimable_gates': not_estimable_gates,
            }

    foundation_eligible.sort(key=contract['foundation_candidate_ids'].index)
    optional_specialists_eligible.sort(key=contract['optional_specialist_ids'].index)
    missing_foundation_candidates = [
        cid for cid in contract['foundation_candidate_ids'] if cid not in seen
    ]
    tournament_complete = not missing_foundation_candidates
    foundation_not_estimable = any(
        rejected.get(cid, {}).get('not_estimable_gates')
        or rejected.get(cid, {}).get('status') == 'NOT_ESTIMABLE'
        for cid in contract['foundation_candidate_ids']
        if cid in rejected
    )
    if not tournament_complete:
        terminal = 'TOURNAMENT_INCOMPLETE__FOUNDATION_CANDIDATES_MISSING__NO_TARGET_AUTHORITY'
    elif foundation_eligible:
        terminal = 'CANDIDATES_ELIGIBLE_FOR_TARGET_SELECTION__NO_TARGET_AUTHORITY'
    elif foundation_not_estimable:
        terminal = 'NO_TARGET_WINNER__FOUNDATION_EVIDENCE_NOT_ESTIMABLE__NO_TARGET_AUTHORITY'
    else:
        terminal = 'NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION'
    return {
        'schema': 'JEPA_TD_TARGET_TOURNAMENT_SCAFFOLD_ADJUDICATION_V1',
        'fixture_only': True,
        'tournament_complete': tournament_complete,
        'missing_foundation_candidates': missing_foundation_candidates,
        'foundation_eligible': foundation_eligible,
        'optional_specialists_eligible': optional_specialists_eligible,
        'rejected': rejected,
        'terminal': terminal,
        'target_selected': False,
        'representation_selected': False,
        'stage4_authorized': False,
        'training_authorized': False,
        'value_read_authorized': False,
    }
