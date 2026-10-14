from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.v5.td_unified.premerger_migration_task0 import (
    GLOBAL_AUTHORITY,
    MIGRATION_CLASSES,
    validate_migration_outputs,
)

ROOT = Path(__file__).resolve().parents[3]
RESULT_DIR = ROOT / "results" / "target_discovery" / "unified_qualification_v1"
MATRIX = RESULT_DIR / "PREMERGER_ARTIFACT_MIGRATION_MATRIX_V1.json"
UNRESOLVED = RESULT_DIR / "PREMERGER_UNRESOLVED_WORK_LEDGER_V1.json"
DECOMPOSITION = RESULT_DIR / "PREMERGER_MIXED_ARTIFACT_DECOMPOSITION_V1.json"
MACHA_STREAMS = RESULT_DIR / "PREMERGER_MACHA_DUAL_STREAM_CUSTODY_V1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_required_task0_outputs_validate():
    report = validate_migration_outputs(MATRIX, UNRESOLVED)
    assert report["status"] == "PASS_TASK0_PREMERGER_MIGRATION_CUSTODY_VALIDATION"
    assert report["global_authority"] == GLOBAL_AUTHORITY
    assert report["artifact_count"] >= 30
    assert report["decomposition_child_count"] >= 8
    assert report["macha_stream_artifact_count"] >= 8
    assert report["unresolved_count"] >= 8


def test_two_macha_custody_streams_are_machine_traceable():
    payload = _load(MACHA_STREAMS)
    assert payload["global_authority"] == GLOBAL_AUTHORITY
    streams = {stream["stream_id"]: stream for stream in payload["streams"]}
    assert set(streams) == {"MACHA_REAL_TD_CORRECTED_REPLAY", "MACHA_V79_BAYESIAN_KNOWN_TRUTH"}
    real_ids = {a["artifact_id"] for a in streams["MACHA_REAL_TD_CORRECTED_REPLAY"]["artifacts"]}
    synth_ids = {a["artifact_id"] for a in streams["MACHA_V79_BAYESIAN_KNOWN_TRUTH"]["artifacts"]}
    assert {"MACHA_PR314_CORRECTED_REPLAY", "MACHA_PR316_FINE_RARE_SUCCESSOR", "MACHA_REAL_DATA_AUDIT", "MACHA_REPAIR_LINEAGE_364_369"}.issubset(real_ids)
    assert {"MACHA_PR261_V79_BAYESIAN_HANDOFF", "MACHA_V79_Q00_Q11_REALIZATION_CUSTODY", "MACHA_V79_TERMINAL_NOT_QUALIFIED", "MACHA_V80_BENCHMARK_PACKAGE"}.issubset(synth_ids)
    for stream in streams.values():
        assert stream["historical_scientific_custodian"] == "Macha"
        assert stream["unified_destination"]
        assert stream["review_obligations"]
        for artifact in stream["artifacts"]:
            assert artifact["migration_class"] in MIGRATION_CLASSES
            assert artifact["destination_in_unified_architecture"]
            assert artifact["historical_evidence_retained"] is True
            assert artifact["current_authority"] != "CURRENT_UNIFIED_SCIENTIFIC_AUTHORITY"


def test_macha_stream_unresolved_registration_obligations_are_retained():
    unresolved = _load(UNRESOLVED)
    ids = {item["item_id"] for item in unresolved["items"]}
    assert "U_MACHA_REAL_TD_HISTORY_REGISTRATION" in ids
    assert "U_MACHA_V79_HISTORY_REGISTRATION" in ids


def test_every_artifact_has_exactly_one_allowed_migration_class():
    matrix = _load(MATRIX)
    for artifact in matrix["artifacts"]:
        assert artifact["migration_class"] in MIGRATION_CLASSES
        assert isinstance(artifact["migration_class"], str)


def test_available_exact_identity_is_not_omitted():
    matrix = _load(MATRIX)
    for artifact in matrix["artifacts"]:
        assert "exact_identity_available" in artifact
        if artifact["exact_identity_available"]:
            assert artifact.get("source_commit")
            assert artifact.get("artifact_digest")


def test_validator_rejects_deleted_exact_identity_attestation(tmp_path: Path):
    matrix = _load(MATRIX)
    unresolved = _load(UNRESOLVED)
    matrix["artifacts"][0].pop("exact_identity_available")
    bad_matrix = tmp_path / "matrix.json"
    ledger = tmp_path / "ledger.json"
    bad_matrix.write_text(json.dumps(matrix), encoding="utf-8")
    ledger.write_text(json.dumps(unresolved), encoding="utf-8")
    with pytest.raises(ValueError, match="exact_identity_available"):
        validate_migration_outputs(bad_matrix, ledger)


def test_parallel_authority_is_never_ambiguously_active():
    matrix = _load(MATRIX)
    for artifact in matrix["artifacts"]:
        if artifact["migration_class"] == "SUPERSEDED_PARALLEL_IMPLEMENTATION":
            assert artifact["current_authority"] in {
                "NONE__HISTORICAL_EVIDENCE_ONLY",
                "SUPERSEDED__NO_NEW_SCIENTIFIC_AUTHORITY",
            }
            assert artifact["continue_stop_or_redirect"] == "STOP_AND_FREEZE"


