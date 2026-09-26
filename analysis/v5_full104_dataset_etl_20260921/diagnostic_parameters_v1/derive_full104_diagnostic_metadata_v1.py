#!/usr/bin/env python3
"""Physically authenticated FULL104 metadata-only derivation; no expression/outcomes/training.

Requires exact local August 24 bundle and extracted, rehashed SQLite member.
Does not open D_shared, expression, validation/oracle outcomes, pathology, or N1.
Outputs population- and support-bound *facts*, not a V5 execution authorization.
"""
import csv,hashlib,io,json,sqlite3,sys,zipfile
from collections import Counter,defaultdict
from pathlib import Path
from fractions import Fraction
from datetime import date

EXPECTED_BUNDLE='07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444'
EXPECTED_SQLITE='a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913'
EXPECTED_SUPPORT_OPERATOR='1814a22c8ae01ee94a6fe132546a029af01a7d762384d53c152f37cb545787c1'
EXPECTED_FIT_DONORS=104
EXPECTED_FIT_CELLS=4553407
EXPECTED_OPERATORS=42
EXPECTED_NAMESPACE=41238


def digest_file(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for block in iter(lambda:f.read(8<<20),b''):h.update(block)
 return h.hexdigest()


def _table(z,mapping,key,expected=None):
 data=z.read(mapping[key]);sha=hashlib.sha256(data).hexdigest()
 if expected is not None and sha!=expected:raise ValueError(f'STOP member digest mismatch {key}: {sha}')
 return list(csv.DictReader(io.StringIO(data.decode('utf-8')))),sha


def derive(bundle,sqlite_path,out_dir):
 out_dir.mkdir(parents=True,exist_ok=True)
 if digest_file(bundle)!=EXPECTED_BUNDLE:raise ValueError('STOP wrong full calibration bundle hash')
 with zipfile.ZipFile(bundle) as z:
  names={name.rsplit('/foundation_calibration_bundle_20260824/',1)[-1]:name for name in z.namelist() if '/foundation_calibration_bundle_20260824/' in name}
  manifest,_=_table(z,names,'BUNDLE_SHA256_MANIFEST.csv')
  listing={x['path']:(int(x['bytes']),x['sha256']) for x in manifest}
  keys=['metadata/foundation_metadata_rows.sqlite','metadata/FOUNDATION_METADATA_DONOR.csv','splits/reader_donor_split.csv','splits/foundation_split_registry.csv','support/FOUNDATION_SUPPORT_BY_OPERATOR.csv','support/FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv']
  if any(k not in listing or k not in names for k in keys):raise ValueError('STOP missing authoritative bundle member')
  donor,donor_sha=_table(z,names,'metadata/FOUNDATION_METADATA_DONOR.csv')
  reader,reader_sha=_table(z,names,'splits/reader_donor_split.csv')
  foundation,foundation_sha=_table(z,names,'splits/foundation_split_registry.csv')
  ops,ops_sha=_table(z,names,'support/FOUNDATION_SUPPORT_BY_OPERATOR.csv',EXPECTED_SUPPORT_OPERATOR)
  recurrence,recurrence_sha=_table(z,names,'support/FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv')
  checks={'metadata/FOUNDATION_METADATA_DONOR.csv':donor_sha,'splits/reader_donor_split.csv':reader_sha,'splits/foundation_split_registry.csv':foundation_sha,'support/FOUNDATION_SUPPORT_BY_OPERATOR.csv':ops_sha,'support/FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv':recurrence_sha,'metadata/foundation_metadata_rows.sqlite':EXPECTED_SQLITE}
  for key,hash_ in checks.items():
   if listing[key][1]!=hash_:raise ValueError(f'STOP internal manifest disagreement {key}')
   if z.getinfo(names[key]).file_size!=listing[key][0]:raise ValueError(f'STOP member length disagreement {key}')
  if digest_file(sqlite_path)!=EXPECTED_SQLITE:raise ValueError('STOP physically extracted SQLITE hash mismatch')
  if len({r['donor_id'] for r in reader})!=149 or len(reader)!=149:raise ValueError('STOP reader partition roster duplicate/incomplete')
  fit_ids={r['donor_id'] for r in reader if r['reader_partition']=='reader_fit'}
  val_ids={r['donor_id'] for r in reader if r['reader_partition']=='reader_validation'}
  oracle_ids={r['donor_id'] for r in reader if r['reader_partition']=='reader_oracle'}
  if [len(s) for s in (fit_ids,val_ids,oracle_ids)]!=[104,22,23] or len(fit_ids|val_ids|oracle_ids)!=149:raise ValueError('STOP reader split count/overlap')
  registry={}
  for row in foundation:
   if row['study_id']=='siletti_human_brain_cell_atlas_v1':continue
   if row['canonical_person_id']!=f"{row['study_id']}::{row['canonical_person_id'].split('::',1)[-1]}":raise ValueError('STOP foundation canonical ID')
   key=row['canonical_person_id'].split('::',1)[-1]
   if key in registry:raise ValueError('STOP cross-source donor ID alias')
   registry[key]=row
  if not fit_ids<=registry.keys() or any(registry[d]['split']!='train' for d in fit_ids):raise ValueError('STOP source registry fit-versus-heldout mismatch')
  counts={r['donor_id']:int(r['cell_count']) for r in donor}
  if set(counts)!=fit_ids or len(donor)!=104 or any(n<1 for n in counts.values()) or sum(counts.values())!=EXPECTED_FIT_CELLS:raise ValueError('STOP per-donor census mismatch')
  if len(ops)!=42 or set(int(r['operator_index']) for r in ops)!=set(range(42)):raise ValueError('STOP operator roster mismatch')
  op_by_id={int(r['operator_index']):r for r in ops}
  assert sum(int(r['fit104_cells']) for r in ops)==EXPECTED_FIT_CELLS
  for row in ops:
   if sum(int(row[k]) for k in ('measured_scalar_addresses','structurally_unmeasured_addresses','collision_unresolved_addresses'))!=EXPECTED_NAMESPACE:raise ValueError('STOP support state partition incomplete')
  if len(recurrence)!=EXPECTED_NAMESPACE:raise ValueError('STOP address recurrence size mismatch')
  strict=sum(int(x['operators_measured_scalar'])==42 for x in recurrence)
  any3=sum(int(x['source_families_measuring'])==3 for x in recurrence)
  neither=sum(int(x['operators_measured_scalar'])==0 for x in recurrence)
  if (strict,any3,neither)!=(17186,17346,289):raise ValueError('STOP exact support counts differ from frozen physical ETL')
  conn=sqlite3.connect(f'file:{sqlite_path}?mode=ro',uri=True)
  try:
   # Read-only integrity/authority: confirm SQLite contains the SAME 149 donor roster
   # but never extract/inspect non-fit expression or outcomes.
   conn.execute('PRAGMA query_only=ON')
   sizes=conn.execute("SELECT partition,source,COUNT(*),COUNT(DISTINCT donor_id) FROM cells GROUP BY partition,source ORDER BY partition,source").fetchall()
   fit_groups=conn.execute("SELECT donor_id,source,operator_index,COUNT(*) FROM cells WHERE partition='reader_fit' GROUP BY donor_id,source,operator_index ORDER BY donor_id,operator_index").fetchall()
  finally:conn.close()
  partition_counts={(p,s):(int(c),int(d)) for p,s,c,d in sizes}
  if sum(c for (p,s),(c,d) in partition_counts.items() if p=='reader_fit')!=EXPECTED_FIT_CELLS:raise ValueError('STOP fit partition SQLite sum mismatch')
  if sum(d for (p,s),(c,d) in partition_counts.items() if p=='reader_fit')!=EXPECTED_FIT_DONORS:raise ValueError('STOP fit donor SQLite sum mismatch')
  check_counts=Counter();check_ops=Counter();group_by_source=Counter();stats=defaultdict(list)
  per_donor_ops=defaultdict(set)
  for d,s,op,n in fit_groups:
   op=int(op);n=int(n)
   if d not in fit_ids or registry[d]['study_id']!=s or s!=op_by_id[op]['source'] or n<1:raise ValueError('STOP fit source/donor/operator join')
   check_counts[d]+=n;check_ops[op]+=n;group_by_source[s]+=1;stats[s].append(n);per_donor_ops[d].add(op)
  if check_counts!=Counter(counts):raise ValueError('STOP authentic SQLite donor count mismatch')
  if check_ops!=Counter({int(r['operator_index']):int(r['fit104_cells']) for r in ops}):raise ValueError('STOP SQLite operator/support census mismatch')
  if len(fit_groups)!=1400 or sum(n>=3 for *_,n in fit_groups)!=1361:raise ValueError('STOP relational capacity count mismatch')
  source_n=Counter(registry[d]['study_id'] for d in fit_ids)
  expected_source={'HVS':41,'NPH52':17,'SEA_AD':46}
  if dict(source_n)!=expected_source:raise ValueError('STOP source donor roster mismatch')
  source_cells=Counter();source_groups_ge3=Counter();cells_in_ge3=0
  group_rows=[]
  for d,s,op,n in fit_groups:
   n=int(n);source_cells[s]+=n
   if n>=3:source_groups_ge3[s]+=1;cells_in_ge3+=n
   group_rows.append({'donor_id':d,'source':s,'operator_index':int(op),'cells':n,'triplet_capacity':n*(n-1)*(n-2)//2 if n>=3 else 0,'estimable_triplets':n>=3,'D1_P002_donor_operator_group_mass_numerator':1,'D1_P002_donor_operator_group_mass_denominator':104*len(per_donor_ops[d]),'D1_P002_cell_mass_numerator':1,'D1_P002_cell_mass_denominator':104*len(per_donor_ops[d])*n})
  if dict(source_cells)!={'HVS':198718,'NPH52':236476,'SEA_AD':4118213}:raise ValueError('STOP source cell mass mismatch')
  per_donor=[]
  for d in sorted(fit_ids):
   n=counts[d];s=registry[d]['study_id']
   per_donor.append({'donor_id':d,'source':s,'fit_cells':n,'donor_scientific_mass_numerator':1,'donor_scientific_mass_denominator':104,'cell_scientific_mass_numerator':1,'cell_scientific_mass_denominator':104*n,'cell_scientific_mass_decimal':format(1/(104*n),'.17g'),'operator_count':len(per_donor_ops[d])})
  per_op=[]
  for op in sorted(op_by_id):
   row=op_by_id[op]
   per_op.append({'operator_index':op,'matrix_id':row['matrix_id'],'source':row['source'],'fit_cells':int(row['fit104_cells']),'measured_scalar_addresses':int(row['measured_scalar_addresses']),'structurally_unmeasured_addresses':int(row['structurally_unmeasured_addresses']),'collision_unresolved_addresses':int(row['collision_unresolved_addresses'])})
  receipt={
   'schema':'FULL104_AUTHENTICATED_READER_FIT_METADATA_PARAMETER_RECEIPT_V1',
   'status':'PHYSICALLY_REDERIVED_FROM_AUTHENTIC_CALIBRATION_AND_SQLITE__METADATA_ONLY',
   'training_authorized':False,'protected_expression_or_outcomes_opened':False,'d_shared_evaluated':False,'masking_policy_selected':False,
   'source_roots':{'calibration_zip_sha256':EXPECTED_BUNDLE,'sqlite_member_sha256':EXPECTED_SQLITE,**{k+'_sha256':v for k,v in checks.items() if k!='metadata/foundation_metadata_rows.sqlite'}},
   'census':{'fit_donors':104,'fit_cells':4553407,'operators':42,'donor_operator_groups':len(fit_groups),'group_count_ge3':sum(n>=3 for *_,n in fit_groups),'cells_in_ge3_groups':cells_in_ge3,'smallest_donor_cells':min(counts.values()),'largest_donor_cells':max(counts.values()),'source_donor_counts':dict(sorted(source_n.items())),'source_cell_counts':dict(sorted(source_cells.items())),'donor_scientific_source_mass':{s:f'{n}/104' for s,n in sorted(source_n.items())},'cell_uniform_source_mass':{s:f'{n}/4553407' for s,n in sorted(source_cells.items())},'validation_source_donors_metadata_only':{s:d for (p,s),(c,d) in sorted(partition_counts.items()) if p=='reader_validation'},'oracle_source_donors_metadata_only':{s:d for (p,s),(c,d) in sorted(partition_counts.items()) if p=='reader_oracle'},'source_group_count':dict(sorted(group_by_source.items())),'source_group_count_ge3':dict(sorted(source_groups_ge3.items()))},
   'support':{'total_addresses':41238,'strict_all42_operator_measured':strict,'any_operator_in_each_source_measured':any3,'not_measured_by_any_operator':neither,'operator_rows':42,'source_operator_measured_address_ranges':{s:[min(x['measured_scalar_addresses'] for x in per_op if x['source']==s),max(x['measured_scalar_addresses'] for x in per_op if x['source']==s)] for s in sorted(source_n)}},
   'D1_P002_metadata_ready':{'group_cell_weight_law':'1 / (104 * number_of_operators_for_donor * cells_in_that_donor_operator_group)','qualification':'METADATA_DERIVED_ONLY__NO_TEACHER_STATES_OR_D1_RANK','not_equal_to_base_JEPA_p':'base JEPA is 1/(104*donor_cells) and does not equalize operator groups'},
   'candidate_bound_not_execution_schedule':{'unique_cells_per_donor_draw_without_replacement_limit':min(counts.values()),'proposal':'DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1','conditional_on':'exact currently proposed PR135/139 within-update no-replacement donor sample law, not a full-training run authorization'},
   'deferred_parameters':{'D_shared':'SEALED_NOT_DERIVABLE_FROM_METADATA','D_private':'UNRESOLVED','D_obs':'UNRESOLVED','mask_fraction':'NOT_DERIVED_FROM_HISTORICAL_40_PCT','ema_half_life_presentations':'REQUIRES_PROSPECTIVE_SCHEDULE','learning_rate':'REQUIRES_SEPARATE_TRAINING_DESIGN','model_width':'PROVISIONAL_GPU_RESOURCE_CHOICE_NOT_BIOLOGICAL_DIMENSION','microbatch_token_budget':'REQUIRES_VERIFIED_GPU_RESOURCE_BUDGET','masked_views_per_cell':'REQUIRES_PROSPECTIVE_TARGET_AND_MASK_CONTRACT'},
   'limitations':['Source registry and SQL metadata authenticate source/identity/size, not protected biological outcomes','No full Level4 raw-count reaggregation, expression target, physical training proof or D_shared result','Source/native support patterns can identify source; operator has distinct class/region semantics','Any per-donor CSV must not be replaced by historical 94-donor sample or synthetic test fixture']
  }
  def csv_write(name, rows):
   with (out_dir/name).open('w',newline='',encoding='utf-8') as f:
    wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
  csv_write('fit104_donor_scientific_masses.csv',per_donor)
  csv_write('fit104_operator_token_support.csv',per_op)
  csv_write('fit104_donor_operator_relational_capacity.csv',group_rows)
  jpath=out_dir/'FULL104_AUTHENTICATED_READER_FIT_METADATA_PARAMETER_RECEIPT_V1.json'
  jpath.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
  m=[]
  for p in sorted(out_dir.iterdir()):
   if p.is_file() and p.name in {'fit104_donor_scientific_masses.csv', 'fit104_operator_token_support.csv', 'fit104_donor_operator_relational_capacity.csv', 'FULL104_AUTHENTICATED_READER_FIT_METADATA_PARAMETER_RECEIPT_V1.json'}:
    m.append({'file':p.name,'bytes':p.stat().st_size,'sha256':digest_file(p)})
  (out_dir/'OUTPUT_SHA256_MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
  print('PASS_METADATA_ONLY',json.dumps({'receipt_sha256':digest_file(jpath),'census':receipt['census'],'support':receipt['support']},sort_keys=True),flush=True)
  return receipt

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('USAGE: script BUNDLE.zip extracted.sqlite OUT_DIR')
 derive(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))
