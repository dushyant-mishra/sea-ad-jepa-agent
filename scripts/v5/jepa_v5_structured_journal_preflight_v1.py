#!/usr/bin/env python3
"""V5 read-only CPU checkpoint validation -> V2 synthetic journal bridge.

No optimizer step, backward, model forward, model loader, GPU, dataset access or
real training. The caller's metrics and synthetic Adam contents are NOT proof
that a step happened or that biological representation was learned.

This adapter rejects malformed/mismatched full-state *component* snapshots
BEFORE an otherwise allowed synthetic V2 UPDATE_COMMITTED can write a file.
It does not add a new kind of V2 scientific outcome or restart authority.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from scripts.v5 import jepa_synth2048_attempt_journal_v2 as journal
from scripts.v5 import jepa_v5_full_state_readonly_audit_v1 as state

SCHEMA = "JEPA_V5_SYNTHETIC_STRUCTURED_JOURNAL_PREFLIGHT_V1"
AUTHORITY = journal.AUTHORITY


class StructuredJournalRefusal(ValueError):
    pass


def insist(ok: object, reason: str) -> None:
    if not bool(ok):
        raise StructuredJournalRefusal("REFUSE_STRUCTURED_JOURNAL_V1__" + reason)


def _sha_match(value: object, name: str) -> None:
    insist(type(value) is str and len(value) == 64
           and all(c in "0123456789abcdef" for c in value),
           "INVALID_SHA_" + name.upper())


def check_structured_bytes(raw: bytes, *, expected_update: int,
                           run_id: str, panel_sha256: str,
                           config_sha256: str, rights_sha256: str,
                           gene_axis_sha256: str,
                           source_manifest_sha256: str,
                           philox_contract_sha256: str) -> dict:
    """Check state *structure and declarations*; never the truth of training.

    All expected binding SHAs are supplied by the caller, not authenticated
    against a signed source or dataset. The V2 journal persists panel/config/
    rights only; gene-axis/source/Philox need a future independently locked
    execution contract and source-authenticated provenance.
    """
    insist(type(raw) is bytes and 0 < len(raw) <= journal.MAX_STATE,
           "STRUCTURED_STATE_BYTES_INVALID_OR_OVERSIZE")
    insist(type(expected_update) is int and 0 <= expected_update <= 99999,
           "UPDATE_INVALID")
    for key, val in (("gene_axis", gene_axis_sha256),
                     ("source_manifest", source_manifest_sha256),
                     ("philox_contract", philox_contract_sha256)):
        _sha_match(val, key)
    digest = sha256(raw).hexdigest()
    try:
        bundle, report = state.read_verified_bytes(
            raw, expected_sha256=digest)
    except state.FullStateRefusal as exc:
        raise StructuredJournalRefusal(
            "REFUSE_STRUCTURED_JOURNAL_V1__INVALID_FULL_STATE_COMPONENTS"
        ) from exc
    meta = bundle["metadata"]
    require = {
        "run_id": run_id,
        "completed_updates": expected_update,
        "ema_updates": expected_update,
        "panel_sha256": panel_sha256,
        "config_sha256": config_sha256,
        "source_rights_sha256": rights_sha256,
        "gene_axis_sha256": gene_axis_sha256,
        "source_manifest_sha256": source_manifest_sha256,
        "keyed_philox_contract_sha256": philox_contract_sha256,
        "execution_authorized": False,
        "training_authorized": False,
    }
    for name, value in require.items():
        insist(meta.get(name) == value and
               (type(meta.get(name)) is type(value)),
               "STRUCTURED_METADATA_BINDING_" + name.upper())
    insist(report["actual_step_or_bitwise_resume_proved"] is False
           and report["biological_health_proved"] is False
           and report["training_authorized"] is False,
           "STRUCTURED_STATE_CLAIMS_UNPROVEN_AUTHORITY")
    return {
        "schema": SCHEMA,
        "snapshot_sha256": digest,
        "snapshot_bytes": len(raw),
        "state_update": expected_update,
        "model_component_names": report["model_modules"],
        "all_trainable_parameter_names_present":
            report["all_trainable_parameter_names_present"],
        "optimizer_tensor_count": report["optimizer_tensor_count"],
        "has_expression_value_encoder": (
            "online.value_encoder.weight" in bundle["parameter_names"]
        ),
        "physically_executed_optimizer_step_proved": False,
        "probe_computation_origin_proved": False,
        "learned_biology_proved": False,
        "resume_authorized": False,
        "training_authorized": False,
        "authority": AUTHORITY,
    }


def _run_args(run_id: str, panel_sha256: str,
              config_sha256: str, rights_sha256: str,
              gene_axis_sha256: str, source_manifest_sha256: str,
              philox_contract_sha256: str) -> dict:
    return {
        "run_id": run_id, "panel_sha256": panel_sha256,
        "config_sha256": config_sha256,
        "rights_sha256": rights_sha256,
        "gene_axis_sha256": gene_axis_sha256,
        "source_manifest_sha256": source_manifest_sha256,
        "philox_contract_sha256": philox_contract_sha256,
    }


def open_synthetic_journal(*, root: Path, custody: Path,
                           run_id: str, horizon: int,
                           panel_sha256: str, config_sha256: str,
                           rights_sha256: str, gene_axis_sha256: str,
                           source_manifest_sha256: str,
                           philox_contract_sha256: str,
                           state_bytes: bytes, reported_probe: dict) -> dict:
    """Validate u0 *before* creating a run folder or emitting any bytes."""
    args = _run_args(run_id, panel_sha256, config_sha256,
                     rights_sha256, gene_axis_sha256,
                     source_manifest_sha256, philox_contract_sha256)
    check = check_structured_bytes(
        state_bytes, expected_update=0, **args)
    lock = journal._run_lock(
        run_id=run_id, horizon=horizon, panel_sha256=panel_sha256,
        config_sha256=config_sha256, rights_sha256=rights_sha256)
    journal._validate_probe(
        reported_probe, update=0,
        state_sha256=check["snapshot_sha256"], lock=lock)
    result = journal.open_journal(
        root, custody, run_id=run_id, horizon=horizon,
        panel_sha256=panel_sha256,
        config_sha256=config_sha256, rights_sha256=rights_sha256,
        initial_state_bytes=state_bytes, initial_probe=reported_probe)
    insist(result["training_authorized"] is False,
           "JOURNAL_PROMOTED_TRAINING")
    return {
        "status": "SYNTHETIC_U0_STRUCTURED_BYTES_RECORDED",
        "run_id": run_id, "state": check,
        "neural_state_health_proved": False,
        "resume_authorized": False, "training_authorized": False,
    }


def commit_synthetic_preflight(*, root: Path, custody: Path,
                               update: int, state_bytes: bytes,
                               reported_probe: dict,
                               expected_gene_axis_sha256: str,
                               expected_source_manifest_sha256: str,
                               expected_philox_contract_sha256: str) -> dict:
    """Fail closed before any V2 write if an Adam/model/metadata slot is bad.

    Requires ATTEMPT_BEGIN to have already been durably recorded by V2.
    The snapshot is *synthetic*: no optimizer activity is performed here.
    """
    root, custody = journal._paths(root, custody)
    lock = journal._binding(root, custody)
    args = _run_args(
        lock["run_id"], lock["panel_sha256"],
        lock["config_sha256"], lock["rights_sha256"],
        expected_gene_axis_sha256,
        expected_source_manifest_sha256,
        expected_philox_contract_sha256)
    check = check_structured_bytes(
        state_bytes, expected_update=update, **args)
    journal._validate_probe(
        reported_probe, update=update,
        state_sha256=check["snapshot_sha256"], lock=lock)
    outcome = journal.commit_reported_update(
        root, custody, update=update,
        state_bytes=state_bytes,
        panel_sha256=lock["panel_sha256"],
        probe=reported_probe)
    insist(outcome["training_authorized"] is False
           and outcome["resumable"] is False,
           "JOURNAL_PROMOTED_RESUME_OR_TRAINING")
    return {
        "status": "SYNTHETIC_COMPONENTS_CHECKED_AND_REPORTED_COMMIT",
        "journal": outcome,
        "state": check,
        "biological_health_proved": False,
        "optimizer_step_executed_by_bridge": False,
        "resume_authorized": False,
        "training_authorized": False,
        "authority": AUTHORITY,
    }


def inspect_stored_structured_snapshot(
        *, root: Path, custody: Path, update: int,
        expected_gene_axis_sha256: str,
        expected_source_manifest_sha256: str,
        expected_philox_contract_sha256: str) -> dict:
    """Read-only forensic scan, plus safe full-state component check.

    A SHA-valid reported probe checkpoint is not a proven HEALTHY state.
    No torch module is constructed and no optimizer/model is restored.
    """
    root, custody = journal._paths(root, custody)
    lock, _issues = journal._forensic_binding(root, custody)
    raw = journal.read_forensic_opaque_state(
        root, custody, update=update)
    check = check_structured_bytes(
        raw, expected_update=update, **_run_args(
            lock["run_id"], lock["panel_sha256"],
            lock["config_sha256"], lock["rights_sha256"],
            expected_gene_axis_sha256,
            expected_source_manifest_sha256,
            expected_philox_contract_sha256))
    return {
        "status": "RETRIEVED_FORENSIC_STRUCTURED_COMPONENTS",
        "state": check,
        "biological_health_proved": False,
        "resume_authorized": False,
        "training_authorized": False,
        "authority": AUTHORITY,
    }
