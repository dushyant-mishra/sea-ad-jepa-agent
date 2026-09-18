from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.v5.masking_qualification_decision_v2 import evaluate_policy_v2
from sea_ad_jepa.v5.masking_terminal_evidence_assembly_v1 import (
    PRIMARY_DELTA_ESTIMAND_ID,
    PRIMARY_NULL_ESTIMAND_ID,
    PLANTED_DETECT_ESTIMAND_ID,
    NONLINEAR_NULL_ESTIMAND_ID,
    TerminalEvidenceAssemblySemanticsV1,
    assemble_policy_decision_evidence,
)


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True)
class _Interval:
    mean: float
    lower_two_sided: float
    upper_two_sided: float
    lower_one_sided: float
    upper_one_sided: float


class PrecisionStub:
    required_target_count = 128

    def validate(self):
        return None

    def assert_sufficient(self, *, target_count, donor_count, outer_fold_count):
        if target_count < 128 or donor_count < 104 or outer_fold_count < 4:
            raise ValueError("below frozen precision")

    def canonical_digest(self):
        return h("precision")

    def interval(self, matrix, donor_source_code):
        values = np.asarray(matrix, dtype=float)
        mean = float(np.mean(values))
        # Exact intervals are intentional for constant synthetic matrices.
        if np.all(values == values.flat[0]):
            return _Interval(mean, mean, mean, mean, mean)
        # Deterministic conservative test-only envelope around the mean.
        span = float(np.max(np.abs(values - mean)))
        return _Interval(mean, mean - span, mean + span, mean - span, mean + span)


def matrices():
    shape = (128, 104)
    source = np.array([0] * 40 + [1] * 34 + [2] * 30, dtype=np.int64)
    return shape, source


def assemble(**updates):
    shape, source = matrices()
    values = dict(
        policy_id="RIDGE8_CONDITIONAL",
        burden_numerator=1,
        burden_denominator=20,
        actual_policy_scores=np.full(shape, 0.10),
        actual_uniform_scores=np.full(shape, 0.20),
        shuffled_same_mask_scores=np.full(shape, 0.10),
        negative_control_delta=np.zeros(shape),
        planted_detect_excess=np.full(shape, 0.40),
        planted_after_mask_excess=np.zeros(shape),
        nonlinear_actual_scores=np.full(shape, 0.05),
        nonlinear_shuffled_same_mask_scores=np.full(shape, 0.05),
        effective_targeted_n_by_target_fold=np.full((128, 4), 7.0),
        donor_source_code=source,
        source_names={0: "HVS", 1: "NPH52", 2: "SEA_AD"},
        precision=PrecisionStub(),
        raw_primary_evidence_sha256=h("primary"),
        raw_control_evidence_sha256=h("control"),
        raw_nonlinear_evidence_sha256=h("nonlinear"),
        replay_exact=True,
        untreated_identity_exact=True,
        no_privileged_metadata=True,
    )
    values.update(updates)
    return assemble_policy_decision_evidence(**values)


def test_semantics_freeze_is_explicit_and_preoutcome():
    s = TerminalEvidenceAssemblySemanticsV1()
    s.validate()
    assert s.primary_delta_estimand_id == PRIMARY_DELTA_ESTIMAND_ID
    assert s.primary_null_estimand_id == PRIMARY_NULL_ESTIMAND_ID
    assert s.planted_detect_estimand_id == PLANTED_DETECT_ESTIMAND_ID
    assert s.nonlinear_null_estimand_id == NONLINEAR_NULL_ESTIMAND_ID
    assert s.terminal_outcomes_inspected_before_freeze is False
    assert s.training_authorized is False


def test_like_with_like_same_mask_null_can_qualify():
    evidence = assemble()
    receipt = evaluate_policy_v2(evidence)
    assert evidence.delta_vs_uniform.mean == pytest.approx(0.10)
    assert evidence.excess_over_shuffled_null.mean == pytest.approx(0.0)
    assert evidence.nonlinear_excess_over_shuffled_null.mean == pytest.approx(0.0)
    assert receipt.qualified


