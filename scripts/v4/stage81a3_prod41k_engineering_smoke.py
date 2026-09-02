#!/usr/bin/env python3
"""Decision-grade Phase-E engineering smoke for the PROD41K trained teacher.

This is an engineering gate only.  It never reads pathology, DEV, or SEALED
data, never evaluates biology, and never authorizes Phase T1 automatically.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[2]
EXPORT = ROOT / "exports" / "prod41k_teacher_t1_20260823"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "exports" / "static_context_decomposition_v4_20260821"))

from production_train_loader import (  # noqa: E402
    ADDRESS_COUNT,
    MEASURED_COLLISION_UNRESOLVED,
    MEASURED_SCALAR,
    STRUCTURALLY_UNMEASURED,
    ProductionTrainLoader,
)
from sea_ad_jepa.v4 import (  # noqa: E402
    EMAOptimizerStepController,
    capture_synthetic_checkpoint,
    create_ema_target,
    restore_synthetic_checkpoint,
)
from sea_ad_jepa.v4.ipb_jepa import (  # noqa: E402
    BlockPredictor,
    IPBEncoder,
    TargetBlocks,
    block_jepa_loss,
    gather_block_states,
)
from sea_ad_jepa.v4.masking import keyed_mask_seed  # noqa: E402

VOCABULARY_SIZE = 41_238
WIDTH = 160
HEADS = 4
BLOCKS = 6
VIEWS = 4
MASK_FRACTION = 0.40
TARGET_BLOCK_COUNT = 16
EMA_MOMENTUM = 0.996
FROZEN_SAMPLER_SOURCE = (
    ROOT
    / "exports"
    / "stage81b_checkpoints_with_exact_anchor_implementation_20260821-084336"
    / "implementation"
    / "ipb_jepa.py"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=8_113_002)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--effective-batch", type=int, default=128)
    parser.add_argument("--microbatch-candidates", default="8,4,2,1")
    parser.add_argument("--vram-safety-gib", type=float, default=13.0)
    parser.add_argument("--mask-audit-chunk", type=int, default=32)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_key(matrix_id: str, local_row: int, cell_id: str) -> int:
    payload = f"{matrix_id}|{int(local_row)}|{cell_id}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % (2**63 - 1)


def source_family(matrix_id: str) -> str:
    if matrix_id.startswith("HVS::"):
        return "HVS"
    if matrix_id.startswith("NPH52::"):
        return "NPH52"
    return "SEA_AD"


def _block_sizes(hidden_count: int, block_count: int) -> list[int]:
    quotient, remainder = divmod(hidden_count, block_count)
    return [quotient + (index < remainder) for index in range(block_count)]


def sample_uniform_target_blocks(
    measurement_mask: torch.Tensor,
    *,
    production_seed: int,
    cell_indices: torch.Tensor,
    sample_pass: int,
    view_index: int,
    mask_fraction: float = MASK_FRACTION,
    block_count: int = TARGET_BLOCK_COUNT,
) -> TargetBlocks:
    """Exact isolated graph-free sampler mechanics from the frozen Stage81B source."""
    if measurement_mask.dtype is not torch.bool or measurement_mask.ndim != 2:
        raise ValueError("measurement_mask must be boolean [cells, genes]")
    if cell_indices.ndim != 1 or len(cell_indices) != len(measurement_mask):
        raise ValueError("cell_indices must contain one index per cell")
    if block_count < 1 or not 0.0 <= mask_fraction <= 1.0:
        raise ValueError("invalid block_count or mask_fraction")
    device = measurement_mask.device
    measured_cpu = measurement_mask.cpu()
    hidden = torch.zeros_like(measured_cpu)
    row_blocks: list[list[list[int]]] = []
    maximum_size = 0
    for row in range(len(measured_cpu)):
        measured = torch.nonzero(measured_cpu[row], as_tuple=False).flatten()
        hidden_count = int(math.floor(mask_fraction * len(measured)))
        sizes = _block_sizes(hidden_count, block_count)
        maximum_size = max(maximum_size, max(sizes, default=0))
        generator = torch.Generator(device="cpu").manual_seed(
            keyed_mask_seed(
                production_seed=production_seed,
                cell_index=int(cell_indices[row]),
                sample_pass=sample_pass,
                view_index=view_index,
            )
        )
        ranking = measured[torch.randperm(len(measured), generator=generator)]
        cursor = 0
        blocks = []
        for size in sizes:
            block = ranking[cursor : cursor + size].tolist()
            blocks.append(block)
            if block:
                hidden[row, block] = True
            cursor += size
        if cursor != hidden_count:
            raise RuntimeError("uniform target blocks do not match exact hidden count")
        row_blocks.append(blocks)
    indices = torch.full((len(row_blocks), block_count, maximum_size), -1, dtype=torch.int64)
    members = torch.zeros_like(indices, dtype=torch.bool)
    for row, blocks_for_row in enumerate(row_blocks):
        for block_index, block in enumerate(blocks_for_row):
            if block:
                indices[row, block_index, : len(block)] = torch.tensor(block)
                members[row, block_index, : len(block)] = True
    return TargetBlocks(
        hidden.to(device),
        indices.to(device),
        members.to(device),
        torch.zeros(len(row_blocks), dtype=torch.int64, device=device),
    )


def prepare_cohort(loader: ProductionTrainLoader) -> pd.DataFrame:
    cells = loader.cell_table().copy()
    cells["source_family"] = cells.matrix_id.map(source_family)
    cells["canonical_donor_id"] = cells.source_family + "::" + cells.donor_id.astype(str)
    splits = pd.read_csv(loader.inputs["foundation_split_registry"])
    foundation = splits.loc[
        splits.split_domain.eq("foundation"), ["canonical_person_id", "split"]
    ].drop_duplicates()
    cells = cells.merge(
        foundation,
        left_on="canonical_donor_id",
        right_on="canonical_person_id",
        how="left",
        validate="many_to_one",
    )
    if cells["split"].isna().any() or not cells["split"].eq("train").all():
        bad = cells.loc[~cells["split"].eq("train"), ["canonical_donor_id", "split"]]
        raise RuntimeError(f"FOUNDATION TRAIN firewall violation:\n{bad.drop_duplicates()}")
    protected = set(
        foundation.loc[foundation["split"].isin(["development", "sealed_holdout"]), "canonical_person_id"]
    )
    overlap = set(cells.canonical_donor_id) & protected
    if overlap:
        raise RuntimeError(f"DEV/SEALED donor overlap: {sorted(overlap)}")
    cells["stable_mask_key"] = [
        stable_key(row.matrix_id, row.local_row, row.cell_id) for row in cells.itertuples()
    ]
    if cells.stable_mask_key.duplicated().any():
        raise RuntimeError("stable mask-key collision")
    cells = cells.sort_values(
        ["canonical_donor_id", "matrix_id", "local_row", "cell_id"], kind="stable"
    ).reset_index(drop=True)
    cells["cohort_row"] = np.arange(len(cells), dtype=np.int64)
    return cells


def measurement_rows(loader: ProductionTrainLoader, rows: pd.DataFrame) -> torch.Tensor:
    return torch.from_numpy(
        np.stack([loader.states[str(matrix_id)] for matrix_id in rows.matrix_id], axis=0)
    ).eq(int(MEASURED_SCALAR))


def audit_masks(
    loader: ProductionTrainLoader,
    cohort: pd.DataFrame,
    *,
    seed: int,
    chunk_size: int,
) -> dict[str, Any]:
    view_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    cell_rows: list[dict[str, Any]] = []
    illegal = 0
    start = time.perf_counter()
    for begin in range(0, len(cohort), chunk_size):
        rows = cohort.iloc[begin : begin + chunk_size]
        measured = measurement_rows(loader, rows)
        keys = torch.tensor(rows.stable_mask_key.to_numpy(np.int64), dtype=torch.int64)
        blocks = [
            sample_uniform_target_blocks(
                measured,
                production_seed=seed,
                cell_indices=keys,
                sample_pass=0,
                view_index=view,
            )
            for view in range(VIEWS)
        ]
        for local, cohort_row in enumerate(rows.cohort_row):
            masks = [item.hidden_mask[local] for item in blocks]
            measured_count = int(measured[local].sum())
            expected_hidden = int(math.floor(MASK_FRACTION * measured_count))
            signatures = []
            for view, mask in enumerate(masks):
                hidden_count = int(mask.sum())
                illegal_count = int((mask & ~measured[local]).sum())
                illegal += illegal_count
                signatures.append(hashlib.sha256(mask.numpy().tobytes()).hexdigest())
                view_rows.append(
                    {
                        "cohort_row": int(cohort_row),
                        "view": view,
                        "measured_count": measured_count,
                        "hidden_count": hidden_count,
                        "expected_hidden_count": expected_hidden,
                        "hidden_fraction": hidden_count / measured_count,
                        "illegal_hidden_count": illegal_count,
                    }
                )
            cell_rows.append(
                {
                    "cohort_row": int(cohort_row),
                    "four_distinct": len(set(signatures)) == VIEWS,
                }
            )
            for left in range(VIEWS):
                for right in range(left + 1, VIEWS):
                    intersection = int((masks[left] & masks[right]).sum())
                    union = int((masks[left] | masks[right]).sum())
                    k = expected_hidden
                    expected_jaccard = (k / (2 * measured_count - k)) if measured_count else 0.0
                    pair_rows.append(
                        {
                            "cohort_row": int(cohort_row),
                            "view_left": left,
                            "view_right": right,
                            "jaccard": intersection / union if union else 0.0,
                            "expected_independent_jaccard_approx": expected_jaccard,
                            "distinct": signatures[left] != signatures[right],
                        }
                    )
        del blocks, measured
    view_frame = pd.DataFrame(view_rows)
    pair_frame = pd.DataFrame(pair_rows)
    cell_frame = pd.DataFrame(cell_rows)
    view_frame.to_csv(EXPORT / "phase_e_mask_view_stats.csv", index=False)
    pair_frame.to_csv(EXPORT / "phase_e_mask_pair_stats.csv", index=False)
    cell_frame.to_csv(EXPORT / "phase_e_mask_cell_stats.csv", index=False)
    pair_summary = []
    for (left, right), group in pair_frame.groupby(["view_left", "view_right"]):
        q = group.jaccard.quantile([0.0, 0.25, 0.5, 0.75, 1.0])
        pair_summary.append(
            {
                "pair": f"{left}-{right}",
                "mean": float(group.jaccard.mean()),
                "q0": float(q.loc[0.0]),
                "q25": float(q.loc[0.25]),
                "median": float(q.loc[0.5]),
                "q75": float(q.loc[0.75]),
                "q100": float(q.loc[1.0]),
                "pairwise_distinct_fraction": float(group.distinct.mean()),
                "expected_independent_jaccard_approx_mean": float(
                    group.expected_independent_jaccard_approx.mean()
                ),
            }
        )
    return {
        "seconds": time.perf_counter() - start,
        "illegal_hidden_count": illegal,
        "exact_hidden_count_all_rows": bool(
            (view_frame.hidden_count == view_frame.expected_hidden_count).all()
        ),
        "four_distinct_fraction": float(cell_frame.four_distinct.mean()),
        "pairs": pair_summary,
    }


def build_components(seed: int, device: torch.device):
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    online = IPBEncoder(
        vocabulary_size=VOCABULARY_SIZE,
        width=WIDTH,
        heads=HEADS,
        blocks=BLOCKS,
        gradient_checkpointing=True,
    ).to(device)
    target = create_ema_target(online).to(device)
    predictor = BlockPredictor(width=WIDTH, heads=HEADS).to(device)
    online.train()
    predictor.train()
    target.eval()
    parameters = list(online.parameters()) + list(predictor.parameters())
    optimizer = torch.optim.AdamW(parameters, lr=1e-4)
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")
    controller = EMAOptimizerStepController(online, target)
    return online, target, predictor, optimizer, scaler, controller


def component_gradient_report(online: IPBEncoder, predictor: BlockPredictor) -> dict[str, Any]:
    groups = {
        "identity_query_path": list(online.tokenizer.gene_identity.parameters()),
        "value_tokenizer_H": (
            list(online.tokenizer.identity_projection.parameters())
            + list(online.tokenizer.value_encoder.parameters())
            + list(online.tokenizer.output_norm.parameters())
        ),
        "CELL": [online.cell_token],
        "IPB_shared": list(online.blocks.parameters()) + list(online.final_norm.parameters()),
        "predictor": list(predictor.parameters()),
    }
    report: dict[str, Any] = {}
    for name, parameters in groups.items():
        missing = sum(parameter.grad is None for parameter in parameters)
        nonfinite = sum(
            parameter.grad is not None and not bool(torch.isfinite(parameter.grad).all())
            for parameter in parameters
        )
        squared = sum(
            float(parameter.grad.detach().float().square().sum())
            for parameter in parameters
            if parameter.grad is not None
        )
        report[name] = {
            "l2_norm": math.sqrt(squared),
            "missing_parameter_tensors": missing,
            "nonfinite_parameter_tensors": nonfinite,
        }
    return report


def state_snapshot(module: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {name: value.detach().clone() for name, value in module.state_dict().items()}


def compare_tensor_dicts(left: dict[str, torch.Tensor], right: dict[str, torch.Tensor]) -> dict[str, Any]:
    if left.keys() != right.keys():
        return {"equal": False, "mismatched": ["<keys>"], "max_abs_difference": math.inf}
    mismatched = []
    maximum = 0.0
    for name in left:
        a, b = left[name], right[name]
        if not torch.equal(a, b):
            mismatched.append(name)
            if a.is_floating_point() or a.is_complex():
                maximum = max(maximum, float((a - b).abs().max()))
            else:
                maximum = math.inf
    return {"equal": not mismatched, "mismatched": mismatched, "max_abs_difference": maximum}


def nested_equal(left: Any, right: Any) -> bool:
    if isinstance(left, torch.Tensor):
        return isinstance(right, torch.Tensor) and torch.equal(left, right)
    if isinstance(left, dict):
        return isinstance(right, dict) and left.keys() == right.keys() and all(
            nested_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, (list, tuple)):
        return isinstance(right, type(left)) and len(left) == len(right) and all(
            nested_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


def ema_equation_check(
    before: dict[str, torch.Tensor], online: IPBEncoder, target: torch.nn.Module
) -> dict[str, Any]:
    online_state = online.state_dict()
    actual = target.encoder.state_dict()
    expected = {}
    for name, prior in before.items():
        if prior.is_floating_point() or prior.is_complex():
            expected[name] = prior.clone().mul_(EMA_MOMENTUM).add_(
                online_state[name], alpha=1.0 - EMA_MOMENTUM
            )
        else:
            expected[name] = online_state[name].clone()
    return compare_tensor_dicts(expected, actual)


def slice_blocks(blocks: TargetBlocks, start: int, end: int, device: torch.device) -> TargetBlocks:
    return TargetBlocks(
        blocks.hidden_mask[start:end].to(device),
        blocks.indices[start:end].to(device),
        blocks.member_mask[start:end].to(device),
        blocks.fallback_counts[start:end].to(device),
    )


def run_update(
    *,
    loader: ProductionTrainLoader,
    cohort: pd.DataFrame,
    sampler: torch.Generator,
    cursor: int,
    seed: int,
    microbatch: int,
    effective_batch: int,
    device: torch.device,
    online: IPBEncoder,
    target: torch.nn.Module,
    predictor: BlockPredictor,
    optimizer: torch.optim.Optimizer,
    scaler: torch.amp.GradScaler,
    controller: EMAOptimizerStepController,
) -> dict[str, Any]:
    if effective_batch % microbatch:
        raise ValueError("effective batch must be divisible by microbatch")
    timing: dict[str, float] = {}
    selection = torch.randperm(len(cohort), generator=sampler)[:effective_batch]
    rows = cohort.iloc[selection.numpy()].copy().reset_index(drop=True)
    rows["loader_row"] = np.arange(len(rows), dtype=np.int64)
    selected_ids = rows.stable_mask_key.astype(np.int64).tolist()
    start = time.perf_counter()
    values_np, states_np = loader.load(rows)
    timing["loader_materialization_seconds"] = time.perf_counter() - start
    measurements = torch.from_numpy(states_np).eq(int(MEASURED_SCALAR))
    if np.any((states_np != MEASURED_SCALAR) & (values_np != 0.0)):
        raise RuntimeError("numeric value outside MEASURED_SCALAR")
    keys = torch.tensor(rows.stable_mask_key.to_numpy(np.int64), dtype=torch.int64)
    start = time.perf_counter()
    views = [
        sample_uniform_target_blocks(
            measurements,
            production_seed=seed,
            cell_indices=keys,
            sample_pass=cursor,
            view_index=view,
        )
        for view in range(VIEWS)
    ]
    timing["mask_generation_seconds"] = time.perf_counter() - start
    if any(bool((item.hidden_mask & ~measurements).any()) for item in views):
        raise RuntimeError("artificial target outside MEASURED_SCALAR")
    mask_hashes = [sha256_bytes(item.hidden_mask.numpy().tobytes()) for item in views]
    mask_copies = [item.hidden_mask.clone() for item in views]
    optimizer.zero_grad(set_to_none=True)
    target_before = state_snapshot(target.encoder)
    loss_total = 0.0
    transfer_seconds = 0.0
    compute_start = time.perf_counter()
    for begin in range(0, effective_batch, microbatch):
        end = begin + microbatch
        transfer_start = time.perf_counter()
        expression = torch.from_numpy(values_np[begin:end]).to(device)
        measured = measurements[begin:end].to(device)
        gene_ids = torch.arange(VOCABULARY_SIZE, device=device).expand(microbatch, -1)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        transfer_seconds += time.perf_counter() - transfer_start
        with torch.autocast(
            device_type=device.type,
            dtype=torch.float16,
            enabled=device.type == "cuda",
        ):
            with torch.no_grad():
                teacher = target(
                    gene_ids, expression, measured, torch.zeros_like(measured), "target"
                )
            for view in range(VIEWS):
                block = slice_blocks(views[view], begin, end, device)
                student = online(
                    gene_ids, expression, measured, block.hidden_mask, "student"
                )
                prediction = predictor(
                    online.tokenizer.gene_identity,
                    block,
                    student.gene_states,
                    student.cell_state,
                    measured & ~block.hidden_mask,
                )
                teacher_blocks = gather_block_states(teacher.gene_states, block)
                raw_loss = block_jepa_loss(prediction, teacher_blocks)
                scaled_loss = raw_loss / (VIEWS * (effective_batch // microbatch))
                if not bool(torch.isfinite(raw_loss)):
                    raise RuntimeError("nonfinite JEPA loss")
                scaler.scale(scaled_loss).backward()
                loss_total += float(raw_loss.detach()) / (
                    VIEWS * (effective_batch // microbatch)
                )
                del block, student, prediction, teacher_blocks, raw_loss, scaled_loss
            del teacher, expression, measured, gene_ids
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    timing["compute_seconds"] = time.perf_counter() - compute_start
    timing["host_to_device_seconds"] = transfer_seconds
    scaler.unscale_(optimizer)
    gradients = component_gradient_report(online, predictor)
    missing = sum(item["missing_parameter_tensors"] for item in gradients.values())
    nonfinite = sum(item["nonfinite_parameter_tensors"] for item in gradients.values())
    if missing or nonfinite:
        raise RuntimeError(f"invalid active gradients: missing={missing}, nonfinite={nonfinite}")
    if any(parameter.grad is not None for parameter in target.parameters()):
        raise RuntimeError("EMA target received gradients")
    online_before_step = state_snapshot(online)
    scale_before = float(scaler.get_scale())
    scaler.step(optimizer)
    scaler.update()
    scale_after = float(scaler.get_scale())
    step_succeeded = scale_after >= scale_before
    if not step_succeeded:
        target_after_skip = state_snapshot(target.encoder)
        skip_compare = compare_tensor_dicts(target_before, target_after_skip)
        return {
            "cursor": cursor,
            "selected_ids": selected_ids,
            "mask_hashes": mask_hashes,
            "masks": mask_copies,
            "loss": loss_total,
            "step_succeeded": False,
            "skipped_target_immobile": skip_compare["equal"],
            "gradient_components": gradients,
            "timing": timing,
        }
    controller.after_successful_optimizer_step(momentum=EMA_MOMENTUM)
    equation = ema_equation_check(target_before, online, target)
    movement = compare_tensor_dicts(online_before_step, online.state_dict())
    return {
        "cursor": cursor,
        "selected_ids": selected_ids,
        "mask_hashes": mask_hashes,
        "masks": mask_copies,
        "loss": loss_total,
        "step_succeeded": True,
        "online_moved": not movement["equal"],
        "ema_equation": equation,
        "gradient_components": gradients,
        "timing": timing,
    }


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def host_rss_bytes() -> int | None:
    try:
        import psutil

        return int(psutil.Process().memory_info().rss)
    except Exception:
        return None


def main() -> None:
    args = parse_args()
    EXPORT.mkdir(parents=True, exist_ok=True)
    if args.steps < 1 or args.effective_batch < 1:
        raise ValueError("steps and effective batch must be positive")
    device = torch.device(
        args.device if args.device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")
    )
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.cuda.empty_cache()
    torch.use_deterministic_algorithms(True)

    wall_start = time.perf_counter()
    loader_start = time.perf_counter()
    loader = ProductionTrainLoader()
    cohort = prepare_cohort(loader)
    cohort_seconds = time.perf_counter() - loader_start
    if len(cohort) != 4_726 or cohort.canonical_donor_id.nunique() != 149:
        raise RuntimeError("unexpected complete FOUNDATION TRAIN cohort geometry")
    if cohort.operator_index.nunique() != 42 or set(cohort.source_family) != {"HVS", "SEA_AD", "NPH52"}:
        raise RuntimeError("source/operator closure failure")
    cohort.to_csv(EXPORT / "phase_e_foundation_train_cohort_manifest.csv", index=False)
    source_summary = (
        cohort.groupby("source_family")
        .agg(cells=("cell_id", "size"), donors=("canonical_donor_id", "nunique"), operators=("operator_index", "nunique"))
        .reset_index()
    )
    source_summary.to_csv(EXPORT / "phase_e_source_summary.csv", index=False)

    all_states = np.stack(list(loader.states.values()))
    scalar_observable = int((all_states == MEASURED_SCALAR).any(axis=0).sum())
    collision_only = int(
        ((all_states == MEASURED_COLLISION_UNRESOLVED).any(axis=0) & ~(all_states == MEASURED_SCALAR).any(axis=0)).sum()
    )
    if all_states.shape[1] != VOCABULARY_SIZE or scalar_observable != 40_949 or collision_only != 289:
        raise RuntimeError("production address namespace mismatch")
    state_counts = {"MEASURED_SCALAR": 0, "STRUCTURALLY_UNMEASURED": 0, "MEASURED_COLLISION_UNRESOLVED": 0}
    cells_per_operator = cohort.groupby("matrix_id").size().to_dict()
    for matrix_id, state in loader.states.items():
        multiplier = int(cells_per_operator.get(matrix_id, 0))
        state_counts["MEASURED_SCALAR"] += multiplier * int((state == MEASURED_SCALAR).sum())
        state_counts["STRUCTURALLY_UNMEASURED"] += multiplier * int((state == STRUCTURALLY_UNMEASURED).sum())
        state_counts["MEASURED_COLLISION_UNRESOLVED"] += multiplier * int((state == MEASURED_COLLISION_UNRESOLVED).sum())

    mask_audit = audit_masks(
        loader, cohort, seed=args.seed, chunk_size=args.mask_audit_chunk
    )
    if mask_audit["illegal_hidden_count"] or not mask_audit["exact_hidden_count_all_rows"]:
        raise RuntimeError("mask legality/exact-count failure")

    raw_candidates = [int(item) for item in args.microbatch_candidates.split(",")]
    candidates = [
        item for item in raw_candidates if item > 0 and args.effective_batch % item == 0
    ]
    if not candidates or candidates[-1] != 1:
        raise ValueError("microbatch candidates must provide a valid path ending in 1")
    calibration = []
    chosen = None
    components = None
    sampler = None
    first_result = None
    for microbatch in candidates:
        if device.type == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats(device)
        candidate_start = time.perf_counter()
        try:
            trial_components = build_components(args.seed, device)
            trial_sampler = torch.Generator(device="cpu").manual_seed(args.seed + 700_001)
            result = run_update(
                loader=loader,
                cohort=cohort,
                sampler=trial_sampler,
                cursor=0,
                seed=args.seed,
                microbatch=microbatch,
                effective_batch=args.effective_batch,
                device=device,
                online=trial_components[0],
                target=trial_components[1],
                predictor=trial_components[2],
                optimizer=trial_components[3],
                scaler=trial_components[4],
                controller=trial_components[5],
            )
            reserved = (
                int(torch.cuda.max_memory_reserved(device)) if device.type == "cuda" else 0
            )
            safe = device.type != "cuda" or reserved <= int(args.vram_safety_gib * (1024**3))
            calibration.append(
                {
                    "microbatch": microbatch,
                    "status": "PASS" if safe else "OVER_SAFETY_MARGIN",
                    "peak_reserved_bytes": reserved,
                    "seconds": time.perf_counter() - candidate_start,
                }
            )
            if safe:
                chosen = microbatch
                components = trial_components
                sampler = trial_sampler
                first_result = result
                break
            del trial_components, trial_sampler, result
        except torch.OutOfMemoryError as error:
            calibration.append(
                {
                    "microbatch": microbatch,
                    "status": "CUDA_OOM",
                    "error": str(error),
                    "seconds": time.perf_counter() - candidate_start,
                }
            )
        finally:
            gc.collect()
            if device.type == "cuda" and chosen is None:
                torch.cuda.empty_cache()
    if chosen is None or components is None or sampler is None or first_result is None:
        raise RuntimeError("Phase E mechanically blocked: microbatch 1 did not pass")

    online, target, predictor, optimizer, scaler, controller = components
    update_results = [first_result]
    for cursor in range(1, args.steps):
        update_results.append(
            run_update(
                loader=loader,
                cohort=cohort,
                sampler=sampler,
                cursor=cursor,
                seed=args.seed,
                microbatch=chosen,
                effective_batch=args.effective_batch,
                device=device,
                online=online,
                target=target,
                predictor=predictor,
                optimizer=optimizer,
                scaler=scaler,
                controller=controller,
            )
        )
    if not all(item["step_succeeded"] for item in update_results):
        raise RuntimeError("GradScaler skipped a finite Phase-E update")
    if not all(item["online_moved"] and item["ema_equation"]["equal"] for item in update_results):
        raise RuntimeError("optimizer movement or exact full-state EMA equation failed")
    if controller.global_update_step != args.steps or controller.ema_update_count != args.steps:
        raise RuntimeError("optimizer/EMA counter mismatch")

    optimizer.zero_grad(set_to_none=True)
    checkpoint = capture_synthetic_checkpoint(
        online_encoder=online,
        target_encoder=target,
        predictor=predictor,
        optimizer=optimizer,
        global_update_step=controller.global_update_step,
        ema_update_count=controller.ema_update_count,
        accumulation_position=0,
        masking_generator=sampler,
    )
    checkpoint.update(
        {
            "schema": "prod41k-phase-e-restart-v1",
            "scaler": scaler.state_dict(),
            "schedule_cursor": args.steps,
            "cohort_manifest_sha256": sha256(EXPORT / "phase_e_foundation_train_cohort_manifest.csv"),
            "microbatch": chosen,
            "effective_batch": args.effective_batch,
        }
    )
    checkpoint_path = EXPORT / "phase_e_restart_checkpoint.pt"
    write_start = time.perf_counter()
    torch.save(checkpoint, checkpoint_path)
    checkpoint_write_seconds = time.perf_counter() - write_start
    checkpoint_hash = sha256(checkpoint_path)

    branch_a = run_update(
        loader=loader,
        cohort=cohort,
        sampler=sampler,
        cursor=args.steps,
        seed=args.seed,
        microbatch=chosen,
        effective_batch=args.effective_batch,
        device=device,
        online=online,
        target=target,
        predictor=predictor,
        optimizer=optimizer,
        scaler=scaler,
        controller=controller,
    )
    a_online = state_snapshot(online)
    a_target = state_snapshot(target)
    a_predictor = state_snapshot(predictor)
    a_optimizer = optimizer.state_dict()
    a_scaler = scaler.state_dict()
    a_counters = (controller.global_update_step, controller.ema_update_count)

    fresh = build_components(args.seed + 99, device)
    online_b, target_b, predictor_b, optimizer_b, scaler_b, controller_b = fresh
    sampler_b = torch.Generator(device="cpu").manual_seed(1)
    read_start = time.perf_counter()
    loaded = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    checkpoint_read_seconds = time.perf_counter() - read_start
    counters = restore_synthetic_checkpoint(
        loaded,
        online_encoder=online_b,
        target_encoder=target_b,
        predictor=predictor_b,
        optimizer=optimizer_b,
        masking_generator=sampler_b,
    )
    scaler_b.load_state_dict(loaded["scaler"])
    controller_b.load_bookkeeping(
        global_update_step=counters["global_update_step"],
        ema_update_count=counters["ema_update_count"],
    )
    if counters["accumulation_position"] != 0 or loaded["schedule_cursor"] != args.steps:
        raise RuntimeError("checkpoint schedule/cursor mismatch")
    branch_b = run_update(
        loader=loader,
        cohort=cohort,
        sampler=sampler_b,
        cursor=loaded["schedule_cursor"],
        seed=args.seed,
        microbatch=loaded["microbatch"],
        effective_batch=loaded["effective_batch"],
        device=device,
        online=online_b,
        target=target_b,
        predictor=predictor_b,
        optimizer=optimizer_b,
        scaler=scaler_b,
        controller=controller_b,
    )
    restart = {
        "selected_ids_equal": branch_a["selected_ids"] == branch_b["selected_ids"],
        "masks_bitwise_equal": all(
            torch.equal(a, b) for a, b in zip(branch_a["masks"], branch_b["masks"])
        ),
        "mask_hashes_equal": branch_a["mask_hashes"] == branch_b["mask_hashes"],
        "pre_step_loss_bitwise_equal": branch_a["loss"] == branch_b["loss"],
        "step_outcome_equal": branch_a["step_succeeded"] == branch_b["step_succeeded"],
        "online_state": compare_tensor_dicts(a_online, online_b.state_dict()),
        "target_state": compare_tensor_dicts(a_target, target_b.state_dict()),
        "predictor_state": compare_tensor_dicts(a_predictor, predictor_b.state_dict()),
        "optimizer_state_equal": nested_equal(a_optimizer, optimizer_b.state_dict()),
        "scaler_state_equal": nested_equal(a_scaler, scaler_b.state_dict()),
        "controller_counters_equal": a_counters
        == (controller_b.global_update_step, controller_b.ema_update_count),
    }

    optimizer_b.zero_grad(set_to_none=True)
    skipped_online_before = state_snapshot(online_b)
    skipped_target_before = state_snapshot(target_b)
    skipped_predictor_before = state_snapshot(predictor_b)
    skipped_counters_before = (controller_b.global_update_step, controller_b.ema_update_count)
    for parameter in list(online_b.parameters()) + list(predictor_b.parameters()):
        parameter.grad = torch.zeros_like(parameter)
    next(online_b.parameters()).grad.flatten()[0] = float("inf")
    skipped_scale_before = float(scaler_b.get_scale())
    scaler_b.step(optimizer_b)
    scaler_b.update()
    skipped = float(scaler_b.get_scale()) < skipped_scale_before
    skipped_check = {
        "scaler_reported_skip": skipped,
        "online_immobile": compare_tensor_dicts(skipped_online_before, online_b.state_dict())["equal"],
        "target_immobile": compare_tensor_dicts(skipped_target_before, target_b.state_dict())["equal"],
        "predictor_immobile": compare_tensor_dicts(skipped_predictor_before, predictor_b.state_dict())["equal"],
        "controller_immobile": skipped_counters_before
        == (controller_b.global_update_step, controller_b.ema_update_count),
    }
    optimizer_b.zero_grad(set_to_none=True)

    restart_pass = all(
        [
            restart["selected_ids_equal"],
            restart["masks_bitwise_equal"],
            restart["mask_hashes_equal"],
            restart["pre_step_loss_bitwise_equal"],
            restart["step_outcome_equal"],
            restart["online_state"]["equal"],
            restart["target_state"]["equal"],
            restart["predictor_state"]["equal"],
            restart["optimizer_state_equal"],
            restart["scaler_state_equal"],
            restart["controller_counters_equal"],
        ]
    )
    skipped_pass = all(skipped_check.values())
    checks = {
        "namespace": True,
        "foundation_train_firewall": True,
        "observation_contract": True,
        "mask_legality_and_exact_count": True,
        "finite_complete_gradient_paths": True,
        "online_parameter_movement": True,
        "full_state_post_step_ema_equation": True,
        "ema_zero_gradient": True,
        "optimizer_ema_counter_equality": True,
        "disk_restart_exact": restart_pass,
        "skipped_step_immobility": skipped_pass,
        "vram_safety": True,
    }
    verdict = "PASS" if all(checks.values()) else "FAIL"
    peak_allocated = int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else 0
    peak_reserved = int(torch.cuda.max_memory_reserved(device)) if device.type == "cuda" else 0
    telemetry = {
        "device": str(device),
        "cuda_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "cohort_preparation_seconds": cohort_seconds,
        "mask_audit_seconds": mask_audit["seconds"],
        "checkpoint_write_seconds": checkpoint_write_seconds,
        "checkpoint_read_seconds": checkpoint_read_seconds,
        "checkpoint_bytes": checkpoint_path.stat().st_size,
        "checkpoint_sha256": checkpoint_hash,
        "host_rss_bytes_at_report": host_rss_bytes(),
        "peak_cuda_allocated_bytes": peak_allocated,
        "peak_cuda_reserved_bytes": peak_reserved,
        "successful_unique_cell_presentations": args.steps * args.effective_batch,
        "successful_view_presentations": args.steps * args.effective_batch * VIEWS,
        "successful_optimizer_updates": args.steps,
        "wall_seconds": time.perf_counter() - wall_start,
        "chosen_microbatch": chosen,
        "effective_batch": args.effective_batch,
        "calibration": calibration,
        "updates": [
            {key: value for key, value in item.items() if key not in {"masks"}}
            for item in update_results
        ],
    }
    evidence = {
        "schema": "prod41k-phase-e-engineering-smoke-v2",
        "verdict": verdict,
        "claim_scope": "engineering feasibility only; no biological qualification or T1 authorization",
        "checks": checks,
        "cohort": {
            "cells": int(len(cohort)),
            "donors": int(cohort.canonical_donor_id.nunique()),
            "operators": int(cohort.operator_index.nunique()),
            "sources": source_summary.to_dict(orient="records"),
            "manifest_sha256": sha256(EXPORT / "phase_e_foundation_train_cohort_manifest.csv"),
        },
        "namespace": {
            "addresses": VOCABULARY_SIZE,
            "scalar_observable": scalar_observable,
            "collision_only": collision_only,
            "physical_state_counts_over_cells": state_counts,
        },
        "mask_audit": mask_audit,
        "restart": restart,
        "skipped_step": skipped_check,
        "telemetry": telemetry,
        "hashes": {
            "smoke_script": sha256(Path(__file__)),
            "current_ipb": sha256(ROOT / "src/sea_ad_jepa/v4/ipb_jepa.py"),
            "ema": sha256(ROOT / "src/sea_ad_jepa/v4/ema.py"),
            "masking": sha256(ROOT / "src/sea_ad_jepa/v4/masking.py"),
            "production_loader": sha256(ROOT / "exports/static_context_decomposition_v4_20260821/production_train_loader.py"),
            "frozen_sampler_source": sha256(FROZEN_SAMPLER_SOURCE),
        },
    }
    evidence_path = EXPORT / "phase_e_engineering_evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    report = f"""# Phase E engineering smoke report

