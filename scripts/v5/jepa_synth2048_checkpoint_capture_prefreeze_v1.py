#!/usr/bin/env python3
"""Design-only, fail-closed V5 synthetic JEPA checkpoint-cadence/receipt preflight.

NO GPU, model import, optimizer, EMA update, training, or authorization.

A future reviewed trainer must implement physically atomic payload writes,
real telemetry, SHA-verified fresh-process resume, and evidence-specific
nonpromotion. Passing this contract's unit tests never proves those actions.
"""
from __future__ import annotations

from hashlib import sha256
from math import isfinite
import json
from pathlib import Path
from typing import Mapping, Sequence


SCHEMA = "JEPA_SYNTH2048_V5_FINE_GRAIN_CHECKPOINT_PREFREEZE_V1"
TRACE_SCHEMA = "JEPA_SYNTH2048_V5_CHECKPOINT_MECHANICS_RECEIPT_SHAPE_V1"
AUTHORITY = (
    "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__"
    "STAGE4_NOT_AUTHORIZED"
)
SOURCE_V5_HEAD = "cde03f738c758694aa66211b5021603af943675b"
SOURCE_FIT_SHA256 = "87fe3ec2038305c797c439cd9780036fe22cc22b647242749b1af0bfb444c06f"
REQUIRED_STOP_FIELDS = frozenset((
    "update_index", "success", "optimizer_step_proved",
    "ema_completed_after_optimizer", "presentation_cursor_advanced",
    "protected_attention_tensor_count", "missing_or_nonfinite_gradients",
    "exact_zero_protected_gradients", "missing_or_nonfinite_moments",
    "exact_zero_protected_adam_moments", "teacher_gradient_count",
    "amp_skipped_step", "query_visible_to_student", "finite_state",
    "telemetry_committed"
))


class CaptureRefusal(ValueError):
    pass


def refuse_unless(ok: bool, reason: str) -> None:
    if not bool(ok):
        raise CaptureRefusal("STOP_V5_SYNTH2048_CHECKPOINT__" + reason)


def exact_integer(value: object, name: str) -> int:
    refuse_unless(type(value) is int and 0 <= value <= 10000, name + "_INVALID")
    return value


def canonical_checkpoint_steps(max_completed_update: int) -> tuple[int, ...]:
    """Prospective *proposal*: early dense capture, then predeclared spacing.

    Every successful u1..u40 gets a full immutable checkpoint.
    u41..100 checkpoint on every fifth update.
    Above u100 checkpoint on every tenth update.
    Terminal completed update is always retained, even if not on a grid.
    Every attempted update, including failures, requires independent telemetry.
    """
    n = exact_integer(max_completed_update, "MAX_UPDATE")
    refuse_unless(n > 0, "HORIZON_MUST_BE_POSITIVE")
    required = {0, n}
    required.update(range(1, min(40, n) + 1))
    required.update(range(45, min(100, n) + 1, 5))
    required.update(range(110, n + 1, 10))
    return tuple(sorted(required))


def _is_sha256(value: object) -> bool:
    return (type(value) is str and len(value) == 64
            and all(ch in "0123456789abcdef" for ch in value))


