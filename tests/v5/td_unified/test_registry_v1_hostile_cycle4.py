from __future__ import annotations

from scripts.v5.td_unified.authority_v1 import QualificationStage
from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from scripts.v5.td_unified import registry_v1 as r
from tests.v5.td_unified.registry_v1_dependency_fixtures import verified_pair, verified_prereq


def _registry(dep, ref, prereq):
    return r.TDQualificationRegistry((dep, ref), (prereq,), (), ())


def test_external_prerequisite_evidence_must_match_requirement_class():
    dep, ref, deps = verified_pair(r)
    wrong = {
        "object_role": "PREREQUISITE_EVIDENCE",
        "requirement_class": "SOMETHING_ELSE",
        "status": "PASS",
    }
    wrong_sha = canonical_sha256(wrong)
    p = verified_prereq(
        r, dep, ref,
        requirement_class="EXTERNAL_CONTROL",
        evidence_receipt_sha=wrong_sha,
    )
    result = r.derive_real_reference_ready(
        "G8", _registry(dep, ref, p),
        dependency_verifier=deps.get,
        authority_object_resolver={wrong_sha: wrong}.get,
    )
    assert not result.ready
    assert any("requirement_class" in b or "requirement class" in b.lower() for b in result.blockers)


def test_content_validation_receipt_must_bind_prerequisite_and_content_identity():
    dep, ref, deps = verified_pair(r)
    vacuous = {"object_role": "CONTENT_VALIDATION_RECEIPT"}
    vacuous_sha = canonical_sha256(vacuous)
    p = verified_prereq(
        r, dep, ref,
        content_required=True,
        content_validated=True,
        content_validation_receipt_sha=vacuous_sha,
    )
    result = r.derive_real_reference_ready(
        "G8", _registry(dep, ref, p),
        dependency_verifier=deps.get,
        authority_object_resolver={vacuous_sha: vacuous}.get,
    )
    assert not result.ready
    assert any("content" in b.lower() and ("prerequisite" in b.lower() or "identity" in b.lower() or "validator" in b.lower()) for b in result.blockers)


def test_content_validation_receipt_cannot_bind_a_different_prerequisite():
    dep, ref, deps = verified_pair(r)
    bound = {
        "object_role": "CONTENT_VALIDATION_RECEIPT",
        "receipt_schema": "CONTENT_VALIDATION_RECEIPT_V1",
        "prerequisite_id": "OTHER",
        "content_identity_sha": ref.metric_sha,
        "validator_identity_sha": "f" * 64,
        "status": "QUALIFIED",
    }
    bound_sha = canonical_sha256(bound)
    p = verified_prereq(
        r, dep, ref,
        content_required=True,
        content_validated=True,
        content_validation_receipt_sha=bound_sha,
    )
    result = r.derive_real_reference_ready(
        "G8", _registry(dep, ref, p),
        dependency_verifier=deps.get,
        authority_object_resolver={bound_sha: bound}.get,
    )
    assert not result.ready
    assert any("content" in b.lower() and "prerequisite" in b.lower() for b in result.blockers)
