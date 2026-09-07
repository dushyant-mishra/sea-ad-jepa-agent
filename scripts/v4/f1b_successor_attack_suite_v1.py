#!/usr/bin/env python3
"""Executable adversarial attacks for the F1-B independent-verifier findings.

Prospective. Frozen BEFORE any successor implementation exists, so a candidate
cannot be written to the attacks after seeing them pass.

## Why this replaces the existing probes

`scripts/v4/verify_f1b_minimal_bridge_independent_v1.py` gates only four of the
fifteen findings with anything executable. Five more are gated by literal
substring probes over the executor source, for example::

    'visible[0].sum()' in src
    'coverage = gradient_coverage(online)\\n        optimizer.step()' in src

Those **fail open**. A rename, a reformat, or a line break flips the probe to
"not vulnerable" while the defect remains, so a cosmetic edit manufactures a
false PASS. That is the same fail-open class as a gradient check that counts
missing and nonfinite but never zero.

Every attack here is **behavioural**: it constructs an input, runs the candidate,
and observes what the candidate does. None inspects source text.

## Verdict vocabulary

Deliberately unambiguous, because a first draft of this file used "CAUGHT" and
applied it in both directions in different attacks:

- `VULNERABLE` - the attack exploited the candidate. The defect is present.
- `DEFENDED`   - the candidate refused or behaved correctly. The defect is absent.
- `NOT_APPLICABLE` - the candidate does not expose the machinery under attack.

`NOT_APPLICABLE` is never a pass. Absent machinery cannot demonstrate
compliance, and a suite that treated it as success would let a candidate clear
every attack by implementing nothing.

## The polarity requirement

An attack that always reports DEFENDED is worthless, and one that always reports
VULNERABLE is equally worthless. Each attack is proven in both directions
against two reference candidates shipped alongside it: a deliberately vulnerable
one that MUST come back VULNERABLE, and a correct one that MUST come back
DEFENDED. `prove_polarity` asserts both and reports `ATTACK_DEFECTIVE` for any
attack that fails either half, so a non-discriminating attack is never mistaken
for evidence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

VULNERABLE = "VULNERABLE"
DEFENDED = "DEFENDED"
NOT_APPLICABLE = "NOT_APPLICABLE"
ATTACK_DEFECTIVE = "ATTACK_DEFECTIVE"


@dataclass
class Candidate:
    """Callables a successor implementation exposes for adversarial probing.

    Every field is optional. An absent field yields NOT_APPLICABLE, never a pass.
    """

    name: str
    # finding 4: must reject dead predictor gradients/moments, not only backbone
    gate_mandatory_gradients: Callable[[Mapping[str, Any]], Any] | None = None
    # findings 5 and 6: routing statistics per cell, given per-cell valid supports
    routing_report: Callable[[Sequence[Sequence[float]], Sequence[int]], Any] | None = None
    # finding 14: a full update; must raise before the optimizer records any state
    protected_update: Callable[[Mapping[str, Any]], Any] | None = None
    # finding 15: endpoint selection from an NPZ-like key set
    select_endpoints: Callable[[Sequence[str]], Sequence[str]] | None = None
    metadata: dict = field(default_factory=dict)


def _run(fn: Callable[..., Any], *args: Any) -> tuple[bool, Any]:
    """Return (refused, payload). A raise counts as a refusal."""
    try:
        return False, fn(*args)
    except Exception as exc:  # noqa: BLE001 - any refusal is a defence
        return True, exc


def _na(finding: object, what: str) -> dict:
    return {"finding": finding, "verdict": NOT_APPLICABLE,
            "reason": "candidate exposes no " + what}


# --------------------------------------------------------------------------
# finding 4: predictor mechanics are not gated
# --------------------------------------------------------------------------
def attack_predictor_mechanics_ungated(candidate: Candidate) -> dict:
    """A dead predictor tensor must be rejected even when the backbone is healthy.

    The historical gate covered backbone tensors only, so a predictor whose
    gradients were entirely dead passed. The predictor carries the conditional
    computation the whole result rests on.
    """
    if candidate.gate_mandatory_gradients is None:
        return _na(4, "gate_mandatory_gradients")
    payload = {
        "backbone": {"blocks.0.attention.query.weight": 1.0,
                     "blocks.0.attention_norm.weight": 1.0},
        "predictor": {"predictor.cross_attention.in_proj_weight": 0.0,
                      "predictor.output_norm.weight": 0.0},
    }
    refused, _ = _run(candidate.gate_mandatory_gradients, payload)
    return {"finding": 4, "verdict": DEFENDED if refused else VULNERABLE,
            "note": "dead predictor with healthy backbone must be rejected"}


# --------------------------------------------------------------------------
# findings 5 and 6: routing sampled from / normalised by cell 0
# --------------------------------------------------------------------------
def attack_routing_uses_cell_zero(candidate: Candidate) -> dict:
    """A cell with one valid key must be scored over one key, not over cell 0's four.

    Both cells receive the SAME weight row, so any difference in the reported
    statistic can only come from per-cell support handling. Cell 0 has four valid
    keys and must report an effective support near 4. Cell 1 has a single valid
    key, so its distribution is degenerate and it must report near 1. An
    implementation that samples cell 0, or normalises every cell by cell 0's
    support, scores cell 1 over four slots and reports 4 for both.

    An earlier draft of this attack gave the two cells different weight rows.
    That failed to discriminate, because both a correct and a defective
    implementation then separate them. Identical rows isolate the variable.
    """
    if candidate.routing_report is None:
        return _na("5+6", "routing_report")
    weights = [[0.25, 0.25, 0.25, 0.25], [0.25, 0.25, 0.25, 0.25]]
    valid = [4, 1]
    refused, report = _run(candidate.routing_report, weights, valid)
    if refused:
        return {"finding": "5+6", "verdict": DEFENDED,
                "note": "candidate refused the variable-support batch"}
    try:
        per_cell = [float(x) for x in report]
    except Exception:  # noqa: BLE001
        return {"finding": "5+6", "verdict": VULNERABLE,
                "note": "candidate did not return per-cell statistics"}
    if len(per_cell) != len(valid):
        return {"finding": "5+6", "verdict": VULNERABLE,
                "per_cell": per_cell,
                "note": "candidate did not report one statistic per cell"}
    # A single valid key is a degenerate distribution: effective support is 1.
    single_key_cell_correct = math.isclose(per_cell[1], 1.0, rel_tol=0.0, abs_tol=1e-6)
    four_key_cell_correct = per_cell[0] > 1.0 + 1e-6
    ok = single_key_cell_correct and four_key_cell_correct
    return {"finding": "5+6", "verdict": DEFENDED if ok else VULNERABLE,
            "per_cell": per_cell,
            "expected": {"cell0_effective_support": "> 1", "cell1_effective_support": "1.0"},
            "note": "identical weight rows; only per-cell support may change the statistic"}


# --------------------------------------------------------------------------
# finding 14: gate enforced after the optimizer step
# --------------------------------------------------------------------------
def attack_optimizer_steps_before_gate(candidate: Candidate) -> dict:
    """A dead mandatory gradient must stop the update BEFORE any state exists.

    Reporting a violation after stepping is not a gate. The candidate receives an
    update whose mandatory gradients are dead and must both refuse and leave the
    optimizer untouched. Refusing after stepping is still VULNERABLE.
    """
    if candidate.protected_update is None:
        return _na(14, "protected_update")
    ledger: dict[str, Any] = {"optimizer_state_entries": 0, "stepped": False}
    payload = {"mandatory_gradients": {"blocks.0.attention.query.weight": 0.0},
               "ledger": ledger}
    refused, _ = _run(candidate.protected_update, payload)
    stepped = bool(ledger.get("stepped")) or int(ledger.get("optimizer_state_entries", 0)) > 0
    if not refused:
        return {"finding": 14, "verdict": VULNERABLE, "ledger": dict(ledger),
                "note": "dead mandatory gradient did not stop the update"}
    if stepped:
        return {"finding": 14, "verdict": VULNERABLE, "ledger": dict(ledger),
                "note": "update refused, but only after the optimizer had stepped"}
    return {"finding": 14, "verdict": DEFENDED, "ledger": dict(ledger),
            "note": "refused before any optimizer state existed"}


# --------------------------------------------------------------------------
# finding 15: endpoint registry inferred from every l2__ key
# --------------------------------------------------------------------------
def attack_implicit_endpoint_registry(candidate: Candidate) -> dict:
    """Unregistered `l2__` keys must not become gate-bearing endpoints.

    The authority NPZ also carries `recurrent_5pct` and `recurrent_1pct`, which
    are duplicated rare directions and are not authorised main-F1 endpoints.
    Selecting every matching key infers biology from a file layout.
    """
    if candidate.select_endpoints is None:
        return _na(15, "select_endpoints")
    keys = ["l2__broad_common", "l2__local", "l2__recurrent_5pct",
            "l2__recurrent_1pct", "l2__unregistered_experimental", "raw__local"]
    refused, selected = _run(candidate.select_endpoints, keys)
    if refused:
        return {"finding": 15, "verdict": DEFENDED,
                "note": "candidate refused an unregistered key set"}
    chosen = set(selected or ())
    leaked = chosen & {"l2__recurrent_5pct", "l2__recurrent_1pct",
                       "l2__unregistered_experimental"}
    return {"finding": 15, "verdict": VULNERABLE if leaked else DEFENDED,
            "leaked": sorted(leaked), "selected": sorted(chosen),
            "note": "only prospectively registered endpoints may be selected"}


ATTACKS: tuple[tuple[str, Callable[[Candidate], dict]], ...] = (
    ("predictor_mechanics_ungated", attack_predictor_mechanics_ungated),
    ("routing_uses_cell_zero", attack_routing_uses_cell_zero),
    ("optimizer_steps_before_gate", attack_optimizer_steps_before_gate),
    ("implicit_endpoint_registry", attack_implicit_endpoint_registry),
)

COVERED_FINDINGS = (4, 5, 6, 14, 15)


def run_suite(candidate: Candidate) -> dict:
    """A candidate is clean only when every attack reports DEFENDED."""
    results = {name: fn(candidate) for name, fn in ATTACKS}
    vulnerable = sorted(n for n, r in results.items() if r["verdict"] == VULNERABLE)
    defended = sorted(n for n, r in results.items() if r["verdict"] == DEFENDED)
    inapplicable = sorted(n for n, r in results.items() if r["verdict"] == NOT_APPLICABLE)
    clean = not vulnerable and not inapplicable
    return {
        "schema": "F1B_SUCCESSOR_ATTACK_SUITE_V1",
        "candidate": candidate.name,
        "covered_findings": list(COVERED_FINDINGS),
        "results": results,
        "vulnerable": vulnerable,
        "defended": defended,
        "not_applicable": inapplicable,
        "terminal": "PASS_F1B_ATTACK_SUITE" if clean else "STOP_F1B_ATTACK_SUITE",
    }


def prove_polarity(vulnerable: Candidate, correct: Candidate) -> dict:
    """Each attack must report VULNERABLE on the defective reference and DEFENDED on the correct one."""
    report = {}
    for name, fn in ATTACKS:
        on_vuln = fn(vulnerable)["verdict"]
        on_ok = fn(correct)["verdict"]
        discriminating = (on_vuln == VULNERABLE) and (on_ok == DEFENDED)
        report[name] = {"on_vulnerable": on_vuln, "on_correct": on_ok,
                        "status": "DISCRIMINATING" if discriminating else ATTACK_DEFECTIVE}
    defective = sorted(n for n, r in report.items() if r["status"] == ATTACK_DEFECTIVE)
    return {"schema": "F1B_ATTACK_POLARITY_PROOF_V1", "attacks": report,
            "defective": defective,
            "terminal": "PASS_ATTACK_POLARITY" if not defective else "STOP_ATTACK_POLARITY"}
