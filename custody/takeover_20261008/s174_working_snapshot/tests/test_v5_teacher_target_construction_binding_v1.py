from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.teacher_target_semantics_authority_v2 import (
    TeacherTargetSemanticsAuthorityV2,
    bind_teacher_semantics_to_target_construction_v1,
)


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def teacher(**updates):
    values = dict(
        authority_id="JEPA_V5_TEACHER_TARGET_SEMANTICS_V2",
        representation_authority_sha256=h("representation"),
        support_estimability_authority_sha256=h("support"),
        teacher_input_support_authority_sha256=h("teacher-input"),
        target_address_query_authority_sha256=h("address"),
        student_visible_support_authority_sha256=h("student-visible"),
        scientific_weight_authority_sha256=h("weight"),
        masking_authority_sha256=h("masking"),
        ema_boundary_authority_sha256=h("ema"),
        target_construction_authority_sha256=h("construction"),
        gradient_boundary_authority_sha256=h("gradient"),
        remaining_rna_necessity_authority_sha256=h("necessity"),
        state_semantics_id="BIOLOGICAL_CELLULAR_LATENT_STATE_V1",
        query_local_semantics_id="QUERY_LOCAL_STATE_CONDITIONED_ON_CANONICAL_ADDRESS_V1",
        scalar_expression_objective_policy_id="HIDDEN_GENE_SCALAR_RECONSTRUCTION_FORBIDDEN_V1",
        route_sufficiency_policy_id="REMAINING_RNA_REQUIRED__IDENTITY_ONLY_AND_GLOBAL_ONLY_INSUFFICIENT_V1",
    )
    values.update(updates)
    return TeacherTargetSemanticsAuthorityV2(**values)


class Stub:
    training_authorized = False
    def __init__(self, digest: str): self._digest = digest
    def validate(self): return None
    def canonical_digest(self): return self._digest


def test_teacher_semantics_binds_live_target_construction_root() -> None:
    t = teacher()
    bind_teacher_semantics_to_target_construction_v1(t, Stub(t.target_construction_authority_sha256))


def test_teacher_semantics_rejects_wrong_live_target_construction_root() -> None:
    t = teacher()
    with pytest.raises(ValueError, match="target construction authority root mismatch"):
        bind_teacher_semantics_to_target_construction_v1(t, Stub(h("wrong-construction")))


def test_target_construction_binding_rejects_training_authorized_object() -> None:
    t = teacher()

    class BadStub(Stub):
        training_authorized = True

    with pytest.raises(ValueError, match="unexpectedly authorizes training"):
        bind_teacher_semantics_to_target_construction_v1(t, BadStub(t.target_construction_authority_sha256))
