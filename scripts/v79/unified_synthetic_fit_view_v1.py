from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

import numpy as np

from .unified_synthetic_integration_v1 import UnifiedBiologyWorld, world_as_latent_biology
from .v79_observation_operator import observe_latent_biology
from .v79_rare_biology_generator_v1 import REGIMES, SIGNS, SOURCES, VISIBILITY


@dataclass(frozen=True)
class UnifiedObservationConfig:
    source_mode: str = "balanced"  # balanced | shifted
    multimodal_mode: str = "same_nucleus"  # same_nucleus | separate_nucleus
    realization_family: str = "independent_thinning"
    molecule_scale: float = 3.0
    technical_pseudo_rarity: bool = True
    atac_noise_scale: float = 0.35

    def __post_init__(self) -> None:
        if self.source_mode not in {"balanced", "shifted"}:
            raise ValueError("unknown source_mode")
        if self.multimodal_mode not in {"same_nucleus", "separate_nucleus"}:
            raise ValueError("unknown multimodal_mode")
        if self.realization_family not in {"independent_thinning", "conditional_multinomial"}:
            raise ValueError("unknown realization_family")
        if self.molecule_scale <= 0 or self.atac_noise_scale < 0:
            raise ValueError("observation scales must be valid")


@dataclass(frozen=True)
class UnifiedFitView:
    world_hash: str
    counts_hash: str
    values: np.ndarray
    atac_values: np.ndarray
    context_true: np.ndarray
    context_shuffled: np.ndarray
    context_distant: np.ndarray
    support: np.ndarray
    address_index: np.ndarray
    donor_id: np.ndarray
    source: np.ndarray
    operator: np.ndarray
    split: np.ndarray
    perturbation_arm: np.ndarray
    rna_entity_id: np.ndarray
    atac_entity_id: np.ndarray
    atac_donor_id: np.ndarray


def _source_labels(world: UnifiedBiologyWorld, mode: str) -> np.ndarray:
    donors = world.donor_id
    if mode == "balanced":
        donor_source = np.asarray(SOURCES, dtype=object)[np.arange(donors.max() + 1) % len(SOURCES)]
    else:
        # Same latent biology with a different acquisition mix only.
        shifted = np.asarray([SOURCES[1], SOURCES[1], SOURCES[2], SOURCES[0]], dtype=object)
        donor_source = shifted[np.arange(donors.max() + 1) % len(shifted)]
    return donor_source[donors].astype(str)


def _tile_visibility(n_genes: int) -> np.ndarray:
    base = np.stack([VISIBILITY[s] for s in SOURCES], axis=0)
    reps = int(np.ceil(n_genes / base.shape[1]))
    return np.tile(base, (1, reps))[:, :n_genes]


