"""Canonical non-training mechanics diagnostics for the unified teacher/student line.

These helpers are the surviving behavioral seams from the reviewed F1-B/C3
mechanics prototype. They are intentionally data-blind and make no biological
claim. Keeping them under src/sea_ad_jepa/v4 removes the last active runtime
dependency on the retired C3 prototype while preserving identical semantics for
the frozen behavioral attack authority.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

FROZEN_QUALIFICATION_UPDATES = 40
REGISTERED_G5_ENDPOINTS = ("l2__broad_common", "l2__local")


def routing_report(
    weights: Sequence[Sequence[float]],
    valid_support: Sequence[int],
) -> list[float]:
    """Entropy effective support, independently normalized for every cell."""
    if len(weights) != len(valid_support):
        raise RuntimeError("per-cell routing/support length mismatch")
    out: list[float] = []
    for row, support in zip(weights, valid_support):
        support = int(support)
        if support <= 0 or support > len(row):
            raise RuntimeError("invalid per-cell support")
        mass = [max(float(x), 0.0) for x in row[:support]]
        total = sum(mass)
        if total <= 0.0:
            raise RuntimeError("zero routing mass")
        p = [x / total for x in mass]
        out.append(math.exp(-sum(x * math.log(x + 1e-30) for x in p)))
    return out


def routing_metrics(
    weights: Sequence[Sequence[float]],
    masks: Sequence[Sequence[bool]],
) -> dict[str, Any]:
    """Mask-respecting entropy and participation effective support."""
    if len(weights) != len(masks) or not weights:
        raise RuntimeError("query support mismatch")
    width = max(len(row) for row in weights)
    entropy: list[float] = []
    participation: list[float] = []
    top1: list[float] = []
    valid_keys: list[int] = []
    full: list[list[float]] = []

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
        valid_keys.append(len(p))

        vector = [0.0] * width
        j = 0
        for index, keep in enumerate(mask):
            if keep:
                vector[index] = p[j]
                j += 1
        full.append(vector)

    if len(full) == 1:
        query_map_cosine = 1.0
    else:
        cosines: list[float] = []
        for i in range(len(full)):
            for j in range(i + 1, len(full)):
                dot = sum(a * b for a, b in zip(full[i], full[j]))
                ni = math.sqrt(sum(a * a for a in full[i]))
                nj = math.sqrt(sum(b * b for b in full[j]))
                cosines.append(dot / max(ni * nj, 1e-30))
        query_map_cosine = sum(cosines) / len(cosines)

    return {
        "N_eff_entropy": entropy,
        "N_eff_participation": participation,
        "top1_mass": top1,
        "valid_keys": valid_keys,
        "query_map_cosine": query_map_cosine,
    }


def refit_g5_probe(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Deterministic donor-held-out refit mechanic; no biological G5 claim."""
    fit_donors = list(payload.get("fit_donors") or ())
    eval_donors = list(payload.get("eval_donors") or ())
    fit_values = [float(x) for x in payload.get("fit_values") or ()]
    eval_values = list(payload.get("eval_values") or ())
    if not fit_values or len(fit_values) != len(fit_donors):
        raise RuntimeError("invalid fit split")
    if set(fit_donors) & set(eval_donors):
        raise RuntimeError("fit/eval donor overlap")
    fitted_mean = sum(fit_values) / len(fit_values)
    return {
        "predictions": [fitted_mean for _ in eval_values],
        "fit_mean": fitted_mean,
        "fit_donors_used": fit_donors,
    }


def enforce_frozen_horizon(updates: int) -> dict[str, int]:
    updates = int(updates)
    if updates != FROZEN_QUALIFICATION_UPDATES:
        raise RuntimeError(
            "frozen qualification horizon is %d; refused %d"
            % (FROZEN_QUALIFICATION_UPDATES, updates)
        )
    return {"updates": FROZEN_QUALIFICATION_UPDATES}


def directional_claim(payload: Mapping[str, float]) -> dict[str, Any]:
    """Withhold structural claim when CELL-only or identity-only explains it."""
    observed = float(payload["observed"])
    cell = float(payload.get("cell_only_control", 0.0))
    identity = float(payload.get("identity_only_control", 0.0))
    explained = max(abs(cell), abs(identity)) >= 0.5 * abs(observed)
    return {
        "structural": not explained,
        "explained_by_control": explained,
        "claim_scope": (
            "query-local structure remains after both controls"
            if not explained
            else "structural claim withheld because a restricted control explains the effect"
        ),
    }


def target_equivalence(
    singleton_q: Sequence[float],
    all_q: Sequence[float],
) -> dict[str, Any]:
    if len(singleton_q) != len(all_q):
        raise RuntimeError("target length mismatch")
    worst = max(
        (abs(float(a) - float(b)) for a, b in zip(singleton_q, all_q)),
        default=0.0,
    )
    return {"equivalent": worst <= 1e-9, "max_abs_difference": worst}


def select_g5_endpoints(keys: Sequence[str]) -> list[str]:
    missing = [name for name in REGISTERED_G5_ENDPOINTS if name not in set(keys)]
    if missing:
        raise RuntimeError("registered endpoint absent: " + str(missing))
    return [name for name in keys if name in REGISTERED_G5_ENDPOINTS]
