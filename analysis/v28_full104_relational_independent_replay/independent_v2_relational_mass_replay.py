#!/usr/bin/env python3
"""Independent rational-mass replay from exact PR146 metadata CSVs.

No real expression or protected outcomes. Distinct from PR149's row-loop
producer: compute eligible donor strata first and then reconstruct all three
laws from exact arithmetic. Committed output comparison is byte-level.
"""
import argparse, csv, hashlib, json, math
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
EXPECTED_INPUTS = {
    'fit104_donor_scientific_masses.csv': '386e52ecb56031fba7bde855c7af314b08f1773427d367e0679e6de47f79c7b7',
    'fit104_donor_operator_relational_capacity.csv': 'e40acc06844f4a13cb956453fe54e74abed357c3777a80ec6c4a2778dcae8f65',
}
EXPECTED_OUTPUT = 'af718d6963906a7c65bf394d1f8d4bd0a62b7a0580d27128523996879e416b94'
COLUMNS = ('donor_id','source','operator_index','group_cells','eligible_anchor','donor_all_cells','donor_eligible_anchor_cells','donor_observed_operator_count','base_JEPA_group_mass_num','base_JEPA_group_mass_den','D1_P002_group_mass_num','D1_P002_group_mass_den','V2_relational_group_mass_num','V2_relational_group_mass_den','V2_relational_cell_anchor_mass_num','V2_relational_cell_anchor_mass_den','unordered_comparator_pairs_per_anchor','V2_comparator_pair_probability_num','V2_comparator_pair_probability_den')

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def require(ok,why):
    if not ok: raise ValueError('STOP_V28_V2_REPLAY_'+why)

def replay(input_dir: Path, output_dir: Path, required_digest=EXPECTED_OUTPUT):
    input_dir,output_dir=Path(input_dir),Path(output_dir)
    for filename,expect in EXPECTED_INPUTS.items():
        require(digest(input_dir/filename)==expect,'SOURCE_SHA_'+filename)
    with (input_dir/'fit104_donor_scientific_masses.csv').open(newline='') as f:
        donor_rows=list(csv.DictReader(f))
    with (input_dir/'fit104_donor_operator_relational_capacity.csv').open(newline='') as f:
        group_rows=list(csv.DictReader(f))
    donors={d['donor_id']:d for d in donor_rows}
    require(len(donor_rows)==len(donors)==104 and len(group_rows)==1400,'INPUT_CENSUS')
    strata=defaultdict(list)
    for g in group_rows:
        d=g['donor_id'];require(d in donors and donors[d]['source']==g['source'],'DONOR_ROLE_CROSSING')
        strata[d].append(g)
    require(set(strata)==set(donors),'DONOR_COVERAGE')
    D=len(donors)
    per_donor={};eligible_groups=eligible_cells=0
    for d,groups in strata.items():
        n_all=sum(int(g['cells']) for g in groups)
        n_e=sum(int(g['cells']) for g in groups if int(g['cells'])>=3)
        require(n_all==int(donors[d]['fit_cells']),'DONOR_CELLS')
        require(len(groups)==int(donors[d]['operator_count']) and n_e>0,'DONOR_OPERATOR_ELIGIBILITY')
        per_donor[d]={'n_all':n_all,'n_e':n_e,'operators':len(groups)}
        eligible_groups+=sum(int(g['cells'])>=3 for g in groups)
        eligible_cells+=n_e
    require(eligible_groups==1361 and eligible_cells==4553348 and
            sum(x['n_all'] for x in per_donor.values())==4553407,'FULL104_CENSUS')
    rendered=[]; totals=defaultdict(lambda:[Fraction(0),Fraction(0),Fraction(0)])
    for g in group_rows:
        d=g['donor_id']; n=int(g['cells']); st=per_donor[d];eligible=n>=3
        pairs=math.comb(n-1,2) if eligible else 0
        base=Fraction(n,D*st['n_all'])
        d1=Fraction(1,D*st['operators'])
        relational=Fraction(n if eligible else 0,D*st['n_e'])
        anchor=Fraction(1 if eligible else 0,D*st['n_e'])
        pair=Fraction(1,pairs) if eligible else Fraction(0,1)
        triples=[base,d1,relational];totals[d]=[totals[d][i]+triples[i] for i in range(3)]
        values=(d,g['source'],g['operator_index'],n,str(eligible),st['n_all'],st['n_e'],st['operators'],n,D*st['n_all'],1,D*st['operators'],n if eligible else 0,D*st['n_e'],1 if eligible else 0,D*st['n_e'],pairs,1 if eligible else 0,pairs if eligible else 1)
        rendered.append(dict(zip(COLUMNS,values)))
    require(all(row==[Fraction(1,D)]*3 for row in totals.values()),'THREE_WEIGHT_LAWS')
    require(not output_dir.exists() or not any(output_dir.iterdir()),'OUTPUT_MUST_BE_EMPTY')
    output_dir.mkdir(parents=True,exist_ok=True)
    path=output_dir/'FULL104_FIT104_RELATIONAL_V2_RATIONAL_MASSES.csv'
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,COLUMNS);w.writeheader();w.writerows(rendered)
    observed=digest(path)
    require(observed==required_digest,'INDEPENDENT_BYTE_DIGEST_MISMATCH')
    return {'schema':'V28_INDEPENDENT_PR149_RELATIONAL_V2_REPLAY_V1','method':'INDEPENDENT_DONOR_STRATUM_EXACT_FRACTIONS_FULL_OUTPUT_BYTE_COMPARISON','source_files':EXPECTED_INPUTS,'expected_pr149_csv_sha256':required_digest,'recomputed_csv_sha256':observed,'byte_identical':True,'donors':D,'groups':len(group_rows),'eligible_groups':eligible_groups,'eligible_cells':eligible_cells,'noneligible_cells':4553407-eligible_cells,'per_donor_three_laws_each_sum':'1/104','protected_outcomes_opened':False,'training_authorized':False,'scope':'METADATA_ONLY_NOT_ACTUAL_RELATIONAL_SAMPLING_OR_TRAINING'}

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--input-dir',type=Path,required=True);a.add_argument('--out-dir',type=Path,required=True);a.add_argument('--receipt-out',type=Path);args=a.parse_args()
    result=replay(args.input_dir,args.out_dir)
    print(json.dumps(result,indent=2,sort_keys=True))
    if args.receipt_out:args.receipt_out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
