from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.masking_qualification_execution_authority_v1 import (
    MaskingQualificationExecutionAuthorityV1,
)


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="JEPA_V5_MASKING_QUALIFICATION_EXECUTION_AUTHORITY_V1",
        qualification_design_authority_sha256=h("design"),
        execution_source_sha256=h("execution-source"),
        result_artifact_sha256=h("result"),
        execution_status="EXECUTED_PASS",
        selected_policy_id="RIDGE8_CONDITIONAL",
        terminal_universe_status_id="FULL_COMMON_CORE_17186_EXECUTED_V1",
        controls_status_id="ALL_REQUIRED_CONTROLS_EXECUTED_PASS_V1",
        nonlinear_status_id="NONLINEAR_CHALLENGE_REPORTED_WITHOUT_RETUNING_V1",
        precision_status_id="BOUND_PRECISION_REQUIREMENTS_MET_V1",
        protected_outcomes_authorized=False,
    )
    values.update(updates)
    return MaskingQualificationExecutionAuthorityV1(**values)


def test_valid_pass_is_hash_bound_and_deterministic() -> None:
    a = authority()
    a.validate()
    assert a.passed is True
    assert a.canonical_digest() == authority().canonical_digest()


def test_nonexecution_and_skipped_statuses_are_rejected() -> None:
    for status in ("NOT_RUN", "SKIPPED", "PARTIAL", "PASS"):
        with pytest.raises(ValueError, match="execution_status"):
            authority(execution_status=status).validate()
    failed = authority(execution_status="EXECUTED_FAIL", selected_policy_id="NO_POLICY_QUALIFIED")
    failed.validate()
    assert failed.passed is False


def test_pass_requires_a_fixed_candidate_policy_and_fail_requires_none() -> None:
    with pytest.raises(ValueError, match="selected_policy_id"):
        authority(selected_policy_id="RIDGE8_TOP8_HYBRID").validate()
    with pytest.raises(ValueError, match="NO_POLICY_QUALIFIED"):
        authority(execution_status="EXECUTED_FAIL", selected_policy_id="RIDGE8_CONDITIONAL").validate()
    with pytest.raises(ValueError, match="candidate policy"):
        authority(execution_status="EXECUTED_PASS", selected_policy_id="NO_POLICY_QUALIFIED").validate()


def test_terminal_universe_controls_nonlinear_and_precision_must_be_explicit() -> None:
    fields = {
        "terminal_universe_status_id": "ONLY_6000_EXECUTED",
        "controls_status_id": "POSITIVE_ONLY",
        "nonlinear_status_id": "RETUNED_AFTER_RESULTS",
        "precision_status_id": "BELOW_TARGET_COUNT_BUT_OK",
    }
    for field, value in fields.items():
        with pytest.raises(ValueError, match=field):
            authority(**{field: value}).validate()


def test_execution_and_result_roots_are_real_distinct_hashes() -> None:
    with pytest.raises(ValueError, match="result_artifact_sha256"):
        authority(result_artifact_sha256="results.csv").validate()
    same = h("same")
    with pytest.raises(ValueError, match="distinct"):
        authority(execution_source_sha256=same, result_artifact_sha256=same).validate()


def test_live_design_binding_rejects_splice() -> None:
    a = authority()

    class Stub:
        training_authorized = False
        def __init__(self, digest: str): self._digest = digest
        def validate(self): return None
        def canonical_digest(self): return self._digest

    a.bind_qualification_design(Stub(a.qualification_design_authority_sha256))
    with pytest.raises(ValueError, match="qualification design root mismatch"):
        a.bind_qualification_design(Stub(h("other-design")))


def test_protected_outcomes_and_training_are_never_authorized() -> None:
    with pytest.raises(ValueError, match="protected outcomes"):
        authority(protected_outcomes_authorized=True).validate()
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()
