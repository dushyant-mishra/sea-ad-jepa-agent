from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.v79.v79_rare_biology_qualification_v2 import ChallengeConfig, score_challenge, evaluate_geometry_gate


def test_teacher_private_has_privileged_increment():
    s=score_challenge(ChallengeConfig(seed=123,kind='teacher_private',regime='central',n_donors=120,cells_per_donor=20))
    assert s['teacher_auc_full'] > s['rna_auc_full'] + 0.10
    assert s['rna_auc_full'] < 0.85


def test_separate_nucleus_is_donor_not_same_cell_geometry():
    s=score_challenge(ChallengeConfig(seed=321,kind='separate_nucleus',regime='central',n_donors=120,cells_per_donor=20))
    assert abs(s['same_cell_rna_atac_corr']) < 0.30
    assert s['donor_rna_atac_corr'] > 0.20


def test_nested_evidence_and_depth_endpoints_gain_information():
    s=score_challenge(ChallengeConfig(seed=17,kind='rna_recoverable',regime='central',n_donors=120,cells_per_donor=20))
    assert s['rna_auc_e100'] >= s['rna_auc_e20']
    assert s['rna_auc_d100'] >= s['rna_auc_d25']


def test_technical_twin_is_tempting_but_has_no_R():
    s=score_challenge(ChallengeConfig(seed=222,kind='technical_twin',regime='central',n_donors=120,cells_per_donor=20))
    assert s['prevalence'] == 0
    assert s['pseudo_auc_rna'] > 0.70


def test_prefrozen_geometry_gate_accepts_reference_cases():
    for kind in ['rna_recoverable','teacher_private','separate_nucleus','technical_twin']:
        s=score_challenge(ChallengeConfig(seed=1234,kind=kind,regime='central',n_donors=66,cells_per_donor=20))
        ok,why=evaluate_geometry_gate(s)
        assert ok, (kind,why,s)
