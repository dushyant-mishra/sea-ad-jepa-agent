"""Coverage-only bridge for the prospectively frozen V2 target tournament.

This module validates exact case coverage and custody bindings only. It does not
adjudicate a gate, open biological data, or create target/training authority.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter

import td_target_tournament_prefreeze_v2 as p2


class CoverageV2Error(ValueError):
    pass


COVERAGE_SCHEMA = 'JEPA_TD_GATE_CASE_COVERAGE_AUDIT_V2'
ALLOWED_STATUS = {'PASS', 'FAIL', 'NOT_ESTIMABLE'}
_RECEIPT_FIELDS = {
    'case_id', 'candidate_id', 'gate_id', 'source', 'analysis_tier',
    'endpoint_id', 'status', 'evidence_sha256',
}
_ROLE_FIELDS = ('candidate_id', 'gate_id', 'source', 'analysis_tier', 'endpoint_id')
_PREFREEZE_FIELDS = {
    'schema', 'fixture_only', 'family_alpha', 'multiplicity_method',
    'decision_family_size', 'decision_family_registry_sha256', 'alpha_eff',
    'minimum_nonzero_donors_for_sign_resolution',
    'minimum_permutation_draws_for_resolution', 'tournament_contract_sha256',
    'execution_context_sha256', 'null_seed_material', 'case_resolution',
    'authority', 'manifest_sha256',
}
_CASE_RESOLUTION_FIELDS = {
    'case_id', 'candidate_id', 'gate_id', 'source', 'analysis_tier',
    'endpoint_id', 'available_donors_upper_bound',
    'resolution_impossible_from_donor_upper_bound', 'estimability_proven',
    'biological_result',
}


def _canonical_sha(value) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(',', ':'), ensure_ascii=False
    ).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _is_sha256(value) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in '0123456789abcdef' for ch in value)
    )


def _validate_prefreeze(manifest, expected_prefreeze_manifest_sha256):
    if not _is_sha256(expected_prefreeze_manifest_sha256):
        raise CoverageV2Error('expected V2 prefreeze manifest SHA must be lowercase SHA-256')
    if not isinstance(manifest, dict) or set(manifest) != _PREFREEZE_FIELDS:
        raise CoverageV2Error('V2 prefreeze manifest fields must be exact')
    if manifest.get('schema') != p2.MANIFEST_SCHEMA:
        raise CoverageV2Error('wrong V2 prefreeze manifest schema')
    if manifest.get('fixture_only') is not True:
        raise CoverageV2Error('current V2 coverage bridge requires fixture_only=true')
    if manifest.get('manifest_sha256') != expected_prefreeze_manifest_sha256:
        raise CoverageV2Error('V2 prefreeze manifest differs from external frozen pin')
    core = dict(manifest)
    stated = core.pop('manifest_sha256', None)
    if not _is_sha256(stated) or _canonical_sha(core) != stated:
        raise CoverageV2Error('V2 prefreeze manifest hash mismatch')
    if not _is_sha256(manifest.get('execution_context_sha256')):
        raise CoverageV2Error('V2 prefreeze execution_context_sha256 invalid')
    if not _is_sha256(manifest.get('tournament_contract_sha256')):
        raise CoverageV2Error('V2 prefreeze tournament_contract_sha256 invalid')
    authority = manifest.get('authority')
    if (
        not isinstance(authority, dict)
        or set(authority) != set(p2.AUTHORITY_KEYS)
        or any(value is not False for value in authority.values())
    ):
        raise CoverageV2Error('V2 prefreeze authority must remain exact and false')
    rows = manifest.get('case_resolution')
    if not isinstance(rows, list) or not rows:
        raise CoverageV2Error('V2 prefreeze case_resolution required')
    for row in rows:
        if not isinstance(row, dict) or set(row) != _CASE_RESOLUTION_FIELDS:
            raise CoverageV2Error('V2 prefreeze case_resolution fields must be exact')
        if row.get('estimability_proven') is not False:
            raise CoverageV2Error('V2 prefreeze cannot claim estimability before outcomes')
        if row.get('biological_result') != 'NOT_OPENED':
            raise CoverageV2Error('V2 prefreeze biological_result must remain NOT_OPENED')
    return rows


def audit_gate_case_coverage_v2(
    prefreeze_manifest,
    *,
    expected_prefreeze_manifest_sha256,
    candidate_id,
    gate_id,
    case_receipts,
):
    rows = _validate_prefreeze(
        prefreeze_manifest, expected_prefreeze_manifest_sha256
    )
    expected = [
        row for row in rows
        if row.get('candidate_id') == candidate_id and row.get('gate_id') == gate_id
    ]
    if not expected:
        raise CoverageV2Error('candidate/gate pair absent from frozen V2 decision family')

    expected_by = {}
    for row in expected:
        case_id = row.get('case_id')
        if not isinstance(case_id, str) or not case_id or case_id in expected_by:
            raise CoverageV2Error('invalid or duplicate frozen V2 case_id')
        expected_by[case_id] = row

    if not isinstance(case_receipts, list):
        raise CoverageV2Error('case_receipts must be a list')
    actual_by = {}
    for receipt in case_receipts:
        if not isinstance(receipt, dict) or set(receipt) != _RECEIPT_FIELDS:
            raise CoverageV2Error('V2 case receipt fields must be exact')
        case_id = receipt.get('case_id')
        if not isinstance(case_id, str) or not case_id or case_id in actual_by:
            raise CoverageV2Error('invalid or duplicate V2 case receipt')
        if receipt.get('status') not in ALLOWED_STATUS:
            raise CoverageV2Error('invalid V2 case status')
        if not _is_sha256(receipt.get('evidence_sha256')):
            raise CoverageV2Error('invalid V2 case evidence SHA-256')
        actual_by[case_id] = receipt

    if set(actual_by) != set(expected_by):
        raise CoverageV2Error('V2 case receipt set does not exactly cover frozen cases')

    for case_id, expected_row in expected_by.items():
        receipt = actual_by[case_id]
        for field in _ROLE_FIELDS:
            if receipt.get(field) != expected_row.get(field):
                raise CoverageV2Error(f'V2 case role mismatch: {case_id}: {field}')

    ordered = [actual_by[case_id] for case_id in sorted(actual_by)]
    counts = Counter(row['status'] for row in ordered)
    return {
        'schema': COVERAGE_SCHEMA,
        'fixture_only': True,
        'candidate_id': candidate_id,
        'gate_id': gate_id,
        'prefreeze_manifest_sha256': prefreeze_manifest['manifest_sha256'],
        'execution_context_sha256': prefreeze_manifest['execution_context_sha256'],
        'tournament_contract_sha256': prefreeze_manifest['tournament_contract_sha256'],
        'decision_family_registry_sha256': prefreeze_manifest['decision_family_registry_sha256'],
        'expected_case_count': len(expected_by),
        'received_case_count': len(actual_by),
        'coverage_complete': True,
        'status_counts': {
            status: int(counts.get(status, 0))
            for status in ('PASS', 'FAIL', 'NOT_ESTIMABLE')
        },
        'case_evidence_bundle_sha256': _canonical_sha(ordered),
        'gate_status_not_adjudicated': True,
        'authority': {
            'target_selected': False,
            'representation_selected': False,
            'training_authorized': False,
            'value_read_authorized': False,
        },
    }
