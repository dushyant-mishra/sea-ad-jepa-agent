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
    # findings 7, 8: per-query named routing metrics and analytic mutation behaviour
    routing_metrics: Callable[[Sequence[Sequence[float]], Sequence[Sequence[bool]]], Mapping[str, Any]] | None = None
    # finding 9: G5 checkpoint-specific refit probe on a donor-held-out synthetic fixture
    refit: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None
    # finding 10: the frozen update horizon actually enforced
    frozen_horizon: Callable[[int], Any] | None = None
    # finding 11: directional conclusion given controls
    directional_claim: Callable[[Mapping[str, float]], Any] | None = None
    # finding 12: singleton-q versus all-Q target equivalence
    target_equivalence: Callable[[Sequence[float], Sequence[float]], Any] | None = None
    # finding 13: production-like AMP path exercised against an instrumented harness
    amp_smoke: Callable[[Any], Any] | None = None
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


@dataclass
class AmpStepHarness:
    """Instrumented production-like AMP step. Candidate cannot self-report success."""
    gradient: float
    events: list[str] = field(default_factory=list)
    stepped: bool = False
    ema_updated: bool = False
    _autocast_active: bool = False
    _forward_seen: bool = False
    _backward_seen: bool = False
    _unscaled: bool = False
    _gate_passed: bool = False

    def autocast(self):
        harness = self
        class _Ctx:
            def __enter__(self):
                harness._autocast_active = True
                harness.events.append("autocast_enter")
                return harness
            def __exit__(self, exc_type, exc, tb):
                harness.events.append("autocast_exit")
                harness._autocast_active = False
                return False
        return _Ctx()

    def forward(self) -> None:
        if not self._autocast_active:
            raise RuntimeError("forward must execute under autocast")
        self.events.append("forward")
        self._forward_seen = True

    def scaler_scale_backward(self) -> None:
        if self._autocast_active or not self._forward_seen:
            raise RuntimeError("backward must execute after autocast forward")
        self.events.append("scaler_scale_backward")
        self._backward_seen = True

    def scaler_unscale(self) -> None:
        if not self._backward_seen:
            raise RuntimeError("unscale before backward")
        self.events.append("scaler_unscale")
        self._unscaled = True

    def gradient_gate(self) -> None:
        if not self._unscaled:
            raise RuntimeError("gradient gate before unscale")
        self.events.append("gradient_gate")
        if not math.isfinite(float(self.gradient)) or float(self.gradient) == 0.0:
            raise RuntimeError("mandatory gradient rejected")
        self._gate_passed = True

    def optimizer_step(self) -> None:
        self.events.append("optimizer_step")
        if not self._gate_passed:
            raise RuntimeError("optimizer step before live-gradient gate")
        self.stepped = True

    def ema_step(self) -> None:
        self.events.append("ema_step")
        if not self.stepped:
            raise RuntimeError("EMA before optimizer step")
        self.ema_updated = True

# ---------------------------------------------------------------- finding 1
def attack_nonfinite_gradient_accepted(candidate: Candidate) -> dict:
    """NaN/Inf must reject, while a healthy finite gradient must still run."""
    if candidate.gate_mandatory_gradients is None:
        return _na(1, "gate_mandatory_gradients")
    missed = []
    for label, value in (("nan", float("nan")), ("posinf", float("inf")),
                         ("neginf", float("-inf"))):
        refused, _ = _run(candidate.gate_mandatory_gradients,
                          {"backbone": {"blocks.0.attention.query.weight": value},
                           "predictor": {"predictor.output_norm.weight": 1.0}})
        if not refused:
            missed.append(label)
    healthy_refused, _ = _run(candidate.gate_mandatory_gradients,
                              {"backbone": {"blocks.0.attention.query.weight": 1.0},
                               "predictor": {"predictor.output_norm.weight": 1.0}})
    return _verdict(1, not missed and not healthy_refused,
                    "reject every nonfinite gradient but accept a healthy finite fixture",
                    accepted_nonfinite=missed, healthy_refused=healthy_refused)

