from __future__ import annotations

import hashlib
import json

import pytest

from sea_ad_jepa.v5.biological_specificity_authority_v1 import BiologicalSpecificityAuthorityV1
from sea_ad_jepa.v5.critical_test_execution_authority_v2 import (
    CriticalTestExecutionAuthorityV2,
    ProviderTestReceiptV1,
)
from sea_ad_jepa.v5.current_authority_closure_v3 import validate_current_v5_authority_closure_v3
from sea_ad_jepa.v5.current_authority_roots_v2 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2
from sea_ad_jepa.v5.current_teacher_target_receipt_v3 import seal_current_teacher_target_receipt_v3
from sea_ad_jepa.v5.current_trainer_preexecution_contract_v3 import CurrentTrainerPreexecutionAuthorityV3
from sea_ad_jepa.v5.current_training_authority_v2 import issue_training_authority_v2
from sea_ad_jepa.v5.q_safety_authority_v1 import QSafetyAuthorityV1
from sea_ad_jepa.v5.qualified_optimizer_guard_v4 import install_current_optimizer_guard_v4


def h(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def digest(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    ).hexdigest()


def closure_v2_fixture() -> dict:
    roots = {name: h(name) for name in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2}
    core = {
        "schema": "V5_CURRENT_AUTHORITY_CLOSURE_V2",
        "authority_roots": roots,
        "training_authorized": False,
    }
    return {**core, "closure_digest": digest(core)}


class RuntimeSourceFixture:
    training_authorized = False

    def __init__(self, root: str):
        self.root = root

    def validate(self) -> None:
        pass

    def canonical_digest(self) -> str:
        return self.root


def successor_chain():
    c2 = closure_v2_fixture()
    roots2 = c2["authority_roots"]
    target = roots2["target_construction_authority_sha256"]

    bio = BiologicalSpecificityAuthorityV1(
        authority_id="bio-v1",
        target_construction_authority_sha256=target,
        external_regulatory_object_authority_sha256=h("external-object"),
        nuisance_class_contract_sha256=h("nuisance"),
        synthetic_specificity_execution_sha256=h("synthetic"),
        prospective_real_validation_protocol_sha256=h("prospective"),
        biological_validation_execution_sha256=h("biological-validation"),
        semantic_twin_boundary_id="V48_SAME_RNA_SEMANTIC_TWIN",
    )
    q = QSafetyAuthorityV1(
        authority_id="q-v1",
        target_construction_authority_sha256=target,
        preprocessing_implementation_sha256=h("preprocessor"),
        q_intervention_execution_sha256=h("q-intervention"),
        student_preprocessing_mode="q_excluded_total__q_token_dropped",
        teacher_target_mode="Q_BLIND",
        q_token_dropped=True,
    )
    provider = ProviderTestReceiptV1(
        test_id="critical-a",
        provider_id="GITHUB_ACTIONS",
        provider_run_id="123",
        provider_job_id="456",
        test_source_sha256=h("critical-source"),
        provider_artifact_sha256=h("critical-artifact"),
        outcome="PASS",
    )
    critical = CriticalTestExecutionAuthorityV2(
        authority_id="critical-v2",
        predecessor_v1_sha256=roots2["critical_test_authority_sha256"],
        required_test_ids=["critical-a"],
        receipts=[provider],
    )
    c3 = validate_current_v5_authority_closure_v3(
        closure_v2=c2,
        biological_specificity=bio,
        q_safety=q,
        critical_test_v2=critical,
    )
    roots3 = c3["authority_roots"]
    pre = CurrentTrainerPreexecutionAuthorityV3(
        authority_roots=roots3,
        closure_v3_sha256=c3["closure_digest"],
        protected_registry_authority_sha256=roots3["protected_registry_authority_sha256"],
        critical_test_v2_authority_sha256=roots3["critical_test_v2_authority_sha256"],
        relational_training_active=False,
        optimizer_started=False,
    )
    pre_digest = pre.canonical_digest()
    receipt_roots = dict(roots3)
    receipt_roots["preexecution_authority_sha256"] = pre_digest
    target_package = h("target-package")
    receipt = seal_current_teacher_target_receipt_v3(
        target_package_root=target_package,
        authority_roots=receipt_roots,
        closure_v3_sha256=c3["closure_digest"],
    )
    runtime = RuntimeSourceFixture(roots3["runtime_source_authority_sha256"])
    authority = issue_training_authority_v2(
        closure_v3=c3,
        preexecution=pre,
        receipt_v3=receipt,
        expected_target_package_root=target_package,
        runtime_source=runtime,
    )
    return c2, c3, pre, receipt, authority


def test_full_v3_successor_chain_can_issue_only_final_v2_fixture():
    _, c3, _, receipt, authority = successor_chain()
    authority.validate()
    assert authority.training_authorized is True
    assert authority.biological_specificity_authority_sha256 == c3["authority_roots"]["biological_specificity_authority_sha256"]
    assert authority.q_safety_authority_sha256 == c3["authority_roots"]["q_safety_authority_sha256"]
    assert authority.critical_test_v2_authority_sha256 == c3["authority_roots"]["critical_test_v2_authority_sha256"]
    assert receipt["training_authorized"] is False


def test_v3_closure_rejects_q_safety_for_wrong_target():
    c2 = closure_v2_fixture()
    roots = c2["authority_roots"]
    bio = BiologicalSpecificityAuthorityV1(
        "bio", roots["target_construction_authority_sha256"], h("obj"), h("n"), h("s"), h("p"), h("b"), "boundary"
    )
    q = QSafetyAuthorityV1(
        "q", h("different-target"), h("prep"), h("exec"), "q_excluded_total__q_token_dropped", "Q_BLIND", True
    )
    r = ProviderTestReceiptV1("t", "GITHUB_ACTIONS", "r", "j", h("src"), h("art"), "PASS")
    crit = CriticalTestExecutionAuthorityV2("crit", roots["critical_test_authority_sha256"], ["t"], [r])
    with pytest.raises(ValueError, match="q-safety target root mismatch"):
        validate_current_v5_authority_closure_v3(
            closure_v2=c2, biological_specificity=bio, q_safety=q, critical_test_v2=crit
        )


def test_v3_closure_cannot_be_built_from_synthetic_only_specificity():
    c2 = closure_v2_fixture()
    roots = c2["authority_roots"]
    bio = BiologicalSpecificityAuthorityV1(
        "bio", roots["target_construction_authority_sha256"], h("obj"), h("n"), h("s"), h("p"), h("b"), "boundary",
        evidence_class="SYNTHETIC_ONLY",
    )
    q = QSafetyAuthorityV1(
        "q", roots["target_construction_authority_sha256"], h("prep"), h("exec"),
        "q_excluded_total__q_token_dropped", "Q_BLIND", True,
    )
    r = ProviderTestReceiptV1("t", "GITHUB_ACTIONS", "r", "j", h("src"), h("art"), "PASS")
    crit = CriticalTestExecutionAuthorityV2("crit", roots["critical_test_authority_sha256"], ["t"], [r])
    with pytest.raises(ValueError, match="BIOLOGICAL_VALIDATION"):
        validate_current_v5_authority_closure_v3(
            closure_v2=c2, biological_specificity=bio, q_safety=q, critical_test_v2=crit
        )


def test_training_v2_rejects_historical_v2_closure():
    c2, _, pre, receipt, _ = successor_chain()
    runtime = RuntimeSourceFixture(c2["authority_roots"]["runtime_source_authority_sha256"])
    with pytest.raises(ValueError, match="closure_v3"):
        issue_training_authority_v2(
            closure_v3=c2,
            preexecution=pre,
            receipt_v3=receipt,
            expected_target_package_root=h("target-package"),
            runtime_source=runtime,
        )


def test_optimizer_v4_rejects_non_v2_training_authority_before_install():
    with pytest.raises(ValueError, match="CurrentTrainingAuthorityV2"):
        install_current_optimizer_guard_v4(
            object(),
            {},
            training_authority=object(),
            expected_target_package_root=h("target-package"),
            expected_authority_roots={},
            expected_closure_v3_sha256=h("closure"),
        )
