import hashlib

import pytest

from sea_ad_jepa.v5.masking_qualification_execution_authority_v3 import (
    MaskingQualificationExecutionAuthorityV3,
)
from sea_ad_jepa.v5.masking_qualification_decision_v1 import MaskingRungDecisionReceiptV1


def h(name):
    return hashlib.sha256(name.encode()).hexdigest()


def rung(selected="RIDGE8_CONDITIONAL", qualified=True):
    r = MaskingRungDecisionReceiptV1(
        burden_numerator=1,
        burden_denominator=10,
        qualified=qualified,
        selected_policy_id=selected,
        policy_receipt_sha256={
            "UNIFORM_RANDOM": h("u"),
            "TOP8_CORRELATION": h("t"),
            "RIDGE8_CONDITIONAL": h("r"),
            "PREFIX3_SELECTIVE": h("p"),
        },
    )
    r.validate()
    return r


def authority(receipt, **updates):
    values = dict(
        authority_id="TEST",
        run_contract_authority_sha256=h("contract"),
        raw_result_artifact_sha256=h("raw"),
        rung_decision_receipt_sha256=receipt.canonical_digest(),
        selected_policy_id=receipt.selected_policy_id,
        selected_burden_numerator=receipt.burden_numerator,
        selected_burden_denominator=receipt.burden_denominator,
        execution_status="EXECUTED_PASS" if receipt.qualified else "EXECUTED_FAIL",
    )
    values.update(updates)
    return MaskingQualificationExecutionAuthorityV3(**values)


def test_execution_pass_requires_mechanical_rung_receipt():
    receipt = rung()
    a = authority(receipt)
    a.bind_rung_decision_receipt(receipt)


def test_free_policy_name_cannot_override_rung_decision():
    receipt = rung()
    a = authority(receipt, selected_policy_id="TOP8_CORRELATION")
    with pytest.raises(ValueError, match="selected policy"):
        a.bind_rung_decision_receipt(receipt)


def test_execution_status_cannot_disagree_with_rung_decision():
    receipt = rung()
    a = authority(receipt, execution_status="EXECUTED_FAIL", selected_policy_id="NO_POLICY_QUALIFIED")
    with pytest.raises(ValueError, match="selected policy"):
        a.bind_rung_decision_receipt(receipt)


def test_fail_receipt_is_explicit_no_policy():
    receipt = rung(selected="NO_POLICY_QUALIFIED", qualified=False)
    a = authority(receipt)
    a.bind_rung_decision_receipt(receipt)
