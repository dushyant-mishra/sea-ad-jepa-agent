from pathlib import Path
import importlib.util
import json

ROOT=Path(__file__).resolve().parents[1]
TRUTH=ROOT/'scripts/v64/build_v73_sharded_master_truth.py'
MULTI=ROOT/'scripts/v64/build_v73_paired_multiome_sharded_observer.py'
FRAG=ROOT/'scripts/v64/build_v73_synthetic_fragments.py'
VERIFY=ROOT/'scripts/v64/validate_v73_fragment_byte_linkage.py'


def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def build_world(tmp_path):
 T=load(TRUTH,'v75_frag_truth');M=load(MULTI,'v75_frag_multi');G=load(FRAG,'v75_frag_build')
 root=tmp_path/'world';T.build(root,n_cells=72,shard_size=24,seed=7302);M.observe(root,seed=7302);G.build(root);return root


def test_independent_fragment_byte_linkage_passes(tmp_path):
 V=load(VERIFY,'v75_frag_verify_pass');root=build_world(tmp_path);out=V.validate(root)
 assert out['status']=='PASS';assert out['qualified'] is True
 assert out['compressed_sha256_recomputed_from_bytes'] is True
 assert out['barcode_multiplicity_reconciled_to_multiome'] is True


def test_fragment_byte_mutation_fails_even_when_record_content_is_unchanged(tmp_path):
 V=load(VERIFY,'v75_frag_verify_digest');root=build_world(tmp_path)
 base=root/'observable_raw/PAIRED_MULTIOME_fragments';manifest=json.loads((base/'SYNTHETIC_FRAGMENT_MANIFEST.json').read_text())
 target=base/manifest['shards'][0]['file'];before=target.read_bytes();mutated=bytearray(before);mutated[4]^=0x01;target.write_bytes(mutated)
 assert target.stat().st_size==len(before)
 out=V.validate(root);assert out['status']=='FAIL_CLOSED';assert out['failure_code']=='COMPRESSED_SHA256_MISMATCH'
