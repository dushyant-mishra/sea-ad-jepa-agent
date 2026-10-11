import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / 'scripts/v5/td_target_tournament_evidence.py'
spec = importlib.util.spec_from_file_location('td_target_tournament_evidence', MOD)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

GATES = ['G1', 'G2', 'Q1']


def manifest(status='PASS'):
    return {
        'schema': 'JEPA_TD_TARGET_TOURNAMENT_GATE_EVIDENCE_MANIFEST_V1',
        'fixture': True,
        'candidate_id': 'C2_QUERY_MEASURED',
        'gates': {
            g: {
                'status': status,
                'evidence_schema': m.expected_evidence_schema(g),
                'evidence_sha256': ('a' if g != 'G2' else 'b') * 64,
            }
            for g in GATES
        },
        'authority': {
            'target_selected': False,
            'representation_selected': False,
            'stage4_authorized': False,
            'training_authorized': False,
            'value_read_authorized': False,
        },
    }


def test_manifest_validates_and_hash_is_deterministic():
    x = manifest()
    h1 = m.validate_evidence_manifest(x, candidate_id='C2_QUERY_MEASURED', required_gates=GATES)
    h2 = m.validate_evidence_manifest(dict(x), candidate_id='C2_QUERY_MEASURED', required_gates=GATES)
    assert h1 == h2 and len(h1) == 64


def test_manifest_requires_exact_gate_set():
    x = manifest(); del x['gates']['G2']
    with pytest.raises(m.EvidenceManifestError):
        m.validate_evidence_manifest(x, candidate_id='C2_QUERY_MEASURED', required_gates=GATES)


def test_manifest_rejects_unknown_status():
    x = manifest(); x['gates']['G1']['status'] = 'MAYBE'
    with pytest.raises(m.EvidenceManifestError):
        m.validate_evidence_manifest(x, candidate_id='C2_QUERY_MEASURED', required_gates=GATES)


def test_manifest_rejects_bad_hash_and_empty_schema():
    x = manifest(); x['gates']['G1']['evidence_sha256'] = 'nope'
    with pytest.raises(m.EvidenceManifestError):
        m.validate_evidence_manifest(x, candidate_id='C2_QUERY_MEASURED', required_gates=GATES)
    x = manifest(); x['gates']['G1']['evidence_schema'] = ''
    with pytest.raises(m.EvidenceManifestError):
        m.validate_evidence_manifest(x, candidate_id='C2_QUERY_MEASURED', required_gates=GATES)


def test_manifest_rejects_candidate_mismatch():
    with pytest.raises(m.EvidenceManifestError):
        m.validate_evidence_manifest(manifest(), candidate_id='C1_RELATIONAL_SHARED', required_gates=GATES)


def test_manifest_rejects_authority_true_or_missing_key():
    x = manifest(); x['authority']['target_selected'] = True
    with pytest.raises(m.EvidenceManifestError):
        m.validate_evidence_manifest(x, candidate_id='C2_QUERY_MEASURED', required_gates=GATES)
    x = manifest(); del x['authority']['target_selected']
    with pytest.raises(m.EvidenceManifestError):
        m.validate_evidence_manifest(x, candidate_id='C2_QUERY_MEASURED', required_gates=GATES)


def test_gate_boolean_projection_maps_only_pass_to_true():
    x = manifest('PASS'); x['gates']['G2']['status'] = 'NOT_ESTIMABLE'; x['gates']['Q1']['status'] = 'FAIL'
    assert m.gate_boolean_projection(x) == {'G1': True, 'G2': False, 'Q1': False}


def test_canonical_hash_changes_when_evidence_changes():
    a = manifest(); b = manifest(); b['gates']['G1']['evidence_sha256'] = 'c' * 64
    assert m.canonical_manifest_sha256(a) != m.canonical_manifest_sha256(b)


def test_expected_schema_is_gate_specific_and_deterministic():
    assert m.expected_evidence_schema('G1') == 'JEPA_TD_GATE_EVIDENCE_G1_V1'
    assert m.expected_evidence_schema('Q1') != 'JEPA_TD_GATE_EVIDENCE_G1_V1'


def test_wrong_gate_evidence_schema_is_rejected():
    x = manifest()
    x['gates']['G1']['evidence_schema'] = m.expected_evidence_schema('G2')
    with pytest.raises(m.EvidenceManifestError):
        m.validate_evidence_manifest(x, candidate_id='C2_QUERY_MEASURED', required_gates=GATES)


def test_generic_schema_is_rejected_even_with_valid_hash():
    x = manifest()
    x['gates']['G1']['evidence_schema'] = 'SYNTHETIC_GATE_EVIDENCE_V1'
    with pytest.raises(m.EvidenceManifestError):
        m.validate_evidence_manifest(x, candidate_id='C2_QUERY_MEASURED', required_gates=GATES)
