"""Sealed cross-gate system exam V3 after Macha hostile-review repairs.

V3 has two layers:
1. replay the already-sealed V2 cross-gate worlds against the new exact repair
   heads, using only the historical diagnostic paths that remain present; and
2. exercise prospectively frozen repair traps that assert the new fail-closed
   human-authority boundaries discovered by the independent real-data review.

Synthetic results are test-of-test evidence only. They never set human
thresholds or create target/representation/training authority.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import scripts.v5.td_sealed_cross_gate_battery_v2 as V2


class SealedBatteryV3Error(RuntimeError):
    pass


EXACT_GATE_HEADS = {
    "R1": "949d76ff03cb57c5a88fef9efdb79fced9154024",
    "G6": "4110d4478c3353d86740dd135d62460ff7a7611f",
    "G7": "5a711f9a4ea0328445a05dadc1e011efb16a3c13",
    "G9": "8d6b23a18051f64463ee9b2649f4fe5fc7123f0d",
    "G2": "42df903d6190b7aa1b8eb65d810ab813cd327445",
    "G8": "95dd474a02ce571722df9e8f08b42e81af2e8736",
    "INCREMENT": "b7c317c640aa231a7d5ec1fa12271a39bfee86e6",
}

_ROOT_ENV = {
    "R1": "TD_BATTERY_R1_ROOT",
    "G6": "TD_BATTERY_G6_ROOT",
    "G7": "TD_BATTERY_G7_ROOT",
    "G9": "TD_BATTERY_G9_ROOT",
    "G2": "TD_BATTERY_G2_ROOT",
    "G8": "TD_BATTERY_G8_ROOT",
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

_REPAIR_EXPECTED = {
    "G8_REFERENCE_GENERATION": "BLOCKED_G8_STATISTICAL_CONTRACT_NOT_QUALIFIED",
    "G6_ZERO_MARGIN": "NOT_ESTIMABLE_SUBSTANTIVE_MARGIN",
    "G6_TYPED_QUALIFICATION": "BLOCKED_G6_PRODUCED_QUALIFICATION_RECEIPT_REQUIRED",
    "GEOMETRY_TYPED_PRODUCER": "BLOCKED_GEOMETRY_PRODUCER_NOT_INDEPENDENTLY_QUALIFIED",
    "GEOMETRY_NULL_NE_STABILITY_FAIL": "FAIL",
    "R1_MECHANICS_KNOWN_TRUTH": "PASS_R1_V3_MECHANICS_KNOWN_TRUTH",
    "R1_TYPED_PRODUCER": "BLOCKED_R1_CELL_IDENTITY_NULL_PRODUCER_NOT_QUALIFIED",
    "G2_NINE_OF_TEN_POSITIVE": "NOT_ESTIMABLE",
    "G2_TYPED_POLICY": "BLOCKED_G2_STATIC_POLICY_NOT_PRODUCED_AND_QUALIFIED",
}


def world_manifest() -> dict:
    return {
        "schema": "JEPA_TD_SEALED_CROSS_GATE_BATTERY_V3",
        "status": "SEALED_BEFORE_EXECUTION__MACHA_REPAIR_REQUALIFICATION__SYNTHETIC_TEST_OF_TEST_ONLY",
        "sealed_before_execution": True,
        "seed_namespace": "TD_SEALED_CROSS_GATE_V3_MACHA_REPAIRS_20261014",
        "legacy_world_manifest": V2.world_manifest()["worlds"],
        "legacy_expected_statuses": V2.world_manifest()["expected_statuses"],
        "repair_expected_statuses": dict(_REPAIR_EXPECTED),
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
    expected = EXACT_GATE_HEADS[gate]
    if observed != expected:
        raise SealedBatteryV3Error(f"exact head mismatch for {gate}: expected {expected}, observed {observed}")
    return observed


def _run_python(gate: str, code: str) -> dict:
    root = _root(gate)
    _verify_head(gate, root)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    proc = subprocess.run([sys.executable, "-c", code], cwd=root, env=env, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise SealedBatteryV3Error(f"{gate} repair adapter failed with exit {proc.returncode}: {proc.stderr.strip()}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SealedBatteryV3Error(f"{gate} adapter did not emit canonical JSON: {proc.stdout!r}") from exc


def _legacy_v2_receipt() -> dict:
    """Replay V2's sealed worlds against the new exact heads on unchanged diagnostic paths."""
    legacy_heads = {gate: head for gate, head in EXACT_GATE_HEADS.items() if gate != "G8"}
    old = dict(V2.EXACT_GATE_HEADS)
    try:
        V2.EXACT_GATE_HEADS.clear()
        V2.EXACT_GATE_HEADS.update(legacy_heads)
        V2._run_exam_cached.cache_clear()
        return V2.run_exam()
    finally:
        V2._run_exam_cached.cache_clear()
        V2.EXACT_GATE_HEADS.clear()
        V2.EXACT_GATE_HEADS.update(old)


