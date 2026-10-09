"""V2 ledger tests, including DEMONSTRATIONS that V1 was defective.

Self-audit principle applied here: asserting "V1 had a bug" is not evidence.
Each repair test first EXHIBITS the V1 defect on a concrete input, then shows
V2 handling the same input correctly. If a repair test cannot demonstrate the
original defect, the repair is unmotivated and the test is removed.
"""

from __future__ import annotations

import itertools

import numpy as np
import pytest
import torch

from sea_ad_jepa.v4.teacher_student_runtime import sample_uniform_target_blocks
from sea_ad_jepa.v5.inactive_update_reference import (
    build_reference_modules, run_inactive_reference_update)

from sea_ad_jepa.v5 import control_sensitivity_ledger_v1 as V1
from sea_ad_jepa.v5.control_sensitivity_ledger_v2 import (
    ControlSensitivityLedgerV2, DegenerateConfiguration, LegResult, run_leg,
    classify, classify_evidence, canonical_digest, canonical_edge_digest,
    require_structurally_distinct, require_intervention_effective,
    require_comparator_capacity, require_structurally_distinct_graphs,
    full_machine_snapshot, snapshot_changed_keys,
    FIRED, QUIET, REFUSED_DEGENERATE,
    SENSITIVE, VACUOUS_DID_NOT_FIRE, FALSE_POSITIVE_ON_HEALTHY,
    HEALTHY_LEG_UNEVALUABLE, SCORED_A_DEGENERATE_CONFIG, DEGENERATE_LEG_FIRED,
    INCOMPLETE_LEGS, MISLABELLED_LEG,
    EVIDENCE_INVALID, EVIDENCE_INCONCLUSIVE, EVIDENCE_POSITIVE, EVIDENCE_NEGATIVE)


# =========================================================================
# 1A — V1 certified a control whose healthy leg could not be evaluated
# =========================================================================
def test_1A_demonstrate_v1_defect_then_v2_repair():
    h = LegResult("healthy", REFUSED_DEGENERATE, {"reason": "unevaluable"})
    p = LegResult("planted", FIRED)
    d = LegResult("degenerate", REFUSED_DEGENERATE)

    v1h = V1.LegResult("healthy", V1.REFUSED_DEGENERATE, {"reason": "unevaluable"})
    v1p = V1.LegResult("planted", V1.FIRED)
    v1d = V1.LegResult("degenerate", V1.REFUSED_DEGENERATE)
    # THE DEFECT: V1 calls this SENSITIVE despite an unevaluable healthy leg
    assert V1.classify(v1h, v1p, v1d) == V1.SENSITIVE
    # THE REPAIR
    assert classify(h, p, d) == HEALTHY_LEG_UNEVALUABLE


def test_1A_every_leg_combination_is_named():
    """No combination may fall through to SENSITIVE by omission."""
    seen = set()
    for ho, po, do in itertools.product((FIRED, QUIET, REFUSED_DEGENERATE), repeat=3):
        v = classify(LegResult("healthy", ho), LegResult("planted", po),
                     LegResult("degenerate", do))
        seen.add(v)
        if (ho, po, do) == (QUIET, FIRED, REFUSED_DEGENERATE):
            assert v == SENSITIVE
        else:
            assert v != SENSITIVE, (ho, po, do)
    assert SENSITIVE in seen and VACUOUS_DID_NOT_FIRE in seen


def test_1A_missing_and_mislabelled_legs():
    ok = LegResult("planted", FIRED)
    assert classify(None, ok, LegResult("degenerate", REFUSED_DEGENERATE)) == INCOMPLETE_LEGS
    swapped = classify(LegResult("planted", QUIET), ok,
                       LegResult("degenerate", REFUSED_DEGENERATE))
    assert swapped == MISLABELLED_LEG


def test_1A_degenerate_leg_that_fires_is_named():
    assert classify(LegResult("healthy", QUIET), LegResult("planted", FIRED),
                    LegResult("degenerate", FIRED)) == DEGENERATE_LEG_FIRED


# =========================================================================
# 1C — V1 hashed repr(), and NumPy truncates repr
# =========================================================================
def test_1C_demonstrate_v1_repr_truncation_then_v2_repair():
    a = np.arange(10_000, dtype=np.int64)
    b = a.copy()
    b[5000] = -1                      # differs ONLY in the elided middle

    assert repr(a) == repr(b), "precondition: numpy elides the middle"
    # THE DEFECT: V1 sees two different arrays as identical and refuses
    with pytest.raises(V1.DegenerateConfiguration, match="byte-identical"):
        V1.require_distinct_arms(a, b, label="v1")
    # THE REPAIR: V2 reads full bytes and permits the comparison
    require_structurally_distinct(a, b, label="v2")
    assert canonical_digest(a) != canonical_digest(b)


