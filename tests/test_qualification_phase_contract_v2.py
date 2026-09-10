import copy
import pytest

from sea_ad_jepa.v5.qualification_phase_contract_v1 import (
    PRE_EXECUTION_EVIDENCE,
    POST_QUALIFICATION_EVIDENCE,
    build_preexecution_bundle,
)
from sea_ad_jepa.v5.qualification_phase_contract_v2 import (
    DEPENDENCY_EVIDENCE_ID,
    POST_QUALIFICATION_EVIDENCE_V2,
    build_postqualification_bundle_v2,
    validate_postqualification_bundle_v2,
)


def pre_bundle():
    evidence = {
        name: {
            "status": "EXECUTED_PASS",
            "artifact_sha256": format(i + 200, "064x"),
            "authority_id": f"{name}-authority-v1",
            "training_authorized": False,
        }
        for i, name in enumerate(PRE_EXECUTION_EVIDENCE)
    }
    return build_preexecution_bundle(evidence, design_context_sha256="a" * 64, optimizer_started=False)


def base_rows():
    return {
        name: {
            "status": "EXECUTED_PASS",
            "artifact_sha256": format(i + 1, "064x"),
            "authority_id": f"{name}-authority-v1",
            "training_authorized": False,
            "design_context_sha256": "a" * 64,
            "qualification_checkpoint_sha256": "b" * 64,
        }
        for i, name in enumerate(POST_QUALIFICATION_EVIDENCE)
    }


def dep_report(base):
    return {
        "schema": "JEPA_V5_POSTQUALIFICATION_DEPENDENCY_CLOSURE_V1",
        "authority_id": "dependency-owner-v1",
        "post_evidence_artifact_sha256": {name: base[name]["artifact_sha256"] for name in POST_QUALIFICATION_EVIDENCE},
        "post_evidence_authority_ids": {name: base[name]["authority_id"] for name in POST_QUALIFICATION_EVIDENCE},
        "design_context_sha256": "a" * 64,
        "qualification_checkpoint_sha256": "b" * 64,
        "qc_parent_child_bound": True,
        "two_sided_power_parent_child_bound": True,
        "passed": True,
        "training_authorized": False,
    }


def all_rows():
    base = base_rows()
    base[DEPENDENCY_EVIDENCE_ID] = {
        "status": "EXECUTED_PASS",
        "artifact_sha256": "f" * 64,
        "authority_id": "dependency-owner-v1",
        "training_authorized": False,
        "design_context_sha256": "a" * 64,
        "qualification_checkpoint_sha256": "b" * 64,
    }
    return base


def build(e=None, d=None):
    evidence = e or all_rows()
    base = {name: evidence[name] for name in POST_QUALIFICATION_EVIDENCE}
    report = d or dep_report(base)
    return build_postqualification_bundle_v2(
        evidence,
        preexecution_bundle=pre_bundle(),
        qualification_checkpoint_sha256="b" * 64,
        qualification_run_manifest_sha256="c" * 64,
        dependency_closure_report=report,
        dependency_closure_artifact_sha256="f" * 64,
    )


def test_v2_requires_dependency_closure_and_two_sided_power_without_authorizing_training():
    out = build()
    assert set(out["required_evidence"]) == set(POST_QUALIFICATION_EVIDENCE_V2)
    assert out["dependency_closure_required"] is True
    assert out["two_sided_power_calibration_required"] is True
    assert out["production_training_eligible"] is True
    assert out["production_training_authorized"] is False


def test_old_eight_row_bundle_cannot_satisfy_v2():
    with pytest.raises(RuntimeError, match="V2_EVIDENCE_SET_MISMATCH"):
        build_postqualification_bundle_v2(
            base_rows(), preexecution_bundle=pre_bundle(),
            qualification_checkpoint_sha256="b" * 64,
            qualification_run_manifest_sha256="c" * 64,
            dependency_closure_report=dep_report(base_rows()),
            dependency_closure_artifact_sha256="f" * 64,
        )


def test_dependency_artifact_substitution_stops():
    e = all_rows(); e[DEPENDENCY_EVIDENCE_ID]["artifact_sha256"] = "e" * 64
    with pytest.raises(RuntimeError, match="CLOSURE_ARTIFACT_SUBSTITUTION"):
        build(e=e)


def test_dependency_authority_substitution_stops():
    e = all_rows(); e[DEPENDENCY_EVIDENCE_ID]["authority_id"] = "other"
    with pytest.raises(RuntimeError, match="CLOSURE_AUTHORITY_SUBSTITUTION"):
        build(e=e)


def test_stale_dependency_graph_stops_after_child_artifact_changes():
    e = all_rows()
    base_before = {name: copy.deepcopy(e[name]) for name in POST_QUALIFICATION_EVIDENCE}
    d = dep_report(base_before)
    e["heldout_biology_validation"]["artifact_sha256"] = "9" * 64
    with pytest.raises(RuntimeError, match="ARTIFACT_GRAPH_MISMATCH"):
        build(e=e, d=d)


def test_dependency_graph_must_prove_two_sided_power():
    e = all_rows(); d = dep_report({name: e[name] for name in POST_QUALIFICATION_EVIDENCE})
    d["two_sided_power_parent_child_bound"] = False
    with pytest.raises(RuntimeError, match="DEPENDENCY_GRAPH_NOT_CLOSED"):
        build(e=e, d=d)


def test_dependency_row_cannot_claim_training_authority():
    e = all_rows(); e[DEPENDENCY_EVIDENCE_ID]["training_authorized"] = True
    with pytest.raises(RuntimeError, match="CLAIMS_TRAINING_AUTHORITY"):
        build(e=e)


def test_bundle_requires_two_sided_power_on_revalidation():
    out = build()
    tampered = copy.deepcopy(out)
    tampered["two_sided_power_calibration_required"] = False
    base = {name: out["required_evidence"][name] for name in POST_QUALIFICATION_EVIDENCE}
    with pytest.raises(RuntimeError, match="TWO_SIDED_POWER_CALIBRATION_NOT_REQUIRED"):
        validate_postqualification_bundle_v2(
            tampered,
            preexecution_bundle=pre_bundle(),
            dependency_closure_report=dep_report(base),
            dependency_closure_artifact_sha256="f" * 64,
        )


def test_bundle_tamper_is_detected_on_revalidation():
    out = build()
    tampered = copy.deepcopy(out)
    tampered["required_evidence"]["shortcut_superiority"]["artifact_sha256"] = "8" * 64
    base = {name: out["required_evidence"][name] for name in POST_QUALIFICATION_EVIDENCE}
    with pytest.raises(RuntimeError):
        validate_postqualification_bundle_v2(
            tampered,
            preexecution_bundle=pre_bundle(),
            dependency_closure_report=dep_report(base),
            dependency_closure_artifact_sha256="f" * 64,
        )
