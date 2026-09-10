import copy
import pytest

from sea_ad_jepa.v5.qualification_phase_contract_v1 import (
    POST_QUALIFICATION_EVIDENCE,
    PRE_EXECUTION_EVIDENCE,
    build_postqualification_bundle,
    build_preexecution_bundle,
    validate_postqualification_bundle,
    validate_preexecution_bundle,
)


def pre_evidence():
    return {
        name: {
            "status": "EXECUTED_PASS",
            "artifact_sha256": format(i + 1, "064x"),
            "authority_id": f"{name}-authority-v1",
            "training_authorized": False,
        }
        for i, name in enumerate(PRE_EXECUTION_EVIDENCE)
    }


def pre_bundle():
    return build_preexecution_bundle(
        pre_evidence(), design_context_sha256="a" * 64, optimizer_started=False
    )


def post_evidence(checkpoint="b" * 64, context="a" * 64):
    return {
        name: {
            "status": "EXECUTED_PASS",
            "artifact_sha256": format(i + 100, "064x"),
            "authority_id": f"{name}-authority-v1",
            "training_authorized": False,
            "design_context_sha256": context,
            "qualification_checkpoint_sha256": checkpoint,
        }
        for i, name in enumerate(POST_QUALIFICATION_EVIDENCE)
    }


def post_bundle(pre=None):
    return build_postqualification_bundle(
        post_evidence(),
        preexecution_bundle=pre or pre_bundle(),
        qualification_checkpoint_sha256="b" * 64,
        qualification_run_manifest_sha256="c" * 64,
    )


def test_preexecution_contains_only_evidence_available_before_learning():
    out = pre_bundle()
    assert set(out["required_evidence"]) == set(PRE_EXECUTION_EVIDENCE)
    assert "shortcut_superiority" not in out["required_evidence"]
    assert out["qualification_run_eligible"] is True
    assert out["production_training_authorized"] is False


def test_preexecution_rejects_learned_gate_smuggled_into_evidence_set():
    e = pre_evidence()
    e["shortcut_superiority"] = e["representation_firewall"].copy()
    with pytest.raises(RuntimeError, match="EVIDENCE_SET_MISMATCH"):
        build_preexecution_bundle(e, design_context_sha256="a" * 64, optimizer_started=False)


def test_preexecution_tamper_is_detected_by_digest():
    b = copy.deepcopy(pre_bundle())
    b["required_evidence"]["representation_firewall"]["artifact_sha256"] = "f" * 64
    with pytest.raises(RuntimeError, match="DIGEST_MISMATCH"):
        validate_preexecution_bundle(b)


def test_postqualification_binds_every_gate_to_same_checkpoint_and_design():
    out = post_bundle()
    assert out["production_training_eligible"] is True
    assert out["production_training_authorized"] is False
    assert {r["qualification_checkpoint_sha256"] for r in out["required_evidence"].values()} == {"b" * 64}


def test_postqualification_rejects_checkpoint_substitution():
    e = post_evidence()
    e["heldout_biology_validation"]["qualification_checkpoint_sha256"] = "d" * 64
    with pytest.raises(RuntimeError, match="CHECKPOINT_SUBSTITUTION"):
        build_postqualification_bundle(
            e,
            preexecution_bundle=pre_bundle(),
            qualification_checkpoint_sha256="b" * 64,
            qualification_run_manifest_sha256="c" * 64,
        )


def test_postqualification_rejects_design_context_substitution():
    e = post_evidence()
    e["student_representation_collapse"]["design_context_sha256"] = "e" * 64
    with pytest.raises(RuntimeError, match="DESIGN_CONTEXT_SUBSTITUTION"):
        build_postqualification_bundle(
            e,
            preexecution_bundle=pre_bundle(),
            qualification_checkpoint_sha256="b" * 64,
            qualification_run_manifest_sha256="c" * 64,
        )


def test_postqualification_serialized_tamper_is_detected():
    pre = pre_bundle()
    b = copy.deepcopy(post_bundle(pre))
    b["required_evidence"]["shortcut_superiority"]["artifact_sha256"] = "f" * 64
    with pytest.raises(RuntimeError, match="DIGEST_MISMATCH"):
        validate_postqualification_bundle(b, preexecution_bundle=pre)


def test_postqualification_cannot_be_rebound_to_different_preexecution_bundle():
    pre = pre_bundle()
    b = post_bundle(pre)
    other = build_preexecution_bundle(
        pre_evidence(), design_context_sha256="d" * 64, optimizer_started=False
    )
    with pytest.raises(RuntimeError, match="PREEXECUTION_BUNDLE_SUBSTITUTION"):
        validate_postqualification_bundle(b, preexecution_bundle=other)
