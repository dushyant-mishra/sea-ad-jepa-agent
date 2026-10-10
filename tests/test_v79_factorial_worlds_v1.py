import dataclasses
import numpy as np
import pytest

from scripts.v79.v79_hierarchical_biology import generate_latent_biology
from scripts.v79.v79_observation_operator import observe_latent_biology
from scripts.v79.build_v79_factorial_worlds import (
    ArmManifest,
    validate_arm_manifest,
    canonical_manifest_json,
    manifest_hash,
    build_factorial_worlds,
)


def bio_authority():
    return {
        "class_frequencies": [0.5, 0.3, 0.2],
        "substates_per_class": [2, 2, 2],
        "substate_prevalence": [1.0, 1.0, 1.0],
        "module_size_distribution": [4, 7],
        "n_modules_per_substate": 2,
        "n_continuous_factors": 2,
        "substate_effect_scale": 0.9,
        "continuous_factor_scale": 0.05,
        "donor_effect_scale": 0.05,
        "baseline_log_mean": -0.2,
        "baseline_log_sd": 0.2,
    }


def obs_authority(n_genes=36):
    support = np.ones((2, n_genes), dtype=bool)
    support[1, ::5] = False
    return {
        "regime_ids": ["OBS_A", "OBS_B"],
        "structural_support": support.tolist(),
        "capture_log_mean": [-0.2, -0.7],
        "capture_log_sd": [0.1, 0.1],
        "gene_propensity": np.linspace(0.7, 1.3, n_genes).tolist(),
        "realization_family": "independent_thinning",
        "molecule_scale": 5.0,
    }


def manifest_dict():
    return {
        "arm_names": ["H0", "H1", "H2", "H3", "C_OBS", "C_BIO"],
        "biology_seed": 101,
        "observation_seed": 202,
        "counterfactual_biology_seed": 303,
        "crossing_seed": 404,
        "cell_count": 240,
        "donor_count": 12,
        "balancing_rule": "BALANCED_WITHIN_BROAD_CLASS",
        "h2_realization_family": "independent_thinning",
        "h3_realization_family": "independent_thinning",
        "endpoint_version": "V79_FACTORIAL_ENDPOINTS_V1",
        "training_authorized": False,
    }


def baseline_latent(n_cells=240, n_genes=36, n_donors=12):
    # Fixture stands in for the frozen E2 latent world; world builder must not alter it.
    return generate_latent_biology(bio_authority(), n_cells, n_genes, n_donors, seed=7)


def baseline_observer(latent, labels, seed):
    return observe_latent_biology(latent, obs_authority(latent.latent_abundance.shape[1]), labels, seed)


def test_manifest_pins_exact_required_arms_and_is_immutable():
    m = validate_arm_manifest(manifest_dict())
    assert m.arm_names == ("H0", "H1", "H2", "H3", "C_OBS", "C_BIO")
    assert m.training_authorized is False
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.cell_count = 99
    assert manifest_hash(m) == manifest_hash(validate_arm_manifest(manifest_dict()))
    assert canonical_manifest_json(m).startswith("{")


@pytest.mark.parametrize("mutation", [
    {"arm_names": ["H0", "H1", "H2", "H3", "C_OBS", "C_OBS"]},
    {"biology_seed": None},
    {"training_authorized": True},
    {"parameter_grid": [0.1, 0.2]},
])
def test_manifest_rejects_duplicate_missing_seed_unauthorized_or_mutable_grid(mutation):
    d = manifest_dict(); d.update(mutation)
    with pytest.raises(ValueError):
        validate_arm_manifest(d)