def _g8_traps() -> dict:
    return _run_python("G8", r'''
import json
import scripts.v5.td_real_g8_realization_contract_v3 as G
out=G.reference_generation_readiness(
 observation_thinning_schema="JEPA_TD_REAL_MEASUREMENT_THINNING_V2",
 exact_input_bound=True,metric_contract_bound=True,support_contract_bound=True,
 technical_draws_available=599)
print(json.dumps({"G8_REFERENCE_GENERATION":out["status"]},sort_keys=True))
''')


def _g6_traps() -> dict:
    return _run_python("G6", r'''
import json
import scripts.v5.td_real_teacher_information_decision_v3 as G
base={"schema":G.REFERENCE_SCHEMA,"frozen":True,"qualified":True,"metric":G.METRIC,
"orientation":G.ORIENTATION,"reference_kind":"U_REFIT","input_binding_sha256":"a"*64,
"reference_receipt_sha256":"b"*64,"producer_code_sha256":"c"*64,
"measurement_component_present":False,"measurement_component_non_degenerate":False,
"donor_margins":{"D00":0.0,"D01":0.0}}
zero=G.validate_reference_for_future_human_use(base)["status"]
good=dict(base); good.update({"reference_kind":"U_MEASUREMENT","measurement_component_present":True,
"measurement_component_non_degenerate":True,"donor_margins":{"D00":.2,"D01":.3}})
typed=G.human_execution_readiness(probe_qualification={"status":"PASS"},decision_qualification={"status":"PASS"},reference_artifact=good)["status"]
print(json.dumps({"G6_ZERO_MARGIN":zero,"G6_TYPED_QUALIFICATION":typed},sort_keys=True))
''')


def _geometry_traps() -> dict:
    return _run_python("G9", r'''
import json
import scripts.v5.td_real_geometry_recurrence_engine_v1 as V1
import scripts.v5.td_real_geometry_recurrence_engine_v2 as G
B="a"*64

def nulls(n): return [.8]*n
def row(i,n):
 return {"source":"SEA_AD","donor_id":f"D{i:02d}","estimability_status":V1.ESTIMABLE,
 "estimability_reason":None,"observed_displacement":.5,"null_displacements":nulls(n),
 "null_semantics":V1.NULL_SEMANTICS,"null_producer_receipt_sha256":"c"*64,"input_binding_sha256":B}
rows=[row(i,99 if i==0 else 100) for i in range(8)]
ref={"schema":V1.REFERENCE_SCHEMA,"frozen":True,"qualified":True,"metric":V1.PROJECTOR_METRIC,
"orientation":V1.ORIENTATION,"deciding_namespace_disjoint":True,"input_binding_sha256":B,
"reference_receipt_sha256":"b"*64,"refit_margins":{r["donor_id"]:.05 for r in rows},
"stability_margins":{r["donor_id"]:.2 for r in rows}}
mechanic=G.adjudicate_geometry_mechanics_v2(rows=rows,metric=V1.PROJECTOR_METRIC,
 required_sources=["SEA_AD"],reference_artifact=ref,alpha=.01)["status"]
typed=G.human_execution_readiness(producer_receipt={"schema":"X","qualified":True})["status"]
print(json.dumps({"GEOMETRY_TYPED_PRODUCER":typed,"GEOMETRY_NULL_NE_STABILITY_FAIL":mechanic},sort_keys=True))
''')