def test_1C_truly_identical_arrays_still_refused():
    a = np.arange(10_000, dtype=np.int64)
    with pytest.raises(DegenerateConfiguration, match="structurally identical"):
        require_structurally_distinct(a, a.copy(), label="x")


def test_1C_same_object_refused():
    a = np.zeros(4)
    with pytest.raises(DegenerateConfiguration, match="same object"):
        require_structurally_distinct(a, a, label="x")


def test_1C_ordering_does_not_fake_a_structural_difference():
    g1 = [("A", "B"), ("B", "C"), ("C", "D")]
    g2 = [("C", "D"), ("A", "B"), ("B", "C")]          # same graph, listed differently
    assert canonical_edge_digest(g1) == canonical_edge_digest(g2)
    with pytest.raises(DegenerateConfiguration):
        require_structurally_distinct(sorted(g1), sorted(g2), label="reordered")


def test_1C_genuinely_different_graphs_are_distinct():
    g1 = [("A", "B"), ("B", "C")]
    g2 = [("A", "B"), ("B", "D")]
    assert canonical_edge_digest(g1) != canonical_edge_digest(g2)


def test_1C_ineffective_intervention_refused():
    before = np.array([1.0, 2.0, 3.0])
    with pytest.raises(DegenerateConfiguration, match="unchanged"):
        require_intervention_effective(before, before.copy(), label="noop shuffle")


def test_1C_effective_intervention_accepted():
    require_intervention_effective(np.array([1.0, 2.0]), np.array([2.0, 1.0]),
                                   label="real swap")


def test_1C_dtype_and_shape_participate_in_identity():
    assert canonical_digest(np.zeros(4, dtype=np.int64)) != canonical_digest(np.zeros(4, dtype=np.float64))
    assert canonical_digest(np.zeros((2, 2))) != canonical_digest(np.zeros(4))


# =========================================================================
# 1D — inconclusive evidence is not an invalid control
# =========================================================================
def test_1D_stage73r_is_inconclusive_not_invalid():
    """Stage73R: delta -0.008366, CI [-0.019597, +0.000169] includes zero."""
    v = classify_evidence(-0.008366299078667596,
                          -0.01959704363673176, 0.00016928217069961393,
                          experiment_valid=True)
    assert v == EVIDENCE_INCONCLUSIVE
    # V1 conflated this with a broken control
    with pytest.raises(V1.DegenerateConfiguration):
        V1.require_effect_resolvable(-0.01959704363673176, 0.00016928217069961393,
                                     label="v1")


def test_1D_stage73r_vs_no_graph_is_a_positive_effect():
    """context vs no_graph: CI [0.001367, 0.022093] excludes zero."""
    assert classify_evidence(0.01262420006074719,
                             0.0013672167662245327, 0.022092538220107316,
                             experiment_valid=True) == EVIDENCE_POSITIVE


def test_1D_invalid_experiment_outranks_any_interval():
    assert classify_evidence(5.0, 1.0, 9.0, experiment_valid=False) == EVIDENCE_INVALID


def test_1D_negative_effect_is_distinguishable():
    assert classify_evidence(-0.5, -0.9, -0.1, experiment_valid=True) == EVIDENCE_NEGATIVE


# =========================================================================
# 1B — refusal reason AND machine state, on the real harness
# =========================================================================
def _case():
    torch.manual_seed(707)
    n, vocab = 6, 32
    ops = [0, 1, 0, 1, 1, 0]
    op0 = torch.tensor([0, 1, 3, 5, 7, 9, 12, 15, 18, 21, 25, 29])
    op1 = torch.tensor([0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31])
    measured = torch.zeros((n, vocab), dtype=torch.bool)
    for r, o in enumerate(ops):
        measured[r, op0 if o == 0 else op1] = True
    expr = torch.randn(n, vocab); expr[~measured] = 0
    cells = torch.tensor([70_001, 70_002, 70_003, 70_004, 70_005, 70_006], dtype=torch.int64)
    w = torch.tensor([.4, 2.0, 1.1, .7, 3.2, .6], dtype=torch.float32)
    views = [sample_uniform_target_blocks(measured, production_seed=8813003,
             cell_indices=cells, sample_pass=0, view_index=v, mask_fraction=.40,
             block_count=4) for v in range(2)]
    return dict(expression=expr, measurement_mask=measured, stable_cell_keys=cells,
                operator_ids=ops, scientific_cell_weights=w, target_block_views=views,
                measured_tokens_by_operator={0: len(op0), 1: len(op1)},
                max_teacher_tokens_per_microbatch=40, run_seed=8113002,
                update_index=0, ema_momentum=.99)


