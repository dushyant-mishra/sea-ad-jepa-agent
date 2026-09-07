from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from scripts.v4.d1a_synthetic_known_answer_v2 import (
    known_answer_diagnostic,
    make_synthetic_fixture,
)
from sea_ad_jepa.v4.d1a_estimation_atlas import (
    CONTRACT_ROOT,
    build_d1a_atlas,
)


@pytest.fixture(scope="module")
def fixture():
    return make_synthetic_fixture()


@pytest.fixture(scope="module")
def result(fixture):
    return build_d1a_atlas(
        fixture.states,
        fixture.metadata,
        fixture.molecular_values,
        fixture.measured_mask,
        fixture.feature_ids,
        n_components=3,
        mode="synthetic",
        known_molecular_reference_programs=fixture.known_refs,
    )


@pytest.fixture(scope="module")
def diagnostic():
    return known_answer_diagnostic()


def test_contract_root_is_exact_v2_freeze() -> None:
    assert CONTRACT_ROOT == "6af28682da4a5c37a212ad1926fbc6acf5a7fea88c46c49f69295cbaae8a3a81"


def test_injected_biological_and_measurement_directions_are_recovered(diagnostic) -> None:
    assert diagnostic["bio_alignment"] > 0.95
    assert diagnostic["artifact_alignment"] > 0.95


def test_biological_cell_ranking_recovers_injected_continuous_score(diagnostic) -> None:
    assert diagnostic["bio_cell_score_abs_correlation"] > 0.95


def test_injected_molecular_module_dominates_biological_program(diagnostic) -> None:
    assert diagnostic["bio_module_top10_overlap"] >= 8


def test_measurement_artifact_is_flagged_continuously(diagnostic) -> None:
    assert diagnostic["artifact_measurement_support_r2"] > 0.50
    assert diagnostic["artifact_measurement_support_r2"] > diagnostic["bio_measurement_support_r2"]
    assert diagnostic["artifact_source_eta_squared"] > 0.50
    assert diagnostic["artifact_source_eta_squared"] > diagnostic["bio_source_eta_squared"]


def test_biological_program_ranks_above_higher_variance_artifact(diagnostic) -> None:
    assert diagnostic["bio_priority_score"] > diagnostic["artifact_priority_score"]


def test_measurement_only_negative_does_not_recover_absent_biological_direction(diagnostic) -> None:
    assert diagnostic["negative_absent_bio_max_alignment"] < 0.50


def test_all_required_tables_preserve_complete_geometry(result, fixture) -> None:
    assert len(result.program_table) == 3
    assert len(result.state_loading_table) == 3 * 160
    assert len(result.cell_ranking_table) == 3 * len(fixture.states)
    assert len(result.molecular_table) == 3 * len(fixture.feature_ids)
    assert len(result.donor_table) == 3 * fixture.metadata["donor"].nunique()
    assert len(result.source_table) == 3 * fixture.metadata["source"].nunique()
    assert len(result.operator_table) == 3 * fixture.metadata["operator"].nunique()
    assert len(result.hypothesis_catalog) == 3


def test_full_cell_ranking_is_retained_and_tail_is_only_a_derived_view(result, fixture) -> None:
    expected = set(fixture.metadata["canonical_cell_id"].astype(str))
    for _, frame in result.cell_ranking_table.groupby("program_id"):
        assert set(frame["canonical_cell_id"].astype(str)) == expected
        assert len(frame) == len(expected)
        assert set(frame["tail_membership"].astype(str)).issubset(
            {"BOTTOM_5PCT", "NONE", "TOP_5PCT"}
        )


def test_state_direction_exports_every_canonical_coordinate(result) -> None:
    for pid, frame in result.state_loading_table.groupby("program_id"):
        assert frame["state_dimension"].tolist() == list(range(160))
        assert frame["state_direction_sha256"].nunique() == 1
        assert sorted(frame["absolute_loading_rank"].tolist()) == list(range(1, 161))


def test_every_observed_operator_is_retained_for_every_program(result, fixture) -> None:
    expected = set(fixture.metadata["operator"].astype(str))
    for _, frame in result.operator_table.groupby("program_id"):
        assert set(frame["operator"].astype(str)) == expected


