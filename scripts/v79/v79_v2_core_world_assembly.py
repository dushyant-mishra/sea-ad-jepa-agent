#!/usr/bin/env python3
"""Complete in-memory assembly of frozen V79 V2_CORE synthetic worlds.

This module deliberately performs no disk writes, benchmark, fitting, scoring, or
training. Physical world emission remains a separate controller-gated operation.
"""
from __future__ import annotations

import copy
from typing import Any

import numpy as np

import generate_v79_v2_core_worlds as G
import v79_v2_core_observation as O
import v79_v2_core_planting as P
import v79_v2_core_structural_support as S


def _source_by_donor(design: dict[str, np.ndarray]) -> np.ndarray:
    donor = np.asarray(design["donor"], dtype=np.int64)
    src = np.asarray(design["src"], dtype=np.int64)
    levels = np.unique(donor)
    if not np.array_equal(levels, np.arange(len(levels), dtype=np.int64)):
        raise SystemExit("STOP: donor codes must be contiguous 0..D-1")
    out = np.empty(len(levels), dtype=np.int64)
    for d in levels:
        seen = np.unique(src[donor == d])
        if len(seen) != 1:
            raise SystemExit("STOP: donor spans multiple sources")
        out[int(d)] = int(seen[0])
    return out


def _attach_donor_realization(part: dict[str, Any], realization: dict[str, np.ndarray]) -> None:
    sd = np.asarray(part["donor_sd"], dtype=float)
    if np.all(sd == 0):
        effects = np.zeros_like(np.asarray(realization["effects"], dtype=float))
        raw = np.zeros_like(np.asarray(realization["raw_centered"], dtype=float))
        lam = np.zeros_like(np.asarray(realization["lambda"], dtype=float))
        factor = np.zeros_like(np.asarray(realization["shared_factor"], dtype=float))
    else:
        effects = np.asarray(realization["effects"], dtype=float)
        raw = np.asarray(realization["raw_centered"], dtype=float)
        lam = np.asarray(realization["lambda"], dtype=float)
        factor = np.asarray(realization["shared_factor"], dtype=float)
    part["donor_effects"] = effects
    part["raw_centered"] = raw
    part["donor_lambda"] = lam
    part["donor_shared_factor"] = factor


def _deactivate_absent_donor_factors(truth: dict[str, Any]) -> None:
    """Q07 means no active donor factor, not merely a zero reported SD."""
    for part_name in ("detection", "positive"):
        part = truth[part_name]
        if np.all(np.asarray(part["donor_sd"], dtype=float) == 0):
            if "donor_effects" in part:
                part["donor_effects"] = np.zeros_like(np.asarray(part["donor_effects"], dtype=float))
            if "raw_centered" in part:
                part["raw_centered"] = np.zeros_like(np.asarray(part["raw_centered"], dtype=float))
            if "donor_lambda" in part:
                part["donor_lambda"] = np.zeros_like(np.asarray(part["donor_lambda"], dtype=float))
            if "donor_shared_factor" in part:
                part["donor_shared_factor"] = np.zeros_like(np.asarray(part["donor_shared_factor"], dtype=float))


def _fixed_detection_eta(truth: dict, design: dict[str, np.ndarray]) -> np.ndarray:
    det = truth["detection"]
    z, q = O.depth_basis(np.asarray(design["log_lib"], dtype=float))
    cls = np.asarray(design["cls"], dtype=np.int64)
    src = np.asarray(design["src"], dtype=np.int64)
    Hc = O.normalized_helmert(len(np.unique(cls)))
    Hs = O.normalized_helmert(len(np.unique(src)))
    eta = np.broadcast_to(np.asarray(det["intercept"], dtype=float)[None, :],
                          (len(z), len(det["intercept"]))).copy()
    eta += z[:, None] * np.asarray(det["depth1"], dtype=float)[None, :]
    eta += q[:, None] * np.asarray(det["depth2"], dtype=float)[None, :]
    eta += Hc[cls] @ np.asarray(det["class_contrasts"], dtype=float).T
    eta += Hs[src] @ np.asarray(det["source_contrasts"], dtype=float).T
    return eta


def fixed_detection_prevalence(truth: dict, design: dict[str, np.ndarray], support: np.ndarray) -> np.ndarray:
    """Mean fixed-effect detection probability over measured cells, per gene."""
    support = np.asarray(support, dtype=bool)
    eta = _fixed_detection_eta(truth, design)
    if eta.shape != support.shape:
        raise SystemExit("STOP: fixed detection prevalence shape mismatch")
    p = 1.0 / (1.0 + np.exp(-np.clip(eta, -40.0, 40.0)))
    out = np.empty(eta.shape[1], dtype=float)
    for g in range(eta.shape[1]):
        if not support[:, g].any():
            raise SystemExit("STOP: gene has no measured cells")
        out[g] = float(p[support[:, g], g].mean())
    return out


def _operator_offset_matrix(design: dict[str, np.ndarray], truth: dict, *, part: str,
                            world_index: int, payload: dict, amendment: dict) -> np.ndarray:
    gene_count = len(np.asarray(truth[part]["donor_sd"]))
    n_op = int(np.max(np.asarray(design["op"], dtype=np.int64))) + 1
    out = np.empty((n_op, gene_count), dtype=float)
    for g in range(gene_count):
        out[:, g] = G.generate_operator_offsets(
            design,
            donor_sd=float(truth[part]["donor_sd"][g]),
            world_index=int(world_index),
            gene_index=g,
            part=part,
            payload=payload,
            amendment=amendment,
        )
    return out


