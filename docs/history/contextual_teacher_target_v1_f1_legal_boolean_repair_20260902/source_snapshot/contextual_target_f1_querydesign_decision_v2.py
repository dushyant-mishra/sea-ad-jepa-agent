"""Prospective assignment-to-donor F1 query-design adjudication; no project outcomes loaded."""
from __future__ import annotations
import argparse, csv, hashlib, json, tempfile
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.stats import t as student_t

ALPHA=.05
PROGRAMS=("broad_common","weak_distributed","local","local_core","local_halo","core_halo","sparse_marker_like","innovation_tail")
EVIDENCE=(.2,.4,.6,.8,1.0)
FROZEN_ASSIGNMENT_PATH=Path(__file__).resolve().parents[2]/"outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv"
FROZEN_ASSIGNMENT_SHA256="12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617"
# A real evaluator remains fail-closed until its complete per-forward authority is frozen externally.
FROZEN_FORWARD_AUTHORITY_SHA256=None

def interval(x):
    x=np.asarray(x,np.float64); n=len(x); m=float(np.mean(x)) if n else None
    if n<2 or not np.isfinite(x).all() or float(np.var(x,ddof=1))==0:return {"estimable":False,"n":n,"mean":m,"lower_95":None,"upper_95":None,"lower_one_sided_95":None,"p_positive":None,"p_negative":None}
    se=float(x.std(ddof=1)/np.sqrt(n)); stat=m/se; df=n-1
    return {"estimable":True,"n":n,"mean":m,"lower_95":m-float(student_t.ppf(.975,df))*se,"upper_95":m+float(student_t.ppf(.975,df))*se,"lower_one_sided_95":m-float(student_t.ppf(.95,df))*se,"p_positive":float(student_t.sf(stat,df)),"p_negative":float(student_t.cdf(stat,df))}

def holm(p):
    p=np.asarray(p,np.float64); order=np.argsort(p,kind="stable"); out=np.empty(len(p)); run=0.
    for rank,i in enumerate(order):run=max(run,(len(p)-rank)*p[i]);out[i]=min(1.,run)
    return out

def file_sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(4<<20),b""):h.update(b)
 return h.hexdigest()
