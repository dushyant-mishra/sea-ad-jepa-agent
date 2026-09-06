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


FROZEN_BLOCK_COUNT = 6

# The protected set, enumerated rather than discovered. Dynamic discovery alone
# cannot establish completeness: a renamed or removed module would silently
# shrink the registry and the gate would then protect fewer tensors while still
# reporting a pass. Adoption must validate discovery against this list.
FROZEN_MANDATORY_REGISTRY: tuple[str, ...] = tuple(
    "blocks.%d.%s.%s" % (index, role, suffix)
    for index in range(FROZEN_BLOCK_COUNT)
    for role in MANDATORY_ROLES
    for suffix in ("weight", "bias")
)

EXPECTED_MANDATORY_COUNT = 48


def validate_registry(module: Any) -> dict[str, Any]:
    """Fail closed unless discovery yields exactly the frozen 48 identities."""
    discovered = mandatory_names(module)
    expected = sorted(FROZEN_MANDATORY_REGISTRY)
    missing = sorted(set(expected) - set(discovered))
    unexpected = sorted(set(discovered) - set(expected))
    by_role: dict[str, int] = {}
    for name in discovered:
        for role in MANDATORY_ROLES:
            if "." + role + "." in name:
                by_role[role] = by_role.get(role, 0) + 1
                break
    passed = not missing and not unexpected and len(discovered) == EXPECTED_MANDATORY_COUNT
    return {
        "discovered_count": len(discovered),
        "expected_count": EXPECTED_MANDATORY_COUNT,
        "missing": missing,
        "unexpected": unexpected,
        "by_role": by_role,
        "passed": passed,
        "terminal": "PASS_MANDATORY_REGISTRY" if passed
        else "STOP_MANDATORY_REGISTRY_MISMATCH",
    }


def enforce_registry(module: Any) -> dict[str, Any]:
    """Raise unless the module presents exactly the frozen protected registry."""
    report = validate_registry(module)
    if not report["passed"]:
        raise RuntimeError(
            "mandatory registry mismatch: %d discovered, expected %d; missing=%s unexpected=%s"
            % (report["discovered_count"], report["expected_count"],
               report["missing"][:4], report["unexpected"][:4])
        )
    return report


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
    """Adjudicate from a name-to-norm mapping, for reading preserved artifacts.

    Only for recorded norms. Live tensors must go through `gate_module`, which
    never squares: see `classify_tensor`.
    """
    return report_from_statuses(
        {name: classify_norm(norm) for name, norm in norms.items()}
    )


def report_from_statuses(statuses: dict[str, str]) -> dict[str, Any]:
    """Build the adjudication report from per-tensor statuses."""
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


def classify_tensor(grad: Any) -> str:
    """Classify a live gradient tensor without ever squaring it.

    A norm squares before summing, so a tensor whose only nonzero element is a
    small subnormal underflows to a norm of exactly 0.0 and would be
    misclassified as dead. At fp32 the smallest subnormal 1.4e-45 squares to
    2e-90, far below the representable range. Emptiness is therefore tested
    exactly, with `any(grad != 0)`, and finiteness separately.
    """
    import torch  # local import so the pure helpers stay importable without torch

    if grad is None:
        return STATUS_MISSING
    detached = grad.detach()
    if not bool(torch.isfinite(detached).all()):
        return STATUS_NONFINITE
    if not bool((detached != 0).any()):
        return STATUS_EXACT_ZERO
    return STATUS_LIVE


def gate_module(module: Any, names: Iterable[str] | None = None) -> dict[str, Any]:
    """Adjudicate a live module. Call after unscale and before the optimizer step."""
    protected = list(names) if names is not None else mandatory_names(module)
    by_name = dict(module.named_parameters())
    statuses = {name: classify_tensor(by_name[name].grad) for name in protected}
    return report_from_statuses(statuses)


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
