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
import json
import os
from pathlib import Path

from scripts.v5 import jepa_synth2048_attempt_journal_v2 as journal
from scripts.v5 import jepa_v5_full_state_readonly_audit_v1 as state

SCHEMA = "JEPA_V5_SYNTHETIC_STRUCTURED_JOURNAL_PREFLIGHT_V1"
AUTHORITY = journal.AUTHORITY
# Process-local binding prevents accidental changes to the run's gene axis,
# manifest, Philox contract or keyed seed between recorded updates.
# New processes cannot continue V2 updates at all. Not external custody.
_OPENING_CONTRACTS: dict[tuple[int, str], dict] = {}
# Macha #575 review: the u0 model/optimizer structure (tensor names, shapes,
# dtypes, optimizer group layout). Every later commit must match it, so a
# reshaped or missing module cannot become the "last probe-pass" checkpoint.
_OPENING_STRUCTURE: dict[tuple[int, str], str] = {}


def _structure_sha256(bundle: dict) -> str:
    """Digest of structure only: names, shapes, dtypes; never tensor values."""
    modules = {
        label: sorted((name, list(t.shape), str(t.dtype))
                      for name, t in bundle["modules"][label].items())
        for label in sorted(bundle["modules"])
    }
    layout = sorted((name, list(d["shape"]), d["dtype"])
                    for name, d in bundle["parameter_layout"].items())
    # Optimizer state_dict uses integer IDs and positional param_groups.
    # The same tensor shapes/counts are insufficient to prove that the
    # moments still belong to the SAME named parameters at every update.
    # Normalize IDs to names, retaining exact ordered group membership.
    by_id = {desc["optimizer_param_id"]: name
             for name, desc in bundle["parameter_layout"].items()}
    groups = [[by_id[pid] for pid in group["params"]]
              for group in bundle["optimizer"]["param_groups"]]
    raw = json.dumps({"modules": modules, "layout": layout, "groups": groups},
                     sort_keys=True, separators=(",", ":")).encode("ascii")
    return sha256(raw).hexdigest()


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
                           philox_contract_sha256: str,
                           keyed_run_seed: int) -> dict:
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
    insist(type(keyed_run_seed) is int and 0 <= keyed_run_seed < 2**32,
           "KEYED_SEED_INVALID")
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
        "keyed_run_seed": keyed_run_seed,
        "execution_authorized": False,
        "training_authorized": False,
    }
    for name, value in require.items():
        insist(meta.get(name) == value and
               (type(meta.get(name)) is type(value)),
               "STRUCTURED_METADATA_BINDING_" + name.upper())
    insist("online.value_encoder.weight" in bundle["parameter_names"],
           "EXPRESSION_VALUE_ENCODER_MISSING")
    online_state = bundle["modules"]["online"]
    teacher_state = bundle["modules"]["teacher"]
    insist(set(online_state) == set(teacher_state),
           "TEACHER_ONLINE_PARAMETER_OR_BUFFER_NAMES_MISMATCH")
    for name, online_tensor in online_state.items():
        teacher_tensor = teacher_state[name]
        insist(tuple(teacher_tensor.shape) == tuple(online_tensor.shape)
               and teacher_tensor.dtype == online_tensor.dtype,
               "TEACHER_ONLINE_TENSOR_SHAPE_DTYPE_MISMATCH")
    insist(report["actual_step_or_bitwise_resume_proved"] is False
           and report["biological_health_proved"] is False
           and report["training_authorized"] is False,
           "STRUCTURED_STATE_CLAIMS_UNPROVEN_AUTHORITY")
    return {
        "schema": SCHEMA,
        "snapshot_sha256": digest,
        "snapshot_bytes": len(raw),
        "structure_sha256": _structure_sha256(bundle),
        "state_update": expected_update,
        "model_component_names": report["model_modules"],
        "all_trainable_parameter_names_present":
            report["all_trainable_parameter_names_present"],
        "optimizer_tensor_count": report["optimizer_tensor_count"],
        "has_expression_value_encoder": True,
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
              philox_contract_sha256: str,
              keyed_run_seed: int) -> dict:
    return {
        "run_id": run_id, "panel_sha256": panel_sha256,
        "config_sha256": config_sha256,
        "rights_sha256": rights_sha256,
        "gene_axis_sha256": gene_axis_sha256,
        "source_manifest_sha256": source_manifest_sha256,
        "philox_contract_sha256": philox_contract_sha256,
        "keyed_run_seed": keyed_run_seed,
    }


def open_synthetic_journal(*, root: Path, custody: Path,
                           run_id: str, horizon: int,
                           panel_sha256: str, config_sha256: str,
                           rights_sha256: str, gene_axis_sha256: str,
                           source_manifest_sha256: str,
                           philox_contract_sha256: str,
                           keyed_run_seed: int,
                           state_bytes: bytes, reported_probe: dict) -> dict:
    """Validate u0 *before* creating a run folder or emitting any bytes."""
    args = _run_args(run_id, panel_sha256, config_sha256,
                     rights_sha256, gene_axis_sha256,
                     source_manifest_sha256, philox_contract_sha256,
                     keyed_run_seed)
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
    _OPENING_CONTRACTS[(os.getpid(), str(Path(root).absolute()))] = args
    _OPENING_STRUCTURE[(os.getpid(), str(Path(root).absolute()))] =         check["structure_sha256"]
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
                               expected_philox_contract_sha256: str,
                               expected_keyed_run_seed: int) -> dict:
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
        expected_philox_contract_sha256,
        expected_keyed_run_seed)
    insist(_OPENING_CONTRACTS.get(
        (os.getpid(), str(Path(root).absolute()))) == args,
        "OPENING_PROCESS_CONTRACT_CHANGED_OR_UNKNOWN")
    check = check_structured_bytes(
        state_bytes, expected_update=update, **args)
    insist(_OPENING_STRUCTURE.get((os.getpid(), str(Path(root).absolute())))
           == check["structure_sha256"],
           "MODEL_OR_OPTIMIZER_STRUCTURE_CHANGED_SINCE_U0")
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
        expected_philox_contract_sha256: str,
        expected_keyed_run_seed: int) -> dict:
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
            expected_philox_contract_sha256,
            expected_keyed_run_seed))
    return {
        "status": "RETRIEVED_FORENSIC_STRUCTURED_COMPONENTS",
        "state": check,
        "biological_health_proved": False,
        "resume_authorized": False,
        "training_authorized": False,
        "authority": AUTHORITY,
    }