def canonical_sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def load_assignment_authority(path,expected_sha,*,require_frozen=True):
 path=Path(path)
 if file_sha(path)!=expected_sha:raise ValueError("assignment file hash mismatch")
 with path.open("r",encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
 out={}
 for r in rows:
  k=r["assignment_key_sha256"]
  if k in out:raise ValueError("duplicate assignment key")
  out[k]={"cell":r["canonical_cell_id"],"donor":r["donor_id"],"source":r["source"],"operator":int(r["operator_index"]),"cell_weight_num":int(r["cell_weight_numerator"]),"cell_weight_den":int(r["cell_weight_denominator"]),"cell_weight_hex":r["cell_weight_float64_hex"],"cell_weight_authority":r["cell_weight_authority_sha256"],"program":r["program"],"replicate":int(r["draw_replicate"]),"query_address":int(r["selected_query_address"]),"evaluation_row_authority":r["evaluation_row_authority_sha256"]}
 if require_frozen and (len(rows)!=44496 or len(out)!=44496):raise ValueError("STOP_F1_QUERYDESIGN_POPULATION_INCOMPLETE assignment count")
 cells={};by_cell_program=defaultdict(set)
 for a in out.values():
  ident=(a["donor"],a["source"],a["operator"],a["evaluation_row_authority"])
  if a["cell"] in cells and cells[a["cell"]]!=ident:raise ValueError("assignment cell identity conflict")
  cells[a["cell"]]=ident;by_cell_program[(a["cell"],a["program"])].add(a["replicate"])
 if require_frozen and (len(cells)!=2781 or len({x[0] for x in cells.values()})!=104 or len({x[2] for x in cells.values()})!=42):raise ValueError("STOP_F1_QUERYDESIGN_POPULATION_INCOMPLETE assignment population")
 if {a["program"] for a in out.values()}!=set(PROGRAMS):raise ValueError("STOP_F1_QUERYDESIGN_POPULATION_INCOMPLETE program population")
 if len(by_cell_program)!=len(cells)*8 or any(v!={0,1} for v in by_cell_program.values()):raise ValueError("assignment replicate completeness")
 return out

def validate_observed_keyspace(observed,authority,*,require_frozen=True):
 expected={(k,e) for k in authority for e in EVIDENCE}
 expected_n=222480 if require_frozen else len(authority)*len(EVIDENCE)
 if len(observed)!=expected_n or len(set(observed))!=expected_n or set(observed)!=expected:raise ValueError("STOP_F1_QUERYDESIGN_POPULATION_INCOMPLETE result key space")
 return expected
def validate_record_population(records,authority,*,require_frozen=True):
 observed=[(r.get("assignment_key"),float(r.get("evidence",float("nan")))) for r in records]
 expected=validate_observed_keyspace(observed,authority,require_frozen=require_frozen)
 frozen_cells={a["cell"] for a in authority.values()};frozen_donors={a["donor"] for a in authority.values()}
 if {str(r.get("cell")) for r in records}!=frozen_cells or {str(r.get("donor")) for r in records}!=frozen_donors:raise ValueError("STOP_F1_QUERYDESIGN_POPULATION_INCOMPLETE result population")
 return expected,frozen_cells,frozen_donors
def aggregate(records, assignment_csv_path=None, assignment_file_sha256=None, *, test_only=False, forward_authority_sha256=None):
    """Require complete records and return exact replicate->program->cell->operator->donor aggregates."""
    required={"cell","donor","source","operator","program","replicate","evidence","query_address","assignment_key","evaluation_row_authority","assignment_authority_sha256","mask_authority","model_checkpoint","sketch","forward_identity_sha256","A","direct_delta","qid_margin","qid_win"}
    if any(set(r)!=required for r in records):raise ValueError("exact record schema mismatch")
    if not test_only:
        assignment_csv_path=FROZEN_ASSIGNMENT_PATH;assignment_file_sha256=FROZEN_ASSIGNMENT_SHA256
        if FROZEN_FORWARD_AUTHORITY_SHA256 is None or forward_authority_sha256!=FROZEN_FORWARD_AUTHORITY_SHA256:raise ValueError("STOP_FORWARD_AUTHORITY_NOT_FROZEN")
    assignment_authority=load_assignment_authority(assignment_csv_path,assignment_file_sha256,require_frozen=not test_only)
    validate_record_population(records,assignment_authority,require_frozen=not test_only)
    donors=sorted({a["donor"] for a in assignment_authority.values()}); cells=sorted({a["cell"] for a in assignment_authority.values()})
    donor_sources={d:{a["source"] for a in assignment_authority.values() if a["donor"]==d} for d in donors}
    if any(len(x)!=1 for x in donor_sources.values()):raise ValueError("donor source identity conflict")
    authority_cell_meta={a["cell"]:(a["donor"],a["operator"]) for a in assignment_authority.values()}
    cell_meta={}
    for r in records:
        key=str(r["cell"]); meta=(str(r["donor"]),int(r["operator"]))
        if key in cell_meta and cell_meta[key]!=meta:raise ValueError("cell metadata conflict")
        cell_meta[key]=meta
        if r["program"] not in PROGRAMS or int(r["replicate"]) not in (0,1) or float(r["evidence"]) not in EVIDENCE:raise ValueError("domain mismatch")
        if r["assignment_authority_sha256"]!=assignment_file_sha256:raise ValueError("assignment file authority mismatch")
        ar=assignment_authority.get(r["assignment_key"])
        if ar is None or (str(r["cell"]),str(r["donor"]),str(r["source"]),int(r["operator"]),r["program"],int(r["replicate"]),int(r["query_address"]),r["evaluation_row_authority"])!=(ar["cell"],ar["donor"],ar["source"],ar["operator"],ar["program"],ar["replicate"],ar["query_address"],ar["evaluation_row_authority"]):raise ValueError("assignment identity mismatch")
        if not all(str(r[k]) for k in ("mask_authority","model_checkpoint","sketch")):raise ValueError("forward authority empty")
        fi={"cell":str(r["cell"]),"query_address":int(r["query_address"]),"evidence":float(r["evidence"]),"mask_authority":r["mask_authority"],"model_checkpoint":r["model_checkpoint"],"sketch":r["sketch"]}
        if canonical_sha(fi)!=r["forward_identity_sha256"]:raise ValueError("forward identity mismatch")
        for k in ("A","direct_delta","qid_margin","qid_win"):
            if not np.isfinite(float(r[k])):raise ValueError("nonfinite")
        if float(r["qid_win"]) not in (0.0,0.5,1.0):raise ValueError("STOP_F1_QUERYDESIGN_METRIC_DOMAIN")
    by=defaultdict(list)
    for r in records:by[(str(r["cell"]),r["program"],float(r["evidence"]),int(r["replicate"]))].append(r)
    if any(len(v)!=1 for v in by.values()):raise ValueError("duplicate assignment outcome")
    if len(by)!=(222480 if not test_only else len(assignment_authority)*len(EVIDENCE)):raise ValueError("missing assignment outcome")
    forward_seen={}
    for r in records:
        fk=(str(r["cell"]),int(r["query_address"]),float(r["evidence"]))
        value=(r["forward_identity_sha256"],float(r["A"]),float(r["direct_delta"]),float(r["qid_margin"]),float(r["qid_win"]))
        if fk in forward_seen and forward_seen[fk]!=value:raise ValueError("inconsistent duplicate forward reuse")
        forward_seen[fk]=value
    # frozen hierarchy weights
    cell_weight={}
    for ar in assignment_authority.values():
        v=(ar["cell_weight_num"],ar["cell_weight_den"],ar["cell_weight_hex"],ar["cell_weight_authority"])
        if ar["cell"] in cell_weight and cell_weight[ar["cell"]]!=v:raise ValueError("cell weight authority conflict")
        cell_weight[ar["cell"]]=v
    if len({v[3] for v in cell_weight.values()})!=1:raise ValueError("cell weight root mismatch")
    a={c:cell_weight[c][0]/cell_weight[c][1] for c in cells}
    if any(float(a[c]).hex()!=cell_weight[c][2] for c in cells):raise ValueError("cell weight bytes mismatch")
    if any(abs(sum(a[c] for c,(dd,_) in authority_cell_meta.items() if dd==d)-1)>1e-14 for d in donors):raise ValueError("donor weight mass")
    result={"donors":donors,"donor_source":[next(iter(donor_sources[d])) for d in donors],"population_authority":{"assignment_sha256":assignment_file_sha256,"assignment_count":len(assignment_authority),"result_count":len(assignment_authority)*len(EVIDENCE),"cell_count":len(cells),"donor_count":len(donors),"operator_count":len({a["operator"] for a in assignment_authority.values()}),"test_fixture":bool(test_only)},"program":{},"program_direct":{},"program_qid_margin":{},"overall":{},"query_variance":{}}
    for e in EVIDENCE:
        p_by={}; direct_by={}; qm_by={}; qw_by={}; draw_by={0:{},1:{}}
        vq_d={d:{} for d in donors}
        for p in PROGRAMS:
            for d in donors:
                z=[]; direct=[]; qm=[]; qw=[]; zdraw={0:[],1:[]}; vq=0.
                for c,(dd,o) in cell_meta.items():
                    if dd!=d:continue
                    rr=[by[(c,p,e,r)][0] for r in (0,1)]
                    z.append(a[c]*(float(rr[0]["A"])+float(rr[1]["A"]))/2)
                    direct.append(a[c]*(float(rr[0]["direct_delta"])+float(rr[1]["direct_delta"]))/2)
                    qm.append(a[c]*(float(rr[0]["qid_margin"])+float(rr[1]["qid_margin"]))/2)
                    qw.append(a[c]*((float(rr[0]["qid_win"])-.5)+(float(rr[1]["qid_win"])-.5))/2)
                    for r in (0,1):zdraw[r].append(a[c]*float(rr[r]["A"]))
                    vhat=(float(rr[0]["A"])-float(rr[1]["A"]))**2/4
                    vq += a[c]**2 * vhat
                p_by[(d,p)]=sum(z);direct_by[(d,p)]=sum(direct);qm_by[(d,p)]=sum(qm);qw_by[(d,p)]=sum(qw);vq_d[d][p]=vq
                for r in (0,1):draw_by[r][(d,p)]=sum(zdraw[r])
        result["program"][str(e)]={p:[p_by[(d,p)] for d in donors] for p in PROGRAMS}
        result["program_direct"][str(e)]={p:[direct_by[(d,p)] for d in donors] for p in PROGRAMS}
        result["program_qid_margin"][str(e)]={p:[qm_by[(d,p)] for d in donors] for p in PROGRAMS}
        result["overall"][str(e)]={
            "A":[sum(p_by[(d,p)] for p in PROGRAMS)/8 for d in donors],
            "direct":[sum(direct_by[(d,p)] for p in PROGRAMS)/8 for d in donors],
            "qid_margin":[sum(qm_by[(d,p)] for p in PROGRAMS)/8 for d in donors],
            "qid_win_minus_half":[sum(qw_by[(d,p)] for p in PROGRAMS)/8 for d in donors],
            "draw0":[sum(draw_by[0][(d,p)] for p in PROGRAMS)/8 for d in donors],
            "draw1":[sum(draw_by[1][(d,p)] for p in PROGRAMS)/8 for d in donors],
        }
        result["query_variance"][str(e)]={"donor_program":vq_d,"population_program":{p:sum(vq_d[d][p] for d in donors)/len(donors)**2 for p in PROGRAMS},"population_overall":sum(vq_d[d][p] for d in donors for p in PROGRAMS)/(64*len(donors)**2)}
    return result

def adjudicate(agg):
    e="0.6"; ov=agg["overall"][e]; program=agg["program"][e]
    overall={k:interval(ov[k]) for k in ("A","direct","qid_margin","qid_win_minus_half")}
    prog_int={p:interval(program[p]) for p in PROGRAMS}
    # QID arrays are provided in overall aggregation only here; callers must include program-specific QID in extension payload before real execution.
    # Fail closed unless program_qid_margin has been bound by the runtime adapter.
    if "program_qid_margin" not in agg or e not in agg["program_qid_margin"]:raise ValueError("program-specific QID margin missing")
    qprog={p:interval(agg["program_qid_margin"][e][p]) for p in PROGRAMS}
    qneg=holm([qprog[p]["p_negative"] if qprog[p]["estimable"] else 0. for p in PROGRAMS])
    draw0=float(np.mean(ov["draw0"]));draw1=float(np.mean(ov["draw1"])); sign_stable=not ((draw0<0<draw1) or (draw1<0<draw0))
    gates={"overall_one_sided_95lcb_positive":overall["A"]["estimable"] and overall["A"]["lower_one_sided_95"]>0,"qid_margin_one_sided_95lcb_positive":overall["qid_margin"]["estimable"] and overall["qid_margin"]["lower_one_sided_95"]>0,"qid_win_one_sided_95lcb_positive":overall["qid_win_minus_half"]["estimable"] and overall["qid_win_minus_half"]["lower_one_sided_95"]>0,"no_qid_negative_program_holm":all(x>=ALPHA for x in qneg),"draw_sign_stable":sign_stable,"all_programs_estimable":all(prog_int[p]["estimable"] for p in PROGRAMS)}
    return {"component_scope":"QUERY_DESIGN_COMPONENT_ONLY","query_design_component_pass":all(gates.values()),"gates":gates,"overall":overall,"program":prog_int,"qid_negative_holm":dict(zip(PROGRAMS,qneg.tolist())),"draw_means":[draw0,draw1],"claim_scope":"FINITE_FROZEN_2781_DESIGN_SAMPLED_W2_EXPECTATION; donor-t is a superpopulation working inference; Vq is finite-design randomization uncertainty"}

def frozen_population_adversarial():
    """Outcome-blind attacks against the exact frozen assignment-derived key universe."""
    authority=load_assignment_authority(FROZEN_ASSIGNMENT_PATH,FROZEN_ASSIGNMENT_SHA256)
    observed=[(k,e) for k in authority for e in EVIDENCE]
    validate_observed_keyspace(observed,authority)
    donor=next(iter(authority.values()))["donor"];cell=next(iter(authority.values()))["cell"]
    attacks={
      "drop_entire_donor_rejected":[x for x in observed if authority[x[0]]["donor"]!=donor],
      "drop_entire_cell_rejected":[x for x in observed if authority[x[0]]["cell"]!=cell],
      "missing_assignment_evidence_rejected":observed[:-1],
      "duplicate_replace_rejected":observed[:-1]+[observed[0]],
      "extra_assignment_rejected":observed+[("0"*64,EVIDENCE[0])],
    }
    out={}
    for name,attack in attacks.items():
      try:validate_observed_keyspace(attack,authority);out[name]=False
      except ValueError:out[name]=True
    out.update({"exact_222480_record_space_verified":len(observed)==222480 and len(set(observed))==222480,"exact_104_donor_population_verified":len({a["donor"] for a in authority.values()})==104,"exact_2781_cell_population_verified":len({a["cell"] for a in authority.values()})==2781,"exact_42_operator_population_verified":len({a["operator"] for a in authority.values()})==42})
    return out

def synthetic():
    # Two donors, two operators, unequal cells: validates hierarchy and adversarial gates, not production power.
    rec=[]; authority_rows=[]
    layout=[("c1","d1",0),("c2","d1",0),("c3","d1",1),("c4","d2",0),("c5","d2",1),("c6","d2",1)]
    syn_weight={"c1":(1,4),"c2":(1,4),"c3":(1,2),"c4":(1,2),"c5":(1,4),"c6":(1,4)};weight_root="synthetic-weight-root"
    for c,d,o in layout:
      for p in PROGRAMS:
       for e in EVIDENCE:
        for r in (0,1):
         ak=hashlib.sha256(f"{c}|{p}|{r}".encode()).hexdigest(); er=hashlib.sha256(f"row|{c}".encode()).hexdigest(); q=100+PROGRAMS.index(p)*2+r
         if e==EVIDENCE[0]:
          wn,wd=syn_weight[c];authority_rows.append({"canonical_cell_id":c,"donor_id":d,"source":"S","operator_index":o,"cell_weight_numerator":wn,"cell_weight_denominator":wd,"cell_weight_float64_hex":float(wn/wd).hex(),"cell_weight_authority_sha256":weight_root,"program":p,"draw_replicate":r,"selected_query_address":q,"assignment_key_sha256":ak,"evaluation_row_authority_sha256":er})
         fi={"cell":c,"query_address":q,"evidence":e,"mask_authority":f"mask|{e}","model_checkpoint":"model","sketch":"A"}
         rec.append({"cell":c,"donor":d,"source":"S","operator":o,"program":p,"replicate":r,"evidence":e,"query_address":q,"assignment_key":ak,"evaluation_row_authority":er,"assignment_authority_sha256":"PENDING","mask_authority":fi["mask_authority"],"model_checkpoint":"model","sketch":"A","forward_identity_sha256":canonical_sha(fi),"A":1+o+.01*r,"direct_delta":.2,"qid_margin":.4,"qid_win":1.})
    td=tempfile.TemporaryDirectory();apath=Path(td.name)/"assignments.csv"
    with apath.open("w",encoding="utf-8",newline="") as f:
     w=csv.DictWriter(f,fieldnames=list(authority_rows[0]),lineterminator="\n");w.writeheader();w.writerows(authority_rows)
    assignment_sha=file_sha(apath)
    for x in rec:x["assignment_authority_sha256"]=assignment_sha
    agg=aggregate(rec,apath,assignment_sha,test_only=True)
    agg["program_qid_margin"]["0.6"]={p:[.4,.5] for p in PROGRAMS}
    # With only two donors and no variance in some endpoints, qualification is expected fail-closed; arithmetic identities are decisive.
    d1=agg["overall"]["0.6"]["A"][0]; expected_d1=((1.005)+(2.005))/2
    v_expected=sum(agg["query_variance"]["0.6"]["population_program"].values())/64
    decision=adjudicate(agg)
    attack=dict(agg);attack["program_qid_margin"]={k:dict(v) for k,v in agg["program_qid_margin"].items()};attack["program_qid_margin"]["0.6"]["local_core"]=[-.4,-.401]
    attacked=adjudicate(attack)
    swapped=[dict(x) for x in rec];swapped[0]["query_address"]+=1
    try:aggregate(swapped,apath,assignment_sha,test_only=True);swap_rejected=False
    except ValueError:swap_rejected=True
    inconsistent=[dict(x) for x in rec]; target=inconsistent[0]
    # Force a second assignment to claim the same forward key but a different result.
    inconsistent[1]["query_address"]=target["query_address"]
    try:aggregate(inconsistent,apath,assignment_sha,test_only=True);reuse_rejected=False
    except ValueError:reuse_rejected=True
    variance_attack=[dict(x) for x in rec];variance_attack[0]["Vhat_design"]=999.
    try:aggregate(variance_attack,apath,assignment_sha,test_only=True);variance_rejected=False
    except ValueError:variance_rejected=True
    forward_attack=[dict(x) for x in rec];forward_attack[0]["mask_authority"]="changed"
    try:aggregate(forward_attack,apath,assignment_sha,test_only=True);forward_rejected=False
    except ValueError:forward_rejected=True
    relabel=[dict(x) for x in rec];relabel[0]["donor"]="changed";relabel[0]["operator"]=99
    try:aggregate(relabel,apath,assignment_sha,test_only=True);donor_operator_relabel_rejected=False
    except ValueError:donor_operator_relabel_rejected=True
    cell_relabel=[dict(x) for x in rec];cell_relabel[0]["cell"]="c2"
    try:aggregate(cell_relabel,apath,assignment_sha,test_only=True);cell_relabel_rejected=False
    except ValueError:cell_relabel_rejected=True
    qid_domain={}
    for label,value in (("two",2.),("negative_one",-1.),("quarter",.25),("nan",float("nan")),("inf",float("inf"))):
     attack_q=[dict(x) for x in rec];attack_q[0]["qid_win"]=value
     try:aggregate(attack_q,apath,assignment_sha,test_only=True);qid_domain[label]=False
     except ValueError:qid_domain[label]=True
    try:aggregate(rec,apath,assignment_sha,test_only=False,forward_authority_sha256="caller-chosen");production_unfrozen_forward_rejected=False
    except ValueError:production_unfrozen_forward_rejected=True
    with apath.open("a",encoding="utf-8") as f:f.write("\n")
    try:aggregate(rec,apath,assignment_sha,test_only=True);authority_mutation_rejected=False
    except ValueError:authority_mutation_rejected=True
    out={"hierarchy_exact":abs(d1-expected_d1)<1e-14,"population_overall_vq_exact":abs(agg["query_variance"]["0.6"]["population_overall"]-v_expected)<1e-14,"negative_qid_program_veto":not attacked["gates"]["no_qid_negative_program_holm"],"assignment_query_swap_rejected":swap_rejected,"inconsistent_duplicate_reuse_rejected":reuse_rejected,"caller_variance_rejected":variance_rejected,"forward_identity_mutation_rejected":forward_rejected,"assignment_authority_mutation_rejected":authority_mutation_rejected,"donor_relabel_rejected":donor_operator_relabel_rejected,"cell_relabel_rejected":cell_relabel_rejected,"qid_win_domain_attacks":qid_domain,"production_unfrozen_forward_rejected":production_unfrozen_forward_rejected,"frozen_population":frozen_population_adversarial(),"base":decision,"attack":attacked};td.cleanup();return out

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--synthetic-out",type=Path,required=True);a=ap.parse_args();a.synthetic_out.write_text(json.dumps(synthetic(),indent=2),encoding="utf-8")