# ---------------------------------------------------------------- finding 2
def attack_one_moment_zero_accepted(candidate: Candidate) -> dict:
    """Both Adam moments independently reject zero, missing and nonfinite values."""
    if candidate.gate_mandatory_gradients is None:
        return _na(2, "gate_mandatory_gradients")
    base = {"backbone": {"blocks.0.attention.query.weight": 1.0},
            "predictor": {"predictor.output_norm.weight": 1.0}}
    accepted_bad = []
    for which in ("exp_avg", "exp_avg_sq"):
        for mode in ("zero", "missing", "nan"):
            moments = {"exp_avg": 1.0, "exp_avg_sq": 1.0}
            if mode == "zero":
                moments[which] = 0.0
            elif mode == "missing":
                del moments[which]
            else:
                moments[which] = float("nan")
            payload = dict(base)
            payload["moments"] = {"blocks.0.attention.query.weight": moments}
            refused, _ = _run(candidate.gate_mandatory_gradients, payload)
            if not refused:
                accepted_bad.append(which + ":" + mode)
    healthy = dict(base)
    healthy["moments"] = {"blocks.0.attention.query.weight":
                          {"exp_avg": 1.0, "exp_avg_sq": 1.0}}
    healthy_refused, _ = _run(candidate.gate_mandatory_gradients, healthy)
    return _verdict(2, not accepted_bad and not healthy_refused,
                    "both moments must be independently live",
                    accepted_bad_moments=accepted_bad, healthy_refused=healthy_refused)

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
    """Dead predictor must reject; healthy predictor/backbone must remain runnable."""
    if candidate.gate_mandatory_gradients is None:
        return _na(4, "gate_mandatory_gradients")
    dead = {"backbone": {"blocks.0.attention.query.weight": 1.0,
                         "blocks.0.attention_norm.weight": 1.0},
            "predictor": {"predictor.cross_attention.in_proj_weight": 0.0,
                          "predictor.output_norm.weight": 0.0}}
    dead_refused, _ = _run(candidate.gate_mandatory_gradients, dead)
    healthy = {"backbone": {"blocks.0.attention.query.weight": 1.0,
                            "blocks.0.attention_norm.weight": 1.0},
               "predictor": {"predictor.cross_attention.in_proj_weight": 1.0,
                             "predictor.output_norm.weight": 1.0}}
    healthy_refused, _ = _run(candidate.gate_mandatory_gradients, healthy)
    return _verdict(4, dead_refused and not healthy_refused,
                    "predictor is mandatory but valid mechanics cannot be refused",
                    healthy_refused=healthy_refused)

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
        return _verdict("5+6", False, "valid variable-support routing fixture was refused")
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
    """N_eff_entropy and N_eff_participation must carry distinct analytic values."""
    if candidate.routing_metrics is None:
        return _na(7, "routing_metrics")
    p = [0.5, 0.25, 0.25]
    expected_entropy = math.exp(-sum(x * math.log(x) for x in p))
    expected_participation = 1.0 / sum(x * x for x in p)
    if math.isclose(expected_entropy, expected_participation, abs_tol=1e-3):
        return {"finding": 7, "verdict": ATTACK_DEFECTIVE,
                "note": "attack premise broken: the two metrics do not disagree"}
    refused, report = _run(candidate.routing_metrics, [p], [[True, True, True]])
    if refused or not isinstance(report, Mapping):
        return _verdict(7, False, "valid routing metric fixture must execute")
    got_e = report.get("N_eff_entropy")
    got_p = report.get("N_eff_participation")
    try:
        e0, p0 = float(got_e[0]), float(got_p[0])
    except Exception:  # noqa: BLE001
        return _verdict(7, False, "both named per-query metrics must be present")
    defended = (math.isclose(e0, expected_entropy, rel_tol=1e-6)
                and math.isclose(p0, expected_participation, rel_tol=1e-6)
                and not math.isclose(e0, p0, rel_tol=1e-9))
    return _verdict(7, defended,
                    "each metric name must carry its own analytic per-query value",
                    expected={"N_eff_entropy": expected_entropy,
                              "N_eff_participation": expected_participation},
                    reported={"N_eff_entropy": e0, "N_eff_participation": p0})