def read_prefreeze_contract(contract: Mapping[str, object]) -> dict[str, object]:
    """Reject any attempt to turn a plan into training permission."""
    refuse_unless(type(contract) is dict, "CONTRACT_TYPE")
    expected_keys = {
        "schema", "status", "v5_source_head", "fit_sha256", "checkpoint_schedule",
        "telemetry", "payload_requirements", "rights_and_evaluation",
        "gates", "training_authorized", "execution_authorized",
        "requires_macha_review", "requires_separate_owner_authorization",
        "authority",
    }
    refuse_unless(set(contract) == expected_keys, "CONTRACT_FIELDS_CHANGED")
    refuse_unless(contract["schema"] == SCHEMA, "CONTRACT_SCHEMA")
    refuse_unless(
        contract["status"] == "PROPOSAL_NOT_FROZEN__INDEPENDENT_REVIEW_REQUIRED",
        "PROPOSAL_PROMOTED"
    )
    refuse_unless(contract["v5_source_head"] == SOURCE_V5_HEAD, "V5_SOURCE_DRIFT")
    refuse_unless(contract["fit_sha256"] == SOURCE_FIT_SHA256, "FIT_SOURCE_DRIFT")
    refuse_unless(contract["authority"] == AUTHORITY, "AUTHORITY_CHANGED")
    refuse_unless(contract["training_authorized"] is False
                  and contract["execution_authorized"] is False,
                  "UNAUTHORIZED_TRAINING")
    refuse_unless(contract["requires_macha_review"] is True
                  and contract["requires_separate_owner_authorization"] is True,
                  "REVIEW_OR_OWNER_GATE_REMOVED")
    schedule = contract["checkpoint_schedule"]
    refuse_unless(type(schedule) is dict and schedule == {
        "u0": True,
        "u1_through_u40": "EVERY_SUCCESSFUL_UPDATE",
        "u41_through_u100": "EVERY_FIFTH_SUCCESSFUL_UPDATE",
        "above_u100": "EVERY_TENTH_SUCCESSFUL_UPDATE",
        "terminal_update": "ALWAYS",
        "failed_attempt": "TELEMETRY_AND_LAST_PREVIOUS_VALID_ONLY",
        "full_payload_only_at_completed_update_boundary": True,
        "update_cadence_precommitted_and_not_loss_adaptive": True,
        "training_horizon_selected": False,
    }, "CHECKPOINT_SCHEDULE_DRIFT")
    t = contract["telemetry"]
    refuse_unless(type(t) is dict and t.get("frequency") == "EVERY_ATTEMPTED_UPDATE",
                  "PER_UPDATE_TELEMETRY_MISSING")
    refuse_unless(set(t.get("mandatory_fields", ())) == REQUIRED_STOP_FIELDS,
                  "TELEMETRY_REQUIRED_FIELDS_CHANGED")
    refuse_unless(t.get("biology_and_shortcut_telemetry_required_at_reviewed_probe_windows") is True,
                  "BIOLOGY_SHORTCUT_DIAGNOSTICS_DROPPED")
    p = contract["payload_requirements"]
    refuse_unless(type(p) is dict
                  and set(p.get("state_components", ())) == {
                      "online_encoder", "ema_teacher", "predictor",
                      "optimizer_with_adam_moments", "grad_scaler",
                      "protected_gradient_proof", "completed_step_ema_proof",
                      "masking_rng", "python_rng", "numpy_rng", "torch_cpu_rng",
                      "torch_cuda_rngs", "presentation_cursor", "schedule_cursor",
                      "raw_cell_and_gene_token_telemetry",
                      "exact_source_dataset_config_and_evidence_rights_sha256",
                  }, "CHECKPOINT_FIELDS_CHANGED")
    refuse_unless(p.get("write_once_atomic_fsync_sha256_manifest") is True
                  and p.get("verified_fresh_process_resume_before_continue") is True
                  and p.get("do_not_save_invalid_as_resumable") is True
                  and p.get("require_replay_identity") is True,
                  "CRASH_OR_RESTART_PROTECTION_REMOVED")
    rights = contract["rights_and_evaluation"]
    refuse_unless(type(rights) is dict
                  and rights.get("q_exclusion_verified_at_every_update") is True
                  and rights.get("no_query_derived_depth") is True
                  and rights.get("source_donor_disjoint_split") is True
                  and rights.get("blinded_protected_test_not_used_for_tuning") is True
                  and rights.get("prospective_eval_panel_freeze_before_run") is True,
                  "QUERY_SOURCE_OR_BLIND_RIGHTS_REMOVED")
    gates = contract["gates"]
    refuse_unless(type(gates) is dict
                  and gates.get("actual_unscaled_48_gradient_and_adam_moment_proof_each_step") is True
                  and gates.get("no_ema_on_skipped_optimizer") is True
                  and gates.get("raw_cell_and_gene_token_collapse_monitoring") is True
                  and gates.get("loss_not_biology") is True
                  and gates.get("synthetic_cpu_gpu_parity_required_before_gpu") is True,
                  "HISTORICAL_COLLAPSE_GATES_REMOVED")
    return dict(contract)