def _modules():
    return build_reference_modules(vocabulary_size=32, width=16, heads=4, blocks=1,
                                   ffn_width=24, dropout=.10, learning_rate=3e-4,
                                   betas=(.9, .999), eps=1e-8, weight_decay=.01,
                                   init_seed=8113002)


def _probe_gate(damage):
    """COMPLETE before/after snapshot — every mutable tensor, not a sampled subset.

    The prior revision compared only the first optimizer step counter, the COUNT
    of populated Adam states and the teacher parameters. That left the online
    and predictor parameters, the individual moment TENSORS and the cursor free
    to move undetected, so the check verified less than its name claimed.
    """
    m, kw = _modules(), _case()
    before = full_machine_snapshot(m, cursor=0)
    handle = None
    if damage in ("zero", "nonfinite"):
        p = next(x for x in m.online.parameters() if x.requires_grad)
        fn = (lambda g: torch.zeros_like(g)) if damage == "zero" else (lambda g: g * float("nan"))
        handle = p.register_hook(fn)
    elif damage == "teacher":
        tp = next(iter(m.teacher.parameters())); tp.grad = torch.zeros_like(tp)
    refused, reason_ok = False, False
    try:
        run_inactive_reference_update(m, **kw)
    except RuntimeError as exc:
        refused = True
        reason_ok = "gradient gate failed" in str(exc)   # 1B: the EXPECTED cause
    finally:
        if handle is not None:
            handle.remove()
    after = full_machine_snapshot(m, cursor=0 if refused else 1)
    return refused, reason_ok, snapshot_changed_keys(before, after)


@pytest.mark.parametrize("damage", ["zero", "nonfinite", "teacher"])
def test_1B_planted_defect_refuses_and_leaves_ALL_state_byte_identical(damage):
    refused, reason_ok, changed = _probe_gate(damage)
    assert refused, f"{damage}: gate did not refuse"
    assert reason_ok, f"{damage}: refused for an UNEXPECTED reason - not proof the gate fired"
    assert changed == [], f"{damage}: state advanced despite refusal: {changed}"


def test_1B_healthy_execution_advances_the_expected_state():
    """The converse: a healthy update must move online, predictor, Adam and cursor."""
    refused, _, changed = _probe_gate(None)
    assert not refused
    assert changed, "a healthy update must actually advance state"
    fams = {k.split(".")[0].split("[")[0] for k in changed}
    for expected in ("online", "predictor", "teacher", "optimizer", "cursor"):
        assert any(f.startswith(expected) or expected in k
                   for f in fams for k in changed if k.startswith(expected)) or \
               any(k.startswith(expected) for k in changed), \
               f"healthy update did not advance {expected}: {sorted(fams)}"
    assert any(k.startswith("optimizer.state[") and k.endswith(".exp_avg") for k in changed), \
        "healthy update did not populate an Adam first moment"
    assert any(k.startswith("optimizer.state[") and k.endswith(".exp_avg_sq") for k in changed), \
        "healthy update did not populate an Adam second moment"


def test_1B_snapshot_covers_every_mutable_family():
    """Guard against the snapshot silently narrowing later."""
    m = _modules()
    snap = full_machine_snapshot(m, cursor=0)
    fams = {k.split(".")[0] for k in snap}
    assert {"online", "teacher", "predictor", "cursor"} <= fams, sorted(fams)
    n_params = sum(len(mod.state_dict()) for mod in (m.online, m.teacher, m.predictor))
    assert len([k for k in snap if not k.startswith(("optimizer", "cursor"))]) == n_params


def test_1B_snapshot_detects_a_single_perturbed_parameter():
    """A snapshot that cannot detect one changed weight is not a snapshot."""
    m = _modules()
    before = full_machine_snapshot(m, cursor=0)
    with torch.no_grad():
        next(iter(m.online.parameters())).add_(1e-6)
    changed = snapshot_changed_keys(before, full_machine_snapshot(m, cursor=0))
    assert len(changed) == 1 and changed[0].startswith("online."), changed


def test_1B_snapshot_detects_a_cursor_advance_alone():
    m = _modules()
    before = full_machine_snapshot(m, cursor=0)
    assert snapshot_changed_keys(before, full_machine_snapshot(m, cursor=1)) == ["cursor"]


