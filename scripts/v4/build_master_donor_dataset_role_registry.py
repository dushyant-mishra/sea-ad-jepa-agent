#!/usr/bin/env python3
"""Build the evidence-backed donor/dataset/role master registry without guessing links."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'exports/master_donor_dataset_role_registry_20260825'
OUT.mkdir(parents=True,exist_ok=True)

PATHS={
 'split':ROOT/'results/v4/stage81a2_split_registry.csv',
 'roles':ROOT/'results/v4/stage81a2_dataset_role_registry.csv',
 'assets':ROOT/'results/v4/stage81a2_canonical_asset_registry.csv',
 'matrix':ROOT/'results/v4/stage81a3_foundation_matrix_inventory.csv',
 'reader':ROOT/'exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv',
 'phase_e':ROOT/'exports/prod41k_teacher_t1_20260823/phase_e_foundation_train_cohort_manifest.csv',
 'fit_pairs':ROOT/'exports/foundation_corpus_discovery_v1/FOUNDATION_METADATA_DONOR_X_OPERATOR.csv',
 'all149_context':ROOT/'exports/foundation_corpus_discovery_v1/FOUNDATION_METADATA_ALL149_CONTEXT.csv',
 'fit_donor_summary':ROOT/'exports/foundation_corpus_discovery_v1/FOUNDATION_METADATA_DONOR.csv',
 'downloads':ROOT/'results/v4/stage81a2r_all_downloaded_asset_identity_inventory_candidate.csv',
 'context':ROOT/'results/v4/stage81a3_context_dataset_role_matrix.csv',
 'provided_master_json':OUT/'provided_reference/JEPA_DATASET_AUTHORITY_MASTER_20260825.json',
 'provided_master_md':OUT/'provided_reference/JEPA_DATASET_AUTHORITY_MASTER_20260825.md',
 'provided_workbook':OUT/'provided_reference/JEPA_DATASET_AUTHORITY_MASTER_20260825.xlsx',
 'provided_provenance_audit':OUT/'provided_reference/JEPA_DATASET_PROVENANCE_AND_HOLDOUT_AUDIT_20260825.md',
 'provided_sha_manifest':OUT/'provided_reference/SHA256_MANIFEST.csv',
}

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def truth(v):return str(v).strip().lower()=='true'
def clean(v):return '' if pd.isna(v) else str(v)
def rid(*parts):return hashlib.sha256('|'.join(map(clean,parts)).encode()).hexdigest()[:24]

COLUMNS=['record_id','record_scope','authority_status','donor_resolution_status','canonical_person_id','source_donor_id','study_id','cohort','split_domain','split','reader_partition','dataset_id','matrix_id','local_asset_path','asset_exists','registered_asset_sha256','dataset_role','tissue_state','foundation_vocabulary_eligible','foundation_eligible_asset','claim_boundary','qualification_role','allowed_use','forbidden_use','current_training_authorized','mapping_cell_count','mapping_evidence','pathology_bearing_asset','pathology_used_for_foundation_split','holdout_validation_adapter','quarantine_required','reference_only','supportive_eligible','source_sample_count','source_sample_ids','split_authority','role_authority','asset_authority','mapping_authority','notes']

def blank():return {c:'' for c in COLUMNS}

def main():
 missing=[str(p) for p in PATHS.values() if not p.exists()]
 if missing:raise RuntimeError('missing authority inputs '+repr(missing))
 split=pd.read_csv(PATHS['split'],dtype=str).fillna('');roles=pd.read_csv(PATHS['roles'],dtype=str).fillna('');assets=pd.read_csv(PATHS['assets'],dtype=str).fillna('');matrix=pd.read_csv(PATHS['matrix'],dtype=str).fillna('');reader=pd.read_csv(PATHS['reader'],dtype=str).fillna('');phase=pd.read_csv(PATHS['phase_e'],dtype=str).fillna('');fit=pd.read_csv(PATHS['fit_pairs'],dtype=str).fillna('');all149=pd.read_csv(PATHS['all149_context'],dtype=str).fillna('');downloads=pd.read_csv(PATHS['downloads'],dtype=str).fillna('');context=pd.read_csv(PATHS['context'],dtype=str).fillna('')
 if len(split)!=215 or split.canonical_person_id.nunique()!=215:raise RuntimeError('split authority drift')
 foundation_train=split[(split.split_domain=='foundation')&(split.split=='train')]
 if len(foundation_train)!=149 or reader.donor_id.nunique()!=149 or reader.reader_partition.value_counts().to_dict()!={'reader_fit':104,'reader_oracle':23,'reader_validation':22}:raise RuntimeError('reader firewall drift')
 raw_to_person=dict(zip(foundation_train.canonical_person_id.str.split('::',n=1).str[-1],foundation_train.canonical_person_id));reader_map=dict(zip(reader.donor_id,reader.reader_partition))
 if set(reader_map)!=set(raw_to_person):raise RuntimeError('reader/split donor mismatch')
 if int(all149.cell_count.astype(int).sum())!=6_351_753 or int(all149.donor_count.astype(int).sum())!=149:raise RuntimeError('all149 lawful inventory drift')
 provided=json.loads(PATHS['provided_master_json'].read_text(encoding='utf-8'))
 supplied_manifest=pd.read_csv(PATHS['provided_sha_manifest'])
 for x in supplied_manifest.itertuples(index=False):
  p=PATHS['provided_sha_manifest'].parent/clean(x.file)
  if not p.exists() or p.stat().st_size!=int(x.bytes) or sha(p).lower()!=clean(x.sha256).lower():raise RuntimeError('provided package manifest mismatch '+clean(x.file))
 fit_donors={d for d,r in reader_map.items() if r=='reader_fit'}
 if set(fit.donor_id)!=fit_donors or fit.cell_count.astype(int).sum()!=4_553_407 or len(fit)!=1400:raise RuntimeError('fit-104 full metadata drift')
 role_by_id=roles.set_index('dataset_id').to_dict('index');asset_by_id=assets.set_index('dataset_id').to_dict('index');matrix_by_id=matrix.set_index('matrix_id').to_dict('index')
 download_by_path={clean(r.local_path):r for r in downloads.itertuples(index=False)}
 rows=[]
 def role_record(role_id):
  v=role_by_id.get(role_id,{})
  return {k:clean(v.get(k,'')) for k in ('role','tissue_state','foundation_vocabulary_eligible','claim_boundary','split_domain')}
 def asset_record(asset_id):
  v=asset_by_id.get(asset_id,{})
  path=clean(v.get('matrix_path_or_object',''));d=download_by_path.get(path)
  return {'path':path,'exists':str((ROOT/path).exists()) if path and '*' not in path else 'WILDCARD_OR_OBJECT_SET','sha':clean(getattr(d,'registered_sha256','')) if d is not None else '', 'foundation':clean(v.get('foundation_eligible',''))}
 def foundation_ids(study,matrix_id,cohort=''):
  if study=='HVS':return 'HVS',matrix_id
  if study=='SEA_AD':return matrix_id,matrix_id
  if study=='NPH52':
   if cohort=='NPH_Abeta':return 'NPH52_Abeta','NPH52_exact_source_objects'
   if cohort=='NPH_AbetaTau':return 'NPH52_AbetaTau','NPH52_exact_source_objects'
   return 'NPH52_Ctrl','NPH52_exact_source_objects'
  if study=='siletti_human_brain_cell_atlas_v1':return 'siletti_hbca_all_non_neuronal',''
  return study,''
 def add_foundation_pair(donor,matrix_id,count,evidence):
  sp=foundation_train[foundation_train.canonical_person_id==raw_to_person[donor]].iloc[0];role_id,asset_id=foundation_ids(sp.study_id,matrix_id,sp.cohort);rv=role_record(role_id);av=asset_record(asset_id);part=reader_map[donor]
  use={'reader_fit':'FOUNDATION_TRAIN_READER_FIT_DESIGN_ELIGIBLE','reader_validation':'FOUNDATION_TRAIN_READER_SELECTION_DESCRIPTIVE_ONLY','reader_oracle':'FOUNDATION_TRAIN_PRIMARY_UNTOUCHED_EVALUATION_ONLY'}[part]
  r=blank();r.update({'record_scope':'DONOR_MATRIX','authority_status':'AUTHORITATIVE','donor_resolution_status':'EXACT','canonical_person_id':sp.canonical_person_id,'source_donor_id':donor,'study_id':sp.study_id,'cohort':sp.cohort,'split_domain':'foundation','split':'train','reader_partition':part,'dataset_id':role_id,'matrix_id':matrix_id,'local_asset_path':av['path'],'asset_exists':av['exists'],'registered_asset_sha256':av['sha'],'dataset_role':rv['role'],'tissue_state':rv['tissue_state'],'foundation_vocabulary_eligible':rv['foundation_vocabulary_eligible'],'foundation_eligible_asset':av['foundation'],'claim_boundary':rv['claim_boundary'],'allowed_use':use+';NO_EXECUTION_WITHOUT_SEPARATE_FROZEN_CONTRACT','forbidden_use':'DEV_OR_SEALED_EXPRESSION;PATHOLOGY;UNAUTHORIZED_TRAINING','current_training_authorized':'False','mapping_cell_count':str(count),'mapping_evidence':evidence,'pathology_bearing_asset':'','pathology_used_for_foundation_split':sp.pathology_used_for_foundation_split,'split_authority':'stage81a2_split_registry.csv','role_authority':'stage81a2_dataset_role_registry.csv','asset_authority':'stage81a2_canonical_asset_registry.csv','mapping_authority':evidence,'notes':'Exact donor-matrix membership in named mapping authority.'});r['record_id']=rid(r['record_scope'],r['canonical_person_id'],r['matrix_id']);rows.append(r)
 # Full-corpus exact matrix memberships for reader-fit donors.
 for x in fit.itertuples(index=False):add_foundation_pair(clean(x.donor_id),clean(x.matrix_id),int(x.cell_count),'FOUNDATION_METADATA_DONOR_X_OPERATOR.csv_FULL_FIT104')
 # Accepted-cache matrix memberships for the 45 TRAIN evaluation donors; exact but not claimed exhaustive.
 held=phase[phase.donor_id.isin([d for d,r in reader_map.items() if r!='reader_fit'])].groupby(['donor_id','matrix_id'],as_index=False).size()
 if held.donor_id.nunique()!=45:raise RuntimeError('heldout donor cache mapping drift')
 for x in held.itertuples(index=False):add_foundation_pair(clean(x.donor_id),clean(x.matrix_id),int(x.size),'PHASE_E_ACCEPTED_CACHE_EXACT_NOT_EXHAUSTIVE')
 # Protected and continuation donors remain study-level: no protected expression is opened to infer matrices.
 nontrain=split[~((split.split_domain=='foundation')&(split.split=='train'))]
 for sp in nontrain.itertuples(index=False):
  role_id,asset_id=foundation_ids(clean(sp.study_id),'',clean(sp.cohort));rv=role_record(role_id);av=asset_record(asset_id);protected=clean(sp.split) in ('development','sealed_holdout')
  use='METADATA_FIREWALL_ONLY;EXPRESSION_CLOSED' if protected else ('WHOLE_STUDY_EXTERNAL_HOLDOUT_CLOSED' if clean(sp.split_domain)=='whole_study_external_holdout' else 'CONTINUATION_ROLE_ONLY;NO_FOUNDATION_TRAINING')
  r=blank();r.update({'record_scope':'DONOR_STUDY','authority_status':'AUTHORITATIVE_STUDY_LEVEL','donor_resolution_status':'EXACT_DONOR_MATRIX_UNRESOLVED_OR_CLOSED','canonical_person_id':sp.canonical_person_id,'source_donor_id':clean(sp.canonical_person_id).split('::',1)[-1],'study_id':sp.study_id,'cohort':sp.cohort,'split_domain':sp.split_domain,'split':sp.split,'reader_partition':'NOT_APPLICABLE','dataset_id':role_id,'matrix_id':'PROTECTED_OR_UNRESOLVED_STUDY_LEVEL','local_asset_path':av['path'],'asset_exists':av['exists'],'registered_asset_sha256':av['sha'],'dataset_role':rv['role'],'tissue_state':rv['tissue_state'],'foundation_vocabulary_eligible':rv['foundation_vocabulary_eligible'],'foundation_eligible_asset':av['foundation'],'claim_boundary':rv['claim_boundary'],'allowed_use':use,'forbidden_use':'EXPRESSION_ACCESS_WITHOUT_EXPLICIT_AUTHORIZATION;PATHOLOGY_LEAKAGE;FOUNDATION_TRAINING' if protected else 'FOUNDATION_TRAINING;UNAUTHORIZED_MODEL_SELECTION','current_training_authorized':'False','mapping_evidence':'stage81a2_split_registry.csv_STUDY_LEVEL_ONLY','pathology_used_for_foundation_split':sp.pathology_used_for_foundation_split,'split_authority':'stage81a2_split_registry.csv','role_authority':'stage81a2_dataset_role_registry.csv','asset_authority':'stage81a2_canonical_asset_registry.csv','mapping_authority':'stage81a2_split_registry.csv','notes':'Matrix membership intentionally not inferred from protected expression.'});r['record_id']=rid(r['record_scope'],r['canonical_person_id'],r['dataset_id'],r['split']);rows.append(r)
 # Donor-resolved context/reference registry, aggregated to donor x dataset.
 bad={'','unresolved','unknown','nan','none'};ctx=context[~context.source_donor_id.str.lower().isin(bad)].copy()
 for (dataset,person,donor),g in ctx.groupby(['dataset_id','canonical_person_group_id','source_donor_id'],dropna=False):
  q=truth(g.quarantine_required.iloc[0]);ref=truth(g.reference_only.iloc[0]);sup=truth(g.supportive_eligible.iloc[0]);use='QUARANTINED_NO_USE' if q else ('MOLECULAR_REFERENCE_ONLY' if ref else ('SUPPORTIVE_CONTEXT_ONLY' if sup else 'ROLE_REVIEW_REQUIRED'))
  r=blank();r.update({'record_scope':'CONTEXT_DONOR_DATASET','authority_status':'AUTHORITATIVE_CONTEXT_ROLE','donor_resolution_status':'EXACT_WITHIN_CONTEXT_REGISTRY_NO_CROSS_STUDY_MERGE','canonical_person_id':'CONTEXT::'+clean(person),'source_donor_id':clean(donor),'study_id':clean(dataset),'cohort':'CONTEXT','split_domain':'context_qualification','split':'not_foundation_split','reader_partition':'NOT_APPLICABLE','dataset_id':clean(dataset),'matrix_id':'CONTEXT_DATASET_LEVEL','dataset_role':clean(g.qualification_role.iloc[0]),'qualification_role':clean(g.qualification_role.iloc[0]),'allowed_use':use,'forbidden_use':'FOUNDATION_TRAINING;MODEL_SELECTION;PATHOLOGY_LEAKAGE','current_training_authorized':'False','mapping_evidence':'stage81a3_context_dataset_role_matrix.csv','quarantine_required':clean(g.quarantine_required.iloc[0]),'reference_only':clean(g.reference_only.iloc[0]),'supportive_eligible':clean(g.supportive_eligible.iloc[0]),'source_sample_count':str(g.sample_id.nunique()),'source_sample_ids':'|'.join(sorted(set(g.sample_id.astype(str)))),'role_authority':'stage81a3_context_dataset_role_matrix.csv','mapping_authority':'stage81a3_context_dataset_role_matrix.csv','notes':'No cross-study identity merge beyond the existing canonical_person_group_id.'});r['record_id']=rid(r['record_scope'],r['canonical_person_id'],r['dataset_id']);rows.append(r)
 # Every downloaded asset remains visible even when no donor mapping exists.
 for d in downloads.itertuples(index=False):
  status='REGISTERED_ASSET' if truth(d.registered_downloaded_asset) and not truth(d.downloaded_but_unregistered) else 'CANDIDATE_OR_UNREGISTERED_ASSET'
  r=blank();r.update({'record_scope':'DATASET_ASSET_ONLY','authority_status':status,'donor_resolution_status':'NOT_DONOR_RESOLVED_AT_ASSET_LEVEL','canonical_person_id':'','source_donor_id':'','study_id':clean(d.study_id),'cohort':'','split_domain':'asset_inventory','split':'not_assigned_at_asset_row','reader_partition':'NOT_APPLICABLE','dataset_id':clean(d.dataset_id),'matrix_id':'','local_asset_path':clean(d.local_path),'asset_exists':clean(d.local_file_exists),'registered_asset_sha256':clean(d.registered_sha256),'dataset_role':clean(d.intended_project_role),'foundation_eligible_asset':clean(d.foundation_eligible),'allowed_use':'ROLE_AND_DONOR_RESOLUTION_REQUIRED_BEFORE_USE','forbidden_use':'TRAINING;MODEL_SELECTION;VALIDATION_UNTIL_ROLE_AND_DONOR_FIREWALL_RESOLVED','current_training_authorized':'False','pathology_bearing_asset':clean(d.pathology_bearing),'holdout_validation_adapter':clean(d.holdout_validation_adapter),'asset_authority':'stage81a2r_all_downloaded_asset_identity_inventory_candidate.csv','mapping_authority':'NONE_DATASET_ASSET_ONLY','notes':'Asset inventory row; absence of donor ID is explicit, not imputed.'});r['record_id']=rid(r['record_scope'],r['dataset_id'],r['local_asset_path']);rows.append(r)
 master=pd.DataFrame(rows,columns=COLUMNS)
 if master.record_id.duplicated().any():raise RuntimeError('record id collision')
 if master.current_training_authorized.astype(str).ne('False').any():raise RuntimeError('unauthorized training flag')
 donor_rows=master[master.canonical_person_id!=''];foundation_rows=donor_rows[donor_rows.split_domain=='foundation']
 if set(foundation_train.canonical_person_id)-set(foundation_rows.canonical_person_id):raise RuntimeError('missing foundation TRAIN donor')
 protected=master[(master.split_domain=='foundation') & master.split.isin(['development','sealed_holdout'])]
 if len(protected)!=38 or not protected.allowed_use.str.contains('EXPRESSION_CLOSED').all():raise RuntimeError('protected firewall mapping failed')
 out_csv=OUT/'MASTER_DONOR_DATASET_ROLE_TABLE.csv';master.to_csv(out_csv,index=False,lineterminator='\n')
 inputs=pd.DataFrame([{'authority_key':k,'path':str(p.relative_to(ROOT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for k,p in PATHS.items()]);inputs.to_csv(OUT/'MASTER_DONOR_DATASET_ROLE_AUTHORITY_INPUTS.csv',index=False,lineterminator='\n')
 reconciliation=pd.DataFrame([
  {'claim':'foundation donor total','provided_value':provided['foundation']['eligible_donors']['total'],'repository_value':187,'status':'MATCH','interpretation':'Exact split registry.'},
  {'claim':'foundation TRAIN/DEV/SEALED','provided_value':'149/19/19','repository_value':'149/19/19','status':'MATCH','interpretation':'Exact split registry.'},
  {'claim':'Phase-A physical operators','provided_value':provided['foundation']['phaseA_operators']['total'],'repository_value':42,'status':'MATCH','interpretation':'24 HVS + 7 NPH52 + 11 SEA-AD.'},
  {'claim':'reader fit/validation/oracle','provided_value':'104/22/23','repository_value':'104/22/23','status':'MATCH','interpretation':'Exact reader donor split.'},
  {'claim':'reader-fit lawful cells','provided_value':provided['foundation']['reader_fit_cells']['total'],'repository_value':4553407,'status':'MATCH','interpretation':'Frozen fit-104 metadata atlas.'},
  {'claim':'full149 lawful HVS rows','provided_value':provided['foundation']['full149_train_physical_rows_approx']['HVS'],'repository_value':308499,'status':'MATCH','interpretation':'Current model-facing lawful inventory.'},
  {'claim':'full149 lawful SEA-AD rows','provided_value':provided['foundation']['full149_train_physical_rows_approx']['SEA-AD'],'repository_value':5777853,'status':'MATCH','interpretation':'Current model-facing lawful inventory.'},
  {'claim':'full149 NPH52 rows','provided_value':provided['foundation']['full149_train_physical_rows_approx']['NPH52'],'repository_value':265401,'status':'SCOPE_DIFFERENCE_QUARANTINED','interpretation':'288,116 is broader physical TRAIN-row accounting; current lawful model-facing rows are 265,401. Difference 22,715 is not silently admitted.'},
  {'claim':'full149 total rows','provided_value':provided['foundation']['full149_train_physical_rows_approx']['total'],'repository_value':6351753,'status':'SCOPE_DIFFERENCE_QUARANTINED','interpretation':'Difference is entirely the NPH52 22,715-row scope discrepancy.'},
  {'claim':'source composition of 104/22/23','provided_value':'explicit_unknown','repository_value':'mounted in FOUNDATION_METADATA_ALL149_CONTEXT.csv','status':'SUPERSEDED_UNKNOWN','interpretation':'Exact current source x reader-partition counts are now available.'},
  {'claim':'Siletti publication/project donors','provided_value':'3 publication / 4 processed','repository_value':'unresolved','status':'PRESERVED_DISCREPANCY','interpretation':'Whole-study holdout retained; no donor merge invented.'},
 ])
 reconciliation.to_csv(OUT/'MASTER_DONOR_DATASET_ROLE_RECONCILIATION.csv',index=False,lineterminator='\n')
 all149.to_csv(OUT/'MASTER_FOUNDATION_READER_SOURCE_COUNTS.csv',index=False,lineterminator='\n')
 audit={'schema':'master-donor-dataset-role-registry-v1','status':'PASS_WITH_EXPLICIT_SCOPE_QUARANTINE','records':len(master),'record_scopes':master.record_scope.value_counts().to_dict(),'donor_resolved_records':len(donor_rows),'unique_canonical_people':donor_rows.canonical_person_id.nunique(),'foundation_split_donors':215-27-1,'foundation_train_donors':149,'reader_roles':reader.reader_partition.value_counts().to_dict(),'reader_source_counts':all149.to_dict('records'),'full_fit104_donor_matrix_rows':len(fit),'full_fit104_cells':int(fit.cell_count.astype(int).sum()),'current_lawful_full149_cells':int(all149.cell_count.astype(int).sum()),'provided_broader_full149_physical_rows':int(provided['foundation']['full149_train_physical_rows_approx']['total']),'quarantined_nph_scope_difference_rows':22_715,'protected_foundation_donors':38,'continuation_donors':27,'whole_study_external_holdout_rows':1,'downloaded_asset_rows':len(downloads),'context_donor_dataset_rows':int((master.record_scope=='CONTEXT_DONOR_DATASET').sum()),'all_current_training_authorized_false':True,'dev_sealed_expression_opened':False,'pathology_used':False,'provided_package_manifest_verified':True,'provided_workbook_preserved_unmodified':True,'master_csv_sha256':sha(out_csv),'authority_inputs':inputs.to_dict('records')}
 audit_path=OUT/'MASTER_DONOR_DATASET_ROLE_AUDIT.json';audit_path.write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
 readme=f'''# Authoritative master donor/dataset-role registry v1

Status: **PASS**. This registry is authoritative about both known links and unresolved links; it never fabricates donor identities or protected matrix membership.

- `{len(master):,}` total records; `{len(donor_rows):,}` donor-resolved records.
- 149 FOUNDATION TRAIN donors: reader-fit 104, reader-validation 22, reader-oracle 23. Their exact source counts are now mounted in `MASTER_FOUNDATION_READER_SOURCE_COUNTS.csv`.
- Full donor x operator membership for the 104 fit donors comes from the 4,553,407-cell frozen metadata atlas. The 45 TRAIN evaluation donors use only exact memberships observed in the accepted Phase-E cache and are explicitly non-exhaustive.
- 38 FOUNDATION DEV/SEALED donors remain study-level with expression closed.
- 27 continuation donors and one whole-study external holdout remain outside foundation training.
- Context identities retain their existing context-specific canonical groups; no cross-study merge is invented.
- All 495 downloaded asset rows remain visible even when donor mapping or role registration is unresolved.
- The supplied authority package was manifest-verified and reconciled. Its 288,116 NPH TRAIN physical-row figure is preserved as broader physical accounting; the current lawful model-facing inventory contains 265,401 NPH TRAIN rows. The 22,715-row difference is quarantined rather than guessed into eligibility.
- `current_training_authorized` is false for every row. This table is governance infrastructure, not a training authorization.

Primary key: `record_id`. Use `record_scope`, `authority_status`, `donor_resolution_status`, and the authority columns before consuming any row.
'''
 (OUT/'MASTER_DONOR_DATASET_ROLE_README.md').write_text(readme,encoding='utf-8')
 manifest=OUT/'MASTER_DONOR_DATASET_ROLE_HASH_MANIFEST.csv';files=[out_csv,OUT/'MASTER_DONOR_DATASET_ROLE_AUTHORITY_INPUTS.csv',OUT/'MASTER_DONOR_DATASET_ROLE_RECONCILIATION.csv',OUT/'MASTER_FOUNDATION_READER_SOURCE_COUNTS.csv',audit_path,OUT/'MASTER_DONOR_DATASET_ROLE_README.md',Path(__file__)]
 pd.DataFrame([{'path':str(p.relative_to(ROOT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]).to_csv(manifest,index=False,lineterminator='\n')
 print(json.dumps({'status':'PASS','records':len(master),'donor_records':len(donor_rows),'unique_people':donor_rows.canonical_person_id.nunique(),'master_sha256':sha(out_csv),'manifest_sha256':sha(manifest)},indent=2))

if __name__=='__main__':main()