def validate_update_mechanics_receipt(receipt: Mapping[str, object]) -> None:
    """Illustrative shape and STOP enforcement, not proof a real step was done."""
    refuse_unless(type(receipt) is dict
                  and set(receipt) == REQUIRED_STOP_FIELDS, "STEP_TELEMETRY_INCOMPLETE")
    exact_integer(receipt["update_index"], "UPDATE")
    refuse_unless(receipt["update_index"] > 0, "UPDATE_MUST_BE_POSITIVE")
    for key in ("success", "optimizer_step_proved", "ema_completed_after_optimizer",
                "presentation_cursor_advanced", "amp_skipped_step",
                "query_visible_to_student", "finite_state", "telemetry_committed"):
        refuse_unless(type(receipt[key]) is bool, key + "_MUST_BE_BOOL")
    for key in ("protected_attention_tensor_count", "missing_or_nonfinite_gradients",
                "exact_zero_protected_gradients", "missing_or_nonfinite_moments",
                "exact_zero_protected_adam_moments", "teacher_gradient_count"):
        exact_integer(receipt[key], key)
    refuse_unless(receipt["telemetry_committed"], "STEP_TELEMETRY_NOT_COMMITTED")
    refuse_unless(not receipt["amp_skipped_step"], "AMP_STEP_SKIPPED")
    refuse_unless(not receipt["query_visible_to_student"], "QUERY_LEAK")
    refuse_unless(receipt["finite_state"], "NONFINITE_STATES")
    refuse_unless(receipt["protected_attention_tensor_count"] == 48,
                  "PROTECTED_48_REGISTRY_DRIFT")
    for key in ("missing_or_nonfinite_gradients", "exact_zero_protected_gradients",
                "missing_or_nonfinite_moments", "exact_zero_protected_adam_moments",
                "teacher_gradient_count"):
        refuse_unless(receipt[key] == 0, key.upper() + "_FAIL")
    refuse_unless(receipt["success"] and receipt["optimizer_step_proved"]
                  and receipt["ema_completed_after_optimizer"]
                  and receipt["presentation_cursor_advanced"],
                  "INCOMPLETE_OPTIMIZER_TO_EMA_CHAIN")



# Every failure must have an independently identifiable *reported* cause.
# Legacy mechanical V1 receipts are interpreted from their existing numeric fields;
# representation failure requires an explicit cause plus a numeric probe.
# None of these caller-provided values constitutes physical neural evidence.
COLLAPSE_CAUSE_METRIC = {
    "CELL_CONSTANT": "cell_centered_energy",
    "IDENTITY_ONLY_GENE_TOKENS": "same_gene_cross_cell_variance",
    "EXPRESSION_RESPONSE_ZERO": "same_cell_expression_shuffle_delta",
}


def _reported_mechanics_causes(receipt: Mapping[str, object]) -> list[str]:
    signals = {
        "DEAD_PROTECTED_GRADIENTS": receipt["exact_zero_protected_gradients"] > 0,
        "MISSING_OR_NONFINITE_GRADIENTS": receipt["missing_or_nonfinite_gradients"] > 0,
        "MISSING_OR_NONFINITE_ADAM": receipt["missing_or_nonfinite_moments"] > 0,
        "ZERO_ADAM_MOMENTS": receipt["exact_zero_protected_adam_moments"] > 0,
        "AMP_SKIP": receipt["amp_skipped_step"],
        "QUERY_LEAK": receipt["query_visible_to_student"],
        "NONFINITE_STATE": not receipt["finite_state"],
        "TEACHER_GRADIENTS": receipt["teacher_gradient_count"] > 0,
        "PROTECTED_GRADIENT_REGISTRY_DRIFT": (
            receipt["protected_attention_tensor_count"] != 48
        ),
    }
    return [name for name, observed in signals.items() if observed]


def _validate_collapse_evidence(cause: str, evidence: object) -> dict:
    """Validate exact-collapse *reported* panel evidence, never inferred biology."""
    refuse_unless(type(evidence) is dict
                  and set(evidence) == {
                      "metric", "observed", "u0_reference", "probe_panel_sha256",
                      "operator_homogeneous_eval_mode", "identical_gene_sets",
                  }, "COLLAPSE_EVIDENCE_FIELDS")
    refuse_unless(evidence["metric"] == COLLAPSE_CAUSE_METRIC[cause],
                  "COLLAPSE_CAUSE_METRIC_MISMATCH")
    for name in ("observed", "u0_reference"):
        value = evidence[name]
        refuse_unless(type(value) in (int, float) and isfinite(value)
                      and value >= 0, "COLLAPSE_" + name.upper() + "_INVALID")
    # Do not treat near-zero or genuinely low-rank biology as an exact STOP.
    refuse_unless(evidence["observed"] == 0
                  and evidence["u0_reference"] > 0, "NO_EXACT_COLLAPSE_ON_PROBE")
    refuse_unless(_is_sha256(evidence["probe_panel_sha256"]),
                  "COLLAPSE_PANEL_ID_INVALID")
    refuse_unless(evidence["operator_homogeneous_eval_mode"] is True
                  and evidence["identical_gene_sets"] is True,
                  "COLLAPSE_PANEL_NOT_COMPARABLE")
    return dict(evidence)


