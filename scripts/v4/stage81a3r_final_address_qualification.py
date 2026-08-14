"""Run the provisional synthetic-only Stage81A3R final-address qualification."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
import torch
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sea_ad_jepa.v4.a3r_qualification import (
    CapacityFixture,
    anti_topk_fixture,
    centered_normalized_linear_kernels,
    contextual_distance,
    donor_split,
    generate_capacity_fixture,
    kernel_factor_scores,
    normalize_counts,
    rare_scores,
)
from sea_ad_jepa.v4.ema import create_ema_target, update_ema_target
from sea_ad_jepa.v4.ipb_jepa import (
    BlockPredictor,
    GeneAnchorDecoder,
    IPBEncoder,
    TargetBlocks,
    block_jepa_loss,
    gather_block_states,
    gene_anchor_loss,
    hidden_gene_indices,
    sample_target_blocks,
    sample_uniform_target_blocks,
)
from sea_ad_jepa.v4.successor_candidate import oracle_module_graph

EXPECTED_A2R_HASH = "5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff"
STATUS = "PROVISIONAL - SYNTHETIC ONLY - NOT FROZEN"


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def atomic_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="") as handle:
        temporary = Path(handle.name)
    frame.to_csv(temporary, index=False, lineterminator="\n")
    os.replace(temporary, path)


def load_frozen_contract(project: Path, config: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    inputs = config["inputs"]
    registry_path = project / inputs["registry"]
    support_path = project / inputs["measurement_support"]
    audit_path = project / inputs["injectivity_audit"]
    registry = pd.read_csv(registry_path)
    support = pd.read_csv(support_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    classes = registry.identity_class.value_counts().to_dict()
    assertions = {
        "status": STATUS,
        "registry_rows": len(registry),
        "address_ids_unique": not registry.molecular_address_id.duplicated().any(),
        "address_indices_unique": not registry.molecular_address_index.duplicated().any(),
        "address_indices_contiguous": registry.molecular_address_index.tolist() == list(range(len(registry))),
        "identity_classes": {key: int(value) for key, value in classes.items()},
        "measurement_operators": int(support.matrix_id.nunique()),
        "matrix_address_rows": len(support),
        "one_row_per_matrix_address": not support.duplicated(["matrix_id", "molecular_address_id"]).any(),
        "measured_zero_distinct_from_structurally_unmeasured": bool(support.measured_zero_distinct_from_unmeasured.all()),
        "semantic_hash": audit["registry_semantic_hash"],
        "future_only_addresses": int(audit["future_only_addresses"]),
    }
    expected = config["frozen_contract"]
    checks = [
        len(registry) == expected["addresses"],
        classes == expected["identity_classes"],
        assertions["address_ids_unique"], assertions["address_indices_unique"], assertions["address_indices_contiguous"],
        assertions["measurement_operators"] == expected["measurement_operators"],
        len(support) == expected["matrix_address_rows"], assertions["one_row_per_matrix_address"],
        assertions["measured_zero_distinct_from_structurally_unmeasured"],
        assertions["semantic_hash"] == EXPECTED_A2R_HASH, assertions["future_only_addresses"] == 0,
    ]
    if not all(checks):
        raise RuntimeError(f"frozen Stage81A2R contract drift: {assertions}")
    return registry, support, assertions


def representative_support_profiles(support: pd.DataFrame, genes: int) -> tuple[list[torch.Tensor], list[dict]]:
    counts = support.groupby("matrix_id", sort=True).measured_address.sum().sort_values()
    distinct_counts = np.sort(counts.unique())
    positions = {
        "lower_support": int(distinct_counts[0]),
        "medium_support": int(distinct_counts[len(distinct_counts) // 2]),
        "high_support": int(distinct_counts[-1]),
    }
    profiles = []
    summaries = []
    for label, measured_count in positions.items():
        matrix_id = counts.loc[counts.eq(measured_count)].index[0]
        subset = support.loc[support.matrix_id.eq(matrix_id), ["molecular_address_index", "measured_address"]]
        mask = torch.zeros(genes, dtype=torch.bool)
        indices = subset.loc[subset.measured_address, "molecular_address_index"].to_numpy(dtype=np.int64)
        mask[torch.from_numpy(indices)] = True
        profiles.append(mask)
        summaries.append({"support_class": label, "matrix_id": matrix_id, "measured_addresses": int(mask.sum())})
    return profiles, summaries


def build_components(genes: int, width: int, config: dict, device: torch.device):
    architecture = config["architecture"]
    online = IPBEncoder(
        vocabulary_size=genes, width=width, heads=architecture["heads"],
        blocks=architecture["blocks"], ffn_width=architecture["ffn_width"],
        dropout=0.0, gradient_checkpointing=architecture["gradient_checkpointing"],
    ).to(device)
    target = create_ema_target(online).to(device)
    predictor = BlockPredictor(width=width, heads=architecture["heads"]).to(device)
    decoder = GeneAnchorDecoder(width=width).to(device)
    return online, target, predictor, decoder


def one_training_step(
    online: IPBEncoder,
    target: IPBEncoder,
    predictor: BlockPredictor,
    decoder: GeneAnchorDecoder,
    optimizer: torch.optim.Optimizer,
    expression: torch.Tensor,
    measured: torch.Tensor,
    blocks: TargetBlocks,
    gene_ids: torch.Tensor,
    ema: float,
) -> dict[str, Any]:
    device = expression.device
    optimizer.zero_grad(set_to_none=True)
    if device.type == "cuda":
        torch.cuda.synchronize()
    total_start = time.perf_counter()
    forward_start = time.perf_counter()
    with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == "cuda"):
        student = online(gene_ids, expression, measured, blocks.hidden_mask, "student")
        with torch.no_grad():
            teacher = target(gene_ids, expression, measured, torch.zeros_like(measured), "target")
        teacher_blocks = gather_block_states(teacher.gene_states, blocks)
        predicted = predictor(
            online.tokenizer.gene_identity, blocks, student.gene_states,
            student.cell_state, measured & ~blocks.hidden_mask,
        )
        hidden_ids = hidden_gene_indices(blocks.hidden_mask)
        value_hat, detection_hat = decoder(student.cell_state, online.tokenizer.gene_identity, hidden_ids)
        rows = torch.arange(len(expression), device=device)[:, None]
        anchor = gene_anchor_loss(
            value_hat, detection_hat, expression[rows, hidden_ids], expression[rows, hidden_ids] > 0,
        )
        jepa = block_jepa_loss(predicted, teacher_blocks)
        loss = jepa + anchor["gene"]
    if device.type == "cuda":
        torch.cuda.synchronize()
    forward_seconds = time.perf_counter() - forward_start
    backward_start = time.perf_counter()
    loss.backward()
    if device.type == "cuda":
        torch.cuda.synchronize()
    backward_seconds = time.perf_counter() - backward_start
    gradient = torch.sqrt(sum(
        (parameter.grad.float().square().sum() for parameter in online.parameters() if parameter.grad is not None),
        torch.tensor(0.0, device=device),
    ))
    optimizer_start = time.perf_counter()
    optimizer.step()
    update = update_ema_target(online, target, momentum=ema)
    if device.type == "cuda":
        torch.cuda.synchronize()
    optimizer_seconds = time.perf_counter() - optimizer_start
    return {
        "total_loss": float(loss.detach()), "jepa_loss": float(jepa.detach()),
        "gene_anchor_loss": float(anchor["gene"].detach()), "gradient_norm": float(gradient),
        "minimum_linear_attention_denominator": float(student.minimum_denominator.detach()),
        "forward_seconds": forward_seconds, "backward_seconds": backward_seconds,
        "optimizer_ema_seconds": optimizer_seconds, "total_step_seconds": time.perf_counter() - total_start,
        "finite": bool(torch.isfinite(loss) and torch.isfinite(student.gene_states).all()),
        "optimizer_state_created": bool(optimizer.state), "ema_success": update.parameter_count > 0,
    }


def mechanics_probe(
    genes: int,
    microbatch: int,
    profiles: list[torch.Tensor],
    config: dict,
) -> dict[str, Any]:
    device = torch.device("cuda")
    torch.manual_seed(814000 + microbatch)
    torch.cuda.manual_seed_all(814000 + microbatch)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    result: dict[str, Any] = {"microbatch": microbatch, "status": STATUS}
    try:
        online, target, predictor, decoder = build_components(genes, 160, config, device)
        online.train(); predictor.train(); decoder.train()
        optimizer = torch.optim.AdamW(
            list(online.parameters()) + list(predictor.parameters()) + list(decoder.parameters()), lr=1e-4,
        )
        probe_profile = {1: 0, 8: 1, 16: 2}.get(microbatch, 1)
        measured = profiles[probe_profile].unsqueeze(0).expand(microbatch, -1).to(device)
        result["support_profile_index"] = probe_profile
        generator = torch.Generator(device=device).manual_seed(814100 + microbatch)
        expression = torch.rand((microbatch, genes), generator=generator, device=device)
        expression = expression.masked_fill(~measured, 0.0)
        expression[measured & (torch.rand((microbatch, genes), generator=generator, device=device) < 0.20)] = 0.0
        ids = torch.arange(genes, device=device).expand(microbatch, -1)
        records = []
        for step in range(config["mechanics"]["optimizer_steps"]):
            blocks = sample_uniform_target_blocks(
                measured, production_seed=814201, cell_indices=torch.arange(microbatch, device=device),
                sample_pass=step, view_index=0, mask_fraction=0.40, block_count=16,
            )
            records.append(one_training_step(
                online, target, predictor, decoder, optimizer, expression, measured, blocks, ids,
                config["training"]["ema_momentum"],
            ))
        result.update(
            steps=records, optimizer_steps_completed=len(records),
            peak_cuda_allocated_bytes=int(torch.cuda.max_memory_allocated()),
            peak_cuda_reserved_bytes=int(torch.cuda.max_memory_reserved()),
            finite=all(item["finite"] for item in records),
            optimizer_state_created=all(item["optimizer_state_created"] for item in records),
            ema_success=all(item["ema_success"] for item in records),
            classification="FULL 41,238-ADDRESS MECHANICALLY FEASIBLE",
        )
    except torch.cuda.OutOfMemoryError as exc:
        result.update(
            classification="ENGINEERING LIMITATION", error=f"{type(exc).__name__}: {exc}",
            peak_cuda_allocated_bytes=int(torch.cuda.max_memory_allocated()),
            peak_cuda_reserved_bytes=int(torch.cuda.max_memory_reserved()), optimizer_steps_completed=0,
        )
    finally:
        for name in ("online", "target", "predictor", "decoder", "optimizer"):
            if name in locals():
                del locals()[name]
        torch.cuda.empty_cache()
    return result


def encode_context(
    model: IPBEncoder,
    expression: np.ndarray,
    support: np.ndarray,
    *,
    batch_size: int,
    device: torch.device,
) -> torch.Tensor:
    model.eval()
    outputs = []
    with torch.no_grad():
        for start in range(0, len(expression), batch_size):
            stop = min(start + batch_size, len(expression))
            values = torch.from_numpy(expression[start:stop]).to(device)
            measured = torch.from_numpy(support[start:stop]).to(device)
            ids = torch.arange(expression.shape[1], device=device).expand(stop - start, -1)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == "cuda"):
                states = model(ids, values, measured, torch.zeros_like(measured), "target").gene_states
            outputs.append(states.to(dtype=torch.float16, device="cpu"))
    model.train()
    return torch.cat(outputs)


def evaluate_context(
    model: IPBEncoder,
    fixture: CapacityFixture,
    *,
    checkpoint: int,
    width: int,
    masker: str,
    config: dict,
) -> tuple[list[dict], dict, torch.Tensor]:
    device = next(model.parameters()).device
    support = np.ones_like(fixture.counts, dtype=bool)
    states = encode_context(
        model, fixture.normalized, support,
        batch_size=config["training"]["evaluation_microbatch"], device=device,
    )
    train, test = donor_split(fixture.donors)
    h_train = states[train].to(device)
    h_test = states[test].to(device)
    k_h_train, k_h_test = centered_normalized_linear_kernels(h_train, h_test)
    del h_train, h_test
    x_train = torch.from_numpy(fixture.normalized[train]).to(device)
    x_test = torch.from_numpy(fixture.normalized[test]).to(device)
    k_x_train, k_x_test = centered_normalized_linear_kernels(x_train, x_test)
    del x_train, x_test
    raw = kernel_factor_scores(k_x_train, k_x_test, fixture.factors[train], fixture.factors[test])
    learned = kernel_factor_scores(k_h_train, k_h_test, fixture.factors[train], fixture.factors[test])
    raw_auroc, raw_ap = rare_scores(k_x_train, k_x_test, fixture.rare_mask[train], fixture.rare_mask[test])
    h_auroc, h_ap = rare_scores(k_h_train, k_h_test, fixture.rare_mask[train], fixture.rare_mask[test])
    rows = []
    for index, (name, family) in enumerate(zip(fixture.factor_names, fixture.factor_families)):
        rows.append({
            "status": STATUS, "fixture": fixture.name, "masker": masker, "d_gene": width,
            "checkpoint": checkpoint, "factor": name, "factor_family": family,
            "raw_r2": float(raw[index]), "learned_h_r2": float(learned[index]),
            "h_minus_raw_r2": float(learned[index] - raw[index]),
            "raw_recoverable": bool(raw[index] >= config["capacity_gate"]["raw_recoverable_r2"]),
            "full_h_frobenius_kernel": True, "mean_pool_used": False, "raw_x_concatenated_to_h": False,
        })
    rare = {
        "status": STATUS, "fixture": fixture.name, "masker": masker, "d_gene": width,
        "checkpoint": checkpoint, "raw_rare_auroc": raw_auroc, "raw_rare_ap": raw_ap,
        "learned_h_rare_auroc": h_auroc, "learned_h_rare_ap": h_ap,
    }
    torch.cuda.empty_cache()
    return rows, rare, states


def train_fixture(
    fixture: CapacityFixture,
    *,
    masker: str,
    width: int,
    config: dict,
) -> tuple[list[dict], list[dict], dict[str, torch.Tensor], torch.Tensor]:
    device = torch.device("cuda")
    seed = config["training"]["seed"]
    torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    online, target, predictor, decoder = build_components(fixture.normalized.shape[1], width, config, device)
    online.train(); predictor.train(); decoder.train()
    initial_state = copy.deepcopy(online.state_dict())
    optimizer = torch.optim.AdamW(
        list(online.parameters()) + list(predictor.parameters()) + list(decoder.parameters()),
        lr=config["training"]["learning_rate"],
    )
    train, _ = donor_split(fixture.donors)
    expression = torch.from_numpy(fixture.normalized)
    measured_cpu = torch.ones_like(expression, dtype=torch.bool)
    graph = oracle_module_graph(fixture.module_ids) if masker == "oracle" else None
    checkpoints = set(config["training"]["checkpoints"])
    metrics = []
    rare_rows = []
    rows, rare, _ = evaluate_context(online, fixture, checkpoint=0, width=width, masker=masker, config=config)
    metrics.extend(rows); rare_rows.append(rare)
    generator = torch.Generator(device="cpu").manual_seed(seed + 1)
    order = torch.tensor(train)[torch.randperm(len(train), generator=generator)]
    cursor = 0
    loss_trace = []
    for step in range(1, config["training"]["max_steps"] + 1):
        batch_size = config["training"]["microbatch"]
        if cursor + batch_size > len(order):
            order = torch.tensor(train)[torch.randperm(len(train), generator=generator)]
            cursor = 0
        selected = order[cursor:cursor + batch_size]
        cursor += batch_size
        values = expression[selected].to(device)
        measured = measured_cpu[selected].to(device)
        ids = torch.arange(fixture.normalized.shape[1], device=device).expand(len(selected), -1)
        if masker == "oracle":
            blocks = sample_target_blocks(
                measured, graph, production_seed=seed, cell_indices=selected.to(device),
                sample_pass=step, view_index=0, mask_fraction=0.40, block_count=16,
            )
        else:
            blocks = sample_uniform_target_blocks(
                measured, production_seed=seed, cell_indices=selected.to(device),
                sample_pass=step, view_index=0, mask_fraction=0.40, block_count=16,
            )
        record = one_training_step(
            online, target, predictor, decoder, optimizer, values, measured, blocks, ids,
            config["training"]["ema_momentum"],
        )
        record.update(step=step, fixture=fixture.name, masker=masker, d_gene=width)
        loss_trace.append(record)
        if not record["finite"]:
            raise RuntimeError(f"nonfinite training at {fixture.name}/{masker}/step={step}")
        if step in checkpoints:
            rows, rare, _ = evaluate_context(online, fixture, checkpoint=step, width=width, masker=masker, config=config)
            metrics.extend(rows); rare_rows.append(rare)
            print(f"{fixture.name}/{masker}/d{width}: checkpoint {step} evaluated", flush=True)
    final_states = encode_context(
        online, fixture.normalized, np.ones_like(fixture.counts, dtype=bool),
        batch_size=config["training"]["evaluation_microbatch"], device=device,
    )
    state = {key: value.detach().cpu() for key, value in online.state_dict().items()}
    state["__initial_parameter_checksum__"] = sum(
        value.float().sum() for value in initial_state.values()
    ).detach().cpu()
    del online, target, predictor, decoder, optimizer
    torch.cuda.empty_cache()
    return metrics, rare_rows, state, final_states


def capacity_gate(rows: list[dict], config: dict, *, width: int = 160, masker: str = "oracle") -> dict:
    final = pd.DataFrame(rows)
    final = final.loc[(final.d_gene == width) & (final.masker == masker) & (final.checkpoint == 256)]
    losses = final.loc[
        final.raw_recoverable & (final.learned_h_r2 < final.raw_r2 - config["capacity_gate"]["loss_r2"])
    ]
    replicated = []
    for family in sorted(losses.factor_family.unique()):
        fixtures = sorted(losses.loc[losses.factor_family.eq(family), "fixture"].unique())
        if len(fixtures) == len(config["fixtures"]):
            replicated.append(family)
    fired = bool(replicated)
    return {
        "status": STATUS, "width_160_gate_fired": fired,
        "replicated_loss_families": replicated,
        "training_healthy_and_finite": True,
        "failure_concerns_h_itself": fired,
        "classification": "CONTEXTUAL CAPACITY CONCERN AT 160 - WIDTH 256 COMPARISON AUTHORIZED" if fired else "KEEP d_gene=160 PROVISIONAL",
    }


def reload_model(state: dict[str, torch.Tensor], genes: int, width: int, config: dict) -> IPBEncoder:
    device = torch.device("cuda")
    architecture = config["architecture"]
    model = IPBEncoder(
        vocabulary_size=genes, width=width, heads=architecture["heads"],
        blocks=architecture["blocks"], ffn_width=architecture["ffn_width"],
        dropout=0.0, gradient_checkpointing=architecture["gradient_checkpointing"],
    ).to(device)
    clean = {key: value for key, value in state.items() if not key.startswith("__")}
    model.load_state_dict(clean)
    return model.eval()


def operator_audit(
    fixture: CapacityFixture,
    state: dict[str, torch.Tensor],
    config: dict,
) -> tuple[list[dict], dict]:
    model = reload_model(state, fixture.normalized.shape[1], 160, config)
    device = torch.device("cuda")
    train, test = donor_split(fixture.donors)
    rows = []
    states_by_operator = {}
    support_by_operator = {}
    rng = np.random.default_rng(config["operator"]["seed"])
    for label, fraction, depth in config["operator"]["profiles"]:
        panel = np.zeros(fixture.normalized.shape[1], dtype=bool)
        panel[rng.choice(len(panel), size=int(math.floor(fraction * len(panel))), replace=False)] = True
        support = np.broadcast_to(panel, fixture.counts.shape).copy()
        rate = fixture.rates / fixture.rates.sum(1, keepdims=True) * depth
        counts = rng.poisson(rate).astype(np.float32)
        normalized = normalize_counts(counts, support)
        states = encode_context(model, normalized, support, batch_size=config["training"]["evaluation_microbatch"], device=device)
        states_by_operator[label] = states
        support_by_operator[label] = support
        k_h_train, k_h_test = centered_normalized_linear_kernels(states[train].to(device), states[test].to(device))
        k_x_train, k_x_test = centered_normalized_linear_kernels(
            torch.from_numpy(normalized[train]).to(device), torch.from_numpy(normalized[test]).to(device),
        )
        h_scores = kernel_factor_scores(k_h_train, k_h_test, fixture.factors[train], fixture.factors[test])
        raw_scores = kernel_factor_scores(k_x_train, k_x_test, fixture.factors[train], fixture.factors[test])
        for index, (name, family) in enumerate(zip(fixture.factor_names, fixture.factor_families)):
            if raw_scores[index] < 0.20:
                classification = "DATA / OPERATOR LIMITATION"
            elif h_scores[index] < raw_scores[index] - 0.10:
                classification = "CONTEXTUAL REPRESENTATION CONCERN"
            else:
                classification = "MEASUREMENT-AWARE TRANSFER SUPPORTED"
            rows.append({
                "status": STATUS, "fixture": fixture.name, "operator": label,
                "support_fraction": fraction, "depth": depth, "factor": name,
                "factor_family": family, "raw_panel_r2": float(raw_scores[index]),
                "learned_h_r2": float(h_scores[index]), "h_minus_raw_panel_r2": float(h_scores[index] - raw_scores[index]),
                "classification": classification,
            })
    comparisons = []
    labels = [item[0] for item in config["operator"]["profiles"]]
    for left, right in zip(labels[:-1], labels[1:]):
        joint = torch.from_numpy(support_by_operator[left] & support_by_operator[right])
        distances = contextual_distance(states_by_operator[left], states_by_operator[right], joint)
        comparisons.append({"operators": f"{left}_vs_{right}", "median_joint_measured_h_distance": float(np.median(distances))})
    del model
    torch.cuda.empty_cache()
    summary = {"status": STATUS, "fixture": fixture.name, "operator_ids_supplied_to_encoder": False, "jointly_measured_comparisons": comparisons}
    return rows, summary


def uncertainty_audit(
    fixture: CapacityFixture,
    state: dict[str, torch.Tensor],
    config: dict,
) -> tuple[list[dict], dict]:
    model = reload_model(state, fixture.normalized.shape[1], 160, config)
    device = torch.device("cuda")
    genes = fixture.normalized.shape[1]
    full_support = np.ones_like(fixture.counts, dtype=bool)
    reference = encode_context(model, fixture.normalized, full_support, batch_size=config["training"]["evaluation_microbatch"], device=device)
    informative = np.flatnonzero(fixture.factor_gene_mask.any(0))
    background = np.flatnonzero(~fixture.factor_gene_mask.any(0))
    rng = np.random.default_rng(config["uncertainty"]["seed"])
    ordering = np.concatenate((rng.permutation(informative), rng.permutation(background)))
    rows = []
    bio_medians = []
    for fraction in config["uncertainty"]["biology_fractions"]:
        panel = np.zeros(genes, dtype=bool); panel[ordering[:int(math.floor(fraction * genes))]] = True
        support = np.broadcast_to(panel, fixture.counts.shape).copy()
        candidate = encode_context(model, fixture.normalized, support, batch_size=config["training"]["evaluation_microbatch"], device=device)
        distance = contextual_distance(candidate, reference, torch.from_numpy(support))
        bio_medians.append(float(np.median(distance)))
        rows.append({"status": STATUS, "fixture": fixture.name, "uncertainty": "U_BIO", "level": fraction, "median_distance": bio_medians[-1], "mean_distance": float(distance.mean())})
    meas_medians = []
    for quality in config["uncertainty"]["measurement_quality"]:
        rate = fixture.rates / fixture.rates.sum(1, keepdims=True) * (quality * config["uncertainty"]["reference_depth"])
        counts = rng.poisson(rate).astype(np.float32)
        normalized = normalize_counts(counts, full_support)
        candidate = encode_context(model, normalized, full_support, batch_size=config["training"]["evaluation_microbatch"], device=device)
        distance = contextual_distance(candidate, reference, torch.from_numpy(full_support))
        meas_medians.append(float(np.median(distance)))
        rows.append({"status": STATUS, "fixture": fixture.name, "uncertainty": "U_MEAS", "level": quality, "median_distance": meas_medians[-1], "mean_distance": float(distance.mean())})
    bio_violations = sum(later > earlier + 1e-8 for earlier, later in zip(bio_medians, bio_medians[1:]))
    meas_violations = sum(later > earlier + 1e-8 for earlier, later in zip(meas_medians, meas_medians[1:]))
    low_bio_high_measurement = bio_medians[0]
    high_bio_low_measurement = meas_medians[0]
    high_bio_high_measurement = max(bio_medians[-1], meas_medians[-1])
    separable = bio_violations == 0 and meas_violations == 0 and low_bio_high_measurement > high_bio_high_measurement and high_bio_low_measurement > high_bio_high_measurement
    summary = {
        "status": STATUS, "fixture": fixture.name,
        "u_bio_monotonicity_violations": bio_violations, "u_meas_monotonicity_violations": meas_violations,
        "low_biology_high_measurement_distance": low_bio_high_measurement,
        "high_biology_low_measurement_distance": high_bio_low_measurement,
        "high_biology_high_measurement_distance": high_bio_high_measurement,
        "classification": "U_BIO/U_MEAS OPERATIONALLY SEPARABLE" if separable else "SEPARATION NOT DEMONSTRATED",
        "combined_score_created": False,
    }
    del model
    torch.cuda.empty_cache()
    return rows, summary


def write_readout(path: Path, report: dict) -> None:
    mechanics = report["mechanics"]
    capacity = report["capacity_gate"]
    graph = report["graph_free"]
    operator = report["operator_summary"]
    uncertainty = report["uncertainty_summary"]
    anti = report["anti_top_k"]
    lines = [
        "# Stage81A3R Synthetic Closure Readout", "", f"**{STATUS}**", "",
        "## Frozen Contract", "",
        f"- Universal molecular addresses: **{report['a2r_contract']['registry_rows']:,}**.",
        f"- Semantic hash: `{report['a2r_contract']['semantic_hash']}` (unchanged).",
        f"- Measurement operators/rows: **{report['a2r_contract']['measurement_operators']} / {report['a2r_contract']['matrix_address_rows']:,}**.", "",
        "## Final-Address Mechanics", "",
    ]
    for probe in mechanics["probes"]:
        lines.append(f"- Microbatch {probe['microbatch']}: {probe['classification']}; peak allocated/reserved {probe.get('peak_cuda_allocated_bytes', 0) / 1024**3:.2f}/{probe.get('peak_cuda_reserved_bytes', 0) / 1024**3:.2f} GiB; steps {probe.get('optimizer_steps_completed', 0)}.")
    lines.extend(["", f"Classification: **{mechanics['classification']}**.", "", "## Contextual Capacity", "", f"- Width-256 gate fired: **{capacity['width_160_gate_fired']}**.", f"- Replicated loss families: `{capacity['replicated_loss_families']}`.", f"- Classification: **{capacity['classification']}**.", "", "The capacity audit used the centered normalized Frobenius kernel over full contextual gene states. It did not mean-pool `H`, substitute the CELL token, or concatenate raw expression into `H`.", "", "## Graph-Free Masking", "", f"- Pearson graph invoked: **{graph['pearson_graph_invoked']}**.", f"- Classification: **{graph['classification']}**.", "", "## Observation Operators", "", f"- Operator IDs supplied to encoder: **{operator['operator_ids_supplied_to_encoder']}**.", f"- Classification counts: `{operator['classification_counts']}`.", "", "## U_BIO / U_MEAS", "", f"- Classification: **{uncertainty['classification']}**.", f"- U_BIO monotonicity violations: **{uncertainty['u_bio_monotonicity_violations']}**; U_MEAS: **{uncertainty['u_meas_monotonicity_violations']}**.", f"- U_MEAS reference: {uncertainty['u_meas_reference_definition']}", f"- Level-1 interpretation: **{uncertainty['u_meas_level_1_interpretation']}**", "- Neither U_BIO nor U_MEAS is calibrated.", "", "## Anti-Top-K Regression", "", f"- Full rare AUROC/AP: **{anti['full_rare_auroc']:.3f}/{anti['full_rare_ap']:.3f}**.", f"- Top-4096 rare AUROC/AP: **{anti['topk_rare_auroc']:.3f}/{anti['topk_rare_ap']:.3f}**.", f"- Broad full/top-K R2: **{anti['full_broad_r2']:.3f}/{anti['topk_broad_r2']:.3f}**.", "- Permanent deterministic regression: **ENABLED**.", "", "## Governance", "", "- Real RNA expression accessed: **NO**.", "- DEV/SEALED RNA accessed: **NO/NO**.", "- Pathology accessed: **NO**.", "- Stage81B/Stage81C started: **NO/NO**.", "- Stage81A3 Freeze1 declared: **NO**.", "", "Final state: **STAGE81A3R_SYNTHETIC_CLOSURE_COMPLETE_NOT_FROZEN**", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a3r_final_address_qualification.yaml"))
    parser.add_argument("--skip-mechanics", action="store_true")
    parser.add_argument("--mechanics-only", action="store_true")
    args = parser.parse_args()
    project = args.project_dir.resolve()
    config = yaml.safe_load((project / args.config).read_text(encoding="utf-8"))
    outputs = {key: project / value for key, value in config["outputs"].items()}
    registry, support, contract = load_frozen_contract(project, config)
    if not torch.cuda.is_available():
        raise RuntimeError("Stage81A3R bounded probes require the established CUDA runtime")
    profiles, profile_summary = representative_support_profiles(support, len(registry))
    manifest = {
        "status": STATUS, "stage": config["stage_id"],
        "inputs": [
            {"role": role, "path": value, "sha256": sha256_file(project / value), "expression_values_accessed": False}
            for role, value in config["inputs"].items()
        ],
        "real_rna_expression_accessed": False, "dev_rna_accessed": False,
        "sealed_rna_accessed": False, "pathology_accessed": False,
        "dataset_or_matrix_id_supplied_to_encoder": False,
    }
    atomic_json(outputs["input_manifest"], manifest)

    mechanics = {"status": STATUS, "support_profiles": profile_summary, "probes": []}
    if args.skip_mechanics and outputs["mechanics"].exists():
        mechanics = json.loads(outputs["mechanics"].read_text(encoding="utf-8"))
    else:
        for microbatch in config["mechanics"]["microbatches"]:
            probe = mechanics_probe(len(registry), microbatch, profiles, config)
            mechanics["probes"].append(probe)
            print(f"mechanics microbatch={microbatch}: {probe['classification']}", flush=True)
        feasible = all(item["classification"] == "FULL 41,238-ADDRESS MECHANICALLY FEASIBLE" and item.get("finite") for item in mechanics["probes"])
        mechanics["classification"] = "FULL 41,238-ADDRESS MECHANICALLY FEASIBLE" if feasible else "ENGINEERING LIMITATION"
        atomic_json(outputs["mechanics"], mechanics)
    if mechanics["classification"] != "FULL 41,238-ADDRESS MECHANICALLY FEASIBLE":
        raise RuntimeError("final-address engineering limitation; biological qualification stopped")
    if args.mechanics_only:
        print(json.dumps(mechanics, indent=2, sort_keys=True))
        return 0

    fixtures = [generate_capacity_fixture(genes=config["synthetic"]["genes"], cells=config["synthetic"]["cells"], donors=config["synthetic"]["donors"], seed=item["seed"], name=item["name"]) for item in config["fixtures"]]
    all_capacity = []
    all_rare = []
    final_states: dict[tuple[str, str, int], dict[str, torch.Tensor]] = {}
    final_h: dict[tuple[str, str, int], torch.Tensor] = {}
    for fixture in fixtures:
        for masker in ("oracle", "graph_free"):
            rows, rare, state, states = train_fixture(fixture, masker=masker, width=160, config=config)
            all_capacity.extend(rows); all_rare.extend(rare)
            final_states[(fixture.name, masker, 160)] = state
            final_h[(fixture.name, masker, 160)] = states
    gate = capacity_gate(all_capacity, config)
    if gate["width_160_gate_fired"]:
        comparison_rows = []
        for fixture in fixtures:
            rows, rare, _, _ = train_fixture(fixture, masker="oracle", width=256, config=config)
            comparison_rows.extend(rows); all_rare.extend(rare)
        all_capacity.extend(comparison_rows)
        gate["width_256_run"] = True
        gate["classification"] = "WIDTH 256 COMPARISON COMPLETED - HUMAN LOCALIZATION REQUIRED"
    else:
        gate["width_256_run"] = False
    atomic_csv(outputs["capacity"], all_capacity)
    atomic_csv(outputs["rare"], all_rare)
    atomic_json(outputs["capacity_gate"], gate)

    capacity_frame = pd.DataFrame(all_capacity)
    final160 = capacity_frame.loc[(capacity_frame.d_gene == 160) & (capacity_frame.checkpoint == 256)]
    oracle = final160.loc[final160.masker.eq("oracle")]
    uniform = final160.loc[final160.masker.eq("graph_free")]
    merged = oracle.merge(uniform, on=["fixture", "factor", "factor_family"], suffixes=("_oracle", "_graph_free"))
    merged["graph_free_minus_oracle_r2"] = merged.learned_h_r2_graph_free - merged.learned_h_r2_oracle
    family = merged.groupby(["fixture", "factor_family"], as_index=False).agg(
        oracle_h_r2=("learned_h_r2_oracle", "mean"), graph_free_h_r2=("learned_h_r2_graph_free", "mean"),
        graph_free_minus_oracle_r2=("graph_free_minus_oracle_r2", "mean"),
    )
    family.insert(0, "status", STATUS)
    rare_frame = pd.DataFrame(all_rare)
    rare_final = rare_frame.loc[(rare_frame.d_gene == 160) & (rare_frame.checkpoint == 256)]
    rare_compare = rare_final.pivot(index="fixture", columns="masker", values=["learned_h_rare_auroc", "learned_h_rare_ap"])
    replicated_bad = family.loc[family.graph_free_minus_oracle_r2 < -0.10].groupby("factor_family").fixture.nunique()
    rare_degraded = []
    for fixture in rare_compare.index:
        if rare_compare.loc[fixture, ("learned_h_rare_auroc", "graph_free")] < rare_compare.loc[fixture, ("learned_h_rare_auroc", "oracle")] - 0.10 or rare_compare.loc[fixture, ("learned_h_rare_ap", "graph_free")] < rare_compare.loc[fixture, ("learned_h_rare_ap", "oracle")] - 0.10:
            rare_degraded.append(fixture)
    graph_free_pass = not any(replicated_bad >= len(fixtures)) and len(rare_degraded) < len(fixtures)
    graph_summary = {
        "status": STATUS, "pearson_graph_invoked": False,
        "replicated_factor_family_degradation": sorted(replicated_bad.loc[replicated_bad >= len(fixtures)].index.tolist()),
        "rare_degradation_fixtures": rare_degraded,
        "classification": "PEARSON GRAPH NOT REQUIRED BY BOUNDED SYNTHETIC EVIDENCE" if graph_free_pass else "STRUCTURED MASKING REQUIREMENT SUPPORTED; SCALABLE MASKING DESIGN REMAINS OPEN",
    }
    atomic_csv(outputs["graph_free"], family.to_dict("records"))
    atomic_json(outputs["graph_free_summary"], graph_summary)

    operator_rows = []
    operator_summaries = []
    uncertainty_rows = []
    uncertainty_summaries = []
    for fixture in fixtures:
        op_rows, op_summary = operator_audit(fixture, final_states[(fixture.name, "oracle", 160)], config)
        operator_rows.extend(op_rows); operator_summaries.append(op_summary)
        u_rows, u_summary = uncertainty_audit(fixture, final_states[(fixture.name, "oracle", 160)], config)
        uncertainty_rows.extend(u_rows); uncertainty_summaries.append(u_summary)
    operator_counts = pd.Series([row["classification"] for row in operator_rows]).value_counts().to_dict()
    operator_summary = {"status": STATUS, "operator_ids_supplied_to_encoder": False, "classification_counts": {key: int(value) for key, value in operator_counts.items()}, "fixtures": operator_summaries}
    u_separable = all(item["classification"] == "U_BIO/U_MEAS OPERATIONALLY SEPARABLE" for item in uncertainty_summaries)
    uncertainty_summary = {
        "status": STATUS,
        "classification": "U_BIO/U_MEAS OPERATIONALLY SEPARABLE" if u_separable else "SEPARATION NOT DEMONSTRATED",
        "u_meas_reference_definition": (
            "Each quality level is an independent Poisson remeasurement of the same latent rate. "
            "Level 1.0 uses complete support and reference depth 12,000 and is compared with the "
            "original independently sampled complete-support observation after library normalization; "
            "it is not an observation compared with itself."
        ),
        "u_meas_level_1_interpretation": (
            "Independent-measurement and depth/noise floor; zero is not expected. "
            "This is not a calibrated U_MEAS score."
        ),
        "u_bio_monotonicity_violations": int(sum(item["u_bio_monotonicity_violations"] for item in uncertainty_summaries)),
        "u_meas_monotonicity_violations": int(sum(item["u_meas_monotonicity_violations"] for item in uncertainty_summaries)),
        "fixtures": uncertainty_summaries, "combined_score_created": False,
    }
    atomic_csv(outputs["operator"], operator_rows); atomic_json(outputs["operator_summary"], operator_summary)
    atomic_csv(outputs["uncertainty"], uncertainty_rows); atomic_json(outputs["uncertainty_summary"], uncertainty_summary)
    anti = anti_topk_fixture(**config["anti_top_k"])
    anti["status"] = STATUS
    anti["permanent_regression_pass"] = bool(
        anti["full_broad_r2"] >= 0.20 and anti["topk_broad_r2"] >= 0.20
        and anti["full_rare_auroc"] >= 0.75 and anti["topk_rare_auroc"] < anti["full_rare_auroc"] - 0.10
    )
    atomic_json(outputs["anti_top_k"], anti)
    hash_report = {
        "status": STATUS, "expected_a2r_semantic_hash": EXPECTED_A2R_HASH,
        "observed_a2r_semantic_hash": contract["semantic_hash"],
        "a2r_hash_unchanged": contract["semantic_hash"] == EXPECTED_A2R_HASH,
        "registry_file_sha256": sha256_file(project / config["inputs"]["registry"]),
        "measurement_support_file_sha256": sha256_file(project / config["inputs"]["measurement_support"]),
    }
    atomic_json(outputs["hashes"], hash_report)
    report = {
        "status": STATUS, "stage": config["stage_id"], "a2r_contract": contract,
        "mechanics": mechanics, "capacity_gate": gate, "graph_free": graph_summary,
        "operator_summary": operator_summary, "uncertainty_summary": uncertainty_summary,
        "anti_top_k": anti, "governance": {
            "real_rna_accessed": False, "dev_rna_accessed": False, "sealed_rna_accessed": False,
            "pathology_accessed": False, "stage81b_started": False, "stage81c_started": False,
            "a3_freeze1_declared": False,
        },
        "final_state": "STAGE81A3R_SYNTHETIC_CLOSURE_COMPLETE_NOT_FROZEN",
    }
    atomic_json(outputs["report"], report)
    write_readout(outputs["readout"], report)
    print(json.dumps({
        "mechanics": mechanics["classification"], "capacity": gate["classification"],
        "graph_free": graph_summary["classification"], "uncertainty": uncertainty_summary["classification"],
        "anti_top_k_pass": anti["permanent_regression_pass"], "final_state": report["final_state"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
