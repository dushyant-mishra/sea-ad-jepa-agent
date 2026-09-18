from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.v5.masking_qualification_decision_v2 import evaluate_policy_v2
from sea_ad_jepa.v5.masking_terminal_evidence_assembly_v1 import (
    NONLINEAR_NULL_ESTIMAND_ID,
    PLANTED_DETECT_ESTIMAND_ID,
    PRIMARY_DELTA_ESTIMAND_ID,
    PRIMARY_NULL_ESTIMAND_ID,
    RAW_EVIDENCE_SCHEMA_ID,
    TerminalEvidenceAssemblySemanticsV1,
    TerminalPolicyRawEvidenceV1,
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
        if np.all(values == values.flat[0]):
            return _Interval(mean, mean, mean, mean, mean)
        span = float(np.max(np.abs(values - mean)))
        return _Interval(mean, mean - span, mean + span, mean - span, mean + span)


def matrices(target_count: int = 128):
    shape = (target_count, 104)
    source = np.array([0] * 40 + [1] * 34 + [2] * 30, dtype=np.int64)
    folds = np.arange(104, dtype=np.int64) % 4
    return shape, source, folds


def raw_bundle(target_count: int = 128, **updates):
    shape, source, folds = matrices(target_count)
    values = dict(
        policy_id="RIDGE8_CONDITIONAL",
        burden_numerator=1,
        burden_denominator=20,
        target_ids=[f"target-{i:04d}" for i in range(target_count)],
        donor_ids=[f"donor-{i:03d}" for i in range(104)],
        donor_source_code=source,
        donor_outer_fold=folds,
        source_names={0: "HVS", 1: "NPH52", 2: "SEA_AD"},
        policy_mask_sha256_by_target_fold=[
            [h(f"mask-{i}-{fold}") for fold in range(4)]
            for i in range(target_count)
        ],
        actual_policy_scores=np.full(shape, 0.10),
        actual_uniform_scores=np.full(shape, 0.20),
        shuffled_same_mask_scores=np.full(shape, 0.10),
        negative_control_delta=np.zeros(shape),
        planted_detect_excess=np.full(shape, 0.40),
        planted_after_mask_excess=np.zeros(shape),
        nonlinear_actual_scores=np.full(shape, 0.05),
        nonlinear_shuffled_same_mask_scores=np.full(shape, 0.05),
        effective_targeted_n_by_target_fold=np.full((target_count, 4), 7.0),
        replay_exact=True,
        untreated_identity_exact=True,
        no_privileged_metadata=True,
    )
    values.update(updates)
    return TerminalPolicyRawEvidenceV1(**values)


def assemble(**updates):
    return assemble_policy_decision_evidence(
        raw_evidence=raw_bundle(**updates),
        precision=PrecisionStub(),
    )


def test_semantics_freeze_is_explicit_and_preoutcome():
    s = TerminalEvidenceAssemblySemanticsV1()
    s.validate()
    assert s.primary_delta_estimand_id == PRIMARY_DELTA_ESTIMAND_ID
    assert s.primary_null_estimand_id == PRIMARY_NULL_ESTIMAND_ID
    assert s.planted_detect_estimand_id == PLANTED_DETECT_ESTIMAND_ID
    assert s.nonlinear_null_estimand_id == NONLINEAR_NULL_ESTIMAND_ID
    assert s.raw_evidence_schema_id == RAW_EVIDENCE_SCHEMA_ID
    assert s.terminal_outcomes_inspected_before_freeze is False
    assert s.training_authorized is False


def test_like_with_like_same_mask_null_can_qualify():
    raw = raw_bundle()
    evidence = assemble_policy_decision_evidence(raw_evidence=raw, precision=PrecisionStub())
    receipt = evaluate_policy_v2(evidence)
    assert evidence.raw_primary_evidence_sha256 == raw.primary_evidence_digest()
    assert evidence.raw_control_evidence_sha256 == raw.control_evidence_digest()
    assert evidence.raw_nonlinear_evidence_sha256 == raw.nonlinear_evidence_digest()
    assert evidence.delta_vs_uniform.mean == pytest.approx(0.10)
    assert evidence.excess_over_shuffled_null.mean == pytest.approx(0.0)
    assert evidence.nonlinear_excess_over_shuffled_null.mean == pytest.approx(0.0)
    assert receipt.qualified


def test_real_residual_above_same_mask_shuffled_null_fails():
    shape, _, _ = matrices()
    evidence = assemble(shuffled_same_mask_scores=np.zeros(shape))
    receipt = evaluate_policy_v2(evidence)
    assert evidence.excess_over_shuffled_null.mean == pytest.approx(0.10)
    assert not receipt.primary_null_level_passed
    assert not receipt.qualified


def test_source_balanced_target_delta_does_not_follow_donor_count():
    shape, source, _ = matrices()
    actual = np.full(shape, 0.20)
    uniform = actual.copy()
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
        raw_bundle(**{field: "PASS"})


def test_matrix_role_mismatch_fails_closed():
    with pytest.raises(ValueError, match="align target x donor"):
        raw_bundle(shuffled_same_mask_scores=np.zeros((128, 103)))


def test_precision_shortfall_fails_closed():
    with pytest.raises(ValueError, match="below frozen precision"):
        assemble_policy_decision_evidence(
            raw_evidence=raw_bundle(target_count=127),
            precision=PrecisionStub(),
        )


def test_exact_full104_donor_axis_is_required():
    shape = (128, 103)
    source = np.array([0] * 40 + [1] * 33 + [2] * 30, dtype=np.int64)
    folds = np.arange(103, dtype=np.int64) % 4
    with pytest.raises(ValueError, match="exactly 104 donors"):
        TerminalPolicyRawEvidenceV1(
            policy_id="RIDGE8_CONDITIONAL",
            burden_numerator=1,
            burden_denominator=20,
            target_ids=[f"t-{i}" for i in range(128)],
            donor_ids=[f"d-{i}" for i in range(103)],
            donor_source_code=source,
            donor_outer_fold=folds,
            source_names={0: "HVS", 1: "NPH52", 2: "SEA_AD"},
            policy_mask_sha256_by_target_fold=[
                [h(f"mask-{i}-{fold}") for fold in range(4)]
                for i in range(128)
            ],
            actual_policy_scores=np.zeros(shape),
            actual_uniform_scores=np.zeros(shape),
            shuffled_same_mask_scores=np.zeros(shape),
            negative_control_delta=np.zeros(shape),
            planted_detect_excess=np.zeros(shape),
            planted_after_mask_excess=np.zeros(shape),
            nonlinear_actual_scores=np.zeros(shape),
            nonlinear_shuffled_same_mask_scores=np.zeros(shape),
            effective_targeted_n_by_target_fold=np.zeros((128, 4)),
            replay_exact=True,
            untreated_identity_exact=True,
            no_privileged_metadata=True,
        )


def test_raw_roots_change_when_bound_matrix_changes():
    first = raw_bundle()
    changed = np.full((128, 104), 0.10)
    changed[0, 0] = 0.1000001
    second = raw_bundle(actual_policy_scores=changed)
    assert first.primary_evidence_digest() != second.primary_evidence_digest()
    assert first.canonical_digest() != second.canonical_digest()
    assert first.control_evidence_digest() == second.control_evidence_digest()
    assert first.nonlinear_evidence_digest() == second.nonlinear_evidence_digest()


def test_mask_identity_is_bound_into_primary_and_nonlinear_roots():
    first = raw_bundle()
    changed_masks = [
        [h(f"mask-{i}-{fold}") for fold in range(4)]
        for i in range(128)
    ]
    changed_masks[0][0] = h("different-mask")
    second = raw_bundle(policy_mask_sha256_by_target_fold=changed_masks)
    assert first.primary_evidence_digest() != second.primary_evidence_digest()
    assert first.nonlinear_evidence_digest() != second.nonlinear_evidence_digest()
    assert first.control_evidence_digest() == second.control_evidence_digest()


def test_mask_grid_must_cover_every_target_and_four_folds():
    bad = [[h("mask")] * 4 for _ in range(127)]
    with pytest.raises(ValueError, match="one row per target"):
        raw_bundle(policy_mask_sha256_by_target_fold=bad)


def test_raw_bundle_copies_and_freezes_input_arrays():
    original = np.full((128, 104), 0.10)
    raw = raw_bundle(actual_policy_scores=original)
    digest = raw.primary_evidence_digest()
    original[0, 0] = 999.0
    assert raw.actual_policy_scores[0, 0] == pytest.approx(0.10)
    assert raw.primary_evidence_digest() == digest
    with pytest.raises(ValueError):
        raw.actual_policy_scores[0, 0] = 2.0


def test_target_or_donor_identity_changes_root():
    first = raw_bundle()
    second = raw_bundle(target_ids=[f"other-{i:04d}" for i in range(128)])
    third = raw_bundle(donor_ids=[f"other-donor-{i:03d}" for i in range(104)])
    assert first.canonical_digest() != second.canonical_digest()
    assert first.canonical_digest() != third.canonical_digest()


def test_assembler_no_longer_accepts_free_raw_sha_arguments():
    raw = raw_bundle()
    with pytest.raises(TypeError):
        assemble_policy_decision_evidence(
            raw_evidence=raw,
            precision=PrecisionStub(),
            raw_primary_evidence_sha256=h("unrelated"),
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