# ---------------------------------------------------------------- finding 8
def attack_routing_analytic_mutations(candidate: Candidate) -> dict:
    """Mutate query support, key support, masks, normalization and routing mass independently."""
    if candidate.routing_metrics is None:
        return _na(8, "routing_metrics")

    def snap(weights: Sequence[Sequence[float]],
             masks: Sequence[Sequence[bool]]) -> Mapping[str, Any] | None:
        refused, report = _run(candidate.routing_metrics,
                               [list(row) for row in weights],
                               [list(row) for row in masks])
        return None if refused or not isinstance(report, Mapping) else report

    failures = []
    baseline_w = [[1.0, 1.0, 0.0, 100.0], [3.0, 1.0, 0.0, 100.0]]
    baseline_m = [[True, True, False, False], [True, True, False, False]]
    base = snap(baseline_w, baseline_m)
    if base is None:
        return _verdict(8, False, "valid analytic routing fixture was refused")

    expected_second = math.exp(-(.75 * math.log(.75) + .25 * math.log(.25)))
    expected_cos = 0.8944271909999159
    checks = {
        "N_eff_entropy": ([2.0, expected_second], 1e-6),
        "N_eff_participation": ([2.0, 1.6], 1e-6),
        "top1_mass": ([0.5, 0.75], 1e-6),
        "valid_keys": ([2, 2], 0.0),
    }
    for key, (expected, tol) in checks.items():
        got = base.get(key)
        if got is None or len(got) != len(expected) or any(
                not math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)
                for a, b in zip(got, expected)):
            failures.append({"mutation": "baseline_" + key, "expected": expected, "got": got})
    if not math.isclose(float(base.get("query_map_cosine", float("nan"))),
                        expected_cos, rel_tol=1e-6):
        failures.append({"mutation": "baseline_query_map_cosine",
                         "expected": expected_cos, "got": base.get("query_map_cosine")})

    one_query = snap([baseline_w[0]], [baseline_m[0]])
    for key in ("N_eff_entropy", "N_eff_participation", "top1_mass", "valid_keys"):
        got = None if one_query is None else one_query.get(key)
        if got is None or len(got) != 1:
            failures.append({"mutation": "query_support", "metric": key, "got": got})

    four = snap([[1.0, 1.0, 1.0, 1.0]], [[True, True, True, True]])
    if four is None or four.get("valid_keys") != [4] or not math.isclose(
            float(four.get("N_eff_entropy", [float("nan")])[0]), 4.0, rel_tol=1e-6):
        failures.append({"mutation": "key_support", "got": four})

    no_masked_mass = snap([[1.0, 1.0, 0.0, 0.0], [3.0, 1.0, 0.0, 0.0]], baseline_m)
    for key in ("N_eff_entropy", "N_eff_participation", "top1_mass", "valid_keys"):
        if no_masked_mass is None or list(no_masked_mass.get(key, ())) != list(base.get(key, ())):
            failures.append({"mutation": "masked_mass", "metric": key})

    scaled = snap([[10.0 * x for x in row] for row in baseline_w], baseline_m)
    for key in ("N_eff_entropy", "N_eff_participation", "top1_mass", "query_map_cosine"):
        a, b = base.get(key), None if scaled is None else scaled.get(key)
        if isinstance(a, Sequence) and not isinstance(a, (str, bytes)):
            if b is None or len(a) != len(b) or any(
                    not math.isclose(float(x), float(y), rel_tol=1e-6)
                    for x, y in zip(a, b)):
                failures.append({"mutation": "normalization_denominator", "metric": key})
        elif b is None or not math.isclose(float(a), float(b), rel_tol=1e-6):
            failures.append({"mutation": "normalization_denominator", "metric": key})

    onehot = snap([[1.0, 0.0, 0.0, 0.0]], [[True, True, True, True]])
    if onehot is None or not math.isclose(float(onehot.get("N_eff_entropy", [9])[0]), 1.0,
                                          abs_tol=1e-6) or not math.isclose(
            float(onehot.get("top1_mass", [0])[0]), 1.0, abs_tol=1e-6):
        failures.append({"mutation": "routing_mass", "got": onehot})

    perm_w = [[100.0, 1.0, 1.0, 0.0], [100.0, 1.0, 3.0, 0.0]]
    perm_m = [[False, True, True, False], [False, True, True, False]]
    perm = snap(perm_w, perm_m)
    for key in ("N_eff_entropy", "N_eff_participation", "top1_mass", "query_map_cosine"):
        a, b = base.get(key), None if perm is None else perm.get(key)
        if isinstance(a, Sequence) and not isinstance(a, (str, bytes)):
            if b is None or len(a) != len(b) or any(
                    not math.isclose(float(x), float(y), rel_tol=1e-6)
                    for x, y in zip(a, b)):
                failures.append({"mutation": "permutation", "metric": key})
        elif b is None or not math.isclose(float(a), float(b), rel_tol=1e-6):
            failures.append({"mutation": "permutation", "metric": key})

    return _verdict(8, not failures,
                    "all five required analytic mutation families must match known answers",
                    failures=failures)

