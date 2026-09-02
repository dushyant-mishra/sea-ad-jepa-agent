"""Run synthetic-only 15C integration verification and emit staged evidence."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = load(HERE / "contextual_target_f1_hc3_15c_adapter_v1.py", "adapter15c_run")
fixtures = load(HERE / "test_contextual_target_f1_decision_truth_table_v2.py", "fixtures15c_run")
legal_test = load(HERE / "test_contextual_target_f1_legal_boolean_v1.py", "legal15c_run")
v1 = load(HERE / "contextual_target_f1_decision_v1.py", "v1_15c_run")


def safe(value):
    if isinstance(value, (np.bool_,)): return bool(value)
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.floating,)): return float(value) if np.isfinite(value) else str(value)
    if isinstance(value, np.ndarray): return safe(value.tolist())
    if isinstance(value, dict): return {str(k): safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [safe(v) for v in value]
    if isinstance(value, float) and not np.isfinite(value): return str(value)
    return value


def write(path: Path, value):
    path.write_text(json.dumps(safe(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_input():
    p = fixtures.base_payload()
    donors = adapter.load_selected_design()[0]["donor_order"]
    records={}
    for i,donor in enumerate(donors):
        records[donor]={key:p[key][i] for key in adapter.VECTOR_FIELDS}
        records[donor]["evidence_A"]=p["evidence_A"][i]
        for family in adapter.FAMILY_FIELDS:
            records[donor][family]={program:p[family][program][i] for program in p[family]}
    return {"donor_records":records,"legal":p["legal"]}


def changed(base, attacked):
    return [k for k, value in base["gates"].items() if attacked["gates"].get(k) != value]


def rejection(name, base, mutate, reason):
    p = copy.deepcopy(base); mutate(p)
    try:
        adapter.qualify_synthetic(p); rejected = False; error = None
    except (ValueError, TypeError) as exc:
        rejected = True; error = str(exc)
    return {"attack": name, "rejected": rejected, "error": error, "reason": reason, "pass": rejected}

def design_rejection(name, mutate_schema=None, mutate_design=None, design_bytes=None):
    schema_path=adapter.P15B/"F1_HC3_SELECTED_DONOR_DESIGN_SCHEMA.json";design_path=adapter.P15B/"F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin"
    sb=bytearray(schema_path.read_bytes());db=bytearray(design_path.read_bytes() if design_bytes is None else design_bytes)
    if mutate_schema:sb=bytearray(mutate_schema(json.loads(bytes(sb).decode("utf-8"))))
    if mutate_design:mutate_design(db)
    try:adapter.verify_candidate_selected_design(bytes(sb),bytes(db));rejected=False;error=None
    except ValueError as exc:rejected=True;error=str(exc)
    return {"attack":name,"actual_candidate_schema_sha256":hashlib.sha256(sb).hexdigest(),"actual_candidate_design_sha256":hashlib.sha256(db).hexdigest(),"rejected":rejected,"error":error,"pass":rejected}


def find_isolated_hc3_veto(base):
    """Fixed algebraic candidates only; no real outcome or random tuning."""
    schema, x = adapter.load_selected_design()
    q = np.linalg.qr(x, mode="reduced")[0]
    lever = np.sum(q*q, axis=1)
    source = np.array([d.split("::", 1)[0] for d in schema["donor_order"]])
    projector = np.eye(104)-q@q.T
    raw=[]
    for idx in np.argsort(lever)[::-1]:
        e=np.zeros(104);e[idx]=1.;raw.append((f"basis_{idx}",e))
    rng=np.random.default_rng(1503)
    raw.extend((f"fixed_normal_{j}",rng.normal(size=104)) for j in range(2048))
    columns = {f"c{i:02d}_{schema['columns'][i]['identity']}": x[:, i] for i in range(1, 16)}
    candidates=[]
    for label,z0 in raw:
        residual=projector@z0
        base_overall=v1.t_interval(residual);base_groups=v1.group_intervals(residual,source);base_hc3=v1.hc3_intercept(residual,columns)
        if not base_hc3["estimable"]:continue
        source_threshold={g:-base_groups[g]["lower"] for g in base_groups}
        weighted_source=sum(np.mean(source==g)*t for g,t in source_threshold.items())
        ordinary=max(-base_overall["lower_one_sided"],weighted_source)
        robust=-base_hc3["lower"]
        if robust>ordinary+1e-12:
            mean=(ordinary+robust)/2
            delta=mean-weighted_source
            source_means={g:source_threshold[g]+delta for g in source_threshold}
            y=residual+np.asarray([source_means[g] for g in source])
            p=copy.deepcopy(base)
            for donor,value in zip(schema["donor_order"],y):p["donor_records"][donor]["overall_A"]=float(value)
            candidates.append((label,float(mean),p,None));break
    if not candidates:
        raise RuntimeError("STOP_F1_15C_NUISANCE_INTEGRATION_FAIL_OPEN")
    idx, mean, p, _ = candidates[0]
    decision = adapter.qualify_synthetic(p)
    return {"construction": "first fixed residual-space vector whose frozen HC3 critical offset exceeds both ordinary and within-source critical offsets; mean is their midpoint", "candidate": idx, "mean": mean, "payload": p, "decision": decision}


def run(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    authority = adapter.verify_authorities()
    authority.update({
        "status": "PASS_F1_15C_AUTHORITY_VERIFIED", "selected_design_sha256": adapter.EXPECTED["design"],
        "truth_table_sha256": adapter.EXPECTED["truth_table"], "decision_v4_sha256": adapter.EXPECTED["decision"],
        "integration_v4_sha256": adapter.EXPECTED["integration"],
        "chronology_claim": "EXECUTION_ENFORCED_PROSPECTIVELY__EXTERNAL_TIME_ANCHOR_UNAVAILABLE",
        "separate_anchor_classification": "SEPARATE_LOCAL_ROOT_BINDING_NOT_PRE_RESULT_TIME_PROOF",
        "real_reader_forward_authority": None, "expression_or_model_access": False,
    })
    write(out / "F1_15C_INTEGRATION_AUTHORITY.json", authority)
    write(out / "F1_15C_SELECTED_DESIGN_REVERIFICATION.json", adapter.reverify_selected_design())

    base = make_input(); decision = adapter.qualify_synthetic(base)
    if not decision["qualified"]: raise RuntimeError("synthetic baseline did not pass")
    baseline = {"status": "PASS_F1_15C_SYNTHETIC_ALL_PASS", "construction": "fixed seed 9022026 legacy truth-table fixture with exact frozen donor identities; no real outcomes", "payload": base, "decision": decision}
    write(out / "F1_15C_SYNTHETIC_BASELINE.json", baseline)

    veto = find_isolated_hc3_veto(base)
    veto_changed = changed(decision, veto["decision"])
    attacks = [{"attack": "A_nuisance_veto", "changed_gates": veto_changed, "intended_gate": "hc3_nuisance_positive", "pass": veto_changed == ["hc3_nuisance_positive"] and not veto["decision"]["qualified"], **veto}]
    attacks.extend([
        rejection("B_forged_hc3_pass", base, lambda p: p.__setitem__("hc3_pass", True), "caller-derived authority forbidden"),
        rejection("F_donor_omission", base, lambda p: p["donor_records"].pop(next(iter(p["donor_records"]))), "exact donor set required"),
        rejection("G_donor_relabel", base, lambda p: p["donor_records"].__setitem__("fake::donor",p["donor_records"].pop(next(iter(p["donor_records"])))), "exact donor identities required"),
        rejection("K_nonfinite", base, lambda p: p["donor_records"][next(iter(p["donor_records"]))].__setitem__("overall_A", float("nan")), "decision-bearing endpoint must be finite"),
    ])
    attacks.extend([
        design_rejection("C_one_bit_design_mutation",mutate_design=lambda b:b.__setitem__(17,b[17]^1)),
        design_rejection("D_wrong_triple",mutate_schema=lambda s:(s.__setitem__("selected_triple",[5,1,4]) or json.dumps(s,sort_keys=True).encode())),
        design_rejection("H_forbidden_NPH_C1",mutate_schema=lambda s:(s["columns"].append({"identity":"NPH52_residual_svd_score_01","source":"NPH52"}) or json.dumps(s,sort_keys=True).encode())),
        design_rejection("I_forbidden_HVS_C6",mutate_schema=lambda s:(s["columns"].append({"identity":"HVS_residual_svd_score_06","source":"HVS"}) or json.dumps(s,sort_keys=True).encode())),
        design_rejection("J_old_raw_rank18_design",design_bytes=(ROOT/"outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902/F1_NUISANCE_DONOR_DESIGN_F64LE.bin").read_bytes()),
    ])
    perm = copy.deepcopy(base); perm["donor_records"]={k:perm["donor_records"][k] for k in reversed(list(perm["donor_records"]))}
    pdec = adapter.qualify_synthetic(perm)
    parallel=copy.deepcopy(base);parallel["donor_ids"]=list(parallel["donor_records"]);parallel["overall_A"]=[parallel["donor_records"][d]["overall_A"] for d in reversed(list(parallel["donor_records"]))]
    try:adapter.qualify_synthetic(parallel);parallel_rejected=False
    except ValueError:parallel_rejected=True
    attacks.append({"attack": "E_donor_order_and_positional_drift", "behavior": "donor-keyed insertion permutation realigned; obsolete parallel-array positional attack rejected", "same_gate_vector": pdec["gates"] == decision["gates"], "parallel_array_attack_rejected":parallel_rejected, "pass": pdec["gates"] == decision["gates"] and parallel_rejected})
    zero = copy.deepcopy(base)
    for record in zero["donor_records"].values():record["overall_A"]=0.
    zdec = adapter.qualify_synthetic(zero)
    attacks.append({"attack": "L_zero_variance_nonestimability", "changed_gates": changed(decision,zdec), "attacked_gates": zdec["gates"], "hc3_estimable":zdec["reports"]["nuisance"]["estimable"], "pass":not zdec["reports"]["nuisance"]["estimable"] and not zdec["gates"]["hc3_nuisance_positive"]})
    source = copy.deepcopy(base); y=np.r_[.62+.02*np.sin(np.arange(41)),.62+.02*np.cos(np.arange(17)),-.04+.02*np.sin(np.arange(46))]
    for donor,value in zip(adapter.load_selected_design()[0]["donor_order"],y):source["donor_records"][donor]["overall_A"]=float(value)
    sdec=adapter.qualify_synthetic(source)
    attacks.append({"attack":"M_source_confined", "changed_gates":changed(decision,sdec), "attacked_gates":sdec["gates"], "pass":not sdec["gates"]["cross_source_replication"]})
    legal_rows=[]
    legal_cases=[("True",True),("False",False),("str_true","True"),("str_false","False"),("int1",1),("int0",0),("list",[]),("dict",{}),("none",None),("numpy_true",np.bool_(True)),("numpy_false",np.bool_(False))]
    for name,value in legal_cases:
        p=copy.deepcopy(base);p["legal"]=value
        try:r=adapter.qualify_synthetic(p); passed=r["qualified"]
        except ValueError:passed=False
        expected = (name == "True")
        legal_rows.append({"case":name,"qualified":passed,"expected":expected,"pass":passed==expected})
    attacks.append({"attack":"N_legal_type_domain","cases":legal_rows,"pass":all(r["pass"] for r in legal_rows)})
    adversarial={"status":"PASS_F1_15C_NUISANCE_ADVERSARIAL" if all(a["pass"] for a in attacks) else "STOP_F1_15C_NUISANCE_INTEGRATION_FAIL_OPEN","base_gates":decision["gates"],"attacks":attacks}
    write(out / "F1_15C_NUISANCE_ADVERSARIAL.json", adversarial)
    if not adversarial["status"].startswith("PASS_"): raise RuntimeError(adversarial["status"])

    legacy = fixtures.attacks()
    assignment = ROOT / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv"
    assignment_rows = sum(1 for _ in assignment.open(encoding="utf-8"))-1
    regression = {
        "status": "PASS_F1_15C_FULL_DECISION_REGRESSION" if legacy["status"].startswith("PASS_") and assignment_rows==44496 else "STOP_F1_15C_DECISION_REGRESSION_MISMATCH",
        "legacy_14_cases": [{"attack":a["attack"],"changed_gates":a["changed_gates"],"isolated_pass":a["isolated_pass"]} for a in legacy["attacks"]],
        "all_14_pass": all(a["isolated_pass"] for a in legacy["attacks"]), "population_attacks": legacy["population_attacks"],
        "record_identity_attacks": legacy["record_identity_attacks"], "strict_legal_suite": legal_rows,
        "assignment_rows": assignment_rows, "assignment_evidence_records": assignment_rows*5,
        "claim_scope": decision["claim_scope"], "program_estimand": decision["program_estimand"],
        "single_hc3_gate": list(decision["gates"]).count("hc3_nuisance_positive")==1,
        "decision_v4_unchanged": adapter.sha256(adapter.DECISION)==adapter.EXPECTED["decision"],
        "integration_v4_unchanged": adapter.sha256(adapter.INTEGRATION)==adapter.EXPECTED["integration"],
    }
    write(out / "F1_15C_FULL_DECISION_REGRESSION.json", regression)
    if not regression["status"].startswith("PASS_"): raise RuntimeError(regression["status"])


if __name__ == "__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--out",type=Path,required=True);args=parser.parse_args();run(args.out)