def test_every_output_table_carries_one_input_root(result) -> None:
    tables = (
        result.program_table,
        result.state_loading_table,
        result.cell_ranking_table,
        result.molecular_table,
        result.donor_table,
        result.source_table,
        result.operator_table,
        result.hypothesis_catalog,
    )
    roots = set()
    for table in tables:
        assert "input_root_sha256" in table.columns
        assert table["input_root_sha256"].nunique() == 1
        roots.add(str(table["input_root_sha256"].iloc[0]))
    assert roots == {result.diagnostics["input_root_sha256"]}


def test_outputs_are_discovery_only_and_zero_update(result, diagnostic) -> None:
    assert set(result.hypothesis_catalog["claim_status"].astype(str)) == {"DISCOVERY_ONLY"}
    assert result.diagnostics["optimizer_steps"] == 0
    assert result.diagnostics["ema_updates"] == 0
    assert result.diagnostics["real_d1_authorized"] is False
    assert result.diagnostics["confirmatory_terminal"] is None
    assert diagnostic["confirmatory_terminal"] is None


def test_metadata_permutation_cannot_change_fitted_directions_or_cell_scores(fixture, result) -> None:
    permuted = fixture.metadata.copy()
    permuted["source"] = np.roll(permuted["source"].to_numpy(), 7)
    permuted["operator"] = np.roll(permuted["operator"].to_numpy(), 11)
    mutated = build_d1a_atlas(
        fixture.states,
        permuted,
        fixture.molecular_values,
        fixture.measured_mask,
        fixture.feature_ids,
        n_components=3,
        mode="synthetic",
        known_molecular_reference_programs=fixture.known_refs,
    )

    left = result.state_loading_table.sort_values(["program_id", "state_dimension"])
    right = mutated.state_loading_table.sort_values(["program_id", "state_dimension"])
    assert np.allclose(left["loading"].to_numpy(), right["loading"].to_numpy(), atol=0.0, rtol=0.0)

    left_scores = result.cell_ranking_table.sort_values(["program_id", "canonical_cell_id"])
    right_scores = mutated.cell_ranking_table.sort_values(["program_id", "canonical_cell_id"])
    assert np.allclose(
        left_scores["raw_score"].to_numpy(),
        right_scores["raw_score"].to_numpy(),
        atol=0.0,
        rtol=0.0,
    )
    assert result.diagnostics["input_root_sha256"] != mutated.diagnostics["input_root_sha256"]


def test_real_trained_teacher_mode_is_rejected_before_estimation(fixture) -> None:
    with pytest.raises(ValueError, match="real trained-teacher execution is unauthorized"):
        build_d1a_atlas(
            fixture.states,
            fixture.metadata,
            fixture.molecular_values,
            fixture.measured_mask,
            fixture.feature_ids,
            n_components=3,
            mode="trained_teacher",
            known_molecular_reference_programs=fixture.known_refs,
        )


def test_protected_outcome_metadata_is_rejected(fixture) -> None:
    metadata = fixture.metadata.copy()
    metadata["pathology_stage"] = "forbidden"
    with pytest.raises(ValueError, match="protected outcome metadata is forbidden"):
        build_d1a_atlas(
            fixture.states,
            metadata,
            fixture.molecular_values,
            fixture.measured_mask,
            fixture.feature_ids,
            n_components=3,
            mode="synthetic",
            known_molecular_reference_programs=fixture.known_refs,
        )


def test_measured_nonfinite_value_is_rejected_but_unmeasured_nan_is_legal(fixture) -> None:
    molecular = fixture.molecular_values.copy()
    measured = np.argwhere(fixture.measured_mask)[0]
    molecular[tuple(measured)] = np.nan
    with pytest.raises(ValueError, match="physically measured molecular values must be finite"):
        build_d1a_atlas(
            fixture.states,
            fixture.metadata,
            molecular,
            fixture.measured_mask,
            fixture.feature_ids,
            n_components=3,
            mode="synthetic",
            known_molecular_reference_programs=fixture.known_refs,
        )


def test_no_known_reference_reports_unknown_novelty_not_maximal_novelty(fixture) -> None:
    smaller = build_d1a_atlas(
        fixture.states,
        fixture.metadata,
        fixture.molecular_values,
        fixture.measured_mask,
        fixture.feature_ids,
        n_components=1,
        mode="synthetic",
        known_molecular_reference_programs=None,
    )
    row = smaller.program_table.iloc[0]
    assert pd.isna(row["known_reference_id"])
    assert np.isnan(float(row["known_reference_max_abs_cosine"]))
    assert np.isnan(float(row["novelty_score"]))