def test_reusable_work_cannot_be_discarded_without_reason():
    matrix = _load(MATRIX)
    for artifact in matrix["artifacts"]:
        if artifact["migration_class"] in {
            "REUSABLE_SHARED_INFRASTRUCTURE",
            "KNOWN_TRUTH_SUBSTRATE",
            "KNOWN_TRUTH_CHALLENGE_ASSET",
            "HISTORICAL_NEGATIVE_CONTROL",
        }:
            assert artifact.get("destination_in_unified_architecture")
            assert artifact.get("historical_evidence_retained") is True


def test_closed_failed_experiments_are_not_promoted():
    matrix = _load(MATRIX)
    for artifact in matrix["artifacts"]:
        if artifact["migration_class"] == "CLOSED_FAILED_EXPERIMENT":
            assert artifact["current_authority"].startswith("NONE")
            assert artifact["requires_requalification"] is True


def test_every_unresolved_dependency_is_present_in_ledger():
    matrix = _load(MATRIX)
    unresolved = _load(UNRESOLVED)
    ids = {item["item_id"] for item in unresolved["items"]}
    for artifact in matrix["artifacts"]:
        for item_id in artifact.get("unresolved_item_ids", []):
            assert item_id in ids


def test_conflicting_classes_require_explicit_decomposition():
    matrix = _load(MATRIX)
    artifact_ids = [a["artifact_id"] for a in matrix["artifacts"]]
    assert len(artifact_ids) == len(set(artifact_ids))
    decomposition = _load(DECOMPOSITION)
    by_parent = {entry["parent_artifact_id"]: entry for entry in decomposition["decompositions"]}
    for artifact in matrix["artifacts"]:
        assert not isinstance(artifact["migration_class"], list)
        if artifact.get("mixed_historical_object", False):
            assert artifact["artifact_id"] in by_parent
            children = by_parent[artifact["artifact_id"]]["children"]
            assert len(children) >= 2
            assert len({child["migration_class"] for child in children}) >= 2


def test_validator_rejects_prose_only_mixed_decomposition(tmp_path: Path):
    matrix = _load(MATRIX)
    unresolved = _load(UNRESOLVED)
    bad_matrix = tmp_path / "PREMERGER_ARTIFACT_MIGRATION_MATRIX_V1.json"
    ledger = tmp_path / "PREMERGER_UNRESOLVED_WORK_LEDGER_V1.json"
    bad_matrix.write_text(json.dumps(matrix), encoding="utf-8")
    ledger.write_text(json.dumps(unresolved), encoding="utf-8")
    with pytest.raises(ValueError, match="mixed artifact decomposition registry missing"):
        validate_migration_outputs(bad_matrix, ledger)


def test_navigation_metadata_never_confers_authority():
    matrix = _load(MATRIX)
    for artifact in matrix["artifacts"]:
        assert artifact.get("authority_basis") != "PR_OR_BRANCH_NAME"
        if artifact.get("source_pr") or artifact.get("source_branch"):
            assert artifact.get("authority_basis")


def test_task0_does_not_open_candidate_outcomes_or_protected_partitions():
    matrix = _load(MATRIX)
    unresolved = _load(UNRESOLVED)
    assert matrix["audit_boundaries"]["candidate_outcomes_opened"] is False
    assert matrix["audit_boundaries"]["reader_validation_opened"] is False
    assert matrix["audit_boundaries"]["reader_oracle_opened"] is False
    assert matrix["audit_boundaries"]["real_data_recomputed"] is False
    assert unresolved["audit_boundaries"] == matrix["audit_boundaries"]


def test_global_authority_is_unchanged():
    matrix = _load(MATRIX)
    unresolved = _load(UNRESOLVED)
    assert matrix["global_authority"] == GLOBAL_AUTHORITY
    assert unresolved["global_authority"] == GLOBAL_AUTHORITY


def test_validator_rejects_missing_class(tmp_path: Path):
    matrix = _load(MATRIX)
    unresolved = _load(UNRESOLVED)
    matrix["artifacts"][0].pop("migration_class")
    bad_matrix = tmp_path / "matrix.json"
    ledger = tmp_path / "ledger.json"
    bad_matrix.write_text(json.dumps(matrix), encoding="utf-8")
    ledger.write_text(json.dumps(unresolved), encoding="utf-8")
    with pytest.raises(ValueError, match="migration_class"):
        validate_migration_outputs(bad_matrix, ledger)


def test_validator_rejects_silent_authority_change(tmp_path: Path):
    matrix = _load(MATRIX)
    unresolved = _load(UNRESOLVED)
    matrix["global_authority"] = "TARGET_WINNER_C2"
    bad_matrix = tmp_path / "matrix.json"
    ledger = tmp_path / "ledger.json"
    bad_matrix.write_text(json.dumps(matrix), encoding="utf-8")
    ledger.write_text(json.dumps(unresolved), encoding="utf-8")
    with pytest.raises(ValueError, match="global authority"):
        validate_migration_outputs(bad_matrix, ledger)
