#!/usr/bin/env python3
"""Bounded V5 mechanical integration diagnostic (SYNTHETIC FIXTURES ONLY).

WHAT THIS IS
    A physical exercise of the assembled V5 update path end to end, over a
    bounded trajectory, verifying every mechanical invariant the diagnostic
    execution contract requires BEFORE any real reader_fit expression is
    consumed.

WHAT THIS IS NOT
    Not training. Not a scientific result. Not evidence about biology. The
    fixtures are synthetic tensors with no donor, no source and no pathology.
    A falling loss here demonstrates that gradients flow, nothing more.

WHY IT EXISTS
    `reader_fit` is ELIGIBLE_POOL__NOT_EXECUTION_AUTHORITY in the population
    access registry, and "new teacher training" is listed under
    forbidden_without_new_authority. The registry does permit
    "D1-A synthetic/u0-safe development when no real reader-fit expression is
    consumed". This script is exactly that, and it stops at that boundary.

GEOMETRY BINDING
    Every geometry number below is an explicitly DECLARED DIAGNOSTIC constant
    chosen for this harness. None is inherited from historical V4/V21
    production: not the 0.996 EMA momentum, not a six-block depth, not a
    128x8 batch geometry, not historical widths, seeds or visibility channels.
    They are declared here so a reader can object to them, and they carry no
    production authority. `DECLARED_WITHOUT_EXTERNAL_JUSTIFICATION` marks the
    ones that are conventional choices rather than derived quantities.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from copy import deepcopy

import torch

from sea_ad_jepa.v4.teacher_student_runtime import sample_uniform_target_blocks
from sea_ad_jepa.v5.inactive_update_reference import (
    build_reference_modules,
    run_inactive_reference_update,
    capture_reference_checkpoint,
    restore_reference_checkpoint,
)

# ---------------------------------------------------------------------------
# DECLARED DIAGNOSTIC GEOMETRY - not production authority, not inherited
# ---------------------------------------------------------------------------
DIAGNOSTIC_GEOMETRY = {
    "vocabulary_size": 96,
    "width": 32,
    "heads": 4,
    "blocks": 2,
    "ffn_width": 64,
    "dropout": 0.10,
    "cells_per_update": 12,
    "target_block_count": 4,
    "mask_fraction": 0.40,
    "views_per_update": 2,
    "max_teacher_tokens_per_microbatch": 48,
    "_justification": "DECLARED_WITHOUT_EXTERNAL_JUSTIFICATION: sized to exercise "
                      "multi-head, multi-block, multi-operator and multi-microbatch "
                      "paths on CPU within a bounded budget. Carries no production "
                      "authority and must be re-derived from real dataset geometry "
                      "before any production run.",
    "_budget_note": "A first attempt declared vocab=256/width=64/cells=24 and was "
                    "measured at 169.6 s per update, i.e. ~3.8 h for the 80 updates "
                    "this diagnostic runs. The geometry was reduced for tractability "
                    "ONLY. Every invariant verified here is geometry-independent - "
                    "step-once, teacher-detached, EMA-follows-step, moments populate, "
                    "restart-reproduces - so the reduction changes the cost and not "
                    "what is proved. Recorded rather than silently applied.",
}
DIAGNOSTIC_OPTIMIZER = {
    "learning_rate": 3e-4,
    "betas": (0.9, 0.999),
    "eps": 1e-8,
    "weight_decay": 0.01,
    "_justification": "DECLARED_WITHOUT_EXTERNAL_JUSTIFICATION: conventional AdamW "
                      "defaults, chosen to make optimizer mechanics observable.",
}
# Deliberately NOT 0.996. The historical value is not inherited; this one is
# declared for the diagnostic and is not a production EMA timescale.
DIAGNOSTIC_EMA_MOMENTUM = 0.99
DIAGNOSTIC_EMA_NOTE = ("DECLARED_WITHOUT_EXTERNAL_JUSTIFICATION and deliberately "
                       "distinct from the historical 0.996 so that inheritance "
                       "would be visible as a mismatch rather than silent.")
INIT_SEED = 20260925
RUN_SEED = 20260925
FIXTURE_SEED = 4455661


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def tensor_fingerprint(module) -> str:
    """Order-stable digest of a module's parameters, keyed by NAME not position."""
    h = hashlib.sha256()
    for name, p in sorted(module.state_dict().items()):
        h.update(name.encode("utf-8"))
        h.update(p.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def build_fixture(update_index: int):
    """Synthetic fixture. Cell identity is an explicit stable key, never a position."""
    g = torch.Generator().manual_seed(FIXTURE_SEED + update_index)
    n = DIAGNOSTIC_GEOMETRY["cells_per_update"]
    vocab = DIAGNOSTIC_GEOMETRY["vocabulary_size"]
    ops = [(i % 3) for i in range(n)]
    measured = torch.zeros((n, vocab), dtype=torch.bool)
    per_op = {}
    budget = DIAGNOSTIC_GEOMETRY["max_teacher_tokens_per_microbatch"]
    for op in sorted(set(ops)):
        # Per-operator support must never exceed the microbatch token budget:
        # a single cell that cannot fit is a hard refusal in the harness, and
        # an earlier geometry hit exactly that. Assert rather than rely on care.
        k = 24 + 12 * op
        if k > budget:
            raise ValueError(
                f"STOP_FIXTURE_GEOMETRY: operator {op} support {k} exceeds "
                f"max_teacher_tokens_per_microbatch {budget}")
        if k > vocab:
            raise ValueError(f"STOP_FIXTURE_GEOMETRY: support {k} exceeds vocab {vocab}")
        idx = torch.randperm(vocab, generator=g)[:k].sort().values
        per_op[op] = idx
    for row, op in enumerate(ops):
        measured[row, per_op[op]] = True
    expression = torch.randn(n, vocab, generator=g)
    expression[~measured] = 0.0
    # stable scientific identity keys - unique, explicit, not storage position
    cells = torch.tensor([900_000 + update_index * 1000 + i for i in range(n)],
                         dtype=torch.int64)
    weights = (torch.rand(n, generator=g) * 2.5 + 0.25).to(torch.float32)
    views = [
        sample_uniform_target_blocks(
            measured, production_seed=8813003, cell_indices=cells,
            sample_pass=update_index, view_index=v,
            mask_fraction=DIAGNOSTIC_GEOMETRY["mask_fraction"],
            block_count=DIAGNOSTIC_GEOMETRY["target_block_count"])
        for v in range(DIAGNOSTIC_GEOMETRY["views_per_update"])
    ]
    return (expression, measured, cells, ops, weights, views,
            {op: int(len(ix)) for op, ix in per_op.items()})


def make_modules():
    return build_reference_modules(
        vocabulary_size=DIAGNOSTIC_GEOMETRY["vocabulary_size"],
        width=DIAGNOSTIC_GEOMETRY["width"],
        heads=DIAGNOSTIC_GEOMETRY["heads"],
        blocks=DIAGNOSTIC_GEOMETRY["blocks"],
        ffn_width=DIAGNOSTIC_GEOMETRY["ffn_width"],
        dropout=DIAGNOSTIC_GEOMETRY["dropout"],
        learning_rate=DIAGNOSTIC_OPTIMIZER["learning_rate"],
        betas=DIAGNOSTIC_OPTIMIZER["betas"],
        eps=DIAGNOSTIC_OPTIMIZER["eps"],
        weight_decay=DIAGNOSTIC_OPTIMIZER["weight_decay"],
        init_seed=INIT_SEED,
    )


def adam_moment_state(modules):
    """Return (n_params_with_state, n_exp_avg_nonzero, n_exp_avg_sq_nonzero)."""
    st = modules.optimizer.state
    have = nz1 = nz2 = 0
    for p, s in st.items():
        if "exp_avg" not in s:
            continue
        have += 1
        if float(s["exp_avg"].abs().sum()) > 0:
            nz1 += 1
        if float(s["exp_avg_sq"].abs().sum()) > 0:
            nz2 += 1
    return have, nz1, nz2


def run_trajectory(modules, updates, start_index=0, collect=True):
    rows = []
    for u in range(start_index, start_index + updates):
        data = build_fixture(u)
        before_online = {k: v.detach().clone()
                         for k, v in modules.online.state_dict().items()}
        before_teacher = tensor_fingerprint(modules.teacher)
        rep = run_inactive_reference_update(
            modules,
            expression=data[0], measurement_mask=data[1], stable_cell_keys=data[2],
            operator_ids=data[3], scientific_cell_weights=data[4],
            target_block_views=data[5], measured_tokens_by_operator=data[6],
            max_teacher_tokens_per_microbatch=DIAGNOSTIC_GEOMETRY[
                "max_teacher_tokens_per_microbatch"],
            run_seed=RUN_SEED, update_index=u,
            ema_momentum=DIAGNOSTIC_EMA_MOMENTUM,
        )
        after_online = modules.online.state_dict()
        moved = 0
        max_delta = 0.0
        for k, v in after_online.items():
            if not v.is_floating_point():
                continue
            d = float((v.detach() - before_online[k]).abs().max())
            max_delta = max(max_delta, d)
            if d > 0:
                moved += 1
        have, nz1, nz2 = adam_moment_state(modules)
        # Fail closed on the report contract. An earlier version of this driver
        # read rep.get("optimizer_step") and rep.get("gradient_report"); NEITHER
        # key exists. The first defaulted to -1 and produced a loud false FAIL,
        # but the second defaulted to None and silently recorded nothing, so the
        # protected-gradient gate was never actually inspected. Missing keys now
        # raise instead of defaulting.
        required = ("loss", "optimizer_step_before", "optimizer_step_after",
                    "gradient_gate", "ema_max_abs_error", "microbatches",
                    "scientific_weight_mass", "cells", "views")
        missing = [k for k in required if k not in rep]
        if missing:
            raise KeyError(f"STOP_HARNESS_REPORT_CONTRACT_CHANGED: missing {missing}")
        if collect:
            rows.append({
                "update_index": u,
                "loss": float(rep["loss"]),
                "optimizer_step_before": int(rep["optimizer_step_before"]),
                "optimizer_step_after": int(rep["optimizer_step_after"]),
                "stepped_exactly_once":
                    int(rep["optimizer_step_after"]) - int(rep["optimizer_step_before"]) == 1,
                "ema_max_abs_error": float(rep["ema_max_abs_error"]),
                "gradient_gate": rep["gradient_gate"],
                "microbatches": rep["microbatches"],
                "scientific_weight_mass": rep["scientific_weight_mass"],
                "cells": rep["cells"],
                "views": rep["views"],
                "teacher_changed": tensor_fingerprint(modules.teacher) != before_teacher,
                "online_tensors_moved": moved,
                "max_param_delta": max_delta,
                "adam_params_with_state": have,
                "adam_exp_avg_nonzero": nz1,
                "adam_exp_avg_sq_nonzero": nz2,
                "report_keys": sorted(rep.keys()),
                "online_fingerprint": tensor_fingerprint(modules.online),
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--updates", type=int, default=40)
    ap.add_argument("--checkpoint-at", type=int, default=20)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS__USE_NEW_VERSIONED_DIRECTORY")
    os.makedirs(a.out_dir, exist_ok=True)

    t0 = time.time()
    print("=== V5 mechanical integration diagnostic (SYNTHETIC ONLY) ===")

    # ---- continuous reference trajectory --------------------------------
    cont = make_modules()
    cont_rows = run_trajectory(cont, a.updates, 0)
    cont_fp = tensor_fingerprint(cont.online)

    # ---- interrupted trajectory: checkpoint, restore, resume ------------
    inter = make_modules()
    _ = run_trajectory(inter, a.checkpoint_at, 0)
    ckpt = capture_reference_checkpoint(
        inter, next_update_index=a.checkpoint_at, presentations_seen=a.checkpoint_at)
    fresh = make_modules()
    restored_cursor = restore_reference_checkpoint(fresh, ckpt)
    resumed_rows = run_trajectory(
        fresh, a.updates - a.checkpoint_at, a.checkpoint_at)
    resumed_fp = tensor_fingerprint(fresh.online)

    restart_reproduces = (resumed_fp == cont_fp)

    # ---- invariant verdicts --------------------------------------------
    steps = [r["optimizer_step_after"] for r in cont_rows]
    steps_monotone_by_one = (
        all(r["stepped_exactly_once"] for r in cont_rows)
        and all(steps[i + 1] - steps[i] == 1 for i in range(len(steps) - 1)))
    # the harness computes its own EMA residual; require it to be at float noise
    ema_exact = all(r["ema_max_abs_error"] <= 1e-6 for r in cont_rows)
    # The protected-gradient gate must be AFFIRMATIVE, not merely present.
    # An earlier version asserted `is not None`, which is close to a tautology:
    # it would pass on any object the harness returned, including one reporting
    # dead gradients. Assert the actual contract instead.
    def gate_affirmative(g):
        return (isinstance(g, dict)
                and int(g.get("missing", -1)) == 0
                and int(g.get("nonfinite", -1)) == 0
                and int(g.get("exact_zero", -1)) == 0
                and int(g.get("teacher_gradients", -1)) == 0
                and float(g.get("max_abs_gradient", 0.0)) > 0.0)
    gate_ok = all(gate_affirmative(r["gradient_gate"]) for r in cont_rows)
    teacher_never_changed_without_step = all(r["teacher_changed"] for r in cont_rows)
    all_moved = all(r["online_tensors_moved"] > 0 for r in cont_rows)
    adam_ok = all(r["adam_exp_avg_nonzero"] > 0 and r["adam_exp_avg_sq_nonzero"] > 0
                  for r in cont_rows[1:])
    losses = [r["loss"] for r in cont_rows]
    finite_losses = all(l == l and abs(l) != float("inf") for l in losses)

    receipt = {
        "schema": "V5_MECHANICAL_INTEGRATION_DIAGNOSTIC_V1",
        "status": "SYNTHETIC_TESTED_ONLY__NOT_A_SCIENTIFIC_RESULT",
        "scope_statement": (
            "Synthetic fixtures only. No reader_fit, reader_validation, "
            "reader_oracle, foundation, sealed, Siletti, pathology or D_shared "
            "data was opened or read. No biological claim is made or implied."),
        "declared_geometry": DIAGNOSTIC_GEOMETRY,
        "declared_optimizer": DIAGNOSTIC_OPTIMIZER,
        "declared_ema_momentum": DIAGNOSTIC_EMA_MOMENTUM,
        "declared_ema_note": DIAGNOSTIC_EMA_NOTE,
        "legacy_inheritance_check": {
            "ema_momentum_is_historical_0_996": DIAGNOSTIC_EMA_MOMENTUM == 0.996,
            "block_depth_is_historical_six": DIAGNOSTIC_GEOMETRY["blocks"] == 6,
            "batch_geometry_is_historical_128x8":
                DIAGNOSTIC_GEOMETRY["cells_per_update"] == 128,
            "note": "all three must be false; geometry is declared, not inherited",
        },
        "seeds": {"init_seed": INIT_SEED, "run_seed": RUN_SEED,
                  "fixture_seed": FIXTURE_SEED},
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "torch": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device": (torch.cuda.get_device_name(0)
                            if torch.cuda.is_available() else None),
            "device_used": "cpu",
            "device_rationale": (
                "inactive_update_reference is documented as a bounded CPU "
                "mechanics harness; it was run on the device it is written for. "
                "Forcing CUDA would change the method rather than repair the "
                "infrastructure."),
            "gpu_memory_bytes_used": 0,
        },
        "producer_sha256": sha_file(os.path.abspath(__file__)),
        "updates_executed": a.updates,
        "checkpoint_at": a.checkpoint_at,
        "invariants": {
            "optimizer_steps_exactly_once_per_update": bool(steps_monotone_by_one),
            "optimizer_step_sequence": steps,
            "ema_advanced_on_every_successful_step":
                bool(teacher_never_changed_without_step),
            "online_parameters_moved_every_update": bool(all_moved),
            "adam_first_and_second_moments_populated": bool(adam_ok),
            "all_losses_finite": bool(finite_losses),
            "checkpoint_restart_reproduces_uninterrupted_run":
                bool(restart_reproduces),
            "restored_cursor": list(restored_cursor)
                if isinstance(restored_cursor, tuple) else restored_cursor,
        },
        "loss_trajectory": {
            "first": losses[0], "last": losses[-1],
            "min": min(losses), "max": max(losses),
            "all": losses,
            "interpretation_guard": (
                "A falling loss on synthetic tensors demonstrates gradient flow "
                "and nothing about biology."),
        },
        "fingerprints": {
            "continuous_online": cont_fp,
            "resumed_online": resumed_fp,
            "identical": bool(restart_reproduces),
        },
        "per_update": cont_rows,
        "wall_clock_seconds": round(time.time() - t0, 3),
        "training_authorized": False,
        "protected_outcome_opened": False,
        "real_reader_fit_expression_consumed": False,
    }

    receipt["invariants"]["ema_residual_at_float_noise"] = bool(ema_exact)
    receipt["invariants"]["protected_gradient_gate_present_every_update"] = bool(gate_ok)
    receipt["invariants"]["max_ema_residual"] = max(
        r["ema_max_abs_error"] for r in cont_rows)
    ok = all([steps_monotone_by_one, teacher_never_changed_without_step,
              all_moved, adam_ok, finite_losses, restart_reproduces,
              ema_exact, gate_ok])
    receipt["verdict"] = ("PASS_V5_MECHANICAL_INTEGRATION_SYNTHETIC"
                          if ok else "FAIL_V5_MECHANICAL_INTEGRATION_SYNTHETIC")

    rp = os.path.join(a.out_dir, "V5_MECHANICAL_INTEGRATION_DIAGNOSTIC_V1.json")
    with open(rp, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print(f"  updates executed        {a.updates}")
    print(f"  optimizer step sequence {steps[0]} .. {steps[-1]}  "
          f"exactly-once={steps_monotone_by_one}")
    print(f"  EMA advanced each step  {teacher_never_changed_without_step}")
    print(f"  params moved each step  {all_moved}")
    print(f"  Adam moments populated  {adam_ok}")
    print(f"  losses finite           {finite_losses}")
    print(f"  loss first -> last      {losses[0]:.6f} -> {losses[-1]:.6f}")
    print(f"  restart reproduces      {restart_reproduces}")
    print(f"  wall clock              {receipt['wall_clock_seconds']}s")
    print(f"\n=== VERDICT: {receipt['verdict']} ===")
    print(f"wrote {rp}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
