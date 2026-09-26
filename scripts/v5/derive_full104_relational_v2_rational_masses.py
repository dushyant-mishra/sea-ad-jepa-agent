#!/usr/bin/env python3
"""Derived scientific-relational V2 group masses; not training authorization."""
import argparse,csv,collections,hashlib,math,json,pathlib
from fractions import Fraction
ap=argparse.ArgumentParser(description='Reproduce full104 relational V2 rational masses ONLY from exact PR146 CSV roots')
ap.add_argument('--input-dir',required=True,type=pathlib.Path)
ap.add_argument('--out-dir',required=True,type=pathlib.Path)
args=ap.parse_args()
IN=args.input_dir
OUT=args.out_dir
if OUT.exists() and any(OUT.iterdir()):raise SystemExit('STOP_OUTPUT_DIRECTORY_NOT_EMPTY')
OUT.mkdir(parents=True,exist_ok=True)
EXPECTED={'fit104_donor_scientific_masses.csv':'386e52ecb56031fba7bde855c7af314b08f1773427d367e0679e6de47f79c7b7','fit104_donor_operator_relational_capacity.csv':'e40acc06844f4a13cb956453fe54e74abed357c3777a80ec6c4a2778dcae8f65'}
for f,s in EXPECTED.items():
 h=hashlib.sha256((IN/f).read_bytes()).hexdigest();assert h==s,(f,h)
with (IN/'fit104_donor_scientific_masses.csv').open(newline='') as f:donors={r['donor_id']:r for r in csv.DictReader(f)}
with (IN/'fit104_donor_operator_relational_capacity.csv').open(newline='') as f:groups=list(csv.DictReader(f))
assert len(groups)==1400 and len(donors)==104
eligible=collections.Counter();sizes=collections.Counter();ops=collections.Counter()
for r in groups:
 d=r['donor_id'];n=int(r['cells']);assert r['source']==donors[d]['source'];sizes[d]+=n;ops[d]+=1
 if n>=3:eligible[d]+=n
assert all(sizes[d]==int(r['fit_cells']) and eligible[d]>=1 and ops[d]==int(r['operator_count']) for d,r in donors.items())
field=['donor_id','source','operator_index','group_cells','eligible_anchor','donor_all_cells','donor_eligible_anchor_cells','donor_observed_operator_count','base_JEPA_group_mass_num','base_JEPA_group_mass_den','D1_P002_group_mass_num','D1_P002_group_mass_den','V2_relational_group_mass_num','V2_relational_group_mass_den','V2_relational_cell_anchor_mass_num','V2_relational_cell_anchor_mass_den','unordered_comparator_pairs_per_anchor','V2_comparator_pair_probability_num','V2_comparator_pair_probability_den']
rows=[]
for g in groups:
 d=g['donor_id'];n=int(g['cells']);e=eligible[d];nd=sizes[d];o=ops[d];pairs=math.comb(n-1,2) if n>=3 else 0
 rows.append(dict(zip(field,[d,g['source'],g['operator_index'],n,n>=3,nd,e,o,n,104*nd,1,104*o,n if n>=3 else 0,104*e,1 if n>=3 else 0,104*e,pairs,1 if n>=3 else 0,pairs if n>=3 else 1])))
assert sum(int(r['eligible_anchor']) for r in rows)==1361
assert sum(int(r['group_cells']) for r in rows if r['eligible_anchor'])==4553348
for d in donors:
 gg=[r for r in rows if r['donor_id']==d]
 assert sum((Fraction(int(g['base_JEPA_group_mass_num']),int(g['base_JEPA_group_mass_den'])) for g in gg),Fraction(0))==Fraction(1,104)
 assert sum((Fraction(int(g['D1_P002_group_mass_num']),int(g['D1_P002_group_mass_den'])) for g in gg),Fraction(0))==Fraction(1,104)
 assert sum((Fraction(int(g['V2_relational_group_mass_num']),int(g['V2_relational_group_mass_den'])) for g in gg),Fraction(0))==Fraction(1,104)
for r in rows:
 if r['eligible_anchor']:
  assert int(r['unordered_comparator_pairs_per_anchor'])==math.comb(int(r['group_cells'])-1,2)
 else: assert int(r['V2_relational_group_mass_num'])==0
name='FULL104_FIT104_RELATIONAL_V2_RATIONAL_MASSES.csv'
with (OUT/name).open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,field);w.writeheader();w.writerows(rows)
summary={'schema':'FULL104_FIT104_RELATIONAL_V2_METADATA_DERIVATION_V1','source_data':'PR146 physically authenticated CSVs, exact content SHAs in script','status':'PHYSICAL_METADATA_DERIVED__NOT_TRAINING_AUTHORITY','training_authorized':False,'eligible_donors':len(eligible),'fit_donors':104,'eligible_groups':1361,'total_groups':1400,'eligible_cells':4553348,'all_fit_cells':4553407,'noneligible_cells':59,'minimum_eligible_fraction_donor':min(eligible[d]/sizes[d] for d in donors),'maximum_eligible_fraction_donor':max(eligible[d]/sizes[d] for d in donors),'max_V2_vs_D1_group_mass_ratio':max(Fraction(int(g['V2_relational_group_mass_num']),int(g['V2_relational_group_mass_den']))/Fraction(int(g['D1_P002_group_mass_num']),int(g['D1_P002_group_mass_den'])) for g in rows if g['eligible_anchor']),'output_sha256':hashlib.sha256((OUT/name).read_bytes()).hexdigest(),'csv_output':name,'scope_note':'V2 relational eligible-anchor weights are NOT D1 equal-operator weights, and not base JEPA all-cell weights. Triplet capacities are combinatorial opportunities, not triplet sampling weights.'}
summary['max_V2_vs_D1_group_mass_ratio']=str(summary['max_V2_vs_D1_group_mass_ratio'])
(OUT/'FULL104_RELATIONAL_V2_METADATA_RECEIPT.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
print(json.dumps(summary,sort_keys=True))
