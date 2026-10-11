"""Pure synthetic validator for the prospectively frozen target-tournament V2 contract.

This module opens no biological data and creates no execution or selection authority.
"""
from __future__ import annotations


class ContractV2Error(ValueError):
    pass


SCHEMA = 'JEPA_TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V2'
CLAIM_BOUNDARY = 'SYNTHETIC_SCAFFOLD_ONLY__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY'
SPEC_PATH = 'docs/superpowers/specs/2026-10-11-td-multitarget-tournament-prefreeze-v2.md'
SPEC_GIT_BLOB_SHA = 'd996c5044fe8fd0367d4f573347409c065604a88'

CANDIDATES = [
    'C1_SHARED_EMERGENT',
    'C2_RELATIONAL_SHARED',
    'C3_QUERY_MEASURED',
    'C4_STRUCTURED_COMPOSITE',
    'C5_REGULATORY_SPECIALIST',
]
FOUNDATION = CANDIDATES[:4]
SPECIALISTS = ['C5_REGULATORY_SPECIALIST']

PROMOTION_GATES = [
    'G1_INTEGRITY_LINEAGE',
    'G2_NONTRIVIAL_BIOLOGICAL_CONTENT',
    'G3_CORRECT_CELL_SPECIFICITY',
    'G4_DONOR_RECURRENCE',
    'G5_SOURCE_REPLICATION',
    'G6_TEACHER_INFORMATION_ADVANTAGE',
    'G7_EVIDENCE_CONVERGENCE',
    'G8_MEASUREMENT_ROBUSTNESS',
    'G9_LEARNED_TEACHER_CONTINUITY',
    'G10_COLLAPSE_SHORTCUT_RESISTANCE',
    'G11_TRANSFER',
    'G12_COVERAGE_ABSTENTION',
]
SHARED_GATES = [
    'S1_DISJOINT_VIEW_RECURRENCE',
    'S2_DONOR_BALANCED_SUBSPACE_STABILITY',
    'S3_IDENTITY_SUPPORT_BASELINE_DEFEAT',
]
RELATIONAL_GATES = [
    'R1_SCALE_FREE_RELATIONAL_RECURRENCE',
    'R2_LOCALITY_RULE_FROZEN_NO_FINE_MINING',
    'R3_FINE_NEIGHBOR_WRONG_CELL_DEFEAT',
    'R4_INCREMENT_OVER_C1_SHARED',
]
QUERY_GATES = [
    'Q1_Q_SCALAR_STUDENT_ABSENT',
    'Q2_Q_EXCLUDED_TEACHER_PRIMARY_ANCHOR',
    'Q3_TARGET_NORMALIZATION_Q_SCALAR_FREE',
    'Q4_Q_COUNT_ONLY_DEFEAT',
    'Q5_Q_ADDRESS_ONLY_DEFEAT',
    'Q6_QUERY_AGNOSTIC_DEFEAT',
    'Q7_WRONG_Q_DEFEAT',
    'Q8_TECHNICAL_PLUS_Q_DEFEAT',
]
COMPOSITE_GATES = ['C4_INCREMENT_OVER_CONSTITUENTS']
SPECIALIST_GATES = [
    'M1_CIRCULARITY_CONTROL',
    'M2_INDEPENDENT_PROVENANCE',
    'M3_CAUSAL_CLAIM_FALSE',
    'M4_SUPPORT_ABSTENTION',
]

C1_GATES = PROMOTION_GATES + SHARED_GATES
C2_GATES = C1_GATES + RELATIONAL_GATES
C3_GATES = [g for g in PROMOTION_GATES if g != 'G9_LEARNED_TEACHER_CONTINUITY'] + QUERY_GATES
C4_GATES = PROMOTION_GATES + SHARED_GATES + RELATIONAL_GATES + QUERY_GATES + COMPOSITE_GATES
C5_GATES = PROMOTION_GATES[:5] + PROMOTION_GATES[9:12] + SPECIALIST_GATES

CANDIDATE_GATE_SETS = {
    'C1_SHARED_EMERGENT': C1_GATES,
    'C2_RELATIONAL_SHARED': C2_GATES,
    'C3_QUERY_MEASURED': C3_GATES,
    'C4_STRUCTURED_COMPOSITE': C4_GATES,
    'C5_REGULATORY_SPECIALIST': C5_GATES,
}

INHERITANCE = {
    'C2_RELATIONAL_SHARED_must_superset': ['C1_SHARED_EMERGENT'],
    'C4_STRUCTURED_COMPOSITE_must_equal_union_plus': {
        'parents': ['C2_RELATIONAL_SHARED', 'C3_QUERY_MEASURED'],
        'plus': ['C4_INCREMENT_OVER_CONSTITUENTS'],
    },
}

