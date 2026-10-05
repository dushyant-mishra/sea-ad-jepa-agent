from __future__ import annotations
import hashlib
import pytest

from sea_ad_jepa.v5.current_authority_roots_v4 import (
    CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V4,
)
from sea_ad_jepa.v5.current_authority_closure_v4 import CurrentAuthorityClosureV4
from sea_ad_jepa.v5.current_trainer_preexecution_contract_v4 import (
    CurrentTrainerPreexecutionAuthorityV4,
)
from sea_ad_jepa.v5.current_teacher_target_receipt_v4 import (
    seal_current_teacher_target_receipt_v4,
)
from sea_ad_jepa.v5.current_training_authority_v2 import issue_training_authority_v2
from sea_ad_jepa.v5.qualified_optimizer_guard_v4 import install_current_optimizer_guard_v4
from sea_ad_jepa.v5.current_training_authority_v1 import CurrentTrainingAuthorityV1
from sea_ad_jepa.v5.validated_e2_authority_v1 import (
    ValidatedE2AuthorityV1, PROMOTION_STATUS, CLAIM_SCOPE,
)
from sea_ad_jepa.v5.rna_e2_target_integration_authority_v1 import (
    RnaE2TargetIntegrationAuthorityV1,
)

def h(x:str)->str:
    return hashlib.sha256(x.encode()).hexdigest()

class Stub:
    training_authorized=False
    def __init__(self,d): self.d=d
    def validate(self): return None
    def canonical_digest(self): return self.d

class Handle:
    def remove(self): pass

class Opt:
    def __init__(self): self.pre=None; self.post=None
    def register_step_pre_hook(self,f): self.pre=f; return Handle()
    def register_step_post_hook(self,f): self.post=f; return Handle()
    def step(self,**kw):
        args=()
        if self.pre:
            out=self.pre(self,args,dict(kw))
            if out is not None: args,kw=out
        if self.post: self.post(self,args,kw)

def roots():
    return {k:h(k) for k in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V4}

def build_chain():
    r=roots()
    closure=CurrentAuthorityClosureV4(r)
    pre=CurrentTrainerPreexecutionAuthorityV4(
        authority_roots=r,
        closure_v4_sha256=closure.canonical_digest(),
        protected_registry_authority_sha256=r["protected_registry_authority_sha256"],
        critical_test_authority_sha256=r["critical_test_authority_sha256"],
        critical_test_execution_authority_sha256=r["critical_test_execution_authority_sha256"],
        relational_training_active=False,optimizer_started=False)
    rr=dict(r); rr["preexecution_authority_sha256"]=pre.canonical_digest()
    target=h("target-package")
    receipt=seal_current_teacher_target_receipt_v4(
        target_package_root=target,authority_roots=rr,
        closure_v4_sha256=closure.canonical_digest())
    live={k:Stub(r[k]) for k in (
        "biological_specificity_authority_sha256","q_safety_authority_sha256",
        "validated_e2_authority_sha256","rna_e2_target_integration_authority_sha256",
        "critical_test_execution_authority_sha256","runtime_source_authority_sha256")}
    auth=issue_training_authority_v2(
        closure_v4=closure,preexecution=pre,receipt_v4=receipt,
        expected_target_package_root=target,
        biological_specificity=live["biological_specificity_authority_sha256"],
        q_safety=live["q_safety_authority_sha256"],
        validated_e2=live["validated_e2_authority_sha256"],
        rna_e2_target_integration=live["rna_e2_target_integration_authority_sha256"],
        critical_test_execution=live["critical_test_execution_authority_sha256"],
        runtime_source=live["runtime_source_authority_sha256"])
    return r,closure,pre,rr,target,receipt,auth

def test_v4_roots_make_new_scientific_roots_mandatory():
    assert "biological_specificity_authority_sha256" in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V4
    assert "q_safety_authority_sha256" in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V4
    assert "critical_test_execution_authority_sha256" in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V4
    assert "validated_e2_authority_sha256" in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V4
    assert "rna_e2_target_integration_authority_sha256" in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V4

def test_v4_closure_rejects_missing_or_extra_roots():
    r=roots()
    CurrentAuthorityClosureV4(r).validate()
    bad=dict(r); bad.pop("validated_e2_authority_sha256")
    with pytest.raises(ValueError):
        CurrentAuthorityClosureV4(bad).validate()
    bad=dict(r); bad["legacy_extra"]=h("x")
    with pytest.raises(ValueError):
        CurrentAuthorityClosureV4(bad).validate()