def test_1B_an_unrelated_runtimeerror_is_not_counted_as_detection():
    """The V1 probe counted ANY RuntimeError as the gate firing."""
    m, kw = _modules(), _case()
    kw["expression"] = torch.randn(3, 32)      # wrong shape -> unrelated failure
    with pytest.raises(Exception) as ei:
        run_inactive_reference_update(m, **kw)
    assert "gradient gate failed" not in str(ei.value)


# =========================================================================
# ledger behaviour
# =========================================================================
def test_ledger_v2_records_and_digests():
    led = ControlSensitivityLedgerV2()
    v = led.record("c1",
                   healthy=LegResult("healthy", QUIET),
                   planted=LegResult("planted", FIRED),
                   degenerate=LegResult("degenerate", REFUSED_DEGENERATE),
                   source="src/sea_ad_jepa/v5/inactive_update_reference.py")
    assert v == SENSITIVE
    s = led.summary()
    assert s["all_sensitive"] is True and s["training_authorized"] is False
    assert len(s["ledger_digest"]) == 64


def test_ledger_v2_names_a_vacuous_control_in_summary():
    led = ControlSensitivityLedgerV2()
    led.record("bad", healthy=LegResult("healthy", QUIET),
               planted=LegResult("planted", QUIET),
               degenerate=LegResult("degenerate", REFUSED_DEGENERATE), source="t")
    s = led.summary()
    assert s["all_sensitive"] is False and s["not_sensitive"] == ["bad"]


def test_ledger_v2_refuses_empty_and_duplicate():
    with pytest.raises(ValueError):
        ControlSensitivityLedgerV2().summary()
    led = ControlSensitivityLedgerV2()
    kw = dict(healthy=LegResult("healthy", QUIET), planted=LegResult("planted", FIRED),
              degenerate=LegResult("degenerate", REFUSED_DEGENERATE), source="t")
    led.record("x", **kw)
    with pytest.raises(ValueError):
        led.record("x", **kw)


# =========================================================================
# guards added after review: nonfinite / contradictory intervals, graph canon
# =========================================================================
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_evidence_rejects_nonfinite_bounds(bad):
    with pytest.raises(ValueError, match="finite real number"):
        classify_evidence(bad, -1.0, 1.0, experiment_valid=True)
    with pytest.raises(ValueError, match="finite real number"):
        classify_evidence(0.0, bad, 1.0, experiment_valid=True)
    with pytest.raises(ValueError, match="finite real number"):
        classify_evidence(0.0, -1.0, bad, experiment_valid=True)


def test_evidence_rejects_estimate_outside_its_own_interval():
    """A mean outside its CI is arithmetically impossible upstream."""
    with pytest.raises(ValueError, match="contradictory estimate"):
        classify_evidence(5.0, -1.0, 1.0, experiment_valid=True)
    with pytest.raises(ValueError, match="contradictory estimate"):
        classify_evidence(-5.0, -1.0, 1.0, experiment_valid=True)


def test_evidence_rejects_inverted_interval():
    with pytest.raises(ValueError, match="ci_lower exceeds ci_upper"):
        classify_evidence(0.0, 1.0, -1.0, experiment_valid=True)


def test_evidence_still_accepts_the_real_stage73r_numbers():
    """The guards must not reject genuine data."""
    assert classify_evidence(-0.008366299078667596,
                             -0.01959704363673176, 0.00016928217069961393,
                             experiment_valid=True) == EVIDENCE_INCONCLUSIVE


def test_graph_comparison_uses_canonical_edges_not_list_order():
    """Edge-list ordering alone must not make identical graphs look distinct."""
    g1 = [("A", "B"), ("B", "C"), ("C", "D")]
    g2 = [("C", "D"), ("A", "B"), ("B", "C")]
    # the generic detector, given raw lists, WOULD call these distinct
    require_structurally_distinct(g1, g2, label="generic-on-raw-lists")
    # the graph-aware detector correctly refuses
    with pytest.raises(DegenerateConfiguration, match="structurally identical"):
        require_structurally_distinct_graphs(g1, g2, label="graph-aware")


def test_graph_comparison_accepts_genuinely_different_graphs():
    require_structurally_distinct_graphs([("A", "B")], [("A", "C")], label="real")


def test_graph_comparison_rejects_same_object():
    g = [("A", "B")]
    with pytest.raises(DegenerateConfiguration, match="same object"):
        require_structurally_distinct_graphs(g, g, label="x")
