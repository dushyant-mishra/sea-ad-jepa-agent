"""Frozen healthy-teacher schedule/inventory adapter.

This module materializes exactly one already-selected 128-cell schedule update.
It never samples donors or cells and cannot expand the frozen reader-fit corpus.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

FROZEN_INVENTORY_SHA256 = "7ac13973162a46cafa5baa24c5bea14beb64bd5859e8f58900801eee07083a30"
FROZEN_SCHEDULE_SHA256 = "4657d669658712234d7ee8ede9496297009b808d4902766a9e43f7591ca640fc"
FROZEN_READER_SPLIT_SHA256 = "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511"
EFFECTIVE_BATCH = 128
MAX_UPDATE = 205


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class FrozenHealthyTeacherBatchSource:
    def __init__(
        self,
        *,
        loader: Any,
        inventory_path: Path,
        schedule_path: Path,
        reader_split_path: Path,
    ) -> None:
        if sha256(inventory_path) != FROZEN_INVENTORY_SHA256:
            raise RuntimeError("healthy-teacher inventory SHA-256 mismatch")
        if sha256(schedule_path) != FROZEN_SCHEDULE_SHA256:
            raise RuntimeError("healthy-teacher schedule SHA-256 mismatch")
        if sha256(reader_split_path) != FROZEN_READER_SPLIT_SHA256:
            raise RuntimeError("reader split SHA-256 mismatch")

        self.loader = loader
        self.inventory = pd.read_csv(inventory_path)
        self.schedule = pd.read_csv(schedule_path)
        self.reader_split = pd.read_csv(reader_split_path)

        fit_donors = set(
            self.reader_split.loc[
                self.reader_split["reader_partition"].eq("reader_fit"), "donor_id"
            ].astype(str)
        )
        if len(fit_donors) != 104:
            raise RuntimeError("reader_fit donor count mismatch")
        if len(self.inventory) != 3_292:
            raise RuntimeError("healthy-teacher inventory row count mismatch")
        if self.inventory["donor_id"].astype(str).nunique() != 104:
            raise RuntimeError("healthy-teacher inventory donor count mismatch")
        if set(self.inventory["donor_id"].astype(str)) != fit_donors:
            raise RuntimeError("healthy-teacher inventory is not exactly reader_fit")
        if self.inventory["stable_mask_key"].duplicated().any():
            raise RuntimeError("healthy-teacher inventory stable-key duplication")

        if len(self.schedule) != 26_240:
            raise RuntimeError("healthy-teacher schedule presentation count mismatch")
        if self.schedule["update"].min() != 1 or self.schedule["update"].max() != MAX_UPDATE:
            raise RuntimeError("healthy-teacher schedule update range mismatch")
        grouped = self.schedule.groupby("update", sort=False)
        if not (grouped.size() == EFFECTIVE_BATCH).all():
            raise RuntimeError("schedule does not contain 128 rows per update")
        if grouped["stable_mask_key"].nunique().min() != EFFECTIVE_BATCH:
            raise RuntimeError("same-update cell duplication in frozen schedule")
        if self.schedule.groupby("stable_mask_key").size().max() > 8:
            raise RuntimeError("frozen schedule exceeds cap 8")

        table = loader.cell_table().reset_index().rename(
            columns={"index": "accepted_inventory_row"}
        )
        if len(table) <= int(self.inventory["accepted_inventory_row"].max()):
            raise RuntimeError("inventory references loader row outside current table")
        authoritative = table.iloc[
            self.inventory["accepted_inventory_row"].to_numpy(np.int64)
        ].reset_index(drop=True)
        for column in ("operator_index", "matrix_id", "local_row", "donor_id", "cell_id"):
            if not authoritative[column].astype(str).eq(
                self.inventory[column].astype(str)
            ).all():
                raise RuntimeError(f"inventory/loader identity mismatch: {column}")

    def materialize(self, update: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict[str, Any]]:
        update = int(update)
        if not 1 <= update <= MAX_UPDATE:
            raise ValueError("update must be in 1..205")
        selected = self.schedule.loc[self.schedule["update"].eq(update)].sort_values("slot")
        if selected["slot"].tolist() != list(range(EFFECTIVE_BATCH)):
            raise RuntimeError("frozen schedule slots are not exactly 0..127")
        rows = self.inventory.iloc[
            selected["inventory_row"].to_numpy(np.int64)
        ].copy().reset_index(drop=True)
        if not rows["stable_mask_key"].astype(np.int64).eq(
            selected["stable_mask_key"].astype(np.int64).reset_index(drop=True)
        ).all():
            raise RuntimeError("schedule/inventory stable-key mismatch")
        rows["loader_row"] = np.arange(EFFECTIVE_BATCH, dtype=np.int64)
        values_np, states_np = self.loader.load(rows)
        measured_scalar = states_np == np.uint8(1)
        if np.any((states_np != np.uint8(1)) & (values_np != 0.0)):
            raise RuntimeError("numeric value outside MEASURED_SCALAR")
        expression = torch.from_numpy(values_np.astype(np.float32, copy=False))
        measurement = torch.from_numpy(measured_scalar)
        keys = torch.tensor(rows["stable_mask_key"].to_numpy(np.int64), dtype=torch.int64)
        provenance = {
            "update": update,
            "stable_mask_keys": keys.tolist(),
            "donors": sorted(rows["donor_id"].astype(str).unique().tolist()),
            "operator_indices": sorted(rows["operator_index"].astype(int).unique().tolist()),
        }
        return expression, measurement, keys, provenance
