import dataclasses

import numpy as np
import pytest

from sea_ad_jepa.v5.audit_b_n1_execution_authority_v1 import (
    AuditBN1ExecutionAuthorityV1,
    AuditBN1PrimaryPrecisionReceiptV1,
    AuditBN1ToN2EscalationReceiptV1,
    B4_CONTRACT_SHA256,
    B4_RUNTIME_PREFLIGHT_SOURCE_SHA,
    ESCALATION_RECEIPT_ID,
    N1_TARGET_COUNT,
    N2_TARGET_COUNT,
    build_n2_escalation_receipt,
    summarize_n1_primary_values,
)


def test_n1_execution_authority_binds_verified_b4_and_preflight() -> None:
    a = AuditBN1ExecutionAuthorityV1(
        authority_id="JEPA_V5_FULL104_AUDIT_B_N1_EXECUTION_AUTHORITY_V1"
    )
    a.validate()
    assert a.b4_contract_sha256 == B4_CONTRACT_SHA256
    assert a.b4_runtime_preflight_source_sha == B4_RUNTIME_PREFLIGHT_SOURCE_SHA
    assert a.sample_level == "N1"
    assert a.target_count == 256
    assert a.n2_directly_authorized is False
    assert a.terminal_masking_authorized is False
    assert a.training_authorized is False
    assert len(a.canonical_digest()) == 64


def test_n1_precision_receipt_requires_exact_256_primary_values() -> None:
    with pytest.raises(ValueError, match="target count"):
        summarize_n1_primary_values(
            n1_result_sha256="1" * 64,
            target_values=np.zeros(255),
        )

    receipt = summarize_n1_primary_values(
        n1_result_sha256="1" * 64,
        target_values=np.zeros(N1_TARGET_COUNT),
    )
    assert receipt.n_targets == N1_TARGET_COUNT
    assert receipt.precision_passed is True
    assert receipt.threshold_branch == "ABSOLUTE_FLOOR"


def test_n2_cannot_exist_when_n1_precision_passed() -> None:
    receipt = summarize_n1_primary_values(
        n1_result_sha256="2" * 64,
        target_values=np.zeros(N1_TARGET_COUNT),
    )
    with pytest.raises(ValueError, match="N2_NOT_AUTHORIZED"):
        build_n2_escalation_receipt(receipt)


def test_n2_receipt_exists_only_after_frozen_primary_precision_failure() -> None:
    values = np.tile(np.array([-0.03, 0.03]), 128)
    precision = summarize_n1_primary_values(
        n1_result_sha256="3" * 64,
        target_values=values,
    )
    assert precision.precision_passed is False

    escalation = build_n2_escalation_receipt(precision)
    escalation.validate()
    assert escalation.receipt_id == ESCALATION_RECEIPT_ID
    assert escalation.precision_passed is False
    assert escalation.authorized_next_sample_level == "N2"
    assert escalation.authorized_next_target_count == N2_TARGET_COUNT
    assert escalation.terminal_masking_authorized is False
    assert escalation.training_authorized is False


def test_resealed_escalation_cannot_switch_to_n3_or_change_size() -> None:
    values = np.tile(np.array([-0.03, 0.03]), 128)
    precision = summarize_n1_primary_values(
        n1_result_sha256="4" * 64,
        target_values=values,
    )
    e = build_n2_escalation_receipt(precision)

    with pytest.raises(ValueError, match="N2 only"):
        dataclasses.replace(e, authorized_next_sample_level="N3").validate()
    with pytest.raises(ValueError, match="1024"):
        dataclasses.replace(e, authorized_next_target_count=4096).validate()
    with pytest.raises(ValueError, match="terminal masking"):
        dataclasses.replace(e, terminal_masking_authorized=True).validate()


def test_precision_receipt_cannot_change_policy_or_rung_after_n1() -> None:
    values = np.tile(np.array([-0.03, 0.03]), 128)
    r = summarize_n1_primary_values(
        n1_result_sha256="5" * 64,
        target_values=values,
    )
    with pytest.raises(ValueError, match="frozen primary policy"):
        dataclasses.replace(r, policy_id="TOP8_CORRELATION").validate()
    with pytest.raises(ValueError, match="frozen primary burden rung"):
        dataclasses.replace(r, rung_denominator=10).validate()


def test_b4_preflight_source_identity_is_git_commit_sha() -> None:
    a = AuditBN1ExecutionAuthorityV1(
        authority_id="JEPA_V5_FULL104_AUDIT_B_N1_EXECUTION_AUTHORITY_V1"
    )
    a.validate()
    assert len(a.b4_runtime_preflight_source_sha) == 40
    with pytest.raises(ValueError, match="40-hex Git commit SHA"):
        dataclasses.replace(a, b4_runtime_preflight_source_sha="0" * 64).validate()
