"""Sealed cross-gate known-truth exam V2 after G7 source-noncompensation repair.

V2 preserves the V1 sealed world definitions and all exact non-G7 gate heads.
Only the G7 adapter/head changes: it exercises G7 V3 with explicit required-source
noncompensation. Synthetic outcomes remain test-of-test only and carry no human
biological threshold or execution authority.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import scripts.v5.td_sealed_cross_gate_battery_v1 as V1


class SealedBatteryV2Error(RuntimeError):
    pass


EXACT_GATE_HEADS = dict(V1.EXACT_GATE_HEADS)
EXACT_GATE_HEADS["G7"] = "5a711f9a4ea0328445a05dadc1e011efb16a3c13"

_ROOT_ENV = dict(V1._ROOT_ENV)
_NO_AUTHORITY = dict(V1._NO_AUTHORITY)
_WORLDS = copy.deepcopy(V1._WORLDS)
_EXPECTED = copy.deepcopy(V1._EXPECTED)
_EXPECTED["SOURCE_ASYMMETRY"]["G7"] = "NOT_ESTIMABLE"


def world_manifest() -> dict:
    return {
        "schema": "JEPA_TD_SEALED_CROSS_GATE_BATTERY_V2",
        "status": "SEALED_BEFORE_EXECUTION__G7_V3_REQUALIFICATION__SYNTHETIC_TEST_OF_TEST_ONLY",
        "sealed_before_execution": True,
        "seed_namespace": "TD_SEALED_CROSS_GATE_V2_G7V3_20261014",
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
        raise SealedBatteryV2Error(f"missing exact-tree root for {gate}")
    root = Path(raw)
    if not root.is_dir():
        raise SealedBatteryV2Error(f"exact-tree root for {gate} does not exist: {root}")
    return root


def _verify_head(gate: str, root: Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False,
    )
    if proc.returncode != 0:
        raise SealedBatteryV2Error(f"cannot resolve exact head for {gate}: {proc.stderr.strip()}")
    observed = proc.stdout.strip()
    expected = EXACT_GATE_HEADS[gate]
    if observed != expected:
        raise SealedBatteryV2Error(
            f"exact head mismatch for {gate}: expected {expected}, observed {observed}"
        )
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
        raise SealedBatteryV2Error(
            f"{gate} sealed adapter failed with exit {proc.returncode}: {proc.stderr.strip()}"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SealedBatteryV2Error(
            f"{gate} adapter did not emit canonical JSON: {proc.stdout!r}"
        ) from exc


def _run_v1_adapter(gate: str, function_name: str) -> dict:
    """Run an unchanged V1 adapter while binding V1's verifier to the V2 exact heads.

    Each adapter still executes inside its own exact repository tree/subprocess. The
    temporary module-level head substitution is local to this controller process and
    is restored immediately; only G7 differs between V1 and V2 in any case.
    """
    old = dict(V1.EXACT_GATE_HEADS)
    try:
        V1.EXACT_GATE_HEADS.clear()
        V1.EXACT_GATE_HEADS.update(EXACT_GATE_HEADS)
        return getattr(V1, function_name)()
    finally:
        V1.EXACT_GATE_HEADS.clear()
        V1.EXACT_GATE_HEADS.update(old)


def _g7_results() -> dict:
    return _run_python("G7", r'''
import json
import scripts.v5.td_real_g7_terminal_decision_v3 as G
B="1"*64

def qual():
    return {"schema":G.QUAL_SCHEMA,"status":G.QUAL_PASS,"known_truth_power_qualified":True}

def rows(source,n,disp,added):
    return [{"source":source,"donor_id":f"{source}_D{i:02d}","terminal_displacement":float(disp),
             "penultimate_supported_evidence":10,"full_supported_evidence":10+added,
             "added_supported_evidence":added,"input_binding_sha256":B} for i in range(n)]

def unit(r): return f'{r["source"]}::{r["donor_id"]}'

def ref(rs,margin=.1):
    return {"schema":G.REFERENCE_SCHEMA,"frozen":True,"qualified":True,"metric":G.METRIC,
            "orientation":G.ORIENTATION,"reference_kind":"U_REFIT","deciding_namespace_disjoint":True,
            "input_binding_sha256":B,"reference_receipt_sha256":"2"*64,
            "unit_margins":{unit(r):margin for r in rs}}

def dec(rs,sources):
    return G.adjudicate_g7_terminal_v3(rows=rs,required_sources=sources,
        decision_qualification=qual(),reference_artifact=ref(rs),alpha=.01)["status"]

sparse=rows("SEA_AD",7,.02,1)
none=rows("SEA_AD",8,0.0,0)
asym=rows("SEA_AD",8,.02,1)+rows("HVS",7,.02,1)
out={
    "SPARSE_SUPPORT":dec(sparse,["SEA_AD"]),
    "NO_ADDED_EVIDENCE":dec(none,["SEA_AD"]),
    "SOURCE_ASYMMETRY":dec(asym,["SEA_AD","HVS"]),
}
print(json.dumps(out,sort_keys=True))
''')


@lru_cache(maxsize=1)
def _run_exam_cached() -> dict:
    observed_heads = {gate: _verify_head(gate, _root(gate)) for gate in EXACT_GATE_HEADS}
    gate_outputs = {
        "R1": _run_v1_adapter("R1", "_r1_results"),
        "G6": _run_v1_adapter("G6", "_g6_results"),
        "G7": _g7_results(),
        "G9": _run_v1_adapter("G9", "_g9_results"),
        "G2": _run_v1_adapter("G2", "_g2_results"),
        "INCREMENT": _run_v1_adapter("INCREMENT", "_increment_results"),
    }
    world_results: dict[str, dict[str, str]] = {w["name"]: {} for w in _WORLDS}
    for world, status in gate_outputs["R1"].items():
        world_results[world]["R1"] = status
    for world, status in gate_outputs["G6"].items():
        world_results[world]["G6"] = status
    for world, status in gate_outputs["G7"].items():
        world_results[world]["G7"] = status
    for world, status in gate_outputs["G9"].items():
        world_results[world]["G9"] = status
    for world, status in gate_outputs["G2"].items():
        world_results[world]["G2"] = status
    for world, status in gate_outputs["INCREMENT"].items():
        label = "C6" if world == "C6_PARTIAL_INCREMENT" else "R4"
        world_results[world][label] = status

    mismatches = []
    for world, expected_gate_statuses in _EXPECTED.items():
        for gate, expected in expected_gate_statuses.items():
            observed = world_results.get(world, {}).get(gate)
            if observed != expected:
                mismatches.append(
                    {"world": world, "gate": gate, "expected": expected, "observed": observed}
                )
    passed = not mismatches and observed_heads == EXACT_GATE_HEADS
    return {
        "schema": "JEPA_TD_SEALED_CROSS_GATE_BATTERY_RECEIPT_V2",
        "status": "PASS_SEALED_CROSS_GATE_BATTERY_V2" if passed else "FAIL_SEALED_CROSS_GATE_BATTERY_V2",
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
