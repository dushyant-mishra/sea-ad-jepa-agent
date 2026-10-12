import hashlib
from pathlib import Path
import numpy as np
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.v79.v79_rare_biology_production_v1 import ProductionConfig, realize_production


def test_production_realization_is_deterministic_and_blinded(tmp_path):
    cfg = ProductionConfig(seed_root=79102026, n_donors=12, cells_per_donor=8, regimes=('central',), worlds=('rna_only','same_nucleus','separate_nucleus','technical_twin'))
    a = tmp_path/'a'; b = tmp_path/'b'
    ra = realize_production(cfg, a); rb = realize_production(cfg, b)
    assert ra['directory_digest_sha256'] == rb['directory_digest_sha256']
    assert len(ra['worlds']) == 4
    for w in ra['worlds']:
        fit = np.load(a/w['fit_relpath'], allow_pickle=False)
        assert set(fit.files) == {'rna','atac','source_code','donor_code','rna_entity_code','atac_entity_code'}
        truth = np.load(a/w['truth_relpath'], allow_pickle=False)
        assert {'R','pseudo_rare','donor_active','donor_prevalence','world_code','regime_code'}.issubset(truth.files)
        assert 'R' not in fit.files and 'pseudo_rare' not in fit.files


def test_world_ids_do_not_disclose_world_or_regime(tmp_path):
    cfg = ProductionConfig(seed_root=79102026, n_donors=6, cells_per_donor=4, regimes=('weak','central'), worlds=('rna_only','technical_twin'))
    receipt = realize_production(cfg, tmp_path)
    ids = [w['world_id'] for w in receipt['worlds']]
    assert ids == ['RW000','RW001','RW002','RW003']
    for w in receipt['worlds']:
        assert w['world'] not in w['fit_relpath']
        assert w['regime'] not in w['fit_relpath']


def test_truth_and_fit_hashes_are_bound(tmp_path):
    cfg = ProductionConfig(seed_root=79102026, n_donors=6, cells_per_donor=4, regimes=('central',), worlds=('same_nucleus',))
    r = realize_production(cfg, tmp_path)
    w=r['worlds'][0]
    for key in ('fit','truth'):
        p=tmp_path/w[f'{key}_relpath']
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        assert h == w[f'{key}_sha256']
