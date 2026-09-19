from dataclasses import replace
import hashlib

import pytest

from sea_ad_jepa.v5.null_equivalence_margin_authority_v1 import (
    FULL104_SUBSTRATE_SHA256,
    HISTORICAL_ROLE_ID,
    HISTORICAL_SCALE_CONTEXT_SHA256,
    MARGIN_DENOMINATOR,
    MARGIN_NUMERATOR,
    MARGIN_SELECTION_POLICY_ID,
    PRIMARY_SCORE_ID,
    NullEquivalenceMarginAuthorityV1,
)


def authority(**updates):
    values = dict(
        authority_id="TEST_NULL_MARGIN",
        full104_substrate_sha256=FULL104_SUBSTRATE_SHA256,
        historical_scale_context_artifact_sha256=HISTORICAL_SCALE_CONTEXT_SHA256,
    )
    values.update(updates)
    return NullEquivalenceMarginAuthorityV1(**values)


def test_margin_is_exact_prospective_one_per_thousand():
    a = authority()
    a.validate()
    assert (a.margin_numerator, a.margin_denominator) == (
        MARGIN_NUMERATOR,
        MARGIN_DENOMINATOR,
    )
    assert a.margin == pytest.approx(0.001)
    assert a.primary_score_id == PRIMARY_SCORE_ID
    assert a.margin_selection_policy_id == MARGIN_SELECTION_POLICY_ID


def test_historical_material_is_role_limited_and_exact_byte_bound():
    a = authority()
    assert a.historical_role_id == HISTORICAL_ROLE_ID
    assert "NO_FULL104_DATA_TARGET_FOLD_BURDEN_SEED_ROW_CAP_POLICY_PASS_RUNTIME_OR_TRAINING_AUTHORITY" in a.historical_role_id
    with pytest.raises(ValueError, match="frozen exact byte source"):
        replace(
            a,
            historical_scale_context_artifact_sha256=hashlib.sha256(b"drift").hexdigest(),
        ).validate()


def test_margin_cannot_be_retuned_through_constructor():
    with pytest.raises(ValueError, match="exactly 1/1000"):
        authority(margin_numerator=1, margin_denominator=100).validate()
    with pytest.raises(ValueError, match="exactly 1/1000"):
        authority(margin_numerator=2, margin_denominator=1000).validate()


def test_terminal_and_training_flags_fail_closed():
    with pytest.raises(ValueError, match="before terminal outcomes"):
        authority(terminal_outcomes_inspected_before_freeze=True).validate()
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()


def test_digest_binds_historical_context_root():
    a = authority()
    b = NullEquivalenceMarginAuthorityV1(
        authority_id="TEST_NULL_MARGIN_2",
        full104_substrate_sha256=FULL104_SUBSTRATE_SHA256,
        historical_scale_context_artifact_sha256=HISTORICAL_SCALE_CONTEXT_SHA256,
    )
    assert a.canonical_digest() != b.canonical_digest()

def test_authority_rejects_different_full104_substrate():
    with pytest.raises(ValueError, match="different FULL104 substrate"):
        authority(
            full104_substrate_sha256=hashlib.sha256(b"other-substrate").hexdigest()
        ).validate()