def _base_world_index(world_def: dict, amendment: dict | None) -> int:
    idx = int(world_def["index"])
    if amendment is None:
        return idx
    # Stream 10 is non-operator randomness; the pairing amendment maps Q11 -> Q10.
    return G.effective_seed_world_index(idx, 10, amendment)


def assemble_world_in_memory(payload: dict, calibration: dict, world_def: dict,
                             design: dict[str, np.ndarray], *, source_code_map: dict[str, int],
                             amendment: dict | None = None, poison: float = -1.0) -> dict[str, Any]:
    """Assemble one complete synthetic world and both held-out replicates in memory.

    Order is frozen: planting -> donor realization -> world modification -> support
    -> detection-intercept calibration -> train/same-donor/new-donor observations.
    Source identities are passed explicitly from frozen custody. Q11 reuses Q10 for
    every non-operator random stream and differs only through streams 22/23.
    """
    idx = int(world_def["index"])
    name = str(world_def["name"])
    gene_count = int(payload["worlds"]["genes_per_world"])
    root = int(payload["seeds"]["root"])
    base_idx = _base_world_index(world_def, amendment)

    required = {"src", "donor", "cls", "op", "log_lib"}
    if not required.issubset(design):
        raise SystemExit(f"STOP: design missing keys {sorted(required - set(design))}")
    n = len(np.asarray(design["src"]))
    if any(len(np.asarray(design[k])) != n for k in required):
        raise SystemExit("STOP: design arrays disagree on cell count")
    source_code_map = S.validate_source_code_map(source_code_map, design)

    truth = P.build_q00_planting(calibration, payload, world_index=base_idx, G=gene_count)
    audit_lhs = truth.pop("lhs_levels")
    audit_signs = truth.pop("contrast_signs")

    src_by_donor = _source_by_donor(design)
    for part in ("detection", "positive"):
        realization = P.build_donor_effects(
            src_by_donor,
            np.asarray(truth[part]["donor_sd"], dtype=float),
            world_index=base_idx,
            part=part,
            root=root,
        )
        _attach_donor_realization(truth[part], realization)

    truth = G.apply_world_modifications(truth, world_def, payload)
    _deactivate_absent_donor_factors(truth)
    support = S.build_structural_support(
        payload,
        design,
        world_index=idx,
        source_code_map=source_code_map,
        genes=gene_count,
        amendment=amendment,
    )
    truth = G.calibrate_detection_intercepts(truth, design, support)

    new_truth = copy.deepcopy(truth)
    for part in ("detection", "positive"):
        realization = P.build_new_donor_effects(
            src_by_donor,
            np.asarray(truth[part]["donor_sd"], dtype=float),
            world_index=base_idx,
            part=part,
            root=root,
        )
        _attach_donor_realization(new_truth[part], realization)
    _deactivate_absent_donor_factors(new_truth)

    is_q11 = world_def.get("modifications", {}).get("operator") == "omitted_perturbation"
    if is_q11:
        if amendment is None:
            raise SystemExit("STOP: Q11 requires the pairing amendment")
        op_det = _operator_offset_matrix(design, truth, part="detection", world_index=idx,
                                         payload=payload, amendment=amendment)
        op_pos = _operator_offset_matrix(design, truth, part="positive", world_index=idx,
                                         payload=payload, amendment=amendment)
        pair_parent = int(amendment["paired_counterfactual"]["parent_world"]["world_index"])
    else:
        op_det = None
        op_pos = None
        pair_parent = None

    train = O.generate_observation(design, truth, support, world_index=idx, root=root, poison=poison,
                                   replicate="train", pairing_parent_world=pair_parent,
                                   operator_offsets_detection=op_det, operator_offsets_positive=op_pos)
    same = O.generate_observation(design, truth, support, world_index=idx, root=root, poison=poison,
                                  replicate="same_donor", pairing_parent_world=pair_parent,
                                  operator_offsets_detection=op_det, operator_offsets_positive=op_pos)
    new = O.generate_observation(design, new_truth, support, world_index=idx, root=root, poison=poison,
                                 replicate="new_donor", pairing_parent_world=pair_parent,
                                 operator_offsets_detection=op_det, operator_offsets_positive=op_pos)
    for obs in (train, same, new):
        G.validate_poison_integrity(obs["observed"], support, poison=poison)

    return {
        "schema": "V79_V2_CORE_WORLD_IN_MEMORY_V1",
        "world_name": name,
        "world_index": idx,
        "design_sha256": G.array_bundle_sha({k: np.asarray(design[k]) for k in sorted(required)}),
        "source_code_map": dict(source_code_map),
        "support": support,
        "truth": truth,
        "new_donor_truth": new_truth,
        "lhs_levels": audit_lhs,
        "contrast_signs": audit_signs,
        "operator_offsets_detection": op_det,
        "operator_offsets_positive": op_pos,
        "observations": {"train": train, "same_donor": same, "new_donor": new},
        "benchmark_run": False,
        "qualification_fits_run": 0,
        "training_authorized": False,
    }
