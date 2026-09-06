#!/usr/bin/env python3
"""Synthetic-only C2 forensic: localize the T1 gradient-severing condition.

Reconstructs a healthy simplified endpoint and the historical-scale endpoint,
instruments every mandatory tensor, and executes a frozen one-factor bisection.
Loads no real expression, no pathology, and no protected partition.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any

import torch
from torch import nn

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from sea_ad_jepa.v4.ipb_jepa import (  # noqa: E402
    BlockPredictor,
    IPBEncoder,
    TargetBlocks,
    block_jepa_loss,
    gather_block_states,
)

MANDATORY_ROLES = ("attention_norm", "attention.query", "attention.key", "attention.value")
LIVE_REFERENCE_ROLES = ("attention.output",)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def role_of(name: str) -> str | None:
    """Return the mechanical role of an encoder parameter, or None."""
    for role in MANDATORY_ROLES + LIVE_REFERENCE_ROLES:
        if "." + role + "." in name:
            return role
    return None


def mandatory_tensor_registry(encoder: nn.Module) -> list[dict[str, Any]]:
    """Every parameter whose gradient the contract requires to be live."""
    registry = []
    for name, param in encoder.named_parameters():
        role = role_of(name)
        if role in MANDATORY_ROLES:
            registry.append(
                {
                    "name": name,
                    "role": role,
                    "shape": list(param.shape),
                    "requires_grad": bool(param.requires_grad),
                }
            )
    return sorted(registry, key=lambda item: item["name"])


def live_reference_registry(encoder: nn.Module) -> list[dict[str, Any]]:
    """Attention output tensors, which the historical signature shows staying live."""
    entries = [
        {"name": name, "role": role_of(name), "shape": list(param.shape)}
        for name, param in encoder.named_parameters()
        if role_of(name) in LIVE_REFERENCE_ROLES
    ]
    return sorted(entries, key=lambda item: item["name"])


def gradient_snapshot(encoder: nn.Module, registry: list[dict[str, Any]]) -> dict[str, Any]:
    """Distinguish missing gradient from zero gradient from nonfinite gradient."""
    by_name = dict(encoder.named_parameters())
    entries = {}
    for item in registry:
        param = by_name[item["name"]]
        if param.grad is None:
            entries[item["name"]] = {"status": "MISSING", "norm": None, "max_abs": None}
            continue
        grad = param.grad.detach().float()
        norm = float(grad.norm())
        max_abs = float(grad.abs().max())
        if not math.isfinite(norm):
            status = "NONFINITE"
        elif norm == 0.0:
            status = "ZERO"
        else:
            status = "LIVE"
        entries[item["name"]] = {"status": status, "norm": norm, "max_abs": max_abs}
    dead = sorted(name for name, entry in entries.items() if entry["status"] != "LIVE")
    return {
        "entries": entries,
        "dead_names": dead,
        "dead_count": len(dead),
        "total": len(registry),
    }


def moment_snapshot(
    optimizer: torch.optim.Optimizer, encoder: nn.Module, registry: list[dict[str, Any]]
) -> dict[str, Any]:
    """Report Adam first and second moments independently, never pooled."""
    by_name = dict(encoder.named_parameters())
    entries = {}
    for item in registry:
        state = optimizer.state.get(by_name[item["name"]], {})
        first = state.get("exp_avg")
        second = state.get("exp_avg_sq")
        entries[item["name"]] = {
            "exp_avg_norm": None if first is None else float(first.float().norm()),
            "exp_avg_sq_norm": None if second is None else float(second.float().norm()),
        }
    zero_first = sum(
        1 for entry in entries.values()
        if entry["exp_avg_norm"] is None or entry["exp_avg_norm"] == 0.0
    )
    zero_second = sum(
        1 for entry in entries.values()
        if entry["exp_avg_sq_norm"] is None or entry["exp_avg_sq_norm"] == 0.0
    )
    return {
        "entries": entries,
        "zero_first_moment": zero_first,
        "zero_second_moment": zero_second,
        "total": len(registry),
    }


def movement_snapshot(
    before: dict[str, torch.Tensor],
    encoder: nn.Module,
    registry: list[dict[str, Any]],
    lr: float,
    weight_decay: float,
    steps: int,
) -> dict[str, Any]:
    """Per-tensor relative movement, with the decay-only prediction alongside."""
    by_name = dict(encoder.named_parameters())
    decay_only = 1.0 - (1.0 - lr * weight_decay) ** max(steps, 0)
    entries = {}
    for item in registry:
        name = item["name"]
        start = before[name]
        end = by_name[name].detach().float()
        base = float(start.norm())
        delta = float((end - start).norm())
        entries[name] = {
            "baseline_norm": base,
            "relative_movement": None if base == 0.0 else delta / base,
            "zero_baseline": base == 0.0,
        }
    return {
        "entries": entries,
        "decay_only_prediction": decay_only,
        "steps": steps,
        "total": len(registry),
    }


def make_blocks(
    measurement: torch.Tensor,
    mode: str,
    generator: torch.Generator,
    n_blocks: int = 8,
    block_size: int = 16,
) -> TargetBlocks:
    """Construct target blocks. random40 mirrors the historical blocks_for semantics."""
    batch, _ = measurement.shape
    device = measurement.device
    if mode == "random40":
        draw = torch.rand(measurement.shape, generator=generator, device=device)
        hidden = (draw < 0.40) & measurement
    elif mode == "measured_complement":
        visible = torch.zeros_like(measurement)
        visible[:, ::2] = True
        hidden = measurement & ~visible
    else:
        raise ValueError("unknown block mode: " + str(mode))
    # Preserve the encoder invariant that every cell keeps one visible gene.
    hidden[:, 0] = False
    indices = torch.zeros(batch, n_blocks, block_size, dtype=torch.long, device=device)
    member = torch.zeros(batch, n_blocks, block_size, dtype=torch.bool, device=device)
    for cell in range(batch):
        pool = torch.nonzero(hidden[cell], as_tuple=False).flatten()
        if len(pool) == 0:
            continue
        order = torch.randperm(len(pool), generator=generator, device=device)
        perm = pool[order]
        need = n_blocks * block_size
        if len(perm) < need:
            perm = perm.repeat((need // len(perm)) + 1)
        indices[cell] = perm[:need].reshape(n_blocks, block_size)
        member[cell] = True
    return TargetBlocks(
        hidden_mask=hidden,
        indices=indices,
        member_mask=member,
        fallback_counts=torch.zeros(batch, dtype=torch.long, device=device),
    )


def synthetic_batch(
    tokens: int, vocabulary: int, size: int, generator: torch.Generator, device: torch.device
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Synthetic expression only. No real corpus, no protected partition."""
    ids = torch.stack(
        [torch.randperm(vocabulary, generator=generator, device=device)[:tokens]
         for _ in range(size)]
    )
    expression = torch.rand(size, tokens, generator=generator, device=device) * 4.0
    measurement = torch.rand(size, tokens, generator=generator, device=device) < 0.70
    measurement[:, 0] = True
    return ids, expression, measurement


