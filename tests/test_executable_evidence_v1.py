import hashlib
import json

import pytest

from sea_ad_jepa.v5.executable_evidence_v1 import (
    recompute_control_artifact,
    verify_declared_control_verdicts,
)


def raw_artifact(*, geometry="a" * 64, provenance="PROSPECTIVE_PREMODEL") -> bytes:
    payload = {
        "schema": "JEPA_V5_EXECUTABLE_CONTROL_EVIDENCE_V1",
        "gate_id": "shortcut_superiority",
        "geometry_sha256": geometry,
        "threshold_provenance": provenance,
        "checks": {
            "minimum_acceptable_signal_present": [
                {"id": "valid_signal", "observed": 0.25, "operator": ">=", "threshold": 0.20}
            ],
            "minimum_rejection_violation_present": [
                {"id": "invalid_violation", "observed": 0.30, "operator": ">=", "threshold": 0.20}
            ],
            "gate_accepts_valid_control": [
                {"id": "valid_gate_metric", "observed": 0.12, "operator": ">=", "threshold": 0.10}
            ],
            "gate_rejects_invalid_control": [
                {"id": "invalid_gate_metric", "observed": 0.45, "operator": ">=", "threshold": 0.40}
            ],
        },
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def test_recomputes_verdicts_from_bound_raw_bytes():
    raw = raw_artifact()
    out = recompute_control_artifact(
        raw,
        expected_gate_id="shortcut_superiority",
        expected_geometry_sha256="a" * 64,
        declared_raw_sha256=sha(raw),
    )
    assert out["raw_sha256"] == sha(raw)
    assert out["verdicts"] == {
        "minimum_acceptable_signal_present": True,
        "minimum_rejection_violation_present": True,
        "gate_accepts_valid_control": True,
        "gate_rejects_invalid_control": True,
    }


def test_mutated_raw_bytes_with_stale_digest_stop():
    raw = raw_artifact()
    stale = sha(raw)
    mutated = raw.replace(b"0.45", b"0.05")
    with pytest.raises(RuntimeError, match="RAW_SHA256_MISMATCH"):
        recompute_control_artifact(
            mutated,
            expected_gate_id="shortcut_superiority",
            expected_geometry_sha256="a" * 64,
            declared_raw_sha256=stale,
        )


def test_declared_pass_cannot_override_recomputed_failure():
    raw = raw_artifact().replace(b"0.45", b"0.05")
    declared = {
        "minimum_acceptable_signal_present": True,
        "minimum_rejection_violation_present": True,
        "gate_accepts_valid_control": True,
        "gate_rejects_invalid_control": True,
    }
    with pytest.raises(RuntimeError, match="DECLARED_VERDICT_MISMATCH"):
        verify_declared_control_verdicts(
            raw,
            expected_gate_id="shortcut_superiority",
            expected_geometry_sha256="a" * 64,
            declared_raw_sha256=sha(raw),
            declared_verdicts=declared,
        )


def test_after_the_fact_threshold_provenance_stops():
    raw = raw_artifact(provenance="AFTER_OUTCOME")
    with pytest.raises(RuntimeError, match="THRESHOLD_PROVENANCE"):
        recompute_control_artifact(
            raw,
            expected_gate_id="shortcut_superiority",
            expected_geometry_sha256="a" * 64,
            declared_raw_sha256=sha(raw),
        )


def test_geometry_substitution_stops():
    raw = raw_artifact(geometry="b" * 64)
    with pytest.raises(RuntimeError, match="GEOMETRY_MISMATCH"):
        recompute_control_artifact(
            raw,
            expected_gate_id="shortcut_superiority",
            expected_geometry_sha256="a" * 64,
            declared_raw_sha256=sha(raw),
        )