# ---------------------------------------------------------------- finding 9
def attack_g5_refit_is_not_a_refit(candidate: Candidate) -> dict:
    """A donor-held-out synthetic refit must change evaluation predictions with the fit split."""
    if candidate.refit is None:
        return _na(9, "refit")
    eval_donors = ["eval_a", "eval_b"]
    a = {"fit_donors": ["fit_a1", "fit_a2", "fit_a3", "fit_a4"],
         "fit_values": [0.0, 0.0, 0.0, 0.0],
         "eval_donors": eval_donors, "eval_values": [7.0, 9.0]}
    b = {"fit_donors": ["fit_b1", "fit_b2", "fit_b3", "fit_b4"],
         "fit_values": [1.0, 2.0, 3.0, 4.0],
         "eval_donors": eval_donors, "eval_values": [7.0, 9.0]}
    if set(a["fit_donors"]) & set(eval_donors) or set(b["fit_donors"]) & set(eval_donors):
        return {"finding": 9, "verdict": ATTACK_DEFECTIVE,
                "note": "attack fixture is not donor-held-out"}
    refused_a, fit_a = _run(candidate.refit, a)
    refused_b, fit_b = _run(candidate.refit, b)
    refused_repeat, fit_a2 = _run(candidate.refit, a)
    if refused_a or refused_b or refused_repeat:
        return _verdict(9, False, "valid synthetic held-out refit fixture was refused")
    try:
        pa = [float(x) for x in fit_a["predictions"]]
        pb = [float(x) for x in fit_b["predictions"]]
        pa2 = [float(x) for x in fit_a2["predictions"]]
    except Exception:  # noqa: BLE001
        return _verdict(9, False, "refit must return held-out predictions")
    analytic = (pa == [0.0, 0.0] and pb == [2.5, 2.5])
    deterministic = pa2 == pa
    changed = pb != pa
    return _verdict(9, analytic and deterministic and changed,
                    "held-out predictions must be analytically refit-dependent and deterministic",
                    predictions_a=pa, predictions_b=pb, repeat_a=pa2)

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
    """CELL-only and identity-only controls must each independently limit the claim."""
    if candidate.directional_claim is None:
        return _na(11, "directional_claim")
    cases = [
        ("cell_only_explains",
         {"observed": 1.0, "cell_only_control": 1.0, "identity_only_control": 0.0}, False),
        ("identity_only_explains",
         {"observed": 1.0, "cell_only_control": 0.0, "identity_only_control": 1.0}, False),
        ("neither_explains",
         {"observed": 1.0, "cell_only_control": 0.0, "identity_only_control": 0.0}, True),
    ]
    failures = []
    for label, payload, expected in cases:
        refused, claim = _run(candidate.directional_claim, payload)
        if refused:
            failures.append({"case": label, "reason": "valid control fixture refused"})
            continue
        asserted = bool(claim) if not isinstance(claim, Mapping) else bool(claim.get("structural"))
        if asserted is not expected:
            failures.append({"case": label, "expected_structural": expected,
                             "reported_structural": asserted})
    return _verdict(11, not failures,
                    "CELL-only and identity-only controls each constrain the structural claim",
                    failures=failures)

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
    """Exercise autocast -> backward -> unscale -> gate -> step -> EMA, not self-report."""
    if candidate.amp_smoke is None:
        return _na(13, "amp_smoke")
    expected_healthy = ["autocast_enter", "forward", "autocast_exit",
                        "scaler_scale_backward", "scaler_unscale",
                        "gradient_gate", "optimizer_step", "ema_step"]
    healthy = AmpStepHarness(gradient=1.0)
    healthy_refused, _ = _run(candidate.amp_smoke, healthy)
    if healthy_refused:
        return _verdict(13, False, "healthy production-like AMP fixture was refused",
                        events=healthy.events)
    if healthy.events != expected_healthy or not healthy.stepped or not healthy.ema_updated:
        return _verdict(13, False, "healthy AMP path did not execute the required operation order",
                        events=healthy.events, stepped=healthy.stepped,
                        ema_updated=healthy.ema_updated)
    dead = AmpStepHarness(gradient=0.0)
    dead_refused, _ = _run(candidate.amp_smoke, dead)
    expected_dead = ["autocast_enter", "forward", "autocast_exit",
                     "scaler_scale_backward", "scaler_unscale", "gradient_gate"]
    defended = (dead_refused and dead.events == expected_dead
                and not dead.stepped and not dead.ema_updated)
    return _verdict(13, defended,
                    "dead gradient must stop after unscale/gate and before optimizer/EMA",
                    healthy_events=healthy.events, dead_events=dead.events,
                    dead_refused=dead_refused)

