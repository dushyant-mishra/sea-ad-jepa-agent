"""Sealed cross-gate known-truth exam for pre-outcome TD decision mechanics.

This harness is intentionally separate from per-gate development fixtures. It checks
exact frozen gate commits in isolated subprocesses using a sealed set of synthetic
worlds. Synthetic outcomes validate decision mechanics only; they do not set human
thresholds or create biological authority.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path


class SealedBatteryError(RuntimeError):
    pass


EXACT_GATE_HEADS = {
    "R1": "1df20029defaa2bcd7a51869c1026ac6075b1323",
    "G6": "bb1e35d33deb52236829012be452e4c4d8b362fc",
    "G7": "d90047308d633e259195a54501a230373b36d043",
    "G9": "6e5182e2dc4e8e263e8cbd309aed6494b5ea7a55",
    "G2": "c174d05215f14bda5292c07559b10445bc17d86c",
    "INCREMENT": "b7c317c640aa231a7d5ec1fa12271a39bfee86e6",
}

_ROOT_ENV = {
    "R1": "TD_BATTERY_R1_ROOT",
    "G6": "TD_BATTERY_G6_ROOT",
    "G7": "TD_BATTERY_G7_ROOT",
    "G9": "TD_BATTERY_G9_ROOT",
    "G2": "TD_BATTERY_G2_ROOT",
    "INCREMENT": "TD_BATTERY_INCREMENT_ROOT",
}

_NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}

_WORLDS = [
    {"name": "TRUE_CONTENT", "seed": 910001, "purpose": "large genuine advantage beyond frozen nuisance/noise margins"},
    {"name": "MARGIN_TRAP", "seed": 910019, "purpose": "small positive direction that remains below the substantive margin"},
    {"name": "SPARSE_SUPPORT", "seed": 910033, "purpose": "support loss must abstain rather than become biological failure"},
    {"name": "SOURCE_ASYMMETRY", "seed": 910051, "purpose": "one good source cannot compensate for one failed or non-estimable source"},
    {"name": "ADVERSE_NULL_TAIL_TRAP", "seed": 910057, "purpose": "good null median cannot rescue an adverse lower-tail collision"},
    {"name": "NO_ADDED_EVIDENCE", "seed": 910073, "purpose": "nominal ladder expansion with zero physical support cannot count as convergence"},
    {"name": "C6_PARTIAL_INCREMENT", "seed": 910079, "purpose": "C6 beating C1 but not C3 must fail"},
    {"name": "RELATIONAL_STRATUM_MISMATCH", "seed": 910103, "purpose": "cross-source relational pairing is a contract error"},
    {"name": "BINDING_MISMATCH", "seed": 910121, "purpose": "wrong deciding/reference identity must be rejected"},
]

_EXPECTED = {
    "TRUE_CONTENT": {"G6": "PASS", "G2": "PASS", "R4": "PASS"},
    "MARGIN_TRAP": {"G6": "FAIL", "G2": "FAIL", "R4": "FAIL"},
    "SPARSE_SUPPORT": {
        "R1": "NOT_ESTIMABLE_SUPPORT", "G7": "NOT_ESTIMABLE", "G9": "NOT_ESTIMABLE",
        "G2": "NOT_ESTIMABLE", "R4": "NOT_ESTIMABLE",
    },
    "SOURCE_ASYMMETRY": {"G9": "NOT_ESTIMABLE", "G2": "FAIL", "R4": "FAIL"},
    "ADVERSE_NULL_TAIL_TRAP": {"G9": "FAIL"},
    "NO_ADDED_EVIDENCE": {"G7": "NOT_ESTIMABLE"},
    "C6_PARTIAL_INCREMENT": {"C6": "FAIL"},
    "RELATIONAL_STRATUM_MISMATCH": {"R1": "CONTRACT_ERROR"},
    "BINDING_MISMATCH": {"G6": "CONTRACT_ERROR", "G2": "CONTRACT_ERROR", "R4": "CONTRACT_ERROR"},
}


def world_manifest() -> dict:
    return {
        "schema": "JEPA_TD_SEALED_CROSS_GATE_BATTERY_V1",
        "status": "SEALED_BEFORE_EXECUTION__SYNTHETIC_TEST_OF_TEST_ONLY",
        "sealed_before_execution": True,
        "seed_namespace": "TD_SEALED_CROSS_GATE_V1_20261014",
        "worlds": copy.deepcopy(_WORLDS),
        "expected_statuses": copy.deepcopy(_EXPECTED),
        "exact_gate_heads": dict(EXACT_GATE_HEADS),
        "human_candidate_outcomes_used": False,
        "human_thresholds_imported": False,
        "synthetic_results_have_biological_authority": False,
        "authority": dict(_NO_AUTHORITY),
    }


def _root(gate: str) -> Path:
    raw = os.environ.get(_ROOT_ENV[gate])
    if not raw:
        raise SealedBatteryError(f"missing exact-tree root for {gate}")
    root = Path(raw)
    if not root.is_dir():
        raise SealedBatteryError(f"exact-tree root for {gate} does not exist: {root}")
    return root


def _verify_head(gate: str, root: Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False,
    )
    if proc.returncode != 0:
        raise SealedBatteryError(f"cannot resolve exact head for {gate}: {proc.stderr.strip()}")
    observed = proc.stdout.strip()
    expected = EXACT_GATE_HEADS[gate]
    if observed != expected:
        raise SealedBatteryError(f"exact head mismatch for {gate}: expected {expected}, observed {observed}")
    return observed


def _run_python(gate: str, code: str) -> dict:
    root = _root(gate)
    _verify_head(gate, root)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    proc = subprocess.run(
        [sys.executable, "-c", code], cwd=root, env=env, text=True,
        capture_output=True, check=False,
    )
    if proc.returncode != 0:
        raise SealedBatteryError(
            f"{gate} sealed adapter failed with exit {proc.returncode}: {proc.stderr.strip()}"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SealedBatteryError(f"{gate} adapter did not emit canonical JSON: {proc.stdout!r}") from exc


def _r1_results() -> dict:
    return _run_python("R1", r'''
import json
import scripts.v5.td_r1_known_truth_stress_v1 as S

def row(donor, rid, qx, qy, *, eligible=True, source_x="SEA_AD", source_y="SEA_AD"):
    return {"donor_id":donor,"relation_id":rid,"source_x":source_x,"source_y":source_y,
            "operator_x":"opA","operator_y":"opA","support_stratum_x":"S","support_stratum_y":"S",
            "q_x":qx,"q_y":qy,"eligible":eligible,"cell_weight":1}
out={}
sparse=S.summarize_recurrence([row("D1","R1",1,1,eligible=False),row("D2","R2",1,-1,eligible=False)],minimum_informative_relations_per_donor=1)
out["SPARSE_SUPPORT"]=sparse["status"]
try:
    S.summarize_recurrence([row("D1","R1",1,1,source_y="HVS")],minimum_informative_relations_per_donor=1)
    out["RELATIONAL_STRATUM_MISMATCH"]="UNEXPECTED_ACCEPT"
except S.R1StressError:
    out["RELATIONAL_STRATUM_MISMATCH"]="CONTRACT_ERROR"
print(json.dumps(out,sort_keys=True))
''')


def _g6_results() -> dict:
    return _run_python("G6", r'''
import json, random
import scripts.v5.td_real_teacher_information_decision_v2 as G
B="a"*64

def qual_probe(): return {"schema":G.PROBE_QUAL_SCHEMA,"status":G.PROBE_QUAL_STATUS,"human_fail_semantics_qualified":True,"probe_scope":G.PROBE_SCOPE}
def qual_dec(): return {"schema":G.DECISION_QUAL_SCHEMA,"status":G.DECISION_QUAL_PASS,"known_truth_power_qualified":True}
def probe(vals,binding=B): return {"status":"PASS","input_binding_sha256":binding,"donor_deltas":[{"donor_id":f"D{i:02d}","delta":float(v)} for i,v in enumerate(vals)],"claim_boundary":"FINITE_LINEAR_DIAGNOSTIC_ONLY__NO_INFORMATION_THEORETIC_ABSENCE_CLAIM"}
def ref(n,margin,binding=B): return {"schema":G.REFERENCE_SCHEMA,"frozen":True,"qualified":True,"metric":G.METRIC,"orientation":G.ORIENTATION,"reference_kind":"MAX_U_REFIT_U_MEASUREMENT","donor_margins":{f"D{i:02d}":float(margin) for i in range(n)},"deciding_namespace_disjoint":True,"input_binding_sha256":binding,"reference_receipt_sha256":"b"*64}
def decide(vals,margin,binding=B,ref_binding=B): return G.adjudicate_g6_human_decision(probe_result=probe(vals,binding),probe_qualification=qual_probe(),decision_qualification=qual_dec(),reference_artifact=ref(len(vals),margin,ref_binding),alpha=0.01)["status"]
r=random.Random(910001); true_vals=[0.95+r.uniform(-0.02,0.02) for _ in range(8)]
r=random.Random(910019); trap_vals=[0.055+r.uniform(-0.003,0.003) for _ in range(8)]
out={"TRUE_CONTENT":decide(true_vals,0.20),"MARGIN_TRAP":decide(trap_vals,0.10)}
try:
    decide(true_vals,0.20,binding=B,ref_binding="c"*64); out["BINDING_MISMATCH"]="UNEXPECTED_ACCEPT"
except G.TeacherInformationDecisionError:
    out["BINDING_MISMATCH"]="CONTRACT_ERROR"
print(json.dumps(out,sort_keys=True))
''')


def _g7_results() -> dict:
    return _run_python("G7", r'''
import json
import scripts.v5.td_real_g7_terminal_decision_v2 as G
B="1"*64

def qual(): return {"schema":G.QUAL_SCHEMA,"status":G.QUAL_PASS,"known_truth_power_qualified":True}
def rows(n,disp,added): return [{"donor_id":f"D{i}","terminal_displacement":float(disp),"penultimate_supported_evidence":10,"full_supported_evidence":10+added,"added_supported_evidence":added,"input_binding_sha256":B} for i in range(n)]
def ref(rs,margin=.1): return {"schema":G.REFERENCE_SCHEMA,"frozen":True,"qualified":True,"metric":G.METRIC,"orientation":G.ORIENTATION,"reference_kind":"U_REFIT","deciding_namespace_disjoint":True,"input_binding_sha256":B,"reference_receipt_sha256":"2"*64,"donor_margins":{r["donor_id"]:margin for r in rs}}
def dec(rs): return G.adjudicate_g7_terminal(rows=rs,decision_qualification=qual(),reference_artifact=ref(rs))["status"]
sparse=rows(7,.02,1); none=rows(8,0.0,0)
out={"SPARSE_SUPPORT":dec(sparse),"NO_ADDED_EVIDENCE":dec(none)}
print(json.dumps(out,sort_keys=True))
''')


def _g9_results() -> dict:
    return _run_python("G9", r'''
import json
import scripts.v5.td_real_geometry_recurrence_engine_v1 as G
B="a"*64; RECEIPT="c"*64

def qual(): return {"schema":G.QUAL_SCHEMA,"status":G.QUAL_PASS,"known_truth_power_qualified":True}
def nulls(center,n=100): return [float(center-.02+(0.04*i/max(n-1,1))) for i in range(n)]
def row(source,donor,obs=.10,null=.80,estim="ESTIMABLE",reason=None): return {"source":source,"donor_id":donor,"estimability_status":estim,"estimability_reason":reason,"observed_displacement":float(obs) if estim=="ESTIMABLE" else None,"null_displacements":nulls(null) if estim=="ESTIMABLE" else None,"null_semantics":G.NULL_SEMANTICS,"null_producer_receipt_sha256":RECEIPT,"input_binding_sha256":B}
def ref(rs,refit=.05,stability=.20):
    ds=[r["donor_id"] for r in rs if r["estimability_status"]=="ESTIMABLE"]
    return {"schema":G.REFERENCE_SCHEMA,"frozen":True,"qualified":True,"metric":G.PROJECTOR_METRIC,"orientation":G.ORIENTATION,"deciding_namespace_disjoint":True,"input_binding_sha256":B,"reference_receipt_sha256":"b"*64,"refit_margins":{d:refit for d in ds},"stability_margins":{d:stability for d in ds}}
def dec(rs,sources,refit=.05,stability=.20): return G.adjudicate_geometry_recurrence(rows=rs,metric=G.PROJECTOR_METRIC,required_sources=sources,decision_qualification=qual(),reference_artifact=ref(rs,refit,stability),alpha=.01)["status"]
sparse=[row("SEA_AD",f"D{i:02d}") for i in range(7)]+[row("SEA_AD","D07",estim="NOT_ESTIMABLE_STRUCTURAL_SUPPORT",reason="NO_SUPPORT")]
asym=[row("SEA_AD",f"SEA_D{i:02d}") for i in range(8)]+[row("HVS",f"HVS_D{i:02d}") for i in range(7)]
tail=[row("SEA_AD",f"T_D{i:02d}") for i in range(8)]
for r in tail: r["null_displacements"]=[0.12]+[0.80]*99
out={"SPARSE_SUPPORT":dec(sparse,["SEA_AD"]),"SOURCE_ASYMMETRY":dec(asym,["SEA_AD","HVS"]),"ADVERSE_NULL_TAIL_TRAP":dec(tail,["SEA_AD"],refit=.05,stability=.20)}
print(json.dumps(out,sort_keys=True))
''')


def _g2_results() -> dict:
    return _run_python("G2", r'''
import json, random
import scripts.v5.td_real_g2_content_decision_v1 as G
B="a"*64; BASE=("constant_train_mean","technical_operator_only","address_support_operator")
def qual(): return {"schema":G.QUAL_SCHEMA,"status":G.QUAL_PASS,"known_truth_power_qualified":True}
def rows(source="SEA_AD",candidate=.8,baseline=.2,n=8,supports=None):
    supports=supports or ["SUPPORTED"]*n
    return [{"source":source,"endpoint":"PRIMARY","donor_id":f"{source}_D{i:02d}","candidate_score":float(candidate),"baseline_scores":{x:float(baseline) for x in BASE},"support_state":supports[i],"input_binding_sha256":B} for i in range(n)]
def key(r): return f'{r["source"]}::{r["endpoint"]}::{r["donor_id"]}'
def ref(rs,margin=.1,binding=B): return {"schema":G.REFERENCE_SCHEMA,"frozen":True,"qualified":True,"metric":G.METRIC,"orientation":G.ORIENTATION,"input_binding_sha256":binding,"reference_namespace_disjoint":True,"reference_receipt_sha256":"b"*64,"margins":{key(r):margin for r in rs if r["support_state"]=="SUPPORTED"}}
def dec(rs,strata,margin=.1,binding=B): return G.adjudicate_g2(rows=rs,required_strata=strata,frozen_baseline_ids=BASE,decision_qualification=qual(),reference_artifact=ref(rs,margin,binding),alpha=.01)["status"]
r=random.Random(910001); true_rows=rows(candidate=.80+r.uniform(-.01,.01),baseline=.20)
r=random.Random(910019); trap_rows=rows(candidate=.255+r.uniform(-.002,.002),baseline=.20)
sparse_rows=rows(supports=["UNSUPPORTED_STRUCTURAL","BLOCKED_EVIDENCE_CONTRACT"]+["SUPPORTED"]*6)
asym=rows(source="SEA_AD",candidate=.8,baseline=.2)+rows(source="NPH52",candidate=.21,baseline=.2)
out={"TRUE_CONTENT":dec(true_rows,[("SEA_AD","PRIMARY")]),"MARGIN_TRAP":dec(trap_rows,[("SEA_AD","PRIMARY")],margin=.10),"SPARSE_SUPPORT":dec(sparse_rows,[("SEA_AD","PRIMARY")]),"SOURCE_ASYMMETRY":dec(asym,[("SEA_AD","PRIMARY"),("NPH52","PRIMARY")],margin=.10)}
try:
    dec(true_rows,[("SEA_AD","PRIMARY")],binding="c"*64); out["BINDING_MISMATCH"]="UNEXPECTED_ACCEPT"
except G.G2DecisionError:
    out["BINDING_MISMATCH"]="CONTRACT_ERROR"
print(json.dumps(out,sort_keys=True))
''')


def _increment_results() -> dict:
    return _run_python("INCREMENT", r'''
import json
import scripts.v5.td_real_increment_decision_v1 as I
B="a"*64
def qual(): return {"schema":I.QUAL_SCHEMA,"status":I.QUAL_PASS,"known_truth_power_qualified":True}
def rows(source="SEA_AD",scores=None,n=8,supports=None):
    scores=scores or {"C1":.2,"C2":.8,"C3":.3,"C6":.9,"C4":1.0}; supports=supports or ["SUPPORTED"]*n
    return [{"source":source,"endpoint":"PRIMARY","donor_id":f"{source}_D{i:02d}","scores":dict(scores),"support_state":supports[i],"input_binding_sha256":B} for i in range(n)]
def key(r): return f'{r["source"]}::{r["endpoint"]}::{r["donor_id"]}'
def ref(rs,margin=.1,binding=B): return {"schema":I.REFERENCE_SCHEMA,"qualified":True,"metric":I.METRIC,"orientation":I.ORIENTATION,"input_binding_sha256":binding,"reference_receipt_sha256":"b"*64,"margins":{key(r):margin for r in rs if r["support_state"]=="SUPPORTED"}}
def dec(gate,rs,strata,prereq,margin=.1,binding=B): return I.adjudicate_increment(gate=gate,rows=rs,required_strata=strata,prerequisite_statuses=prereq,reference_artifact=ref(rs,margin,binding),decision_qualification=qual(),alpha=.01)["status"]
true_rows=rows(); trap=rows(scores={"C1":.20,"C2":.25,"C3":.20,"C6":.30,"C4":.40})
sparse=rows(supports=["UNSUPPORTED_STRUCTURAL"]+["SUPPORTED"]*7)
asym=rows(source="SEA_AD")+rows(source="NPH52",scores={"C1":.8,"C2":.7,"C3":.2,"C6":.9,"C4":1.0})
partial=rows(scores={"C1":.2,"C2":.8,"C3":.95,"C6":.9,"C4":1.0})
out={"TRUE_CONTENT":dec("R4",true_rows,[("SEA_AD","PRIMARY")],{"C1":"PASS"}),"MARGIN_TRAP":dec("R4",trap,[("SEA_AD","PRIMARY")],{"C1":"PASS"}),"SPARSE_SUPPORT":dec("R4",sparse,[("SEA_AD","PRIMARY")],{"C1":"PASS"}),"SOURCE_ASYMMETRY":dec("R4",asym,[("SEA_AD","PRIMARY"),("NPH52","PRIMARY")],{"C1":"PASS"},margin=.01),"C6_PARTIAL_INCREMENT":dec("C6",partial,[("SEA_AD","PRIMARY")],{"C1":"PASS","C3":"PASS"},margin=.01)}
try:
    dec("R4",true_rows,[("SEA_AD","PRIMARY")],{"C1":"PASS"},binding="c"*64); out["BINDING_MISMATCH"]="UNEXPECTED_ACCEPT"
except I.IncrementDecisionError:
    out["BINDING_MISMATCH"]="CONTRACT_ERROR"
print(json.dumps(out,sort_keys=True))
''')


@lru_cache(maxsize=1)
def _run_exam_cached() -> dict:
    observed_heads = {gate: _verify_head(gate, _root(gate)) for gate in EXACT_GATE_HEADS}
    gate_outputs = {
        "R1": _r1_results(), "G6": _g6_results(), "G7": _g7_results(),
        "G9": _g9_results(), "G2": _g2_results(), "INCREMENT": _increment_results(),
    }
    world_results: dict[str, dict[str, str]] = {w["name"]: {} for w in _WORLDS}
    for world, status in gate_outputs["R1"].items(): world_results[world]["R1"] = status
    for world, status in gate_outputs["G6"].items(): world_results[world]["G6"] = status
    for world, status in gate_outputs["G7"].items(): world_results[world]["G7"] = status
    for world, status in gate_outputs["G9"].items(): world_results[world]["G9"] = status
    for world, status in gate_outputs["G2"].items(): world_results[world]["G2"] = status
    for world, status in gate_outputs["INCREMENT"].items():
        label = "C6" if world == "C6_PARTIAL_INCREMENT" else "R4"
        world_results[world][label] = status

    mismatches = []
    for world, expected_gate_statuses in _EXPECTED.items():
        for gate, expected in expected_gate_statuses.items():
            observed = world_results.get(world, {}).get(gate)
            if observed != expected:
                mismatches.append({"world": world, "gate": gate, "expected": expected, "observed": observed})
    passed = not mismatches and observed_heads == EXACT_GATE_HEADS
    return {
        "schema": "JEPA_TD_SEALED_CROSS_GATE_BATTERY_RECEIPT_V1",
        "status": "PASS_SEALED_CROSS_GATE_BATTERY_V1" if passed else "FAIL_SEALED_CROSS_GATE_BATTERY_V1",
        "all_expectations_met": bool(passed),
        "exact_gate_heads": dict(EXACT_GATE_HEADS),
        "observed_gate_heads": observed_heads,
        "world_results": world_results,
        "mismatches": mismatches,
        "human_candidate_outcomes_used": False,
        "human_thresholds_imported": False,
        "synthetic_results_have_biological_authority": False,
        "authority": dict(_NO_AUTHORITY),
    }


def run_exam() -> dict:
    return copy.deepcopy(_run_exam_cached())