def run_condition(
    cfg: dict[str, Any],
    condition_id: str,
    settings: dict[str, Any],
    seed: int,
    device: torch.device,
) -> dict[str, Any]:
    """Execute one fully specified mechanical condition and instrument it."""
    torch.manual_seed(seed)
    generator = torch.Generator(device=device).manual_seed(seed)
    model_cfg = cfg["model"]
    vocabulary = cfg["vocabulary_size"]

    online = IPBEncoder(
        width=model_cfg["width"],
        heads=model_cfg["heads"],
        blocks=model_cfg["blocks"],
        ffn_width=model_cfg["ffn_width"],
        dropout=model_cfg["dropout"],
        gradient_checkpointing=settings["grad_checkpointing"],
        vocabulary_size=vocabulary,
    ).to(device)
    target = copy.deepcopy(online).to(device)
    for param in target.parameters():
        param.requires_grad_(False)
    predictor = BlockPredictor(
        identity_dim=online.tokenizer.identity_dim,
        width=model_cfg["width"],
        heads=model_cfg["heads"],
    ).to(device)
    online.train()
    target.train()
    predictor.train()

    registry = mandatory_tensor_registry(online)
    live_registry = live_reference_registry(online)
    if len(registry) != cfg["expected_mandatory_tensors"]:
        raise RuntimeError("mandatory registry size " + str(len(registry)))
    if len(live_registry) != cfg["expected_live_reference_tensors"]:
        raise RuntimeError("live reference registry size " + str(len(live_registry)))

    opt_cfg = cfg["optimizer"]
    optimizer = torch.optim.AdamW(
        list(online.parameters()) + list(predictor.parameters()),
        lr=opt_cfg["lr"],
        weight_decay=opt_cfg["weight_decay"],
        betas=tuple(opt_cfg["betas"]),
        eps=opt_cfg["eps"],
    )
    named = dict(online.named_parameters())
    before = {
        item["name"]: named[item["name"]].detach().float().clone()
        for item in registry + live_registry
    }

    amp = bool(settings["amp"]) and device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    batch = settings["batch"]
    micro = settings["microbatch"]
    views = settings["views"]
    if batch % micro:
        raise ValueError("batch must be divisible by microbatch")
    n_micro = batch // micro
    backwards = n_micro * views
    divisor = float(views * n_micro) if settings["loss_division"] else 1.0

    optimizer.zero_grad(set_to_none=True)
    losses = []
    for _ in range(n_micro):
        ids, expression, measurement = synthetic_batch(
            settings["tokens"], vocabulary, micro, generator, device
        )
        for _ in range(views):
            blocks = make_blocks(measurement, settings["blocks"], generator)
            if settings["teacher_hidden_mask"] == "blocks_hidden_mask":
                teacher_mask = blocks.hidden_mask
            else:
                teacher_mask = torch.zeros_like(measurement)
            with torch.autocast("cuda", dtype=torch.float16, enabled=amp):
                with torch.no_grad():
                    tgt = target(ids, expression, measurement, teacher_mask, "target")
                student = online(ids, expression, measurement, blocks.hidden_mask, "student")
                predicted = predictor(
                    online.tokenizer.gene_identity,
                    blocks,
                    student.gene_states,
                    student.cell_state,
                    measurement & ~blocks.hidden_mask,
                )
                if settings["loss_operands_fp32"]:
                    target_blocks = gather_block_states(tgt.gene_states.float(), blocks)
                    loss = block_jepa_loss(predicted.float(), target_blocks)
                else:
                    target_blocks = gather_block_states(tgt.gene_states, blocks)
                    loss = block_jepa_loss(predicted, target_blocks)
            losses.append(float(loss.detach().float()))
            scaler.scale(loss / divisor).backward()

    pre_unscale = gradient_snapshot(online, registry)
    pre_unscale_live = gradient_snapshot(online, live_registry)
    if amp:
        scaler.unscale_(optimizer)
    post_unscale = gradient_snapshot(online, registry)
    post_unscale_live = gradient_snapshot(online, live_registry)
    scaler.step(optimizer)
    scaler.update()

    return {
        "condition_id": condition_id,
        "seed": seed,
        "settings": settings,
        "backwards": backwards,
        "loss_first": losses[0],
        "loss_last": losses[-1],
        "loss_all_finite": all(math.isfinite(value) for value in losses),
        "scaler_scale": float(scaler.get_scale()) if amp else None,
        "mandatory": {
            "pre_unscale": pre_unscale,
            "post_unscale": post_unscale,
            "moments": moment_snapshot(optimizer, online, registry),
            "movement": movement_snapshot(
                before, online, registry, opt_cfg["lr"], opt_cfg["weight_decay"], 1
            ),
        },
        "live_reference": {
            "pre_unscale": pre_unscale_live,
            "post_unscale": post_unscale_live,
            "movement": movement_snapshot(
                before, online, live_registry, opt_cfg["lr"], opt_cfg["weight_decay"], 1
            ),
        },
    }