# --------------------------------------------------------------- finding 14
def attack_optimizer_steps_before_gate(candidate: Candidate) -> dict:
    """Dead gradient stops pre-step; healthy gradient still reaches optimizer state."""
    if candidate.protected_update is None:
        return _na(14, "protected_update")
    ledger: dict[str, Any] = {"optimizer_state_entries": 0, "stepped": False}
    payload = {"mandatory_gradients": {"blocks.0.attention.query.weight": 0.0},
               "ledger": ledger}
    refused, _ = _run(candidate.protected_update, payload)
    stepped = bool(ledger.get("stepped")) or int(ledger.get("optimizer_state_entries", 0)) > 0
    if not refused or stepped:
        return _verdict(14, False, "dead mandatory gradient was not rejected before the step",
                        ledger=dict(ledger), refused=refused)
    healthy_ledger: dict[str, Any] = {"optimizer_state_entries": 0, "stepped": False}
    healthy_payload = {"mandatory_gradients": {"blocks.0.attention.query.weight": 1.0},
                       "ledger": healthy_ledger}
    healthy_refused, _ = _run(candidate.protected_update, healthy_payload)
    healthy_stepped = (bool(healthy_ledger.get("stepped"))
                       and int(healthy_ledger.get("optimizer_state_entries", 0)) > 0)
    return _verdict(14, not healthy_refused and healthy_stepped,
                    "gate must precede the step without degenerating into an always-refuse stub",
                    dead_ledger=dict(ledger), healthy_ledger=dict(healthy_ledger),
                    healthy_refused=healthy_refused)

# --------------------------------------------------------------- finding 15
def attack_implicit_endpoint_registry(candidate: Candidate) -> dict:
    """Extra l2__ keys cannot become endpoints; registered-only input must still run."""
    if candidate.select_endpoints is None:
        return _na(15, "select_endpoints")
    keys = ["l2__broad_common", "l2__local", "l2__recurrent_5pct",
            "l2__recurrent_1pct", "l2__unregistered_experimental", "raw__local"]
    refused, selected = _run(candidate.select_endpoints, keys)
    first_ok = False
    leaked = []
    chosen = []
    if refused:
        first_ok = True
    else:
        chosen = sorted(set(selected or ()))
        leaked = sorted(set(chosen) & {"l2__recurrent_5pct", "l2__recurrent_1pct",
                                       "l2__unregistered_experimental"})
        first_ok = not leaked and set(chosen) == {"l2__broad_common", "l2__local"}
    refused_clean, selected_clean = _run(
        candidate.select_endpoints, ["l2__broad_common", "l2__local"])
    clean = sorted(set(selected_clean or ())) if not refused_clean else []
    defended = first_ok and not refused_clean and set(clean) == {"l2__broad_common", "l2__local"}
    return _verdict(15, defended,
                    "registry may reject/filter extras but must accept exactly the registered endpoints",
                    leaked=leaked, selected=chosen, registered_only=clean,
                    registered_only_refused=refused_clean)

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
    def _refuse(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("refusal-only stub")
    refusal_only = Candidate(
        name="registry_probe_refusal_only",
        gate_mandatory_gradients=_refuse, movement_gate=_refuse,
        routing_report=_refuse, routing_metrics=_refuse, refit=_refuse,
        frozen_horizon=_refuse, directional_claim=_refuse,
        target_equivalence=_refuse, amp_smoke=_refuse, protected_update=_refuse,
        select_endpoints=_refuse,
    )
    refusal_report = run_suite(refusal_only)
    check("refusal_only_cannot_pass_any_attack",
          refusal_report["terminal"] == "STOP_F1B_ATTACK_SUITE"
          and not refusal_report["defended"],
          {"terminal": refusal_report["terminal"],
           "defended": refusal_report["defended"]})
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
