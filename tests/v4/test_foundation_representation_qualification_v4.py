from pathlib import Path
import importlib.util
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
V4 = ROOT / "src" / "sea_ad_jepa" / "v4"


def load(name: str):
    path = V4 / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"qualification_v4_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


QUAL = load("foundation_qualification_v4")
SAMP = load("foundation_sampling")
RES = load("foundation_resource_guard")
OBS = load("observation_process")
STAB = load("foundation_state_stability")
requalify_historical_report = QUAL.requalify_historical_report
hierarchical_sampling_plan = SAMP.hierarchical_sampling_plan
compact_cache_plan, dense_bytes = RES.compact_cache_plan, RES.dense_bytes
assert_no_provenance_inputs = OBS.assert_no_provenance_inputs


def historical_report():
    return {
        "all_hard_gates_pass": True,
        "foundation_datasets": 13,
        "foundation_matrices": 36,
        "classifications": {
            "balanced_pca160": "QUALIFIED",
            "biological_evidence_response": "DISTINCT",
            "biology_measurement_separation": "SUPPORTED",
            "coordinate_uncertainty": "SUBSPACE-ONLY",
            "cross_dataset_transfer": "STRONG",
            "cross_donor_transfer": "WEAK",
            "cross_matrix_transfer": "WEAK",
            "cross_technology_transfer": "STRONG",
            "measurement_depth_response": "SUPPORTED",
            "state_axes": "ROTATING-WITHIN-STABLE-SUBSPACE",
            "state_subspace": "STABLE",
            "two_axis_domain_support": "INFORMATIVE",
        },
        "governance": {
            "pathology_blind": True,
            "neural_optimizer_updates": 0,
            "production_basis_frozen": False,
            "stage81b_started": False,
            "train_expression_only": True,
            "development_expression_forbidden": True,
            "sealed_expression_forbidden": True,
        },
        "performance": {"peak_cpu_rss_bytes": 6387449856, "temporary_disk_bytes": 5030195626},
    }


def test_rotated_basis_is_same_subspace_even_when_axes_change():
    reference = np.eye(6)[:, :2]
    theta = np.pi / 4
    rotation = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    candidate = reference @ rotation
    rec = STAB.principal_angle_metrics(reference, candidate)
    assert np.allclose(rec["canonical_correlations"], 1.0)
    match = STAB.hungarian_axis_match(reference, candidate)
    assert np.min(match["absolute_correlation"]) < 1.0


def test_historical_requalification_preserves_subspace_only_and_blocks_current_freeze():
    rec = requalify_historical_report(historical_report())
    assert rec["basis_uncertainty"] == "SUBSPACE_ONLY"
    assert rec["biology_measurement_uncertainty"] == "SEPARATE_RESPONSES_SUPPORTED_HISTORICALLY"
    assert rec["transfer_ladder"]["donor"] == "WEAK"
    assert rec["transfer_ladder"]["matrix"] == "WEAK"
    assert rec["representation_freeze_authorized"] is False
    assert rec["terminal"] == "HISTORICAL_EVIDENCE_REQUALIFIED__CURRENT_REPRESENTATION_FREEZE_BLOCKED"
    assert rec["training_authorized"] is False
    assert rec["target_discovery_value_read_authorized"] is False


def test_requalification_fails_closed_if_historical_run_not_pathology_blind():
    report = historical_report(); report["governance"]["pathology_blind"] = False
    with pytest.raises(ValueError, match="pathology_blind"):
        requalify_historical_report(report)


def test_requalification_fails_closed_if_optimizer_updates_occurred():
    report = historical_report(); report["governance"]["neural_optimizer_updates"] = 1
    with pytest.raises(ValueError, match="optimizer"):
        requalify_historical_report(report)


def test_observation_operator_rejects_provenance_shortcuts():
    with pytest.raises(ValueError, match="provenance identifiers"):
        assert_no_provenance_inputs({"assay_type": "snRNA", "donor_id": "D1"})
    assert_no_provenance_inputs({"assay_type": "snRNA", "sequencing_depth": 5000})


def test_hierarchical_sampling_is_sublinear_normalized_and_not_cell_uniform():
    plan = hierarchical_sampling_plan(
        {"A": 100, "B": 10_000},
        {"A": {"A1": 50, "A2": 50}, "B": {"B1": 1000, "B2": 9000}},
        dataset_alpha=0.5, donor_alpha=0.5,
    )
    assert np.isclose(sum(plan["dataset_probability"].values()), 1.0)
    assert np.isclose(sum(plan["donor_mass"].values()), 1.0)
    assert np.isclose(sum(plan["donor_cell_mass"][k] * plan["donor_cell_count"][k] for k in plan["donor_cell_mass"]), 1.0)
    assert plan["dataset_probability"]["B"] < 100 * plan["dataset_probability"]["A"]
    assert plan["dataset_probability"]["B"] > plan["dataset_probability"]["A"]
    assert plan["outcome_tuned"] is False


@pytest.mark.parametrize("alpha", [0.0, 1.0, -0.1, 1.1])
def test_hierarchical_sampling_rejects_non_sublinear_alpha(alpha):
    with pytest.raises(ValueError, match="0 < alpha < 1"):
        hierarchical_sampling_plan({"A": 10}, {"A": {"A1": 10}}, dataset_alpha=alpha, donor_alpha=0.5)


def test_resource_guard_forbids_full_registry_dense_but_allows_selected_cache():
    assert dense_bytes(4000, 41238, 4) == 659_808_000
    plan = compact_cache_plan(4000, 41238, 3000, 4, 128 * 1024 * 1024)
    assert plan["full_registry_dense_authorized"] is False
    assert plan["selected_dense_authorized"] is True
    assert plan["selected_dense_bytes"] == 48_000_000
    assert plan["required_fields"] == ["selected_counts", "library_size", "detected_features", "design_indices"]


def test_resource_guard_rejects_selected_cache_over_budget():
    with pytest.raises(MemoryError, match="selected dense cache"):
        compact_cache_plan(4000, 41238, 10000, 8, 128 * 1024 * 1024)
