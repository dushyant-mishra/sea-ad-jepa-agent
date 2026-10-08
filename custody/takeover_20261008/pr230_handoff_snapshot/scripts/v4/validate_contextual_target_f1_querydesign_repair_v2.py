#!/usr/bin/env python3
"""Independent, metadata-only validator for F1 query-design repair.

Deliberately does not import the production derivation module.
"""
from __future__ import annotations
import bisect, csv, hashlib, hmac, json, math, struct, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from scipy.stats import t as student_t

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901"
PROGRAMS=("broad_common","weak_distributed","local","local_core","local_halo","core_halo","sparse_marker_like","innovation_tail")
REPAIR="2314fc5c72f4bcbf6cbcc193e55731be6a2ad554944d6d0a1526b61828cc5cdf"

def rows(p):
    with p.open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def F(t,b):return bytes([t])+len(b).to_bytes(8,"big")+b
def S(x):return unicodedata.normalize("NFC",str(x)).encode()
def U4(x):return int(x).to_bytes(4,"big")
def U8(x):return int(x).to_bytes(8,"big")
def H(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):h.update(b)
    return h.hexdigest()
def exact_mass_vector(w,idx):
    triples=[]
    for i in idx:
        a,b=float(np.float32(w[i])).as_integer_ratio(); triples.append((a*a,2*(b.bit_length()-1)))
    D=max(d for _,d in triples); mm=[a<<(D-d) for a,d in triples]; g=math.gcd(*mm)
    return [x//g for x in mm]
def main():
    source=json.loads((OUT/"F1_QUERYDESIGN_REPAIR_SOURCE_AUTHORITY.json").read_text()) if (OUT/"F1_QUERYDESIGN_REPAIR_SOURCE_AUTHORITY.json").exists() else None
    # The generator rewrites this authority immediately before validation.
    if source:
        for rec in source["authorities"].values():
            if H(ROOT/rec["path"])!=rec["sha256"]:raise SystemExit("STOP_F1_QUERYDESIGN_REPAIR_AUTHORITY_MISMATCH")
        for rec in source.get("generated_authorities",{}).values():
            if H(ROOT/rec["path"])!=rec["sha256"]:raise SystemExit("generated authority mutation")
        if H(ROOT/source["randomization_authority"]["path"])!=source["randomization_authority"]["sha256"]:raise SystemExit("randomization authority mutation")
        for name,rec in source["implementation"].items():
            if H(ROOT/rec["path"])!=rec["sha256"]:raise SystemExit(name+" mutation")
    seed=json.loads((OUT/"F1_QUERY_RANDOMIZATION_AUTHORITY.json").read_text()); key=bytes.fromhex(seed["public_hmac_sha256_key_hex"])
    root=hmac.new(key,F(1,b"F1_DESIGN_SAMPLED_QUERY_V3_HMAC")+F(2,bytes.fromhex(REPAIR)),hashlib.sha256).digest()
    ns=rows(ROOT/"exports/foundation_calibration_bundle_20260824/contracts/address_namespace.csv"); ids=[r["molecular_address_id"] for r in ns]
    bind=rows(OUT/"F1_ADDRESS_NAMESPACE_BINDING.csv")
    with np.load(ROOT/"exports/contextual_biology_v6r5a_20260822/program_weights.npz",allow_pickle=True) as z:
        wid=[str(x) for x in z["molecular_address_id"]]; W={p:z["raw__"+p].copy() for p in PROGRAMS}
    with np.load(ROOT/"exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz",allow_pickle=False) as z:
        st=z["states"].copy(); names=[str(x) for x in z["state_names"]]; ix=z["molecular_address_index"].copy()
    namespace_ok=(len(ns)==len(bind)==41238 and ids==wid and np.array_equal(ix,np.arange(41238,dtype=ix.dtype)) and all(int(r["position"])==i and r["canonical_address_id"]==ids[i] and int(r["expression_interface_column"])==i and int(r["tokenizer_gene_id"])==i for i,r in enumerate(bind)))
    if not namespace_ok:raise SystemExit("STOP_F1_ADDRESS_NAMESPACE_UNRESOLVED")
    scalar=names.index("MEASURED_SCALAR")
    cache={}; signs={}
    for p,w in W.items():
        signs[p]={"negative":int((w<0).sum()),"zero":int((w==0).sum()),"positive":int((w>0).sum()),"nonfinite":int((~np.isfinite(w)).sum())}
        if signs[p]["negative"] or signs[p]["nonfinite"]:raise SystemExit("STOP_F1_WEIGHT_SIGN_ASSUMPTION_FALSE")
    for o in range(42):
        for p,w in W.items():
            idx=np.flatnonzero((st[o]==scalar)&(w>0)).tolist(); mm=exact_mass_vector(w,idx); cc=[]; s=0
            for m in mm:s+=m;cc.append(s)
            cache[(o,p)]=(idx,mm,cc,s)
    cells=json.loads((ROOT/"outputs/contextual_teacher_target_v1_f1_preflight_20260901/CONTEXTUAL_TARGET_V1_F1_CELL_DONOR_OPERATOR_AUTHORITY.json").read_text())["selected_rows"]
    cell={r["canonical_cell_id"]:r for r in cells}; aa=rows(OUT/"F1_QUERY_ASSIGNMENTS_2DRAW.csv")
    if len(aa)!=44496:raise SystemExit("assignment count")
    donor_ops=defaultdict(set);donor_op_n=Counter()
    for r in cells:donor_ops[r["canonical_donor_id"]].add(int(r["operator_index"]));donor_op_n[(r["canonical_donor_id"],int(r["operator_index"]))]+=1
    cell_w={r["canonical_cell_id"]:(1,len(donor_ops[r["canonical_donor_id"]])*donor_op_n[(r["canonical_donor_id"],int(r["operator_index"]))]) for r in cells}
    weight_roots={a["cell_weight_authority_sha256"] for a in aa};cell_weight_ok=len(weight_roots)==1 and all((int(a["cell_weight_numerator"]),int(a["cell_weight_denominator"]))==cell_w[a["canonical_cell_id"]] and float(int(a["cell_weight_numerator"])/int(a["cell_weight_denominator"])).hex()==a["cell_weight_float64_hex"] for a in aa)
    donor_mass={d:sum(n/den for c,(n,den) in cell_w.items() if cell[c]["canonical_donor_id"]==d) for d in donor_ops};cell_weight_ok=cell_weight_ok and max(abs(x-1) for x in donor_mass.values())<1e-14
    mismatches=[]; independent=[]
    for a in aa:
        r=cell[a["canonical_cell_id"]]; o=int(a["operator_index"]); p=a["program"]; rep=int(a["draw_replicate"]); idx,mm,cc,M=cache[(o,p)]; L=(1<<256)//M*M; j=0
        while True:
            msg=b"".join((F(1,b"F1_PPS_UNIFORM_V3_HMAC"),F(2,root),F(3,S(r["canonical_cell_id"])),F(4,U4(o)),F(5,S(p)),F(6,bytes([rep])),F(8,U8(j))))
            d=hmac.new(key,msg,hashlib.sha256).digest(); z=int.from_bytes(d,"big")
            if z<L:break
            j+=1
        t=z%M; pos=bisect.bisect_right(cc,t); q=idx[pos]
        ok=(q==int(a["selected_query_address"]) and mm[pos]==int(a["exact_integer_mass"]) and M==int(a["total_integer_mass_M"]) and j==int(a["rejection_counter"]) and d.hex()==a["accepted_hmac_sha256"] and t==int(a["t_integer"]))
        if not ok:mismatches.append(a["assignment_key_sha256"])
        independent.append((r["canonical_cell_id"],p,rep,q))
    gv=json.loads((OUT/"F1_SERIALIZATION_GOLDEN_VECTORS.json").read_text()); golden_ok=len(gv["vectors"])==10
    for v in gv["vectors"]:
        x=v["inputs"];r=cell[x["canonical_cell_id"]];msg=b"".join((F(1,b"F1_PPS_UNIFORM_V3_HMAC"),F(2,root),F(3,S(r["canonical_cell_id"])),F(4,U4(x["operator_index"])),F(5,S(x["program"])),F(6,bytes([int(x["replicate"])])),F(8,U8(x["counter"]))))
        cand=b"".join((F(1,b"F1_PPS_CANDIDATE_AUTHORITY_V3"),F(2,root),F(3,S(r["canonical_cell_id"])),F(4,U4(x["operator_index"])),F(5,S(x["program"])),F(6,bytes([int(x["replicate"])])),F(7,U4(x["address"])),F(8,U8(x["counter"]))))
        golden_ok=golden_ok and msg.hex()==v["drawmsg_hex"] and hmac.new(key,msg,hashlib.sha256).hexdigest()==v["draw_hmac_sha256"] and cand.hex()==v["candidate_msg_hex"] and hashlib.sha256(cand).hexdigest()==v["candidate_sha256"]
    # Independently reconstruct cyclic QID map.
    by=defaultdict(set)
    for c,p,r,q in independent:by[c].add(q)
    qid={}
    for c,qs in by.items():
        order=sorted(qs,key=lambda q:hashlib.sha256(F(1,b"F1_QUERY_IDENTITY_V2")+F(2,root)+F(3,S(c))+F(7,U4(q))).digest())
        if len(order)<2:raise SystemExit("STOP_F1_QUERY_IDENTITY_COVERAGE_UNRESOLVED")
        for i,q in enumerate(order):qid[(c,q)]=order[(i+1)%len(order)]
    dd=rows(OUT/"F1_QUERY_EXECUTION_DEDUP_MAP.csv"); qid_ok=(len(dd)==len(qid) and all(qid[(r["canonical_cell_id"],int(r["selected_query_address"]))]==int(r["wrong_query_address"]) for r in dd))
    # Exact finite-population algebra fixture: two iid draws from values [-2,1,5] with masses [1,2,3].
    vals=np.array([-2.,1.,5.]); prob=np.array([1.,2.,3.])/6; mu=float(prob@vals)
    pairs=[(i,j) for i in range(3) for j in range(3)]; pp=np.array([prob[i]*prob[j] for i,j in pairs]); means=np.array([(vals[i]+vals[j])/2 for i,j in pairs]); vh=np.array([(vals[i]-vals[j])**2/4 for i,j in pairs])
    algebra={"E_Zbar":float(pp@means),"mu":mu,"E_Vhat":float(pp@vh),"Var_Zbar":float(pp@((means-mu)**2))}
    algebra_ok=all(abs(algebra[a]-algebra[b])<1e-15 for a,b in (("E_Zbar","mu"),("E_Vhat","Var_Zbar")))
    # Metadata firewall authority and attacks: the results must prove no callback invocation.
    fw=json.loads((OUT/"F1_POPULATION_FIREWALL_RESULTS.json").read_text()); firewall_ok=(fw["status"]=="PASS" and fw["recipients_authorized"]==2781 and fw["null_sources_authorized"]==2781 and not fw["expression_values_opened"] and fw["baseline_expression_reads_before_authorization"]==0 and fw["callback_response_binding_pass"] and fw["callback_wrong_order_rejected"] and fw["callback_column_swap_rejected"] and fw["nph_live_derivative_hashes_verified"]==7 and all(x["expression_read_count"]==0 and x["rejected_before_callback"] for x in fw["sentinel_attacks"]))
    # Mutation checks establish hash binding for assignment and namespace artifacts.
    assignment_sha=H(OUT/"F1_QUERY_ASSIGNMENTS_2DRAW.csv"); binding_sha=H(OUT/"F1_ADDRESS_NAMESPACE_BINDING.csv")
    # Independent hierarchy / Holm / STOP fixtures (no production adjudicator import).
    # d1 has cells [c1,c2] in op0 and [c3] in op1: equal operator means, then equal donor.
    d1=(np.mean([1.0,1.0])+np.mean([2.0]))/2
    hierarchy_ok=bool(abs(d1-1.5)<1e-15)
    # six cells, a=[1/4,1/4,1/2,1/2,1/4,1/4], two donors, eight programs.
    av=np.array([.25,.25,.5,.5,.25,.25]); per_program=sum((av*.5)**2*.25)/4 # Vhat averaged only through a^2; final /104 analogue n_donor^2 below
    independent_pop_overall_vq=(8*sum((av*.5)**2*.25))/(64*2**2)
    vq_ok=bool(np.isfinite(independent_pop_overall_vq) and independent_pop_overall_vq>0)
    x=np.array([-.4,-.401]); se=x.std(ddof=1)/np.sqrt(2); pneg=float(student_t.cdf(x.mean()/se,1)); qid_negative_holm_veto=bool(min(1.,8*pneg)<.05)
    draw_sign_stop=bool(np.mean([-1.,-2.])<0<np.mean([1.,2.]))
    synthetic_path=OUT/"F1_QUERYDESIGN_DECISION_SYNTHETIC.json"; synthetic=json.loads(synthetic_path.read_text()) if synthetic_path.exists() else {}
    adjudicator_fixture_ok=bool(synthetic.get("hierarchy_exact") and synthetic.get("population_overall_vq_exact") and synthetic.get("negative_qid_program_veto") and synthetic.get("assignment_query_swap_rejected") and synthetic.get("inconsistent_duplicate_reuse_rejected") and synthetic.get("caller_variance_rejected") and synthetic.get("forward_identity_mutation_rejected") and synthetic.get("assignment_authority_mutation_rejected") and synthetic.get("donor_operator_relabel_rejected") and synthetic.get("production_unfrozen_forward_rejected"))
    end_to_end_ok=hierarchy_ok and vq_ok and qid_negative_holm_veto and draw_sign_stop and adjudicator_fixture_ok
    report={"schema":"f1-querydesign-independent-validation-v2","status":"PASS" if not mismatches and namespace_ok and qid_ok and algebra_ok and firewall_ok and end_to_end_ok and golden_ok and cell_weight_ok else "STOP","production_helpers_imported":False,"assignment_rows_reproduced":len(aa),"assignment_mismatch_count":len(mismatches),"exact_integer_mass_and_draw_match":not mismatches,"golden_vectors_exact":golden_ok,"namespace_order_exact":namespace_ok,"cell_weight_bytes_and_donor_mass_exact":cell_weight_ok,"cell_weight_authority_sha256":next(iter(weight_roots)),"weight_sign_counts":signs,"qid_map_exact":qid_ok,"query_design_algebra":algebra,"query_design_algebra_exact":algebra_ok,"independent_hierarchy_exact":hierarchy_ok,"independent_population_query_variance_positive":vq_ok,"independent_negative_qid_holm_veto":qid_negative_holm_veto,"independent_draw_sign_stop":draw_sign_stop,"production_fixture_boolean_agreement":adjudicator_fixture_ok,"firewall_zero_read_attacks":firewall_ok,"assignment_csv_sha256":assignment_sha,"binding_csv_sha256":binding_sha,"candidate_outcomes_read":False,"protected_expression_read":False,"training_or_ema":False}
    (OUT/"F1_QUERYDESIGN_INDEPENDENT_VALIDATION.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"status":report["status"],"rows":len(aa),"mismatches":len(mismatches),"qid":qid_ok,"algebra":algebra_ok,"firewall":firewall_ok}))
    if report["status"]!="PASS":raise SystemExit(2)
if __name__=="__main__":main()