def test_real_residual_above_same_mask_shuffled_null_fails():
    shape, _ = matrices()
    evidence = assemble(shuffled_same_mask_scores=np.zeros(shape))
    receipt = evaluate_policy_v2(evidence)
    assert evidence.excess_over_shuffled_null.mean == pytest.approx(0.10)
    assert not receipt.primary_null_level_passed
    assert not receipt.qualified


def test_source_balanced_target_delta_does_not_follow_donor_count():
    shape, source = matrices()
    actual = np.full(shape, 0.20)
    uniform = actual.copy()
    # Source deltas 0, 0, 0.30. Equal-source mean is 0.10 even though SEA_AD
    # has the fewest donors in this synthetic geometry.
    uniform[:, source == 2] = 0.50
    evidence = assemble(
        actual_policy_scores=actual,
        actual_uniform_scores=uniform,
        shuffled_same_mask_scores=actual,
    )
    assert evidence.target_delta_median == pytest.approx(0.10)
    assert evidence.worst_target_delta == pytest.approx(0.10)


def test_targeting_complexity_is_target_by_fold_not_donor_weighted():
    counts = np.zeros((128, 4), dtype=float)
    counts[:, 3] = 8.0
    evidence = assemble(effective_targeted_n_by_target_fold=counts)
    assert evidence.mean_effective_targeted_n == pytest.approx(2.0)


@pytest.mark.parametrize(
    "field",
    ("replay_exact", "untreated_identity_exact", "no_privileged_metadata"),
)
def test_free_status_strings_cannot_enter_mechanical_booleans(field):
    with pytest.raises(ValueError, match="mechanically computed boolean"):
        assemble(**{field: "PASS"})


def test_matrix_role_mismatch_fails_closed():
    with pytest.raises(ValueError, match="align target x donor"):
        assemble(shuffled_same_mask_scores=np.zeros((128, 103)))


def test_precision_shortfall_fails_closed():
    shape, source = matrices()
    with pytest.raises(ValueError, match="below frozen precision"):
        assemble_policy_decision_evidence(
            policy_id="RIDGE8_CONDITIONAL",
            burden_numerator=1,
            burden_denominator=20,
            actual_policy_scores=np.zeros((127, 104)),
            actual_uniform_scores=np.zeros((127, 104)),
            shuffled_same_mask_scores=np.zeros((127, 104)),
            negative_control_delta=np.zeros((127, 104)),
            planted_detect_excess=np.ones((127, 104)),
            planted_after_mask_excess=np.zeros((127, 104)),
            nonlinear_actual_scores=np.zeros((127, 104)),
            nonlinear_shuffled_same_mask_scores=np.zeros((127, 104)),
            effective_targeted_n_by_target_fold=np.zeros((127, 4)),
            donor_source_code=source,
            source_names={0: "HVS", 1: "NPH52", 2: "SEA_AD"},
            precision=PrecisionStub(),
            raw_primary_evidence_sha256=h("primary"),
            raw_control_evidence_sha256=h("control"),
            raw_nonlinear_evidence_sha256=h("nonlinear"),
            replay_exact=True,
            untreated_identity_exact=True,
            no_privileged_metadata=True,
        )


def test_terminal_evidence_source_has_no_historical_or_calibration_input_path():
    source = Path(
        "src/sea_ad_jepa/v5/masking_terminal_evidence_assembly_v1.py"
    ).read_text(encoding="utf-8")
    forbidden = (
        "analysis/v5_masking_successor_spike_20260917",
        "analysis/v5_masking_v2_20260916",
        "stage81a3",
        "X_common6000",
        "CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1",
        "training_authorized=True",
        "protected_outcomes_authorized=True",
    )
    assert [token for token in forbidden if token in source] == []
