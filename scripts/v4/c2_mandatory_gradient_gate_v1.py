#!/usr/bin/env python3
"""Fail-closed mandatory gradient gate for successor training paths.

`phase_e.component_gradient_report` detects missing and nonfinite gradients but
permits an exact-zero gradient tensor. It passed on every historical-condition
run while all 48 mandatory attention tensors were dead, which is why T1
completed 205 updates without raising a mechanics error. It did catch overflow.
The asymmetry is the defect.

This gate rejects, per tensor, before any optimizer step:

- a missing gradient
- a nonfinite gradient
- an exact-zero gradient norm

No generic "small gradient" threshold is defined. The historical defect is exact
zero, and a tiny finite nonzero gradient is legitimate: inventing a magnitude
floor would reject real training signal and would need its own prospective
justification.
"""

from __future__ import annotations

import math
from typing import Any, Iterable

MANDATORY_ROLES = ("attention_norm", "attention.query", "attention.key", "attention.value")

STATUS_MISSING = "MISSING"
STATUS_NONFINITE = "NONFINITE"
STATUS_EXACT_ZERO = "EXACT_ZERO"
STATUS_LIVE = "LIVE"

REJECTING_STATUSES = (STATUS_MISSING, STATUS_NONFINITE, STATUS_EXACT_ZERO)


def mandatory_names(module: Any) -> list[str]:
    """Parameter names whose gradients this gate protects."""
    names = []
    for name, _ in module.named_parameters():
        for role in MANDATORY_ROLES:
            if "." + role + "." in name:
                names.append(name)
                break
    return sorted(names)


def classify_norm(norm: float | None) -> str:
    """Classify one gradient by its norm. `None` means the gradient is absent."""
    if norm is None:
        return STATUS_MISSING
    if not math.isfinite(norm):
        return STATUS_NONFINITE
    if norm == 0.0:
        return STATUS_EXACT_ZERO
    return STATUS_LIVE


def gate_from_norms(norms: dict[str, float | None]) -> dict[str, Any]:
    """Adjudicate from a name-to-norm mapping. Pure, so it can read preserved bytes."""
    statuses = {name: classify_norm(norm) for name, norm in norms.items()}
    rejected = sorted(
        name for name, status in statuses.items() if status in REJECTING_STATUSES
    )
    counts = {status: 0 for status in (*REJECTING_STATUSES, STATUS_LIVE)}
    for status in statuses.values():
        counts[status] += 1
    return {
        "statuses": statuses,
        "rejected_names": rejected,
        "rejected_count": len(rejected),
        "counts": counts,
        "total": len(statuses),
        "passed": not rejected,
        "terminal": "PASS_MANDATORY_GRADIENT_GATE" if not rejected
        else "STOP_MANDATORY_GRADIENT_GATE_REJECTED",
    }


def gate_module(module: Any, names: Iterable[str] | None = None) -> dict[str, Any]:
    """Adjudicate a live module. Call after unscale and before the optimizer step."""
    protected = list(names) if names is not None else mandatory_names(module)
    by_name = dict(module.named_parameters())
    norms: dict[str, float | None] = {}
    for name in protected:
        grad = by_name[name].grad
        norms[name] = None if grad is None else float(grad.detach().float().norm())
    return gate_from_norms(norms)


def enforce(module: Any, names: Iterable[str] | None = None) -> dict[str, Any]:
    """Raise unless every protected tensor has a finite, strictly nonzero gradient."""
    report = gate_module(module, names)
    if not report["passed"]:
        raise RuntimeError(
            "mandatory gradient gate rejected %d of %d tensors (%s): %s"
            % (
                report["rejected_count"],
                report["total"],
                ", ".join(
                    "%s=%d" % (status, report["counts"][status])
                    for status in REJECTING_STATUSES
                    if report["counts"][status]
                ),
                ", ".join(report["rejected_names"][:6])
                + (" ..." if report["rejected_count"] > 6 else ""),
            )
        )
    return report
