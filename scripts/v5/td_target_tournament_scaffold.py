"""Synthetic-fixture-only target tournament adjudication.

This module intentionally does not read biological matrices and cannot emit target authority.
"""

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
CONTRACT_SCHEMA = 'JEPA_TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V1'
RECEIPT_SCHEMA = 'JEPA_TD_TARGET_TOURNAMENT_CANDIDATE_RECEIPT_V1'
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


def validate_contract(contract):
    if contract.get('schema') != CONTRACT_SCHEMA:
        raise ContractError('wrong contract schema')
    if contract.get('fixture_only') is not True:
        raise ContractError('scaffold contract must remain fixture_only=true')
    if contract.get('candidate_ids') != EXPECTED_CANDIDATES:
        raise ContractError('candidate_ids differ from frozen scaffold')
    if contract.get('foundation_candidate_ids') != EXPECTED_FOUNDATION:
        raise ContractError('foundation_candidate_ids differ from frozen scaffold')
    if contract.get('optional_specialist_ids') != EXPECTED_SPECIALISTS:
        raise ContractError('optional_specialist_ids differ from frozen scaffold')
    if contract.get('mandatory_gates') != EXPECTED_GATES:
        raise ContractError('mandatory_gates differ from frozen scaffold')
    auth = contract.get('authority')
    if not isinstance(auth, dict):
        raise ContractError('authority object required')
    if set(auth) != EXPECTED_CONTRACT_AUTHORITY_KEYS:
        raise ContractError('authority keys differ from frozen scaffold')
    _assert_all_false(auth, ContractError, 'authority')


def validate_candidate_receipt(receipt, contract):
    validate_contract(contract)
    if receipt.get('schema') != RECEIPT_SCHEMA:
        raise ReceiptError('wrong receipt schema')
    if receipt.get('fixture') is not True:
        raise ReceiptError('scaffold accepts synthetic fixture receipts only')
    cid = receipt.get('candidate_id')
    if cid not in contract['candidate_ids']:
        raise ReceiptError('unknown candidate_id')
    gates = receipt.get('gates')
    if not isinstance(gates, dict) or set(gates) != set(contract['mandatory_gates']):
        raise ReceiptError('receipt gates must exactly match frozen mandatory gates')
    if any(type(gates[g]) is not bool for g in contract['mandatory_gates']):
        raise ReceiptError('gate values must be boolean')
    auth = receipt.get('authority')
    if not isinstance(auth, dict):
        raise ReceiptError('receipt authority object required')
    if set(auth) != EXPECTED_RECEIPT_AUTHORITY_KEYS:
        raise ReceiptError('receipt authority keys differ from frozen scaffold')
    _assert_all_false(auth, ReceiptError, 'receipt.authority')
    if receipt.get('status') not in {'PASS', 'FAIL', 'NOT_ESTIMABLE'}:
        raise ReceiptError('unsupported status')


def adjudicate(contract, receipts):
    validate_contract(contract)
    foundation_eligible = []
    optional_specialists_eligible = []
    rejected = {}
    seen = set()
    for receipt in receipts:
        validate_candidate_receipt(receipt, contract)
        cid = receipt['candidate_id']
        if cid in seen:
            raise ReceiptError(f'duplicate candidate receipt: {cid}')
        seen.add(cid)
        failed_gates = [g for g in contract['mandatory_gates'] if receipt['gates'][g] is not True]
        eligible = receipt['status'] == 'PASS' and not failed_gates
        if eligible and cid in contract['foundation_candidate_ids']:
            foundation_eligible.append(cid)
        elif eligible and cid in contract['optional_specialist_ids']:
            optional_specialists_eligible.append(cid)
        else:
            rejected[cid] = {'status': receipt['status'], 'failed_gates': failed_gates}

    foundation_eligible.sort(key=contract['foundation_candidate_ids'].index)
    optional_specialists_eligible.sort(key=contract['optional_specialist_ids'].index)
    terminal = (
        'CANDIDATES_ELIGIBLE_FOR_TARGET_SELECTION__NO_TARGET_AUTHORITY'
        if foundation_eligible
        else 'NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION'
    )
    return {
        'schema': 'JEPA_TD_TARGET_TOURNAMENT_SCAFFOLD_ADJUDICATION_V1',
        'fixture_only': True,
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
