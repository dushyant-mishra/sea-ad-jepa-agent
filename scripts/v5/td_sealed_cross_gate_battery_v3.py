"""Sealed cross-gate system exam V3 after Macha hostile-review repairs.

V3 does not recycle pre-repair biological PASS/FAIL expectations. It verifies the
cross-gate safety invariants that motivated the repairs against exact frozen gate
heads in isolated subprocess trees. Synthetic outputs remain tests of tests only.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path


class SealedBatteryV3Error(RuntimeError):
    pass


EXACT_GATE_HEADS = {
    "G8": "95dd474a02ce571722df9e8f08b42e81af2e8736",
    "G6": "aa36d56bfdd92335a516e329817411a66da917c9",
    "G7": "5a711f9a4ea0328445a05dadc1e011efb16a3c13",
    "G9": "a28f158007f20df1b0c9329915220a1a71ae7aec",
    "G2": "49edb657e2653532eca9365976f5b3b9f14b4467",
    "R1": "a0a1d060faff9a7a38e8f331302f17dac6610f51",
    "INCREMENT": "b7c317c640aa231a7d5ec1fa12271a39bfee86e6",
}
_ROOT_ENV = {gate: f"TD_BATTERY_{gate}_ROOT" for gate in EXACT_GATE_HEADS}
_NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}
_EXPECTED = {
    "CALLER_STEERING": {"G2": "REJECTED", "G6": "FAIL_CLOSED", "G9": "FAIL_CLOSED"},
    "ZERO_MARGIN": {"G2": "NOT_ESTIMABLE", "G6": "NOT_ESTIMABLE"},
    "SUPPORT_ATTRITION": {"G2": "REJECTED"},
    "SOURCE_ASYMMETRY": {"G7": "NOT_ESTIMABLE", "G9": "NOT_ESTIMABLE", "R1": "NOT_ESTIMABLE"},
    "TECHNICAL_DEPTH_CONFOUND": {"R1": "PASS_TECHNICAL_NEGATIVE", "G8": "REFERENCE_GENERATION_BLOCKED"},
    "NUMERICAL_FAILURE": {"G2": "NUMERICAL_FAILURE", "G6": "NUMERICAL_FAILURE", "G9": "NUMERICAL_FAILURE"},
}


def world_manifest() -> dict:
    return {
        "schema": "JEPA_TD_SEALED_CROSS_GATE_BATTERY_V3",
        "status": "SEALED_BEFORE_EXECUTION__MACHA_HOSTILE_REPAIR_REQUALIFICATION__SYNTHETIC_TEST_OF_TEST_ONLY",
        "sealed_before_execution": True,
        "seed_namespace": "TD_SEALED_CROSS_GATE_V3_MACHA_REPAIRS_20261014",
        "invariants": copy.deepcopy(_EXPECTED),
        "exact_gate_heads": dict(EXACT_GATE_HEADS),
        "human_candidate_outcomes_used": False,
        "human_thresholds_imported": False,
        "synthetic_results_have_biological_authority": False,
        "authority": dict(_NO_AUTHORITY),
    }


def _root(gate: str) -> Path:
    raw = os.environ.get(_ROOT_ENV[gate])
    if not raw:
        raise SealedBatteryV3Error(f"missing exact-tree root for {gate}")
    root = Path(raw)
    if not root.is_dir():
        raise SealedBatteryV3Error(f"exact-tree root for {gate} does not exist: {root}")
    return root


def _verify_head(gate: str, root: Path) -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise SealedBatteryV3Error(f"cannot resolve exact head for {gate}: {proc.stderr.strip()}")
    observed = proc.stdout.strip()
    if observed != EXACT_GATE_HEADS[gate]:
        raise SealedBatteryV3Error(f"exact head mismatch for {gate}: {observed}")
    return observed


def _run(gate: str, code: str) -> dict:
    root = _root(gate)
    _verify_head(gate, root)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    proc = subprocess.run([sys.executable, "-c", code], cwd=root, env=env, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise SealedBatteryV3Error(f"{gate} adapter failed: {proc.stderr.strip()}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SealedBatteryV3Error(f"{gate} adapter emitted non-JSON: {proc.stdout!r}") from exc


def _g8() -> dict:
    return _run("G8", r'''
import json
import scripts.v5.td_real_g8_realization_contract_v3 as G
out=G.reference_generation_readiness(observation_thinning_schema=G.REQUIRED_THINNING_SCHEMA,
    exact_input_bound=True,metric_contract_bound=True,support_contract_bound=True,technical_draws_available=599)
print(json.dumps({"TECHNICAL_DEPTH_CONFOUND":"REFERENCE_GENERATION_BLOCKED" if out["reference_generation_authorized"] is False else "BAD"},sort_keys=True))
''')


def _g6() -> dict:
    return _run("G6", r'''
import json
import scripts.v5.td_real_teacher_information_decision_v3 as G
B="a"*64; S="d"*64

def probe(vals): return {"status":"PASS","input_binding_sha256":B,"target_scale_contract_sha256":S,"donor_deltas":[{"donor_id":f"D{i:02d}","delta":v} for i,v in enumerate(vals)]}
def ref(vals): return {"schema":G.REFERENCE_SCHEMA,"frozen":True,"qualified":True,"metric":G.METRIC,"orientation":G.ORIENTATION,"reference_kind":"U_MEASUREMENT","donor_margins":{f"D{i:02d}":v for i,v in enumerate(vals)},"input_binding_sha256":B,"target_scale_contract_sha256":S,"reference_receipt_sha256":"b"*64,"independent_non_degenerate_reference":True}
steer=G.adjudicate_g6_v3(probe_result=probe([1.0]*8),reference_artifact=ref([.25]*8),external_qualification_receipt_sha256="c"*64)
zero=G.adjudicate_g6_v3(probe_result=probe([1.0]*8),reference_artifact=ref([0.0]*8),external_qualification_receipt_sha256=None)
p=probe([1.0]*8); p["donor_deltas"][2]["delta"]=float("nan")
num=G.adjudicate_g6_v3(probe_result=p,reference_artifact=ref([.25]*8),external_qualification_receipt_sha256=None)
print(json.dumps({"CALLER_STEERING":"FAIL_CLOSED" if steer["status"]=="NOT_ESTIMABLE" and not steer["human_pass_fail_authorized"] else "BAD","ZERO_MARGIN":zero["status"],"NUMERICAL_FAILURE":num["status"]},sort_keys=True))
''')


def _g7() -> dict:
    return _run("G7", r'''
import json
import scripts.v5.td_real_g7_terminal_decision_v3 as G
B="1"*64
def qual(): return {"schema":G.QUAL_SCHEMA,"status":G.QUAL_PASS,"known_truth_power_qualified":True}
def rows(source,n): return [{"source":source,"donor_id":f"{source}_D{i:02d}","terminal_displacement":.02,"penultimate_supported_evidence":10,"full_supported_evidence":11,"added_supported_evidence":1,"input_binding_sha256":B} for i in range(n)]
def unit(r): return f'{r["source"]}::{r["donor_id"]}'
def ref(rs): return {"schema":G.REFERENCE_SCHEMA,"frozen":True,"qualified":True,"metric":G.METRIC,"orientation":G.ORIENTATION,"reference_kind":"U_REFIT","deciding_namespace_disjoint":True,"input_binding_sha256":B,"reference_receipt_sha256":"2"*64,"unit_margins":{unit(r):.1 for r in rs}}
rs=rows("SEA_AD",8)+rows("HVS",7)
out=G.adjudicate_g7_terminal_v3(rows=rs,required_sources=["SEA_AD","HVS"],decision_qualification=qual(),reference_artifact=ref(rs),alpha=.01)
print(json.dumps({"SOURCE_ASYMMETRY":out["status"]},sort_keys=True))
''')


def _g9() -> dict:
    return _run("G9", r'''
import json
import scripts.v5.td_real_geometry_recurrence_engine_v2 as G
B="b"*64
def row(d,source="SEA_AD",obs=.1,n=100): return {"source":source,"donor_id":d,"estimability_status":"ESTIMABLE","estimability_reason":None,"observed_displacement":obs,"null_displacements":[1.0]*n,"null_semantics":"DONOR_PRESERVING_IDENTITY_SHUFFLE_LOWER_ADVERSE_BOUND","null_producer_receipt_sha256":"a"*64,"input_binding_sha256":B}
def ref(ds,st=.5): return {"schema":"JEPA_TD_REAL_GEOMETRY_REFERENCE_MARGIN_V1","frozen":True,"qualified":True,"metric":"PROJECTOR_RMS_PRINCIPAL_ANGLE_DISPLACEMENT","orientation":"SMALLER_DISPLACEMENT_IS_MORE_STABLE","deciding_namespace_disjoint":True,"input_binding_sha256":B,"reference_receipt_sha256":"c"*64,"refit_margins":{d:.1 for d in ds},"stability_margins":{d:st for d in ds}}
ds=[f"D{i:02d}" for i in range(8)]
steer=G.adjudicate_geometry_v2(rows=[row(d) for d in ds],required_sources=["SEA_AD"],reference_artifact=ref(ds),producer_qualification_receipt_sha256="f"*64)
# Missing HVS is explicit required-source non-estimability, not rescue.
asym=G.adjudicate_geometry_v2(rows=[row(d) for d in ds],required_sources=["SEA_AD","HVS"],reference_artifact=ref(ds),producer_qualification_receipt_sha256=None)
r=[row(d) for d in ds]; r[1]["observed_displacement"]=float("nan")
num=G.adjudicate_geometry_v2(rows=r,required_sources=["SEA_AD"],reference_artifact=ref(ds),producer_qualification_receipt_sha256=None)
print(json.dumps({"CALLER_STEERING":"FAIL_CLOSED" if steer["status"]=="NOT_ESTIMABLE" and not steer["human_pass_fail_authorized"] else "BAD","SOURCE_ASYMMETRY":asym["diagnostic_status"],"NUMERICAL_FAILURE":num["status"]},sort_keys=True))
''')


def _g2() -> dict:
    return _run("G2", r'''
import json
import scripts.v5.td_real_g2_content_decision_v2 as G
B="a"*64
base=G.baseline_ids_for_candidate("C1_SHARED_EMERGENT")
def env(n=8): return {"schema":G.ENVELOPE_SCHEMA,"candidate_id":"C1_SHARED_EMERGENT","input_binding_sha256":B,"claim_envelope_receipt_sha256":"b"*64,"frozen_before_values":True,"units":[{"source":"SEA_AD","endpoint":"PRIMARY","donor_id":f"D{i:02d}","support_state":"SUPPORTED"} for i in range(n)]}
def rows(n=8,val=.8): return [{"source":"SEA_AD","endpoint":"PRIMARY","donor_id":f"D{i:02d}","candidate_score":val,"baseline_scores":{b:.2 for b in base},"support_state":"SUPPORTED","input_binding_sha256":B} for i in range(n)]
def ref(rs,m=.1): return {"schema":G.REFERENCE_SCHEMA,"frozen":True,"qualified":True,"metric":G.METRIC,"orientation":G.ORIENTATION,"input_binding_sha256":B,"reference_receipt_sha256":"c"*64,"independent_non_degenerate_reference":True,"margins":{f'{r["source"]}::{r["endpoint"]}::{r["donor_id"]}':m for r in rs if r["support_state"]=="SUPPORTED"}}
# Caller steering: incomplete baseline family must be rejected.
bad=rows(); bad[0]["baseline_scores"]={"constant_train_mean":.2}
try:
 G.adjudicate_g2_v2(candidate_id="C1_SHARED_EMERGENT",rows=bad,claim_envelope=env(),reference_artifact=ref(rows()),external_qualification_receipt_sha256=None); steer="BAD"
except G.G2DecisionV2Error: steer="REJECTED"
# Support attrition: relabel a frozen-supported unit.
bad2=rows(); bad2[0]["support_state"]="UNSUPPORTED_STRUCTURAL"
try:
 G.adjudicate_g2_v2(candidate_id="C1_SHARED_EMERGENT",rows=bad2,claim_envelope=env(),reference_artifact=ref(rows()),external_qualification_receipt_sha256=None); attr="BAD"
except G.G2DecisionV2Error: attr="REJECTED"
rs=rows(val=.201); zero=G.adjudicate_g2_v2(candidate_id="C1_SHARED_EMERGENT",rows=rs,claim_envelope=env(),reference_artifact=ref(rs,0.0),external_qualification_receipt_sha256=None)
rn=rows(); rn[2]["candidate_score"]=float("nan"); num=G.adjudicate_g2_v2(candidate_id="C1_SHARED_EMERGENT",rows=rn,claim_envelope=env(),reference_artifact=ref(rn),external_qualification_receipt_sha256=None)
print(json.dumps({"CALLER_STEERING":steer,"SUPPORT_ATTRITION":attr,"ZERO_MARGIN":zero["status"],"NUMERICAL_FAILURE":num["status"]},sort_keys=True))
''')


def _r1() -> dict:
    return _run("R1", r'''
import json
import scripts.v5.td_r1_depth_matched_null_v2 as G
q=G.qualify_depth_matched_r1_null(seed=777)
rows=[{"donor_id":"H1","source":"HVS","status":"SUPPORTED","delta":.2},{"donor_id":"S1","source":"SEA_AD","status":"UNSUPPORTED","delta":None}]
asym=G.summarize_source_recurrence(rows,required_sources=["HVS","SEA_AD"])
print(json.dumps({"TECHNICAL_DEPTH_CONFOUND":q["worlds"]["TECHNICAL_LIBRARY_SIZE_ONLY"]["status"],"SOURCE_ASYMMETRY":asym["overall_status"]},sort_keys=True))
''')


@lru_cache(maxsize=1)
def _cached() -> dict:
    observed_heads = {gate: _verify_head(gate, _root(gate)) for gate in EXACT_GATE_HEADS}
    outputs = {"G8": _g8(), "G6": _g6(), "G7": _g7(), "G9": _g9(), "G2": _g2(), "R1": _r1()}
    invariants = {name: {} for name in _EXPECTED}
    for gate, result in outputs.items():
        for invariant, value in result.items():
            invariants[invariant][gate] = value
    mismatches = []
    for invariant, gates in _EXPECTED.items():
        for gate, expected in gates.items():
            observed = invariants.get(invariant, {}).get(gate)
            if observed != expected:
                mismatches.append({"invariant": invariant, "gate": gate, "expected": expected, "observed": observed})
    passed = not mismatches and observed_heads == EXACT_GATE_HEADS
    return {
        "schema": "JEPA_TD_SEALED_CROSS_GATE_BATTERY_RECEIPT_V3",
        "status": "PASS_SEALED_CROSS_GATE_BATTERY_V3" if passed else "FAIL_SEALED_CROSS_GATE_BATTERY_V3",
        "exact_gate_heads": dict(EXACT_GATE_HEADS),
        "observed_gate_heads": observed_heads,
        "invariants": invariants,
        "mismatches": mismatches,
        "human_candidate_outcomes_used": False,
        "human_thresholds_imported": False,
        "synthetic_results_have_biological_authority": False,
        "authority": dict(_NO_AUTHORITY),
    }


def run_exam() -> dict:
    return copy.deepcopy(_cached())
