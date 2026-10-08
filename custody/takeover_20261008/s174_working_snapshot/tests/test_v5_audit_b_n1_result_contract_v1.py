import dataclasses

import numpy as np
import pytest

from sea_ad_jepa.v5.audit_b_n1_result_contract_v1 import (
    AuditBN1ResultReceiptV1,
    EXPECTED_TENSOR_SHAPE,
    N1_EXECUTION_AUTHORITY_SHA256,
    POLICY_ORDER,
    RUNG_ORDER,
    aggregate_target_values,
    array_sha256,
    primary_target_values,
    validate_n1_arrays,
)


def _fixture():
    targets = np.arange(256, dtype=np.int64)
    source = np.array([0] * 41 + [2] * 46 + [1] * 17, dtype=np.int64)
    # Deliberately source-dependent donor values so source-balanced != donor-uniform.
    detected = np.zeros(EXPECTED_TENSOR_SHAPE, dtype=np.float64)
    umi = np.zeros_like(detected)
    detected[..., source == 0] = 0.2
    detected[..., source == 1] = 0.9
    detected[..., source == 2] = 0.5
    umi[...] = detected * 2
    return targets, source, detected, umi


def test_complete_n1_artifact_geometry_is_required() -> None:
    targets, source, detected, umi = _fixture()
    out = validate_n1_arrays(
        target_cols=targets,
        donor_normalized_delta_detected=detected,
        donor_normalized_delta_umi=umi,
        expected_target_cols=targets,
        donor_source_code=source,
    )
    assert out["donor_normalized_delta_detected"].shape == EXPECTED_TENSOR_SHAPE

    with pytest.raises(ValueError, match="shape"):
        validate_n1_arrays(
            target_cols=targets,
            donor_normalized_delta_detected=detected[:-1],
            donor_normalized_delta_umi=umi,
            expected_target_cols=targets,
            donor_source_code=source,
        )


def test_exact_frozen_n1_target_order_is_required() -> None:
    targets, source, detected, umi = _fixture()
    wrong = targets.copy()
    wrong[[0, 1]] = wrong[[1, 0]]
    with pytest.raises(ValueError, match="prefix order"):
        validate_n1_arrays(
            target_cols=wrong,
            donor_normalized_delta_detected=detected,
            donor_normalized_delta_umi=umi,
            expected_target_cols=targets,
            donor_source_code=source,
        )


def test_source_balanced_and_donor_uniform_are_independently_recomputable() -> None:
    _, source, detected, _ = _fixture()
    agg = aggregate_target_values(detected, source)
    # Equal source mass: (0.2 + 0.9 + 0.5) / 3
    assert np.allclose(agg["source_balanced"], (0.2 + 0.9 + 0.5) / 3)
    # Equal donor mass uses 41/17/46 donor composition.
    expected = (41 * 0.2 + 17 * 0.9 + 46 * 0.5) / 104
    assert np.allclose(agg["donor_uniform"], expected)
    assert not np.allclose(agg["source_balanced"], agg["donor_uniform"])


def test_primary_values_are_extracted_only_from_ridge8_at_first_rung() -> None:
    _, source, detected, _ = _fixture()
    p = POLICY_ORDER.index("RIDGE8_CONDITIONAL")
    r = RUNG_ORDER.index((1, 20))
    detected[:, p, r, :] = 0.123
    values = primary_target_values(detected, source)
    assert values.shape == (256,)
    assert np.allclose(values, 0.123)


def test_nonfinite_donor_burden_fails_closed() -> None:
    targets, source, detected, umi = _fixture()
    detected[0, 0, 0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        validate_n1_arrays(
            target_cols=targets,
            donor_normalized_delta_detected=detected,
            donor_normalized_delta_umi=umi,
            expected_target_cols=targets,
            donor_source_code=source,
        )


def test_result_receipt_cannot_rebind_authority_or_expand_scope() -> None:
    targets, source, detected, umi = _fixture()
    receipt = AuditBN1ResultReceiptV1(
        result_artifact_sha256="1" * 64,
        target_cols_sha256=array_sha256(targets, dtype="<i8"),
        donor_normalized_delta_detected_sha256=array_sha256(detected, dtype="<f8"),
        donor_normalized_delta_umi_sha256=array_sha256(umi, dtype="<f8"),
        donor_source_code_sha256=array_sha256(source, dtype="<i8"),
    )
    receipt.validate()
    assert receipt.n1_execution_authority_sha256 == N1_EXECUTION_AUTHORITY_SHA256
    assert len(receipt.canonical_digest()) == 64

    with pytest.raises(ValueError, match="N1 execution authority"):
        dataclasses.replace(
            receipt,
            n1_execution_authority_sha256="2" * 64,
        ).validate()
    with pytest.raises(ValueError, match="terminal_masking_authorized"):
        dataclasses.replace(receipt, terminal_masking_authorized=True).validate()
