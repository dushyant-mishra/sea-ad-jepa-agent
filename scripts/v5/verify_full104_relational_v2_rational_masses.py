#!/usr/bin/env python3
"""Independent arithmetic check of FULL104 relational V2, distinct from D1 and base JEPA.
Never authenticates unmounted heavy expression or authorizes training.
"""
import csv,hashlib,math,sys
from collections import Counter
from fractions import Fraction
from pathlib import Path
SHAS={"fit104_donor_scientific_masses.csv":"386e52ecb56031fba7bde855c7af314b08f1773427d367e0679e6de47f79c7b7",
"fit104_donor_operator_relational_capacity.csv":"e40acc06844f4a13cb956453fe54e74abed357c3777a80ec6c4a2778dcae8f65"}
FIELDS=["donor_id","source","operator_index","group_cells","eligible_anchor","donor_all_cells","donor_eligible_anchor_cells",
"donor_observed_operator_count","base_JEPA_group_mass_num","base_JEPA_group_mass_den","D1_P002_group_mass_num",
"D1_P002_group_mass_den","V2_relational_group_mass_num","V2_relational_group_mass_den",
"V2_relational_cell_anchor_mass_num","V2_relational_cell_anchor_mass_den",
"unordered_comparator_pairs_per_anchor","V2_comparator_pair_probability_num","V2_comparator_pair_probability_den"]
def read(p):
    with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def verify(input_dir,output_csv):
    source=Path(input_dir)
    for n,h in SHAS.items():
        if hashlib.sha256((source/n).read_bytes()).hexdigest()!=h:raise ValueError("STOP_WRONG_PR146_INPUT_BYTES "+n)
    donor_rows=read(source/"fit104_donor_scientific_masses.csv")
    source_rows=read(source/"fit104_donor_operator_relational_capacity.csv")
    if len(donor_rows)!=104 or len(source_rows)!=1400:raise ValueError("STOP_WRONG_FULL104_POPULATION")
    donors={r["donor_id"]:r for r in donor_rows}
    group_source={(r["donor_id"],r["operator_index"]):r for r in source_rows}
    if len(donors)!=104 or len(group_source)!=1400:raise ValueError("STOP_DUPLICATED_IDENTITIES")
    E=Counter()
    for r in source_rows:
        if int(r["cells"])>=3:E[r["donor_id"]]+=int(r["cells"])
    out_path=Path(output_csv)
    with out_path.open(newline="",encoding="utf-8") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=FIELDS:raise ValueError("STOP_SCHEMA_ROLE_SPILLOVER")
        records=list(reader)
    if len(records)!=1400:raise ValueError("STOP_GROUP_COUNT")
    seen=set()
    base_sum=Counter();d1_sum=Counter();rel_sum=Counter();eligible_cells=0;eligible_groups=0
    for x in records:
        key=(x["donor_id"],x["operator_index"])
        if key not in group_source or key in seen:raise ValueError("STOP_UNKNOWN_OR_DUPLICATE_GROUP")
        seen.add(key)
        g=group_source[key];d=donors[key[0]]
        n=int(g["cells"]);nd=int(d["fit_cells"]);o=int(d["operator_count"]);e=E[key[0]]
        yes=n>=3;pairs=math.comb(n-1,2) if yes else 0
        expected=dict(zip(FIELDS,[key[0],d["source"],key[1],str(n),str(yes),str(nd),str(e),str(o),
            str(n),str(104*nd),"1",str(104*o),str(n if yes else 0),str(104*e),
            str(1 if yes else 0),str(104*e),str(pairs),str(1 if yes else 0),str(pairs if yes else 1)]))
        for k in FIELDS:
            if x[k]!=expected[k]:raise ValueError("STOP_V2_ESTIMAND_OR_IDENTITY_MISMATCH "+k+" "+str(key))
        eligible_groups+=int(yes);eligible_cells+=n if yes else 0
        base_sum[key[0]]+=Fraction(int(x["base_JEPA_group_mass_num"]),int(x["base_JEPA_group_mass_den"]))
        d1_sum[key[0]]+=Fraction(int(x["D1_P002_group_mass_num"]),int(x["D1_P002_group_mass_den"]))
        rel_sum[key[0]]+=Fraction(int(x["V2_relational_group_mass_num"]),int(x["V2_relational_group_mass_den"]))
    if eligible_groups!=1361 or eligible_cells!=4553348:raise ValueError("STOP_ELIGIBLE_POPULATION")
    if any(z[d]!=Fraction(1,104) for z in (base_sum,d1_sum,rel_sum) for d in donors):
        raise ValueError("STOP_SCIENTIFIC_WEIGHT_MASS")
    return {"status":"PASS_INDEPENDENT_RELATIONAL_V2_ESTIMAND","groups":1400,"eligible_groups":1361,
            "eligible_anchor_cells":4553348,"donors":104,"base_D1_V2_per_donor_exact_mass":"1/104",
            "training_authorized":False}
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("USAGE: verify.py PR146_INPUT_DIR DERIVED_CSV")
    import json
    print(json.dumps(verify(sys.argv[1],sys.argv[2]),sort_keys=True))
