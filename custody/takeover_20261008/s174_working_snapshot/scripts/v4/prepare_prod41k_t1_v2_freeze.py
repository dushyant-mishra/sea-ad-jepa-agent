#!/usr/bin/env python3
"""Create the prospective, executable T1-v2 audit and scheduling artifacts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
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

spec = importlib.util.spec_from_file_location(
    "phase_e", ROOT / "scripts" / "v4" / "stage81a3_prod41k_engineering_smoke.py"
)
phase_e = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(phase_e)

SEED = 8_113_002
PARTIAL_SAMPLE_PASS = 900_001
PARTIAL_VIEW_INDEX = 0
EFFECTIVE_BATCH = 128
REPLAY_CAP = 8
HISTORICAL_SAMPLER_SEED = 1_756_835_074

PRECONDITION_HASHES = {
    "exports/contextual_biology_v6r5a_20260822/program_registry.csv": "8d29cfe86518882492ab8e878b8a2f79b8425a61b79710d5b74a0cbf654ba729",
    "exports/contextual_biology_v6r5a_20260822/program_weights.npz": "001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70",
    "exports/contextual_biology_v6r5a_20260822/biology_evaluation_cohort.csv": "d7cfbe006f6dc04bee96041fcf4ce78595b87a724f8a78d14f32a07651f268a1",
    "exports/contextual_biology_v6r5a_20260822/biology_cohort_intrinsic_labels.csv": "ba50eb0a6683621fc60fd30f2126bb9fb4a609286360463a964dfb8a7b4af52b",
    "exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv": "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511",
    "exports/static_context_decomposition_v4_20260821/production_train_loader.py": "267fa42a5fa6f8b5f8199c68add1ffe0c8b49142095b7d980d1af27a8a31154a",
    "scripts/v4/stage81a3_prod41k_engineering_smoke.py": "11b381762787aaae8920cfced3e245dbc8579b335ee2576ffcc21cc0253d4cd6",
    "exports/prod41k_teacher_t1_20260823/HISTORICAL_STAGE81B_TAXONOMY_NEUTRAL_SAMPLER.py": "253de32ccf30857baab7ecfa8ca51b97bb31fe6a18add4072c2e604a8900451f",
    "exports/prod41k_teacher_t1_20260823/HISTORICAL_STAGE81B_TAXONOMY_NEUTRAL_SAMPLER_AUDIT.md": "05ab421a5ff197975ecb6a75e4f918fa8df439fa9edea38a06046066c93cda9c",
    "exports/prod41k_teacher_t1_20260823/HISTORICAL_STAGE81B_SAMPLER_SEMANTICS_CORRECTION_AUDIT.md": "9c57590b1dce480b511dcd0206392e68569c09e4696261ef89cdc6c5e6956911",
}


def stable_digest(*parts: object) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()


def historical_keyed_seed(*parts: object) -> int:
    value = "|".join(map(str, (HISTORICAL_SAMPLER_SEED, *parts))).encode()
    return int.from_bytes(hashlib.sha256(value).digest()[:8], "big")


def exact_waterfill(capacity: np.ndarray, total: int, labels: list[str]) -> np.ndarray:
    active = set(range(len(capacity)))
    quota = np.zeros(len(capacity), dtype=np.int64)
    remaining = total
    while True:
        level = remaining / len(active)
        binding = sorted((index for index in active if capacity[index] < level), key=lambda i: labels[i])
        if not binding:
            break
        for index in binding:
            quota[index] = capacity[index]
            remaining -= int(capacity[index])
            active.remove(index)
    base = math.floor(level)
    for index in active:
        quota[index] = base
    remainder = total - int(quota.sum())
    for index in sorted(active, key=lambda i: labels[i])[:remainder]:
        quota[index] += 1
    if int(quota.sum()) != total or np.any(quota > capacity):
        raise RuntimeError("historical exact integer waterfill failed")
    return quota


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    for relative, expected in PRECONDITION_HASHES.items():
        if file_sha256(ROOT / relative) != expected:
            raise RuntimeError(f"controlling T1 input drift before generation: {relative}")
    stage = OUT / "_t1_v2_staging"
    if stage.exists():
        raise RuntimeError(f"staging directory already exists: {stage}")
    stage.mkdir(parents=True)
    loader = ProductionTrainLoader()
    cohort = phase_e.prepare_cohort(loader)
    full = loader.cell_table().copy()
    full["stable_mask_key"] = [
        phase_e.stable_key(row.matrix_id, row.local_row, row.cell_id) for row in full.itertuples()
    ]
    if len(cohort) != len(full):
        raise RuntimeError(f"T1 inventory is a subset: cohort={len(cohort)} full={len(full)}")
    if set(cohort.stable_mask_key.astype(np.int64)) != set(full.stable_mask_key.astype(np.int64)):
        raise RuntimeError("T1 cohort is not the complete accepted loader inventory")
    if cohort.stable_mask_key.duplicated().any() or full.stable_mask_key.duplicated().any():
        raise RuntimeError("accepted inventory stable-mask keys are not unique")
    full["accepted_inventory_row"] = np.arange(len(full), dtype=np.int64)
    identity = ["operator_index", "matrix_id", "local_row", "donor_id", "cell_id", "stable_mask_key"]
    cohort = cohort.merge(full[identity + ["accepted_inventory_row"]], on=identity, how="left", validate="one_to_one")
    if cohort.accepted_inventory_row.isna().any() or cohort.accepted_inventory_row.nunique() != len(full):
        raise RuntimeError("cohort/full identity is not one-to-one and complete")
    split = pd.read_csv(V5A / "reader_donor_split.csv")
    fit_donors = set(split.loc[split.reader_partition.eq("reader_fit"), "donor_id"].astype(str))
    fit = cohort.loc[cohort.donor_id.astype(str).isin(fit_donors)].copy().reset_index(drop=True)
    if len(fit_donors) != 104 or fit.donor_id.nunique() != 104:
        raise RuntimeError("frozen 104-donor encoder-fitting population changed")
    inventory_columns = [
        "cohort_row", "accepted_inventory_row", "operator_index", "matrix_id", "local_row", "donor_id", "cell_id",
        "broad_cell_class", "source_library", "stable_mask_key", "canonical_donor_id",
    ]
    fit[inventory_columns].to_csv(stage / "t1_encoder_fit_inventory.csv", index=False, lineterminator="\n")

    fit["study"] = fit.matrix_id.map(phase_e.source_family)
    if fit.groupby(fit.donor_id.astype(str)).study.nunique().max() != 1:
        raise RuntimeError("a T1 fit donor maps to more than one study")
    donor_table = fit.groupby(["study", "donor_id"], sort=True).size().rename("eligible_cells").reset_index()
    if len(donor_table) != 104 or donor_table.donor_id.astype(str).nunique() != 104:
        raise RuntimeError("waterfill must contain exactly 104 unique donor entities")
    donor_table["label"] = donor_table.study + "|" + donor_table.donor_id.astype(str)
    theoretical_presentations = REPLAY_CAP * len(fit)
    cap_last = theoretical_presentations // EFFECTIVE_BATCH
    total_presentations = cap_last * EFFECTIVE_BATCH
    quota = exact_waterfill(
        REPLAY_CAP * donor_table.eligible_cells.to_numpy(np.int64),
        total_presentations,
        donor_table.label.tolist(),
    )
    donor_table["quota"] = quota
    positions_by_donor = fit.groupby(["study", "donor_id"], sort=False).indices
    class_values = fit.broad_cell_class.astype(str).to_numpy()
    sequences: list[np.ndarray] = []
    for row in donor_table.itertuples(index=False):
        positions = np.asarray(positions_by_donor[(row.study, row.donor_id)], dtype=np.int64)
        local_classes = class_values[positions]
        classes = sorted(set(local_classes), key=lambda value: (historical_keyed_seed("class-order", row.study, row.donor_id, value), value))
        reservation = []
        covered = classes if row.quota >= len(classes) else classes[:row.quota]
        for label in covered:
            candidates = positions[local_classes == label]
            reservation.append(int(candidates[historical_keyed_seed("class-cover", row.study, row.donor_id, label) % len(candidates)]))
        reserved = set(reservation)
        first_remainder = np.asarray([value for value in positions if int(value) not in reserved], dtype=np.int64)
        np.random.default_rng(historical_keyed_seed("donor-cycle", row.study, row.donor_id, 0)).shuffle(first_remainder)
        parts = [np.asarray(reservation, dtype=np.int64), first_remainder]
        cycle = 1
        while sum(len(part) for part in parts) < row.quota:
            permutation = positions.copy()
            np.random.default_rng(historical_keyed_seed("donor-cycle", row.study, row.donor_id, cycle)).shuffle(permutation)
            parts.append(permutation)
            cycle += 1
        sequence = np.concatenate(parts)[:int(row.quota)]
        unique_first_length = min(len(positions), int(row.quota))
        if np.unique(sequence[:unique_first_length]).size != unique_first_length:
            raise RuntimeError(f"historical unique-first invariant failed: {row.study}/{row.donor_id}")
        sequences.append(sequence)
    tickets = np.repeat(np.arange(len(quota), dtype=np.int16), quota)
    np.random.default_rng(historical_keyed_seed("t1-phase-a", "donor-tickets")).shuffle(tickets)
    cursors = np.zeros(len(quota), dtype=np.int64)
    selected_rows = np.empty(total_presentations, dtype=np.int64)
    duplicate_repairs = 0
    active_rows = []
    for batch_start in range(0, len(tickets), EFFECTIVE_BATCH):
        used: set[int] = set()
        for position in range(batch_start, batch_start + EFFECTIVE_BATCH):
            donor_index = int(tickets[position])
            cell = int(sequences[donor_index][cursors[donor_index]])
            if cell in used:
                replacement = None
                for future in range(position + 1, len(tickets)):
                    other = int(tickets[future])
                    candidate = int(sequences[other][cursors[other]])
                    if candidate not in used:
                        replacement = future
                        break
                if replacement is None:
                    raise RuntimeError("historical scheduler could not repair same-update duplicate")
                tickets[position], tickets[replacement] = tickets[replacement], tickets[position]
                donor_index = int(tickets[position])
                cell = int(sequences[donor_index][cursors[donor_index]])
                duplicate_repairs += 1
            used.add(cell)
            selected_rows[position] = cell
            cursors[donor_index] += 1
        remaining = quota - cursors
        active_rows.append({"update": batch_start // EFFECTIVE_BATCH + 1, "active_donors_after_update": int(np.count_nonzero(remaining)), "exhausted_donors": int(np.count_nonzero(remaining == 0))})
    if not np.array_equal(cursors, quota):
        raise RuntimeError("historical donor quota consumption mismatch")
    schedule_frame = pd.DataFrame({
        "update": np.repeat(np.arange(1, cap_last + 1), EFFECTIVE_BATCH),
        "slot": np.tile(np.arange(EFFECTIVE_BATCH), cap_last),
        "inventory_row": selected_rows,
        "accepted_inventory_row": fit.accepted_inventory_row.to_numpy(np.int64)[selected_rows],
        "donor_id": fit.donor_id.astype(str).to_numpy()[selected_rows],
        "stable_mask_key": fit.stable_mask_key.to_numpy(np.int64)[selected_rows],
    })
    exposure_by_inventory_row = np.bincount(selected_rows, minlength=len(fit))
    if int(exposure_by_inventory_row.max()) > REPLAY_CAP:
        raise RuntimeError("historical schedule exceeded per-cell replay cap 8")
    donor_spreads = []
    for (_, _), positions in positions_by_donor.items():
        counts = exposure_by_inventory_row[np.asarray(positions, dtype=np.int64)]
        donor_spreads.append(int(counts.max() - counts.min()))
    if max(donor_spreads) > 1:
        raise RuntimeError("historical schedule within-donor exposure spread exceeds 1")
    if schedule_frame.groupby("update").stable_mask_key.nunique().min() != EFFECTIVE_BATCH:
        raise RuntimeError("historical schedule contains a same-update duplicate cell")
    schedule_frame.to_csv(stage / "t1_training_schedule.csv", index=False, lineterminator="\n")
    pd.DataFrame(active_rows).to_csv(stage / "t1_active_donor_count_by_update.csv", index=False, lineterminator="\n")
    donor_table["capacity_8N"] = REPLAY_CAP * donor_table.eligible_cells
    donor_table["capacity_binding_at_u205"] = donor_table.quota.eq(donor_table.capacity_8N)
    donor_table.to_csv(stage / "t1_historical_waterfill_donor_quotas.csv", index=False, lineterminator="\n")
    budget_rows = []
    donor_by_cell = fit.donor_id.astype(str).to_numpy()
    for checkpoint in (10, 25, 50, 100, 200, cap_last):
        budget = checkpoint * EFFECTIVE_BATCH
        local_quota = exact_waterfill(
            REPLAY_CAP * donor_table.eligible_cells.to_numpy(np.int64), budget, donor_table.label.tolist()
        )
        prefix_rows = schedule_frame.loc[schedule_frame["update"].le(checkpoint), "inventory_row"].to_numpy(np.int64)
        prefix_counts = np.bincount(prefix_rows, minlength=len(fit))
        prefix_donor = pd.Series(donor_by_cell[prefix_rows]).value_counts().reindex(donor_table.donor_id.astype(str), fill_value=0)
        budget_rows.append({
            "checkpoint_update": checkpoint,
            "presentations": budget,
            "independent_waterfill_binding_donors": int(np.sum(local_quota == REPLAY_CAP * donor_table.eligible_cells.to_numpy(np.int64))),
            "independent_waterfill_quota_min": int(local_quota.min()),
            "independent_waterfill_quota_median": float(np.median(local_quota)),
            "independent_waterfill_quota_max": int(local_quota.max()),
            "actual_prefix_donor_exposure_min": int(prefix_donor.min()),
            "actual_prefix_donor_exposure_median": float(prefix_donor.median()),
            "actual_prefix_donor_exposure_max": int(prefix_donor.max()),
            "actual_prefix_unique_cells": int(np.count_nonzero(prefix_counts)),
            "actual_prefix_cell_exposure_max": int(prefix_counts.max()),
            "actual_prefix_same_update_duplicates": 0,
        })
    pd.DataFrame(budget_rows).to_csv(stage / "t1_waterfill_budget_diagnostics.csv", index=False, lineterminator="\n")
    presentations = schedule_frame.groupby("stable_mask_key").size()
    source_lookup = fit.set_index("stable_mask_key")["source_family"]
    operator_lookup = fit.set_index("stable_mask_key")["matrix_id"]
    source_counts = schedule_frame.stable_mask_key.map(source_lookup).value_counts().sort_index().to_dict()
    operator_counts = schedule_frame.stable_mask_key.map(operator_lookup).value_counts().sort_index().to_dict()
    fit_counts = fit.groupby(fit.donor_id.astype(str)).size()
    equal_donors = sorted(fit_counts.index, key=lambda x: stable_digest(SEED, "donor-primary", x))
    equal_rows = {
        donor: sorted(group.index.tolist(), key=lambda i: stable_digest(SEED, "unique-first", fit.at[i, "stable_mask_key"]))
        for donor, group in fit.groupby(fit.donor_id.astype(str))
    }
    equal_cursors = {donor: 0 for donor in equal_donors}
    equal_exposure: dict[int, int] = {}
    offender = None
    stream_cursor = 0
    for _update in range(1, 15):
        for _slot in range(EFFECTIVE_BATCH):
            donor = equal_donors[stream_cursor % len(equal_donors)]
            stream_cursor += 1
            choices = equal_rows[donor]
            cell = choices[equal_cursors[donor] % len(choices)]
            equal_cursors[donor] += 1
            key = int(fit.at[cell, "stable_mask_key"])
            equal_exposure[key] = equal_exposure.get(key, 0) + 1
            if equal_exposure[key] == REPLAY_CAP + 1 and offender is None:
                offender = donor
    if offender is None:
        raise RuntimeError("failed to reproduce current equal-round-robin cap violation")
    summary = {
        "schema": "prod41k-t1-training-schedule-summary-historical-stage81b-cap8-v2",
        "historical_sampler_source_sha256": "253de32ccf30857baab7ecfa8ca51b97bb31fe6a18add4072c2e604a8900451f",
        "historical_semantics": "exact capacity-constrained donor waterfill q_d=min(8*N_d,lambda), native-class reservation, keyed without-replacement donor cycles, shuffled donor tickets, deterministic same-update duplicate repair",
        "complete_accepted_inventory_cells": int(len(full)),
        "complete_accepted_inventory_donors": int(full.donor_id.nunique()),
        "eligible_fit_cells": int(len(fit)),
        "eligible_fit_donors": int(fit.donor_id.nunique()),
        "scheduled_presentations": int(len(schedule_frame)),
        "replay_cap": REPLAY_CAP,
        "cap8_last_complete_update": cap_last,
        "maximum_presentations_at_cap8_last_complete_update": int(presentations.max()),
        "absolute_cap8_presentations": int(theoretical_presentations),
        "unused_cap8_presentations_below_full_batch": int(theoretical_presentations - total_presentations),
        "historical_duplicate_repairs": duplicate_repairs,
        "maximum_within_donor_exposure_spread": int(max(donor_spreads)),
        "fit_cells_per_donor": {"min": int(fit_counts.min()), "median": float(fit_counts.median()), "max": int(fit_counts.max())},
        "current_equal_round_robin_first_cap_violation_donor": offender,
        "current_equal_round_robin_first_cap_violation_donor_cells": int(fit_counts[offender]),
        "current_equal_round_robin_cap_safe_updates": 13,
        "historical_stage81b_cap_safe_updates": cap_last,
        "unique_cells_ever_presented": int(presentations.size),
        "fraction_fit_inventory_seen": float(presentations.size / len(fit)),
        "presentations_per_cell": {"min": int(presentations.min()), "median": float(presentations.median()), "max": int(presentations.max())},
        "cells_never_presented": int(len(fit) - presentations.size),
        "same_update_duplicates": int(EFFECTIVE_BATCH - schedule_frame.groupby("update").stable_mask_key.nunique().min()),
        "source_presentation_counts": {str(k): int(v) for k, v in source_counts.items()},
        "operator_presentation_counts": {str(k): int(v) for k, v in operator_counts.items()},
    }
    (stage / "t1_training_schedule_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    split_lookup = split.set_index("donor_id").reader_partition.astype(str)
    coverage = full.copy()
    coverage["reader_partition"] = coverage.donor_id.astype(str).map(split_lookup)
    if coverage.reader_partition.isna().any():
        raise RuntimeError("fit/heldout coverage contains unmapped donor")
    coverage_rows = []
    for role, take in (("encoder_fit", coverage.reader_partition.eq("reader_fit")), ("encoder_heldout", ~coverage.reader_partition.eq("reader_fit"))):
        subset = coverage.loc[take]
        for kind, column in (("source", "matrix_id"), ("operator", "matrix_id")):
            labels = subset[column].map(phase_e.source_family) if kind == "source" else subset[column]
            for label, indices in subset.groupby(labels).groups.items():
                group = subset.loc[indices]
                coverage_rows.append({"role": role, "stratum_type": kind, "stratum": str(label), "cells": len(group), "donors": group.donor_id.nunique()})
    pd.DataFrame(coverage_rows).to_csv(stage / "t1_fit_heldout_source_operator_coverage.csv", index=False, lineterminator="\n")

    evaluation = pd.read_csv(V5A / "biology_evaluation_cohort.csv")
    table = loader.cell_table().copy()
    table["accepted_inventory_row"] = np.arange(len(table), dtype=np.int64)
    table["loader_stable_mask_key"] = [
        phase_e.stable_key(row.matrix_id, row.local_row, row.cell_id) for row in table.itertuples()
    ]
    keys = ["operator_index", "matrix_id", "local_row"]
    audit = evaluation.merge(table, on=keys, how="left", suffixes=("_frozen", "_loader"), validate="one_to_one")
    identity_fields = ["donor_id", "cell_id", "broad_cell_class", "source_library"]
    for field in identity_fields:
        left = audit[f"{field}_frozen"].astype(str)
        right = audit[f"{field}_loader"].astype(str)
        audit[f"{field}_exact"] = left.eq(right)
    audit["all_identity_fields_exact"] = audit[[f"{x}_exact" for x in identity_fields]].all(axis=1)
    audit["computed_stable_mask_key"] = [
        phase_e.stable_key(row.matrix_id, row.local_row, row.cell_id_frozen) for row in audit.itertuples()
    ]
    audit["stable_mask_key_exact"] = audit.computed_stable_mask_key.astype(np.int64).eq(audit.loader_stable_mask_key.astype(np.int64))
    if len(audit) != 4_540 or not audit.all_identity_fields_exact.all() or not audit.stable_mask_key_exact.all():
        raise RuntimeError("4,540-cell source-row identity audit failed")
    audit.to_csv(stage / "t1_evaluation_cell_identity_audit.csv", index=False, lineterminator="\n")

    mask_rows = []
    packed_masks = []
    global_hash = hashlib.sha256()
    for begin in range(0, len(evaluation), 64):
        block = evaluation.iloc[begin:begin + 64]
        measurements = torch.from_numpy(
            np.stack([loader.states[str(matrix)] for matrix in block.matrix_id], axis=0)
        ).eq(int(MEASURED_SCALAR))
        stable_keys = torch.tensor([
            phase_e.stable_key(row.matrix_id, row.local_row, row.cell_id)
            for row in block.itertuples()
        ], dtype=torch.int64)
        masks = phase_e.sample_uniform_target_blocks(
            measurements,
            production_seed=SEED,
            cell_indices=stable_keys,
            sample_pass=PARTIAL_SAMPLE_PASS,
            view_index=PARTIAL_VIEW_INDEX,
            mask_fraction=0.40,
            block_count=16,
        ).hidden_mask
        if bool((masks & ~measurements).any()):
            raise RuntimeError("partial panel hides non-MEASURED_SCALAR address")
        expected = torch.floor(measurements.sum(1).float() * 0.40).long()
        if not torch.equal(masks.sum(1), expected):
            raise RuntimeError("partial panel hidden count is not floor(0.40 * measured)")
        packed_masks.append(np.packbits(masks.numpy(), axis=1, bitorder="little"))
        for offset, mask in enumerate(masks):
            payload = mask.numpy().tobytes()
            digest = hashlib.sha256(payload).hexdigest()
            global_hash.update(payload)
            row = block.iloc[offset]
            mask_rows.append({
                "biology_cell_index": int(row.biology_cell_index),
                "operator_index": int(row.operator_index),
                "matrix_id": str(row.matrix_id),
                "local_row": int(row.local_row),
                "cell_id": str(row.cell_id),
                "stable_mask_key": int(stable_keys[offset]),
                "sample_pass": PARTIAL_SAMPLE_PASS,
                "view_index": PARTIAL_VIEW_INDEX,
                "measured_count": int(measurements[offset].sum()),
                "hidden_count": int(mask.sum()),
                "mask_sha256": digest,
            })
    mask_frame = pd.DataFrame(mask_rows)
    mask_frame["bitorder"] = "little"
    mask_frame.to_csv(stage / "t1_partial_evidence_panel.csv", index=False, lineterminator="\n")
    np.savez_compressed(
        stage / "t1_partial_evidence_masks.npz",
        masks=np.concatenate(packed_masks, axis=0),
        biology_cell_index=evaluation.biology_cell_index.to_numpy(np.int64),
        address_count=np.array(phase_e.VOCABULARY_SIZE, dtype=np.int64),
        bitorder=np.array("little"),
    )
    (stage / "t1_partial_evidence_global_mask_sha256.txt").write_text(global_hash.hexdigest() + "\n", encoding="utf-8")

    registry = pd.read_csv(V5A / "program_registry.csv").set_index("program_name")
    innovation = registry.loc["innovation_tail"]
    rare_rows = []
    for endpoint in ("recurrent_5pct", "recurrent_1pct"):
        row = registry.loc[endpoint]
        exact = bool(
            row.raw_weight_sha256 == innovation.raw_weight_sha256
            and row.l2_weight_sha256 == innovation.l2_weight_sha256
        )
        if not exact:
            raise RuntimeError(f"frozen rare-to-innovation mapping failed for {endpoint}")
        rare_rows.append({
            "rare_endpoint": endpoint,
            "representation_program": "innovation_tail",
            "raw_weight_sha256": row.raw_weight_sha256,
            "l2_weight_sha256": row.l2_weight_sha256,
            "interpretation": row.interpretation,
            "mapping_exact": exact,
        })
    pd.DataFrame(rare_rows).to_csv(stage / "t1_rare_representation_mapping.csv", index=False, lineterminator="\n")
    generated = sorted(path for path in stage.iterdir() if path.is_file())
    status = {
        "schema": "prod41k-t1-v2-staged-publication-status",
        "status": "PASS_READY_TO_PUBLISH",
        "preconditions": PRECONDITION_HASHES,
        "artifacts": [{"name": path.name, "bytes": path.stat().st_size, "sha256": file_sha256(path)} for path in generated],
    }
    (stage / "T1_V2_GENERATION_STATUS.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    for row in status["artifacts"]:
        path = stage / row["name"]
        if path.stat().st_size != row["bytes"] or file_sha256(path) != row["sha256"]:
            raise RuntimeError(f"staged output verification failed: {path.name}")
    for path in generated:
        os.replace(path, OUT / path.name)
    status["status"] = "PUBLISHED_HASH_VERIFIED"
    published_status = stage / "T1_V2_GENERATION_STATUS.json"
    published_status.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    os.replace(published_status, OUT / published_status.name)
    stage.rmdir()
    print({
        "eligible_encoder_fit_cells": len(fit),
        "encoder_fit_donors": fit.donor_id.nunique(),
        "schedule_rows": len(schedule_frame),
        "cap8_last_complete_update": cap_last,
        "evaluation_identity_rows": len(audit),
        "partial_panel_rows": len(mask_frame),
        "partial_global_mask_sha256": global_hash.hexdigest(),
    })


if __name__ == "__main__":
    main()
