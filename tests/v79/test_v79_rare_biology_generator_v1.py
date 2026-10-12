import numpy as np
import pandas as pd
from scripts.v79.v79_rare_biology_generator_v1 import RareWorldConfig, generate_world


def test_deterministic_seed():
    cfg = RareWorldConfig(seed=17, n_donors=60, cells_per_donor=20)
    a = generate_world(cfg)
    b = generate_world(cfg)
    pd.testing.assert_frame_equal(a.cells, b.cells)
    np.testing.assert_allclose(a.rna, b.rna)
    np.testing.assert_allclose(a.atac, b.atac)


def test_latent_biology_is_not_caused_by_source():
    cfg = RareWorldConfig(seed=3, n_donors=120, cells_per_donor=20)
    w = generate_world(cfg)
    donor = w.cells.drop_duplicates('donor_id')
    assert donor.groupby('source')['donor_active'].mean().max() - donor.groupby('source')['donor_active'].mean().min() < 0.20


def test_central_regime_is_donor_sparse_and_cell_rare():
    cfg = RareWorldConfig(seed=41, n_donors=300, cells_per_donor=40, regime='central')
    w = generate_world(cfg)
    donor = w.cells.drop_duplicates('donor_id')
    active = donor['donor_active'].mean()
    cell_prev = w.cells['R'].mean()
    assert 0.15 <= active <= 0.38
    assert 0.015 <= cell_prev <= 0.075
    assert (donor['donor_active'] == 0).mean() > 0.5


def test_technical_twin_has_no_biological_state():
    cfg = RareWorldConfig(seed=11, n_donors=80, cells_per_donor=20, world='technical_twin')
    w = generate_world(cfg)
    assert w.cells['R'].sum() == 0
    assert 0.02 <= w.cells['pseudo_rare'].mean() <= 0.07


def test_same_nucleus_world_couples_rna_and_atac_more_than_null():
    cfg = RareWorldConfig(seed=23, n_donors=100, cells_per_donor=25, world='same_nucleus')
    w = generate_world(cfg)
    rna_score = w.rna.mean(axis=1)
    atac_score = w.atac.mean(axis=1)
    corr = np.corrcoef(rna_score, atac_score)[0, 1]
    assert corr > 0.30


def test_separate_nucleus_world_has_donor_but_not_cell_pairing():
    cfg = RareWorldConfig(seed=29, n_donors=90, cells_per_donor=20, world='separate_nucleus')
    w = generate_world(cfg)
    assert not np.array_equal(w.cells['rna_entity_id'].to_numpy(), w.cells['atac_entity_id'].to_numpy())
    donor_rna = pd.Series(w.rna.mean(axis=1)).groupby(w.cells['donor_id']).mean()
    donor_atac = pd.Series(w.atac.mean(axis=1)).groupby(w.cells['donor_id']).mean()
    assert donor_rna.corr(donor_atac) > 0.25


def test_source_visibility_changes_observed_genes_not_latent_state():
    cfg = RareWorldConfig(seed=31, n_donors=180, cells_per_donor=20)
    w = generate_world(cfg)
    means = {}
    for src in ['HVS','NPH52','SEA_AD']:
        idx = w.cells['source'].eq(src).to_numpy() & w.cells['R'].eq(1).to_numpy()
        means[src] = w.rna[idx].mean() if idx.any() else np.nan
    assert means['NPH52'] > means['HVS']
    assert means['NPH52'] > means['SEA_AD']
