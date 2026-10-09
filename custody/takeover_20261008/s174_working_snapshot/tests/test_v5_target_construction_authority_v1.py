from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.target_construction_authority_v1 import TargetConstructionAuthorityV1


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="JEPA_V5_TARGET_CONSTRUCTION_AUTHORITY_V1",
        representation_authority_sha256=h("representation"),
        support_estimability_authority_sha256=h("support"),
        target_address_provider_authority_sha256=h("address"),
        implementation_source_sha256=h("implementation"),
        query_identity_policy_id="QUERY_IDENTITY_SUPPLIED_V1",
        query_scalar_policy_id="QUERY_SCALAR_WITHHELD_BEFORE_CONTEXT_MIXING_V1",
        non_query_rna_policy_id="NON_QUERY_LAWFUL_RNA_VISIBLE_V1",
        global_context_policy_id="LAWFUL_GLOBAL_BIOLOGICAL_CONTEXT_ALLOWED_V1",
        teacher_gradient_policy_id="TEACHER_STOPGRAD_V1",
        scalar_expression_objective_policy_id="SCALAR_EXPRESSION_OBJECTIVE_ABSENT_V1",
        target_state_policy_id="QUERY_LOCAL_BIOLOGICAL_LATENT_STATE_V1",
    )
    values.update(updates)
    return TargetConstructionAuthorityV1(**values)


def test_valid_target_construction_is_deterministic() -> None:
    a = authority()
    a.validate()
    assert a.canonical_digest() == authority().canonical_digest()


def test_exact_implementation_and_upstream_roots_are_required_and_distinct() -> None:
    with pytest.raises(ValueError, match="implementation_source_sha256"):
        authority(implementation_source_sha256="target.py").validate()
    same = h("same")
    with pytest.raises(ValueError, match="distinct"):
        authority(representation_authority_sha256=same, support_estimability_authority_sha256=same).validate()


def test_query_identity_is_available_but_query_scalar_is_not() -> None:
    with pytest.raises(ValueError, match="query_identity_policy_id"):
        authority(query_identity_policy_id="QUERY_IDENTITY_MASKED").validate()
    with pytest.raises(ValueError, match="query_scalar_policy_id"):
        authority(query_scalar_policy_id="QUERY_SCALAR_VISIBLE_TO_TEACHER").validate()


def test_lawful_nonquery_rna_and_global_context_semantics_are_explicit() -> None:
    with pytest.raises(ValueError, match="non_query_rna_policy_id"):
        authority(non_query_rna_policy_id="DROP_ALL_RNA").validate()
    with pytest.raises(ValueError, match="global_context_policy_id"):
        authority(global_context_policy_id="FREE_DONOR_ID_EMBEDDING").validate()


def test_teacher_is_stopgrad_and_hidden_gene_scalar_objective_is_absent() -> None:
    with pytest.raises(ValueError, match="teacher_gradient_policy_id"):
        authority(teacher_gradient_policy_id="BACKPROP_THROUGH_TEACHER").validate()
    with pytest.raises(ValueError, match="scalar_expression_objective_policy_id"):
        authority(scalar_expression_objective_policy_id="PREDICT_HIDDEN_GENE_VALUE").validate()
    with pytest.raises(ValueError, match="target_state_policy_id"):
        authority(target_state_policy_id="HIDDEN_GENE_SCALAR").validate()


def test_live_binder_rejects_wrong_address_provider_role() -> None:
    a = authority()

    class Stub:
        training_authorized = False
        def __init__(self, digest: str): self._digest = digest
        def validate(self): return None
        def canonical_digest(self): return self._digest

    a.bind_live_authorities(
        representation=Stub(a.representation_authority_sha256),
        support_estimability=Stub(a.support_estimability_authority_sha256),
        target_address_provider=Stub(a.target_address_provider_authority_sha256),
    )
    with pytest.raises(ValueError, match="target address provider root mismatch"):
        a.bind_live_authorities(
            representation=Stub(a.representation_authority_sha256),
            support_estimability=Stub(a.support_estimability_authority_sha256),
            target_address_provider=Stub(h("wrong-address")),
        )


def test_target_construction_cannot_authorize_training() -> None:
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()
