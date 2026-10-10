import inspect
import numpy as np
import pytest

from scripts.v79.v79_hierarchical_biology import (
    validate_biology_authority,
    generate_latent_biology,
)


def good_authority():
    return {
        "class_frequencies": [0.45, 0.35, 0.20],
        "substates_per_class": [2, 3, 2],
        "substate_prevalence": [1.0, 1.0, 1.0],
        "module_size_distribution": [6, 10, 14],
        "n_modules_per_substate": 2,
        "n_continuous_factors": 3,
        "substate_effect_scale": 1.2,
        "continuous_factor_scale": 0.08,
        "donor_effect_scale": 0.12,
        "baseline_log_mean": -0.2,
        "baseline_log_sd": 0.35,
    }


@pytest.mark.parametrize("bad_key", [
    "gene_ids", "gene_names", "edge_list", "pathway", "target",
    "donor_gene_effects", "source", "operator", "source_library",
])
def test_authority_rejects_identity_or_observation_fields(bad_key):
    a = good_authority()
    a[bad_key] = [1, 2]
    with pytest.raises(ValueError, match="forbidden|unknown"):
        validate_biology_authority(a)


def test_authority_accepts_anonymous_distributional_fields():
    a = validate_biology_authority(good_authority())
    assert a.class_frequencies == (0.45, 0.35, 0.20)
    assert a.module_size_distribution == (6, 10, 14)
    assert a.donor_effect_scale == pytest.approx(0.12)


def test_generate_signature_has_no_observation_arguments():
    params = set(inspect.signature(generate_latent_biology).parameters)
    assert not {"source", "operator", "source_library", "observation_regime"} & params


def test_deterministic_replay_is_byte_identical():
    kwargs = dict(authority=good_authority(), n_cells=240, n_genes=96, n_donors=12, seed=7302)
    a = generate_latent_biology(**kwargs)
    b = generate_latent_biology(**kwargs)
    for name in ["broad_class", "substate", "donor", "continuous_factors", "latent_abundance", "biological_total_scale"]:
        assert np.array_equal(getattr(a, name), getattr(b, name))
    assert a.truth_hashes == b.truth_hashes


def test_different_seed_changes_latent_truth():
    a = generate_latent_biology(good_authority(), 240, 96, 12, seed=7302)
    b = generate_latent_biology(good_authority(), 240, 96, 12, seed=7303)
    assert a.truth_hashes["latent_abundance"] != b.truth_hashes["latent_abundance"]


def test_substate_blocks_are_coherent_within_class():
    x = generate_latent_biology(good_authority(), 1200, 120, 20, seed=11)
    cls = 0
    ix0 = np.flatnonzero((x.broad_class == cls) & (x.substate == 0))
    ix1 = np.flatnonzero((x.broad_class == cls) & (x.substate == 1))
    assert len(ix0) > 20 and len(ix1) > 20
    delta = np.abs(x.latent_abundance[ix0].mean(0) - x.latent_abundance[ix1].mean(0))
    assert np.quantile(delta, 0.9) > 3 * np.median(delta)


def test_continuous_factors_add_lower_amplitude_within_substate_variation():
    x = generate_latent_biology(good_authority(), 800, 96, 16, seed=19)
    grp = np.flatnonzero((x.broad_class == 0) & (x.substate == 0))
    assert len(grp) > 20
    within = np.std(x.latent_abundance[grp], axis=0)
    means = []
    for s in np.unique(x.substate[x.broad_class == 0]):
        ix = np.flatnonzero((x.broad_class == 0) & (x.substate == s))
        means.append(x.latent_abundance[ix].mean(0))
    between = np.std(np.stack(means), axis=0)
    # Sparse anonymous blocks need not move the median gene. On the genes most
    # affected by substate structure, the discrete effect must dominate typical
    # within-substate continuous/donor variation.
    assert np.quantile(between, 0.9) > np.median(within)


def test_donor_labels_are_synthetic_and_supported():
    x = generate_latent_biology(good_authority(), 600, 64, 15, seed=23)
    assert x.donor.dtype.kind in "iu"
    assert x.donor.min() >= 0 and x.donor.max() < 15
    assert len(np.unique(x.donor)) == 15
    assert np.all(x.biological_total_scale > 0)

def test_authority_accepts_identity_scrubbed_baseline_abundance_quantiles():
    a = good_authority()
    a["baseline_abundance_quantile_probs"] = [0.0, 0.5, 1.0]
    a["baseline_abundance_quantiles"] = [0.2, 1.0, 8.0]
    out = validate_biology_authority(a)
    assert out.baseline_abundance_quantiles == (0.2, 1.0, 8.0)


def test_empirical_baseline_quantiles_create_anonymous_gene_heterogeneity():
    a = good_authority()
    a["baseline_abundance_quantile_probs"] = [0.0, 0.5, 0.9, 1.0]
    a["baseline_abundance_quantiles"] = [0.1, 1.0, 4.0, 20.0]
    x = generate_latent_biology(a, 600, 120, 12, seed=31)
    gene_means = x.latent_abundance.mean(0)
    assert np.quantile(gene_means, 0.9) > 2 * np.median(gene_means)

def test_dense_latent_numeric_arrays_use_float32_for_fullscale_memory_budget():
    x = generate_latent_biology(good_authority(), 120, 96, 12, seed=37)
    assert x.latent_abundance.dtype == np.float32
    assert x.continuous_factors.dtype == np.float32
    assert x.biological_total_scale.dtype == np.float32
