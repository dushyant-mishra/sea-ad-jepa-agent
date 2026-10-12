from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.v79.v79_rare_biology_qualification_realizer_v2 import QualificationRealizationConfig, realize_qualification
from scripts.v79.v79_rare_biology_qualification_scorer_v2 import score_package


def test_controller_scorer_scores_all_challenges_and_keeps_extreme_report_only(tmp_path):
    cfg=QualificationRealizationConfig(seed_root=79202026,n_donors=120,cells_per_donor=20,
        kinds=('rna_recoverable','teacher_private','separate_nucleus','technical_twin'),regimes=('weak','central','strong','extreme'))
    realize_qualification(cfg,tmp_path)
    result=score_package(tmp_path)
    assert len(result['rows'])==16
    assert result['gating_challenge_count']==12
    assert result['extreme_report_only_count']==4
    assert set(r['gate_status'] for r in result['rows'] if r['regime']=='extreme') <= {'REPORT_ONLY_STRUCTURAL_PASS','REPORT_ONLY_STRUCTURAL_FAIL'}


def test_controller_scorer_detects_truth_tamper(tmp_path):
    cfg=QualificationRealizationConfig(seed_root=79202026,n_donors=30,cells_per_donor=10,kinds=('technical_twin',),regimes=('central',))
    receipt=realize_qualification(cfg,tmp_path)
    truth=tmp_path/receipt['challenges'][0]['truth_relpath']
    truth.write_bytes(truth.read_bytes()+b'x')
    try:
        score_package(tmp_path)
    except ValueError as e:
        assert 'hash' in str(e).lower()
    else:
        raise AssertionError('tamper not detected')
