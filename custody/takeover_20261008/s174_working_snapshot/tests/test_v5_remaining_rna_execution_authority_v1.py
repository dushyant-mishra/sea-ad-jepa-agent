from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.remaining_rna_execution_authority_v1 import RemainingRnaExecutionAuthorityV1


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="JEPA_V5_REMAINING_RNA_EXECUTION_AUTHORITY_V1",
        remaining_rna_necessity_authority_sha256=h("necessity"),
        precision_authority_sha256=h("precision"),
        target_construction_authority_sha256=h("construction"),
        target_panel_authority_sha256=h("panel"),
        outer_split_authority_sha256=h("split"),
        healthy_teacher_source_authority_sha256=h("healthy-teacher-source"),
        result_artifact_sha256=h("result"),
        evidence_source_id="HEALTHY_CURRENT_V5_TEACHER_V1",
        execution_status="EXECUTED_PASS",
        state_metric_id="QUERY_LOCAL_LATENT_STATE_COSINE_SIMILARITY_V1",
        comparator_set_id="FULL_RNA__IDENTITY_ONLY__IDENTITY_PLUS_LAWFUL_GLOBAL_NO_RNA_V1",
    )
    values.update(updates)
    return RemainingRnaExecutionAuthorityV1(**values)


def test_valid_execution_evidence_is_deterministic() -> None:
    a = authority()
    a.validate()
    assert a.canonical_digest() == authority().canonical_digest()


def test_historical_t1_cannot_be_used_as_healthy_teacher_evidence() -> None:
    with pytest.raises(ValueError, match="evidence_source_id"):
        authority(evidence_source_id="HISTORICAL_T1_U200").validate()


def test_nonexecution_or_skipped_status_can_never_pass() -> None:
    for status in ("NOT_RUN", "SKIPPED", "PARTIAL", "PASS"):
        with pytest.raises(ValueError, match="execution_status"):
            authority(execution_status=status).validate()
    authority(execution_status="EXECUTED_FAIL").validate()


def test_required_roots_are_distinct_and_result_is_hash_bound() -> None:
    same = h("same")
    with pytest.raises(ValueError, match="distinct"):
        authority(precision_authority_sha256=same, target_panel_authority_sha256=same).validate()
    with pytest.raises(ValueError, match="result_artifact_sha256"):
        authority(result_artifact_sha256="results.csv").validate()


def test_state_metric_and_three_way_comparator_are_enumerated() -> None:
    with pytest.raises(ValueError, match="state_metric_id"):
        authority(state_metric_id="HIDDEN_GENE_MSE").validate()
    with pytest.raises(ValueError, match="comparator_set_id"):
        authority(comparator_set_id="FULL_VS_IDENTITY_ONLY").validate()


def test_passed_property_is_true_only_for_executed_pass() -> None:
    assert authority(execution_status="EXECUTED_PASS").passed is True
    assert authority(execution_status="EXECUTED_FAIL").passed is False


def test_live_binding_rejects_precision_splice() -> None:
    a = authority()

    class Stub:
        training_authorized = False
        def __init__(self, digest: str): self._digest = digest
        def validate(self): return None
        def canonical_digest(self): return self._digest

    a.bind_live_authorities(
        remaining_rna_necessity=Stub(a.remaining_rna_necessity_authority_sha256),
        precision=Stub(a.precision_authority_sha256),
        target_construction=Stub(a.target_construction_authority_sha256),
        target_panel=Stub(a.target_panel_authority_sha256),
        outer_split=Stub(a.outer_split_authority_sha256),
    )
    with pytest.raises(ValueError, match="precision authority root mismatch"):
        a.bind_live_authorities(
            remaining_rna_necessity=Stub(a.remaining_rna_necessity_authority_sha256),
            precision=Stub(h("wrong-precision")),
            target_construction=Stub(a.target_construction_authority_sha256),
            target_panel=Stub(a.target_panel_authority_sha256),
            outer_split=Stub(a.outer_split_authority_sha256),
        )


def test_execution_evidence_cannot_authorize_training() -> None:
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()