def _observation_authority(n_genes: int, source_mode: str, family: str, scale: float) -> dict[str, object]:
    # Reuse PR311 source visibility as positional acquisition structure while V79
    # remains the count-realization operator. This affects observation, never biology.
    vis = _tile_visibility(n_genes)
    support = vis > 0
    # Keep a minimal common support so every source has lawful measured addresses.
    support[:, 0] = True
    propensity = np.clip(vis.mean(axis=0) + 0.20, 0.05, None)
    if source_mode == "balanced":
        means = [-0.25, -0.45, -0.65]
        sds = [0.15, 0.18, 0.20]
    else:
        means = [-0.35, -0.85, -0.55]
        sds = [0.18, 0.25, 0.20]
    return {
        "regime_ids": list(SOURCES),
        "structural_support": support.tolist(),
        "capture_log_mean": means,
        "capture_log_sd": sds,
        "gene_propensity": propensity.tolist(),
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


def _observable_hash(*arrays: np.ndarray) -> str:
    h = sha256()
    for arr in arrays:
        a = np.ascontiguousarray(arr)
        h.update(str(a.dtype).encode("ascii"))
        h.update(json.dumps(a.shape).encode("ascii"))
        h.update(a.view(np.uint8))
    return h.hexdigest()


def _program_signal(program_activity: np.ndarray, n_genes: int) -> np.ndarray:
    n_cells, n_programs = program_activity.shape
    out = np.zeros((n_cells, n_genes), dtype=np.float64)
    width = min(len(SIGNS), n_genes)
    signs = np.abs(np.asarray(SIGNS[:width], dtype=float))
    for p in range(n_programs):
        genes = (np.arange(width) + p * width) % n_genes
        out[np.ix_(program_activity[:, p], genes)] += signs[None, :]
    return out


def _atac_realization(world: UnifiedBiologyWorld, mode: str, rng: np.random.Generator, n_genes: int, noise: float) -> np.ndarray:
    if mode == "same_nucleus":
        activity = np.asarray(world.rare_program_activity, dtype=bool)
    else:
        # PR311 separate-nucleus semantics: independent nuclei share donor-level
        # prevalence but not focal-cell state or identity.
        activity = np.zeros_like(world.rare_program_activity, dtype=bool)
        for p in range(activity.shape[1]):
            probs = world.rare_donor_prevalence[world.donor_id, p]
            activity[:, p] = rng.binomial(1, probs).astype(bool)
    latent_signal = _program_signal(activity, n_genes)
    # Broad expected chromatin accessibility tracks coarse molecular abundance;
    # rare-program signal creates the same-nucleus increment.
    coarse = np.log1p(np.asarray(world.expected_molecular_state, dtype=float)) * 0.20
    if mode == "separate_nucleus":
        # Break focal-cell coupling while preserving donor-level abundance scale.
        donor_means = np.zeros_like(coarse)
        for donor in np.unique(world.donor_id):
            ix = np.flatnonzero(world.donor_id == donor)
            donor_means[ix] = coarse[ix].mean(axis=0)
        coarse = donor_means
    atac = coarse + 0.85 * latent_signal + rng.normal(0.0, noise, coarse.shape)
    return atac.astype(np.float32)


def _apply_technical_pseudo_rarity(values: np.ndarray, support: np.ndarray, world: UnifiedBiologyWorld,
                                   rng: np.random.Generator) -> np.ndarray:
    out = values.copy()
    eligible = ~np.asarray(world.rare_activity, dtype=bool)
    rate = float(REGIMES["central"]["tail_fraction"])
    pseudo = eligible & (rng.random(len(eligible)) < rate)
    width = min(len(SIGNS), out.shape[1])
    if pseudo.any() and width:
        effect = rng.poisson(2.0, size=(int(pseudo.sum()), width)).astype(out.dtype) + 1
        rows = np.flatnonzero(pseudo)
        for local, row in enumerate(rows):
            cols = np.arange(width)
            measured = support[row, cols]
            out[row, cols[measured]] += effect[local, measured]
    return out


def _context_views(values: np.ndarray, donor_id: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    true = np.zeros_like(values, dtype=np.float32)
    shuffled = np.zeros_like(values, dtype=np.float32)
    distant = np.zeros_like(values, dtype=np.float32)
    for donor in np.unique(donor_id):
        ix = np.flatnonzero(donor_id == donor)
        n = len(ix)
        if n == 1:
            true[ix[0]] = values[ix[0]]
            shuffled[ix[0]] = values[ix[0]]
            distant[ix[0]] = values[ix[0]]
            continue
        for pos, row in enumerate(ix):
            left = ix[(pos - 1) % n]; right = ix[(pos + 1) % n]
            true[row] = (values[left] + values[right]) / 2.0
            dpos = (pos + n // 2) % n
            distant[row] = (values[ix[(dpos - 1) % n]] + values[ix[(dpos + 1) % n]]) / 2.0
            forbidden = {pos, (pos - 1) % n, (pos + 1) % n}
            candidates = [j for j in range(n) if j not in forbidden]
            if candidates:
                j = int(rng.choice(np.asarray(candidates, dtype=int)))
                shuffled[row] = (values[ix[(j - 1) % n]] + values[ix[(j + 1) % n]]) / 2.0
            else:
                shuffled[row] = distant[row]
    return true, shuffled, distant


def observe_unified_world(world: UnifiedBiologyWorld, config: UnifiedObservationConfig, *, seed: int) -> UnifiedFitView:
    latent = world_as_latent_biology(world)
    source = _source_labels(world, config.source_mode)
    authority = _observation_authority(
        world.expected_molecular_state.shape[1], config.source_mode, config.realization_family, config.molecule_scale
    )
    observed = observe_latent_biology(latent, authority, source, int(seed))
    values = observed.counts.toarray().astype(np.int64)
    support = np.asarray(observed.structural_support, dtype=bool)
    rng = np.random.default_rng(int(seed) + 9091)
    if config.technical_pseudo_rarity:
        values = _apply_technical_pseudo_rarity(values, support, world, rng)
    atac_values = _atac_realization(world, config.multimodal_mode, rng, values.shape[1], config.atac_noise_scale)
    context_true, context_shuffled, context_distant = _context_views(values, world.donor_id, rng)
    address_index = np.arange(values.shape[1], dtype=np.int64)
    donor_id = world.donor_id.copy()
    split = _donor_splits(donor_id)
    operator = np.asarray(["RNA_V79_PR311"] * len(donor_id), dtype=str)
    rna_entity_id = np.asarray([f"D{int(d):04d}:RNA:{i:06d}" for i, d in enumerate(donor_id)], dtype=str)
    if config.multimodal_mode == "same_nucleus":
        atac_entity_id = rna_entity_id.copy()
    else:
        atac_entity_id = np.asarray([f"D{int(d):04d}:ATAC:{i:06d}" for i, d in enumerate(donor_id)], dtype=str)
    atac_donor_id = donor_id.copy()
    perturbation_arm = world.perturbation_arm.copy()
    for arr in (values, atac_values, context_true, context_shuffled, context_distant, support, address_index,
                donor_id, source, operator, split, perturbation_arm, rna_entity_id, atac_entity_id, atac_donor_id):
        arr.setflags(write=False)
    return UnifiedFitView(
        world_hash=world.world_hash,
        counts_hash=_observable_hash(values, support, atac_values, context_true, context_shuffled, context_distant),
        values=values,
        atac_values=atac_values,
        context_true=context_true,
        context_shuffled=context_shuffled,
        context_distant=context_distant,
        support=support,
        address_index=address_index,
        donor_id=donor_id,
        source=source,
        operator=operator,
        split=split,
        perturbation_arm=perturbation_arm,
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
        "atac_values": view.atac_values.tolist(),
        "context_true": view.context_true.tolist(),
        "context_shuffled": view.context_shuffled.tolist(),
        "context_distant": view.context_distant.tolist(),
        "perturbation_arm": view.perturbation_arm.tolist(),
        "split": view.split.tolist(),
        "rna_entity_id": view.rna_entity_id.tolist(),
        "atac_entity_id": view.atac_entity_id.tolist(),
        "atac_donor_id": view.atac_donor_id.tolist(),
    }


def fit_view_sha256(view: UnifiedFitView) -> str:
    raw = json.dumps(serialize_fit_view(view), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(raw).hexdigest()
