from pathlib import Path
import importlib.util
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'scripts/v64/v73_full104_population_geometry.py'

def load():
 spec=importlib.util.spec_from_file_location('g',MOD);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_full_scale_reconstructs_authoritative_counts_exactly(monkeypatch):
 monkeypatch.chdir(ROOT);G=load();a,trip,q=G.quotas_for_n(4_553_407)
 assert np.array_equal(q,trip[:,2])
 s=G.summary_from_quotas(a,trip,q)
 assert s['donor_counts']==a['donor_counts']
 assert s['operator_counts']==a['operator_counts']
 assert s['nonzero_donor_operator_groups']==1400

def test_2k_preserves_all_authenticated_operators(monkeypatch):
 monkeypatch.chdir(ROOT);G=load();a,trip,q=G.quotas_for_n(2_000)
 s=G.summary_from_quotas(a,trip,q)
 assert s['source_operator_nonzero_cells']==42
 assert min(s['operator_counts'])>=1

def test_100k_has_exact_frozen_source_apportionment_and_real_joint_support(monkeypatch):
 monkeypatch.chdir(ROOT);G=load();a,trip,q=G.quotas_for_n(100_000);ops=np.asarray(a['operator_sources'])
 realised={s:int(q[[ops[int(op)]==s for op in trip[:,1]]].sum()) for s in G.SOURCE_ORDER}
 assert realised=={'SEA_AD':90443,'NPH52':5193,'HVS':4364}
 s=G.summary_from_quotas(a,trip,q)
 assert s['source_operator_nonzero_cells']==42
 assert s['nonzero_donor_operator_groups']>1000
 assert s['donor_count_summary']['gini']>0.5
 assert s['operator_count_summary']['gini']>0.7

def test_payload_parts_are_digest_bound(monkeypatch):
 monkeypatch.chdir(ROOT);G=load();a,trip=G.load_authority();assert trip.shape==(1400,3);assert int(trip[:,2].sum())==4_553_407