def validate_failed_attempt_onset_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    """Record the first failed attempt with its *reported* cause; never resume it.

    The unchanged Macha #557 tests send legacy mechanical failure receipts.
    Their explicit nonzero gradients/AMP-skip flags remain supported as
    inferred untrusted causes; an uncaused receipt fails Macha #560.
    A representation collapse requires a named cause and exact-zero probe
    evidence on a fixed, comparable TRAIN panel. Physical F2/F3/F4 remain open.
    """
    refuse_unless(type(receipt) is dict, "FAILED_ATTEMPT_TELEMETRY_INCOMPLETE")
    extras = set(receipt) - REQUIRED_STOP_FIELDS
    refuse_unless(REQUIRED_STOP_FIELDS.issubset(receipt)
                  and extras in (
                      set(), {"failure_cause"},
                      {"failure_cause", "collapse_evidence"},
                  ), "FAILED_ATTEMPT_TELEMETRY_INCOMPLETE")
    exact_integer(receipt["update_index"], "FAILED_ATTEMPT_UPDATE")
    refuse_unless(receipt["update_index"] > 0, "FAILED_ATTEMPT_INDEX")
    for key in ("success", "optimizer_step_proved", "ema_completed_after_optimizer",
                "presentation_cursor_advanced", "amp_skipped_step",
                "query_visible_to_student", "finite_state", "telemetry_committed"):
        refuse_unless(type(receipt[key]) is bool,
                      "FAILED_ATTEMPT_" + key.upper() + "_TYPE")
    for key in ("protected_attention_tensor_count", "missing_or_nonfinite_gradients",
                "exact_zero_protected_gradients", "missing_or_nonfinite_moments",
                "exact_zero_protected_adam_moments", "teacher_gradient_count"):
        exact_integer(receipt[key], key)
    refuse_unless(receipt["telemetry_committed"] is True, "FAILED_ONSET_NOT_RECORDED")
    refuse_unless(receipt["success"] is False, "FAILED_ONSET_MUST_NOT_PASS")
    refuse_unless(receipt["optimizer_step_proved"] is False
                  and receipt["ema_completed_after_optimizer"] is False
                  and receipt["presentation_cursor_advanced"] is False,
                  "FAILED_ONSET_CLAIMS_OPTIMIZER_OR_EMA")

    signals = _reported_mechanics_causes(receipt)
    cause = receipt.get("failure_cause")
    origin = "EXPLICIT_UNVERIFIED_TELEMETRY"
    probe = None
    if cause is None and "failure_cause" not in receipt:
        # Compatibility for unchanged #557 and #558 mechanically failing inputs:
        # derive the cause ONLY from an observed nonzero/true mechanical field.
        refuse_unless(bool(signals), "UNCAUSED_FAILED_ATTEMPT")
        cause = signals[0]
        origin = "INFERRED_FROM_UNVERIFIED_LEGACY_MECHANICS"
    else:
        refuse_unless(type(cause) is str, "FAILURE_CAUSE_TYPE")
        if cause in COLLAPSE_CAUSE_METRIC:
            refuse_unless("collapse_evidence" in receipt,
                          "COLLAPSE_EVIDENCE_REQUIRED")
            probe = _validate_collapse_evidence(
                cause, receipt["collapse_evidence"]
            )
        else:
            refuse_unless(cause in signals, "UNSUPPORTED_OR_UNOBSERVED_CAUSE")
            refuse_unless("collapse_evidence" not in receipt,
                          "MECHANICS_WITH_UNRELATED_COLLAPSE_EVIDENCE")
    return {
        "status": "FAILED_ATTEMPT_RETAINED_AS_UNTRUSTED_STOP_EVIDENCE",
        "attempt_update_index": receipt["update_index"],
        "failure_cause": cause,
        "failure_cause_origin": origin,
        "other_reported_mechanical_causes": [s for s in signals if s != cause],
        "collapse_probe_self_reported": probe,
        "protected_attention_tensors_reported": receipt["protected_attention_tensor_count"],
        "exact_zero_gradients_reported": receipt["exact_zero_protected_gradients"],
        "missing_or_nonfinite_gradients_reported": receipt["missing_or_nonfinite_gradients"],
        "amp_skip_reported": receipt["amp_skipped_step"],
        "query_leak_reported": receipt["query_visible_to_student"],
        "nonfinite_state_reported": not receipt["finite_state"],
        "resumable_or_authorizing": False,
        "physical_gradient_or_adam_moment_evidence_verified": False,
        "causal_mechanism_independently_verified": False,
    }



