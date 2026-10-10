from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any, Callable, Mapping
from pathlib import Path
import json

import numpy as np

from .v79_hierarchical_biology import LatentBiology, generate_latent_biology
from .v79_observation_operator import ObservationResult, observe_latent_biology, validate_observation_authority

_REQUIRED_ARMS = ("H0", "H1", "H2", "H3", "C_OBS", "C_BIO")
_ALLOWED_MANIFEST = {
    "arm_names", "biology_seed", "observation_seed", "counterfactual_biology_seed",
    "crossing_seed", "cell_count", "donor_count", "balancing_rule",
    "h2_realization_family", "h3_realization_family", "endpoint_version",
    "training_authorized",
}


@dataclass(frozen=True)
class ArmManifest:
    arm_names: tuple[str, ...]
    biology_seed: int
    observation_seed: int
    counterfactual_biology_seed: int
    crossing_seed: int
    cell_count: int
    donor_count: int
    balancing_rule: str
    h2_realization_family: str
    h3_realization_family: str
    endpoint_version: str
    training_authorized: bool


@dataclass(frozen=True)
class WorldArm:
    name: str
    biology_kind: str
    observer_kind: str
    latent: LatentBiology
    observed: ObservationResult
    latent_truth_hash: str
    observation_family: str


@dataclass(frozen=True)
class FactorialWorlds:
    manifest: ArmManifest
    arms: dict[str, WorldArm]
    c_obs: tuple[WorldArm, WorldArm]
    c_bio: tuple[WorldArm, WorldArm]


def validate_arm_manifest(manifest: Mapping[str, Any] | ArmManifest) -> ArmManifest:
    if isinstance(manifest, ArmManifest):
        return manifest
    keys = set(manifest)
    unknown = keys - _ALLOWED_MANIFEST
    if unknown:
        raise ValueError(f"unknown or mutable manifest fields: {sorted(unknown)}")
    missing = _ALLOWED_MANIFEST - keys
    if missing:
        raise ValueError(f"missing manifest fields: {sorted(missing)}")
    arms = tuple(str(x) for x in manifest["arm_names"])
    if arms != _REQUIRED_ARMS or len(set(arms)) != len(arms):
        raise ValueError("arm_names must exactly equal frozen H0/H1/H2/H3/C_OBS/C_BIO sequence")
    for seed_name in ("biology_seed", "observation_seed", "counterfactual_biology_seed", "crossing_seed"):
        if manifest[seed_name] is None:
            raise ValueError(f"missing seed: {seed_name}")
    if bool(manifest["training_authorized"]):
        raise ValueError("training_authorized must be false")
    if int(manifest["cell_count"]) < 1 or int(manifest["donor_count"]) < 1:
        raise ValueError("cell_count and donor_count must be positive")
    return ArmManifest(
        arm_names=arms,
        biology_seed=int(manifest["biology_seed"]),
        observation_seed=int(manifest["observation_seed"]),
        counterfactual_biology_seed=int(manifest["counterfactual_biology_seed"]),
        crossing_seed=int(manifest["crossing_seed"]),
        cell_count=int(manifest["cell_count"]),
        donor_count=int(manifest["donor_count"]),
        balancing_rule=str(manifest["balancing_rule"]),
        h2_realization_family=str(manifest["h2_realization_family"]),
        h3_realization_family=str(manifest["h3_realization_family"]),
        endpoint_version=str(manifest["endpoint_version"]),
        training_authorized=False,
    )


def canonical_manifest_json(manifest: Mapping[str, Any] | ArmManifest) -> str:
    m = validate_arm_manifest(manifest)
    return json.dumps(asdict(m), sort_keys=True, separators=(",", ":"))


def manifest_hash(manifest: Mapping[str, Any] | ArmManifest) -> str:
    return sha256(canonical_manifest_json(manifest).encode()).hexdigest()


def _crossed_labels(latent: LatentBiology, regime_ids: tuple[str, ...], seed: int) -> np.ndarray:
    rng = np.random.default_rng(int(seed))
    labels = np.empty(len(latent.broad_class), dtype=object)
    for cls in np.unique(latent.broad_class):
        ix = np.flatnonzero(latent.broad_class == cls)
        order = ix.copy()
        rng.shuffle(order)
        tiled = np.resize(np.asarray(regime_ids, dtype=object), len(ix))
        labels[order] = tiled
    return labels.astype(str)


def _arm(name: str, biology_kind: str, observer_kind: str, latent: LatentBiology,
         observed: ObservationResult, family: str) -> WorldArm:
    return WorldArm(
        name=name,
        biology_kind=biology_kind,
        observer_kind=observer_kind,
        latent=latent,
        observed=observed,
        latent_truth_hash=observed.latent_truth_hash,
        observation_family=family,
    )


