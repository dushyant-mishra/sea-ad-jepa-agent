import importlib.util
from pathlib import Path
import pytest

P = Path(__file__).resolve().parents[1] / 'src' / 'sea_ad_jepa' / 'v5' / 'artifact_binding_v1.py'
spec = importlib.util.spec_from_file_location('artifact_binding_v1', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_canonical_json_is_order_independent_and_stable():
    a = {'b': 2, 'a': {'y': 2, 'x': 1}}
    b = {'a': {'x': 1, 'y': 2}, 'b': 2}
    assert m.canonical_json_bytes(a) == m.canonical_json_bytes(b)
    assert m.artifact_sha256(a) == m.artifact_sha256(b)


def test_seal_and_validate_round_trip_binds_payload_and_parents():
    envelope = m.seal_artifact(
        schema='TEST_ARTIFACT_V1',
        payload={'value': 7, 'training_authorized': False},
        parent_sha256={'full104': 'a' * 64, 'design': 'b' * 64},
    )
    out = m.validate_artifact(
        envelope,
        expected_schema='TEST_ARTIFACT_V1',
        expected_parents={'full104': 'a' * 64, 'design': 'b' * 64},
    )
    assert out == {'value': 7, 'training_authorized': False}


def test_payload_mutation_fails_digest_validation():
    envelope = m.seal_artifact('TEST_ARTIFACT_V1', {'value': 7}, {'full104': 'a' * 64})
    envelope['payload']['value'] = 8
    with pytest.raises(RuntimeError, match='DIGEST_MISMATCH'):
        m.validate_artifact(envelope, expected_schema='TEST_ARTIFACT_V1', expected_parents={'full104': 'a' * 64})


def test_parent_substitution_fails_even_with_valid_shape():
    envelope = m.seal_artifact('TEST_ARTIFACT_V1', {'value': 7}, {'full104': 'a' * 64})
    with pytest.raises(RuntimeError, match='PARENT_MISMATCH'):
        m.validate_artifact(envelope, expected_schema='TEST_ARTIFACT_V1', expected_parents={'full104': 'b' * 64})


def test_digest_substitution_fails():
    envelope = m.seal_artifact('TEST_ARTIFACT_V1', {'value': 7}, {'full104': 'a' * 64})
    envelope['artifact_sha256'] = 'f' * 64
    with pytest.raises(RuntimeError, match='DIGEST_MISMATCH'):
        m.validate_artifact(envelope, expected_schema='TEST_ARTIFACT_V1', expected_parents={'full104': 'a' * 64})
