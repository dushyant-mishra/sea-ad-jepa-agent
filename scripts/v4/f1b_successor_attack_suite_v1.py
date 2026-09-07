#!/usr/bin/env python3
"""Executable adversarial attacks for all fifteen F1-B independent-verifier findings.

Prospective. Frozen BEFORE any successor implementation exists, so a candidate
cannot be written to the attacks after seeing them pass.

## Why this replaces the existing probes

`scripts/v4/verify_f1b_minimal_bridge_independent_v1.py` gates only four of the
fifteen findings with anything executable. Five more are gated by literal
substring probes over the executor source, for example::

    'visible[0].sum()' in src
    'coverage = gradient_coverage(online)\\n        optimizer.step()' in src

Those **fail open**: a rename, a reformat, or a line break flips the probe to
"not vulnerable" while the defect remains, so a formatting-only edit
manufactures a PASS. That is a verifier defect in its own right, and it is the
same fail-open class as a gradient check that counts missing and nonfinite but
never zero. Findings 4, 5, 6, 14 and 15 are therefore treated here as
**effectively uncovered** rather than covered.

Every attack in this module is **behavioural**: it constructs an input, runs the
candidate, and observes what the candidate does. None inspects source text.

## Verdict vocabulary

Deliberately unambiguous, because a first draft used "CAUGHT" and applied it in
both directions in different attacks:

- `VULNERABLE` - the attack exploited the candidate. The defect is present.
- `DEFENDED`   - the candidate refused or behaved correctly. The defect is absent.
- `NOT_APPLICABLE` - the candidate does not expose the machinery under attack.

## The two frozen meta-rules

1. `NOT_APPLICABLE != PASS`. Absent machinery cannot demonstrate compliance, or
   a candidate would clear every attack by implementing nothing.
2. Every attack must prove polarity: `VULNERABLE` against a known-defective
   reference and `DEFENDED` against a known-correct one. Anything else is
   `ATTACK_DEFECTIVE` and is not evidence.

Rule 2 has already earned itself. A first routing attack gave the two cells
different weight rows, so a correct and a defective implementation both
separated them and the attack discriminated nothing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

VULNERABLE = "VULNERABLE"
DEFENDED = "DEFENDED"
NOT_APPLICABLE = "NOT_APPLICABLE"
ATTACK_DEFECTIVE = "ATTACK_DEFECTIVE"

ALL_FINDINGS = tuple(range(1, 16))


@dataclass
class Candidate:
    """Callables a successor exposes for adversarial probing. Absent field -> NOT_APPLICABLE."""

    name: str
    # findings 1, 2, 4: gradient/moment validity for backbone AND predictor
    gate_mandatory_gradients: Callable[[Mapping[str, Any]], Any] | None = None
    # finding 3: per-tensor movement beyond decay, with zero-baseline handling
    movement_gate: Callable[[Mapping[str, Any]], Any] | None = None
    # findings 5, 6: per-cell routing statistics given per-cell valid supports
    routing_report: Callable[[Sequence[Sequence[float]], Sequence[int]], Any] | None = None
    # findings 7, 8: named routing metrics and their analytic behaviour
    routing_metrics: Callable[[Sequence[float], Sequence[bool]], Mapping[str, float]] | None = None
    # finding 9: G5 refit; must depend on the fit split
    refit: Callable[[Sequence[float]], Any] | None = None
    # finding 10: the frozen update horizon actually enforced
    frozen_horizon: Callable[[int], Any] | None = None
    # finding 11: directional conclusion given controls
    directional_claim: Callable[[Mapping[str, float]], Any] | None = None
    # finding 12: singleton-q versus all-Q target equivalence
    target_equivalence: Callable[[Sequence[float], Sequence[float]], Any] | None = None
    # finding 13: production AMP path; must invoke the supplied probe
    amp_smoke: Callable[[Callable[..., None]], Any] | None = None
    # findings 14: a protected update; must refuse before the optimizer records state
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


def _verdict(finding: object, defended: bool, note: str, **extra: Any) -> dict:
    return {"finding": finding, "verdict": DEFENDED if defended else VULNERABLE,
            "note": note, **extra}


# ---------------------------------------------------------------- finding 1
def attack_nonfinite_gradient_accepted(candidate: Candidate) -> dict:
    """A NaN or Inf gradient norm is not zero, and must still be rejected."""
    if candidate.gate_mandatory_gradients is None:
        return _na(1, "gate_mandatory_gradients")
    outcomes = []
    for label, value in (("nan", float("nan")), ("posinf", float("inf")),
                         ("neginf", float("-inf"))):
        refused, _ = _run(candidate.gate_mandatory_gradients,
                          {"backbone": {"blocks.0.attention.query.weight": value},
                           "predictor": {"predictor.output_norm.weight": 1.0}})
        outcomes.append((label, refused))
    missed = [label for label, refused in outcomes if not refused]
    return _verdict(1, not missed,
                    "nonfinite gradients must be rejected, not treated as nonzero",
                    accepted=missed)


# ---------------------------------------------------------------- finding 2
def attack_one_moment_zero_accepted(candidate: Candidate) -> dict:
    """Both Adam moments are required; a live first moment must not mask a dead second."""
    if candidate.gate_mandatory_gradients is None:
        return _na(2, "gate_mandatory_gradients")
    payload = {"backbone": {"blocks.0.attention.query.weight": 1.0},
               "predictor": {"predictor.output_norm.weight": 1.0},
               "moments": {"blocks.0.attention.query.weight": {"exp_avg": 1.0,
                                                               "exp_avg_sq": 0.0}}}
    refused, _ = _run(candidate.gate_mandatory_gradients, payload)
    return _verdict(2, refused,
                    "zero second moment must reject even with a nonzero first moment")


# ---------------------------------------------------------------- finding 3
def attack_pooled_movement_masks_dead_tensor(candidate: Candidate) -> dict:
    """A mean over tensors lets one decay-only tensor hide behind large movement."""
    if candidate.movement_gate is None:
        return _na(3, "movement_gate")
    decay_only = 1e-6
    payload = {"relative_movement": {"a": 1.0, "b": 1.0, "c": 1.0, "dead": decay_only},
               "decay_only_prediction": decay_only,
               "absolute_movement": {"a": 1.0, "b": 1.0, "c": 1.0, "dead": 0.0},
               "baseline_norm": {"a": 1.0, "b": 1.0, "c": 1.0, "dead": 1.0}}
    refused, _ = _run(candidate.movement_gate, payload)
    if not refused:
        return _verdict(3, False, "one decay-only tensor was masked by the pooled mean")
    # Second pole of the same finding: a zero-baseline tensor that DID move must pass.
    zero_baseline = {"relative_movement": {"bias": None},
                     "decay_only_prediction": decay_only,
                     "absolute_movement": {"bias": 1e-3},
                     "baseline_norm": {"bias": 0.0}}
    refused_ok, _ = _run(candidate.movement_gate, zero_baseline)
    return _verdict(3, not refused_ok,
                    "per-tensor gating required, and a moved zero-baseline tensor must pass",
                    zero_baseline_rejected=refused_ok)


# ---------------------------------------------------------------- finding 4
def attack_predictor_mechanics_ungated(candidate: Candidate) -> dict:
    """A dead predictor tensor must be rejected even when the backbone is healthy."""
    if candidate.gate_mandatory_gradients is None:
        return _na(4, "gate_mandatory_gradients")
    payload = {"backbone": {"blocks.0.attention.query.weight": 1.0,
                            "blocks.0.attention_norm.weight": 1.0},
               "predictor": {"predictor.cross_attention.in_proj_weight": 0.0,
                             "predictor.output_norm.weight": 0.0}}
    refused, _ = _run(candidate.gate_mandatory_gradients, payload)
    return _verdict(4, refused, "dead predictor with healthy backbone must be rejected")


# ------------------------------------------------------------- findings 5, 6
def attack_routing_uses_cell_zero(candidate: Candidate) -> dict:
    """A cell with one valid key must be scored over one key, not over cell 0's four.

    Both cells receive the SAME weight row, so any difference in the reported
    statistic can only come from per-cell support handling. Identical rows
    isolate the variable; an earlier draft using different rows discriminated
    nothing.
    """
    if candidate.routing_report is None:
        return _na("5+6", "routing_report")
    weights = [[0.25, 0.25, 0.25, 0.25], [0.25, 0.25, 0.25, 0.25]]
    valid = [4, 1]
    refused, report = _run(candidate.routing_report, weights, valid)
    if refused:
        return _verdict("5+6", True, "candidate refused the variable-support batch")
    try:
        per_cell = [float(x) for x in report]
    except Exception:  # noqa: BLE001
        return _verdict("5+6", False, "candidate did not return per-cell statistics")
    if len(per_cell) != len(valid):
        return _verdict("5+6", False, "candidate did not report one statistic per cell",
                        per_cell=per_cell)
    single_ok = math.isclose(per_cell[1], 1.0, rel_tol=0.0, abs_tol=1e-6)
    four_ok = per_cell[0] > 1.0 + 1e-6
    return _verdict("5+6", single_ok and four_ok,
                    "identical weight rows; only per-cell support may change the statistic",
                    per_cell=per_cell)


# ---------------------------------------------------------------- finding 7
def attack_routing_metric_collision(candidate: Candidate) -> dict:
    """Entropy perplexity and participation ratio must not substitute for each other.

    For p = (0.5, 0.25, 0.25): exp(H) = 2.8284 while 1/sum(p^2) = 2.6667. A
    candidate reporting one number under both names, or reporting a value that
    matches the wrong analytic answer, is substituting metrics.
    """
    if candidate.routing_metrics is None:
        return _na(7, "routing_metrics")
    p = [0.5, 0.25, 0.25]
    entropy = -sum(x * math.log(x) for x in p)
    expected_perplexity = math.exp(entropy)              # 2.8284...
    expected_participation = 1.0 / sum(x * x for x in p)  # 2.6667...
    if math.isclose(expected_perplexity, expected_participation, abs_tol=1e-3):
        return {"finding": 7, "verdict": ATTACK_DEFECTIVE,
                "note": "attack premise broken: the two metrics do not disagree here"}
    refused, report = _run(candidate.routing_metrics, p, [True, True, True])
    if refused:
        return _verdict(7, True, "candidate refused rather than substitute metrics")
    got_perp = report.get("entropy_perplexity") if hasattr(report, "get") else None
    got_part = report.get("participation_ratio") if hasattr(report, "get") else None
    if got_perp is None or got_part is None:
        return _verdict(7, False, "both metrics must be reported under distinct names",
                        reported=sorted(report) if hasattr(report, "__iter__") else None)
    perp_ok = math.isclose(float(got_perp), expected_perplexity, rel_tol=1e-6)
    part_ok = math.isclose(float(got_part), expected_participation, rel_tol=1e-6)
    collided = math.isclose(float(got_perp), float(got_part), rel_tol=1e-9)
    return _verdict(7, perp_ok and part_ok and not collided,
                    "each name must carry its own analytic value",
                    expected={"entropy_perplexity": expected_perplexity,
                              "participation_ratio": expected_participation},
                    reported={"entropy_perplexity": got_perp,
                              "participation_ratio": got_part})


# ---------------------------------------------------------------- finding 8
def attack_routing_analytic_mutations(candidate: Candidate) -> dict:
    """Each independent mutation has a predictable analytic answer.

    Uniform over n -> perplexity n. One-hot -> 1. Mass on a masked key must be
    ignored. Scaling all weights must not change a normalised statistic.
    Permuting keys must not change it either.
    """
    if candidate.routing_metrics is None:
        return _na(8, "routing_metrics")

    def perp(weights: Sequence[float], mask: Sequence[bool]) -> float | None:
        refused, report = _run(candidate.routing_metrics, list(weights), list(mask))
        if refused or not hasattr(report, "get"):
            return None
        value = report.get("entropy_perplexity")
        return None if value is None else float(value)

    failures = []
    uniform = perp([0.25] * 4, [True] * 4)
    if uniform is None or not math.isclose(uniform, 4.0, rel_tol=1e-6):
        failures.append({"mutation": "uniform_over_4", "expected": 4.0, "got": uniform})
    onehot = perp([1.0, 0.0, 0.0, 0.0], [True] * 4)
    if onehot is None or not math.isclose(onehot, 1.0, abs_tol=1e-6):
        failures.append({"mutation": "one_hot", "expected": 1.0, "got": onehot})
    masked = perp([0.25, 0.25, 0.25, 0.25], [True, True, False, False])
    if masked is None or not math.isclose(masked, 2.0, rel_tol=1e-6):
        failures.append({"mutation": "two_keys_masked", "expected": 2.0, "got": masked})
    scaled = perp([2.5, 2.5, 2.5, 2.5], [True] * 4)
    if scaled is None or uniform is None or not math.isclose(scaled, uniform, rel_tol=1e-6):
        failures.append({"mutation": "scale_invariance", "expected": uniform, "got": scaled})
    permuted = perp([0.25, 0.5, 0.25], [True] * 3)
    original = perp([0.5, 0.25, 0.25], [True] * 3)
    if permuted is None or original is None or not math.isclose(permuted, original, rel_tol=1e-6):
        failures.append({"mutation": "permutation_invariance",
                         "expected": original, "got": permuted})
    return _verdict(8, not failures, "every routing mutation has a predictable analytic answer",
                    failures=failures)


# ---------------------------------------------------------------- finding 9
def attack_g5_refit_is_not_a_refit(candidate: Candidate) -> dict:
    """A genuine refit depends on its fit split; a cached path returns the same object.

    No real G5 biology is used. Two clearly different synthetic fit sets must
    produce different fitted objects.
    """
    if candidate.refit is None:
        return _na(9, "refit")
    refused_a, fit_a = _run(candidate.refit, [0.0, 0.0, 0.0, 0.0])
    refused_b, fit_b = _run(candidate.refit, [1.0, 2.0, 3.0, 4.0])
    if refused_a or refused_b:
        return _verdict(9, True, "candidate refused rather than reuse a cached fit")
    same = repr(fit_a) == repr(fit_b)
    return _verdict(9, not same,
                    "different fit splits must produce different fitted objects",
                    fit_a=repr(fit_a)[:80], fit_b=repr(fit_b)[:80])


# --------------------------------------------------------------- finding 10
def attack_horizon_override(candidate: Candidate) -> dict:
    """The frozen horizon must be enforced, not merely defaulted."""
    if candidate.frozen_horizon is None:
        return _na(10, "frozen_horizon")
    refused_over, _ = _run(candidate.frozen_horizon, 300)
    refused_exact, _ = _run(candidate.frozen_horizon, 40)
    if not refused_over:
        return _verdict(10, False, "a 300-update request must not be accepted under a frozen 40")
    return _verdict(10, not refused_exact,
                    "the frozen horizon itself must remain runnable",
                    frozen_horizon_rejected=refused_exact)


# --------------------------------------------------------------- finding 11
def attack_directional_claim_too_strong(candidate: Candidate) -> dict:
    """If a control explains the effect, the strong directional claim must be withheld.

    Query-centering removes additive query-common cell components. It does not
    prove a query-conditioned transformation of global or CELL state is
    impossible. When the CELL-only control reproduces the effect, asserting the
    strong claim is unsupported.
    """
    if candidate.directional_claim is None:
        return _na(11, "directional_claim")
    explained = {"observed": 1.0, "cell_only_control": 1.0, "identity_only_control": 0.0}
    refused, claim = _run(candidate.directional_claim, explained)
    if refused:
        return _verdict(11, True, "candidate refused to claim under an explaining control")
    asserted = bool(claim) if not isinstance(claim, Mapping) else bool(claim.get("structural"))
    if asserted:
        return _verdict(11, False,
                        "strong directional claim asserted while the CELL-only control explains it")
    # Second pole: with controls flat, the claim must remain available.
    unexplained = {"observed": 1.0, "cell_only_control": 0.0, "identity_only_control": 0.0}
    refused2, claim2 = _run(candidate.directional_claim, unexplained)
    available = (not refused2) and (bool(claim2) if not isinstance(claim2, Mapping)
                                   else bool(claim2.get("structural")))
    return _verdict(11, available,
                    "claim withheld when controls explain it, available when they do not")


# --------------------------------------------------------------- finding 12
def attack_target_equivalence_assumed(candidate: Candidate) -> dict:
    """Singleton-q and all-Q masking must be compared, not assumed equivalent.

    One case where equality genuinely holds and one where it deliberately does
    not. A verifier that always reports equivalence fails the second.
    """
    if candidate.target_equivalence is None:
        return _na(12, "target_equivalence")
    equal_single, equal_all = [1.0, 2.0, 3.0], [1.0, 2.0, 3.0]
    diff_single, diff_all = [1.0, 2.0, 3.0], [1.0, 2.0, 9.0]

    def equivalent(a: Sequence[float], b: Sequence[float]) -> bool | None:
        refused, out = _run(candidate.target_equivalence, list(a), list(b))
        if refused:
            return None
        return bool(out) if not isinstance(out, Mapping) else bool(out.get("equivalent"))

    same = equivalent(equal_single, equal_all)
    differ = equivalent(diff_single, diff_all)
    if same is None or differ is None:
        return _verdict(12, False, "candidate could not adjudicate target equivalence")
    return _verdict(12, same is True and differ is False,
                    "equality must be detected and inequality must be detected",
                    reported={"true_equality": same, "true_inequality": differ})


# --------------------------------------------------------------- finding 13
def attack_amp_smoke_is_declarative(candidate: Candidate) -> dict:
    """The AMP path must be executed and observed, not declared.

    The attack supplies the probe. A candidate that reports AMP semantics
    without invoking the probe has not executed anything, and a candidate whose
    observations are internally inconsistent has not observed them either.
    """
    if candidate.amp_smoke is None:
        return _na(13, "amp_smoke")
    seen: list[dict] = []

    def probe(**observation: Any) -> None:
        seen.append(dict(observation))

    refused, _ = _run(candidate.amp_smoke, probe)
    if refused:
        return _verdict(13, True, "candidate refused rather than declare AMP semantics")
    if not seen:
        return _verdict(13, False, "candidate never invoked the supplied probe")
    required = {"autocast_enabled", "grad_dtype", "scaler_enabled",
                "unscaled_before_gate", "gate_before_step"}
    record = seen[-1]
    missing = sorted(required - set(record))
    if missing:
        return _verdict(13, False, "observation record incomplete", missing=missing,
                        observed=record)
    consistent = (bool(record["unscaled_before_gate"]) and bool(record["gate_before_step"])
                  and str(record["grad_dtype"]) != "")
    return _verdict(13, consistent,
                    "observed AMP ordering must show unscale before gate and gate before step",
                    observed=record)


# --------------------------------------------------------------- finding 14
def attack_optimizer_steps_before_gate(candidate: Candidate) -> dict:
    """A dead mandatory gradient must stop the update BEFORE any state exists."""
    if candidate.protected_update is None:
        return _na(14, "protected_update")
    ledger: dict[str, Any] = {"optimizer_state_entries": 0, "stepped": False}
    payload = {"mandatory_gradients": {"blocks.0.attention.query.weight": 0.0},
               "ledger": ledger}
    refused, _ = _run(candidate.protected_update, payload)
    stepped = bool(ledger.get("stepped")) or int(ledger.get("optimizer_state_entries", 0)) > 0
    if not refused:
        return _verdict(14, False, "dead mandatory gradient did not stop the update",
                        ledger=dict(ledger))
    if stepped:
        return _verdict(14, False, "update refused, but only after the optimizer had stepped",
                        ledger=dict(ledger))
    return _verdict(14, True, "refused before any optimizer state existed",
                    ledger=dict(ledger))


# --------------------------------------------------------------- finding 15
def attack_implicit_endpoint_registry(candidate: Candidate) -> dict:
    """Unregistered `l2__` keys must not become gate-bearing endpoints."""
    if candidate.select_endpoints is None:
        return _na(15, "select_endpoints")
    keys = ["l2__broad_common", "l2__local", "l2__recurrent_5pct",
            "l2__recurrent_1pct", "l2__unregistered_experimental", "raw__local"]
    refused, selected = _run(candidate.select_endpoints, keys)
    if refused:
        return _verdict(15, True, "candidate refused an unregistered key set")
    chosen = set(selected or ())
    leaked = chosen & {"l2__recurrent_5pct", "l2__recurrent_1pct",
                       "l2__unregistered_experimental"}
    return _verdict(15, not leaked,
                    "only prospectively registered endpoints may be selected",
                    leaked=sorted(leaked), selected=sorted(chosen))


# Attack name -> (callable, findings covered)
ATTACKS: tuple[tuple[str, Callable[[Candidate], dict], tuple[int, ...]], ...] = (
    ("nonfinite_gradient_accepted", attack_nonfinite_gradient_accepted, (1,)),
    ("one_moment_zero_accepted", attack_one_moment_zero_accepted, (2,)),
    ("pooled_movement_masks_dead_tensor", attack_pooled_movement_masks_dead_tensor, (3,)),
    ("predictor_mechanics_ungated", attack_predictor_mechanics_ungated, (4,)),
    ("routing_uses_cell_zero", attack_routing_uses_cell_zero, (5, 6)),
    ("routing_metric_collision", attack_routing_metric_collision, (7,)),
    ("routing_analytic_mutations", attack_routing_analytic_mutations, (8,)),
    ("g5_refit_is_not_a_refit", attack_g5_refit_is_not_a_refit, (9,)),
    ("horizon_override", attack_horizon_override, (10,)),
    ("directional_claim_too_strong", attack_directional_claim_too_strong, (11,)),
    ("target_equivalence_assumed", attack_target_equivalence_assumed, (12,)),
    ("amp_smoke_is_declarative", attack_amp_smoke_is_declarative, (13,)),
    ("optimizer_steps_before_gate", attack_optimizer_steps_before_gate, (14,)),
    ("implicit_endpoint_registry", attack_implicit_endpoint_registry, (15,)),
)


def run_suite(candidate: Candidate) -> dict:
    """A candidate is clean only when every attack reports DEFENDED."""
    results = {name: fn(candidate) for name, fn, _ in ATTACKS}
    vulnerable = sorted(n for n, r in results.items() if r["verdict"] == VULNERABLE)
    defended = sorted(n for n, r in results.items() if r["verdict"] == DEFENDED)
    inapplicable = sorted(n for n, r in results.items() if r["verdict"] == NOT_APPLICABLE)
    defective = sorted(n for n, r in results.items() if r["verdict"] == ATTACK_DEFECTIVE)
    clean = not vulnerable and not inapplicable and not defective
    return {
        "schema": "F1B_SUCCESSOR_ATTACK_SUITE_V1",
        "candidate": candidate.name,
        "results": results,
        "vulnerable": vulnerable,
        "defended": defended,
        "not_applicable": inapplicable,
        "attack_defective": defective,
        "terminal": "PASS_F1B_ATTACK_SUITE" if clean else "STOP_F1B_ATTACK_SUITE",
    }


def prove_polarity(vulnerable: Candidate, correct: Candidate) -> dict:
    """VULNERABLE on the defective reference, DEFENDED on the correct one, or ATTACK_DEFECTIVE."""
    report = {}
    for name, fn, findings in ATTACKS:
        on_vuln = fn(vulnerable)["verdict"]
        on_ok = fn(correct)["verdict"]
        discriminating = (on_vuln == VULNERABLE) and (on_ok == DEFENDED)
        report[name] = {"findings": list(findings), "on_vulnerable": on_vuln,
                        "on_correct": on_ok,
                        "status": "DISCRIMINATING" if discriminating else ATTACK_DEFECTIVE}
    defective = sorted(n for n, r in report.items() if r["status"] == ATTACK_DEFECTIVE)
    return {"schema": "F1B_ATTACK_POLARITY_PROOF_V1", "attacks": report,
            "defective": defective,
            "terminal": "PASS_ATTACK_POLARITY" if not defective else "STOP_ATTACK_POLARITY"}


def registry_audit(vulnerable: Candidate, correct: Candidate) -> dict:
    """Registry-level meta-test, required before the attack authority may be frozen.

    Asserts that exactly fifteen finding IDs exist, each has at least one
    executable discriminating attack, no attack inspects source text, none can
    reach PASS through NOT_APPLICABLE, and every attack has demonstrated both
    poles.
    """
    covered: dict[int, list[str]] = {f: [] for f in ALL_FINDINGS}
    for name, _, findings in ATTACKS:
        for finding in findings:
            covered.setdefault(finding, []).append(name)
    polarity = prove_polarity(vulnerable, correct)
    discriminating = {n for n, r in polarity["attacks"].items()
                      if r["status"] == "DISCRIMINATING"}

    checks = []

    def check(name: str, passed: bool, detail: Any = None) -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    check("exactly_15_finding_ids", sorted(covered) == list(ALL_FINDINGS), sorted(covered))
    uncovered = sorted(f for f, names in covered.items() if not names)
    check("every_finding_has_an_attack", not uncovered, uncovered)
    weak = sorted(f for f, names in covered.items()
                  if not any(n in discriminating for n in names))
    check("every_finding_has_a_DISCRIMINATING_attack", not weak, weak)
    check("no_attack_is_defective", not polarity["defective"], polarity["defective"])
    # NOT_APPLICABLE must never reach PASS: an empty candidate must be stopped.
    empty = Candidate(name="registry_probe_empty")
    empty_report = run_suite(empty)
    check("not_applicable_cannot_pass",
          empty_report["terminal"] == "STOP_F1B_ATTACK_SUITE"
          and len(empty_report["not_applicable"]) == len(ATTACKS),
          empty_report["terminal"])
    # No attack may read source text.
    import inspect as _inspect
    text_readers = []
    for name, fn, _ in ATTACKS:
        src = _inspect.getsource(fn)
        if "read_text" in src or "getsource" in src or " in src" in src:
            text_readers.append(name)
    check("no_attack_inspects_source_text", not text_readers, text_readers)

    passed = all(c["passed"] for c in checks)
    return {"schema": "F1B_ATTACK_REGISTRY_AUDIT_V1",
            "coverage": {str(f): covered[f] for f in ALL_FINDINGS},
            "checks": checks,
            "terminal": "PASS_F1B_ATTACK_REGISTRY" if passed else "STOP_F1B_ATTACK_REGISTRY"}
