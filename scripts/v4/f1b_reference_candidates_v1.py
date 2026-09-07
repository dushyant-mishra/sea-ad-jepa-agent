#!/usr/bin/env python3
"""Reference candidates that prove each F1-B attack discriminates.

`ReferenceVulnerable` reproduces the historical defect for each covered finding.
`ReferenceCorrect` implements the repaired behaviour. Every attack must report
VULNERABLE on the first and DEFENDED on the second; an attack that fails either
half is not evidence and is flagged ATTACK_DEFECTIVE.

These are deliberately small and self-contained. They are QA fixtures, not
successor implementations, and nothing here is a training path.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from scripts.v4.f1b_successor_attack_suite_v1 import Candidate

# Prospectively registered gate-bearing endpoints. `recurrent_5pct` and
# `recurrent_1pct` are deliberately absent: they are duplicated rare directions
# and are not authorised main-F1 endpoints.
REGISTERED_ENDPOINTS = ("l2__broad_common", "l2__local")


# ---------------------------------------------------------------- vulnerable
def _vuln_gate(payload: Mapping[str, Any]) -> dict:
    """Historical defect: only backbone tensors are gated."""
    backbone = payload.get("backbone", {})
    dead = [k for k, v in backbone.items() if float(v) == 0.0]
    if dead:
        raise RuntimeError("dead backbone tensors: " + str(dead))
    return {"checked": sorted(backbone)}


def _vuln_routing(weights: Sequence[Sequence[float]], valid: Sequence[int]) -> list[float]:
    """Historical defect: every cell normalised by cell 0's support."""
    support0 = int(valid[0])
    out = []
    for row in weights:
        w = [max(float(x), 0.0) for x in row[:support0]]
        total = sum(w) or 1.0
        p = [x / total for x in w]
        entropy = -sum(x * math.log(x + 1e-30) for x in p)
        out.append(math.exp(entropy))
    return out


def _vuln_update(payload: Mapping[str, Any]) -> dict:
    """Historical defect: step first, then report the violation."""
    ledger = payload["ledger"]
    ledger["stepped"] = True
    ledger["optimizer_state_entries"] = len(payload["mandatory_gradients"])
    dead = [k for k, v in payload["mandatory_gradients"].items() if float(v) == 0.0]
    if dead:
        raise RuntimeError("dead mandatory gradients (after step): " + str(dead))
    return {"stepped": True}


def _vuln_select(keys: Sequence[str]) -> list[str]:
    """Historical defect: every `l2__` key becomes an endpoint."""
    return [k for k in keys if k.startswith("l2__")]


# ------------------------------------------------------------------ correct
def _ok_gate(payload: Mapping[str, Any]) -> dict:
    """Backbone and predictor are both mandatory."""
    protected = dict(payload.get("backbone", {}))
    protected.update(payload.get("predictor", {}))
    if not protected:
        raise RuntimeError("no protected tensors supplied")
    dead = [k for k, v in protected.items() if float(v) == 0.0]
    if dead:
        raise RuntimeError("dead mandatory tensors: " + str(dead))
    return {"checked": sorted(protected)}


def _ok_routing(weights: Sequence[Sequence[float]], valid: Sequence[int]) -> list[float]:
    """Each cell normalised by its own valid-key count."""
    if len(weights) != len(valid):
        raise RuntimeError("per-cell support count mismatch")
    out = []
    for row, support in zip(weights, valid):
        support = int(support)
        if support <= 0:
            raise RuntimeError("non-positive per-cell support")
        w = [max(float(x), 0.0) for x in row[:support]]
        total = sum(w) or 1.0
        p = [x / total for x in w]
        entropy = -sum(x * math.log(x + 1e-30) for x in p)
        out.append(math.exp(entropy))
    return out


def _ok_update(payload: Mapping[str, Any]) -> dict:
    """Gate before the step. The optimizer is never touched on refusal."""
    dead = [k for k, v in payload["mandatory_gradients"].items() if float(v) == 0.0]
    if dead:
        raise RuntimeError("dead mandatory gradients (before step): " + str(dead))
    ledger = payload["ledger"]
    ledger["stepped"] = True
    ledger["optimizer_state_entries"] = len(payload["mandatory_gradients"])
    return {"stepped": True}


def _ok_select(keys: Sequence[str]) -> list[str]:
    """Only prospectively registered endpoints, and every one must be present."""
    missing = [k for k in REGISTERED_ENDPOINTS if k not in set(keys)]
    if missing:
        raise RuntimeError("registered endpoint absent from authority: " + str(missing))
    return [k for k in keys if k in REGISTERED_ENDPOINTS]


def reference_vulnerable() -> Candidate:
    return Candidate(
        name="ReferenceVulnerable",
        gate_mandatory_gradients=_vuln_gate,
        routing_report=_vuln_routing,
        protected_update=_vuln_update,
        select_endpoints=_vuln_select,
        metadata={"role": "reproduces the historical defect for each covered finding"},
    )


def reference_correct() -> Candidate:
    return Candidate(
        name="ReferenceCorrect",
        gate_mandatory_gradients=_ok_gate,
        routing_report=_ok_routing,
        protected_update=_ok_update,
        select_endpoints=_ok_select,
        metadata={"role": "repaired behaviour for each covered finding"},
    )


def reference_empty() -> Candidate:
    """Exposes nothing. Must yield NOT_APPLICABLE everywhere, never a pass."""
    return Candidate(name="ReferenceEmpty",
                     metadata={"role": "absent machinery must not read as compliance"})
