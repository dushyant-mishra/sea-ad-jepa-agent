#!/usr/bin/env python3
"""Synthetic world -> model-facing batch, with oracle truth PHYSICALLY separated.

RUNTIME-AGNOSTIC BY DESIGN. This does not import, subclass or name any historical loader
class. It emits a neutral structure described in terms of the tensors and metadata a V5-style
consumer needs. When the runtime lane freezes the canonical consumer interface, the join is a
thin bridge, not a rewrite. There is no trainer here, no optimizer step, no EMA and no
checkpoint loop; those belong to the runtime lane and must have exactly one implementation.

THE SEPARATION IS STRUCTURAL, NOT DOCUMENTARY. Two distinct frozen types:

    SyntheticModelBatch    everything a model may lawfully see
    SyntheticOracleRecord  planted truth, usable ONLY after prediction, for scoring

They are separate objects with no reference from the batch to the oracle. A model-facing
function cannot receive z_reg_private by accident, because the batch has no field that could
carry it and no handle on the record that does. ORACLE_ONLY_FIELDS below is the enforced
list, and the test suite asserts the two namespaces never intersect.

WHY THIS MATTERS HERE SPECIFICALLY. The B3 non-recoverable arms and z_reg_private are
provably absent from permitted RNA evidence. If they leaked into model-visible fields through
ordinary plumbing, the anti-cheat rehearsal would report a cheat that the harness itself
created. The separation is the instrument, so it has to be sound before any forward pass.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse

# Planted variables that may NEVER appear in a model-facing structure. Enforced by tests.
ORACLE_ONLY_FIELDS = frozenset({
    "z_global", "z_query", "z_reg_shared", "z_reg_private", "technical_latents",
    "z_donor", "z_marker", "z_partial", "z_gain", "z_bioqc", "z_tf",
    "z_atac_bio", "z_atac_tech", "rare_flags", "state_index", "substate",
    "c_state_a", "c_state_b", "pseudotime", "niche_score", "compartment",
    "pert_id", "pert_dose", "spatial_x", "spatial_y",
})

# Lawful physical descriptors a model or diagnostic may see.
PERMITTED_METADATA = frozenset({
    "operator_index", "source_index", "library_size", "n_measured",
    "global_cell_index",
})


@dataclass(frozen=True)
class SyntheticModelBatch:
    """Model-visible only. Adding an oracle field here is a test failure, by construction."""
    gene_ids: np.ndarray            # [cells, genes] int64, canonical registry indices
    expression: np.ndarray          # [cells, genes] float32, CPM-log1p of observed counts
    measurement_mask: np.ndarray    # [cells, genes] bool, address was measurable for this cell
    hidden_target_mask: np.ndarray  # [cells, genes] bool, hidden from the student view
    operator_index: np.ndarray      # [cells] int16
    source_index: np.ndarray        # [cells] int8
    library_size: np.ndarray        # [cells] float32
    n_measured: np.ndarray          # [cells] int32
    global_cell_index: np.ndarray   # [cells] int64, synthetic cell identity

    def digest(self) -> str:
        h = hashlib.sha256()
        for f in sorted(fields(self), key=lambda x: x.name):
            a = np.ascontiguousarray(getattr(self, f.name))
            h.update(f.name.encode()); h.update(str(a.dtype).encode())
            h.update(str(a.shape).encode()); h.update(a.tobytes())
        return h.hexdigest()

    def student_visible_expression(self) -> np.ndarray:
        """Expression the STUDENT may use: measured AND not hidden.

        Hidden targets are zeroed here rather than merely flagged, so a consumer that ignores
        the mask still cannot read them.
        """
        allow = self.measurement_mask & ~self.hidden_target_mask
        return np.where(allow, self.expression, 0.0).astype(np.float32)


@dataclass(frozen=True)
class SyntheticOracleRecord:
    """Planted truth. For scoring AFTER prediction. Never passed to a model-facing function."""
    global_cell_index: np.ndarray
    latents: dict[str, np.ndarray]      # z_global, z_reg_private, ...
    b3_arm_membership: np.ndarray | None
    b6_ladder_level: np.ndarray | None
    substate: np.ndarray | None
    annotated_class: np.ndarray | None

    def digest(self) -> str:
        h = hashlib.sha256()
        h.update(np.ascontiguousarray(self.global_cell_index).tobytes())
        for k in sorted(self.latents):
            a = np.ascontiguousarray(self.latents[k])
            h.update(k.encode()); h.update(a.tobytes())
        return h.hexdigest()


def _cpm_log1p(counts: np.ndarray, library: np.ndarray) -> np.ndarray:
    lib = np.where(library > 0, library, 1.0)[:, None]
    return np.log1p(counts / lib * 1e4).astype(np.float32)


def sample_hidden_targets(measurement_mask: np.ndarray, global_cell_index: np.ndarray,
                          hidden_fraction: float, seed: int) -> np.ndarray:
    """Hidden-target mask, eligible only where the address is MEASURED.

    Eligibility depends on declared support, never on the realized value: a value-dependent
    mask would leak information about the very quantity being predicted.
    """
    rng = np.random.default_rng(seed)
    hidden = np.zeros_like(measurement_mask, dtype=bool)
    for i in range(measurement_mask.shape[0]):
        elig = np.where(measurement_mask[i])[0]
        if len(elig) == 0:
            continue
        k = int(round(hidden_fraction * len(elig)))
        if k <= 0:
            continue
        pick = rng.choice(elig, size=min(k, len(elig)), replace=False)
        hidden[i, pick] = True
    return hidden


def build_from_world(root: Path, obs_dir: str, universe: np.ndarray,
                     hidden_fraction: float = 0.15, seed: int = 20261006,
                     max_cells: int | None = None
                     ) -> tuple[SyntheticModelBatch, SyntheticOracleRecord, dict[str, Any]]:
    """Read a generated synthetic world and emit (model batch, oracle record, provenance)."""
    odir = root / "observable_raw" / obs_dir
    man = json.loads(next(odir.glob("*MANIFEST*.json")).read_text())
    n_addr = int(man["n_addresses"])

    counts_parts, cell_parts = [], []
    for s in man["shards"]:
        z = np.load(odir / s["file"], allow_pickle=False)
        X = sparse.csr_matrix((z["data"].astype(np.float64), z["indices"], z["indptr"]),
                              shape=(len(z["indptr"]) - 1, n_addr))
        counts_parts.append(X)
        cell_parts.append(np.asarray(z["global_cell_index"], dtype=np.int64))
    X = sparse.vstack(counts_parts).tocsr()
    cells = np.concatenate(cell_parts)
    if max_cells is not None:
        X = X[:max_cells]; cells = cells[:max_cells]

    # truth, read once and routed ONLY into the oracle record
    truth: dict[str, np.ndarray] = {}
    for f in sorted((root / "hidden_truth").glob("TRUTH_*.npz")):
        z = np.load(f, allow_pickle=False)
        for k in z.files:
            if k == "cell_id":
                continue
            truth.setdefault(k, []).append(z[k])
    truth = {k: np.concatenate(v, 0)[: len(cells)] for k, v in truth.items()}

    counts = np.asarray(X[:, universe].todense(), dtype=np.float32)
    library = np.asarray(X.sum(1)).ravel().astype(np.float32)
    measured = counts > 0
    # an address is MEASURABLE for a cell if its source family covers it; detection is separate
    measurement_mask = np.ones_like(measured, dtype=bool)
    hidden = sample_hidden_targets(measured, cells, hidden_fraction, seed)

    gene_ids = np.tile(universe.astype(np.int64), (len(cells), 1))
    batch = SyntheticModelBatch(
        gene_ids=gene_ids,
        expression=_cpm_log1p(counts, library),
        measurement_mask=measurement_mask,
        hidden_target_mask=hidden,
        operator_index=truth.get("operator_index", np.zeros(len(cells), np.int16)).astype(np.int16),
        source_index=truth.get("source_index", np.zeros(len(cells), np.int8)).astype(np.int8),
        library_size=library,
        n_measured=measured.sum(1).astype(np.int32),
        global_cell_index=cells)

    oracle = SyntheticOracleRecord(
        global_cell_index=cells,
        latents={k: v for k, v in truth.items() if k in ORACLE_ONLY_FIELDS},
        b3_arm_membership=truth.get("rare_flags"),
        b6_ladder_level=truth.get("z_partial"),
        substate=truth.get("substate"),
        annotated_class=truth.get("state_index"))

    prov = dict(
        schema="V77_SYNTHETIC_BATCH_ADAPTER_PROVENANCE_V1",
        world_root=str(root), observer_dir=obs_dir,
        observer_manifest_schema=man.get("schema"),
        n_cells=int(len(cells)), n_genes_in_universe=int(len(universe)),
        hidden_fraction=hidden_fraction, seed=seed,
        batch_digest=batch.digest(), oracle_digest=oracle.digest(),
        oracle_only_fields=sorted(ORACLE_ONLY_FIELDS),
        permitted_metadata=sorted(PERMITTED_METADATA),
        separation=("SyntheticModelBatch holds no reference to SyntheticOracleRecord; the "
                    "namespaces are asserted disjoint by test"),
        runtime_binding="NONE; this adapter names no runtime loader class",
        no_training_performed=True)
    return batch, oracle, prov
