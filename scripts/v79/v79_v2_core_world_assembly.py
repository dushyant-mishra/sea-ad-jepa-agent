#!/usr/bin/env python3
"""Complete in-memory assembly for V79 V2_CORE synthetic qualification worlds.

This is an engineering/audit primitive only. It writes no files, runs no benchmark,
performs no Bayesian fit, and does not authorize physical qualification-world emission.
"""
from __future__ import annotations

import copy
from typing import Any

import numpy as np

import generate_v79_v2_core_worlds as G
import v79_v2_core_observation as O
import v79_v2_core_planting as P


def _new_donor_truth(world_truth: dict, design: dict[str, np.ndarray], payload: dict) -> dict[str, Any]:
    """Replace donor realizations with the frozen new-donor streams 3/18/19.

    Fixed effects, detection intercepts, positive sigma, structural support and any
    Q11 operator perturbation remain unchanged. Factor-loading assignment remains
    the same stream-4 identity. Q07 stays a true no-donor-factor world.
    """
    out = {"detection": copy.deepcopy(world_truth["detection"]),
           "positive": copy.deepcopy(world_truth["positive"])}
    parent = int(world_truth["seed_parent_world_index"])
    root = int(payload["seeds"]["root"])
    src_by_donor = G._src_by_donor(design)
    for part in ("detection", "positive"):
        sd = np.asarray(out[part]["donor_sd"], dtype=float)
        if np.all(sd == 0.0):
            out[part]["donor_raw_centered"] = np.zeros_like(np.asarray(out[part]["donor_raw_centered"], dtype=float))
            out[part]["donor_effects"] = np.zeros_like(np.asarray(out[part]["donor_effects"], dtype=float))
            out[part]["factor_loading"] = np.zeros_like(np.asarray(out[part]["factor_loading"], dtype=float))
            continue
        don = P.build_new_donor_effects(src_by_donor, sd, world_index=parent, part=part, root=root)
        out[part]["donor_raw_centered"] = np.asarray(don["raw_centered"], dtype=float)
        out[part]["donor_effects"] = np.asarray(don["effects"], dtype=float)
        out[part]["factor_loading"] = np.asarray(don["lambda"], dtype=float)
    return out


def assemble_world_in_memory(payload: dict, cal: dict, designs: dict[str, dict[str, np.ndarray]],
                             world_def: dict, amendment: dict, *, poison: float = -1.0) -> dict[str, Any]:
    """Assemble one complete world with TRAIN and both frozen held-out replicates.

    Q11 inherits Q10's every non-operator stream through the pairing amendment;
    only operator-offset streams 22/23 remain Q11-specific.
    """
    world_truth = G.build_world_truth(payload, cal, designs, world_def, amendment)
    name = str(world_truth["world"])
    wi = int(world_truth["world_index"])
    parent = int(world_truth["seed_parent_world_index"])
    design = designs[name]
    support = np.asarray(world_truth["support"], dtype=bool)
    base_truth = {"detection": world_truth["detection"], "positive": world_truth["positive"]}
    new_truth = _new_donor_truth(world_truth, design, payload)
    offsets = world_truth.get("operator_offsets")
    det_offsets = None if offsets is None else offsets["detection"]
    pos_offsets = None if offsets is None else offsets["positive"]
    pairing_parent = parent if parent != wi else None
    root = int(payload["seeds"]["root"])

    train = O.generate_observation(
        design, base_truth, support, world_index=wi, root=root, poison=poison, replicate="train",
        pairing_parent_world=pairing_parent,
        operator_offsets_detection=det_offsets, operator_offsets_positive=pos_offsets)
    same = O.generate_observation(
        design, base_truth, support, world_index=wi, root=root, poison=poison, replicate="same_donor",
        pairing_parent_world=pairing_parent,
        operator_offsets_detection=det_offsets, operator_offsets_positive=pos_offsets)
    new = O.generate_observation(
        design, new_truth, support, world_index=wi, root=root, poison=poison, replicate="new_donor",
        pairing_parent_world=pairing_parent,
        operator_offsets_detection=det_offsets, operator_offsets_positive=pos_offsets)

    for obs in (train, same, new):
        G.validate_poison_integrity(obs["observed"], support, poison=poison)

    return {
        "schema": "V79_V2_CORE_WORLD_IN_MEMORY_V1",
        "world": name,
        "world_index": wi,
        "seed_parent_world_index": parent,
        "design_sha256": G.array_bundle_sha(design),
        "support": support.copy(),
        "truth": base_truth,
        "new_donor_truth": new_truth,
        "operator_offsets": offsets,
        "observations": {"train": train, "same_donor": same, "new_donor": new},
        "benchmark_run": False,
        "qualification_fits_run": 0,
        "training_authorized": False,
    }
