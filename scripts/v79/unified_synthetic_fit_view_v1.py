from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

import numpy as np

from .unified_synthetic_integration_v1 import UnifiedBiologyWorld, world_as_latent_biology
from .v79_observation_operator import observe_latent_biology


@dataclass(frozen=True)
class UnifiedObservationConfig:
    source_mode: str = "balanced"  # balanced | shifted
    multimodal_mode: str = "same_nucleus"  # same_nucleus | separate_nucleus
    realization_family: str = "independent_thinning"
    molecule_scale: float = 3.0

    def __post_init__(self) -> None:
        if self.source_mode not in {"balanced", "shifted"}:
            raise ValueError("unknown source_mode")
        if self.multimodal_mode not in {"same_nucleus", "separate_nucleus"}:
            raise ValueError("unknown multimodal_mode")
        if self.realization_family not in {"independent_thinning", "conditional_multinomial"}:
            raise ValueError("unknown realization_family")
        if self.molecule_scale <= 0:
            raise ValueError("molecule_scale must be positive")


@dataclass(frozen=True)
class UnifiedFitView:
    world_hash: str
    counts_hash: str
    values: np.ndarray
    support: np.ndarray
    address_index: np.ndarray
    donor_id: np.ndarray
    source: np.ndarray
    operator: np.ndarray
    split: np.ndarray
    rna_entity_id: np.ndarray
    atac_entity_id: np.ndarray
    atac_donor_id: np.ndarray


def _source_labels(world: UnifiedBiologyWorld, mode: str) -> np.ndarray:
    donors = world.donor_id
    if mode == "balanced":
        donor_source = np.asarray(["SRC_A", "SRC_B", "SRC_C"], dtype=object)[np.arange(donors.max() + 1) % 3]
    else:
        # Same biology, altered acquisition composition only.
        donor_source = np.asarray(["SRC_B", "SRC_B", "SRC_C", "SRC_A"], dtype=object)[np.arange(donors.max() + 1) % 4]
    return donor_source[donors].astype(str)


def _observation_authority(n_genes: int, source_mode: str, family: str, scale: float) -> dict[str, object]:
    support = np.ones((3, n_genes), dtype=bool)
    support[1, ::5] = False
    support[2, ::7] = False
    if source_mode == "balanced":
        means = [-0.25, -0.45, -0.65]
        sds = [0.15, 0.18, 0.20]
    else:
        means = [-0.35, -0.85, -0.55]
        sds = [0.18, 0.25, 0.20]
    return {
        "regime_ids": ["SRC_A", "SRC_B", "SRC_C"],
        "structural_support": support.tolist(),
        "capture_log_mean": means,
        "capture_log_sd": sds,
        "gene_propensity": np.linspace(0.75, 1.25, n_genes).tolist(),
        "realization_family": family,
        "molecule_scale": scale,
    }


def _donor_splits(donor_id: np.ndarray) -> np.ndarray:
    labels = np.empty(len(donor_id), dtype=object)
    for d in np.unique(donor_id):
        if int(d) % 5 == 0:
            split = "test"
        elif int(d) % 5 == 1:
            split = "val"
        else:
            split = "train"
        labels[donor_id == d] = split
    return labels.astype(str)


def _counts_hash(values: np.ndarray, support: np.ndarray) -> str:
    h = sha256()
    h.update(np.ascontiguousarray(values).view(np.uint8))
    h.update(np.ascontiguousarray(support).view(np.uint8))
    return h.hexdigest()


def observe_unified_world(world: UnifiedBiologyWorld, config: UnifiedObservationConfig, *, seed: int) -> UnifiedFitView:
    latent = world_as_latent_biology(world)
    source = _source_labels(world, config.source_mode)
    authority = _observation_authority(
        world.expected_molecular_state.shape[1], config.source_mode, config.realization_family, config.molecule_scale
    )
    observed = observe_latent_biology(latent, authority, source, int(seed))
    values = observed.counts.toarray().astype(np.int64)
    support = np.asarray(observed.structural_support, dtype=bool)
    address_index = np.arange(values.shape[1], dtype=np.int64)
    donor_id = world.donor_id.copy()
    split = _donor_splits(donor_id)
    operator = np.asarray(["RNA_V79"] * len(donor_id), dtype=str)
    rna_entity_id = np.asarray([f"D{int(d):04d}:RNA:{i:06d}" for i, d in enumerate(donor_id)], dtype=str)
    if config.multimodal_mode == "same_nucleus":
        atac_entity_id = rna_entity_id.copy()
    else:
        atac_entity_id = np.asarray([f"D{int(d):04d}:ATAC:{i:06d}" for i, d in enumerate(donor_id)], dtype=str)
    atac_donor_id = donor_id.copy()
    for arr in (values, support, address_index, donor_id, source, operator, split, rna_entity_id, atac_entity_id, atac_donor_id):
        arr.setflags(write=False)
    return UnifiedFitView(
        world_hash=world.world_hash,
        counts_hash=_counts_hash(values, support),
        values=values,
        support=support,
        address_index=address_index,
        donor_id=donor_id,
        source=source,
        operator=operator,
        split=split,
        rna_entity_id=rna_entity_id,
        atac_entity_id=atac_entity_id,
        atac_donor_id=atac_donor_id,
    )


def serialize_fit_view(view: UnifiedFitView) -> dict[str, object]:
    return {
        "schema": "UNIFIED_SYNTHETIC_FIT_VIEW_V1",
        "world_sha256": view.world_hash,
        "counts_sha256": view.counts_hash,
        "address_index": view.address_index.tolist(),
        "donor_id": view.donor_id.tolist(),
        "source": view.source.tolist(),
        "operator": view.operator.tolist(),
        "support": view.support.tolist(),
        "values": view.values.tolist(),
        "split": view.split.tolist(),
        "rna_entity_id": view.rna_entity_id.tolist(),
        "atac_entity_id": view.atac_entity_id.tolist(),
        "atac_donor_id": view.atac_donor_id.tolist(),
    }


def fit_view_sha256(view: UnifiedFitView) -> str:
    raw = json.dumps(serialize_fit_view(view), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(raw).hexdigest()
