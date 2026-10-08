from pathlib import Path
import importlib.util
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
TRUTH=ROOT/'scripts/v64/build_v73_sharded_master_truth.py'
OBS=ROOT/'scripts/v64/build_v73_full104_sharded_observer.py'


def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def collect_panel_targets(root):
 base=root/'observable_raw/FULL104_like_sharded'
 out=[]
 import json
 manifest=json.loads((base/'FULL104_SHARDED_MANIFEST.json').read_text())
 for s in manifest['shards']:
  z=np.load(base/s['rna_file'],allow_pickle=False)
  out.append(z['empirical_projected_panel_count_target_int'])
 return np.concatenate(out)


def test_mutating_consumed_empirical_library_distribution_changes_generated_targets(tmp_path,monkeypatch):
 monkeypatch.chdir(ROOT)
 T=load(TRUTH,'v75_truth_qc_mut'); O=load(OBS,'v75_obs_qc_mut')
 a=tmp_path/'a'; b=tmp_path/'b'
 T.build(a,n_cells=600,shard_size=211,seed=7302)
 T.build(b,n_cells=600,shard_size=211,seed=7302)
 O.observe(a,seed=7302)
 original=O.Q.by_operator
 meta,by_op=original()
 mutated={k:dict(v) for k,v in by_op.items()}
 for row in mutated.values():
  row['rna_library_size_quantiles']=[float(x)*2.0 for x in row['rna_library_size_quantiles']]
 monkeypatch.setattr(O.Q,'by_operator',lambda:(meta,mutated))
 O.observe(b,seed=7302)
 ta=collect_panel_targets(a); tb=collect_panel_targets(b)
 assert not np.array_equal(ta,tb)
 assert tb.mean()>ta.mean()*1.5


def test_mutating_unused_copy_does_not_change_generated_targets(tmp_path,monkeypatch):
 monkeypatch.chdir(ROOT)
 T=load(TRUTH,'v75_truth_qc_unused'); O=load(OBS,'v75_obs_qc_unused')
 a=tmp_path/'a'; b=tmp_path/'b'
 T.build(a,n_cells=300,shard_size=101,seed=7302)
 T.build(b,n_cells=300,shard_size=101,seed=7302)
 O.observe(a,seed=7302)
 unused={'rna_library_size_quantiles':[1,2,3]}
 unused['rna_library_size_quantiles']=[10_000,20_000,30_000]
 O.observe(b,seed=7302)
 assert np.array_equal(collect_panel_targets(a),collect_panel_targets(b))
