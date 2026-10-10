import numpy as np
import pytest
from scipy import sparse

from scripts.v79.v79_hierarchical_biology import generate_latent_biology
from scripts.v79.v79_observation_operator import (
    validate_observation_authority,
    observe_latent_biology,
)


def bio_authority():
    return {
        "class_frequencies": [0.5, 0.5],
        "substates_per_class": [2, 2],
        "substate_prevalence": [1.0, 1.0],
        "module_size_distribution": [5, 8],
        "n_modules_per_substate": 2,
        "n_continuous_factors": 2,
        "substate_effect_scale": 1.0,
        "continuous_factor_scale": 0.05,
        "donor_effect_scale": 0.05,
        "baseline_log_mean": -0.2,
        "baseline_log_sd": 0.2,
    }


def good_authority(n_genes=48, family="independent_thinning"):
    support = np.ones((2, n_genes), dtype=bool)
    support[1, ::4] = False
    return {
        "regime_ids": ["OBS_A", "OBS_B"],
        "structural_support": support.tolist(),
        "capture_log_mean": [-0.2, -0.8],
        "capture_log_sd": [0.15, 0.20],
        "gene_propensity": np.linspace(0.6, 1.4, n_genes).tolist(),
        "realization_family": family,
        "molecule_scale": 6.0,
    }


@pytest.mark.parametrize("bad_key", [
    "biological_modules", "class_loadings", "gene_pair_signed_field",
    "target", "pathology", "detected_gene_count_target", "forced_k",
])
def test_authority_rejects_biology_or_shortcut_fields(bad_key):
    a = good_authority()
    a[bad_key] = [1]
    with pytest.raises(ValueError, match="forbidden|unknown"):
        validate_observation_authority(a)


def test_authority_rejects_unknown_realization_family():
    a = good_authority(family="flexible_magic")
    with pytest.raises(ValueError, match="realization"):
        validate_observation_authority(a)


@pytest.mark.parametrize("family", ["independent_thinning", "conditional_multinomial"])
def test_authority_accepts_preregistered_realization_families(family):
    a = validate_observation_authority(good_authority(family=family))
    assert a.realization_family == family
    assert a.regime_ids == ("OBS_A", "OBS_B")


def latent(n_genes=48):
    return generate_latent_biology(bio_authority(), 160, n_genes, 8, seed=41)


def test_observe_does_not_mutate_latent_truth():
    z = latent()
    before = {k: v for k, v in z.truth_hashes.items()}
    abundance = z.latent_abundance.copy()
    observe_latent_biology(z, good_authority(), np.array(["OBS_A"] * 160), seed=9)
    assert z.truth_hashes == before
    assert np.array_equal(z.latent_abundance, abundance)


def test_observation_regimes_change_counts_for_identical_latent_truth():
    z = latent()
    a = observe_latent_biology(z, good_authority(), np.array(["OBS_A"] * 160), seed=5)
    b = observe_latent_biology(z, good_authority(), np.array(["OBS_B"] * 160), seed=5)
    assert a.latent_truth_hash == b.latent_truth_hash
    assert a.counts_hash != b.counts_hash
    assert a.counts.shape == b.counts.shape


def test_structural_support_zeroes_unsupported_addresses():
    z = latent()
    out = observe_latent_biology(z, good_authority(), np.array(["OBS_B"] * 160), seed=12)
    assert sparse.isspmatrix_csr(out.counts)
    assert out.counts[:, ::4].nnz == 0


def test_detected_counts_are_outcomes_not_forced_constant():
    z = latent()
    out = observe_latent_biology(z, good_authority(), np.array(["OBS_A"] * 160), seed=17)
    assert len(np.unique(out.detected_counts)) > 5
    assert np.array_equal(out.detected_counts, np.asarray((out.counts > 0).sum(1)).ravel())
    assert np.array_equal(out.observed_library_totals, np.asarray(out.counts.sum(1)).ravel())


def test_observation_replay_is_deterministic():
    z = latent()
    labels = np.array(["OBS_A", "OBS_B"] * 80)
    a = observe_latent_biology(z, good_authority(), labels, seed=77)
    b = observe_latent_biology(z, good_authority(), labels, seed=77)
    assert a.counts_hash == b.counts_hash
    assert np.array_equal(a.capture_efficiency, b.capture_efficiency)


def test_gene_propensity_is_positional_not_identity_keyed():
    a = validate_observation_authority(good_authority())
    assert isinstance(a.gene_propensity, tuple)
    assert all(isinstance(x, float) for x in a.gene_propensity)
    assert not hasattr(a, "gene_ids")

def test_authority_accepts_compact_support_bitsets_and_constant_propensity():
    support = np.ones((2, 10), dtype=bool); support[1, ::3] = False
    packed = [np.packbits(row, bitorder="little").tobytes().hex() for row in support]
    a = {
        "regime_ids": ["A","B"],
        "n_genes": 10,
        "structural_support_hex": packed,
        "capture_log_mean": [0.0,0.0],
        "capture_log_sd": [0.2,0.2],
        "gene_propensity_constant": 1.0,
        "realization_family": "independent_thinning",
        "molecule_scale": 0.2,
    }
    out = validate_observation_authority(a)
    assert np.array_equal(np.asarray(out.structural_support), support)
    assert out.gene_propensity == (1.0,) * 10