def _r1_traps() -> dict:
    return _run_python("R1", r'''
import json
import scripts.v5.td_real_r1_executor_v3 as R
q=R.qualify_r1_v3_mechanics()["status"]
typed=R.human_execution_readiness(producer_receipt={"schema":"R1_PRODUCER","qualified":True})["status"]
print(json.dumps({"R1_MECHANICS_KNOWN_TRUTH":q,"R1_TYPED_PRODUCER":typed},sort_keys=True))
''')


def _g2_traps() -> dict:
    return _run_python("G2", r'''
import json
import scripts.v5.td_real_g2_content_decision_v2 as G
B="a"*64
rows=[]
for i,delta in enumerate([1.0]*9+[-1.0]):
 rows.append({"source":"SEA_AD","endpoint":"PRIMARY","donor_id":f"D{i:02d}",
 "candidate_score":1.0+delta,"baseline_scores":{"B0":0.0,"B1":0.0},
 "support_state":"SUPPORTED","input_binding_sha256":B})
ref={"schema":G.REFERENCE_SCHEMA,"frozen":True,"qualified":True,"metric":G.METRIC,
"orientation":G.ORIENTATION,"reference_kind":"U_MEASUREMENT","input_binding_sha256":B,
"reference_receipt_sha256":"b"*64,"producer_code_sha256":"c"*64,
"margins":{f'SEA_AD::PRIMARY::D{i:02d}':1.0 for i in range(10)}}
status=G.adjudicate_g2_mechanics_v2(rows=rows,required_strata=[("SEA_AD","PRIMARY")],
 diagnostic_baseline_ids=["B0","B1"],reference_artifact=ref)["status"]
typed=G.human_execution_readiness(policy_artifact={"schema":"X","qualified":True})["status"]
print(json.dumps({"G2_NINE_OF_TEN_POSITIVE":status,"G2_TYPED_POLICY":typed},sort_keys=True))
''')


@lru_cache(maxsize=1)
def _run_exam_cached() -> dict:
    observed_heads = {gate: _verify_head(gate, _root(gate)) for gate in EXACT_GATE_HEADS}
    legacy = _legacy_v2_receipt()
    traps: dict[str, str] = {}
    for result in (_g8_traps(), _g6_traps(), _geometry_traps(), _r1_traps(), _g2_traps()):
        traps.update(result)
    repair_mismatches = [
        {"trap": key, "expected": expected, "observed": traps.get(key)}
        for key, expected in _REPAIR_EXPECTED.items() if traps.get(key) != expected
    ]
    legacy_ok = bool(legacy.get("all_expectations_met"))
    heads_ok = observed_heads == EXACT_GATE_HEADS
    passed = legacy_ok and not repair_mismatches and heads_ok
    return {
        "schema": "JEPA_TD_SEALED_CROSS_GATE_BATTERY_RECEIPT_V3",
        "status": "PASS_SEALED_CROSS_GATE_BATTERY_V3" if passed else "FAIL_SEALED_CROSS_GATE_BATTERY_V3",
        "all_expectations_met": bool(passed),
        "exact_gate_heads": dict(EXACT_GATE_HEADS),
        "observed_gate_heads": observed_heads,
        "legacy_worlds_all_expectations_met": legacy_ok,
        "legacy_world_mismatches": copy.deepcopy(legacy.get("mismatches", [])),
        "repair_traps": traps,
        "repair_mismatches": repair_mismatches,
        "human_candidate_outcomes_used": False,
        "human_thresholds_imported": False,
        "synthetic_results_have_biological_authority": False,
        "authority": dict(_NO_AUTHORITY),
    }


def run_exam() -> dict:
    return copy.deepcopy(_run_exam_cached())