**Verdict:** `{verdict}`  
**Scope:** engineering feasibility only. This report does not qualify biology and does not authorize or auto-start Phase T1.

- Complete cohort: {len(cohort):,} FOUNDATION TRAIN cells, {cohort.canonical_donor_id.nunique()} donors, {cohort.operator_index.nunique()} operators; zero DEV/SEALED overlap.
- Namespace: {VOCABULARY_SIZE:,} addresses; {scalar_observable:,} scalar-observable; {collision_only:,} collision-only.
- Four views: exact-count lawful masks; all six overlap distributions are in `phase_e_mask_pair_stats.csv`; four-distinct fraction {mask_audit['four_distinct_fraction']:.6f}.
- Optimization: {args.steps} successful updates; full active gradient paths; exact full-state post-step EMA equation; optimizer/EMA counters agree.
- Compute: microbatch {chosen}, effective batch {args.effective_batch}, peak CUDA reserved {peak_reserved / (1024**3):.3f} GiB, wall {telemetry['wall_seconds']:.1f} s.
- Restart: disk-loaded fresh-object real-next-update equivalence `{restart_pass}`; checkpoint `{checkpoint_hash}`.
- Skipped AMP step: scaler skip observed and online/predictor/EMA/controller immobility `{skipped_pass}`.

Detailed machine-readable evidence: `phase_e_engineering_evidence.json`.
No T1 action was taken.
"""
    (EXPORT / "ENGINEERING_SMOKE_REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps({"verdict": verdict, "report": str(EXPORT / "ENGINEERING_SMOKE_REPORT.md")}, indent=2))
    if verdict != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
