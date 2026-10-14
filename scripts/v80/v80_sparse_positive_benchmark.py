from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from typing import Iterable

import numpy as np


FAMILIES = (
    "SP00_BALANCED_ESTIMABLE",
    "SP01_ULTRASPARSE_ESTIMABLE",
    "SP02_DONOR_IMBALANCED_ESTIMABLE",
    "SP03_SOURCE_SHIFT_ESTIMABLE",
    "SP04_SUPPORT_THINNED_ESTIMABLE",
    "SP05_NO_POSITIVE_SUPPORT_NOT_ESTIMABLE",
    "SP06_RANK_DEFICIENT_NOT_ESTIMABLE",
    "SP07_NEW_DONOR_ESTIMABLE",
)

ESTIMABLE = "ESTIMABLE"
NOT_ESTIMABLE = "NOT_ESTIMABLE_BY_CONSTRUCTION"


@dataclass(frozen=True)
class SparsePositiveConfig:
    n_genes: int = 24
    n_donors: int = 24
    cells_per_donor: int = 80

    @property
    def n_cells(self) -> int:
        return self.n_donors * self.cells_per_donor


@dataclass(frozen=True)
class SparsePositiveWorld:
    family: str
    opaque_id: str
    estimability_truth: str
    donor_id: np.ndarray
    source: np.ndarray
    cell_class: np.ndarray
    depth_z: np.ndarray
    split: np.ndarray
    design_matrix: np.ndarray
    support: np.ndarray
    detected: np.ndarray
    positive_value: np.ndarray
    latent_detection_intercept: np.ndarray
    latent_positive_location: np.ndarray


def _canon(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _logit(p: float) -> float:
    return float(np.log(p / (1.0 - p)))


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30.0, 30.0)))


def _opaque_id(seed_root: int, family_index: int) -> str:
    return sha256(f"V80:{int(seed_root)}:{int(family_index)}".encode("ascii")).hexdigest()[:24]


def _split_from_donor(donor_id: np.ndarray) -> np.ndarray:
    out = np.empty(len(donor_id), dtype=object)
    for donor in np.unique(donor_id):
        label = "test" if int(donor) % 5 == 0 else "train"
        out[donor_id == donor] = label
    return out.astype(str)


def _family_base_rate(family: str) -> float:
    return {
        "SP00_BALANCED_ESTIMABLE": 0.080,
        "SP01_ULTRASPARSE_ESTIMABLE": 0.025,
        "SP02_DONOR_IMBALANCED_ESTIMABLE": 0.055,
        "SP03_SOURCE_SHIFT_ESTIMABLE": 0.045,
        "SP04_SUPPORT_THINNED_ESTIMABLE": 0.070,
        "SP05_NO_POSITIVE_SUPPORT_NOT_ESTIMABLE": 0.000,
        "SP06_RANK_DEFICIENT_NOT_ESTIMABLE": 0.080,
        "SP07_NEW_DONOR_ESTIMABLE": 0.050,
    }[family]


def _make_world(config: SparsePositiveConfig, seed_root: int, family_index: int, family: str) -> SparsePositiveWorld:
    rng = np.random.default_rng(int(seed_root) + 1009 * (family_index + 1))
    n_cells = config.n_cells
    donor_id = np.repeat(np.arange(config.n_donors, dtype=np.int64), config.cells_per_donor)
    within = np.tile(np.arange(config.cells_per_donor, dtype=np.int64), config.n_donors)
    cell_class = (within % 2).astype(np.int8)
    source = (donor_id % 2).astype(np.int8)
    if family == "SP06_RANK_DEFICIENT_NOT_ESTIMABLE":
        source = cell_class.copy()
    depth_z = rng.normal(0.0, 1.0, n_cells).astype(np.float64)
    design = np.column_stack([
        np.ones(n_cells, dtype=np.float64),
        depth_z,
        cell_class.astype(np.float64),
        source.astype(np.float64),
    ])
    split = _split_from_donor(donor_id)

    n_genes = config.n_genes
    support = np.ones((n_cells, n_genes), dtype=bool)
    if family == "SP04_SUPPORT_THINNED_ESTIMABLE":
        support = rng.random((n_cells, n_genes)) < 0.55
        # Structural support is fixed prospectively and independently of realized
        # detection outcomes. Keep lawful support in both train/test donor blocks.
        for g in range(n_genes):
            support[: config.cells_per_donor, g] = True
            support[config.cells_per_donor : 2 * config.cells_per_donor, g] = True

    base_rate = _family_base_rate(family)
    latent_detection_intercept = np.full(n_genes, -30.0 if base_rate == 0 else _logit(base_rate), dtype=np.float64)
    latent_detection_intercept += np.linspace(-0.18, 0.18, n_genes)
    latent_positive_location = np.linspace(-0.25, 0.25, n_genes).astype(np.float64)

    if base_rate == 0.0:
        detected = np.zeros((n_cells, n_genes), dtype=bool)
    else:
        donor_effect = rng.normal(0.0, 0.25, config.n_donors)
        if family == "SP02_DONOR_IMBALANCED_ESTIMABLE":
            donor_effect += np.where(np.arange(config.n_donors) % 4 == 0, 1.0, -0.35)
        source_coef = 0.75 if family == "SP03_SOURCE_SHIFT_ESTIMABLE" else 0.20
        eta = (
            latent_detection_intercept[None, :]
            + 0.30 * depth_z[:, None]
            + 0.25 * cell_class[:, None]
            + source_coef * source[:, None]
            + donor_effect[donor_id, None]
        )
        prob = _sigmoid(eta)
        detected = (rng.random((n_cells, n_genes)) < prob) & support

    positive_value = np.zeros((n_cells, n_genes), dtype=np.float64)
    if detected.any():
        noise = rng.normal(0.0, 0.35, (n_cells, n_genes))
        donor_pos = rng.normal(0.0, 0.12, config.n_donors)
        mu = latent_positive_location[None, :] + 0.10 * depth_z[:, None] + donor_pos[donor_id, None]
        positive_value[detected] = np.exp(mu[detected] + noise[detected])

    estimability = NOT_ESTIMABLE if family in {
        "SP05_NO_POSITIVE_SUPPORT_NOT_ESTIMABLE",
        "SP06_RANK_DEFICIENT_NOT_ESTIMABLE",
    } else ESTIMABLE

    arrays = (donor_id, source, cell_class, depth_z, split, design, support, detected,
              positive_value, latent_detection_intercept, latent_positive_location)
    for arr in arrays:
        arr.setflags(write=False)

    return SparsePositiveWorld(
        family=family,
        opaque_id=_opaque_id(seed_root, family_index),
        estimability_truth=estimability,
        donor_id=donor_id,
        source=source,
        cell_class=cell_class,
        depth_z=depth_z,
        split=split,
        design_matrix=design,
        support=support,
        detected=detected,
        positive_value=positive_value,
        latent_detection_intercept=latent_detection_intercept,
        latent_positive_location=latent_positive_location,
    )


