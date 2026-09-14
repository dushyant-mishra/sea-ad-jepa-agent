"""Fail-closed authority boundary for retrospective T0 V3 stress testing.

T0 can falsify/reject a prospective mechanism or allow it to proceed to an
independent FULL104 qualification.  It can never certify V5, authorize D_shared,
or supply V5 numerical/rank/null authority.
"""
from __future__ import annotations

from typing import Mapping, Sequence


class T0V3SandboxStop(RuntimeError):
    pass


_SCHEMA = "JEPA_V5_T0_V3_SANDBOX_RECEIPT_V1"
_ALLOWED_TERMINALS = {"REJECT_CANDIDATE", "ELIGIBLE_FOR_FULL104_QUALIFICATION"}
_RARE_TAIL_TERMINAL = "RARE_TAIL_UNDERDETERMINED_MEASUREMENT"
_REQUIRED_STRESS_TESTS = {
    "STRICT_NULL_CALIBRATION",
    "CONTROLLED_POSITIVE_SIGNAL",
    "SAME_CELL_MEASUREMENT_INTERVENTION",
    "RARE_TAIL_FALSIFICATION",
    "BROAD_STATE_NON_DESTRUCTION",
    "CROSS_FIT_VARIANCE_INFLATION",
}
_REQUIRED_FIELDS = {
    "schema",
    "candidate_id",
    "terminal",
    "stress_tests_executed",
    "historical_inputs_only",
    "synthetic_controls_used",
    "fresh_reader_validation_used",
    "fresh_at8_used",
    "oracle_or_protected_used",
    "rare_tail_terminal_preserved",
    "broad_state_used_as_acceptance_criterion",
    "permutation_significance_used_as_effect_magnitude",
    "effect_transport_claimed",
    "survivor_only_metrics_used",
    "unconditional_failure_accounting",
    "v5_numeric_thresholds_derived_from_t0",
    "v5_rank_rule_derived_from_t0",
    "v5_null_frozen_from_t0",
    "d_shared_outcomes_used",
    "d_shared_real_outcome_access_authorized",
    "training_authorized",
}


def validate_t0_v3_sandbox_receipt_v1(receipt: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(receipt, Mapping):
        raise ValueError("T0 V3 sandbox receipt must be a mapping")
    missing = sorted(_REQUIRED_FIELDS - set(receipt))
    if missing:
        raise T0V3SandboxStop(f"STOP_T0_V3_SANDBOX_MISSING:{','.join(missing)}")
    if receipt.get("schema") != _SCHEMA:
        raise T0V3SandboxStop("STOP_T0_V3_SANDBOX_SCHEMA")
    candidate = receipt.get("candidate_id")
    if not isinstance(candidate, str) or not candidate:
        raise T0V3SandboxStop("STOP_T0_V3_SANDBOX_CANDIDATE_ID")
    terminal = receipt.get("terminal")
    if terminal not in _ALLOWED_TERMINALS:
        raise T0V3SandboxStop("STOP_T0_V3_SANDBOX_TERMINAL")

    if receipt.get("historical_inputs_only") is not True:
        raise T0V3SandboxStop("STOP_T0_V3_SANDBOX_FORBIDDEN_INPUT:historical_inputs_only")
    for field in ("fresh_reader_validation_used", "fresh_at8_used", "oracle_or_protected_used"):
        if receipt.get(field) is not False:
            raise T0V3SandboxStop(f"STOP_T0_V3_SANDBOX_FORBIDDEN_INPUT:{field}")

    if receipt.get("rare_tail_terminal_preserved") != _RARE_TAIL_TERMINAL:
        raise T0V3SandboxStop("STOP_T0_V3_SANDBOX_RARE_TAIL_TERMINAL")
    if receipt.get("broad_state_used_as_acceptance_criterion") is not False:
        raise T0V3SandboxStop("STOP_T0_V3_SANDBOX_BROAD_STATE_TUNING")
    for field in ("v5_numeric_thresholds_derived_from_t0", "v5_rank_rule_derived_from_t0", "v5_null_frozen_from_t0"):
        if receipt.get(field) is not False:
            raise T0V3SandboxStop(f"STOP_T0_V3_SANDBOX_V5_TUNING:{field}")

    if receipt.get("permutation_significance_used_as_effect_magnitude") is not False or receipt.get("effect_transport_claimed") is not False:
        raise T0V3SandboxStop("STOP_T0_V3_SANDBOX_EFFECT_TRANSPORT")
    if receipt.get("survivor_only_metrics_used") is not False or receipt.get("unconditional_failure_accounting") is not True:
        raise T0V3SandboxStop("STOP_T0_V3_SANDBOX_FAILURE_ACCOUNTING")

    for field in ("d_shared_outcomes_used", "d_shared_real_outcome_access_authorized", "training_authorized"):
        if receipt.get(field) is not False:
            raise T0V3SandboxStop(f"STOP_T0_V3_SANDBOX_AUTHORITY_ESCALATION:{field}")

    executed = receipt.get("stress_tests_executed")
    if not isinstance(executed, Sequence) or isinstance(executed, (str, bytes)):
        raise T0V3SandboxStop("STOP_T0_V3_SANDBOX_STRESS_TEST_COVERAGE")
    normalized = {str(x) for x in executed}
    if terminal == "ELIGIBLE_FOR_FULL104_QUALIFICATION" and not _REQUIRED_STRESS_TESTS.issubset(normalized):
        raise T0V3SandboxStop("STOP_T0_V3_SANDBOX_STRESS_TEST_COVERAGE")

    return {
        "passed": True,
        "candidate_id": candidate,
        "terminal": terminal,
        "t0_can_certify_v5": False,
        "next_stage": (
            "FULL104_INDEPENDENT_MEASUREMENT_QUALIFICATION"
            if terminal == "ELIGIBLE_FOR_FULL104_QUALIFICATION"
            else "NONE__CANDIDATE_REJECTED"
        ),
        "v3_null_frozen": False,
        "rank_authority_frozen": False,
        "d_shared_real_outcome_access_authorized": False,
        "training_authorized": False,
    }
