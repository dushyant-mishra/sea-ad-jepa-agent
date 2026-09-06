#!/usr/bin/env python3
"""C2-v3 exact-path forensic: drive the real historical training step, unmodified.

The historical update is `phase_e.run_update` from
`scripts/v4/stage81a3_prod41k_engineering_smoke.py`. v3 calls that function
directly. The only substitution is the loader, so target construction, block
sampling, block identity, dropout, AMP, checkpointing, loss scaling and the
optimizer are inherited rather than re-approximated.

`run_update` zeroes gradients only at its start, so on return `.grad` holds the
post-unscale gradients and `optimizer.state` holds the moments.

Reads no real expression, no pathology, no protected partition.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

import torch

WORKTREE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKTREE))

MANDATORY_ROLES = ("attention_norm", "attention.query", "attention.key", "attention.value")
LIVE_REFERENCE_ROLES = ("attention.output",)


def canonical_root(declared: list[str]) -> Path:
    for candidate in declared:
        if (Path(candidate) / "scripts/v4/stage81a3_prod41k_engineering_smoke.py").is_file():
            return Path(candidate)
    raise RuntimeError("canonical repository not found in: " + str(declared))


def load_phase_e(root: Path):
    """Import the historical module exactly as the historical trainer does."""
    sys.path.insert(0, str(root / "src"))
    sys.path.insert(0, str(root / "exports" / "static_context_decomposition_v4_20260821"))
    spec = importlib.util.spec_from_file_location(
        "phase_e", root / "scripts" / "v4" / "stage81a3_prod41k_engineering_smoke.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["phase_e"] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def role_of(name: str) -> str | None:
    for role in MANDATORY_ROLES + LIVE_REFERENCE_ROLES:
        if "." + role + "." in name:
            return role
    return None


def registries(online: torch.nn.Module) -> tuple[list[str], list[str]]:
    mandatory = sorted(n for n, _ in online.named_parameters() if role_of(n) in MANDATORY_ROLES)
    live = sorted(n for n, _ in online.named_parameters() if role_of(n) in LIVE_REFERENCE_ROLES)
    return mandatory, live


def gradient_report(online: torch.nn.Module, names: list[str]) -> dict[str, Any]:
    """Missing, zero, nonfinite and live are distinguished; nothing is pooled."""
    by_name = dict(online.named_parameters())
    entries = {}
    for name in names:
        grad = by_name[name].grad
        if grad is None:
            entries[name] = {"status": "MISSING", "norm": None}
            continue
        norm = float(grad.detach().float().norm())
        if norm != norm or norm in (float("inf"), float("-inf")):
            status = "NONFINITE"
        elif norm == 0.0:
            status = "ZERO"
        else:
            status = "LIVE"
        entries[name] = {"status": status, "norm": norm}
    dead = sorted(n for n, e in entries.items() if e["status"] != "LIVE")
    return {"entries": entries, "dead_names": dead, "dead_count": len(dead), "total": len(names)}


def moment_report(
    optimizer: torch.optim.Optimizer, online: torch.nn.Module, names: list[str]
) -> dict[str, Any]:
    by_name = dict(online.named_parameters())
    entries = {}
    for name in names:
        state = optimizer.state.get(by_name[name], {})
        first, second = state.get("exp_avg"), state.get("exp_avg_sq")
        step = state.get("step")
        entries[name] = {
            "exp_avg_norm": None if first is None else float(first.float().norm()),
            "exp_avg_sq_norm": None if second is None else float(second.float().norm()),
            "step": None if step is None else (
                int(step.item()) if torch.is_tensor(step) else int(step)
            ),
        }
    zero_both = sum(
        1 for e in entries.values()
        if e["exp_avg_norm"] == 0.0 and e["exp_avg_sq_norm"] == 0.0
    )
    return {"entries": entries, "zero_both_moments": zero_both, "total": len(names)}


class autocast_override:
    """Override the outer autocast only, leaving nested disabled regions intact.

    `run_update` hardcodes `torch.autocast(..., dtype=float16, enabled=cuda)`.
    Rather than fork the historical function, intercept the outer context. The
    nested `torch.autocast(enabled=False)` inside KernelLinearAttention passes
    `enabled=False` explicitly and is therefore never touched.
    """

    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.real = torch.autocast

    def __enter__(self):
        if self.mode == "fp16":
            return self
        real, mode = self.real, self.mode

        def patched(*args, **kwargs):
            if kwargs.get("enabled", True):
                if mode == "off":
                    kwargs["enabled"] = False
                elif mode == "bf16":
                    kwargs["dtype"] = torch.bfloat16
                else:
                    raise ValueError("unknown autocast mode: " + mode)
            return real(*args, **kwargs)

        torch.autocast = patched
        return self

    def __exit__(self, *exc: object) -> None:
        torch.autocast = self.real


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--updates", type=int, default=1)
    parser.add_argument("--batch", type=int, default=None, help="default: historical EFFECTIVE_BATCH")
    parser.add_argument("--microbatch", type=int, default=None, help="default: historical MICROBATCH")
    parser.add_argument("--seed", type=int, default=8113002)
    parser.add_argument("--measured-fraction", type=float, default=1.0)
    parser.add_argument("--zero-inflation", type=float, default=0.0)
    parser.add_argument("--value-law", default="log1p_exponential")
    parser.add_argument("--value-scale", type=float, default=1.0)
    parser.add_argument("--label", default="STEP_A_EXACT_MECHANICS")
    parser.add_argument("--autocast", choices=("fp16", "off", "bf16"), default="fp16")
    parser.add_argument("--attention-cast", choices=("historical", "after_projection", "projections_fp32", "branch_fp32"),
                        default="historical")
    parser.add_argument("--no-gradscaler", action="store_true")
    parser.add_argument("--no-autocast-cache", action="store_true",
                        help="disable the autocast weight cast cache")
    parser.add_argument("--no-fp16-reduced-reduction", action="store_true",
                        help="force fp32 accumulation in fp16 matmul reductions")
    parser.add_argument("--no-checkpointing", action="store_true")
    parser.add_argument("--target-blocks", type=int, default=None)
    parser.add_argument("--mask-fraction", type=float, default=None)
    parser.add_argument("--canonical-root", action="append",
                        default=["/mnt/d/Jepa project", "D:/Jepa project"])
    args = parser.parse_args()

    root = canonical_root(args.canonical_root)
    phase_e = load_phase_e(root)
    from scripts.v4.c2_synthetic_loader_v3 import SyntheticTrainLoader, synthetic_cohort
    from scripts.v4.c2_attention_cast_variant_v3 import attention_cast_variant
    from sea_ad_jepa.v4.ipb_jepa import KernelLinearAttention

    # Historical geometry is declared by the trainer, not the smoke module.
    HISTORICAL_EFFECTIVE_BATCH, HISTORICAL_MICROBATCH = 128, 8
    batch = args.batch if args.batch is not None else HISTORICAL_EFFECTIVE_BATCH
    micro = args.microbatch if args.microbatch is not None else HISTORICAL_MICROBATCH
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    online, target, predictor, optimizer, scaler, controller = phase_e.build_components(
        args.seed, device
    )
    mandatory, live = registries(online)
    if len(mandatory) != 48 or len(live) != 12:
        raise RuntimeError(f"registry sizes {len(mandatory)}/{len(live)}")

    if args.no_gradscaler:
        scaler = torch.amp.GradScaler("cuda", enabled=False)
    if args.no_checkpointing:
        online.gradient_checkpointing = False
    # sample_uniform_target_blocks binds these as keyword-only defaults at def time.
    sampler_defaults = dict(phase_e.sample_uniform_target_blocks.__kwdefaults__ or {})
    if args.target_blocks is not None:
        phase_e.sample_uniform_target_blocks.__kwdefaults__["block_count"] = args.target_blocks
    if args.mask_fraction is not None:
        phase_e.sample_uniform_target_blocks.__kwdefaults__["mask_fraction"] = args.mask_fraction

    loader = SyntheticTrainLoader(
        seed=args.seed,
        measured_fraction=args.measured_fraction,
        zero_inflation=args.zero_inflation,
        value_law=args.value_law,
        value_scale=args.value_scale,
    )
    cohort = synthetic_cohort(batch)
    sampler = torch.Generator().manual_seed(args.seed)

    updates = []
    for cursor in range(args.updates):
        online.train()
        predictor.train()
        target.eval()
        torch.set_autocast_cache_enabled(not args.no_autocast_cache)
        if args.no_fp16_reduced_reduction:
            torch.backends.cuda.matmul.allow_fp16_reduced_precision_reduction = False
        with autocast_override(args.autocast), attention_cast_variant(
            KernelLinearAttention, args.attention_cast
        ):
            result = phase_e.run_update(
                loader=loader, cohort=cohort, sampler=sampler, cursor=cursor,
                seed=args.seed, microbatch=micro, effective_batch=batch,
                device=device, online=online, target=target, predictor=predictor,
                optimizer=optimizer, scaler=scaler, controller=controller,
            )
        grads = gradient_report(online, mandatory)
        live_grads = gradient_report(online, live)
        moments = moment_report(optimizer, online, mandatory)
        live_moments = moment_report(optimizer, online, live)
        updates.append({
            "cursor": cursor,
            "loss": result["loss"],
            "step_succeeded": result["step_succeeded"],
            "online_moved": result.get("online_moved"),
            "ema_equation_equal": (result.get("ema_equation") or {}).get("equal"),
            "mandatory_gradients_post_unscale": grads,
            "live_reference_gradients_post_unscale": live_grads,
            "mandatory_moments": moments,
            "live_reference_moments": live_moments,
        })
        print(
            "u%03d loss=%.4f  mandatory dead=%d/48  zero-both-moments=%d/48  "
            "live_ref dead=%d/12  zero-both=%d/12  step_ok=%s"
            % (cursor, result["loss"], grads["dead_count"], moments["zero_both_moments"],
               live_grads["dead_count"], live_moments["zero_both_moments"],
               result["step_succeeded"]),
            flush=True,
        )

    args.out.mkdir(parents=True, exist_ok=True)
    payload = {
        "label": args.label,
        "historical_step_source": str(
            root / "scripts/v4/stage81a3_prod41k_engineering_smoke.py"
        ),
        "historical_step_sha256": sha256_file(
            root / "scripts/v4/stage81a3_prod41k_engineering_smoke.py"
        ),
        "ipb_jepa_sha256": sha256_file(root / "src/sea_ad_jepa/v4/ipb_jepa.py"),
        "forensic_source_sha256": sha256_file(Path(__file__)),
        "loader_manifest": loader.manifest(),
        "geometry": {
            "effective_batch": batch, "microbatch": micro,
            "views": phase_e.VIEWS, "mask_fraction": phase_e.MASK_FRACTION,
            "target_block_count": phase_e.TARGET_BLOCK_COUNT,
            "vocabulary_size": phase_e.VOCABULARY_SIZE,
            "historical_effective_batch": HISTORICAL_EFFECTIVE_BATCH,
            "historical_microbatch": HISTORICAL_MICROBATCH,
            "ema_momentum": phase_e.EMA_MOMENTUM,
            "is_historical_geometry": batch == HISTORICAL_EFFECTIVE_BATCH
            and micro == HISTORICAL_MICROBATCH,
        },
        "environment": {
            "python": sys.version.split()[0], "platform": platform.platform(),
            "torch": torch.__version__, "device": str(device),
            "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
        "factors": {
            "autocast": args.autocast,
            "attention_cast": args.attention_cast,
            "gradscaler_enabled": not args.no_gradscaler,
            "autocast_cache_enabled": not args.no_autocast_cache,
            "fp16_reduced_precision_reduction": torch.backends.cuda.matmul.allow_fp16_reduced_precision_reduction,
            "gradient_checkpointing": online.gradient_checkpointing,
            "target_blocks": phase_e.sample_uniform_target_blocks.__kwdefaults__["block_count"],
            "mask_fraction": phase_e.sample_uniform_target_blocks.__kwdefaults__["mask_fraction"],
            "historical_defaults": sampler_defaults,
        },
        "invocation": {"argv": sys.argv[1:], "seed": args.seed},
        "updates": updates,
    }
    (args.out / ("C2_V3_" + args.label + ".json")).write_bytes(
        canonical_json_bytes(payload) + b"\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
