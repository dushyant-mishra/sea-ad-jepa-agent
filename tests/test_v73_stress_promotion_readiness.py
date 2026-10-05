from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]
TRUTH=ROOT/'scripts/v64/build_v73_sharded_master_truth.py'; OBS=ROOT/'scripts/v64/build_v73_full104_sharded_observer.py'; MULTI=ROOT/'scripts/v64/build_v73_paired_multiome_sharded_observer.py'; FRAG=ROOT/'scripts/v64/build_v73_synthetic_fragments.py'; EST=ROOT/'scripts/v64/estimate_v73_synthetic_stress_resources.py'; LINK=ROOT/'scripts/v64/validate_v73_fragment_byte_linkage.py'; GATE=ROOT/'scripts/v64/validate_v73_stress_promotion_readiness.py'
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def build_ci_world(tmp_path):
 T=load(TRUTH,'t');O=load(OBS,'o');M=load(MULTI,'m');G=load(FRAG,'g');E=load(EST,'e');L=load(LINK,'l');root=tmp_path/'world';T.build(root,120,40,7302);O.observe(root,7302);M.observe(root,7302);G.build(root);rr=tmp_path/'resource.json';rr.write_text(json.dumps({'measured':E.measured_bytes(root),'calibrated_projection':{'calibration_is_ci_scale_only':True,'requires_100k_measurement_before_500k_promotion':True}}));lr=tmp_path/'link.json';lr.write_text(json.dumps(L.validate(root)));return root,rr,lr
def test_exact_empirical_bindings_authorize_only_100k(tmp_path,monkeypatch):
 V=load(GATE,'gate');monkeypatch.chdir(ROOT);root,rr,lr=build_ci_world(tmp_path);out=V.validate(root,rr,fragment_receipt=lr)
 assert out['status']=='READY_FOR_100K_STRESS_ONLY' and out['authorized_scale']=='100K_STRESS_ONLY';assert not out['blockers']
 assert out['checks']['population_authority_qualified'] and out['checks']['sampled_qc_authority_qualified'];assert out['checks']['truth_binds_population_authority'] and out['checks']['rna_binds_qc_authority'];assert out['checks']['donor_structure_qualified'] and out['checks']['operator_structure_qualified'];assert out['checks']['realised_operator_support_complete'];assert out['checks']['fragment_byte_linkage_qualified'];assert '500K_STRESS' in out['explicitly_not_authorized'] and 'FULL_4553407' in out['explicitly_not_authorized'] and 'TRAINING' in out['explicitly_not_authorized']
def test_source_manifest_tamper_fails_closed(tmp_path,monkeypatch):
 V=load(GATE,'gate2');monkeypatch.chdir(ROOT);root,rr,lr=build_ci_world(tmp_path);p=root/'observable_raw/FULL104_like_sharded/FULL104_SHARDED_MANIFEST.json';m=json.loads(p.read_text());m['source_counts']['SEA_AD']-=1;m['source_counts']['HVS']+=1;p.write_text(json.dumps(m));out=V.validate(root,rr,fragment_receipt=lr);assert out['status']=='BLOCKED';assert 'SOURCE_COUNTS_DISAGREE_ACROSS_OBSERVERS' in out['blockers']
def test_resource_receipt_is_required(tmp_path,monkeypatch):
 V=load(GATE,'gate3');monkeypatch.chdir(ROOT);root,_,lr=build_ci_world(tmp_path);out=V.validate(root,None,fragment_receipt=lr);assert out['status']=='BLOCKED';assert 'RESOURCE_RECEIPT_NOT_SUPPLIED' in out['blockers']
def test_fragment_receipt_is_required(tmp_path,monkeypatch):
 V=load(GATE,'gate_frag');monkeypatch.chdir(ROOT);root,rr,_=build_ci_world(tmp_path);out=V.validate(root,rr,fragment_receipt=None);assert out['status']=='BLOCKED';assert 'FRAGMENT_BYTE_LINKAGE_NOT_QUALIFIED' in out['blockers']
def test_realised_operator_zero_fails_closed(tmp_path,monkeypatch):
 V=load(GATE,'gate_ops');monkeypatch.chdir(ROOT);root,rr,lr=build_ci_world(tmp_path);p=root/'hidden_truth/TRUTH_MANIFEST.json';m=json.loads(p.read_text());m['empirical_calibration']['synthetic_population_summary']['operator_counts'][0]=0;m['empirical_calibration']['synthetic_population_summary']['source_operator_nonzero_cells']=41;p.write_text(json.dumps(m));out=V.validate(root,rr,fragment_receipt=lr);assert out['status']=='BLOCKED';assert 'REALIZED_OPERATOR_SUPPORT_INCOMPLETE' in out['blockers']
def test_population_authority_digest_tamper_fails_closed(tmp_path,monkeypatch):
 V=load(GATE,'gate4');monkeypatch.chdir(ROOT);root,rr,lr=build_ci_world(tmp_path);p=root/'hidden_truth/TRUTH_MANIFEST.json';m=json.loads(p.read_text());m['empirical_calibration']['authority_sha256']='0'*64;p.write_text(json.dumps(m));out=V.validate(root,rr,fragment_receipt=lr);assert out['status']=='BLOCKED';assert 'TRUTH_NOT_BOUND_TO_POPULATION_AUTHORITY' in out['blockers']
def test_qc_authority_digest_tamper_fails_closed(tmp_path,monkeypatch):
 V=load(GATE,'gate5');monkeypatch.chdir(ROOT);root,rr,lr=build_ci_world(tmp_path);p=root/'observable_raw/FULL104_like_sharded/FULL104_SHARDED_MANIFEST.json';m=json.loads(p.read_text());m['empirical_qc_calibration']['authority_sha256']='f'*64;p.write_text(json.dumps(m));out=V.validate(root,rr,fragment_receipt=lr);assert out['status']=='BLOCKED';assert 'RNA_NOT_BOUND_TO_QC_AUTHORITY' in out['blockers']
