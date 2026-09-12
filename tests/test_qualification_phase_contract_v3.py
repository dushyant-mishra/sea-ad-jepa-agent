import copy
import pytest

from sea_ad_jepa.v5.qualification_phase_contract_v1 import (
    PRE_EXECUTION_EVIDENCE,
    POST_QUALIFICATION_EVIDENCE,
    build_preexecution_bundle,
)
from sea_ad_jepa.v5.qualification_phase_contract_v3 import (
    DEPENDENCY_EVIDENCE_ID,
    POST_QUALIFICATION_EVIDENCE_V3,
    build_postqualification_bundle_v3,
    validate_postqualification_bundle_v3,
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
        "schema": "JEPA_V5_POSTQUALIFICATION_DEPENDENCY_CLOSURE_V2",
        "authority_id": "dependency-owner-v2",
        "post_evidence_artifact_sha256": {name: base[name]["artifact_sha256"] for name in POST_QUALIFICATION_EVIDENCE},
        "post_evidence_authority_ids": {name: base[name]["authority_id"] for name in POST_QUALIFICATION_EVIDENCE},
        "design_context_sha256": "a" * 64,
        "qualification_checkpoint_sha256": "b" * 64,
        "qc_parent_child_bound": True,
        "executable_power_parent_child_bound": True,
        "power_execution_mode": "ACTUAL_FROZEN_GATE_EXECUTION",
        "independent_power_recomputation": True,
        "passed": True,
        "training_authorized": False,
    }


def all_rows():
    base = base_rows()
    base[DEPENDENCY_EVIDENCE_ID] = {
        "status": "EXECUTED_PASS",
        "artifact_sha256": "f" * 64,
        "authority_id": "dependency-owner-v2",
        "training_authorized": False,
        "design_context_sha256": "a" * 64,
        "qualification_checkpoint_sha256": "b" * 64,
    }
    return base


def build(e=None, d=None):
    evidence = e or all_rows()
    base = {name: evidence[name] for name in POST_QUALIFICATION_EVIDENCE}
    report = d or dep_report(base)
    return build_postqualification_bundle_v3(
        evidence,
        preexecution_bundle=pre_bundle(),
        qualification_checkpoint_sha256="b" * 64,
        qualification_run_manifest_sha256="c" * 64,
        dependency_closure_report=report,
        dependency_closure_artifact_sha256="f" * 64,
    )


def test_v3_requires_executable_power_before_eligibility():
    out = build()
    assert set(out["required_evidence"]) == set(POST_QUALIFICATION_EVIDENCE_V3)
    assert out["executable_power_calibration_required"] is True
    assert out["legacy_v3_power_report_disallowed"] is True
    assert out["production_training_eligible"] is True
    assert out["production_training_authorized"] is False


def test_legacy_dependency_closure_v1_is_rejected():
    e = all_rows()
    report = dep_report({name: e[name] for name in POST_QUALIFICATION_EVIDENCE})
    report["schema"] = "JEPA_V5_POSTQUALIFICATION_DEPENDENCY_CLOSURE_V1"
    with pytest.raises(ValueError, match="V2"):
        build(e=e, d=report)


def test_dependency_must_prove_executable_power():
    e = all_rows()
    report = dep_report({name: e[name] for name in POST_QUALIFICATION_EVIDENCE})
    report["executable_power_parent_child_bound"] = False
    with pytest.raises(RuntimeError, match="EXECUTABLE_POWER_NOT_BOUND"):
        build(e=e, d=report)


def test_dependency_must_prove_independent_recomputation():
    e = all_rows()
    report = dep_report({name: e[name] for name in POST_QUALIFICATION_EVIDENCE})
    report["independent_power_recomputation"] = False
    with pytest.raises(RuntimeError, match="POWER_RECOMPUTATION_NOT_INDEPENDENT"):
        build(e=e, d=report)


def test_bundle_tamper_is_detected_on_revalidation():
    out = build()
    tampered = copy.deepcopy(out)
    tampered["legacy_v3_power_report_disallowed"] = False
    base = {name: out["required_evidence"][name] for name in POST_QUALIFICATION_EVIDENCE}
    with pytest.raises(RuntimeError, match="LEGACY_V3_POWER_REPORT_NOT_DISALLOWED"):
        validate_postqualification_bundle_v3(
            tampered,
            preexecution_bundle=pre_bundle(),
            dependency_closure_report=dep_report(base),
            dependency_closure_artifact_sha256="f" * 64,
        )
