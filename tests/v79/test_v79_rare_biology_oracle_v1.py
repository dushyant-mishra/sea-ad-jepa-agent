import numpy as np
from scripts.v79.v79_rare_biology_generator_v1 import RareWorldConfig, generate_world
from scripts.v79.v79_rare_biology_oracle_v1 import score_world


def test_same_nucleus_oracle_sees_strong_teacher_signal():
    w = generate_world(RareWorldConfig(seed=101, n_donors=120, cells_per_donor=30, world='same_nucleus'))
    s = score_world(w)
    assert s['teacher_auc'] > 0.80
    assert s['student_auc'] > 0.60
    assert s['same_cell_rna_atac_corr'] > 0.30


def test_separate_nucleus_drops_same_cell_but_retains_donor_signal():
    w = generate_world(RareWorldConfig(seed=102, n_donors=120, cells_per_donor=30, world='separate_nucleus'))
    s = score_world(w)
    assert s['same_cell_rna_atac_corr'] < 0.30
    assert s['donor_rna_atac_corr'] > 0.25


def test_technical_twin_contains_no_oracle_biology():
    w = generate_world(RareWorldConfig(seed=103, n_donors=120, cells_per_donor=30, world='technical_twin'))
    s = score_world(w)
    assert s['n_biological_positive'] == 0
    assert np.isnan(s['teacher_auc'])
    assert s['pseudo_rare_fraction'] > 0.02


def test_source_prevalence_gap_is_bounded():
    w = generate_world(RareWorldConfig(seed=104, n_donors=300, cells_per_donor=30, world='same_nucleus'))
    s = score_world(w)
    assert s['latent_source_prevalence_gap'] < 0.04