def test_factorial_arm_composition_and_matched_hashes():
    z0 = baseline_latent()
    worlds = build_factorial_worlds(
        manifest_dict(), bio_authority(), obs_authority(), z0, baseline_observer
    )
    assert set(worlds.arms) == {"H0", "H1", "H2", "H3"}
    assert worlds.arms["H0"].biology_kind == "E2_BASELINE"
    assert worlds.arms["H0"].observer_kind == "BASELINE"
    assert worlds.arms["H1"].biology_kind == "HIERARCHICAL"
    assert worlds.arms["H1"].observer_kind == "BASELINE"
    assert worlds.arms["H2"].biology_kind == "E2_BASELINE"
    assert worlds.arms["H2"].observer_kind == "EXPLICIT"
    assert worlds.arms["H3"].biology_kind == "HIERARCHICAL"
    assert worlds.arms["H3"].observer_kind == "EXPLICIT"
    assert worlds.arms["H1"].latent_truth_hash == worlds.arms["H3"].latent_truth_hash
    assert worlds.arms["H2"].observation_family == worlds.arms["H3"].observation_family


def test_factorial_crosses_observation_regimes_with_each_supported_class():
    worlds = build_factorial_worlds(
        manifest_dict(), bio_authority(), obs_authority(), baseline_latent(), baseline_observer
    )
    h3 = worlds.arms["H3"]
    for cls in np.unique(h3.latent.broad_class):
        labels = set(h3.observed.regime_labels[h3.latent.broad_class == cls])
        assert labels == {"OBS_A", "OBS_B"}


def test_c_obs_has_identical_truth_and_distinct_observers():
    worlds = build_factorial_worlds(
        manifest_dict(), bio_authority(), obs_authority(), baseline_latent(), baseline_observer
    )
    a, b = worlds.c_obs
    assert a.latent_truth_hash == b.latent_truth_hash
    assert set(a.observed.regime_labels) == {"OBS_A"}
    assert set(b.observed.regime_labels) == {"OBS_B"}
    assert a.observed.counts_hash != b.observed.counts_hash


def test_c_bio_has_distinct_truth_under_identical_observation_regime():
    worlds = build_factorial_worlds(
        manifest_dict(), bio_authority(), obs_authority(), baseline_latent(), baseline_observer
    )
    a, b = worlds.c_bio
    assert a.latent_truth_hash != b.latent_truth_hash
    assert np.array_equal(a.observed.regime_labels, b.observed.regime_labels)
    assert set(a.observed.regime_labels) == {"OBS_A"}

def test_world_serialization_is_identity_scrubbed_and_hash_bound(tmp_path):
    from scripts.v79.build_v79_factorial_worlds import serialize_factorial_worlds
    worlds = build_factorial_worlds(
        manifest_dict(), bio_authority(), obs_authority(), baseline_latent(), baseline_observer
    )
    rec = serialize_factorial_worlds(worlds, tmp_path)
    assert set(rec["worlds"]) == {"H0","H1","H2","H3","C_OBS_A","C_OBS_B","C_BIO_A","C_BIO_B"}
    for name, meta in rec["worlds"].items():
        assert (tmp_path / meta["npz"]).is_file()
        assert (tmp_path / meta["receipt"]).is_file()
        text = (tmp_path / meta["receipt"]).read_text().lower()
        assert "gene_id" not in text and "gene_name" not in text and "edge_list" not in text
        assert meta["latent_truth_hash"]
        assert meta["counts_hash"]

def test_world_serialization_deduplicates_dense_latent_truth(tmp_path):
    from scripts.v79.build_v79_factorial_worlds import serialize_factorial_worlds
    worlds = build_factorial_worlds(
        manifest_dict(), bio_authority(), obs_authority(), baseline_latent(), baseline_observer
    )
    rec = serialize_factorial_worlds(worlds, tmp_path)
    latent_paths = {meta["latent_npz"] for meta in rec["worlds"].values()}
    assert len(latent_paths) == 3  # baseline, hierarchical, alternate C_BIO truth
    for rel in latent_paths:
        assert (tmp_path / rel).is_file()
    for meta in rec["worlds"].values():
        observed = np.load(tmp_path / meta["npz"])
        assert "latent_abundance" not in observed.files