AUTHORITY_KEYS = {
    'value_read_authorized',
    'corrected_replay_authorized',
    'real_tournament_authorized',
    'target_selection_authorized',
    'representation_selection_authorized',
    'td60_authorized',
    'stage4_authorized',
    'training_authorized',
}

CONTRACT_FIELDS = {
    'schema',
    'fixture_only',
    'claim_boundary',
    'spec_path',
    'spec_git_blob_sha',
    'candidate_ids',
    'foundation_candidate_ids',
    'optional_specialist_ids',
    'promotion_gate_catalog',
    'candidate_gate_sets',
    'inheritance',
    'authority',
}


def _assert_unique_nonempty_strings(values, label):
    if (
        not isinstance(values, list)
        or not values
        or len(values) != len(set(values))
        or any(not isinstance(v, str) or not v for v in values)
    ):
        raise ContractV2Error(f'{label} must be a nonempty unique string list')


def _assert_structural_inheritance(contract):
    gate_sets = contract['candidate_gate_sets']
    c1 = set(gate_sets['C1_SHARED_EMERGENT'])
    c2 = set(gate_sets['C2_RELATIONAL_SHARED'])
    c3 = set(gate_sets['C3_QUERY_MEASURED'])
    c4 = set(gate_sets['C4_STRUCTURED_COMPOSITE'])

    if not c1 <= c2:
        raise ContractV2Error('C2 must inherit every C1 gate')
    if c2 - c1 != set(RELATIONAL_GATES):
        raise ContractV2Error('C2 may add exactly the frozen relational-extension gates')

    expected_c4 = c2 | c3 | set(COMPOSITE_GATES)
    if c4 != expected_c4:
        raise ContractV2Error('C4 must equal union(C2,C3)+composite increment gate')

    if 'G9_LEARNED_TEACHER_CONTINUITY' in set(gate_sets['C3_QUERY_MEASURED']):
        raise ContractV2Error('C3 measured target must not silently acquire G9 learned-teacher gate')


def validate_contract(contract):
    if not isinstance(contract, dict) or set(contract) != CONTRACT_FIELDS:
        raise ContractV2Error('V2 contract fields must exactly match frozen schema')
    if contract.get('schema') != SCHEMA:
        raise ContractV2Error('wrong V2 contract schema')
    if contract.get('fixture_only') is not True:
        raise ContractV2Error('V2 scaffold must remain fixture_only=true')
    if contract.get('claim_boundary') != CLAIM_BOUNDARY:
        raise ContractV2Error('V2 claim boundary mismatch')
    if contract.get('spec_path') != SPEC_PATH:
        raise ContractV2Error('V2 spec path mismatch')
    if contract.get('spec_git_blob_sha') != SPEC_GIT_BLOB_SHA:
        raise ContractV2Error('V2 spec git blob identity mismatch')

    if contract.get('candidate_ids') != CANDIDATES:
        raise ContractV2Error('V2 candidate IDs/order differ from frozen design')
    if contract.get('foundation_candidate_ids') != FOUNDATION:
        raise ContractV2Error('V2 foundation candidate partition mismatch')
    if contract.get('optional_specialist_ids') != SPECIALISTS:
        raise ContractV2Error('V2 specialist partition mismatch')

    if contract.get('promotion_gate_catalog') != PROMOTION_GATES:
        raise ContractV2Error('V2 promotion gate catalog mismatch')
    _assert_unique_nonempty_strings(contract['promotion_gate_catalog'], 'promotion_gate_catalog')

    gate_sets = contract.get('candidate_gate_sets')
    if not isinstance(gate_sets, dict) or set(gate_sets) != set(CANDIDATES):
        raise ContractV2Error('candidate_gate_sets must cover exact V2 candidates')
    for cid in CANDIDATES:
        _assert_unique_nonempty_strings(gate_sets[cid], f'candidate_gate_sets.{cid}')
        if gate_sets[cid] != CANDIDATE_GATE_SETS[cid]:
            raise ContractV2Error(f'candidate gate set differs from frozen V2 design: {cid}')

    if contract.get('inheritance') != INHERITANCE:
        raise ContractV2Error('V2 inheritance declaration mismatch')
    _assert_structural_inheritance(contract)

    auth = contract.get('authority')
    if (
        not isinstance(auth, dict)
        or set(auth) != AUTHORITY_KEYS
        or any(value is not False for value in auth.values())
    ):
        raise ContractV2Error('V2 authority must contain exact frozen keys, all false')
