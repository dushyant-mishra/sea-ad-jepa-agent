"""Independent fail-closed verifier for exported FULL104 metadata-only receipt.

Checks independent spreadsheet arithmetic, sorted identities, cross-file joins,
shas, source/support consistency, and impossible authority promotions. This does
not replace source-byte authentication performed by the producer.
"""
import csv,hashlib,json
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path

OUTPUTS=('fit104_donor_scientific_masses.csv','fit104_operator_token_support.csv','fit104_donor_operator_relational_capacity.csv','FULL104_AUTHENTICATED_READER_FIT_METADATA_PARAMETER_RECEIPT_V1.json')


def file_sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()


def rows(path):
 with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))


def verify(root):
 root=Path(root)
 manifest=json.loads((root/'OUTPUT_SHA256_MANIFEST.json').read_text())
 mapped={x['file']:x for x in manifest}
 if set(mapped)!=set(OUTPUTS):raise ValueError('STOP output manifest has missing or unknown exports')
 for name in OUTPUTS:
  meta=mapped[name];p=root/name
  if p.stat().st_size!=meta['bytes'] or file_sha(p)!=meta['sha256']:
   raise ValueError(f'STOP output byte identity tampered: {name}')
 receipt=json.loads((root/OUTPUTS[3]).read_text())
 expected_top={'schema','status','training_authorized','protected_expression_or_outcomes_opened','d_shared_evaluated','masking_policy_selected','source_roots','census','support','candidate_bound_not_execution_schedule','deferred_parameters','limitations','D1_P002_metadata_ready'}
 if set(receipt)!=expected_top:raise ValueError('STOP unknown/missing authority-bearing receipt fields')
 expected_roots={
  'calibration_zip_sha256':'07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444',
  'sqlite_member_sha256':'a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913',
  'metadata/FOUNDATION_METADATA_DONOR.csv_sha256':'c9cbe47d4727aabec8a0c3fed5474c2dab4f9f2b8848357e08b0cec6ef044508',
  'splits/reader_donor_split.csv_sha256':'efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511',
  'splits/foundation_split_registry.csv_sha256':'35afb7f53fa36d580a4552dd5ad7e59841e454ea85d4adcb761666cb20d05433',
  'support/FOUNDATION_SUPPORT_BY_OPERATOR.csv_sha256':'1814a22c8ae01ee94a6fe132546a029af01a7d762384d53c152f37cb545787c1',
  'support/FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv_sha256':'8f90c91e333eba6b58c39767069addef72bb4d9d6015ad8de14e7ff383c092da',
 }
 if receipt.get('source_roots')!=expected_roots:raise ValueError('STOP source provenance root substitution or unexpected member')
 if receipt.get('schema')!='FULL104_AUTHENTICATED_READER_FIT_METADATA_PARAMETER_RECEIPT_V1':raise ValueError('STOP receipt schema')
 for k in ('training_authorized','protected_expression_or_outcomes_opened','d_shared_evaluated','masking_policy_selected'):
  if receipt.get(k) is not False:raise ValueError(f'STOP scope promotion {k}')
 if receipt.get('status')!='PHYSICALLY_REDERIVED_FROM_AUTHENTIC_CALIBRATION_AND_SQLITE__METADATA_ONLY':raise ValueError('STOP scope missing')
 if receipt.get('source_roots',{}).get('calibration_zip_sha256')!='07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444':raise ValueError('STOP wrong bundle provenance')
 if receipt['source_roots'].get('sqlite_member_sha256')!='a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913':raise ValueError('STOP wrong sqlite provenance')
 if set(receipt['deferred_parameters'])!={'D_shared','D_private','D_obs','mask_fraction','ema_half_life_presentations','learning_rate','model_width','microbatch_token_budget','masked_views_per_cell'}:raise ValueError('STOP missing unresolved scientific parameter')
 if not all(isinstance(v,str) for v in receipt['deferred_parameters'].values()):raise ValueError('STOP numerical parameter contamination')
 donors=rows(root/OUTPUTS[0]);operators=rows(root/OUTPUTS[1]);groups=rows(root/OUTPUTS[2]);c=receipt['census'];support=receipt['support'];
 if (len(donors),len(operators),len(groups))!=(104,42,1400):raise ValueError('STOP row count')
 donor_ids=[r['donor_id'] for r in donors]
 if donor_ids!=sorted(set(donor_ids)):raise ValueError('STOP donor roster duplicate or order invalid')
 source_donors=Counter(r['source'] for r in donors)
 source_cells=Counter(); donor_sum=0; min_d=10**30
 group_by_donor=Counter();group_by_operator=Counter(); group_source=Counter();source_group_ge3=Counter();
 seen_groups=set();cells_ge3=0
 for r in donors:
  n=int(r['fit_cells']); min_d=min(min_d,n)
  if n<=0 or (int(r['donor_scientific_mass_numerator']),int(r['donor_scientific_mass_denominator']))!=(1,104):raise ValueError('STOP invalid donor mass')
  if (int(r['cell_scientific_mass_numerator']),int(r['cell_scientific_mass_denominator']))!=(1,104*n):raise ValueError('STOP wrong cell scientific mass')
  if abs(float(r['cell_scientific_mass_decimal'])-float(Fraction(1,104*n)))>2e-18:raise ValueError('STOP rounded cell scientific weight incorrectly')
  donor_sum+=n;source_cells[r['source']]+=n
 if sum(Fraction(1,int(r['cell_scientific_mass_denominator']))*int(r['fit_cells']) for r in donors)!=1:raise ValueError('STOP per-cell scientific weights do not sum to one')
 src_by_d={r['donor_id']:r['source'] for r in donors};op_by_id={int(r['operator_index']):r for r in operators}
 if set(op_by_id)!=set(range(42)):raise ValueError('STOP operator identity')
 for op,r in op_by_id.items():
  if sum(int(r[k]) for k in ('measured_scalar_addresses','structurally_unmeasured_addresses','collision_unresolved_addresses'))!=41238:raise ValueError('STOP support state collapse')
 for r in groups:
  d=r['donor_id'];s=r['source'];op=int(r['operator_index']);n=int(r['cells']);key=(d,op)
  if key in seen_groups or d not in src_by_d or s!=src_by_d[d] or op not in op_by_id or op_by_id[op]['source']!=s or n<1:raise ValueError('STOP group donor/source/operator spillover')
  seen_groups.add(key)
  cap=n*(n-1)*(n-2)//2 if n>=3 else 0
  if int(r['triplet_capacity'])!=cap or r['estimable_triplets']!=str(n>=3):raise ValueError('STOP relational capacity')
  nops=int(next(x['operator_count'] for x in donors if x['donor_id']==d))
  if (int(r['D1_P002_donor_operator_group_mass_numerator']),int(r['D1_P002_donor_operator_group_mass_denominator']))!=(1,104*nops) or (int(r['D1_P002_cell_mass_numerator']),int(r['D1_P002_cell_mass_denominator']))!=(1,104*nops*n):raise ValueError('STOP D1 donor/operator group mass')
  group_by_donor[d]+=n;group_by_operator[op]+=n;group_source[s]+=1
  if n>=3:cells_ge3+=n;source_group_ge3[s]+=1
 if {d:int(x['fit_cells']) for d,x in [(r['donor_id'],r) for r in donors]}!=dict(group_by_donor):raise ValueError('STOP group donor census')
 if {op:int(row['fit_cells']) for op,row in op_by_id.items()}!=dict(group_by_operator):raise ValueError('STOP group operator census')
 if {d:int(r['operator_count']) for d,r in [(x['donor_id'],x) for x in donors]}!={d:len({int(x['operator_index']) for x in groups if x['donor_id']==d}) for d in donor_ids}:raise ValueError('STOP donor operator membership')
 if sum(Fraction(int(r['D1_P002_donor_operator_group_mass_numerator']),int(r['D1_P002_donor_operator_group_mass_denominator'])) for r in groups)!=1:raise ValueError('STOP D1 group masses do not sum to 1')
 if sum(Fraction(int(r['D1_P002_cell_mass_numerator']),int(r['D1_P002_cell_mass_denominator']))*int(r['cells']) for r in groups)!=1:raise ValueError('STOP D1 cell weights do not sum to 1')
 if receipt['D1_P002_metadata_ready']['qualification']!='METADATA_DERIVED_ONLY__NO_TEACHER_STATES_OR_D1_RANK':raise ValueError('STOP D1 scope promotion')
 if dict(source_donors)!=c['source_donor_counts'] or dict(source_cells)!=c['source_cell_counts']:raise ValueError('STOP source mass')
 if c['fit_cells']!=donor_sum or c['fit_donors']!=104 or c['operators']!=42 or c['smallest_donor_cells']!=min_d or c['largest_donor_cells']!=max(int(r['fit_cells']) for r in donors):raise ValueError('STOP population census')
 if c['donor_operator_groups']!=len(groups) or c['group_count_ge3']!=sum(int(x['cells'])>=3 for x in groups) or c['cells_in_ge3_groups']!=cells_ge3:raise ValueError('STOP group census')
 if dict(group_source)!=c['source_group_count'] or dict(source_group_ge3)!=c['source_group_count_ge3']:raise ValueError('STOP source group census')
 if support['total_addresses']!=41238 or support['strict_all42_operator_measured']!=17186 or support['any_operator_in_each_source_measured']!=17346 or support['not_measured_by_any_operator']!=289:raise ValueError('STOP support recurrence')
 if receipt['candidate_bound_not_execution_schedule']['unique_cells_per_donor_draw_without_replacement_limit']!=min_d:raise ValueError('STOP wrong unique-donor capacity')
 if sum(int(x) for x in c['source_donor_counts'].values())!=104 or sum(int(x) for x in c['source_cell_counts'].values())!=4553407:raise ValueError('STOP source denominator')
 return {'status':'PASS_INDEPENDENT_OUTPUT_VERIFIER','donors':104,'cells':donor_sum,'operators':42,'groups':len(groups),'groups_ge3':c['group_count_ge3'],'source_donors':dict(sorted(source_donors.items())),'source_cells':dict(sorted(source_cells.items())),'strict_common':17186,'source_three_any':17346}

if __name__=='__main__':
 import sys
 print(json.dumps(verify(Path(sys.argv[1])),sort_keys=True))
