#!/usr/bin/env python3
"""Controller-only V79 V2_CORE scoring boundary.

This module may consume controller truth only after a frozen qualification campaign.
No fit-side module imports it.
"""
from __future__ import annotations

from collections import Counter
from typing import Mapping

import v79_v2_core_launch as L


class ScoreRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise ScoreRefused(f"REFUSED V2_CORE scorer: {msg}")


def gate_authority(contract: Mapping) -> dict:
    try:
        L.validate_launch_semantics(dict(contract))
    except Exception as exc:
        _refuse(f"contract is not frozen launch authority: {exc}")
    gates=list(contract["gates"]["list"])
    counts={
        "hard_statistical":sum(g["kind"]=="STAT" and g["verdict_class"]=="FAIL" for g in gates),
        "hard_rule":sum(g["kind"]=="RULE" and g["verdict_class"]=="FAIL" for g in gates),
        "limit_statistical":sum(g["kind"]=="STAT" and g["verdict_class"]=="LIMIT" for g in gates),
        "limit_rule":sum(g["kind"]=="RULE" and g["verdict_class"]=="LIMIT" for g in gates),
    }
    limits=[g for g in gates if g["verdict_class"]=="LIMIT"]
    if counts != {"hard_statistical":260,"hard_rule":28,"limit_statistical":4,"limit_rule":0}:
        _refuse(f"gate counts differ: {counts}")
    if len(limits)!=4 or any(g["verdict_class"]!="FAIL" for g in gates if g["world"]=="Q11_OMITTED_OPERATOR"):
        _refuse("LIMIT/Q11 authority differs")
    return {"gates":gates,"counts":counts,"limit_gates":limits,
            "alpha_per_gate":contract["gates"]["multiplicity"]["alpha_per_gate"]}


def require_complete_campaign(contract: Mapping, fit_receipts: list[Mapping]) -> list[Mapping]:
    want=int(contract.get("resources",{}).get("estimate",{}).get("n_fits",-1))
    if len(fit_receipts)!=want:
        _refuse(f"campaign has {len(fit_receipts)} fit receipts, requires {want}")
    ids=[]
    for r in fit_receipts:
        if r.get("schema")!="V79_V2_CORE_FIT_RECORD_V1" or r.get("execution_mode")!="QUALIFICATION":
            _refuse("non-qualification fit record in campaign")
        if r.get("contract_sha256")!=L.FINAL_CONTRACT_SHA256 or r.get("truth_accessed") is not False or r.get("scoring_run") is not False:
            _refuse("fit record authority/firewall mismatch")
        ids.append(r.get("fit_id"))
    if len(set(ids))!=want: _refuse("duplicate/missing fit identity")
    return fit_receipts


def terminal_from_gate_results(contract: Mapping, gate_results: list[Mapping]) -> dict:
    t=contract.get("terminal_logic",{})
    post_label=t.get("post_terminal_label")
    if post_label!=L.POST_TERMINAL_LABEL: _refuse("terminal post-fail label differs")
    first=None
    for i,r in enumerate(gate_results):
        if r.get("verdict_class")=="FAIL" and r.get("passed") is False:
            first=i; break
    if first is None:
        return {"terminal":"V2_CORE_SYNTHETIC_QUALIFICATION_QUALIFIED","first_hard_fail_index":None,
                "post_terminal_count":0,"limit_failures":sum(r.get("verdict_class")=="LIMIT" and r.get("passed") is False for r in gate_results)}
    return {"terminal":"V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED","first_hard_fail_index":first,
            "post_terminal_count":len(gate_results)-first-1,
            "post_terminal_label":post_label,
            "limit_failures":sum(r.get("verdict_class")=="LIMIT" and r.get("passed") is False for r in gate_results)}


def bind_gate_evaluations(contract: Mapping, evaluations: list[Mapping]) -> dict:
    """Bind externally computed statistics to every frozen gate; thresholds/classes may not be replaced."""
    auth=gate_authority(contract); gates=auth["gates"]
    key=lambda g:(g["world"],g["part"],g["gate"])
    expected={key(g):g for g in gates}; observed={key(e):e for e in evaluations}
    if set(observed)!=set(expected):
        _refuse("gate evaluation keys do not exactly match frozen gate list")
    rows=[]
    for g in gates:
        e=observed[key(g)]
        if not isinstance(e.get("passed"),bool): _refuse(f"gate {key(g)} lacks boolean passed")
        row={"world":g["world"],"part":g["part"],"gate":g["gate"],"kind":g["kind"],
             "verdict_class":g["verdict_class"],"passed":e["passed"],
             "statistic":e.get("statistic"),"detail":e.get("detail"),"frozen_gate":g}
        rows.append(row)
    return {"schema":"V79_V2_CORE_GATE_SCORE_TABLE_V1","rows":rows,"terminal":terminal_from_gate_results(contract,rows),
            "counts":auth["counts"],"alpha_per_gate":auth["alpha_per_gate"]}
