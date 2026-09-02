#!/usr/bin/env python3
"""Hash-freeze the corrected prospective FULL104 shared-state procedure."""
from __future__ import annotations
import hashlib, json, os, platform, sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/full104_v014_20260826/03_phase2_state_derivation_v1'
OUT=BASE/'_staging_shared_procedure_amendment_v2'

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8<<20),b''): h.update(b)
 return h.hexdigest()
def atomic(p,v):
 t=p.with_suffix(p.suffix+'.tmp'); t.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8'); os.replace(t,p)

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 freeze=BASE/'preexpression_freeze/PHASE2_DERIVATION_FREEZE.json'
 rng=BASE/'preexpression_freeze/PHASE2_RNG_KEYS.json'
 ladder=BASE/'preexpression_freeze/PHASE2_SAMPLE_LADDER.csv'
 cap=BASE/'pregeometry_audits/PHASE2_PRODUCTION_CAPACITY_INTERFACE_AUDIT.json'
 mat=BASE/'expression_level1/PHASE2_EXPRESSION_MATERIALIZATION_MANIFEST.csv'
 for p in (freeze,rng,ladder,cap,mat):
  if not p.is_file(): raise RuntimeError(f'missing authority {p}')
 capacity=json.loads(cap.read_text())
 if capacity['status']!='PASS_CAPACITY_INTERFACES_AUTHENTICATED': raise RuntimeError('capacity gate missing')
 authority={
  'schema':'full104-phase2-shared-procedure-amendment-v2',
  'status':'FROZEN_PROSPECTIVELY_BEFORE_LEVEL1_SHARED_GEOMETRY',
  'supersedes_execution_only':['level0 terminal interpretation','analytic-null-only shared selection','unexplained rank320/width160 capacity interpretation'],
  'preserves':['41,238 address order','104 reader_fit donors','42 operators','four views','60% evidence','donor-primary weights','nested sample ladder','all protected-data firewalls'],
  'architecture_capacity':{
   'authority_tag':'FROZEN_ARCHITECTURE_CAPACITY',
   'molecular_ledger_token_width':160,
   'active_CELL_width':160,
   'gene_identity_width':48,
   'IPB_blocks':6,'attention_heads':4,
   'state_head_output':'runtime parameterized state_dim; no code-authenticated fixed D_total ceiling',
   'direct_route_rank':'min(eligible scalar addresses,state_dim)',
   'contextual_residual_input_bottleneck':160,
   'rule':'D_shared/D_private/D_total remain DERIVE_ON_104_FIT; never truncate to 96 or 160; capacity STOP requires stable data-derived D and a demonstrated incompatible authenticated interface',
   'capacity_audit_sha256':sha(cap),
   'code_hashes':capacity['hashes'],
  },
  'sample_ladder':{
   'levels':[0,1,2,3,4], 'full104_level':4,
   'rule':'level0 exploratory; every nonfinal level advances unless convergence is demonstrated against a successive evaluated level; unsupported or boundary-reaching nonfinal evidence always advances; FULL104 is fail-safe',
   'convergence':'smallest nested level within one paired-donor-bootstrap SE of the largest evaluated level for held-donor predictability, with no material donor-resampled subspace loss and stable local D bracket',
   'ladder_sha256':sha(ladder),
  },
  'empirical_matched_null':{
   'authority_tag':'PROSPECTIVE_DERIVATION_PROCEDURE',
   'replicates':256,
   'rng_authority':'matched_null key in PHASE2_RNG_KEYS.json',
   'strata':['donor_id','operator_index'],
   'marginals_preserved':['donor','source','operator','operator physical support','source_library/depth multiset','view marginal','evidence fraction'],
   'map':'for each replicate/sketch/stratum, one keyed random row order; views receive keyed distinct cyclic offsets when n>=4; n=2/3 are explicitly limited-permutation; n=1 is unshufflable and unchanged',
   'selection':'empirical null distribution selects shared prefix; analytic donor×operator derangement expectation is diagnostic only',
   'maps':'save seeds, offsets, stratum counts, and SHA256 digest of every expanded mapping; do not store redundant multi-gigabyte maps',
   'rng_file_sha256':sha(rng),
  },
  'shared_selection':{
   'authority_tag':'DERIVE_ON_104_FIT',
   'coarse_grid_role':'bracket only; local refinement every legal dimension before final freeze',
   'requires':['observed generalized signal above empirical null','donor bootstrap subspace stability above empirical null','donor-heldout predictability above empirical null','support in both paired technical sketches A/B'],
   'technical_replicates':'A/B paired at donor level; never double biological N',
   'labels_forbidden':['PCA96','program','rare','pathology','native cell type'],
  },
  'inputs':{'preexpression_freeze_sha256':sha(freeze),'rng_keys_sha256':sha(rng),'level1_expression_manifest_sha256':sha(mat)},
  'environment':{'python':sys.version,'platform':platform.platform()},
  'no_private_calibration_gpu_training_or_protected_expression':True,
 }
 p=OUT/'PHASE2_SHARED_PROCEDURE_AMENDMENT_V2.json'; atomic(p,authority)
 manifest=OUT/'PHASE2_SHARED_PROCEDURE_AMENDMENT_MANIFEST.csv'
 files=[p,Path(__file__),freeze,rng,ladder,cap,mat]
 pd.DataFrame([{'path':str(x),'bytes':x.stat().st_size,'sha256':sha(x)} for x in files]).to_csv(manifest,index=False,lineterminator='\n')
 (BASE/'PHASE2_SHARED_PROCEDURE_AMENDMENT_MANIFEST_SHA256.txt').write_text(sha(manifest)+'\n',encoding='ascii')
 print(json.dumps({'status':authority['status'],'manifest_sha256':sha(manifest)},indent=2))
if __name__=='__main__': main()
