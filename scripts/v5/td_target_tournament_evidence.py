"""Synthetic/compact gate-evidence manifest validation for target tournaments."""
from __future__ import annotations

import hashlib
import json

SCHEMA = 'JEPA_TD_TARGET_TOURNAMENT_GATE_EVIDENCE_MANIFEST_V1'
ALLOWED_STATUS = {'PASS', 'FAIL', 'NOT_ESTIMABLE'}
EXPECTED_AUTHORITY_KEYS = {
    'target_selected',
    'representation_selected',
    'stage4_authorized',
    'training_authorized',
    'value_read_authorized',
}


class EvidenceManifestError(ValueError):
    pass


def _is_sha256(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in '0123456789abcdef' for ch in value)
    )


def expected_evidence_schema(gate):
    if (
        not isinstance(gate, str)
        or not gate
        or not all(ch.isalnum() or ch == '_' for ch in gate)
    ):
        raise EvidenceManifestError('invalid gate identifier for evidence schema')
    return f'JEPA_TD_GATE_EVIDENCE_{gate}_V1'


def canonical_manifest_sha256(manifest):
    raw = json.dumps(
        manifest, sort_keys=True, separators=(',', ':'), ensure_ascii=False
    ).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def validate_evidence_manifest(manifest, *, candidate_id, required_gates):
    if not isinstance(manifest, dict):
        raise EvidenceManifestError('manifest must be an object')
    if manifest.get('schema') != SCHEMA:
        raise EvidenceManifestError('wrong evidence manifest schema')
    if manifest.get('fixture') is not True:
        raise EvidenceManifestError('current evidence manifest must be fixture=true')
    if manifest.get('candidate_id') != candidate_id:
        raise EvidenceManifestError('candidate_id mismatch')
    gates = manifest.get('gates')
    if not isinstance(gates, dict) or set(gates) != set(required_gates):
        raise EvidenceManifestError('evidence gate set must exactly match required gates')
    for gate in required_gates:
        record = gates[gate]
        if not isinstance(record, dict) or set(record) != {
            'status', 'evidence_schema', 'evidence_sha256'
        }:
            raise EvidenceManifestError(f'invalid evidence record shape: {gate}')
        if record['status'] not in ALLOWED_STATUS:
            raise EvidenceManifestError(f'invalid evidence status: {gate}')
        if record.get('evidence_schema') != expected_evidence_schema(gate):
            raise EvidenceManifestError(f'evidence_schema mismatch: {gate}')
        if not _is_sha256(record['evidence_sha256']):
            raise EvidenceManifestError(f'evidence_sha256 invalid: {gate}')
    authority = manifest.get('authority')
    if not isinstance(authority, dict) or set(authority) != EXPECTED_AUTHORITY_KEYS:
        raise EvidenceManifestError('authority keys differ from frozen manifest')
    if any(value is not False for value in authority.values()):
        raise EvidenceManifestError('evidence manifest cannot carry authority')
    return canonical_manifest_sha256(manifest)


def gate_boolean_projection(manifest):
    gates = manifest.get('gates')
    if not isinstance(gates, dict):
        raise EvidenceManifestError('gates required')
    return {gate: record.get('status') == 'PASS' for gate, record in gates.items()}
