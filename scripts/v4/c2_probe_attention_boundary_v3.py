#!/usr/bin/env python3
"""Diagnostic probe: where inside KernelLinearAttention does fp16 zero the gradient?

DIAGNOSTIC ONLY. Not an endpoint, not gate-bearing. Captures, per block and per
dtype, the forward attention denominator and the gradient arriving at the q/k/v
projection outputs, which is the tensor that must cross the fp32-to-fp16 cast.

Synthetic input only.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import torch

WORKTREE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKTREE))


def load_phase_e(root: Path):
    sys.path.insert(0, str(root / "src"))
    sys.path.insert(0, str(root / "exports" / "static_context_decomposition_v4_20260821"))
    spec = importlib.util.spec_from_file_location(
        "phase_e", root / "scripts" / "v4" / "stage81a3_prod41k_engineering_smoke.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["phase_e"] = module
    spec.loader.exec_module(module)
    return module


def describe(tensor: torch.Tensor) -> str:
    flat = tensor.detach().float()
    finite = torch.isfinite(flat)
    return (
        "dtype=%-15s absmax=%.4e absmin_nonzero=%s zeros=%.4f%% nonfinite=%d"
        % (
            str(tensor.dtype),
            float(flat.abs().max()) if finite.any() else float("nan"),
            ("%.4e" % float(flat[flat != 0].abs().min())) if (flat != 0).any() else "ALL_ZERO",
            100.0 * float((flat == 0).float().mean()),
            int((~finite).sum()),
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dtype", choices=("fp16", "bf16", "fp32"), default="fp16")
    parser.add_argument("--cells", type=int, default=2)
    parser.add_argument("--seed", type=int, default=8113002)
    parser.add_argument("--canonical-root", action="append",
                        default=["/mnt/d/Jepa project", "D:/Jepa project"])
    args = parser.parse_args()

    root = next(
        Path(c) for c in args.canonical_root
        if (Path(c) / "scripts/v4/stage81a3_prod41k_engineering_smoke.py").is_file()
    )
    phase_e = load_phase_e(root)
    from scripts.v4.c2_synthetic_loader_v3 import SyntheticTrainLoader, synthetic_cohort
    from sea_ad_jepa.v4.ipb_jepa import block_jepa_loss, gather_block_states

    device = torch.device("cuda")
    online, target, predictor, optimizer, scaler, controller = phase_e.build_components(
        args.seed, device
    )
    loader = SyntheticTrainLoader(seed=args.seed)
    cohort = synthetic_cohort(args.cells)
    cohort = cohort.copy()
    cohort["loader_row"] = list(range(len(cohort)))
    values, states = loader.load(cohort)

    expression = torch.from_numpy(values).to(device)
    measured = torch.from_numpy(states).eq(1).to(device)
    gene_ids = torch.arange(phase_e.VOCABULARY_SIZE, device=device).expand(args.cells, -1)
    blocks = phase_e.sample_uniform_target_blocks(
        torch.from_numpy(states).eq(1),
        production_seed=args.seed,
        cell_indices=torch.arange(args.cells),
        sample_pass=0,
        view_index=0,
    )
    blocks = phase_e.slice_blocks(blocks, 0, args.cells, device)

    captured: dict[str, dict[str, str]] = {}

    def make_hook(block_index: int, role: str):
        def hook(module, grad_input, grad_output):
            entry = captured.setdefault("block%d" % block_index, {})
            entry[role + "_grad_out"] = describe(grad_output[0])
        return hook

    def make_fwd(block_index: int):
        def hook(module, inputs, output):
            entry = captured.setdefault("block%d" % block_index, {})
            entry["attn_out"] = describe(output[0])
            entry["denominator_min"] = "%.6e" % float(output[1].detach().float())
        return hook

    handles = []
    for index, block in enumerate(online.blocks):
        handles.append(block.attention.register_forward_hook(make_fwd(index)))
        for role in ("query", "key", "value", "output"):
            handles.append(
                getattr(block.attention, role).register_full_backward_hook(
                    make_hook(index, role)
                )
            )

    enabled = args.dtype != "fp32"
    dtype = torch.float16 if args.dtype == "fp16" else torch.bfloat16
    online.train()
    target.eval()
    predictor.train()
    optimizer.zero_grad(set_to_none=True)
    with torch.autocast("cuda", dtype=dtype, enabled=enabled):
        with torch.no_grad():
            teacher = target(gene_ids, expression, measured, torch.zeros_like(measured), "target")
        student = online(gene_ids, expression, measured, blocks.hidden_mask, "student")
        prediction = predictor(
            online.tokenizer.gene_identity, blocks, student.gene_states,
            student.cell_state, measured & ~blocks.hidden_mask,
        )
        teacher_blocks = gather_block_states(teacher.gene_states, blocks)
        loss = block_jepa_loss(prediction, teacher_blocks)
    print("mode=%s  loss=%.6f  scaler_scale=%.1f" % (args.dtype, float(loss), scaler.get_scale()))
    scaler.scale(loss).backward()

    for handle in handles:
        handle.remove()

    for key in sorted(captured):
        print("==", key)
        for role in ("denominator_min", "attn_out", "output_grad_out",
                     "value_grad_out", "key_grad_out", "query_grad_out"):
            if role in captured[key]:
                print("   %-18s %s" % (role, captured[key][role]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
