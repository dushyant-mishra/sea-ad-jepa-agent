import hashlib
import pytest

from sea_ad_jepa.v5.masking_qualification_decision_v2 import (
    DECISION_RULE_ID,
    MaskingRungDecisionReceiptV2,
)
from sea_ad_jepa.v5.masking_qualification_execution_authority_v4 import (
    MaskingQualificationExecutionAuthorityV4,
)


def h(x):
    return hashlib.sha256(x.encode()).hexdigest()


def receipt():
    r = MaskingRungDecisionReceiptV2(
        burden_numerator=1,
        burden_denominator=10,
        qualified=True,
        selected_policy_id="RIDGE8_CONDITIONAL",
        policy_receipt_sha256={
            "UNIFORM_RANDOM": h("u"),
            "TOP8_CORRELATION": h("t"),
            "RIDGE8_CONDITIONAL": h("r"),
            "PREFIX3_SELECTIVE": h("p"),
        },
    )
    r.validate()
    return r


def authority(r, **updates):
    values = dict(
        authority_id="TEST",
        run_contract_authority_sha256=h("contract"),
        raw_result_artifact_sha256=h("raw"),
        rung_decision_receipt_sha256=r.canonical_digest(),
        selected_policy_id=r.selected_policy_id,
        selected_burden_numerator=r.burden_numerator,
        selected_burden_denominator=r.burden_denominator,
        execution_status="EXECUTED_PASS",
    )
    values.update(updates)
    return MaskingQualificationExecutionAuthorityV4(**values)


def test_v4_binds_v2_rung_decision():
    r = receipt()
    authority(r).bind_rung_decision_receipt(r)


def test_old_or_free_decision_rule_cannot_be_substituted():
    r = receipt()
    with pytest.raises(ValueError, match="decision_rule_id"):
        authority(r, decision_rule_id="OLD_RULE_V1").validate()


def test_receipt_rule_mismatch_fails_even_if_other_fields_match():
    r = receipt()
    object.__setattr__(r, "decision_rule_id", "OLD_RULE_V1")
    with pytest.raises(ValueError, match="different decision rule"):
        authority(receipt()).bind_rung_decision_receipt(r)
