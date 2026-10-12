from pathlib import Path
import numpy as np
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.v79.v79_rare_biology_qualification_realizer_v2 import QualificationRealizationConfig, realize_qualification


def test_realization_blinds_kind_and_regime(tmp_path):
    cfg=QualificationRealizationConfig(seed_root=79202026,n_donors=12,cells_per_donor=8,kinds=('rna_recoverable','teacher_private'),regimes=('central',))
    r=realize_qualification(cfg,tmp_path)
    assert r['challenge_count']==2
    for e in r['challenges']:
        assert e['kind'] not in e['fit_relpath']
        assert e['regime'] not in e['fit_relpath']
        fit=np.load(tmp_path/e['fit_relpath'],allow_pickle=False)
        assert 'R' not in fit.files and 'kind_code' not in fit.files
        truth=np.load(tmp_path/e['truth_relpath'],allow_pickle=False)
        assert {'R','pseudo_rare','kind_code','regime_code'}.issubset(truth.files)


def test_realization_is_deterministic(tmp_path):
    cfg=QualificationRealizationConfig(seed_root=79202026,n_donors=10,cells_per_donor=5,kinds=('separate_nucleus','technical_twin'),regimes=('weak','central'))
    a=tmp_path/'a';b=tmp_path/'b'
    ra=realize_qualification(cfg,a);rb=realize_qualification(cfg,b)
    assert ra['directory_digest_sha256']==rb['directory_digest_sha256']
