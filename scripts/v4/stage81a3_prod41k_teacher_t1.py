#!/usr/bin/env python3
"""Run the prospectively frozen PROD41K T1 trained-teacher experiment."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import pickle
import random
import stat
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import average_precision_score, r2_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exports" / "prod41k_teacher_t1_20260823"
RUN = OUT / "t1_run"
V5A = ROOT / "exports" / "contextual_biology_v6r5a_20260822"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "exports" / "static_context_decomposition_v4_20260821"))
sys.path.insert(0, str(V5A))

from production_train_loader import MEASURED_SCALAR, ProductionTrainLoader  # noqa: E402
from sea_ad_jepa.v4 import (  # noqa: E402
    capture_synthetic_checkpoint,
    restore_synthetic_checkpoint,
)
from validate_fallback_reader import QueryAwareBilinearReader  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "phase_e", ROOT / "scripts" / "v4" / "stage81a3_prod41k_engineering_smoke.py"
)
phase_e = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(phase_e)

SEED = 8_113_002
EVALUATION_SEED = 20_260_823_01
CHECKPOINTS = (0, 10, 25, 50, 100, 200, 205)
MAX_UPDATES = CHECKPOINTS[-1]
EFFECTIVE_BATCH = 128
MICROBATCH = 8
EVAL_BATCH = 8
PARTIAL_SAMPLE_PASS = 900_001
PARTIAL_VIEW_INDEX = 0
CONTINUOUS = (
    "broad_common",
    "weak_distributed",
    "local",
    "local_core",
    "local_halo",
    "core_halo",
    "sparse_marker_like",
    "innovation_tail",
)
RARE = ("recurrent_5pct", "recurrent_1pct")
INFERENTIAL_RARE = {"recurrent_5pct"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", choices=("auto", "cuda"), default="auto")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, payload: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def capture_rng_state() -> dict[str, Any]:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch_cpu": torch.get_rng_state().clone(),
        "torch_cuda": [state.clone() for state in torch.cuda.get_rng_state_all()] if torch.cuda.is_available() else None,
    }


def restore_rng_state(state: dict[str, Any]) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch_cpu"])
    if torch.cuda.is_available() and state["torch_cuda"] is not None:
        torch.cuda.set_rng_state_all(state["torch_cuda"])


def rng_state_hash(state: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update(pickle.dumps(state["python"], protocol=4))
    name, keys, position, has_gauss, cached = state["numpy"]
    digest.update(str(name).encode())
    digest.update(keys.tobytes())
    digest.update(np.asarray([position, has_gauss], dtype=np.int64).tobytes())
    digest.update(np.asarray([cached], dtype=np.float64).tobytes())
    digest.update(state["torch_cpu"].cpu().numpy().tobytes())
    for cuda_state in state["torch_cuda"] or []:
        digest.update(cuda_state.cpu().numpy().tobytes())
    return digest.hexdigest()


def validate_contract() -> dict[str, Any]:
    contract_path = OUT / "T1_BIOLOGY_EVALUATION_FREEZE.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract["status"] != "FROZEN" or contract["checkpoint_schedule"] != list(CHECKPOINTS):
        raise RuntimeError("T1 contract status/schedule mismatch")
    for item in contract["frozen_hashes"]:
        path = ROOT / item["path"]
        if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise RuntimeError(f"frozen T1 input drift: {item['path']}")
    return contract


def save_checkpoint(
    update: int,
    online: torch.nn.Module,
    target: torch.nn.Module,
    predictor: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scaler: torch.amp.GradScaler,
    controller: Any,
    sampler: torch.Generator,
) -> dict[str, Any]:
    path = RUN / f"t1_checkpoint_u{update:04d}.pt"
    if path.exists():
        raise RuntimeError(f"refusing to overwrite read-only checkpoint {path}")
    optimizer.zero_grad(set_to_none=True)
    state = capture_synthetic_checkpoint(
        online_encoder=online,
        target_encoder=target,
        predictor=predictor,
        optimizer=optimizer,
        global_update_step=controller.global_update_step,
        ema_update_count=controller.ema_update_count,
        accumulation_position=0,
        masking_generator=sampler,
    )
    state.update(
        {
            "schema": "prod41k-teacher-t1-v2",
            "experiment_id": "EXP-20260823-PROD41K-TEACHER-T1",
            "schedule_cursor": update,
            "donor_primary_scheduler_cursor": update * EFFECTIVE_BATCH,
            "scaler": scaler.state_dict(),
            "effective_batch": EFFECTIVE_BATCH,
            "microbatch": MICROBATCH,
            "contract_sha256": sha256(OUT / "T1_BIOLOGY_EVALUATION_FREEZE.json"),
        }
    )
    start = time.perf_counter()
    torch.save(state, path)
    elapsed = time.perf_counter() - start
    digest = sha256(path)
    os.chmod(path, stat.S_IREAD)
    return {"update": update, "path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": digest, "write_seconds": elapsed}


def load_latest(device: torch.device, components: tuple[Any, ...], sampler: torch.Generator):
    manifest_path = RUN / "checkpoint_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["checkpoints"][-1]
    path = ROOT / row["path"]
    if sha256(path) != row["sha256"]:
        raise RuntimeError("resume checkpoint hash mismatch")
    loaded = torch.load(path, map_location="cpu", weights_only=False)
    if loaded.get("schema") != "prod41k-teacher-t1-v2":
        raise RuntimeError("resume checkpoint is not T1-v2")
    if int(loaded.get("donor_primary_scheduler_cursor", -1)) != int(loaded["schedule_cursor"]) * EFFECTIVE_BATCH:
        raise RuntimeError("donor-primary scheduler state mismatch")
    online, target, predictor, optimizer, scaler, controller = components
    counters = restore_synthetic_checkpoint(
        loaded,
        online_encoder=online,
        target_encoder=target,
        predictor=predictor,
        optimizer=optimizer,
        masking_generator=sampler,
    )
    scaler.load_state_dict(loaded["scaler"])
    controller.load_bookkeeping(
        global_update_step=counters["global_update_step"],
        ema_update_count=counters["ema_update_count"],
    )
    return int(loaded["schedule_cursor"]), manifest


def assert_parameter_correspondence(online: torch.nn.Module, target: torch.nn.Module) -> None:
    online_state = online.state_dict()
    target_state = target.encoder.state_dict()
    if list(online_state) != list(target_state):
        raise RuntimeError("online/EMA parameter names or ordering differ")
    mismatches = [key for key in online_state if online_state[key].shape != target_state[key].shape]
    if mismatches:
        raise RuntimeError(f"online/EMA parameter shape mismatch: {mismatches[:3]}")


def truncate_to_checkpoint(run: Path, update: int, trajectory: dict[str, Any]) -> dict[str, Any]:
    trajectory["updates"] = [row for row in trajectory.get("updates", []) if int(row["update"]) <= update]
    trajectory["evaluations"] = [row for row in trajectory.get("evaluations", []) if int(row["update"]) <= update]
    for pattern in ("t1_biology_metrics_u*.csv", "t1_source_operator_metrics_u*.csv", "t1_representation_health_u*.json", "t1_address_reader_metrics_u*.csv"):
        for path in run.glob(pattern):
            marker = path.stem.rsplit("_u", 1)[-1]
            if marker.isdigit() and int(marker) > update:
                path.unlink()
    return trajectory


def donor_permutation(meta: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    output = np.empty(len(meta), dtype=np.int64)
    assigned = np.zeros(len(meta), dtype=bool)
    audit = []
    for (partition, operator), operator_rows in meta.groupby(["reader_partition", "matrix_id"]):
        if operator_rows["donor_id"].astype(str).nunique() < 2:
            continue
        donors = sorted(
            operator_rows["donor_id"].astype(str).unique(),
            key=lambda donor: hashlib.sha256(f"{EVALUATION_SEED}|shuffle|operator|{partition}|{operator}|{donor}".encode()).hexdigest(),
        )
        mapping = {donor: donors[(index + 1) % len(donors)] for index, donor in enumerate(donors)}
        positions = {str(donor): group.index.to_numpy() for donor, group in operator_rows.groupby(operator_rows["donor_id"].astype(str))}
        for donor, indices in positions.items():
            target_indices = positions[mapping[donor]]
            output[indices] = np.resize(target_indices, len(indices))
            assigned[indices] = True
        audit.append({"partition": partition, "stratum": str(operator), "match_level": "operator", "cells": len(operator_rows), "donors": len(donors)})
    remainder = meta.loc[~assigned]
    for (partition, source), fallback_rows in remainder.groupby(["reader_partition", "study_id"]):
        source_rows = meta.loc[meta["reader_partition"].eq(partition) & meta["study_id"].eq(source)]
        donors = sorted(
            source_rows["donor_id"].astype(str).unique(),
            key=lambda donor: hashlib.sha256(f"{EVALUATION_SEED}|shuffle|source-fallback|{partition}|{source}|{donor}".encode()).hexdigest(),
        )
        if len(donors) < 2:
            raise RuntimeError(f"source fallback shuffle has fewer than two donors: {partition}/{source}")
        mapping = {donor: donors[(index + 1) % len(donors)] for index, donor in enumerate(donors)}
        positions = {str(donor): group.index.to_numpy() for donor, group in source_rows.groupby(source_rows["donor_id"].astype(str))}
        for donor, group in fallback_rows.groupby(fallback_rows["donor_id"].astype(str)):
            indices = group.index.to_numpy()
            output[indices] = np.resize(positions[mapping[str(donor)]], len(indices))
            assigned[indices] = True
        audit.append({"partition": partition, "stratum": str(source), "match_level": "source_fallback", "cells": len(fallback_rows), "donors": len(donors)})
    if not assigned.all():
        raise RuntimeError("donor shuffle left cells unassigned")
    if np.any(meta["donor_id"].astype(str).to_numpy() == meta["donor_id"].astype(str).to_numpy()[output]):
        raise RuntimeError("donor shuffle retained same donor")
    return output, pd.DataFrame(audit)


def load_evaluation(loader: ProductionTrainLoader):
    reader_dependencies = pd.read_csv(OUT / "t1_address_reader_runtime_dependencies.csv")
    for dependency in reader_dependencies.itertuples(index=False):
        path = ROOT / dependency.path
        if path.stat().st_size != int(dependency.bytes) or sha256(path) != str(dependency.sha256):
            raise RuntimeError(f"V6R5A address-reader dependency drift: {dependency.path}")
    meta = pd.read_csv(V5A / "biology_evaluation_cohort.csv")
    labels = pd.read_csv(V5A / "biology_cohort_intrinsic_labels.csv")
    donor_split = pd.read_csv(V5A / "reader_donor_split.csv")
    meta = meta.merge(labels, on="biology_cell_index", validate="one_to_one")
    meta = meta.merge(donor_split, on="donor_id", validate="many_to_one")
    if len(meta) != 4_540 or meta["donor_id"].nunique() != 149 or not meta["split"].eq("train").all():
        raise RuntimeError("frozen T1 evaluation cohort changed")
    identity_audit = pd.read_csv(OUT / "t1_evaluation_cell_identity_audit.csv")
    if (len(identity_audit) != len(meta) or not identity_audit.all_identity_fields_exact.astype(bool).all()
            or not identity_audit.stable_mask_key_exact.astype(bool).all()):
        raise RuntimeError("frozen 4,540-cell source-row identity audit failed")
    request = pd.DataFrame({
        "operator_index": identity_audit.operator_index.astype(np.int64),
        "matrix_id": identity_audit.matrix_id.astype(str),
        "local_row": identity_audit.local_row.astype(np.int64),
        "source_library": identity_audit.source_library_loader.astype(np.int64),
    })
    request["loader_row"] = np.arange(len(request), dtype=np.int64)
    values, states = loader.load(request)
    measured = states == MEASURED_SCALAR
    weights_file = np.load(V5A / "program_weights.npz", allow_pickle=False)
    weights = np.stack([weights_file[f"l2__{name}"].astype(np.float32) for name in CONTINUOUS])
    targets = values.astype(np.float64) @ weights.astype(np.float64).T
    targets[:, CONTINUOUS.index("innovation_tail")] = meta.innovation_tail.to_numpy(np.float64)
    evidence = measured.astype(np.float32) @ np.square(weights).T
    control = pd.get_dummies(meta[["study_id", "matrix_id"]].astype(str), dtype=float).to_numpy(np.float32)
    reader_cells = pd.read_csv(V5A / "reader_cells.csv")
    reader_request = reader_cells.copy()
    reader_request["loader_row"] = np.arange(len(reader_request), dtype=np.int64)
    reader_values, reader_states = loader.load(reader_request)
    reader_data = np.load(V5A / "real_reader_rows.npz", allow_pickle=False)
    reader_spec = {
        "values": reader_values,
        "measured": reader_states == MEASURED_SCALAR,
        "cell_index": reader_data["cell_index"].astype(np.int64),
        "address": reader_data["address"].astype(np.int64),
        "target": reader_data["value"].astype(np.float32),
        "query": reader_data["frozen_identity"].astype(np.float32)[reader_data["address"].astype(np.int64)],
        "partition": reader_cells["reader_partition"].astype(str).to_numpy()[reader_data["cell_index"].astype(np.int64)],
        "donor": reader_cells["donor_id"].astype(str).to_numpy()[reader_data["cell_index"].astype(np.int64)],
    }
    panel = pd.read_csv(OUT / "t1_partial_evidence_panel.csv")
    if len(panel) != len(meta) or not panel["biology_cell_index"].to_numpy().tolist() == meta["biology_cell_index"].to_numpy().tolist():
        raise RuntimeError("partial-evidence panel row identity mismatch")
    packed = np.load(OUT / "t1_partial_evidence_masks.npz", allow_pickle=False)
    if str(packed["bitorder"].item()) != "little":
        raise RuntimeError("packed partial-mask bitorder mismatch")
    if packed["biology_cell_index"].astype(np.int64).tolist() != meta["biology_cell_index"].astype(np.int64).tolist():
        raise RuntimeError("packed partial-mask cell identity mismatch")
    partial_masks = np.unpackbits(packed["masks"], axis=1, count=phase_e.VOCABULARY_SIZE, bitorder="little").astype(bool)
    if np.any(partial_masks & ~measured):
        raise RuntimeError("packed partial panel hides non-measured address")
    rare_mapping = pd.read_csv(OUT / "t1_rare_representation_mapping.csv")
    if set(rare_mapping["rare_endpoint"]) != set(RARE) or not rare_mapping["mapping_exact"].astype(bool).all() or not rare_mapping["representation_program"].eq("innovation_tail").all():
        raise RuntimeError("frozen rare-to-innovation representation mapping mismatch")
    return meta.reset_index(drop=True), values, measured, weights, targets, evidence, control, reader_spec, panel, partial_masks


@torch.inference_mode()
def representation_features(
    encoder: torch.nn.Module,
    values: np.ndarray,
    measured: np.ndarray,
    weights: np.ndarray,
    device: torch.device,
    *,
    role: str,
    panel: pd.DataFrame | None,
    partial_masks: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    encoder.eval()
    count = len(values)
    h = np.empty((count, len(CONTINUOUS), phase_e.WIDTH), dtype=np.float32)
    cell = np.empty((count, phase_e.WIDTH), dtype=np.float32)
    weight_tensor = torch.from_numpy(weights).to(device)
    minima = []
    for begin in range(0, count, EVAL_BATCH):
        end = min(begin + EVAL_BATCH, count)
        batch = end - begin
        expression = torch.from_numpy(values[begin:end]).to(device)
        mask = torch.from_numpy(measured[begin:end]).to(device)
        gene_ids = torch.arange(phase_e.VOCABULARY_SIZE, device=device).expand(batch, -1)
        hidden = torch.zeros_like(mask)
        if panel is not None:
            if partial_masks is None:
                raise RuntimeError("fixed partial masks missing")
            hidden_cpu = torch.from_numpy(partial_masks[begin:end])
            hidden = hidden_cpu.to(device)
            for local in range(batch):
                digest = hashlib.sha256(hidden_cpu[local].numpy().tobytes()).hexdigest()
                if digest != str(panel.iloc[begin + local].mask_sha256):
                    raise RuntimeError("partial-evidence mask hash drift")
        with torch.autocast("cuda", dtype=torch.float16):
            output = encoder(gene_ids, expression, mask, hidden, role)
        pooled = torch.einsum("kg,bgd->bkd", weight_tensor, output.gene_states.float())
        h[begin:end] = pooled.cpu().numpy()
        cell[begin:end] = output.cell_state.float().cpu().numpy()
        minima.append(float(output.minimum_denominator))
        if end % 512 == 0 or end == count:
            print(f"evaluation features {end}/{count}", flush=True)
    health = {
        "minimum_attention_denominator": min(minima),
        "H_program_feature_variance": float(np.var(h, axis=0).mean()),
        "CELL_feature_variance": float(np.var(cell, axis=0).mean()),
    }
    ranks = {}
    for index, endpoint in enumerate(CONTINUOUS):
        singular = np.linalg.svd(h[:, index] - h[:, index].mean(axis=0), compute_uv=False)
        probability = np.square(singular) / np.square(singular).sum()
        ranks[endpoint] = float(np.exp(-(probability * np.log(np.maximum(probability, 1e-30))).sum()))
    health["H_program_effective_rank"] = ranks
    health["evidence_mode"] = "fixed_partial_online" if panel is not None else "rich_ema"
    return h, cell, health


@torch.inference_mode()
def molecular_features(encoder: torch.nn.Module, spec: dict[str, np.ndarray], device: torch.device) -> np.ndarray:
    encoder.eval()
    output_h = np.empty((len(spec["address"]), phase_e.WIDTH), dtype=np.float32)
    positions = {int(cell): np.flatnonzero(spec["cell_index"] == cell) for cell in np.unique(spec["cell_index"])}
    for begin in range(0, len(spec["values"]), EVAL_BATCH):
        end = min(begin + EVAL_BATCH, len(spec["values"]))
        expression = torch.from_numpy(spec["values"][begin:end]).to(device)
        measured = torch.from_numpy(spec["measured"][begin:end]).to(device)
        gene_ids = torch.arange(phase_e.VOCABULARY_SIZE, device=device).expand(end - begin, -1)
        with torch.autocast("cuda", dtype=torch.float16):
            encoded = encoder(gene_ids, expression, measured, torch.zeros_like(measured), "target")
        for cell in range(begin, end):
            take = positions.get(cell)
            if take is None:
                continue
            addresses = torch.from_numpy(spec["address"][take]).to(device)
            output_h[take] = encoded.gene_states[cell - begin, addresses].float().cpu().numpy()
    return output_h


def address_reader_metrics(update: int, current_h: np.ndarray, spec: dict[str, np.ndarray], device: torch.device) -> list[dict[str, Any]]:
    fit_indices = np.flatnonzero(spec["partition"] == "reader_fit")
    validation_indices = np.flatnonzero(spec["partition"] == "reader_validation")
    torch.manual_seed(20_260_822_05)
    torch.cuda.manual_seed_all(20_260_822_05)
    model = QueryAwareBilinearReader(phase_e.WIDTH, spec["query"].shape[1]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-3, weight_decay=1e-6)
    generator = torch.Generator().manual_seed(20_260_822_07)
    best, best_mse, stale, epochs = None, float("inf"), 0, 0
    for epoch in range(100):
        model.train()
        order = torch.randperm(len(fit_indices), generator=generator).numpy()
        for begin in range(0, len(order), 2048):
            take = fit_indices[order[begin:begin + 2048]]
            optimizer.zero_grad(set_to_none=True)
            prediction = model(
                torch.from_numpy(current_h[take]).to(device),
                torch.from_numpy(spec["query"][take]).to(device),
            )
            loss = torch.mean((prediction - torch.from_numpy(spec["target"][take]).to(device)) ** 2)
            loss.backward()
            optimizer.step()
        model.eval()
        predictions = []
        with torch.inference_mode():
            for begin in range(0, len(validation_indices), 4096):
                take = validation_indices[begin:begin + 4096]
                predictions.append(model(
                    torch.from_numpy(current_h[take]).to(device),
                    torch.from_numpy(spec["query"][take]).to(device),
                ).float().cpu().numpy())
        validation_prediction = np.concatenate(predictions)
        validation_mse = float(np.square(spec["target"][validation_indices] - validation_prediction).mean())
        epochs = epoch + 1
        if validation_mse < best_mse - 1e-6:
            best_mse = validation_mse
            best = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
            stale = 0
        else:
            stale += 1
        if stale >= 10:
            break
    if best is None:
        raise RuntimeError("checkpoint-specific address reader produced no fit")
    model.load_state_dict(best)
    model.eval()
    predictions = []
    with torch.inference_mode():
        for begin in range(0, len(current_h), 4096):
            predictions.append(model(
                torch.from_numpy(current_h[begin:begin + 4096]).to(device),
                torch.from_numpy(spec["query"][begin:begin + 4096]).to(device),
            ).float().cpu().numpy())
    prediction = np.concatenate(predictions)
    rows = []
    for partition in ("reader_validation", "reader_oracle", "heldout_combined"):
        take = spec["partition"] != "reader_fit" if partition == "heldout_combined" else spec["partition"] == partition
        y = spec["target"][take]
        p = prediction[take]
        rows.append({
            "update": update, "evidence_mode": "rich_ema", "evaluation_partition": partition,
            "evaluation_role": {
                "reader_validation": "reader_selection_descriptive",
                "reader_oracle": "primary_untouched_evaluation",
                "heldout_combined": "descriptive_combined_includes_reader_selection",
            }[partition],
            "assay": "qualified_v6r5a_address_bilinear_architecture_refit_per_checkpoint",
            "rows": int(take.sum()), "donors": int(np.unique(spec["donor"][take]).size),
            "r2": float(r2_score(y, p)), "mse": float(np.square(y - p).mean()),
            "spearman": float(spearmanr(y, p).statistic),
            "reader_epochs": epochs, "validation_selection_mse": best_mse,
        })
    return rows


def metric(kind: str, y: np.ndarray, prediction: np.ndarray) -> float:
    if kind == "continuous":
        return float(r2_score(y, prediction))
    if np.unique(y).size < 2:
        return float("nan")
    return float(average_precision_score(y, prediction))


def donor_delta_ci(
    kind: str,
    y: np.ndarray,
    trained: np.ndarray,
    baseline: np.ndarray,
    donors: np.ndarray,
    seed: int,
) -> dict[str, Any]:
    requested = 1_000
    unique = np.unique(donors)
    rng = np.random.default_rng(seed)
    values: list[float] = []
    rejected_single_class = 0
    positions = {donor: np.flatnonzero(donors == donor) for donor in unique}
    for _ in range(requested):
        selected = rng.choice(unique, len(unique), replace=True)
        take = np.concatenate([positions[donor] for donor in selected])
        if kind == "rare" and np.unique(y[take]).size < 2:
            rejected_single_class += 1
            continue
        values.append(metric(kind, y[take], trained[take]) - metric(kind, y[take], baseline[take]))
    valid = len(values)
    return {
        "lower": float(np.quantile(values, 0.025)) if valid else float("nan"),
        "upper": float(np.quantile(values, 0.975)) if valid else float("nan"),
        "requested": requested,
        "valid": valid,
        "rejected_single_class": rejected_single_class,
        "valid_fraction": valid / requested,
        "estimable": valid > 0,
        "reason": "estimable" if valid > 0 else "no_estimable_bootstrap_replicates",
    }


def fit_predictions(kind: str, x: np.ndarray, y: np.ndarray, partitions: np.ndarray) -> np.ndarray:
    train = partitions == "reader_fit"
    if kind == "continuous":
        model = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(x[train], y[train])
        return model.predict(x)
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(C=1.0, class_weight="balanced", max_iter=1_000, random_state=EVALUATION_SEED),
    ).fit(x[train], y[train])
    return model.predict_proba(x)[:, 1]


def evaluate_checkpoint(
    update: int,
    online: torch.nn.Module,
    target: torch.nn.Module,
    evaluation: tuple[Any, ...],
    u0: dict[str, np.ndarray] | None,
    device: torch.device,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    meta, values, measured, weights, continuous_targets, evidence, control, reader_spec, panel, partial_masks = evaluation
    rich_h, rich_cell, rich_health = representation_features(
        target, values, measured, weights, device, role="target", panel=None, partial_masks=None
    )
    partial_h, partial_cell, partial_health = representation_features(
        online, values, measured, weights, device, role="student", panel=panel, partial_masks=partial_masks
    )
    if u0 is None:
        u0 = {
            "rich_H": rich_h.copy(), "rich_CELL": rich_cell.copy(),
            "partial_H": partial_h.copy(), "partial_CELL": partial_cell.copy(),
        }
        np.savez_compressed(RUN / "u0_evaluation_features.npz", **u0)
        os.chmod(RUN / "u0_evaluation_features.npz", stat.S_IREAD)
    partitions = meta["reader_partition"].astype(str).to_numpy()
    donors = meta["donor_id"].astype(str).to_numpy()
    perm, shuffle_audit = donor_permutation(meta)
    shuffle_audit.to_csv(RUN / "t1_donor_shuffle_audit.csv", index=False, lineterminator="\n")
    results = []
    predictions: dict[str, dict[str, np.ndarray]] = {}
    for endpoint_index, endpoint in enumerate(CONTINUOUS + RARE):
        kind = "continuous" if endpoint in CONTINUOUS else "rare"
        if kind == "continuous":
            y = continuous_targets[:, endpoint_index]
            h_index = endpoint_index
        else:
            y = meta[endpoint].to_numpy(np.int64)
            h_index = CONTINUOUS.index("innovation_tail")
        excluded_score = h_index
        lawful_score_columns = [index for index in range(len(CONTINUOUS)) if index != excluded_score]
        lawful_rna = np.concatenate([continuous_targets[:, lawful_score_columns], evidence, control], axis=1)
        arms = {
            "source_operator_only": control,
            "lawful_RNA_predictive_baseline": lawful_rna,
            "u0_rich_H": np.concatenate([u0["rich_H"][:, h_index], control], axis=1),
            "trained_rich_H": np.concatenate([rich_h[:, h_index], control], axis=1),
            "u0_partial_H": np.concatenate([u0["partial_H"][:, h_index], control], axis=1),
            "trained_partial_H": np.concatenate([partial_h[:, h_index], control], axis=1),
            "u0_rich_CELL": np.concatenate([u0["rich_CELL"], control], axis=1),
            "trained_rich_CELL": np.concatenate([rich_cell, control], axis=1),
            "u0_partial_CELL": np.concatenate([u0["partial_CELL"], control], axis=1),
            "trained_partial_CELL": np.concatenate([partial_cell, control], axis=1),
            "trained_rich_H_donor_shuffled": np.concatenate([rich_h[perm, h_index], control], axis=1),
        }
        endpoint_predictions = {
            arm: fit_predictions(kind, features, y, partitions) for arm, features in arms.items()
        }
        y_permuted = y[perm]
        permutation_prediction = fit_predictions(kind, arms["trained_rich_H"], y_permuted, partitions)
        endpoint_predictions["readout_donor_permutation"] = permutation_prediction
        endpoint_predictions["exact_full_RNA_oracle"] = y.astype(np.float64)
        evaluation_sets = {
            "reader_validation": partitions == "reader_validation",
            "reader_oracle": partitions == "reader_oracle",
            "heldout_combined": partitions != "reader_fit",
        }
        for evaluation_partition, take_mask in evaluation_sets.items():
            take = np.flatnonzero(take_mask)
            partition_estimable = kind == "continuous" or np.unique(y[take]).size == 2
            trained_metric = metric(kind, y[take], endpoint_predictions["trained_rich_H"][take])
            u0_metric = metric(kind, y[take], endpoint_predictions["u0_rich_H"][take])
            if endpoint == "recurrent_1pct":
                ci = {"lower": np.nan, "upper": np.nan, "requested": 0, "valid": 0,
                      "rejected_single_class": 0, "valid_fraction": np.nan, "estimable": False,
                      "reason": "descriptive_only_no_inferential_interval"}
            elif not partition_estimable:
                ci = {"lower": np.nan, "upper": np.nan, "requested": 1_000, "valid": 0,
                      "rejected_single_class": 1_000, "valid_fraction": 0.0, "estimable": False,
                      "reason": "single_class_evaluation_partition"}
            else:
                ci = donor_delta_ci(kind, y[take], endpoint_predictions["trained_rich_H"][take], endpoint_predictions["u0_rich_H"][take], donors[take], EVALUATION_SEED + update + endpoint_index)
            for arm, prediction in endpoint_predictions.items():
                row = {"update": update, "evaluation_partition": evaluation_partition, "endpoint": endpoint, "endpoint_type": kind, "inferential_role": "inferential_with_heldout_power_caveat" if endpoint in INFERENTIAL_RARE else ("descriptive_only" if endpoint in RARE else "inferential"), "arm": arm, "cells": len(take), "donors": len(np.unique(donors[take])), "metric": "R2" if kind == "continuous" else "AP", "value": metric(kind, y[take], prediction[take]), "estimable": partition_estimable, "estimability_reason": "estimable" if partition_estimable else "single_class", "trained_rich_H_minus_u0_rich_H": trained_metric - u0_metric if arm == "trained_rich_H" else np.nan, "donor_bootstrap_delta_lower": ci["lower"] if arm == "trained_rich_H" else np.nan, "donor_bootstrap_delta_upper": ci["upper"] if arm == "trained_rich_H" else np.nan, "bootstrap_requested": ci["requested"] if arm == "trained_rich_H" else np.nan, "bootstrap_valid": ci["valid"] if arm == "trained_rich_H" else np.nan, "bootstrap_rejected_single_class": ci["rejected_single_class"] if arm == "trained_rich_H" else np.nan, "bootstrap_valid_fraction": ci["valid_fraction"] if arm == "trained_rich_H" else np.nan, "bootstrap_estimable": ci["estimable"] if arm == "trained_rich_H" else np.nan, "bootstrap_reason": ci["reason"] if arm == "trained_rich_H" else "not_applicable_to_arm"}
                if kind == "rare":
                    row["AUROC"] = float(roc_auc_score(y[take], prediction[take])) if np.unique(y[take]).size == 2 else np.nan
                    row["positives"] = int(y[take].sum())
                    row["positive_donors"] = int(meta.iloc[take].loc[y[take] == 1, "donor_id"].nunique())
                results.append(row)
        predictions[endpoint] = endpoint_predictions
    frame = pd.DataFrame(results)
    frame.to_csv(RUN / f"t1_biology_metrics_u{update:04d}.csv", index=False, lineterminator="\n")
    source_rows = []
    for endpoint in CONTINUOUS + RARE:
        kind = "continuous" if endpoint in CONTINUOUS else "rare"
        y = continuous_targets[:, CONTINUOUS.index(endpoint)] if kind == "continuous" else meta[endpoint].to_numpy(np.int64)
        endpoint_predictions = predictions[endpoint]
        heldout_meta = meta.loc[partitions != "reader_fit"]
        for stratum_type, column in (("source", "study_id"), ("operator", "matrix_id")):
            for stratum, group in heldout_meta.groupby(column):
                take = group.index.to_numpy()
                if group["donor_id"].nunique() < 3 or (kind == "rare" and np.unique(y[take]).size < 2):
                    continue
                for arm in ("trained_rich_H", "trained_partial_H", "u0_rich_H", "u0_partial_H", "lawful_RNA_predictive_baseline", "exact_full_RNA_oracle", "source_operator_only", "trained_rich_H_donor_shuffled"):
                    source_rows.append({"update": update, "endpoint": endpoint, "endpoint_type": kind, "stratum_type": stratum_type, "stratum": str(stratum), "arm": arm, "cells": len(take), "donors": group["donor_id"].nunique(), "metric": "R2" if kind == "continuous" else "AP", "value": metric(kind, y[take], endpoint_predictions[arm][take])})
        support_bins = pd.read_csv(OUT / "t1_physical_support_bins.csv").set_index("program_name").loc[endpoint if endpoint in CONTINUOUS else "innovation_tail"]
        evidence_index = CONTINUOUS.index(endpoint if endpoint in CONTINUOUS else "innovation_tail")
        evidence_values = evidence[:, evidence_index]
        boundaries = [-np.inf, support_bins["q25"], support_bins["q50"], support_bins["q75"], np.inf]
        for bin_index in range(4):
            take = np.flatnonzero((partitions != "reader_fit") & (evidence_values >= boundaries[bin_index]) & (evidence_values < boundaries[bin_index + 1]))
            if len(take) == 0 or (kind == "rare" and np.unique(y[take]).size < 2):
                continue
            for arm in ("trained_rich_H", "trained_partial_H", "u0_rich_H", "u0_partial_H", "lawful_RNA_predictive_baseline", "exact_full_RNA_oracle"):
                source_rows.append({"update": update, "endpoint": endpoint, "endpoint_type": kind, "stratum_type": "lawful_physical_support_quartile", "stratum": f"Q{bin_index + 1}", "arm": arm, "cells": len(take), "donors": meta.iloc[take]["donor_id"].nunique(), "metric": "R2" if kind == "continuous" else "AP", "value": metric(kind, y[take], endpoint_predictions[arm][take]), "support_lower": boundaries[bin_index], "support_upper": boundaries[bin_index + 1], "n_eff_1_over_sum_w4": support_bins["n_eff_1_over_sum_w4"]})
    pd.DataFrame(source_rows).to_csv(RUN / f"t1_source_operator_metrics_u{update:04d}.csv", index=False, lineterminator="\n")
    rich_molecular = molecular_features(target, reader_spec, device)
    reader_rows = address_reader_metrics(update, rich_molecular, reader_spec, device)
    pd.DataFrame(reader_rows).to_csv(RUN / f"t1_address_reader_metrics_u{update:04d}.csv", index=False, lineterminator="\n")
    health = {
        "update": update,
        "rich": rich_health,
        "partial": partial_health,
        "u0_rich_H_feature_variance": float(np.var(u0["rich_H"], axis=0).mean()),
        "u0_partial_H_feature_variance": float(np.var(u0["partial_H"], axis=0).mean()),
        "online_ema_parameter_l2": math.sqrt(sum(float((a.detach().float() - b.detach().float()).square().sum()) for a, b in zip(online.parameters(), target.encoder.parameters()))),
    }
    atomic_json(RUN / f"t1_representation_health_u{update:04d}.json", health)
    return u0, {"metrics_rows": len(frame), "address_reader_rows": len(reader_rows), "health": health}


def evaluate_checkpoint_rng_neutral(*args: Any, **kwargs: Any):
    before = capture_rng_state()
    before_hash = rng_state_hash(before)
    try:
        u0, summary = evaluate_checkpoint(*args, **kwargs)
    finally:
        restore_rng_state(before)
    after_hash = rng_state_hash(capture_rng_state())
    if before_hash != after_hash:
        raise RuntimeError("inline biological evaluation changed training RNG state")
    summary["rng_neutrality"] = {"before_sha256": before_hash, "after_sha256": after_hash, "equal": True}
    return u0, summary


def main() -> None:
    args = parse_args()
    RUN.mkdir(parents=True, exist_ok=True)
    lock = RUN / "T1_RUNNING.lock"
    if lock.exists():
        raise RuntimeError(f"T1 lock already exists: {lock}")
    lock.write_text(f"pid={os.getpid()}\nstarted={time.time()}\n", encoding="utf-8")
    try:
        contract = validate_contract()
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if device.type != "cuda":
            raise RuntimeError("T1 requires the Phase-E-qualified CUDA path")
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
        torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
        torch.use_deterministic_algorithms(True)
        loader = ProductionTrainLoader()
        cohort = phase_e.prepare_cohort(loader)
        split = pd.read_csv(V5A / "reader_donor_split.csv")
        fit_donors = set(split.loc[split["reader_partition"].eq("reader_fit"), "donor_id"].astype(str))
        heldout_donors = set(split.loc[~split["reader_partition"].eq("reader_fit"), "donor_id"].astype(str))
        if len(fit_donors) != 104 or len(heldout_donors) != 45 or fit_donors & heldout_donors:
            raise RuntimeError("frozen 104/45 encoder donor split changed")
        cohort = cohort.loc[cohort["donor_id"].astype(str).isin(fit_donors)].reset_index(drop=True)
        if cohort["donor_id"].nunique() != 104 or set(cohort["donor_id"].astype(str)) & heldout_donors:
            raise RuntimeError("encoder-fitting cohort includes held-out donor")
        inventory = pd.read_csv(OUT / "t1_encoder_fit_inventory.csv")
        if len(inventory) != len(cohort) or inventory["stable_mask_key"].astype(np.int64).tolist() != cohort["stable_mask_key"].astype(np.int64).tolist():
            raise RuntimeError("complete encoder-fitting inventory drift")
        full_loader = loader.cell_table().reset_index().rename(columns={"index": "accepted_inventory_row"})
        authoritative = full_loader.iloc[inventory["accepted_inventory_row"].to_numpy(np.int64)].reset_index(drop=True)
        for column in ("operator_index", "matrix_id", "local_row", "donor_id", "cell_id"):
            if not authoritative[column].astype(str).eq(inventory[column].astype(str)).all():
                raise RuntimeError(f"training accepted-inventory-row mismatch: {column}")
        if inventory["stable_mask_key"].duplicated().any():
            raise RuntimeError("training inventory stable-mask-key duplication")
        inventory_study = inventory["matrix_id"].map(phase_e.source_family)
        if inventory["donor_id"].astype(str).nunique() != 104 or pd.DataFrame({"donor": inventory["donor_id"].astype(str), "study": inventory_study}).groupby("donor")["study"].nunique().max() != 1:
            raise RuntimeError("T1 waterfill entities are not exactly 104 one-study donors")
        schedule = pd.read_csv(OUT / "t1_training_schedule.csv")
        if len(schedule) != MAX_UPDATES * EFFECTIVE_BATCH:
            raise RuntimeError("frozen donor-primary schedule length mismatch")
        if schedule.groupby("update")["stable_mask_key"].nunique().min() != EFFECTIVE_BATCH:
            raise RuntimeError("frozen schedule contains a same-update duplicate cell")
        scheduled_inventory = inventory.iloc[schedule["inventory_row"].to_numpy(np.int64)].reset_index(drop=True)
        if (not scheduled_inventory["stable_mask_key"].astype(np.int64).eq(schedule["stable_mask_key"].astype(np.int64)).all()
                or not scheduled_inventory["accepted_inventory_row"].astype(np.int64).eq(schedule["accepted_inventory_row"].astype(np.int64)).all()):
            raise RuntimeError("runner schedule does not exactly consume frozen inventory rows")
        if schedule.groupby("stable_mask_key").size().max() > 8:
            raise RuntimeError("frozen schedule violates accepted replay cap 8")
        components = phase_e.build_components(SEED, device)
        online, target, predictor, optimizer, scaler, controller = components
        assert_parameter_correspondence(online, target)
        sampler = torch.Generator(device="cpu").manual_seed(SEED + 700_001)
        manifest_path = RUN / "checkpoint_manifest.json"
        if args.resume:
            update, manifest = load_latest(device, components, sampler)
        else:
            if manifest_path.exists():
                raise RuntimeError("existing T1 checkpoints require --resume")
            update = 0
            manifest = {"schema": "prod41k-t1-checkpoints-v2", "contract_sha256": sha256(OUT / "T1_BIOLOGY_EVALUATION_FREEZE.json"), "checkpoints": []}
        evaluation = load_evaluation(loader)
        u0_path = RUN / "u0_evaluation_features.npz"
        if u0_path.exists():
            if "u0_features_sha256" not in manifest:
                raise RuntimeError("existing u0 evaluation cache lacks a manifest hash")
            with np.load(u0_path, allow_pickle=False) as stored:
                u0 = {key: stored[key] for key in ("rich_H", "rich_CELL", "partial_H", "partial_CELL")}
            expected_u0 = manifest["u0_features_sha256"]
            if sha256(u0_path) != expected_u0:
                raise RuntimeError("u0 cache hash/provenance mismatch")
        else:
            u0 = None
        trajectory_path = RUN / "t1_training_trajectory.json"
        trajectory = json.loads(trajectory_path.read_text(encoding="utf-8")) if trajectory_path.exists() else {"schema": "prod41k-t1-trajectory-v2", "updates": [], "evaluations": []}
        if args.resume:
            trajectory = truncate_to_checkpoint(RUN, update, trajectory)
            atomic_json(trajectory_path, trajectory)
        if update in CHECKPOINTS and not (RUN / f"t1_biology_metrics_u{update:04d}.csv").exists():
            if not any(row["update"] == update for row in manifest["checkpoints"]):
                manifest["checkpoints"].append(save_checkpoint(update, *components, sampler))
                atomic_json(manifest_path, manifest)
            u0, summary = evaluate_checkpoint_rng_neutral(update, online, target, evaluation, u0, device)
            manifest["u0_features_sha256"] = sha256(u0_path)
            atomic_json(manifest_path, manifest)
            trajectory["evaluations"].append({"update": update, **summary})
            atomic_json(trajectory_path, trajectory)
        for next_update in range(update + 1, MAX_UPDATES + 1):
            torch.cuda.reset_peak_memory_stats(device)
            started = time.perf_counter()
            selected = schedule.loc[schedule["update"].eq(next_update)].sort_values("slot")
            if len(selected) != EFFECTIVE_BATCH:
                raise RuntimeError(
                    f"frozen schedule has {len(selected)} rows at u{next_update}, expected {EFFECTIVE_BATCH}"
                )
            if selected["slot"].tolist() != list(range(EFFECTIVE_BATCH)):
                raise RuntimeError(f"frozen schedule slots are not exactly 0..{EFFECTIVE_BATCH - 1} at u{next_update}")
            batch_cohort = cohort.iloc[selected["inventory_row"].to_numpy(np.int64)].copy().reset_index(drop=True)
            if batch_cohort["stable_mask_key"].nunique() != EFFECTIVE_BATCH:
                raise RuntimeError(f"same-update cell replay at update {next_update}")
            online.train(); predictor.train(); target.eval()
            assert_parameter_correspondence(online, target)
            result = phase_e.run_update(
                loader=loader, cohort=batch_cohort, sampler=sampler, cursor=next_update - 1,
                seed=SEED, microbatch=MICROBATCH, effective_batch=EFFECTIVE_BATCH,
                device=device, online=online, target=target, predictor=predictor,
                optimizer=optimizer, scaler=scaler, controller=controller,
            )
            if not result["step_succeeded"] or not result["online_moved"] or not result["ema_equation"]["equal"]:
                raise RuntimeError(f"T1 mechanics failure at update {next_update}")
            trajectory["updates"].append({
                "update": next_update, "loss": result["loss"], "gradient_components": result["gradient_components"],
                "timing": result["timing"], "wall_seconds": time.perf_counter() - started,
                "peak_cuda_allocated_bytes": int(torch.cuda.max_memory_allocated(device)),
                "peak_cuda_reserved_bytes": int(torch.cuda.max_memory_reserved(device)),
                "ema_updates": controller.ema_update_count,
            })
            atomic_json(trajectory_path, trajectory)
            if next_update in CHECKPOINTS:
                manifest["checkpoints"].append(save_checkpoint(next_update, *components, sampler))
                atomic_json(manifest_path, manifest)
                u0, summary = evaluate_checkpoint_rng_neutral(next_update, online, target, evaluation, u0, device)
                trajectory["evaluations"].append({"update": next_update, **summary})
                atomic_json(trajectory_path, trajectory)
            print(f"T1 update={next_update}/{MAX_UPDATES} loss={result['loss']:.6f}", flush=True)
        atomic_json(RUN / "T1_RUN_COMPLETE.json", {"status": "COMPLETE_PENDING_ADJUDICATION", "updates": MAX_UPDATES, "contract_sha256": sha256(OUT / "T1_BIOLOGY_EVALUATION_FREEZE.json"), "finished": time.time()})
    except Exception as error:
        atomic_json(RUN / "T1_RUN_FAILURE.json", {"status": "FAILED", "error": repr(error), "time": time.time()})
        raise
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
