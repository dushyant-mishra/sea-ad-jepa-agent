#!/usr/bin/env python3
"""Reference candidates that prove each F1-B attack discriminates.

`reference_vulnerable()` reproduces the historical defect for every covered
finding and MUST come back VULNERABLE on every attack.
`reference_correct()` implements the repaired behaviour and MUST come back
DEFENDED on every attack.
`reference_empty()` exposes nothing and must yield NOT_APPLICABLE everywhere,
which the suite treats as a STOP rather than a pass.

These are QA fixtures, deliberately small and self-contained. None is a
successor implementation and none is a training path.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from scripts.v4.f1b_successor_attack_suite_v1 import Candidate

# Prospectively registered gate-bearing endpoints. `recurrent_5pct` and
# `recurrent_1pct` are deliberately absent: duplicated rare directions are not
# authorised main-F1 endpoints.
REGISTERED_ENDPOINTS = ("l2__broad_common", "l2__local")
FROZEN_UPDATES = 40
MOVEMENT_MARGIN = 1.5


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


# ============================== vulnerable ==============================
def _vuln_gate(payload: Mapping[str, Any]) -> dict:
    """Historical defect: backbone only, norm==0 only, moments ignored."""
    backbone = payload.get("backbone", {})
    dead = [k for k, v in backbone.items() if _finite(v) and float(v) == 0.0]
    if dead:
        raise RuntimeError("dead backbone tensors: " + str(dead))
    return {"checked": sorted(backbone)}


def _vuln_movement(payload: Mapping[str, Any]) -> dict:
    """Historical defect: gate the MEAN relative movement across tensors."""
    rel = payload["relative_movement"]
    values = [float(v) for v in rel.values() if _finite(v)]
    mean = sum(values) / len(values) if values else 0.0
    if mean <= float(payload["decay_only_prediction"]) * MOVEMENT_MARGIN:
        raise RuntimeError("pooled movement below decay")
    return {"pooled_mean": mean}


def _vuln_routing(weights: Sequence[Sequence[float]], valid: Sequence[int]) -> list[float]:
    """Historical defect: every cell normalised by cell 0's support."""
    support0 = int(valid[0])
    out = []
    for row in weights:
        w = [max(float(x), 0.0) for x in row[:support0]]
        total = sum(w) or 1.0
        p = [x / total for x in w]
        out.append(math.exp(-sum(x * math.log(x + 1e-30) for x in p)))
    return out


def _vuln_routing_metrics(weights: Sequence[Sequence[float]],
                          masks: Sequence[Sequence[bool]]) -> dict:
    """Historical defect: ignore masks and reuse entropy support under both metric names."""
    entropy, top1, valid = [], [], []
    for row in weights:
        w = [max(float(x), 0.0) for x in row]
        total = sum(w) or 1.0
        p = [x / total for x in w]
        value = math.exp(-sum(x * math.log(x + 1e-30) for x in p))
        entropy.append(value)
        top1.append(max(p) if p else 0.0)
        valid.append(len(p))
    return {"N_eff_entropy": entropy,
            "N_eff_participation": list(entropy),
            "top1_mass": top1,
            "valid_keys": valid,
            "query_map_cosine": 1.0}

_VULN_CACHED_FIT = {"coefficients": [0.0, 0.0], "source": "cached"}


def _vuln_refit(payload: Mapping[str, Any]) -> dict:
    """Historical defect: cached probe reused regardless of checkpoint-specific fit split."""
    return {"predictions": [0.0 for _ in payload.get("eval_values", ())],
            "source": "cached"}

def _vuln_horizon(updates: int) -> dict:
    """Historical defect: the override is accepted."""
    return {"updates": int(updates)}


def _vuln_directional(obs: Mapping[str, float]) -> dict:
    """Historical defect: the structural claim is asserted regardless of controls."""
    return {"structural": True, "observed": float(obs["observed"])}


def _vuln_target_equivalence(single_q: Sequence[float], all_q: Sequence[float]) -> dict:
    """Historical defect: equivalence assumed rather than compared."""
    return {"equivalent": True}


