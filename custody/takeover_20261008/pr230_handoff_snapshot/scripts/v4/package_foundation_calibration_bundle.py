#!/usr/bin/env python3
"""Create a hash-verified, pathology-blind FOUNDATION calibration upload bundle."""
from __future__ import annotations
import csv,hashlib,json,shutil,sys,zipfile
from pathlib import Path
import numpy as np,pandas as pd,torch
from scipy import sparse

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/foundation_calibration_bundle_20260824';ZIP=ROOT/'exports/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip';CORPUS=ROOT/'exports/foundation_corpus_discovery_v1';T1=ROOT/'exports/prod41k_teacher_t1_20260823';CTX=ROOT/'exports/contextual_biology_v6r5a_20260822'
sys.path.insert(0,str(ROOT/'exports/static_context_decomposition_v4_20260821'));sys.path.insert(0,str(ROOT/'scripts/v4'))
from production_train_loader import ProductionTrainLoader
import stage81a3_prod41k_engineering_smoke as phase_e

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def copy(src,rel,role,rows):
 src=Path(src);dst=OUT/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);rows.append({'path':rel.as_posix(),'bytes':dst.stat().st_size,'sha256':sha(dst),'role':role,'source':str(src)});print(f'copied {rel}',flush=True)
def main():
 if OUT.exists():raise RuntimeError(f'refusing to overwrite existing {OUT}')
 OUT.mkdir(parents=True);manifest=[]
 files=[
  (ROOT/'results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv','contracts/address_namespace.csv','41,238-address canonical namespace'),
  (ROOT/'results/v4/stage81a2r_foundation_molecular_address_measurement_support_candidate.csv.gz','contracts/address_measurement_support.csv.gz','authoritative 42-operator measurement support'),
  (ROOT/'results/v4/stage81a2r_matrix_measurement_support_candidate.csv.gz','contracts/matrix_measurement_support.csv.gz','matrix/operator measurement support'),
  (ROOT/'results/v4/stage81a2_split_registry.csv','splits/foundation_split_registry.csv','TRAIN/DEV/SEALED firewall registry'),
  (ROOT/'exports/static_context_decomposition_v4_20260821/production_loader_manifest.json','contracts/production_loader_manifest.json','protected loader authority hashes'),
  (ROOT/'exports/static_context_decomposition_v4_20260821/production_train_loader.py','code/production_train_loader.py','exact normalization and state loader'),
  (Path(r'D:\Jepa project-stage81a3r-20260814\results\v4\stage81a3r_expression_materialization_collision_ledger.csv.gz'),'contracts/collision_ledger.csv.gz','collision-unresolved authority'),
  (Path(r'D:\Jepa project-stage81a3r-20260814\results\v4\stage81a3r_scalar_mapping_unregistered_collisions.csv'),'contracts/unregistered_collisions.csv','supplemental collision authority'),
  (CORPUS/'FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv','support/FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv','40,949 scalar-observable / 289 collision-only recurrence'),
  (CORPUS/'FOUNDATION_SUPPORT_BY_OPERATOR.csv','support/FOUNDATION_SUPPORT_BY_OPERATOR.csv','operator support/depth'),
  (CORPUS/'FOUNDATION_SUPPORT_BY_SOURCE.csv','support/FOUNDATION_SUPPORT_BY_SOURCE.csv','source support'),
  (CORPUS/'FOUNDATION_SUPPORT_BY_CELL_CLASS.csv','support/FOUNDATION_SUPPORT_BY_CELL_CLASS.csv','cell-class support'),
  (CORPUS/'FOUNDATION_SUPPORT_ATLAS.json','support/FOUNDATION_SUPPORT_ATLAS.json','support audit'),
  (CORPUS/'FOUNDATION_SUPPORT_ATLAS.md','support/FOUNDATION_SUPPORT_ATLAS.md','support documentation'),
  (CORPUS/'foundation_metadata_rows.sqlite','metadata/foundation_metadata_rows.sqlite','6,351,753-cell authoritative metadata and reader partitions'),
  (CORPUS/'FOUNDATION_METADATA_ALL149_CONTEXT.csv','metadata/FOUNDATION_METADATA_ALL149_CONTEXT.csv','149-donor partition/source context'),
  (CORPUS/'FOUNDATION_METADATA_DONOR.csv','metadata/FOUNDATION_METADATA_DONOR.csv','donor summary'),
  (CORPUS/'FOUNDATION_METADATA_OPERATOR.csv','metadata/FOUNDATION_METADATA_OPERATOR.csv','operator summary'),
  (CORPUS/'FOUNDATION_METADATA_SOURCE.csv','metadata/FOUNDATION_METADATA_SOURCE.csv','source summary'),
  (CORPUS/'FOUNDATION_METADATA_SOURCE_X_OPERATOR.csv','metadata/FOUNDATION_METADATA_SOURCE_X_OPERATOR.csv','source-operator mapping'),
  (CORPUS/'FOUNDATION_METADATA_ATLAS.json','metadata/FOUNDATION_METADATA_ATLAS.json','metadata audit'),
  (CORPUS/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv','expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv','frozen 50k sample identities'),
  (CORPUS/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.json','expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.json','frozen sample contract'),
  (CORPUS/'FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz','expression/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz','50k x 41,238 lawful real expression'),
  (CORPUS/'FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json','expression/FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json','expression materialization audit'),
  (T1/'T1_BIOLOGY_EVALUATION_FREEZE.json','splits/T1_BIOLOGY_EVALUATION_FREEZE.json','reader-fit/validation/oracle contract'),
  (CTX/'reader_donor_split.csv','splits/reader_donor_split.csv','exact 104/22/23 donor manifest'),
  (T1/'t1_encoder_fit_inventory.csv','sampler/t1_encoder_fit_inventory.csv','accepted fit inventory'),
  (T1/'t1_training_schedule.csv','sampler/t1_training_schedule.csv','real cap8 presentation manifest'),
  (T1/'t1_training_schedule_summary.json','sampler/t1_training_schedule_summary.json','presentation summary'),
  (T1/'t1_historical_waterfill_donor_quotas.csv','sampler/t1_historical_waterfill_donor_quotas.csv','waterfill quotas'),
  (T1/'T1_SAMPLER_AUTHORITY.md','sampler/T1_SAMPLER_AUTHORITY.md','sampler semantics'),
  (T1/'HISTORICAL_STAGE81B_TAXONOMY_NEUTRAL_SAMPLER.py','sampler/HISTORICAL_STAGE81B_TAXONOMY_NEUTRAL_SAMPLER.py','recovered exact allocator'),
  (ROOT/'scripts/v4/prepare_prod41k_t1_v2_freeze.py','code/prepare_prod41k_t1_v2_freeze.py','current schedule allocator/freeze implementation'),
  (ROOT/'scripts/v4/stage81a3_prod41k_teacher_t1.py','code/stage81a3_prod41k_teacher_t1.py','exact training/preprocessing path'),
  (ROOT/'scripts/v4/stage81a3_prod41k_engineering_smoke.py','code/stage81a3_prod41k_engineering_smoke.py','exact view/masking/model construction'),
  (ROOT/'src/sea_ad_jepa/v4/gene_tokenizer.py','code/gene_tokenizer.py','encoder tokenizer'),
  (ROOT/'src/sea_ad_jepa/v4/ipb_jepa.py','code/ipb_jepa.py','encoder/IPB implementation'),
  (ROOT/'src/sea_ad_jepa/v4/masking.py','code/masking.py','mask implementation'),
  (ROOT/'src/sea_ad_jepa/v4/foundation_measurement_masks.py','code/foundation_measurement_masks.py','measurement-state masks'),
  (CORPUS/'FOUNDATION_H_ADDRESS_OPERATOR_DECOMPOSITION.csv','calibration/FOUNDATION_H_ADDRESS_OPERATOR_DECOMPOSITION.csv','real H decomposition'),
  (CORPUS/'FOUNDATION_PARTIAL_EVIDENCE_CEILING.csv','calibration/FOUNDATION_PARTIAL_EVIDENCE_CEILING.csv','partial evidence ceiling'),
  (CORPUS/'FOUNDATION_TEACHER_SHORTCUT_ATLAS.csv','calibration/FOUNDATION_TEACHER_SHORTCUT_ATLAS.csv','teacher shortcut atlas'),
  (CORPUS/'FOUNDATION_TEACHER_SHORTCUT_ATLAS.md','calibration/FOUNDATION_TEACHER_SHORTCUT_ATLAS.md','shortcut documentation'),
  (CORPUS/'SYNTH_BALANCED_VS_EMPIRICAL_RESULTS.csv','calibration/SYNTH_BALANCED_VS_EMPIRICAL_RESULTS.csv','balanced-vs-empirical stress results'),
  (CORPUS/'SYNTH_BALANCED_VS_EMPIRICAL_ADJUDICATION.md','calibration/SYNTH_BALANCED_VS_EMPIRICAL_ADJUDICATION.md','synthetic adjudication'),
  (CORPUS/'SYNTH_HETEROGENEOUS_GENERATOR_AUDIT.md','calibration/SYNTH_HETEROGENEOUS_GENERATOR_AUDIT.md','generator audit'),
  (CORPUS/'FOUNDATION_GEOMETRY_REVIEW.md','calibration/FOUNDATION_GEOMETRY_REVIEW.md','current geometry critic; may predate final geometry'),
  (T1/'t1_run/t1_checkpoint_u0000.pt','checkpoints/t1_checkpoint_u0000.pt','authenticated u0 checkpoint'),
  (T1/'t1_run/t1_checkpoint_u0205.pt','checkpoints/t1_checkpoint_u0205.pt','authenticated u205 checkpoint including EMA'),
  (T1/'t1_run/checkpoint_manifest.json','checkpoints/checkpoint_manifest.json','checkpoint SHAs/configuration'),
 ]
 for src,rel,role in files:copy(src,Path(rel),role,manifest)
 for p in sorted((CORPUS/'discovery_expression_shards').glob('op*.meta.csv')):copy(p,Path('expression/sample_operator_metadata')/p.name,'50k sample source_library/operator metadata',manifest)
 # Full exact 42 x 41,238 observation-state tensor.
 loader=ProductionTrainLoader();states=np.stack([loader.states[item['matrix_id']] for item in loader.items]).astype(np.uint8);state_path=OUT/'support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz';np.savez_compressed(state_path,states=states,matrix_id=np.asarray([item['matrix_id'] for item in loader.items]),operator_index=np.asarray([item['operator_index'] for item in loader.items]),molecular_address_index=np.arange(states.shape[1],dtype=np.int32),state_names=np.asarray(['STRUCTURALLY_UNMEASURED','MEASURED_SCALAR','MEASURED_COLLISION_UNRESOLVED']));manifest.append({'path':state_path.relative_to(OUT).as_posix(),'bytes':state_path.stat().st_size,'sha256':sha(state_path),'role':'exact uint8 observation state [42,41238]','source':'generated from protected ProductionTrainLoader'})
 # 84-cell truth table: two frozen cells/operator, exact values/states/four masks.
 freeze=pd.read_csv(CORPUS/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv');chosen=freeze.groupby('operator_index',sort=True).head(2).sort_values('operator_index');x=sparse.load_npz(CORPUS/'FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz').tocsr()[chosen.index].toarray().astype(np.float32);s=states[chosen.operator_index.to_numpy(np.int64)];hidden=[];visible=[]
 measured=torch.from_numpy(s==1);keys=torch.from_numpy(chosen.stable_key.to_numpy(np.int64))
 for view in range(4):
  block=phase_e.sample_uniform_target_blocks(measured,production_seed=8_113_002,cell_indices=keys,sample_pass=1_990_001,view_index=view);h=block.hidden_mask.cpu().numpy();hidden.append(h);visible.append(np.where(h,0,x))
 truth=OUT/'truth_table/FOUNDATION_84_CELL_TRUTH_TABLE.npz';truth.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(truth,expression_log1p10k=x,observation_state=s,measured_mask=s==1,hidden_mask=np.stack(hidden,1),final_encoder_value_input=np.stack(visible,1),stable_key=chosen.stable_key.to_numpy(np.int64),operator_index=chosen.operator_index.to_numpy(np.int16),sample_row=chosen.sample_row.to_numpy(np.int32),bitorder=np.asarray('little'),sample_pass=np.asarray(1_990_001),production_seed=np.asarray(8_113_002));chosen.to_csv(OUT/'truth_table/FOUNDATION_84_CELL_TRUTH_TABLE_METADATA.csv',index=False,lineterminator='\n');
 for p,role in [(truth,'84-cell exact semantics truth table'),(OUT/'truth_table/FOUNDATION_84_CELL_TRUTH_TABLE_METADATA.csv','truth-table metadata')]:manifest.append({'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'role':role,'source':'generated from frozen 50k sample and exact masks'})
 readme=OUT/'README.md';readme.write_text('# FOUNDATION calibration bundle — 2026-08-24\n\nPathology-blind calibration authority only. No DEV/SEALED expression is included. `expression_log1p10k` is `log1p(10000 * raw_count / source_library)`. Observation states are separate uint8 codes: 0 structural, 1 scalar measured, 2 collision unresolved. Measured zero remains measured evidence. Artificial hidden masks are separate from physical observation state. The full metadata SQLite contains 6,351,753 cells and the exact reader partition field. The 50k expression matrix is the already-frozen corpus-discovery sample. Checkpoints are included for bridge work but do not qualify u205 biology. `FOUNDATION_GEOMETRY_REVIEW.md` is historical/current-at-bundle-time and does not claim the still-running final geometry is frozen.\n',encoding='utf-8');manifest.append({'path':'README.md','bytes':readme.stat().st_size,'sha256':sha(readme),'role':'bundle semantics','source':'generated'})
 mf=OUT/'BUNDLE_SHA256_MANIFEST.csv';pd.DataFrame(manifest).sort_values('path').to_csv(mf,index=False,lineterminator='\n');status={'schema':'foundation-calibration-bundle-v1','files':len(manifest),'manifest_sha256':sha(mf),'dev_sealed_expression_included':False,'pathology_fields_included':False,'expression_cells':50000,'metadata_cells':6351753,'addresses':41238,'operators':42};(OUT/'BUNDLE_STATUS.json').write_text(json.dumps(status,indent=2)+'\n');
 with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  for p in sorted(OUT.rglob('*')):
   if p.is_file():z.write(p,Path(OUT.name)/p.relative_to(OUT))
 status['zip_bytes']=ZIP.stat().st_size;status['zip_sha256']=sha(ZIP);(OUT/'BUNDLE_STATUS.json').write_text(json.dumps(status,indent=2)+'\n');print(json.dumps(status,indent=2))
if __name__=='__main__':main()
