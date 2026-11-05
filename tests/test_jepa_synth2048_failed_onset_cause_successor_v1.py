"""Scope-only #560 repair tests: self-reported cause is NOT physical neural proof.

Macha #557 and #560 tests are inherited unchanged and exercised in the workflow.
NO model, optimizer, EMA, external trust anchor, trainer or biological qualification.
"""
from __future__ import annotations

from copy import deepcopy
import pytest

from scripts.v5 import jepa_synth2048_checkpoint_capture_prefreeze_v1 as c
from tests.test_jepa_synth2048_checkpoint_capture_prefreeze_v1 import complete_update


def failed(u=13):
    row = complete_update(u)
    row.update(success=False, optimizer_step_proved=False,
               ema_completed_after_optimizer=False, presentation_cursor_advanced=False)
    return row


def probe(metric="cell_centered_energy"):
    return {
        "metric": metric,
        "observed": 0.0,
        "u0_reference": 0.25,
        "probe_panel_sha256": "a" * 64,
        "operator_homogeneous_eval_mode": True,
        "identical_gene_sets": True,
    }


@pytest.mark.parametrize(("flag", "value", "cause"), [
    ("exact_zero_protected_gradients", 48, "DEAD_PROTECTED_GRADIENTS"),
    ("amp_skipped_step", True, "AMP_SKIP"),
    ("query_visible_to_student", True, "QUERY_LEAK"),
    ("finite_state", False, "NONFINITE_STATE"),
    ("missing_or_nonfinite_moments", 1, "MISSING_OR_NONFINITE_ADAM"),
])
def test_unchanged_legacy_mechanical_receipts_get_a_reported_cause(flag, value, cause):
    row = failed()
    row[flag] = value
    result = c.validate_failed_attempt_onset_receipt(row)
    assert result["failure_cause"] == cause
    assert result["failure_cause_origin"] == "INFERRED_FROM_UNVERIFIED_LEGACY_MECHANICS"
    assert result["resumable_or_authorizing"] is False
    assert result["causal_mechanism_independently_verified"] is False


@pytest.mark.parametrize(("cause", "metric"), [
    ("CELL_CONSTANT", "cell_centered_energy"),
    ("IDENTITY_ONLY_GENE_TOKENS", "same_gene_cross_cell_variance"),
    ("EXPRESSION_RESPONSE_ZERO", "same_cell_expression_shuffle_delta"),
])
def test_explicit_representation_collapse_cause_requires_exact_probe(cause, metric):
    row = failed()
    row["failure_cause"] = cause
    row["collapse_evidence"] = probe(metric)
    result = c.validate_failed_attempt_onset_receipt(row)
    assert result["failure_cause"] == cause
    assert result["collapse_probe_self_reported"]["observed"] == 0
    assert result["physical_gradient_or_adam_moment_evidence_verified"] is False
    assert result["resumable_or_authorizing"] is False


def test_uncaused_failure_refused_without_real_mechanics_signal():
    with pytest.raises(c.CaptureRefusal, match="UNCAUSED_FAILED_ATTEMPT"):
        c.validate_failed_attempt_onset_receipt(failed())


@pytest.mark.parametrize("mutation", [
    {"failure_cause": "CELL_CONSTANT"},
    {"failure_cause": "UNKNOWN_STOP"},
    {"failure_cause": "AMP_SKIP"},
    {"failure_cause": None},
])
def test_cause_must_be_present_and_consistent_with_signal(mutation):
    row = failed()
    row.update(mutation)
    with pytest.raises(c.CaptureRefusal):
        c.validate_failed_attempt_onset_receipt(row)


@pytest.mark.parametrize(("field", "value"), [
    ("observed", 1e-12),           # near collapse is telemetry, not exact STOP
    ("observed", -1.0),
    ("observed", float("nan")),
    ("observed", True),
    ("u0_reference", 0.0),
    ("u0_reference", float("inf")),
    ("probe_panel_sha256", "not-a-frozen-probe"),
    ("operator_homogeneous_eval_mode", False),
    ("identical_gene_sets", False),
    ("metric", "same_gene_cross_cell_variance"),
])
def test_unsubstantiated_exact_collapse_claim_refused(field, value):
    row = failed()
    row["failure_cause"] = "CELL_CONSTANT"
    row["collapse_evidence"] = probe()
    row["collapse_evidence"][field] = value
    with pytest.raises(c.CaptureRefusal):
        c.validate_failed_attempt_onset_receipt(row)


def test_mechanics_cause_rejects_irrelevant_collapse_payload():
    row = failed()
    row.update(amp_skipped_step=True, failure_cause="AMP_SKIP",
               collapse_evidence=probe())
    with pytest.raises(c.CaptureRefusal):
        c.validate_failed_attempt_onset_receipt(row)


def test_reported_cause_is_not_physical_evidence_or_training_authority():
    row = failed()
    row.update(failure_cause="EXPRESSION_RESPONSE_ZERO",
               collapse_evidence=probe("same_cell_expression_shuffle_delta"))
    result = c.validate_failed_attempt_onset_receipt(row)
    assert result["causal_mechanism_independently_verified"] is False
    assert result["physical_gradient_or_adam_moment_evidence_verified"] is False
    assert result["resumable_or_authorizing"] is False
    assert c.AUTHORITY.endswith("REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED")
