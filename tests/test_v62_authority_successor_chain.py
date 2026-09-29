import hashlib
import json
import pytest

from sea_ad_jepa.v5.current_authority_roots_v2 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2
from sea_ad_jepa.v5.biological_specificity_authority_v1 import BiologicalSpecificityAuthorityV1
from sea_ad_jepa.v5.q_safety_authority_v1 import QSafetyAuthorityV1
from sea_ad_jepa.v5.critical_test_execution_authority_v2 import ProviderTestReceiptV1, CriticalTestExecutionAuthorityV2
from sea_ad_jepa.v5.current_authority_closure_v3 import validate_current_v5_authority_closure_v3
from sea_ad_jepa.v5.current_trainer_preexecution_contract_v3 import CurrentTrainerPreexecutionAuthorityV3
from sea_ad_jepa.v5.current_teacher_target_receipt_v3 import seal_current_teacher_target_receipt_v3
from sea_ad_jepa.v5.current_training_authority_v2 import issue_training_authority_v2

def H(x):
    return hashlib.sha256(x.encode()).hexdigest()

def D(p):
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

class Dummy:
    training_authorized=False
    def __init__(self,d): self.d=d
    def validate(self): pass
    def canonical_digest(self): return self.d

def fixture_chain():
    roots={k:H(k) for k in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2}
    runtime=Dummy(H("runtime_live"))
    roots["runtime_source_authority_sha256"]=runtime.canonical_digest()
    core={"schema":"V5_CURRENT_AUTHORITY_CLOSURE_V2","authority_roots":roots,"training_authorized":False}
    closure2={**core,"closure_digest":D(core)}
    target=roots["target_construction_authority_sha256"]
    bio=BiologicalSpecificityAuthorityV1("bio",target,H("ext"),H("nuis"),H("synth"),H("proto"),H("bioval"),"V48_SEMANTIC_TWIN")
    q=QSafetyAuthorityV1("q",target,H("prep"),H("qint"),"q_excluded_total__q_token_dropped","Q_BLIND",True)
    pr=ProviderTestReceiptV1("t1","GITHUB_ACTIONS","run1","job1",H("testsrc"),H("artifact"),"PASS")
    crit=CriticalTestExecutionAuthorityV2("crit",roots["critical_test_authority_sha256"],["t1"],[pr])
    closure3=validate_current_v5_authority_closure_v3(closure_v2=closure2,biological_specificity=bio,q_safety=q,critical_test_v2=crit)
    pre=CurrentTrainerPreexecutionAuthorityV3(closure3["authority_roots"],closure3["closure_digest"],closure3["authority_roots"]["protected_registry_authority_sha256"],closure3["authority_roots"]["critical_test_v2_authority_sha256"],False,False)
    receipt_roots=dict(closure3["authority_roots"]); receipt_roots["preexecution_authority_sha256"]=pre.canonical_digest()
    receipt=seal_current_teacher_target_receipt_v3(target_package_root=H("targetpkg"),authority_roots=receipt_roots,closure_v3_sha256=closure3["closure_digest"])
    return roots,bio,q,crit,closure3,pre,receipt,runtime

def test_q_safety_rejects_naive_mode():
    roots,bio,q,crit,c,p,r,rt=fixture_chain()
    bad=QSafetyAuthorityV1("q",roots["target_construction_authority_sha256"],H("prep"),H("qint"),"full_total__q_token_dropped","Q_BLIND",True)
    with pytest.raises(ValueError): bad.validate()

def test_critical_test_rejects_caller_declared_provider_and_nonpass():
    with pytest.raises(ValueError): ProviderTestReceiptV1("t","CALLER_DECLARED","r","j",H("s"),H("a"),"PASS").payload()
    with pytest.raises(ValueError): ProviderTestReceiptV1("t","GITHUB_ACTIONS","r","j",H("s"),H("a"),"FAIL").payload()

def test_final_issuance_accepts_bound_live_chain():
    roots,bio,q,crit,c,p,r,rt=fixture_chain()
    a=issue_training_authority_v2(closure_v3=c,preexecution=p,receipt_v3=r,expected_target_package_root=H("targetpkg"),biological_specificity=bio,q_safety=q,critical_test_v2=crit,runtime_source=rt)
    assert a.training_authorized is True

def test_forged_digest_shaped_v3_roots_cannot_issue():
    roots,bio,q,crit,c,p,r,rt=fixture_chain()
    fake=dict(c["authority_roots"]); fake["biological_specificity_authority_sha256"]=H("forged")
    core={"schema":"V5_CURRENT_AUTHORITY_CLOSURE_V3","predecessor_closure_v2_sha256":c["predecessor_closure_v2_sha256"],"authority_roots":fake,"training_authorized":False}
    forged={**core,"closure_digest":D(core)}
    pre2=CurrentTrainerPreexecutionAuthorityV3(fake,forged["closure_digest"],fake["protected_registry_authority_sha256"],fake["critical_test_v2_authority_sha256"],False,False)
    rr=dict(fake); rr["preexecution_authority_sha256"]=pre2.canonical_digest()
    receipt=seal_current_teacher_target_receipt_v3(target_package_root=H("targetpkg"),authority_roots=rr,closure_v3_sha256=forged["closure_digest"])
    with pytest.raises(ValueError,match="biological-specificity authority root mismatch"):
        issue_training_authority_v2(closure_v3=forged,preexecution=pre2,receipt_v3=receipt,expected_target_package_root=H("targetpkg"),biological_specificity=bio,q_safety=q,critical_test_v2=crit,runtime_source=rt)
