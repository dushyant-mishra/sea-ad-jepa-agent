import pytest

from sea_ad_jepa.v5.biological_specificity_authority_v1 import BiologicalSpecificityAuthorityV1
from sea_ad_jepa.v5.critical_test_execution_authority_v2 import CriticalTestExecutionAuthorityV2, ProviderTestReceiptV1
from sea_ad_jepa.v5.q_safety_authority_v1 import QSafetyAuthorityV1

H="a"*64

def test_q_safety_accepts_only_safe_student_and_q_blind_teacher():
    QSafetyAuthorityV1("q",H,H,H,"q_excluded_total__q_token_dropped","Q_BLIND",True).validate()
    QSafetyAuthorityV1("q",H,H,H,"fixed_reference__q_token_dropped","Q_BLIND",True).validate()
    with pytest.raises(ValueError):
        QSafetyAuthorityV1("q",H,H,H,"naive_total__q_token_dropped","Q_BLIND",True).validate()
    with pytest.raises(ValueError):
        QSafetyAuthorityV1("q",H,H,H,"q_excluded_total__q_token_dropped","Q_VISIBLE",True).validate()
    with pytest.raises(ValueError):
        QSafetyAuthorityV1("q",H,H,H,"q_excluded_total__q_token_dropped","Q_BLIND",False).validate()

def test_biological_specificity_requires_biological_validation_class_and_pass():
    BiologicalSpecificityAuthorityV1("bio",H,H,H,H,H,H,"SAME_RNA_SEMANTIC_TWIN_BOUNDARY").validate()
    with pytest.raises(ValueError):
        BiologicalSpecificityAuthorityV1("bio",H,H,H,H,H,H,"boundary",evidence_class="SYNTHETIC_ONLY").validate()
    with pytest.raises(ValueError):
        BiologicalSpecificityAuthorityV1("bio",H,H,H,H,H,H,"boundary",passed=False).validate()

def test_critical_v2_requires_one_provider_receipt_per_required_test():
    r=ProviderTestReceiptV1("t","GITHUB_ACTIONS","run","job",H,H,"PASS")
    CriticalTestExecutionAuthorityV2("crit",H,["t"],[r]).validate()
    with pytest.raises(ValueError):
        CriticalTestExecutionAuthorityV2("crit",H,["t"],[]).validate()
    with pytest.raises(ValueError):
        CriticalTestExecutionAuthorityV2("crit",H,["t"],[ProviderTestReceiptV1("t","CALLER_DECLARED","run","job",H,H,"PASS")]).validate()