def build_factorial_worlds(manifest: Mapping[str, Any] | ArmManifest,
                           biology_authority: Mapping[str, Any],
                           observation_authority: Mapping[str, Any],
                           baseline_latent: LatentBiology,
                           baseline_observer: Callable[[LatentBiology, np.ndarray, int], ObservationResult]) -> FactorialWorlds:
    m = validate_arm_manifest(manifest)
    obs_auth = validate_observation_authority(observation_authority)
    if m.h2_realization_family != obs_auth.realization_family or m.h3_realization_family != obs_auth.realization_family:
        raise ValueError("manifest realization family must match observation authority")
    if baseline_latent.latent_abundance.shape[0] != m.cell_count:
        raise ValueError("baseline latent cell count does not match manifest")
    n_genes = baseline_latent.latent_abundance.shape[1]

    new_latent = generate_latent_biology(
        biology_authority, m.cell_count, n_genes, m.donor_count, m.biology_seed
    )
    alt_latent = generate_latent_biology(
        biology_authority, m.cell_count, n_genes, m.donor_count, m.counterfactual_biology_seed
    )

    labels0 = _crossed_labels(baseline_latent, obs_auth.regime_ids, m.crossing_seed)
    labels1 = _crossed_labels(new_latent, obs_auth.regime_ids, m.crossing_seed)

    h0_obs = baseline_observer(baseline_latent, labels0, m.observation_seed)
    h1_obs = baseline_observer(new_latent, labels1, m.observation_seed)
    h2_obs = observe_latent_biology(baseline_latent, obs_auth, labels0, m.observation_seed)
    h3_obs = observe_latent_biology(new_latent, obs_auth, labels1, m.observation_seed)

    arms = {
        "H0": _arm("H0", "E2_BASELINE", "BASELINE", baseline_latent, h0_obs, "BASELINE"),
        "H1": _arm("H1", "HIERARCHICAL", "BASELINE", new_latent, h1_obs, "BASELINE"),
        "H2": _arm("H2", "E2_BASELINE", "EXPLICIT", baseline_latent, h2_obs, obs_auth.realization_family),
        "H3": _arm("H3", "HIERARCHICAL", "EXPLICIT", new_latent, h3_obs, obs_auth.realization_family),
    }

    obs_a, obs_b = obs_auth.regime_ids[:2]
    a_labels = np.full(m.cell_count, obs_a, dtype=f"<U{max(1, len(obs_a))}")
    b_labels = np.full(m.cell_count, obs_b, dtype=f"<U{max(1, len(obs_b))}")
    cobs_a_obs = observe_latent_biology(new_latent, obs_auth, a_labels, m.observation_seed)
    cobs_b_obs = observe_latent_biology(new_latent, obs_auth, b_labels, m.observation_seed)
    c_obs = (
        _arm("C_OBS_A", "HIERARCHICAL", "EXPLICIT", new_latent, cobs_a_obs, obs_auth.realization_family),
        _arm("C_OBS_B", "HIERARCHICAL", "EXPLICIT", new_latent, cobs_b_obs, obs_auth.realization_family),
    )

    cbio_a_obs = observe_latent_biology(new_latent, obs_auth, a_labels, m.observation_seed)
    cbio_b_obs = observe_latent_biology(alt_latent, obs_auth, a_labels, m.observation_seed)
    c_bio = (
        _arm("C_BIO_A", "HIERARCHICAL", "EXPLICIT", new_latent, cbio_a_obs, obs_auth.realization_family),
        _arm("C_BIO_B", "HIERARCHICAL", "EXPLICIT", alt_latent, cbio_b_obs, obs_auth.realization_family),
    )

    return FactorialWorlds(manifest=m, arms=arms, c_obs=c_obs, c_bio=c_bio)


def serialize_factorial_worlds(worlds: FactorialWorlds, out_dir: str | Path) -> dict[str, Any]:
    """Write sparse observations once per view and dense latent truth once per unique truth hash."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    latent_dir = out / "latent"
    latent_dir.mkdir(exist_ok=True)
    named = dict(worlds.arms)
    named.update({
        "C_OBS_A": worlds.c_obs[0],
        "C_OBS_B": worlds.c_obs[1],
        "C_BIO_A": worlds.c_bio[0],
        "C_BIO_B": worlds.c_bio[1],
    })
    result = {"manifest_hash": manifest_hash(worlds.manifest), "worlds": {}}
    written_latents: set[str] = set()
    for name, arm in named.items():
        X = arm.observed.counts.tocsr()
        latent_rel = f"latent/{arm.latent_truth_hash}.latent.npz"
        if arm.latent_truth_hash not in written_latents:
            np.savez_compressed(
                out / latent_rel,
                broad_class=np.asarray(arm.latent.broad_class),
                substate=np.asarray(arm.latent.substate),
                donor=np.asarray(arm.latent.donor),
                continuous_factors=np.asarray(arm.latent.continuous_factors),
                latent_abundance=np.asarray(arm.latent.latent_abundance),
                biological_total_scale=np.asarray(arm.latent.biological_total_scale),
            )
            written_latents.add(arm.latent_truth_hash)
        npz_name = f"{name}.world.npz"
        receipt_name = f"{name}.receipt.json"
        np.savez_compressed(
            out / npz_name,
            counts_data=X.data, counts_indices=X.indices, counts_indptr=X.indptr,
            counts_shape=np.asarray(X.shape, dtype=np.int64),
            regime_labels=np.asarray(arm.observed.regime_labels).astype(str),
            capture_efficiency=np.asarray(arm.observed.capture_efficiency),
            observed_library_totals=np.asarray(arm.observed.observed_library_totals),
            detected_counts=np.asarray(arm.observed.detected_counts),
        )
        receipt = {
            "schema": "V79_FACTORIAL_WORLD_RECEIPT_V1",
            "name": name,
            "biology_kind": arm.biology_kind,
            "observer_kind": arm.observer_kind,
            "observation_family": arm.observation_family,
            "latent_truth_hash": arm.latent_truth_hash,
            "latent_artifact": latent_rel,
            "counts_hash": arm.observed.counts_hash,
            "manifest_hash": manifest_hash(worlds.manifest),
            "n_cells": int(X.shape[0]),
            "n_addresses": int(X.shape[1]),
            "training_authorized": False,
            "identity_scrubbed_truth": True,
        }
        (out / receipt_name).write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
        result["worlds"][name] = {
            "npz": npz_name, "latent_npz": latent_rel, "receipt": receipt_name,
            "latent_truth_hash": arm.latent_truth_hash,
            "counts_hash": arm.observed.counts_hash,
        }
    return result
