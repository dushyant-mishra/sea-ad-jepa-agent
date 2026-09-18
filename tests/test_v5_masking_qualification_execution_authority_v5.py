import hashlib
import pytest
from sea_ad_jepa.v5.masking_qualification_execution_authority_v5 import MaskingQualificationExecutionAuthorityV5
from sea_ad_jepa.v5.masking_qualification_decision_v3 import MaskingRungDecisionReceiptV3


def h(x): return hashlib.sha256(x.encode()).hexdigest()


def receipt():
    r=MaskingRungDecisionReceiptV3(
        burden_numerator=1, burden_denominator=10, qualified=True,
        selected_policy_id="RIDGE8_CONDITIONAL",
        policy_receipt_sha256={
            "UNIFORM_RANDOM":h("u"),"TOP8_CORRELATION":h("t"),
            "RIDGE8_CONDITIONAL":h("r"),"PREFIX3_SELECTIVE":h("p")
        },
    )
    r.validate()
    return r


def test_v5_binds_v3_decision_receipt():
    r=receipt()
    a=MaskingQualificationExecutionAuthorityV5(
        authority_id="TEST",
        run_contract_authority_sha256=h("contract"),
        raw_result_artifact_sha256=h("raw"),
        rung_decision_receipt_sha256=r.canonical_digest(),
        selected_policy_id=r.selected_policy_id,
        selected_burden_numerator=r.burden_numerator,
        selected_burden_denominator=r.burden_denominator,
        execution_status="EXECUTED_PASS",
    )
    a.bind_rung_decision_receipt(r)


def test_old_decision_rule_receipt_is_rejected_before_validation():
    r=receipt()
    object.__setattr__(r,"decision_rule_id","OLD_RULE")
    a=MaskingQualificationExecutionAuthorityV5(
        authority_id="TEST",
        run_contract_authority_sha256=h("contract"),
        raw_result_artifact_sha256=h("raw"),
        rung_decision_receipt_sha256=h("receipt"),
        selected_policy_id="RIDGE8_CONDITIONAL",
        selected_burden_numerator=1, selected_burden_denominator=10,
        execution_status="EXECUTED_PASS",
    )
    with pytest.raises(ValueError, match="different decision rule"):
        a.bind_rung_decision_receipt(r)
