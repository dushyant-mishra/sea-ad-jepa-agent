"""Adoption regression: the gate must stop a K0-like update before it steps.

Proves three things about the actual successor training step, not about a
standalone helper:

1. a historical K0-like update is rejected BEFORE the optimizer steps;
2. a corrected K1-like update proceeds and moves parameters;
3. the gate cannot be bypassed through an alternate optimizer path.

The first two execute the real `phase_e.run_update` source with only the
declared substitutions, on GPU, at reduced scale. Reduced scale is sufficient:
batch 4 / microbatch 2 reproduces the full 48/48 dead signature.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ROOTS = (Path("/mnt/d/Jepa project"), Path("D:/Jepa project"))


def _canonical() -> Path:
    for root in CANONICAL_ROOTS:
        if (root / "scripts/v4/stage81a3_prod41k_engineering_smoke.py").is_file():
            return root
    pytest.skip("canonical repository not reachable")


def _phase_e():
    root = _canonical()
    sys.path.insert(0, str(root / "src"))
    sys.path.insert(0, str(root / "exports" / "static_context_decomposition_v4_20260821"))
    spec = importlib.util.spec_from_file_location(
        "phase_e", root / "scripts" / "v4" / "stage81a3_prod41k_engineering_smoke.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["phase_e"] = module
    spec.loader.exec_module(module)
    return module


def _run(mode: str, batch: int = 4, micro: int = 2):
    from scripts.v4.c2_corrective_run_update_v3 import build_variant
    from scripts.v4.c2_synthetic_loader_v3 import SyntheticTrainLoader, synthetic_cohort

    phase_e = _phase_e()
    device = torch.device("cuda")
    seed = 8113002
    online, target, predictor, optimizer, scaler, controller = phase_e.build_components(
        seed, device)
    update = build_variant(phase_e, mode)
    loader = SyntheticTrainLoader(seed=seed)
    cohort = synthetic_cohort(batch)
    sampler = torch.Generator().manual_seed(seed)
    online.train()
    predictor.train()
    target.eval()
    before = {n: p.detach().float().clone() for n, p in online.named_parameters()}
    result = update(
        loader=loader, cohort=cohort, sampler=sampler, cursor=0, seed=seed,
        microbatch=micro, effective_batch=batch, device=device, online=online,
        target=target, predictor=predictor, optimizer=optimizer, scaler=scaler,
        controller=controller,
    )
    return online, optimizer, before, result


def _requires_cuda() -> None:
    if not torch.cuda.is_available():
        pytest.skip("CUDA required for the adoption regression")


def test_gate_stops_a_k0_like_update_before_the_optimizer_steps() -> None:
    """The historical condition must never reach the optimizer."""
    _requires_cuda()
    with pytest.raises(RuntimeError) as excinfo:
        _run("gated_historical")
    message = str(excinfo.value)
    assert "mandatory gradient gate rejected" in message
    assert "EXACT_ZERO=48" in message, message


def test_gate_stops_before_any_optimizer_state_exists() -> None:
    """Rejection must precede the step, not merely report after it."""
    _requires_cuda()
    from scripts.v4.c2_corrective_run_update_v3 import build_variant
    from scripts.v4.c2_synthetic_loader_v3 import SyntheticTrainLoader, synthetic_cohort

    phase_e = _phase_e()
    device = torch.device("cuda")
    seed = 8113002
    online, target, predictor, optimizer, scaler, controller = phase_e.build_components(
        seed, device)
    update = build_variant(phase_e, "gated_historical")
    loader = SyntheticTrainLoader(seed=seed)
    online.train()
    predictor.train()
    target.eval()
    before = {n: p.detach().float().clone() for n, p in online.named_parameters()}
    with pytest.raises(RuntimeError):
        update(
            loader=loader, cohort=synthetic_cohort(4),
            sampler=torch.Generator().manual_seed(seed), cursor=0, seed=seed,
            microbatch=2, effective_batch=4, device=device, online=online,
            target=target, predictor=predictor, optimizer=optimizer, scaler=scaler,
            controller=controller,
        )
    # AdamW creates state lazily inside step(). No state means no step occurred.
    assert len(optimizer.state) == 0, "optimizer stepped despite the gate"
    for name, param in online.named_parameters():
        assert torch.equal(param.detach().float(), before[name]), name


def test_corrected_update_passes_the_gate_and_moves_parameters() -> None:
    _requires_cuda()
    from scripts.v4.c2_mandatory_gradient_gate_v1 import (
        FROZEN_MANDATORY_REGISTRY, gate_module)

    online, optimizer, before, result = _run("successor")
    assert result["step_succeeded"] is True
    assert result["online_moved"] is True
    assert result["ema_equation"]["equal"] is True

    report = gate_module(online, list(FROZEN_MANDATORY_REGISTRY))
    assert report["passed"], report["rejected_names"][:4]
    assert report["counts"]["LIVE"] == 48

    by_name = dict(online.named_parameters())
    moved = sum(
        1 for name in FROZEN_MANDATORY_REGISTRY
        if not torch.equal(by_name[name].detach().float(), before[name])
    )
    assert moved == 48, "expected all 48 protected tensors to move, moved %d" % moved
    assert len(optimizer.state) > 0


def test_gate_precedes_every_optimizer_step_in_the_successor_source() -> None:
    """No alternate path may reach a step without passing the gate first."""
    from scripts.v4.c2_corrective_run_update_v3 import build_variant

    phase_e = _phase_e()
    source = build_variant(phase_e, "successor").__c2_variant_source__
    lines = source.splitlines()

    gate_lines = [i for i, line in enumerate(lines) if "_mandatory_gate.enforce" in line]
    registry_lines = [
        i for i, line in enumerate(lines) if "_mandatory_gate.enforce_registry" in line
    ]
    unscale_lines = [i for i, line in enumerate(lines) if "scaler.unscale_(" in line]
    step_lines = [
        i for i, line in enumerate(lines)
        if "scaler.step(" in line or "optimizer.step(" in line
    ]

    assert len(gate_lines) == 2 and len(registry_lines) == 1
    assert unscale_lines, "no unscale found"
    assert step_lines, "no optimizer step found"
    assert max(unscale_lines) < min(gate_lines), "gate must run after unscale"
    for step in step_lines:
        assert max(gate_lines) < step, "an optimizer step precedes the gate"

    # The gate calls sit at function-body depth, not nested in a conditional,
    # so no branch can skip them.
    tree = ast.parse(source)
    function = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    top_level = {
        node.lineno for node in function.body
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
    }
    for index in gate_lines:
        assert index + 1 in top_level, "gate call is not unconditional at body depth"


def test_historical_and_successor_differ_only_as_declared() -> None:
    from scripts.v4.c2_corrective_run_update_v3 import build_variant, variant_diff

    phase_e = _phase_e()
    diff = variant_diff(phase_e, "successor")
    added = [
        line[1:] for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    removed = [
        line[1:] for line in diff.splitlines()
        if line.startswith("-") and not line.startswith("---")
    ]
    substantive_added = [line for line in added if "def run_update" not in line]
    substantive_removed = [line for line in removed if "def run_update" not in line]

    # Exactly: two gate lines, one autocast-disable line, one re-indented backward.
    assert len(substantive_added) == 4, substantive_added
    assert len(substantive_removed) == 1, substantive_removed
    assert "backward()" in substantive_removed[0]
    assert any("enforce_registry" in line for line in substantive_added)
    assert any("enabled=False" in line for line in substantive_added)
    build_variant(phase_e, "successor")
