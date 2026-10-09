#!/usr/bin/env python3
"""Golden, metamorphic, and independent-calculation tests for shared P0 statistics."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from derive_full104_phase2_shared_state import fit_basis as production_fit_basis
from jepa_scientific_promotion_harness_v1 import assert_frozen_consumable, invalidate, promote, save_registry, sha256


ROOT = Path(__file__).resolve().parents[2]


def independent_fit(mean_rows, within_rows, between_rows, donor_indices, rank):
    """Independent whitening implementation; does not call production statistic code."""
    mean = np.mean(mean_rows[donor_indices], axis=0, dtype=np.float64)
    within = np.mean(within_rows[donor_indices], axis=0, dtype=np.float64) - np.outer(mean, mean)
    between = np.mean(between_rows[donor_indices], axis=0, dtype=np.float64) - np.outer(mean, mean)
    within = (within + within.T) * 0.5
    between = (between + between.T) * 0.5
    diagonal = np.clip(np.diag(within), 0, None)
    positive = diagonal[diagonal > 0]
    floor = max(np.finfo(float).eps, (np.median(positive) if len(positive) else 1.0) * math.sqrt(np.finfo(float).eps))
    scale = np.sqrt(np.maximum(diagonal, floor))
    aw = (within / np.outer(scale, scale)); aw = (aw + aw.T) * 0.5
    ab = (between / np.outer(scale, scale)); ab = (ab + ab.T) * 0.5
    ridge = math.sqrt(np.finfo(float).eps) * float(np.trace(aw)) / len(scale)
    metric = aw + ridge * np.eye(len(scale))
    values_m, vectors_m = np.linalg.eigh(metric)
    whitening = vectors_m @ np.diag(1 / np.sqrt(values_m)) @ vectors_m.T
    whitened = whitening @ ab @ whitening
    values, vectors = np.linalg.eigh((whitened + whitened.T) * 0.5)
    order = np.argsort(values)[::-1][:rank]
    values = values[order]
    components = (whitening @ vectors[:, order]) / scale[:, None]
    for column in range(rank):
        pivot = int(np.argmax(np.abs(components[:, column])))
        if components[pivot, column] < 0:
            components[:, column] *= -1
    q, _ = np.linalg.qr(components, mode="reduced")
    return {"mean": mean, "eigenvalues": values, "components": components, "q": q}


def sufficient(x):
    donors = x.shape[0]
    mean, within, between = [], [], []
    for donor in range(donors):
        local = x[donor]
        n, views, _ = local.shape
        summed = local.sum(axis=1)
        within_sum = sum(local[:, view].T @ local[:, view] for view in range(views))
        between_sum = summed.T @ summed - within_sum
        mean.append(local.mean(axis=(0, 1)))
        within.append(within_sum / (n * views))
        between.append(between_sum / (n * views * (views - 1)))
    return np.asarray(mean), np.asarray(within), np.asarray(between)


def fixture(seed, planted):
    rng = np.random.default_rng(seed)
    donors, cells, views, features, rank = 24, 48, 4, 24, 4
    arrays = []
    for sketch in range(2):
        load, _ = np.linalg.qr(rng.normal(size=(features, rank)))
        x = np.empty((donors, cells, views, features), np.float64)
        for donor in range(donors):
            if planted:
                latent = rng.normal(size=(cells, rank)) + rng.normal(scale=0.25, size=(1, rank))
                for view in range(views):
                    x[donor, :, view] = latent @ load.T + rng.normal(scale=0.18, size=(cells, features))
            else:
                x[donor] = rng.normal(size=(cells, views, features))
        arrays.append(x)
    return arrays


def permuted_between(x, key, reps):
    mean, within, _ = sufficient(x)
    output = np.empty((reps, len(x), x.shape[-1], x.shape[-1]), np.float64)
    for rep in range(reps):
        for donor in range(len(x)):
            local = x[donor]
            shuffled = np.empty_like(local)
            for view in range(local.shape[1]):
                seed = int.from_bytes(hashlib.sha256(f"{key}|{rep}|{donor}|{view}".encode()).digest()[:8], "little")
                shuffled[:, view] = local[np.random.default_rng(seed).permutation(len(local)), view]
            _, _, b = sufficient(shuffled[None])
            output[rep, donor] = b[0]
    return mean, within, output


def overlap(a, b, d):
    return float(np.square(a[:, :d].T @ b[:, :d]).sum() / d)


def evaluate_fixture(arrays, planted, reps=64):
    per_sketch = []
    for sketch, x in zip("AB", arrays):
        mean, within, between = sufficient(x)
        primary = production_fit_basis(mean, within, between, np.arange(len(x)), x.shape[-1])
        independent = independent_fit(mean, within, between, np.arange(len(x)), x.shape[-1])
        eigen_diff = float(np.max(np.abs(primary["eigenvalues"] - independent["eigenvalues"])))
        subspace_diff = float(max(1 - overlap(primary["q"], independent["q"], d) for d in range(1, 9)))
        _, _, null_between = permuted_between(x, f"fixture-{planted}-{sketch}", reps)
        null_eigen = np.asarray([independent_fit(mean, within, null_between[r], np.arange(len(x)), x.shape[-1])["eigenvalues"] for r in range(reps)])
        supported = primary["eigenvalues"] > null_eigen.max(axis=0)
        contiguous = 0
        for value in supported:
            if not value:
                break
            contiguous += 1
        # Metamorphic donor order and orthogonal feature rotation.
        reverse = np.arange(len(x))[::-1]
        donor_reordered = independent_fit(mean, within, between, reverse, x.shape[-1])
        rng = np.random.default_rng(9000 + ord(sketch) + int(planted))
        rotation, _ = np.linalg.qr(rng.normal(size=(x.shape[-1], x.shape[-1])))
        rotated = x @ rotation
        rm, rw, rb = sufficient(rotated)
        rotated_fit = independent_fit(rm, rw, rb, np.arange(len(x)), x.shape[-1])
        view_reordered = x[:, :, ::-1]
        vm, vw, vb = sufficient(view_reordered)
        view_fit = independent_fit(vm, vw, vb, np.arange(len(x)), x.shape[-1])
        per_sketch.append({
            "sketch": sketch, "contiguous_supported_rank": contiguous,
            "production_independent_eigen_max_abs": eigen_diff,
            "production_independent_prefix_subspace_max_loss_D1_8": subspace_diff,
            "donor_order_eigen_max_abs": float(np.max(np.abs(independent["eigenvalues"] - donor_reordered["eigenvalues"]))),
            "view_order_eigen_max_abs": float(np.max(np.abs(independent["eigenvalues"] - view_fit["eigenvalues"]))),
            "orthogonal_rotation_eigen_max_abs": float(np.max(np.abs(independent["eigenvalues"] - rotated_fit["eigenvalues"]))),
        })
    if planted:
        passed = all(x["contiguous_supported_rank"] == 4 for x in per_sketch)
    else:
        passed = all(x["contiguous_supported_rank"] == 0 for x in per_sketch)
    passed &= all(x["production_independent_eigen_max_abs"] <= 1e-6 and x["production_independent_prefix_subspace_max_loss_D1_8"] <= 1e-5 and x["donor_order_eigen_max_abs"] <= 1e-8 and x["view_order_eigen_max_abs"] <= 1e-8 and x["orthogonal_rotation_eigen_max_abs"] <= 1e-6 for x in per_sketch)
    return passed, per_sketch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--harness", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    harness, out = Path(args.harness).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    contract = json.loads((harness / "JEPA_SCIENTIFIC_PROMOTION_HARNESS_V1.json").read_text())
    if contract["status"] != "FROZEN_PROSPECTIVELY_BEFORE_LEVEL2_SHARED_STATISTICS":
        raise RuntimeError("promotion contract unavailable")
    planted_pass, planted = evaluate_fixture(fixture(20260827, True), True)
    null_pass, null = evaluate_fixture(fixture(20260828, False), False)

    # State-machine golden test: invalidation taints every transitive dependent;
    # a non-frozen artifact cannot be consumed and cannot skip promotion states.
    graph = {
        "contract": {"state": "FROZEN", "tainted": False, "depends_on": []},
        "stat": {"state": "FROZEN", "tainted": False, "depends_on": ["contract"]},
        "selection": {"state": "PROVISIONAL", "tainted": False, "depends_on": ["stat"]},
        "private": {"state": "EXPLORATORY", "tainted": False, "depends_on": ["selection"]},
    }
    invalidate(graph, "stat", "golden invalidation", "0" * 64)
    taint_pass = all(graph[node]["tainted"] for node in ("stat", "selection", "private"))
    consume_blocked = False
    try:
        assert_frozen_consumable(graph, "selection")
    except RuntimeError:
        consume_blocked = True
    promotion_blocked = False
    try:
        promote(graph, "selection", "QUALIFIED", {"independent": True})
    except RuntimeError:
        promotion_blocked = True
    state_pass = taint_pass and consume_blocked and promotion_blocked
    state_path = out / "GOLDEN_TAINT_REGISTRY.json"
    save_registry(state_path, graph)

    result = {
        "schema": "jepa-shared-promotion-harness-executable-tests-v1",
        "status": "PASS_PROMOTION_HARNESS_EXECUTABLE_TESTS" if planted_pass and null_pass and state_pass else "STOP_PROMOTION_HARNESS_TEST_FAILURE",
        "planted_rank_fixture": {"expected_rank": 4, "pass": planted_pass, "sketches": planted},
        "matched_null_fixture": {"expected_joint_qualified_dimensions": 0, "pass": null_pass, "sketches": null},
        "metamorphic_tests": ["donor order", "view order", "orthogonal coordinate rotation"],
        "observed_null_symmetry": "production and independent fits receive identically constructed donor sufficient statistics; every null replicate is fully refitted",
        "state_machine": {"recursive_taint_pass": taint_pass, "nonfrozen_consumption_blocked": consume_blocked, "tainted_promotion_blocked": promotion_blocked, "pass": state_pass},
        "independent_implementation": "independent symmetric whitening plus numpy.linalg.eigh; production generalized-eigh code is not called by independent_fit",
        "input_hashes": {"harness_manifest": sha256(harness / "JEPA_SCIENTIFIC_PROMOTION_HARNESS_V1_MANIFEST.csv"), "code": sha256(Path(__file__))},
    }
    result_path = out / "SHARED_PROMOTION_HARNESS_EXECUTABLE_TESTS.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    agreement = pd.DataFrame(planted + null)
    agreement["fixture"] = ["planted"] * 2 + ["null"] * 2
    agreement_path = out / "INDEPENDENT_CALCULATION_AGREEMENT.csv"
    agreement.to_csv(agreement_path, index=False, lineterminator="\n")
    manifest = out / "SHARED_PROMOTION_HARNESS_TEST_MANIFEST.csv"
    files = [result_path, agreement_path, state_path, Path(__file__)]
    pd.DataFrame([{"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in files]).to_csv(manifest, index=False, lineterminator="\n")
    (out / "SHARED_PROMOTION_HARNESS_TEST_ROOT_SHA256.txt").write_text(sha256(manifest) + "\n", encoding="ascii")
    print(json.dumps({"status": result["status"], "manifest_sha256": sha256(manifest)}, indent=2))
    if not (planted_pass and null_pass and state_pass):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