def test_training_authority_v2_requires_live_new_roots():
    r,closure,pre,rr,target,receipt,auth=build_chain()
    auth.validate()
    assert auth.training_authorized is True
    bad=Stub(h("wrong-q"))
    with pytest.raises(ValueError,match="q_safety"):
        issue_training_authority_v2(
            closure_v4=closure,preexecution=pre,receipt_v4=receipt,
            expected_target_package_root=target,
            biological_specificity=Stub(r["biological_specificity_authority_sha256"]),
            q_safety=bad,
            validated_e2=Stub(r["validated_e2_authority_sha256"]),
            rna_e2_target_integration=Stub(r["rna_e2_target_integration_authority_sha256"]),
            critical_test_execution=Stub(r["critical_test_execution_authority_sha256"]),
            runtime_source=Stub(r["runtime_source_authority_sha256"]))

def test_optimizer_v4_single_use_and_sequential():
    r,closure,pre,rr,target,receipt,auth=build_chain()
    o=Opt()
    g=install_current_optimizer_guard_v4(
        o,receipt,training_authority=auth,expected_target_package_root=target,
        expected_authority_roots=rr,expected_closure_v4_sha256=closure.canonical_digest())
    g.arm_for_step(schedule_cursor=0)
    o.step(v5_current_guard_schedule_cursor=0)
    assert g.assert_step_completed(schedule_cursor=0)["guarded_optimizer_step"]
    with pytest.raises(RuntimeError):
        g.arm_for_step(schedule_cursor=2)
    g.arm_for_step(schedule_cursor=1)
    o.step(v5_current_guard_schedule_cursor=1)
    assert g.assert_step_completed(schedule_cursor=1)["schedule_cursor"]==1

def test_optimizer_v4_rejects_historical_training_authority_type():
    r,closure,pre,rr,target,receipt,auth=build_chain()
    with pytest.raises(ValueError,match="rejects historical"):
        install_current_optimizer_guard_v4(
            Opt(),receipt,training_authority=object(),
            expected_target_package_root=target,expected_authority_roots=rr,
            expected_closure_v4_sha256=closure.canonical_digest())

def test_validated_e2_authority_carries_scope_limitations():
    a=ValidatedE2AuthorityV1(
        "e2",*[h(str(i)) for i in range(1,9)],
        PROMOTION_STATUS,CLAIM_SCOPE,True,True,True)
    a.validate()
    with pytest.raises(ValueError):
        ValidatedE2AuthorityV1(
            "e2",*[h(str(i)) for i in range(1,9)],
            PROMOTION_STATUS,CLAIM_SCOPE,False,True,True).validate()

def test_rna_e2_integration_forbids_protected_outcomes():
    a=RnaE2TargetIntegrationAuthorityV1(
        authority_id="int",rna_backbone_authority_sha256=h("rna"),
        validated_e2_authority_sha256=h("e2"),
        target_construction_authority_sha256=h("tc"),
        teacher_target_semantics_authority_sha256=h("ts"),
        feature_support_authority_sha256=h("fs"),
        implementation_source_sha256=h("impl"),
        global_state_policy_id="SOURCE_BALANCED_COMMON_RNA_STATE_BACKBONE_V1",
        regulatory_state_policy_id="VALIDATED_E2_QUERY_LOCAL_REGULATORY_STATE_V1",
        multiedge_policy_id="PRESERVE_EDGES__NO_GENE_COLLAPSE__SUPPORT_WEIGHT_REPORTED_V1",
        uncertainty_policy_id="CARRY_MEASUREMENT_SUPPORT_AND_VALIDATION_SCOPE_V1",
        double_counting_policy_id="NO_SAME_STUDY_EVIDENCE_DOUBLE_COUNT_AS_INDEPENDENT_V1",
        integrated_target_semantics_id="QUERY_LOCAL_PLUS_GLOBAL_BIOLOGICAL_STATE_V1")
    a.validate()
    with pytest.raises(ValueError):
        RnaE2TargetIntegrationAuthorityV1(**{**a.__dict__,"protected_outcomes_used_for_integration":True}).validate()