def _vuln_amp(probe: Any) -> dict:
    """Historical defect: AMP semantics declared without executing anything."""
    return {"autocast_enabled": True, "scaler_enabled": True, "status": "declared"}


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


# ================================ correct ================================
def _ok_gate(payload: Mapping[str, Any]) -> dict:
    """Backbone and predictor both mandatory; missing, nonfinite, zero all reject.

    Adam moments, when supplied, are required independently: a live first moment
    must not mask a dead second.
    """
    protected = dict(payload.get("backbone", {}))
    protected.update(payload.get("predictor", {}))
    if not protected:
        raise RuntimeError("no protected tensors supplied")
    for name, value in protected.items():
        if value is None:
            raise RuntimeError("missing gradient: " + name)
        if not _finite(value):
            raise RuntimeError("nonfinite gradient: " + name)
        if float(value) == 0.0:
            raise RuntimeError("exactly-zero gradient: " + name)
    for name, moments in (payload.get("moments") or {}).items():
        for which in ("exp_avg", "exp_avg_sq"):
            value = moments.get(which)
            if value is None or not _finite(value) or float(value) == 0.0:
                raise RuntimeError("dead %s for %s" % (which, name))
    return {"checked": sorted(protected)}


def _ok_movement(payload: Mapping[str, Any]) -> dict:
    """Per tensor, never pooled. Zero baseline is judged on absolute movement."""
    decay = float(payload["decay_only_prediction"])
    rel = payload["relative_movement"]
    absolute = payload.get("absolute_movement", {})
    baseline = payload.get("baseline_norm", {})
    failing = []
    for name in rel:
        base = float(baseline.get(name, 1.0))
        if base == 0.0:
            # Decay scales the parameter, so an exactly-zero parameter stays
            # zero under decay alone: any movement is gradient-driven.
            if float(absolute.get(name, 0.0)) <= 0.0:
                failing.append(name)
            continue
        value = rel.get(name)
        if value is None or not _finite(value) or float(value) <= decay * MOVEMENT_MARGIN:
            failing.append(name)
    if failing:
        raise RuntimeError("tensors at or below decay-only movement: " + str(sorted(failing)))
    return {"checked": sorted(rel)}


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
        out.append(math.exp(-sum(x * math.log(x + 1e-30) for x in p)))
    return out


def _ok_routing_metrics(weights: Sequence[Sequence[float]],
                        masks: Sequence[Sequence[bool]]) -> dict:
    """Per-query routing telemetry: masks respected and metrics named distinctly."""
    if len(weights) != len(masks) or not weights:
        raise RuntimeError("query support mismatch")
    entropy, participation, top1, valid, full = [], [], [], [], []
    width = max(len(row) for row in weights)
    for row, mask in zip(weights, masks):
        if len(row) != len(mask):
            raise RuntimeError("weight/mask length mismatch")
        kept = [max(float(x), 0.0) for x, keep in zip(row, mask) if keep]
        if not kept:
            raise RuntimeError("no valid keys")
        total = sum(kept)
        if total <= 0.0:
            raise RuntimeError("zero routing mass")
        p = [x / total for x in kept]
        entropy.append(math.exp(-sum(x * math.log(x + 1e-30) for x in p)))
        participation.append(1.0 / sum(x * x for x in p))
        top1.append(max(p))
        valid.append(len(p))
        vec, j = [0.0] * width, 0
        for i, keep in enumerate(mask):
            if keep:
                vec[i] = p[j]
                j += 1
        full.append(vec)
    if len(full) < 2:
        qcos = 1.0
    else:
        cosines = []
        for i in range(len(full)):
            for j in range(i + 1, len(full)):
                dot = sum(a * b for a, b in zip(full[i], full[j]))
                ni = math.sqrt(sum(a * a for a in full[i]))
                nj = math.sqrt(sum(b * b for b in full[j]))
                cosines.append(dot / max(ni * nj, 1e-30))
        qcos = sum(cosines) / len(cosines)
    return {"N_eff_entropy": entropy,
            "N_eff_participation": participation,
            "top1_mass": top1,
            "valid_keys": valid,
            "query_map_cosine": qcos}

