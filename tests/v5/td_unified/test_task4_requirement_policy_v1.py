import pytest

from scripts.v5.td_unified.task4_requirement_policy_v1 import (
    RequirementClass,
    Task4RequirementError,
    validate_requirement_evidence,
)


def test_requirement_class_is_closed():
    with pytest.raises(ValueError):
        RequirementClass("DYNAMIC_UNKNOWN")


def test_nonunit_requires_matching_authorized_independent_issuer_and_content():
    req = {"requirement_class": "PROCESS_ISOLATION"}
    good = {
        "requirement_class": "PROCESS_ISOLATION",
        "issuer_identity_sha": "issuer",
        "content_validated": True,
    }
    ctx = {
        "roles_by_actor": {"issuer": "HARNESS"},
        "prohibited_issuer_actor_ids": {"producer"},
    }
    validate_requirement_evidence(req, good, actor_context=ctx)

    for bad in [
        {"requirement_class": "PROCESS_ISOLATION", "content_validated": True},
        {**good, "requirement_class": "CROSS_PROCESS_LEDGER_CUSTODY"},
        {**good, "issuer_identity_sha": "producer"},
        {**good, "content_validated": False},
    ]:
        with pytest.raises(Task4RequirementError):
            validate_requirement_evidence(req, bad, actor_context=ctx)


def test_bare_role_label_cannot_satisfy_requirement():
    with pytest.raises(Task4RequirementError):
        validate_requirement_evidence(
            {"requirement_class": "CHALLENGE_GENERATOR_POLICY"},
            {"object_role": "CHALLENGE_GENERATOR_POLICY"},
            actor_context={"roles_by_actor": {}},
        )
