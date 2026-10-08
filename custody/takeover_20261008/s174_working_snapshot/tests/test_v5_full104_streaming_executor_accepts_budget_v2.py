"""The FULL104 streaming executor must accept the V2 budget with no change.

V2 renames the declared semantics and adds provenance roots, but keeps the
``mask_count(int) -> int`` and ``validate()`` surface that the executor calls.
Claiming "no interface change is required" is not evidence, so this test runs the
executor under both authorities and requires byte-identical results across every
policy arm.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# The sibling fixture module lives in tests/, which is not guaranteed to be on
# sys.path under the project's standard PYTHONPATH of "src;.".
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sea_ad_jepa.v5.full104_masking_streaming_executor_v1 import (
    run_primary_fold_streaming,
)
from sea_ad_jepa.v5.target_evidence_budget_authority_v2 import (
    TargetEvidenceBudgetAuthorityV2,
)

from test_v5_full104_masking_streaming_executor_v1 import (  # type: ignore[import-not-found]
    _fixture,
    budget as budget_v1,
    parameters,
)

MANIFEST_SHA = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
OBS_SHA = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"


def budget_v2_equivalent() -> TargetEvidenceBudgetAuthorityV2:
    """Same burden and retained-evidence floor as the V1 fixture budget."""
    reference = budget_v1()
    return TargetEvidenceBudgetAuthorityV2(
        authority_id="V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V2",
        support_estimability_authority_sha256=(
            reference.support_estimability_authority_sha256
        ),
        support_semantics_id="STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
        census_authority_sha256="b" * 64,
        full104_block_manifest_sha256=MANIFEST_SHA,
        observation_state_sha256=OBS_SHA,
        terminal_universe_id="FULL_COMMON_CORE_17186_V1",
        budget_semantics_id="MASK_FRACTION_OF_STRICT_MEASURED_NON_TARGET_ADDRESSES_V1",
        eligibility_rule_id=(
            "VALUE_INDEPENDENT_ELIGIBILITY__MEASURED_ZERO_IS_MEASURED_EVIDENCE_V1"
        ),
        rounding_policy_id="FLOOR_EXACT_RATIONAL_V1",
        mask_fraction_numerator=reference.mask_fraction_numerator,
        mask_fraction_denominator=reference.mask_fraction_denominator,
        min_retained_non_target_address_count=(
            reference.min_retained_non_target_rna_count
        ),
        infeasible_policy_id="FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1",
    )


def test_streaming_executor_is_unchanged_under_budget_v2(tmp_path: Path) -> None:
    _, stream, _, _ = _fixture(tmp_path)
    with_v1 = run_primary_fold_streaming(
        stream=stream,
        fold_index=0,
        parameters=parameters(),
        evidence_budget=budget_v1(),
        global_seed=17,
    )
    with_v2 = run_primary_fold_streaming(
        stream=stream,
        fold_index=0,
        parameters=parameters(),
        evidence_budget=budget_v2_equivalent(),
        global_seed=17,
    )
    assert len(with_v2) == len(with_v1)
    assert with_v1, "fixture produced no rows, so this comparison would be vacuous"
    for got, want in zip(with_v2, with_v1):
        assert set(got) == set(want)
        for key in want:
            observed, expected = got[key], want[key]
            if isinstance(expected, float):
                assert observed == pytest.approx(expected, abs=0.0, rel=0.0), key
            else:
                assert observed == expected, key


def test_mask_cardinality_is_identical_across_authority_versions(tmp_path: Path) -> None:
    _, stream, _, _ = _fixture(tmp_path)
    kwargs = dict(stream=stream, fold_index=0, parameters=parameters(), global_seed=17)
    v1_rows = run_primary_fold_streaming(evidence_budget=budget_v1(), **kwargs)
    v2_rows = run_primary_fold_streaming(evidence_budget=budget_v2_equivalent(), **kwargs)
    assert [row["mask_cardinality"] for row in v2_rows] == [
        row["mask_cardinality"] for row in v1_rows
    ]
    assert [row["uniform_mask_cardinality"] for row in v2_rows] == [
        row["uniform_mask_cardinality"] for row in v1_rows
    ]


def test_v2_budget_declares_address_semantics(tmp_path: Path) -> None:
    budget = budget_v2_equivalent()
    budget.validate()
    assert budget.budget_semantics_id == (
        "MASK_FRACTION_OF_STRICT_MEASURED_NON_TARGET_ADDRESSES_V1"
    )
    assert budget_v1().budget_semantics_id == "MASK_FRACTION_OF_ELIGIBLE_NON_TARGET_RNA_V1"
    assert budget.mask_count(17185) == budget_v1().mask_count(17185)
