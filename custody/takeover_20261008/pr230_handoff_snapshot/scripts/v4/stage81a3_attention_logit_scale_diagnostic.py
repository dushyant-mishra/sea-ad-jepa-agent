#!/usr/bin/env python3
"""Recover one failed synthetic state and test one forward-only logit rescaling."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.v4 import stage81a3_forensic_failed_trajectory_replay as forensic  # noqa: E402
from scripts.v4 import stage81a3_synthetic_geometry_escape as base  # noqa: E402
from sea_ad_jepa.v4 import (  # noqa: E402
    EMAOptimizerStepController,
    LatentPredictor,
    V4AEncoderSkeleton,
    construct_context_mask,
    create_ema_target,
    ema_target_module,
    jepa_prediction_loss,
)
from sea_ad_jepa.v4.contracts import derive_visibility_masks  # noqa: E402


FIXTURE = "balanced_multifactor"
SEED = 8114001
EMA = 0.996
STEPS = 500
PERMUTATION_SEED = 8114601
TOP_K = 20
EPS = 1e-12
OUTPUT_JSON = Path("results/v4/stage81a3_attention_logit_scale_diagnostic.json")
OUTPUT_FACTOR = Path("results/v4/stage81a3_attention_logit_scale_factor_readout.csv")
OUTPUT_GEOMETRY = Path("results/v4/stage81a3_attention_logit_scale_geometry.csv")
OUTPUT_MASK = Path("results/v4/stage81a3_attention_logit_scale_mask_sensitivity.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--finalize-existing", action="store_true")
    parser.add_argument("--recovery-executions", type=int, default=1)
    parser.add_argument("--cumulative-recovery-optimizer-steps", type=int, default=STEPS)
    parser.add_argument("--cumulative-recovery-ema-updates", type=int, default=STEPS)
    return parser.parse_args()


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = sorted({key for row in rows for key in row})
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.temporary")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def finalize_existing(project: Path, args: argparse.Namespace) -> int:
    path = project / OUTPUT_JSON
    payload = json.loads(path.read_text(encoding="utf-8"))
    equivalence = payload["reference_recovery"]["ordinary_vs_manual_original_forward"]
    equivalence["pass"] = (
        float(equivalence["cross_attention_max_abs_diff"]) <= 3e-3
        and float(equivalence["final_slots_max_abs_diff"]) <= 3e-3
    )
    equivalence["tolerance"] = 3e-3
    equivalence["tolerance_interpretation"] = (
        "Forward-implementation equivalence tolerance under CUDA fp16 autocast; "
        "not a scientific effect threshold."
    )
    payload["execution_provenance"] = {
        "recovery_executions_during_this_task": args.recovery_executions,
        "cumulative_synthetic_recovery_optimizer_steps": (
            args.cumulative_recovery_optimizer_steps
        ),
        "cumulative_synthetic_recovery_ema_updates": args.cumulative_recovery_ema_updates,
        "evidence_producing_final_recovery_optimizer_steps": STEPS,
        "evidence_producing_final_recovery_ema_updates": STEPS,
        "corrective_rerun_reason": (
            "The first successful recovery exposed missing required slot-level and "
            "ordinary-forward equivalence telemetry; no scientific condition changed."
        ),
    }
    boundaries = payload["claim_boundaries"]
    boundaries["synthetic_reference_recovery_executions"] = args.recovery_executions
    boundaries["synthetic_reference_recovery_optimizer_steps"] = (
        args.cumulative_recovery_optimizer_steps
    )
    boundaries["synthetic_reference_recovery_ema_updates"] = (
        args.cumulative_recovery_ema_updates
    )
    boundaries["evidence_producing_reference_recovery_optimizer_steps"] = STEPS
    boundaries["evidence_producing_reference_recovery_ema_updates"] = STEPS
    atomic_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"ordinary_forward_equivalence_pass={equivalence['pass']}")
    print(
        "cumulative_recovery_steps="
        f"{args.cumulative_recovery_optimizer_steps}"
    )
    return 0


def parameter_digest(module: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(module.state_dict().items()):
        digest.update(name.encode("utf-8"))
        contiguous = tensor.detach().cpu().contiguous()
        digest.update(str(contiguous.dtype).encode("ascii"))
        digest.update(np.asarray(contiguous.shape, dtype=np.int64).tobytes())
        digest.update(contiguous.numpy().tobytes())
    return digest.hexdigest()


def parameter_snapshot(module: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: parameter.detach().cpu().clone()
        for name, parameter in module.named_parameters()
    }


def maximum_parameter_change(
    before: dict[str, torch.Tensor], module: torch.nn.Module
) -> float:
    after = dict(module.named_parameters())
    return max(
        float((value - after[name].detach().cpu()).abs().max())
        for name, value in before.items()
    )


def recover_reference_state(
    expression: torch.Tensor,
    factors: torch.Tensor,
    device: torch.device,
) -> tuple[V4AEncoderSkeleton, torch.nn.Module, LatentPredictor, dict[str, Any]]:
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    online = V4AEncoderSkeleton().to(device)
    predictor = LatentPredictor().to(device)
    target = create_ema_target(online).to(device)
    optimizer = torch.optim.AdamW(
        list(online.parameters()) + list(predictor.parameters()),
        lr=base.LEARNING_RATE,
        weight_decay=base.WEIGHT_DECAY,
    )
    scaler = torch.amp.GradScaler("cuda")
    controller = EMAOptimizerStepController(online, target)
    rng = torch.Generator(device="cpu").manual_seed(SEED + 900_000)
    nonfinite = 0
    interval = {"loss": [], "gradient_norm": [], "ema_update_norm": []}
    online.train()
    predictor.train()
    for update in range(1, STEPS + 1):
        optimizer.zero_grad(set_to_none=True)
        selected = torch.randint(0, base.TRAIN_CELLS, (base.EFFECTIVE_BATCH,), generator=rng)
        update_loss = 0.0
        for microbatch in range(base.ACCUMULATION_STEPS):
            start = microbatch * base.MICROBATCH
            indices = selected[start:start + base.MICROBATCH]
            values = expression[indices].to(device)
            measurement_cpu = torch.ones(base.MICROBATCH, base.GENES, dtype=torch.bool)
            context_cpu = construct_context_mask(
                measurement_cpu,
                mask_fraction=base.MASK_FRACTION,
                production_seed=SEED,
                cell_indices=indices,
                sample_pass=update,
                view_index=0,
                rule="exact_count",
            )
            context = context_cpu.to(device)
            measured = measurement_cpu.to(device)
            ids = torch.arange(base.GENES, device=device).repeat(base.MICROBATCH, 1)
            with torch.autocast("cuda", dtype=torch.float16):
                context_latents = online(ids, values, measured, context, "student")
                prediction = predictor(context_latents)
                with torch.no_grad():
                    target_latents = target(ids, values, measured, context, "target")
                loss = jepa_prediction_loss(prediction, target_latents)
            if not torch.isfinite(loss):
                nonfinite += 1
                raise RuntimeError(f"nonfinite recovery loss at update {update}")
            scaler.scale(loss / base.ACCUMULATION_STEPS).backward()
            update_loss += float(loss.detach()) / base.ACCUMULATION_STEPS
        scaler.unscale_(optimizer)
        gradient_norm = base.parameter_gradient_norm(
            list(online.parameters()) + list(predictor.parameters())
        )
        scale_before = scaler.get_scale()
        scaler.step(optimizer)
        scaler.update()
        if scaler.get_scale() < scale_before:
            nonfinite += 1
            raise RuntimeError(f"GradScaler skipped recovery update {update}")
        gap = float(
            sum(
                (online_value.detach() - target_value.detach()).square().sum()
                for online_value, target_value in zip(
                    online.parameters(), ema_target_module(target).parameters(), strict=True
                )
            ).sqrt()
        )
        controller.after_successful_optimizer_step(momentum=EMA)
        interval["loss"].append(update_loss)
        interval["gradient_norm"].append(gradient_norm)
        interval["ema_update_norm"].append((1.0 - EMA) * gap)
        if update % 100 == 0:
            print(f"recovery update {update}/{STEPS} loss={update_loss:.6f}", flush=True)
    if controller.global_update_step != STEPS or controller.ema_update_count != STEPS:
        raise RuntimeError("reference-state recovery update count mismatch")

    row, _, _ = base.checkpoint_metrics(
        online,
        target,
        predictor,
        expression,
        factors,
        fixture=FIXTURE,
        seed=SEED,
        step=STEPS,
        interval=interval,
        nonfinite_events=nonfinite,
        device=device,
        smoke=False,
    )
    return online, target, predictor, {
        "trajectory_row": row,
        "optimizer_updates": controller.global_update_step,
        "ema_updates": controller.ema_update_count,
        "nonfinite_events": nonfinite,
    }


def attention_components(
    model: V4AEncoderSkeleton,
    tokens: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    module = model.cross_attention.cross_attention
    width = module.embed_dim
    heads = module.num_heads
    head_width = width // heads
    queries = model.cross_attention.latents.unsqueeze(0).expand(len(tokens), -1, -1)
    q = F.linear(
        queries.float(), module.in_proj_weight[:width].float(), module.in_proj_bias[:width].float()
    )
    k = F.linear(
        tokens.float(),
        module.in_proj_weight[width:2 * width].float(),
        module.in_proj_bias[width:2 * width].float(),
    )
    v = F.linear(
        tokens.float(),
        module.in_proj_weight[2 * width:].float(),
        module.in_proj_bias[2 * width:].float(),
    )
    q = q.reshape(len(tokens), 24, heads, head_width).permute(0, 2, 1, 3)
    k = k.reshape(len(tokens), base.GENES, heads, head_width).permute(0, 2, 1, 3)
    v = v.reshape(len(tokens), base.GENES, heads, head_width).permute(0, 2, 1, 3)
    logits = torch.matmul(q, k.transpose(-1, -2)) / math.sqrt(head_width)
    return queries, logits, v, module.out_proj.weight.float()


def affine_permute_logits(
    logits: torch.Tensor,
    cell_indices: torch.Tensor,
) -> torch.Tensor:
    """Apply one fixed bijective affine gene permutation per cell/head/slot."""
    genes = logits.shape[-1]
    head = torch.arange(logits.shape[1], device=logits.device)[None, :, None]
    slot = torch.arange(logits.shape[2], device=logits.device)[None, None, :]
    cell = cell_indices.to(logits.device)[:, None, None]
    code = cell * 1315423911 + head * 2654435761 + slot * 2246822519 + PERMUTATION_SEED
    multiplier = torch.remainder(code * 2 + 1, genes).to(torch.long)
    offset = torch.remainder(code * 1103515245 + 12345, genes).to(torch.long)
    gene = torch.arange(genes, device=logits.device)
    permutation = torch.remainder(multiplier[..., None] * gene + offset[..., None], genes)
    return torch.gather(logits, -1, permutation)


def forward_with_logit_rule(
    model: V4AEncoderSkeleton,
    gene_ids: torch.Tensor,
    expression: torch.Tensor,
    valid_mask: torch.Tensor,
    *,
    scale: float,
    cell_indices: torch.Tensor,
    permute: bool = False,
) -> dict[str, torch.Tensor]:
    with torch.autocast("cuda", dtype=torch.float16):
        tokens = model.tokenizer(gene_ids, expression)
    queries, logits, values, output_weight = attention_components(model, tokens)
    logits_used = affine_permute_logits(logits, cell_indices) if permute else logits
    logits_scaled = logits_used * scale
    logits_scaled = logits_scaled.masked_fill(~valid_mask[:, None, None, :], -torch.inf)
    attention = torch.softmax(logits_scaled, dim=-1)
    attended = torch.matmul(attention, values)
    attended = attended.permute(0, 2, 1, 3).reshape(len(tokens), 24, -1)
    module = model.cross_attention.cross_attention
    attended = F.linear(attended, output_weight, module.out_proj.bias.float())
    cross = model.cross_attention.output_norm(queries.float() + attended)
    latents = cross
    with torch.autocast("cuda", dtype=torch.float16):
        for block in model.latent_blocks:
            latents = block(latents)
        final = model.final_norm(latents)
    return {
        "tokens": tokens.float(),
        "original_logits": logits.float(),
        "used_logits": logits_used.float(),
        "scaled_logits": logits_scaled.float(),
        "attention": attention.float(),
        "cross_slots": cross.float(),
        "post_latent_slots": latents.float(),
        "final_slots": final.float(),
    }


def attention_summary(logits: torch.Tensor, attention: torch.Tensor) -> dict[str, Any]:
    entropy = -(attention.clamp_min(EPS) * attention.clamp_min(EPS).log()).sum(dim=-1)
    normalized_entropy = entropy / math.log(attention.shape[-1])
    top = attention.topk(10, dim=-1).values
    normalized = F.normalize(attention, dim=-1)
    slot_cosine = torch.matmul(normalized, normalized.transpose(-1, -2))
    off_diagonal = ~torch.eye(attention.shape[2], dtype=torch.bool, device=attention.device)
    per_head = []
    for head in range(attention.shape[1]):
        per_head.append({
            "head": head,
            "logit_sd": float(logits[:, head].std(unbiased=False)),
            "normalized_entropy": forensic.quantiles(normalized_entropy[:, head].cpu()),
            "maximum_attention_weight": forensic.quantiles(attention[:, head].amax(dim=-1).cpu()),
            "top10_attention_mass": forensic.quantiles(top[:, head].sum(dim=-1).cpu()),
            "between_slot_attention_map_cosine": forensic.quantiles(
                slot_cosine[:, head][:, off_diagonal].cpu()
            ),
            "cross_cell_attention_map_variance": float(
                attention[:, head].var(dim=0, unbiased=False).mean()
            ),
        })
    return {
        "pre_softmax_logit_sd": float(logits[torch.isfinite(logits)].std(unbiased=False)),
        "pre_softmax_logits": forensic.quantiles(logits[torch.isfinite(logits)].cpu()),
        "normalized_entropy": forensic.quantiles(normalized_entropy.cpu()),
        "maximum_attention_weight": forensic.quantiles(attention.amax(dim=-1).cpu()),
        "top10_attention_mass": forensic.quantiles(top.sum(dim=-1).cpu()),
        "between_slot_attention_map_cosine": forensic.quantiles(
            slot_cosine[:, :, off_diagonal].cpu()
        ),
        "cross_cell_attention_map_variance": float(attention.var(dim=0, unbiased=False).mean()),
        "per_head": per_head,
    }


def ranking_preservation(original: torch.Tensor, scaled: torch.Tensor) -> dict[str, Any]:
    original_order = torch.argsort(original, dim=-1)
    scaled_order = torch.argsort(scaled, dim=-1)
    identical = (original_order == scaled_order).all(dim=-1)
    return {
        "rows_checked": int(identical.numel()),
        "rows_with_identical_complete_ranking": int(identical.sum()),
        "identical_ranking_fraction": float(identical.float().mean()),
        "positive_scale_preserves_order_by_construction": True,
    }


def jaccard_summary(attention: torch.Tensor) -> dict[str, Any]:
    top = attention.topk(TOP_K, dim=-1).indices.cpu()
    slot_values = []
    cell_values = []
    for cell in range(top.shape[0]):
        for head in range(top.shape[1]):
            sets = [set(row.tolist()) for row in top[cell, head]]
            for left in range(len(sets)):
                for right in range(left + 1, len(sets)):
                    slot_values.append(len(sets[left] & sets[right]) / len(sets[left] | sets[right]))
    for head in range(top.shape[1]):
        for slot in range(top.shape[2]):
            sets = [set(top[cell, head, slot].tolist()) for cell in range(top.shape[0])]
            for left in range(len(sets)):
                for right in range(left + 1, len(sets)):
                    cell_values.append(len(sets[left] & sets[right]) / len(sets[left] | sets[right]))
    return {
        "top_k": TOP_K,
        "between_slots_within_cell": forensic.quantiles(np.asarray(slot_values)),
        "across_cells_same_head_slot": forensic.quantiles(np.asarray(cell_values)),
    }


def collect_representations(
    model: V4AEncoderSkeleton,
    expression: torch.Tensor,
    indices: torch.Tensor,
    device: torch.device,
    *,
    scale: float,
    permute: bool,
) -> dict[str, torch.Tensor]:
    parts = {
        "cross_attention_slots": [],
        "cross_attention_flattened": [],
        "cross_attention_pooled": [],
        "post_latent_blocks_slots": [],
        "post_latent_blocks_flattened": [],
        "final_slots": [],
        "final_slots_flattened": [],
        "final_slots_pooled": [],
    }
    with torch.no_grad():
        for start in range(0, len(indices), base.MICROBATCH):
            selected = indices[start:start + base.MICROBATCH]
            values = expression[selected].to(device)
            ids = torch.arange(base.GENES, device=device).repeat(len(selected), 1)
            valid = torch.ones(len(selected), base.GENES, dtype=torch.bool, device=device)
            output = forward_with_logit_rule(
                model,
                ids,
                values,
                valid,
                scale=scale,
                cell_indices=selected,
                permute=permute,
            )
            cross = output["cross_slots"].cpu()
            post = output["post_latent_slots"].cpu()
            final = output["final_slots"].cpu()
            parts["cross_attention_slots"].append(cross)
            parts["cross_attention_flattened"].append(cross.flatten(1))
            parts["cross_attention_pooled"].append(cross.mean(dim=1))
            parts["post_latent_blocks_slots"].append(post)
            parts["post_latent_blocks_flattened"].append(post.flatten(1))
            parts["final_slots"].append(final)
            parts["final_slots_flattened"].append(final.flatten(1))
            parts["final_slots_pooled"].append(final.mean(dim=1))
    return {name: torch.cat(values) for name, values in parts.items()}


def factor_and_geometry_rows(
    condition: str,
    representations: dict[str, torch.Tensor],
    factors: torch.Tensor,
    train_indices: torch.Tensor,
    eval_indices: torch.Tensor,
    device: torch.device,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    split = len(train_indices)
    factor_rows = []
    geometry_rows = []
    details = {}
    for name, values in representations.items():
        if values.ndim != 2:
            continue
        readout = base.ridge_readout(
            values[:split], factors[train_indices], values[split:], factors[eval_indices]
        )
        geometry = base.geometry_2d(values[split:], device)
        details[name] = {"factor_readout": readout, "geometry": geometry}
        distribution = forensic.quantiles(np.asarray(readout["per_factor_r2"]))
        factor_rows.append({
            "condition": condition,
            "representation": name,
            "mean_r2": readout["mean_r2"],
            "median_r2": readout["median_r2"],
            "minimum_r2": distribution["minimum"],
            "p10_r2": distribution["p10"],
            "p90_r2": distribution["p90"],
            "maximum_r2": distribution["maximum"],
        })
        geometry_rows.append({
            "condition": condition,
            "representation": name,
            "effective_rank": geometry["effective_rank"],
            "top_singular_l1_fraction": geometry["top_singular_l1_fraction"],
            "top_singular_energy_fraction": geometry["top_singular_energy_fraction"],
            "cross_cell_std": geometry["cross_cell_std_mean"],
            "median_pairwise_distance": geometry["median_pairwise_distance"],
        })
    return factor_rows, geometry_rows, details


def slot_differentiation(
    representations: dict[str, torch.Tensor],
    split: int,
    device: torch.device,
) -> dict[str, Any]:
    return {
        name: base.slot_geometry(representations[name][split:], device)
        for name in (
            "cross_attention_slots",
            "post_latent_blocks_slots",
            "final_slots",
        )
    }


def diagnostic_masks(indices: torch.Tensor) -> torch.Tensor:
    return torch.stack(
        [forensic.mask_for_indices(indices, STEPS, view) for view in range(forensic.MASK_VIEWS)],
        dim=1,
    )


def mask_sensitivity_condition(
    model: V4AEncoderSkeleton,
    expression: torch.Tensor,
    indices: torch.Tensor,
    device: torch.device,
    *,
    scale: float,
    condition: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    masks = diagnostic_masks(indices)
    cross_all = []
    final_all = []
    full_all = []
    with torch.no_grad():
        for cell, index in enumerate(indices):
            selected = index.repeat(forensic.MASK_VIEWS)
            values = expression[index].to(device).repeat(forensic.MASK_VIEWS, 1)
            ids = torch.arange(base.GENES, device=device).repeat(forensic.MASK_VIEWS, 1)
            valid = ~masks[cell].to(device)
            output = forward_with_logit_rule(
                model, ids, values, valid, scale=scale, cell_indices=selected
            )
            cross_all.append(output["cross_slots"].cpu())
            final_all.append(output["final_slots"].cpu())
            full = forward_with_logit_rule(
                model,
                ids[:1],
                values[:1],
                torch.ones(1, base.GENES, dtype=torch.bool, device=device),
                scale=scale,
                cell_indices=index.reshape(1),
            )
            full_all.append(full["final_slots"].cpu())
    cross = torch.stack(cross_all)
    final = torch.stack(final_all)
    pooled = final.mean(dim=2)
    full = torch.cat(full_all)
    full_pooled = full.mean(dim=1)
    cosine = F.cosine_similarity(pooled, full_pooled[:, None, :].expand_as(pooled), dim=-1)
    l2 = torch.linalg.vector_norm(pooled - full_pooled[:, None, :], dim=-1)
    stages = {
        "cross_attention_slots": forensic.squared_distance_ratio(cross),
        "post_latent_final_slots": forensic.squared_distance_ratio(final),
        "pooled_representation": forensic.squared_distance_ratio(pooled),
    }
    rows = [
        {"condition": condition, "stage": stage, **metrics}
        for stage, metrics in stages.items()
    ]
    return rows, {
        "stages": stages,
        "full_vs_masked_pooled": {
            "cosine_similarity": forensic.quantiles(cosine.cpu()),
            "l2_distance": forensic.quantiles(l2.cpu()),
        },
    }


def main() -> int:
    args = parse_args()
    project = args.project_dir.resolve()
    if args.finalize_existing:
        return finalize_existing(project, args)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required")
    device = torch.device("cuda")
    prior = json.loads((project / forensic.OUTPUT_JSON).read_text(encoding="utf-8"))
    if prior["classification"] != "ATTENTION ROUTING BOTTLENECK STRONGLY SUPPORTED":
        raise RuntimeError("prior forensic classification drift")
    expression, factors, fixture_metadata = base.synthetic_fixture(FIXTURE, smoke=False)
    online, target, predictor, recovery = recover_reference_state(expression, factors, device)
    target_model = ema_target_module(target)

    prior_row = next(
        row for row in prior["trajectory"] if int(row["optimizer_step"]) == STEPS
    )
    current_row = recovery["trajectory_row"]
    replay_fields = {
        field: abs(float(current_row[field]) - float(prior_row[field]))
        for field in forensic.REPLAY_TOLERANCES
    }
    target_model.eval()
    online.eval()
    predictor.eval()
    modules = {"online_encoder": online, "ema_target_encoder": target_model, "predictor": predictor}
    for module in modules.values():
        module.eval()
        for parameter in module.parameters():
            parameter.requires_grad_(False)
    hashes_before = {name: parameter_digest(module) for name, module in modules.items()}
    snapshots = {name: parameter_snapshot(module) for name, module in modules.items()}
    eval_indices = torch.arange(len(expression) - base.READOUT_EVAL_CELLS, len(expression))
    fixed_indices = eval_indices[:forensic.FORENSIC_CELLS]
    prior_logits = prior["forensic_checkpoints"]["500"]["pre_softmax_logits"]

    with torch.no_grad():
        fixed_values = expression[fixed_indices].to(device)
        fixed_ids = torch.arange(base.GENES, device=device).repeat(len(fixed_indices), 1)
        valid = torch.ones(len(fixed_indices), base.GENES, dtype=torch.bool, device=device)
        with torch.autocast("cuda", dtype=torch.float16):
            ordinary_tokens = target_model.tokenizer(fixed_ids, fixed_values)
            ordinary_cross = target_model.cross_attention(ordinary_tokens, valid)
            ordinary_latents = ordinary_cross
            for block in target_model.latent_blocks:
                ordinary_latents = block(ordinary_latents)
            ordinary_final = target_model.final_norm(ordinary_latents)
        original_fixed = forward_with_logit_rule(
            target_model,
            fixed_ids,
            fixed_values,
            valid,
            scale=1.0,
            cell_indices=fixed_indices,
        )
    ordinary_forward_equivalence = {
        "cross_attention_max_abs_diff": float(
            (ordinary_cross.float() - original_fixed["cross_slots"]).abs().max()
        ),
        "final_slots_max_abs_diff": float(
            (ordinary_final.float() - original_fixed["final_slots"]).abs().max()
        ),
    }
    sigma_reference = float(original_fixed["original_logits"].std(unbiased=False))
    scale_factor = 1.0 / sigma_reference
    with torch.no_grad():
        scaled_fixed = forward_with_logit_rule(
            target_model,
            fixed_ids,
            fixed_values,
            valid,
            scale=scale_factor,
            cell_indices=fixed_indices,
        )
        permuted_fixed = forward_with_logit_rule(
            target_model,
            fixed_ids,
            fixed_values,
            valid,
            scale=scale_factor,
            cell_indices=fixed_indices,
            permute=True,
        )
    original_attention = attention_summary(
        original_fixed["original_logits"], original_fixed["attention"]
    )
    scaled_attention = attention_summary(
        scaled_fixed["scaled_logits"], scaled_fixed["attention"]
    )
    permuted_attention = attention_summary(
        permuted_fixed["scaled_logits"], permuted_fixed["attention"]
    )
    replay_differences = {
        "trajectory": replay_fields,
        "attention_logit_sd": abs(
            sigma_reference - float(prior_logits["all_heads_logits"]["standard_deviation"])
        ),
        "attention_entropy_median": abs(
            original_attention["normalized_entropy"]["median"]
            - float(prior_row["target_cross_attention_summary"]["normalized_entropy"]["median"])
        ),
    }
    replay_pass = (
        all(replay_fields[field] <= forensic.REPLAY_TOLERANCES[field] for field in replay_fields)
        and replay_differences["attention_logit_sd"] <= 1e-5
        and replay_differences["attention_entropy_median"] <= 1e-5
    )
    if not replay_pass:
        raise RuntimeError(f"REFERENCE STATE RECOVERY FAILED: {replay_differences}")

    train_indices, factor_eval_indices = forensic.evaluation_indices(len(expression))
    combined = torch.cat((train_indices, factor_eval_indices))
    tokenizer_readout = forensic.full_token_kernel_readout(
        target_model, expression, factors, train_indices, factor_eval_indices, device
    )
    conditions = {
        "original": (1.0, False),
        "scaled_learned_ranking": (scale_factor, False),
        "scaled_permuted_ranking": (scale_factor, True),
    }
    factor_rows = []
    geometry_rows = []
    condition_details = {}
    for name, (scale, permute) in conditions.items():
        print(f"collecting {name} representations", flush=True)
        representations = collect_representations(
            target_model,
            expression,
            combined,
            device,
            scale=scale,
            permute=permute,
        )
        rows, geometries, details = factor_and_geometry_rows(
            name,
            representations,
            factors,
            train_indices,
            factor_eval_indices,
            device,
        )
        factor_rows.extend(rows)
        geometry_rows.extend(geometries)
        details["slot_differentiation"] = slot_differentiation(
            representations, len(train_indices), device
        )
        condition_details[name] = details

    mask_rows = []
    mask_details = {}
    for name, scale in (("original", 1.0), ("scaled_learned_ranking", scale_factor)):
        rows, details = mask_sensitivity_condition(
            target_model,
            expression,
            fixed_indices,
            device,
            scale=scale,
            condition=name,
        )
        mask_rows.extend(rows)
        mask_details[name] = details

    hashes_after = {name: parameter_digest(module) for name, module in modules.items()}
    maximum_changes = {
        name: maximum_parameter_change(snapshots[name], module)
        for name, module in modules.items()
    }
    immutable = hashes_before == hashes_after and max(maximum_changes.values()) == 0.0
    if not immutable:
        raise RuntimeError("forward-only diagnostic changed model parameters")

    def readout(condition: str, representation: str) -> float:
        return float(condition_details[condition][representation]["factor_readout"]["mean_r2"])

    original_flat = readout("original", "final_slots_flattened")
    scaled_flat = readout("scaled_learned_ranking", "final_slots_flattened")
    permuted_flat = readout("scaled_permuted_ranking", "final_slots_flattened")
    original_pooled = readout("original", "final_slots_pooled")
    scaled_pooled = readout("scaled_learned_ranking", "final_slots_pooled")
    original_mask = mask_details["original"]["stages"]["post_latent_final_slots"][
        "mask_sensitivity_ratio"
    ]
    scaled_mask = mask_details["scaled_learned_ranking"]["stages"][
        "post_latent_final_slots"
    ]["mask_sensitivity_ratio"]
    differentiated = (
        scaled_attention["between_slot_attention_map_cosine"]["median"]
        < original_attention["between_slot_attention_map_cosine"]["median"]
    )
    learned_beyond_permuted = scaled_flat > permuted_flat
    material_factor_gain = scaled_flat - original_flat >= 0.10
    useful_mask_gain = scaled_mask > original_mask * 1.5
    if material_factor_gain and useful_mask_gain and differentiated and learned_beyond_permuted:
        classification = "Q/K RANKINGS CONTAIN USEFUL INFORMATION BUT LOGIT SCALE SUPPRESSES ROUTING"
        recommendation = (
            "Run one separately approved synthetic training experiment with a single "
            "evidence-backed Q/K routing bootstrap; do not freeze this diagnostic scale."
        )
    elif scaled_flat - original_flat >= 0.02:
        classification = "AMPLIFICATION PRODUCES PARTIAL INFORMATION RECOVERY BUT NOT A HEALTHY REPRESENTATION"
        recommendation = (
            "Human review should distinguish learned-ranking recovery from generic "
            "attention concentration before authorizing another experiment."
        )
    else:
        classification = "Q/K RANKINGS REMAIN UNINFORMATIVE AFTER AMPLIFICATION"
        recommendation = (
            "Do not continue scaling experiments; the next causal experiment should test "
            "mask-specific hidden-content target semantics with the same tokenizer and capacity."
        )

    payload = {
        "stage": "stage81a3_forward_only_attention_logit_scale_diagnostic",
        "status": "complete",
        "reference_contract": {
            "fixture": FIXTURE,
            "seed": SEED,
            "ema": EMA,
            "optimizer_updates": recovery["optimizer_updates"],
            "ema_updates": recovery["ema_updates"],
            "mask_fraction": base.MASK_FRACTION,
            "mask_rule": "exact_count",
            "fixture_metadata": fixture_metadata,
        },
        "reference_recovery": {
            "pass": replay_pass,
            "differences": replay_differences,
            "current_step_500": current_row,
            "ordinary_vs_manual_original_forward": ordinary_forward_equivalence,
        },
        "counterfactual": {
            "rule": "L_scaled = L / sigma_reference",
            "sigma_reference": sigma_reference,
            "deterministic_scale_factor": scale_factor,
            "scale_selected_before_counterfactual_factor_readout": True,
            "temperature_sweep_performed": False,
            "production_scale_selected": False,
        },
        "parameter_immutability": {
            "pass": immutable,
            "hashes_before": hashes_before,
            "hashes_after": hashes_after,
            "maximum_absolute_parameter_change": maximum_changes,
            "counterfactual_optimizer_steps": 0,
            "counterfactual_ema_updates": 0,
            "counterfactual_backward_calls": 0,
        },
        "attention": {
            "original": original_attention,
            "scaled_learned_ranking": scaled_attention,
            "scaled_permuted_ranking": permuted_attention,
            "ranking_preservation": ranking_preservation(
                original_fixed["original_logits"], scaled_fixed["scaled_logits"]
            ),
            "top_gene_overlap": {
                "original": jaccard_summary(original_fixed["attention"]),
                "scaled_learned_ranking": jaccard_summary(scaled_fixed["attention"]),
                "scaled_permuted_ranking": jaccard_summary(permuted_fixed["attention"]),
            },
        },
        "tokenizer_factor_readout": tokenizer_readout,
        "conditions": condition_details,
        "mask_sensitivity": mask_details,
        "classification_evidence": {
            "original_final_flattened_mean_r2": original_flat,
            "scaled_final_flattened_mean_r2": scaled_flat,
            "permuted_final_flattened_mean_r2": permuted_flat,
            "original_final_pooled_mean_r2": original_pooled,
            "scaled_final_pooled_mean_r2": scaled_pooled,
            "original_final_mask_sensitivity_ratio": original_mask,
            "scaled_final_mask_sensitivity_ratio": scaled_mask,
            "scaled_attention_more_slot_differentiated": differentiated,
            "scaled_learned_ranking_beyond_permuted": learned_beyond_permuted,
            "predeclared_material_flattened_factor_gain": material_factor_gain,
            "predeclared_useful_mask_gain": useful_mask_gain,
        },
        "classification": classification,
        "recommendation": recommendation,
        "numerical_health": {
            "reference_nonfinite_events": recovery["nonfinite_events"],
            "counterfactual_nonfinite_events": 0,
        },
        "claim_boundaries": {
            "stage81a3_complete": False,
            "ready_for_stage81b": False,
            "real_rna_optimizer_steps": 0,
            "real_rna_ema_updates": 0,
            "real_rna_model_training": False,
            "synthetic_reference_recovery_optimizer_steps": STEPS,
            "synthetic_reference_recovery_ema_updates": STEPS,
            "forward_counterfactual_optimizer_steps": 0,
            "forward_counterfactual_ema_updates": 0,
            "forward_counterfactual_backward_calls": 0,
            "pathology_opened": False,
            "stage81b_started": False,
            "stage81c_started": False,
            "production_seed_selected": False,
            "production_attention_scale_selected": False,
            "architecture_changed": False,
            "training_objective_changed": False,
        },
    }
    atomic_text(project / OUTPUT_JSON, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_csv(project / OUTPUT_FACTOR, factor_rows)
    write_csv(project / OUTPUT_GEOMETRY, geometry_rows)
    write_csv(project / OUTPUT_MASK, mask_rows)
    print(f"reference_recovery_pass={replay_pass}")
    print(f"sigma_reference={sigma_reference:.9f}")
    print(f"deterministic_scale_factor={scale_factor:.6f}")
    print(f"parameter_immutability_pass={immutable}")
    print(f"classification={classification}")
    print(f"recommendation={recommendation}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
