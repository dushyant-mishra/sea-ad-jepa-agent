#!/usr/bin/env python3
"""Disposable no-production-update proof for frozen T1 u1 cells and masks."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exports" / "prod41k_teacher_t1_20260823"
V5A = ROOT / "exports" / "contextual_biology_v6r5a_20260822"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "exports" / "static_context_decomposition_v4_20260821"))
from production_train_loader import MEASURED_SCALAR, ProductionTrainLoader  # noqa: E402

spec = importlib.util.spec_from_file_location("phase_e", ROOT / "scripts" / "v4" / "stage81a3_prod41k_engineering_smoke.py")
phase_e = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(phase_e)

SEED = 8_113_002
BATCH = 128
MICROBATCH = 8


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("u1 parity requires the qualified CUDA path")
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(True)
    loader = ProductionTrainLoader()
    cohort = phase_e.prepare_cohort(loader)
    split = pd.read_csv(V5A / "reader_donor_split.csv")
    fit_donors = set(split.loc[split.reader_partition.eq("reader_fit"), "donor_id"].astype(str))
    cohort = cohort.loc[cohort.donor_id.astype(str).isin(fit_donors)].reset_index(drop=True)
    inventory = pd.read_csv(OUT / "t1_encoder_fit_inventory.csv")
    schedule = pd.read_csv(OUT / "t1_training_schedule.csv")
    if inventory.stable_mask_key.astype(np.int64).tolist() != cohort.stable_mask_key.astype(np.int64).tolist():
        raise RuntimeError("parity inventory/cohort mismatch")
    u1 = schedule.loc[schedule["update"].eq(1)].sort_values("slot")
    if len(u1) != BATCH:
        raise RuntimeError("frozen u1 does not contain 128 rows")
    batch_cohort = cohort.iloc[u1.inventory_row.to_numpy(np.int64)].copy().reset_index(drop=True)
    online, target, predictor, optimizer, scaler, controller = phase_e.build_components(SEED, device)
    sampler = torch.Generator(device="cpu").manual_seed(SEED + 700_001)
    result = phase_e.run_update(
        loader=loader, cohort=batch_cohort, sampler=sampler, cursor=0, seed=SEED,
        microbatch=MICROBATCH, effective_batch=BATCH, device=device,
        online=online, target=target, predictor=predictor, optimizer=optimizer,
        scaler=scaler, controller=controller,
    )
    expected = sorted(u1.stable_mask_key.astype(np.int64).tolist())
    consumed = [int(value) for value in result["selected_ids"]]
    if sorted(consumed) != expected or len(set(consumed)) != BATCH:
        raise RuntimeError("actual run_update u1 cells differ from frozen schedule")
    by_key = cohort.set_index("stable_mask_key", drop=False)
    consumed_rows = by_key.loc[consumed].copy().reset_index(drop=True)
    consumed_rows["loader_row"] = np.arange(BATCH, dtype=np.int64)
    _, states = loader.load(consumed_rows)
    measured = torch.from_numpy(states).eq(int(MEASURED_SCALAR))
    pairwise_distinct = []
    for left in range(4):
        mask = result["masks"][left]
        if bool((mask & ~measured).any()):
            raise RuntimeError("actual u1 mask hides non-MEASURED_SCALAR address")
        expected_count = torch.floor(measured.sum(1).float() * 0.40).long()
        if not torch.equal(mask.sum(1), expected_count):
            raise RuntimeError("actual u1 mask count mismatch")
        for right in range(left + 1, 4):
            pairwise_distinct.append(result["masks"][left].ne(result["masks"][right]).any(1))
    pairwise = torch.stack(pairwise_distinct)
    if not bool(pairwise.all()):
        raise RuntimeError("u1 four-view masks are not independently keyed for every cell")

    repeated_key = next(key for key in consumed if bool(((schedule.stable_mask_key == key) & (schedule["update"] > 1)).any()))
    occurrences = schedule.loc[schedule.stable_mask_key.eq(repeated_key)].sort_values("update")
    first_update = int(occurrences.iloc[0]["update"])
    later_update = int(occurrences.iloc[1]["update"])
    one = by_key.loc[[repeated_key]].copy().reset_index(drop=True)
    one["loader_row"] = 0
    _, one_states = loader.load(one)
    one_measured = torch.from_numpy(one_states).eq(int(MEASURED_SCALAR))
    key_tensor = torch.tensor([repeated_key], dtype=torch.int64)
    first_masks, later_masks = [], []
    for view in range(4):
        first_masks.append(phase_e.sample_uniform_target_blocks(
            one_measured, production_seed=SEED, cell_indices=key_tensor,
            sample_pass=first_update - 1, view_index=view, mask_fraction=0.40, block_count=16,
        ).hidden_mask)
        later_masks.append(phase_e.sample_uniform_target_blocks(
            one_measured, production_seed=SEED, cell_indices=key_tensor,
            sample_pass=later_update - 1, view_index=view, mask_fraction=0.40, block_count=16,
        ).hidden_mask)
    if not all(bool(first_masks[view].ne(later_masks[view]).any()) for view in range(4)):
        raise RuntimeError("repeated cell did not receive fresh later-pass masks")
    report = {
        "schema": "prod41k-t1-u1-no-production-update-parity-v1",
        "status": "PASS",
        "production_updates_committed": 0,
        "disposable_run_update_succeeded": bool(result["step_succeeded"]),
        "frozen_u1_rows": BATCH,
        "actual_consumed_rows": len(consumed),
        "exact_cell_multiset_match": True,
        "selected_ids_sha256": digest(np.asarray(consumed, dtype=np.int64).tobytes()),
        "four_views": 4,
        "six_pairwise_distinct_for_every_cell": True,
        "masks_measured_scalar_only": True,
        "mask_fraction": 0.40,
        "target_blocks": 16,
        "actual_view_mask_sha256": result["mask_hashes"],
        "repeated_cell": {
            "stable_mask_key": repeated_key,
            "first_update": first_update,
            "later_update": later_update,
            "all_four_views_fresh": True,
            "first_mask_sha256": [digest(mask.numpy().tobytes()) for mask in first_masks],
            "later_mask_sha256": [digest(mask.numpy().tobytes()) for mask in later_masks],
        },
    }
    path = OUT / "T1_U1_NO_UPDATE_PARITY.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