def _ok_refit(payload: Mapping[str, Any]) -> dict:
    """Deterministic donor-held-out synthetic refit used only as a mechanics probe."""
    fit_donors = list(payload.get("fit_donors", ()))
    eval_donors = list(payload.get("eval_donors", ()))
    fit_values = [float(x) for x in payload.get("fit_values", ())]
    eval_values = list(payload.get("eval_values", ()))
    if not fit_values or len(fit_donors) != len(fit_values):
        raise RuntimeError("invalid fit split")
    if set(fit_donors) & set(eval_donors):
        raise RuntimeError("fit/eval donor overlap")
    mean = sum(fit_values) / len(fit_values)
    return {"predictions": [mean for _ in eval_values],
            "fit_mean": mean,
            "fit_donors_used": fit_donors}

def _ok_horizon(updates: int) -> dict:
    """The frozen horizon is enforced, not merely defaulted."""
    if int(updates) != FROZEN_UPDATES:
        raise RuntimeError("frozen horizon is %d; refused %d" % (FROZEN_UPDATES, int(updates)))
    return {"updates": FROZEN_UPDATES}


def _ok_directional(obs: Mapping[str, float]) -> dict:
    """Withhold the structural claim when either control explains the effect."""
    observed = float(obs["observed"])
    cell_only = float(obs.get("cell_only_control", 0.0))
    identity_only = float(obs.get("identity_only_control", 0.0))
    explained = max(abs(cell_only), abs(identity_only)) >= 0.5 * abs(observed)
    return {"structural": not explained,
            "explained_by_control": explained,
            "note": "query-centering removes additive query-common components only"}


def _ok_target_equivalence(single_q: Sequence[float], all_q: Sequence[float]) -> dict:
    """Compare the two targets rather than assume they agree."""
    if len(single_q) != len(all_q):
        raise RuntimeError("target length mismatch")
    worst = max((abs(float(a) - float(b)) for a, b in zip(single_q, all_q)), default=0.0)
    return {"equivalent": worst <= 1e-9, "max_abs_difference": worst}


def _ok_amp(harness: Any) -> dict:
    """Execute the instrumented production-like AMP step in the required order."""
    with harness.autocast():
        harness.forward()
    harness.scaler_scale_backward()
    harness.scaler_unscale()
    harness.gradient_gate()
    harness.optimizer_step()
    harness.ema_step()
    return {"status": "executed"}

def _ok_update(payload: Mapping[str, Any]) -> dict:
    """Gate before the step. The optimizer is never touched on refusal."""
    dead = [k for k, v in payload["mandatory_gradients"].items()
            if not _finite(v) or float(v) == 0.0]
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


# =============================== factories ===============================
def reference_vulnerable() -> Candidate:
    return Candidate(
        name="ReferenceVulnerable",
        gate_mandatory_gradients=_vuln_gate,
        movement_gate=_vuln_movement,
        routing_report=_vuln_routing,
        routing_metrics=_vuln_routing_metrics,
        refit=_vuln_refit,
        frozen_horizon=_vuln_horizon,
        directional_claim=_vuln_directional,
        target_equivalence=_vuln_target_equivalence,
        amp_smoke=_vuln_amp,
        protected_update=_vuln_update,
        select_endpoints=_vuln_select,
        metadata={"role": "reproduces the historical defect for every covered finding"},
    )


def reference_correct() -> Candidate:
    return Candidate(
        name="ReferenceCorrect",
        gate_mandatory_gradients=_ok_gate,
        movement_gate=_ok_movement,
        routing_report=_ok_routing,
        routing_metrics=_ok_routing_metrics,
        refit=_ok_refit,
        frozen_horizon=_ok_horizon,
        directional_claim=_ok_directional,
        target_equivalence=_ok_target_equivalence,
        amp_smoke=_ok_amp,
        protected_update=_ok_update,
        select_endpoints=_ok_select,
        metadata={"role": "repaired behaviour for every covered finding"},
    )


def reference_empty() -> Candidate:
    """Exposes nothing. Must yield NOT_APPLICABLE everywhere, never a pass."""
    return Candidate(name="ReferenceEmpty",
                     metadata={"role": "absent machinery must not read as compliance"})