def verify_capture_inventory(
    *,
    horizon: int,
    checkpoints: Sequence[Mapping[str, object]],
    per_update_receipts: Sequence[Mapping[str, object]],
    root: Path,
) -> dict[str, object]:
    """Simulated receipt inventory requiring actual SHA-256 bytes and no gaps.

    Future training needs independent proof that payloads are valid and resumable
    beyond these descriptive/identity checks.
    """
    required = canonical_checkpoint_steps(horizon)
    refuse_unless(len(checkpoints) == len(required), "MISSING_CHECKPOINT_WINDOW")
    # horizon denotes COMPLETED updates. At most one final, failed u(horizon+1)
    # is retained as observational STOP evidence. Never call it a checkpoint.
    refuse_unless(
        len(per_update_receipts) in (horizon, horizon + 1), "UPDATE_TELEMETRY_GAPS"
    )
    for i, row in enumerate(per_update_receipts[:horizon], start=1):
        validate_update_mechanics_receipt(row)
        refuse_unless(row["update_index"] == i, "UPDATE_SEQUENCE_CHANGED")
    failed_attempt = None
    if len(per_update_receipts) == horizon + 1:
        failed_attempt = validate_failed_attempt_onset_receipt(
            per_update_receipts[horizon]
        )
        refuse_unless(failed_attempt["attempt_update_index"] == horizon + 1,
                      "FAILED_ATTEMPT_OUT_OF_ORDER")
    folder = root.resolve()
    for row, step in zip(checkpoints, required):
        refuse_unless(type(row) is dict
                      and set(row) == {"update", "filename", "sha256", "bytes"},
                      "CHECKPOINT_RECEIPT_FIELDS")
        refuse_unless(type(row["update"]) is int and row["update"] == step,
                      "CHECKPOINT_SEQUENCE_CHANGED")
        filename = f"u{step:05d}.checkpoint"
        refuse_unless(type(row["filename"]) is str
                      and row["filename"] == filename, "CHECKPOINT_FILENAME")
        refuse_unless(_is_sha256(row["sha256"]), "CHECKPOINT_SHA_INVALID")
        refuse_unless(type(row["bytes"]) is int and row["bytes"] > 0,
                      "CHECKPOINT_BYTES_INVALID")
        target = folder / filename
        refuse_unless(target.is_file() and not target.is_symlink()
                      and target.resolve().parent == folder, "CHECKPOINT_PATH_UNSAFE")
        data = target.read_bytes()
        refuse_unless(len(data) == row["bytes"]
                      and sha256(data).hexdigest() == row["sha256"],
                      "CHECKPOINT_BYTE_SHA_FAILED")
    return {
        "schema": TRACE_SCHEMA,
        "status": "PREFREEZE_RECEIPT_SHAPE_AND_FILE_SHA_TEST_ONLY",
        "required_completed_checkpoints": list(required),
        "update_telemetry_windows": len(per_update_receipts),
        "last_valid_completed_update": horizon,
        "failed_attempt_recorded": failed_attempt is not None,
        "failed_attempt": failed_attempt,
        "failed_attempt_never_authorizes_resumable_checkpoint": True,
        "all_telemetry_is_self_reported_not_physical_evidence": True,
        "actual_neural_updates_verified": False,
        "actual_resume_parity_verified": False,
        "training_authorized": False,
        "authority": AUTHORITY,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--illustrative-horizon", type=int, default=60)
    args = p.parse_args()
    plan = read_prefreeze_contract(json.loads(args.plan.read_text()))
    steps = canonical_checkpoint_steps(args.illustrative_horizon)
    print(json.dumps({
        "status": plan["status"], "source_fit_sha256": SOURCE_FIT_SHA256,
        "illustrative_horizon_only": args.illustrative_horizon,
        "checkpoint_updates": list(steps),
        "full_checkpoint_count": len(steps),
        "per_attempt_telemetry_required": args.illustrative_horizon,
        "model_training": False, "execution_authorized": False
    }, sort_keys=True))


if __name__ == "__main__":
    main()
