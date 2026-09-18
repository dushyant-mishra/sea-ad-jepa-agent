from __future__ import annotations

from fractions import Fraction
import hashlib

import numpy as np
import pytest

from sea_ad_jepa.v5.masking_burden_ladder_authority_v2 import (
    MaskingBurdenLadderAuthorityV2,
)
from sea_ad_jepa.v5.masking_qualification_decision_v1 import POLICIES
from sea_ad_jepa.v5.masking_qualification_decision_v2 import (
    MaskingRungDecisionReceiptV2,
)
from sea_ad_jepa.v5.masking_terminal_one_rung_executor_v1 import (
    TerminalOneRungRawResultArtifactV1,
    _fill_donor_values,
    _require_complete,
    _validate_requested_rung,
)


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def ladder() -> MaskingBurdenLadderAuthorityV2:
    return MaskingBurdenLadderAuthorityV2(
        authority_id="TEST_FULL104_BURDEN_LADDER_V2",
        census_authority_sha256=h("census"),
    )


def receipt(numerator: int, denominator: int, *, qualified: bool):
    selected = "RIDGE8_CONDITIONAL" if qualified else "NO_POLICY_QUALIFIED"
    return MaskingRungDecisionReceiptV2(
        burden_numerator=numerator,
        burden_denominator=denominator,
        qualified=qualified,
        selected_policy_id=selected,
        policy_receipt_sha256={
            policy: h(f"{numerator}/{denominator}:{policy}") for policy in POLICIES
        },
    )


def test_first_invocation_can_open_only_first_frozen_rung():
    requested, prior = _validate_requested_rung(
        burden_ladder=ladder(),
        numerator=1,
        denominator=20,
        prior_rung_receipts=(),
    )
    assert requested == Fraction(1, 20)
    assert prior == ()

    with pytest.raises(ValueError, match="only lawful next rung"):
        _validate_requested_rung(
            burden_ladder=ladder(),
            numerator=1,
            denominator=10,
            prior_rung_receipts=(),
        )


def test_second_rung_requires_exact_failed_first_rung_receipt():
    first = receipt(1, 20, qualified=False)
    requested, prior = _validate_requested_rung(
        burden_ladder=ladder(),
        numerator=1,
        denominator=10,
        prior_rung_receipts=(first,),
    )
    assert requested == Fraction(1, 10)
    assert prior == (first.canonical_digest(),)


def test_higher_rung_cannot_open_after_lower_rung_qualified():
    first = receipt(1, 20, qualified=True)
    with pytest.raises(ValueError, match="higher burden cannot open"):
        _validate_requested_rung(
            burden_ladder=ladder(),
            numerator=1,
            denominator=10,
            prior_rung_receipts=(first,),
        )


def test_prior_receipts_must_be_exact_contiguous_prefix():
    wrong_first = receipt(1, 10, qualified=False)
    with pytest.raises(ValueError, match="exact ascending ladder prefix"):
        _validate_requested_rung(
            burden_ladder=ladder(),
            numerator=3,
            denominator=20,
            prior_rung_receipts=(wrong_first,),
        )


def test_fill_donor_values_rejects_duplicate_target_donor_evidence():
    matrix = np.full((2, 3), np.nan)
    seen = np.zeros((2, 3), dtype=bool)
    _fill_donor_values(
        matrix,
        seen,
        target_index=0,
        donor_pairs=((1, 0.25),),
        label="primary",
    )
    with pytest.raises(ValueError, match="duplicate primary evidence"):
        _fill_donor_values(
            matrix,
            seen,
            target_index=0,
            donor_pairs=((1, 0.30),),
            label="primary",
        )


def test_require_complete_rejects_missing_donor_cell():
    matrix = np.zeros((2, 3), dtype=float)
    seen = np.ones((2, 3), dtype=bool)
    seen[1, 2] = False
    with pytest.raises(ValueError, match="missing=1"):
        _require_complete(matrix, seen, "primary")


def test_raw_result_artifact_binds_exactly_all_policy_arms():
    common = dict(
        run_contract_sha256=h("run-contract"),
        burden_numerator=1,
        burden_denominator=20,
        prior_rung_decision_receipt_sha256=(),
        terminal_input_manifest_sha256=h("manifest"),
        split_receipt_sha256=h("split"),
        target_eligibility_receipt_sha256=h("eligibility"),
        target_selection_receipt_sha256=h("selection"),
        mechanical_control_receipt_sha256=h("mechanical"),
    )
    artifact = TerminalOneRungRawResultArtifactV1(
        **common,
        raw_policy_evidence_sha256={
            policy: h(f"raw:{policy}") for policy in POLICIES
        },
    )
    artifact.validate()
    assert len(artifact.canonical_digest()) == 64
    assert artifact.training_authorized is False
    assert artifact.protected_outcomes_authorized is False

    with pytest.raises(ValueError, match="every policy arm exactly once"):
        TerminalOneRungRawResultArtifactV1(
            **common,
            raw_policy_evidence_sha256={
                policy: h(f"raw:{policy}") for policy in POLICIES[:-1]
            },
        ).validate()
