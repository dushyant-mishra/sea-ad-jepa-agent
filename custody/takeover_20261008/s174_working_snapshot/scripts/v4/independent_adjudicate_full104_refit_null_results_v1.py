#!/usr/bin/env python3
"""Independent post-ALL adjudication from primitive observed/null payloads only.

This module intentionally does not import production sensitivity or selector
code and never opens a production calibration/selection result.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd


FREEZE_ROOT = "593e14872b6fe07d3f2855a49dd8eac57bfa5819465b8801b801dd9f6d4b510c"
OBSERVED_FIELDS = ("mean", "within", "between", "components", "eigenvalues", "bootstrap_eigen", "bootstrap_stability", "heldout", "numerical_diagnostics_json")
NULL_FIELDS = ("null_full_eigenvalues", "paired_null_bootstrap_eigenvalues", "stability", "heldout", "numerical_diagnostics_json")


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def semantic_payload_sha(payload, fields) -> str:
    digest = hashlib.sha256()
    for key in sorted(fields):
        value = np.ascontiguousarray(payload[key])
        digest.update(key.encode())
        digest.update(str(value.dtype).encode())
        digest.update(str(value.shape).encode())
        digest.update(value.tobytes())
    return digest.hexdigest()


def scalar_text(value) -> str:
    return str(np.asarray(value).item())


def validate_payload(path: Path, fields, expected_cap: str, sketch: str, replicate: int | None, identity: dict | None) -> dict:
    with np.load(path, allow_pickle=False) as payload:
        required = set(fields) | {"payload_semantic_sha256", "freeze_root", "cap", "sketch", "replicate", "plan_sha256", "plan_semantic_sha256", "implementation_fingerprint", "gate_manifest_sha256", "input_hashes_sha256", "moment_sha256", "mapping_sha256"}
        if not required.issubset(payload.files):
            raise RuntimeError(f"payload fields missing: {path}")
        if semantic_payload_sha(payload, fields) != scalar_text(payload["payload_semantic_sha256"]):
            raise RuntimeError(f"semantic payload hash mismatch: {path}")
        checks = {"freeze_root": FREEZE_ROOT, "cap": expected_cap, "sketch": sketch}
        if replicate is not None:
            checks["replicate"] = replicate
        for key, expected in checks.items():
            if scalar_text(payload[key]) != str(expected):
                raise RuntimeError(f"payload identity mismatch {key}: {path}")
        current = {key: scalar_text(payload[key]) for key in ("implementation_fingerprint", "gate_manifest_sha256", "input_hashes_sha256", "plan_sha256", "plan_semantic_sha256", "moment_sha256")}
        if identity is not None and current != identity:
            raise RuntimeError(f"within-cap identity mismatch: {path}")
        arrays = {key: np.asarray(payload[key]) for key in fields if key != "numerical_diagnostics_json"}
        diagnostics = json.loads(scalar_text(payload["numerical_diagnostics_json"]))
        if not all(np.isfinite(value).all() for value in arrays.values()):
            raise RuntimeError(f"nonfinite scientific payload: {path}")
        if diagnostics.get("all_finite") is not True:
            raise RuntimeError(f"numerical diagnostics failed: {path}")
    return {"identity": current, "arrays": arrays, "diagnostics": diagnostics, "file_sha256": sha(path)}


def verify_manifest(root: Path, name: str, allowed_mutable_prefixes=()) -> dict:
    path = root / name
    table = pd.read_csv(path)
    if not {"path", "sha256"}.issubset(table.columns):
        raise RuntimeError(f"manifest schema mismatch: {path}")
    excluded = []
    scientific_rows = []
    for row in table.itertuples(index=False):
        candidate = root / str(row.path)
        if not candidate.exists():
            candidate = Path(str(row.path))
        if not candidate.exists():
            raise RuntimeError(f"manifest file missing: {row.path}")
        actual = sha(candidate)
        if actual != str(row.sha256):
            if any(str(row.path).replace("\\", "/").startswith(prefix) for prefix in allowed_mutable_prefixes):
                excluded.append({"path": str(row.path), "expected_sha256": str(row.sha256), "current_sha256": actual, "reason": "post-publication operational monitoring sidecar"})
                continue
            raise RuntimeError(f"manifest mismatch: {row.path}")
        scientific_rows.append((str(row.path).replace("\\", "/"), int(row.bytes), str(row.sha256)))
    digest = hashlib.sha256()
    for row in sorted(scientific_rows):
        digest.update(("|".join(map(str, row)) + "\n").encode())
    return {"manifest_sha256": sha(path), "scientific_subset_sha256": digest.hexdigest(), "verified_immutable_rows": len(scientific_rows), "excluded_mutable_mismatches": excluded}


def load_cap(root: Path, cap: str, manifest_name: str, allowed_mutable_prefixes=()) -> dict:
    manifest_audit = verify_manifest(root, manifest_name, allowed_mutable_prefixes)
    result = {"manifest_audit": manifest_audit, "sketches": {}}
    for sketch in "AB":
        observed = validate_payload(root / f"OBSERVED_FULL512_{sketch}.npz", OBSERVED_FIELDS, cap, sketch, -1, None)
        identity = observed["identity"]
        null_full, null_boot, null_stability, null_held = [], [], [], []
        map_hashes = []
        for replicate in range(256):
            path = root / f"null_replicates_{sketch}" / f"replicate_{replicate:03d}.npz"
            item = validate_payload(path, NULL_FIELDS, cap, sketch, replicate, identity)
            null_full.append(item["arrays"]["null_full_eigenvalues"])
            null_boot.append(item["arrays"]["paired_null_bootstrap_eigenvalues"])
            null_stability.append(item["arrays"]["stability"])
            null_held.append(item["arrays"]["heldout"].astype(np.float64))
            with np.load(path, allow_pickle=False) as payload:
                map_hashes.append(scalar_text(payload["mapping_sha256"]))
        result["sketches"][sketch] = {
            "components": observed["arrays"]["components"].astype(np.float64),
            "observed_bootstrap_eigen": observed["arrays"]["bootstrap_eigen"].astype(np.float64),
            "observed_stability": observed["arrays"]["bootstrap_stability"].astype(np.float64),
            "observed_heldout": observed["arrays"]["heldout"].astype(np.float64),
            "null_full_eigen": np.stack(null_full),
            "paired_null_bootstrap_eigen": np.stack(null_boot),
            "null_stability": np.stack(null_stability),
            "null_heldout": np.stack(null_held),
            "map_hashes_sha256": hashlib.sha256("".join(map_hashes).encode()).hexdigest(),
            "identity": identity,
        }
    return result


def mean_se(values: np.ndarray, axis: int = 0) -> tuple[np.ndarray, np.ndarray]:
    return values.mean(axis=axis), values.std(axis=axis, ddof=1) / math.sqrt(values.shape[axis])


def adjudicate_vectorized(cap: dict) -> dict:
    per_sketch = {}
    for sketch in "AB":
        data = cap["sketches"][sketch]
        oe_m, oe_se = mean_se(data["observed_bootstrap_eigen"])
        nb_m, nb_se = mean_se(data["paired_null_bootstrap_eigen"])
        signal_margin_local = (oe_m - oe_se) - (nb_m + nb_se)
        signal = np.logical_and.accumulate(signal_margin_local > 0)
        os_m, os_se = mean_se(data["observed_stability"])
        ns_m, ns_se = mean_se(data["null_stability"])
        stability_margin = (os_m - os_se) - (ns_m + ns_se)
        observed_held_m, observed_held_se = mean_se(data["observed_heldout"])
        null_by_donor = data["null_heldout"].mean(axis=0)
        null_held_m, null_held_se = mean_se(null_by_donor)
        predictability_margin = (observed_held_m - observed_held_se) - (null_held_m + null_held_se)
        stability = stability_margin > 0
        predictability = predictability_margin > 0
        jointly = signal & stability & predictability
        per_sketch[sketch] = {
            "signal": signal,
            "stability": stability,
            "predictability": predictability,
            "jointly": jointly,
            "signal_margin_local": signal_margin_local,
            "stability_margin": stability_margin,
            "predictability_margin": predictability_margin,
            "heldout": data["observed_heldout"],
        }
    common = per_sketch["A"]["jointly"] & per_sketch["B"]["jointly"]
    prefix = []
    for index, supported in enumerate(common):
        if not bool(supported):
            break
        prefix.append(index + 1)
    paired = (per_sketch["A"]["heldout"] + per_sketch["B"]["heldout"]) * 0.5
    means, ses = mean_se(paired)
    candidate, best, threshold, interval = None, None, None, []
    if prefix:
        best = max(prefix, key=lambda dimension: means[dimension - 1])
        threshold = float(means[best - 1] - ses[best - 1])
        interval = [dimension for dimension in prefix if means[dimension - 1] >= threshold]
        candidate = min(interval)
    return {"per_sketch": per_sketch, "common": common, "prefix": prefix, "candidate": candidate, "best": best, "threshold": threshold, "interval": interval, "paired": paired, "paired_mean": means, "paired_se": ses}


def adjudicate_loop(cap: dict) -> dict:
    joint = {}
    held = {}
    for sketch in "AB":
        data = cap["sketches"][sketch]
        held[sketch] = data["observed_heldout"]
        flags, signal_prefix = [], True
        for index in range(320):
            def se(values):
                return float(np.std(values, ddof=1) / math.sqrt(len(values)))
            obs_e = data["observed_bootstrap_eigen"][:, index]
            nul_e = data["paired_null_bootstrap_eigen"][:, index]
            signal_prefix = signal_prefix and (float(np.mean(obs_e)) - se(obs_e) > float(np.mean(nul_e)) + se(nul_e))
            obs_s = data["observed_stability"][:, index]
            nul_s = data["null_stability"][:, index]
            donor_null = data["null_heldout"][:, :, index].mean(axis=0)
            obs_h = data["observed_heldout"][:, index]
            stable = float(np.mean(obs_s)) - se(obs_s) > float(np.mean(nul_s)) + se(nul_s)
            predictable = float(np.mean(obs_h)) - se(obs_h) > float(np.mean(donor_null)) + se(donor_null)
            flags.append(bool(signal_prefix and stable and predictable))
        joint[sketch] = flags
    common = [joint["A"][i] and joint["B"][i] for i in range(320)]
    prefix = []
    for index, value in enumerate(common):
        if not value:
            break
        prefix.append(index + 1)
    paired = (held["A"] + held["B"]) * 0.5
    candidate = None
    if prefix:
        means = [float(np.mean(paired[:, d - 1])) for d in prefix]
        ses = [float(np.std(paired[:, d - 1], ddof=1) / math.sqrt(len(paired))) for d in prefix]
        best_index = int(np.argmax(means))
        threshold = means[best_index] - ses[best_index]
        candidate = next(d for d, value in zip(prefix, means) if value >= threshold)
    return {"joint": joint, "common": common, "prefix": prefix, "candidate": candidate}


def overlap(a: np.ndarray, b: np.ndarray, dimension: int) -> float:
    qa, _ = np.linalg.qr(a[:, :dimension], mode="reduced")
    qb, _ = np.linalg.qr(b[:, :dimension], mode="reduced")
    return float(np.square(qa.T @ qb).sum() / dimension)


def serializable_adjudication(result: dict) -> dict:
    first = next((i + 1 for i, value in enumerate(result["common"]) if not value), None)
    sketches = {}
    for sketch in "AB":
        item = result["per_sketch"][sketch]
        sketches[sketch] = {
            "signal_supported": item["signal"].astype(bool).tolist(),
            "stability_supported": item["stability"].astype(bool).tolist(),
            "predictability_supported": item["predictability"].astype(bool).tolist(),
            "jointly_supported": item["jointly"].astype(bool).tolist(),
            "first_unsupported_dimension": next((i + 1 for i, value in enumerate(item["jointly"]) if not value), None),
        }
    return {
        "sketches": sketches,
        "joint_support": np.asarray(result["common"], bool).tolist(),
        "first_jointly_unsupported_dimension": first,
        "lawful_contiguous_prefix": result["prefix"],
        "lawful_contiguous_prefix_end": result["prefix"][-1] if result["prefix"] else None,
        "one_se_best_dimension": result["best"],
        "one_se_candidate": result["candidate"],
        "one_se_interval": result["interval"],
        "one_se_interval_bounds": [min(result["interval"]), max(result["interval"])] if result["interval"] else None,
        "one_se_threshold": result["threshold"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--all", required=True)
    parser.add_argument("--cap1024", required=True)
    parser.add_argument("--analytic", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    freeze, all_root, cap_root, analytic, out = map(lambda value: Path(value).resolve(), (args.freeze, args.all, args.cap1024, args.analytic, args.out))
    if out.exists():
        raise RuntimeError("refusing to overwrite independent adjudication")
    staging = out.with_name(out.name + ".staging")
    staging.mkdir(parents=True, exist_ok=False)
    if sha(freeze / "REFIT_NULL_SENSITIVITY_FREEZE_MANIFEST.csv") != FREEZE_ROOT:
        raise RuntimeError("freeze root mismatch")
    contract = json.loads((freeze / "PROSPECTIVE_REFIT_NULL_NATURAL_WEIGHT_FULL_FEATURE_SENSITIVITY_V1.json").read_text())
    if contract["selector"]["dimensions"] != "literal integers 1..320" or contract["nested_sampling"]["cap_roles"].split(";")[1].strip() != "ALL is the only selecting population":
        raise RuntimeError("selector authority mismatch")
    if json.loads((all_root / "RUN_STATE.json").read_text())["status"] != "ALL_COMPLETE_AWAITING_INDEPENDENT_REAL_RESULT_VALIDATION":
        raise RuntimeError("ALL terminal state unavailable")

    all_cap = load_cap(all_root, "ALL", "FULL104_BLOCK_MAJOR_ALL_MANIFEST.csv", ("monitoring/",))
    cap1024 = load_cap(cap_root, "1024", "FULL512_SENSITIVITY_CAP_MANIFEST.csv")
    all_result, cap_result = adjudicate_vectorized(all_cap), adjudicate_vectorized(cap1024)
    all_loop, cap_loop = adjudicate_loop(all_cap), adjudicate_loop(cap1024)
    if all_result["prefix"] != all_loop["prefix"] or all_result["candidate"] != all_loop["candidate"] or cap_result["prefix"] != cap_loop["prefix"] or cap_result["candidate"] != cap_loop["candidate"]:
        raise RuntimeError("independent calculation paths disagree")
    for sketch in "AB":
        if not np.array_equal(all_result["per_sketch"][sketch]["jointly"], np.asarray(all_loop["joint"][sketch])):
            raise RuntimeError("independent boolean paths disagree")

    all_serial = serializable_adjudication(all_result)
    cap_serial = serializable_adjudication(cap_result)
    same_endpoint = all_serial["lawful_contiguous_prefix_end"] == cap_serial["lawful_contiguous_prefix_end"]
    same_candidate = all_serial["one_se_candidate"] == cap_serial["one_se_candidate"]
    intervals_overlap = bool(all_result["interval"] and cap_result["interval"] and max(min(all_result["interval"]), min(cap_result["interval"])) <= min(max(all_result["interval"]), max(cap_result["interval"])))
    comparison_dimension = max(value for value in (all_result["candidate"], cap_result["candidate"]) if value is not None) if all_result["candidate"] is not None and cap_result["candidate"] is not None else None
    prediction = None
    overlaps, floors = {}, {}
    support_through_failure = {}
    if comparison_dimension is not None:
        delta = all_result["paired"][:, comparison_dimension - 1] - cap_result["paired"][:, comparison_dimension - 1]
        all_values = all_result["paired"][:, comparison_dimension - 1]
        prediction = {
            "dimension": comparison_dimension,
            "ALL_mean": float(all_values.mean()),
            "cap1024_mean": float(cap_result["paired"][:, comparison_dimension - 1].mean()),
            "paired_delta_mean": float(delta.mean()),
            "paired_delta_se": float(delta.std(ddof=1) / math.sqrt(len(delta))),
            "ALL_donor_se": float(all_values.std(ddof=1) / math.sqrt(len(all_values))),
            "cap1024_within_one_ALL_donor_se": bool(float(cap_result["paired"][:, comparison_dimension - 1].mean()) >= float(all_values.mean() - all_values.std(ddof=1) / math.sqrt(len(all_values)))),
        }
        for sketch in "AB":
            overlaps[sketch] = overlap(cap1024["sketches"][sketch]["components"], all_cap["sketches"][sketch]["components"], comparison_dimension)
            values = all_cap["sketches"][sketch]["observed_stability"][:, comparison_dimension - 1]
            floors[sketch] = float(values.mean() - values.std(ddof=1) / math.sqrt(len(values)))
    for sketch in "AB":
        stop = max(filter(None, (all_serial["sketches"][sketch]["first_unsupported_dimension"], cap_serial["sketches"][sketch]["first_unsupported_dimension"])), default=320)
        support_through_failure[sketch] = bool(np.array_equal(all_result["per_sketch"][sketch]["jointly"][:stop], cap_result["per_sketch"][sketch]["jointly"][:stop]))
    subspace_pass = comparison_dimension is not None and all(overlaps[s] >= floors[s] for s in "AB")
    convergence_pass = bool(same_endpoint and same_candidate and intervals_overlap and prediction and prediction["cap1024_within_one_ALL_donor_se"] and subspace_pass and all(support_through_failure.values()))

    calibration_rows = []
    for name, result in (("ALL", all_result), ("1024", cap_result)):
        for sketch in "AB":
            item = result["per_sketch"][sketch]
            for index in range(320):
                calibration_rows.append({"population": name, "sketch": sketch, "dimension": index + 1, "signal_supported": bool(item["signal"][index]), "stability_supported": bool(item["stability"][index]), "predictability_supported": bool(item["predictability"][index]), "jointly_supported": bool(item["jointly"][index]), "signal_margin": float(item["signal_margin_local"][index]), "stability_margin": float(item["stability_margin"][index]), "predictability_margin": float(item["predictability_margin"][index]), "paired_heldout_mean": float(result["paired_mean"][index]), "paired_heldout_se": float(result["paired_se"][index]), "one_se_margin": float(result["paired_mean"][index] - result["threshold"]) if result["threshold"] is not None else None})
    calibration_path = staging / "INDEPENDENT_FULL104_REFIT_NULL_CALIBRATION.csv"
    pd.DataFrame(calibration_rows).to_csv(calibration_path, index=False, lineterminator="\n")

    diagnostic_files = [analytic / "SHARED_SOURCE_SENSITIVITY.csv", analytic / "SHARED_PHYSICAL_SUPPORT_SENSITIVITY.csv", analytic / "SHARED_LEVEL4_ANALYTIC_DIAGNOSTIC_MANIFEST.csv"]
    diagnostic_status = {path.name: {"exists": path.exists(), "sha256": sha(path) if path.exists() else None} for path in diagnostic_files}
    if not all(item["exists"] for item in diagnostic_status.values()):
        raise RuntimeError("required nonselecting diagnostic artifact missing")
    routing = "QUALIFIED_SHARED_CANDIDATE_AWAITING_COUNCIL"
    if not all_result["prefix"]:
        routing = "TEACHER_BIOLOGY_LIMIT"
    elif len(all_result["prefix"]) == 320:
        routing = "STOP_SEARCH_BOUNDARY_REACHED"
    elif not convergence_pass:
        routing = "FULL104_REACHED_NOT_CONVERGED"
    result = {
        "schema": "independent-full104-refit-null-real-result-adjudication-v1",
        "status": routing,
        "result_state": "QUALIFIED" if routing == "QUALIFIED_SHARED_CANDIDATE_AWAITING_COUNCIL" else "PROVISIONAL",
        "frozen": False,
        "downstream_consumable": False,
        "production_selection_opened": False,
        "production_calibration_opened": False,
        "ALL": all_serial,
        "cap1024": cap_serial,
        "cap1024_to_ALL_convergence": {"pass": convergence_pass, "same_prefix_endpoint": same_endpoint, "same_one_se_candidate": same_candidate, "one_se_intervals_overlap": intervals_overlap, "predictability": prediction, "principal_subspace_overlap": overlaps, "ALL_bootstrap_one_se_stability_floor": floors, "subspace_pass": subspace_pass, "same_support_through_first_failure": support_through_failure},
        "independent_path_agreement": {"vectorized_vs_dimension_loop_booleans_exact": True, "candidate_exact": True},
        "required_nonselecting_diagnostics": diagnostic_status,
        "manifest_integrity": {"ALL": all_cap["manifest_audit"], "cap1024": cap1024["manifest_audit"]},
        "input_hashes": {"freeze_root": FREEZE_ROOT, "ALL_manifest": all_cap["manifest_audit"]["manifest_sha256"], "ALL_scientific_subset": all_cap["manifest_audit"]["scientific_subset_sha256"], "cap1024_manifest": cap1024["manifest_audit"]["manifest_sha256"], "cap1024_scientific_subset": cap1024["manifest_audit"]["scientific_subset_sha256"], "analytic_manifest": sha(analytic / "SHARED_LEVEL4_ANALYTIC_DIAGNOSTIC_MANIFEST.csv"), "code": sha(Path(__file__))},
    }
    result_path = staging / "INDEPENDENT_FULL104_REAL_RESULT_ADJUDICATION.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = staging / "INDEPENDENT_FULL104_REAL_RESULT_MANIFEST.csv"
    rows = []
    for path in (result_path, calibration_path, Path(__file__).resolve()):
        rows.append({"path": str(path if path == Path(__file__).resolve() else path.relative_to(staging)), "bytes": path.stat().st_size, "sha256": sha(path)})
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "bytes", "sha256"], lineterminator="\n"); writer.writeheader(); writer.writerows(rows); stream.flush(); os.fsync(stream.fileno())
    (staging / "INDEPENDENT_FULL104_REAL_RESULT_ROOT_SHA256.txt").write_text(sha(manifest) + "\n", encoding="ascii")
    os.replace(staging, out)
    print(json.dumps({"status": routing, "candidate": all_result["candidate"], "prefix_end": all_serial["lawful_contiguous_prefix_end"], "convergence": convergence_pass, "manifest_sha256": sha(out / manifest.name)}, indent=2))


if __name__ == "__main__":
    main()
