#!/usr/bin/env python3
"""Validate and hash-freeze FOUNDATION_CORPUS_DISCOVERY_V1."""
from __future__ import annotations
import hashlib,json,platform,sys
from pathlib import Path
import numpy,pandas,scipy,sklearn,torch

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'exports/foundation_corpus_discovery_v1'

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()

def main():
 required=['FOUNDATION_CORPUS_DISCOVERY_FINAL.md','FOUNDATION_CORPUS_DISCOVERY_FINAL.json','FOUNDATION_CORPUS_DISCOVERY_MULTIAGENT_ADJUDICATION.md','FOUNDATION_TEACHER_DISCOVERY_SYNTHESIS.md','FOUNDATION_DISCOVERY_EXPRESSION_LINEAGE_V2.json','FOUNDATION_OPERATOR_PARALLEL_SKETCH_COMPARISON.json','FOUNDATION_OPERATOR_PARALLEL_SKETCH_ITERATIVE_SENSITIVITY.json','FOUNDATION_TEACHER_FROZEN_EXPRESSION_AUDIT.json','FOUNDATION_CURRENT_REAL_VALUE_SANITY.json','SYNTH_BALANCED_VS_EMPIRICAL_RESULTS.csv']
 missing=[x for x in required if not (OUT/x).exists()]
 if missing:raise RuntimeError('missing final artifacts '+repr(missing))
 final=json.loads((OUT/'FOUNDATION_CORPUS_DISCOVERY_FINAL.json').read_text());lineage=json.loads((OUT/'FOUNDATION_DISCOVERY_EXPRESSION_LINEAGE_V2.json').read_text());geo=json.loads((OUT/'FOUNDATION_OPERATOR_PARALLEL_SKETCH_COMPARISON.json').read_text())
 if final['decision']!='FRESH_MATCHED_U0_ARM_REQUIRED' or lineage['status']!='PASS' or lineage['operator_count']!=42 or geo['local_geometry_validity']!='UNRESOLVED_SEED_SENSITIVE' or final['training_updates']!=0:raise RuntimeError('final contract mismatch')
 env={'schema':'foundation-discovery-environment-v1','platform':platform.platform(),'python':sys.version,'packages':{'numpy':numpy.__version__,'pandas':pandas.__version__,'scipy':scipy.__version__,'scikit_learn':sklearn.__version__,'torch':torch.__version__},'cuda_available':torch.cuda.is_available(),'cuda_version':torch.version.cuda,'cuda_device':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,'code_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'scripts/v4/foundation_materialize_discovery_expression.py',ROOT/'scripts/v4/foundation_expression_lineage_reaudit.py',ROOT/'scripts/v4/foundation_gpu_sketch_materialize.py',ROOT/'scripts/v4/foundation_operator_parallel_sketch.py',ROOT/'scripts/v4/foundation_sketch_iterative_sensitivity.py',ROOT/'scripts/v4/foundation_teacher_discovery_on_frozen_expression.py',ROOT/'scripts/v4/foundation_expression_value_sanity.py',ROOT/'scripts/v4/foundation_finalize_discovery.py']},'training_updates':0}
 ep=OUT/'FOUNDATION_DISCOVERY_ENVIRONMENT_PROVENANCE.json';ep.write_text(json.dumps(env,indent=2)+'\n',encoding='utf-8')
 manifest=OUT/'FOUNDATION_CORPUS_DISCOVERY_HASH_MANIFEST.csv';rows=[]
 for p in sorted(x for x in OUT.rglob('*') if x.is_file() and x!=manifest):rows.append((str(p.relative_to(OUT)).replace('\\','/'),p.stat().st_size,sha(p)))
 with manifest.open('w',encoding='utf-8',newline='') as f:
  f.write('relative_path,bytes,sha256\n')
  for path,size,digest in rows:f.write(f'"{path}",{size},{digest}\n')
 print(json.dumps({'status':'PASS','files_hashed':len(rows),'manifest_sha256':sha(manifest),'final_json_sha256':sha(OUT/'FOUNDATION_CORPUS_DISCOVERY_FINAL.json')},indent=2))

if __name__=='__main__':main()
