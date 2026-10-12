from __future__ import annotations
import numpy as np
import pandas as pd
from .v79_rare_biology_generator_v1 import RareWorld, SIGNS


def _auc(y: np.ndarray, score: np.ndarray) -> float:
    y = np.asarray(y, dtype=int)
    score = np.asarray(score, dtype=float)
    n1 = int(y.sum())
    n0 = int((1-y).sum())
    if n1 == 0 or n0 == 0:
        return float('nan')
    ranks = pd.Series(score).rank(method='average').to_numpy()
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def score_world(world: RareWorld) -> dict[str, float | int]:
    y = world.cells['R'].to_numpy(dtype=int)
    rna_score = (world.rna * SIGNS[None, :]).mean(axis=1)
    atac_score = world.atac.mean(axis=1)
    # Controller-only privileged diagnostic. Fit/student code must never receive R.
    teacher_score = rna_score + atac_score
    by_donor = pd.DataFrame({
        'donor_id': world.cells['donor_id'].to_numpy(),
        'rna': rna_score,
        'atac': atac_score,
    }).groupby('donor_id', sort=False).mean()
    source_prev = world.cells.groupby('source', sort=False)['R'].mean()
    return {
        'n_cells': int(len(y)),
        'n_biological_positive': int(y.sum()),
        'biological_prevalence': float(y.mean()),
        'pseudo_rare_fraction': float(world.cells['pseudo_rare'].mean()),
        'student_auc': _auc(y, rna_score),
        'teacher_auc': _auc(y, teacher_score),
        'same_cell_rna_atac_corr': float(np.corrcoef(rna_score, atac_score)[0, 1]),
        'donor_rna_atac_corr': float(by_donor['rna'].corr(by_donor['atac'])),
        'latent_source_prevalence_gap': float(source_prev.max() - source_prev.min()),
    }
