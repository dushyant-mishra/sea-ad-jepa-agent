from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.v79.v79_rare_biology_context_perturb_v3 import (
    SpatialConfig, generate_spatial, score_spatial,
    PerturbConfig, generate_perturb, score_perturb
)


def test_context_conditioned_prefers_true_neighbors():
    w=generate_spatial(SpatialConfig(seed=11,mode='conditioned',n_donors=66,cells_per_donor=20))
    s=score_spatial(w)
    assert s['true_context_auc'] > s['shuffled_context_auc'] + 0.05
    assert s['true_context_auc'] > s['distant_context_auc'] + 0.05


def test_intrinsic_context_has_no_true_neighbor_advantage():
    w=generate_spatial(SpatialConfig(seed=12,mode='intrinsic',n_donors=66,cells_per_donor=20))
    s=score_spatial(w)
    assert abs(s['true_minus_shuffled_auc']) < 0.12


def test_perturbation_changes_program_amplitude_but_null_does_not():
    w=generate_perturb(PerturbConfig(seed=13,n_donors=66,cells_per_donor=30))
    s=score_perturb(w)
    assert s['actual_minus_control_Rpos'] > 0.08
    assert abs(s['null_minus_control_Rpos']) < 0.12
    assert s['arm_prevalence_gap'] < 0.10


def test_prefrozen_v3_gate_helpers_accept_reference_cases():
    sc=score_spatial(generate_spatial(SpatialConfig(seed=11,mode='conditioned',n_donors=66,cells_per_donor=20)))
    si=score_spatial(generate_spatial(SpatialConfig(seed=12,mode='intrinsic',n_donors=66,cells_per_donor=20)))
    sp=score_perturb(generate_perturb(PerturbConfig(seed=13,n_donors=66,cells_per_donor=30)))
    from scripts.v79.v79_rare_biology_context_perturb_v3 import evaluate_spatial_gate,evaluate_perturb_gate
    assert evaluate_spatial_gate(sc,'conditioned')[0]
    assert evaluate_spatial_gate(si,'intrinsic')[0]
    assert evaluate_perturb_gate(sp)[0]