def build_sparse_positive_worlds(*, seed_root: int, config: SparsePositiveConfig | None = None) -> tuple[SparsePositiveWorld, ...]:
    cfg = config or SparsePositiveConfig()
    return tuple(_make_world(cfg, int(seed_root), i, family) for i, family in enumerate(FAMILIES))


def _fit_id(world: SparsePositiveWorld, gene_index: int) -> str:
    return sha256(f"{world.opaque_id}:gene:{int(gene_index)}".encode("ascii")).hexdigest()


def _array_list(x: np.ndarray) -> list:
    return np.asarray(x).tolist()


def serialize_fit_transport(worlds: Iterable[SparsePositiveWorld]) -> dict[str, object]:
    payload_worlds = []
    for world in worlds:
        support = np.asarray(world.support, dtype=bool)
        detected = np.asarray(world.detected, dtype=bool) & support
        positive = np.where(support & detected, np.asarray(world.positive_value, dtype=float), 0.0)
        payload_worlds.append({
            "opaque_world_id": world.opaque_id,
            "opaque_fit_ids": [_fit_id(world, g) for g in range(support.shape[1])],
            "donor_id": _array_list(world.donor_id),
            "source": _array_list(world.source),
            "cell_class": _array_list(world.cell_class),
            "depth_z": _array_list(world.depth_z),
            "split": _array_list(world.split),
            "design_matrix": _array_list(world.design_matrix),
            "support": _array_list(support),
            "detected": _array_list(detected),
            "positive_value": _array_list(positive),
        })
    payload = {
        "schema": "V80_SPARSE_POSITIVE_FIT_TRANSPORT_V1",
        "worlds": payload_worlds,
        "authority": {"estimator_qualification_authorized": False, "training_authorized": False},
    }
    validate_fit_transport(payload)
    return payload


def serialize_controller_transport(worlds: Iterable[SparsePositiveWorld]) -> dict[str, object]:
    fit_truth = []
    world_truth = []
    for world in worlds:
        world_truth.append({
            "opaque_world_id": world.opaque_id,
            "challenge_family": world.family,
            "estimability_truth": world.estimability_truth,
        })
        for g in range(world.support.shape[1]):
            fit_truth.append({
                "opaque_fit_id": _fit_id(world, g),
                "opaque_world_id": world.opaque_id,
                "challenge_family": world.family,
                "gene_index": g,
                "estimability_truth": world.estimability_truth,
                "latent_detection_intercept": float(world.latent_detection_intercept[g]),
                "latent_positive_location": float(world.latent_positive_location[g]),
            })
    return {
        "schema": "V80_SPARSE_POSITIVE_CONTROLLER_TRANSPORT_V1",
        "worlds": world_truth,
        "fits": fit_truth,
        "authority": {"estimator_qualification_authorized": False, "training_authorized": False},
    }


def _walk_keys(value: object) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def validate_fit_transport(payload: dict[str, object]) -> None:
    if payload.get("schema") != "V80_SPARSE_POSITIVE_FIT_TRANSPORT_V1":
        raise ValueError("fit transport schema differs")
    forbidden = {
        "estimability_truth",
        "latent_detection_intercept",
        "latent_positive_location",
        "challenge_family",
        "controller_truth",
    }
    leaked = forbidden.intersection(set(_walk_keys(payload)))
    if leaked:
        raise ValueError(f"controller fields leaked into fit transport: {sorted(leaked)}")
    raw = json.dumps(payload, sort_keys=True)
    for family in FAMILIES:
        if family in raw:
            raise ValueError("challenge identity leaked into fit transport")


def benchmark_identity(worlds: Iterable[SparsePositiveWorld]) -> str:
    controller = serialize_controller_transport(worlds)
    fit = serialize_fit_transport(worlds)
    return sha256(_canon({"fit": fit, "controller": controller})).hexdigest()


def with_unsupported_poison(world: SparsePositiveWorld, *, poison: float) -> SparsePositiveWorld:
    values = np.asarray(world.positive_value, dtype=float).copy()
    values[~np.asarray(world.support, dtype=bool)] = float(poison)
    values.setflags(write=False)
    return replace(world, positive_value=values)
