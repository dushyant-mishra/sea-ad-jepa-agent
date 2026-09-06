#!/usr/bin/env python3
"""Synthetic stand-in for ProductionTrainLoader, for the C2-v3 exact-path forensic.

This is the ONLY substitution v3 makes against the historical training path. It
reproduces the real loader's output contract exactly so that
`phase_e.run_update` can be called unmodified.

Reads no real expression, no pathology, no protected partition.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

ADDRESS_COUNT = 41_238
STRUCTURALLY_UNMEASURED = np.uint8(0)
MEASURED_SCALAR = np.uint8(1)
MEASURED_COLLISION_UNRESOLVED = np.uint8(2)


class SyntheticTrainLoader:
    """Emit values plus explicit observation states, deterministically per cell.

    Contract mirrored from `ProductionTrainLoader.load`:

    - `values` is ``float32 [n, ADDRESS_COUNT]``
    - `states` is ``uint8  [n, ADDRESS_COUNT]`` drawn from the three-state vocabulary
    - a state vector is a property of the source matrix, so every cell emitted by one
      operator shares it
    - no nonzero value may appear at a non-``MEASURED_SCALAR`` address, which
      `run_update` asserts directly
    """

    def __init__(
        self,
        *,
        seed: int,
        measured_fraction: float = 1.0,
        collision_fraction: float = 0.0,
        value_law: str = "log1p_exponential",
        value_scale: float = 1.0,
        zero_inflation: float = 0.0,
    ) -> None:
        if not 0.0 <= measured_fraction <= 1.0:
            raise ValueError("measured_fraction must be in [0, 1]")
        if not 0.0 <= collision_fraction <= 1.0:
            raise ValueError("collision_fraction must be in [0, 1]")
        if not 0.0 <= zero_inflation <= 1.0:
            raise ValueError("zero_inflation must be in [0, 1]")
        if measured_fraction + collision_fraction > 1.0:
            raise ValueError("measured and collision fractions cannot exceed all addresses")
        self.seed = int(seed)
        self.measured_fraction = float(measured_fraction)
        self.collision_fraction = float(collision_fraction)
        self.value_law = str(value_law)
        self.value_scale = float(value_scale)
        self.zero_inflation = float(zero_inflation)
        self._states = self._build_operator_states()

    def _build_operator_states(self) -> np.ndarray:
        """One operator-level state vector, shared by every cell it emits."""
        generator = np.random.default_rng(self.seed)
        states = np.full(ADDRESS_COUNT, STRUCTURALLY_UNMEASURED, dtype=np.uint8)
        order = generator.permutation(ADDRESS_COUNT)
        n_measured = int(round(self.measured_fraction * ADDRESS_COUNT))
        n_collision = int(round(self.collision_fraction * ADDRESS_COUNT))
        states[order[:n_measured]] = MEASURED_SCALAR
        states[order[n_measured:n_measured + n_collision]] = MEASURED_COLLISION_UNRESOLVED
        return states

    def _values_for_cell(self, key: int, measured: np.ndarray) -> np.ndarray:
        generator = np.random.default_rng((self.seed, int(key)))
        row = np.zeros(ADDRESS_COUNT, dtype=np.float32)
        count = int(measured.sum())
        if count == 0:
            return row
        if self.value_law == "log1p_exponential":
            draw = generator.exponential(scale=self.value_scale, size=count)
        elif self.value_law == "log1p_lognormal":
            draw = generator.lognormal(mean=0.0, sigma=self.value_scale, size=count)
        elif self.value_law == "uniform":
            draw = generator.uniform(0.0, self.value_scale, size=count)
        else:
            raise ValueError("unknown value_law: " + self.value_law)
        if self.value_law.startswith("log1p_"):
            draw = np.log1p(draw)
        if self.zero_inflation > 0.0:
            draw = np.where(generator.random(count) < self.zero_inflation, 0.0, draw)
        row[measured] = draw.astype(np.float32)
        return row

    def load(self, selected: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Return (values, states) for the selected rows, keyed by stable_mask_key."""
        values = np.zeros((len(selected), ADDRESS_COUNT), np.float32)
        states = np.zeros((len(selected), ADDRESS_COUNT), np.uint8)
        measured = self._states == MEASURED_SCALAR
        destinations = selected.loader_row.to_numpy(np.int64)
        keys = selected.stable_mask_key.to_numpy(np.int64)
        for destination, key in zip(destinations, keys):
            values[destination] = self._values_for_cell(int(key), measured)
            states[destination] = self._states
        # The invariant `run_update` asserts; fail here rather than deep in training.
        if np.any((states != MEASURED_SCALAR) & (values != 0.0)):
            raise RuntimeError("numeric value outside MEASURED_SCALAR")
        return values, states

    def manifest(self) -> dict[str, Any]:
        return {
            "schema": "c2-synthetic-train-loader-v3",
            "seed": self.seed,
            "address_count": ADDRESS_COUNT,
            "measured_fraction": self.measured_fraction,
            "collision_fraction": self.collision_fraction,
            "value_law": self.value_law,
            "value_scale": self.value_scale,
            "zero_inflation": self.zero_inflation,
            "measured_addresses": int((self._states == MEASURED_SCALAR).sum()),
            "reads_real_expression": False,
        }


def synthetic_cohort(n_cells: int, *, first_key: int = 1) -> pd.DataFrame:
    """A cohort with the columns `run_update` requires, and unique mask keys."""
    return pd.DataFrame(
        {
            "stable_mask_key": np.arange(first_key, first_key + n_cells, dtype=np.int64),
            "operator_index": np.zeros(n_cells, dtype=np.int64),
            "local_row": np.arange(n_cells, dtype=np.int64),
            "source_library": np.full(n_cells, 10_000.0, dtype=np.float32),
        }
    )