def adjudicate(cfg: dict[str, Any], results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Name the unique single-factor transition, or refuse to conclude."""
    adj = cfg["adjudication"]

    def dead(condition_id: str) -> int:
        return results[condition_id]["mandatory"]["pre_unscale"]["dead_count"]

    def live_ref_dead(condition_id: str) -> int:
        return results[condition_id]["live_reference"]["pre_unscale"]["dead_count"]

    if "HEALTHY_SIMPLIFIED" not in results or "HISTORICAL_SCALE" not in results:
        return {"terminal": "STOP_C2_ENDPOINTS_INCOMPLETE", "errors": ["missing endpoint"]}

    errors: list[str] = []
    if dead("HEALTHY_SIMPLIFIED") != adj["healthy_requires_dead_mandatory"]:
        errors.append("STOP_C2_HEALTHY_ENDPOINT_NOT_REPRODUCED:" + str(dead("HEALTHY_SIMPLIFIED")))
    if dead("HISTORICAL_SCALE") != adj["historical_requires_dead_mandatory"]:
        errors.append("STOP_C2_HISTORICAL_ENDPOINT_NOT_REPRODUCED:" + str(dead("HISTORICAL_SCALE")))
    if live_ref_dead("HISTORICAL_SCALE") != 0:
        errors.append("STOP_C2_LIVE_REFERENCE_NOT_LIVE_AT_HISTORICAL")
    if errors:
        return {"terminal": errors[0], "errors": errors}

    forward = {f["id"]: dead(f["id"]) for f in cfg["frozen_factor_order"] if f["id"] in results}
    reverse = {
        r["id"]: dead(r["id"]) for r in cfg["reverse_sufficiency_order"] if r["id"] in results
    }
    rescuers = sorted(cid for cid, count in forward.items() if count == 0)
    inducers = sorted(
        cid for cid, count in reverse.items()
        if count == adj["historical_requires_dead_mandatory"]
    )

    if len(rescuers) == 1 and len(inducers) == 1:
        terminal = "C2_GRADIENT_SEVERING_CONDITION_LOCALIZED"
    elif not rescuers:
        terminal = "STOP_C2_CAUSE_NOT_LOCALIZED_NO_SINGLE_FACTOR_RESCUES"
    else:
        terminal = adj["terminal_if_not_unique"]
    return {
        "terminal": terminal,
        "forward_dead_counts": forward,
        "reverse_dead_counts": reverse,
        "necessary_and_sufficient_rescuers": rescuers,
        "sufficient_inducers": inducers,
        "errors": [],
    }


def environment_record() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "cudnn": torch.backends.cudnn.version(),
    }


def build_conditions(cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Expand endpoints plus every frozen one-factor variant. Order is frozen."""
    conditions: dict[str, dict[str, Any]] = {}
    for name, settings in cfg["endpoints"].items():
        conditions[name] = dict(settings)
    for factor in cfg["frozen_factor_order"]:
        merged = dict(cfg["endpoints"]["HISTORICAL_SCALE"])
        merged.update(factor["override"])
        conditions[factor["id"]] = merged
    for factor in cfg["reverse_sufficiency_order"]:
        merged = dict(cfg["endpoints"]["HEALTHY_SIMPLIFIED"])
        merged.update(factor["override"])
        conditions[factor["id"]] = merged
    return conditions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--condition", action="append", default=None)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    device = torch.device(args.device)
    args.out.mkdir(parents=True, exist_ok=True)

    conditions = build_conditions(cfg)
    selected = args.condition or list(conditions)
    results: dict[str, Any] = {}
    for condition_id in selected:
        record = run_condition(cfg, condition_id, conditions[condition_id], cfg["seeds"][0], device)
        results[condition_id] = record
        (args.out / ("CONDITION_" + condition_id + ".json")).write_bytes(
            canonical_json_bytes(record) + b"\n"
        )
        summary = record["mandatory"]["pre_unscale"]
        print(
            "{0:34s} dead={1:3d}/{2}  live_ref_dead={3}  backwards={4}  loss={5:.4f}".format(
                condition_id,
                summary["dead_count"],
                summary["total"],
                record["live_reference"]["pre_unscale"]["dead_count"],
                record["backwards"],
                record["loss_first"],
            ),
            flush=True,
        )

    adjudication = (
        adjudicate(cfg, results) if len(selected) > 2 else {"terminal": "PARTIAL_RUN_NOT_ADJUDICATED"}
    )
    payload = {
        "contract_id": cfg["contract_id"],
        "config_sha256": sha256_file(args.config),
        "source_sha256": sha256_file(Path(__file__)),
        "ipb_jepa_sha256": sha256_file(REPO / "src" / "sea_ad_jepa" / "v4" / "ipb_jepa.py"),
        "environment": environment_record(),
        "invocation": {"argv": sys.argv[1:], "cwd": str(Path.cwd()), "device": str(device)},
        "conditions_executed": selected,
        "results": results,
        "adjudication": adjudication,
    }
    (args.out / "C2_CAUSAL_ADJUDICATION.json").write_bytes(canonical_json_bytes(payload) + b"\n")
    print(json.dumps(adjudication, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
