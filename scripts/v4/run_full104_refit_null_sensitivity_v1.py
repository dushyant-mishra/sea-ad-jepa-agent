#!/usr/bin/env python3
"""Resumable production runner for the frozen FULL104 refit-null sensitivity."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import inspect
import time
from pathlib import Path

import numpy as np
import pandas as pd

from full104_refit_null_sensitivity_core_v1 import (
    DONORS, FEATURE_DIM, RANK, build_nested_plan, heldout_predictability,
    fit_basis_checked, null_between_one, null_mapping_sha256, overlap_curve,
    select_dimension, source_stratified_bootstrap, signal_supported, validate_plan,
    weighted_moments,
)


EXPECTED_FREEZE_ROOT = "593e14872b6fe07d3f2855a49dd8eac57bfa5819465b8801b801dd9f6d4b510c"
PLAN_COLUMNS = {
    "row_index": np.int64, "selection_row": np.int64, "donor_id": "U",
    "operator_index": np.int64, "stratum_n": np.int64, "stratum_m": np.int64,
    "sample_rank": np.int64, "within_donor_weight": np.float64,
    "global_weight": np.float64,
}
OBSERVED_PAYLOAD_FIELDS = ("mean", "within", "between", "components", "eigenvalues", "bootstrap_eigen", "bootstrap_stability", "heldout", "numerical_diagnostics_json")
NULL_PAYLOAD_FIELDS = ("null_full_eigenvalues", "paired_null_bootstrap_eigenvalues", "stability", "heldout", "numerical_diagnostics_json")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, value) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def atomic_npz(path: Path, **arrays) -> None:
    tmp = path.with_suffix(".tmp.npz")
    np.savez_compressed(tmp, **arrays)
    os.replace(tmp, path)


def canonical_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def array_sha(*arrays) -> str:
    digest = hashlib.sha256()
    for array in arrays:
        value = np.ascontiguousarray(array)
        digest.update(str(value.dtype).encode()); digest.update(str(value.shape).encode()); digest.update(value.tobytes())
    return digest.hexdigest()


def checkpoint_identity(implementation_fingerprint: str, gate_manifest_sha256: str,
                        input_hashes: dict, cap: str, sketch: str, replicate: int,
                        plan_sha256: str, plan_semantic_sha256: str,
                        moment_sha256: str, mapping_sha256: str) -> dict:
    return {"freeze_root": EXPECTED_FREEZE_ROOT, "implementation_fingerprint": implementation_fingerprint,
            "gate_manifest_sha256": gate_manifest_sha256, "input_hashes_sha256": canonical_sha(input_hashes),
            "cap": str(cap), "sketch": str(sketch), "replicate": int(replicate),
            "plan_sha256": plan_sha256, "plan_semantic_sha256": plan_semantic_sha256,
            "moment_sha256": moment_sha256, "mapping_sha256": mapping_sha256}


def assert_checkpoint_identity(checkpoint, expected: dict) -> None:
    for key, value in expected.items():
        if key not in checkpoint:
            raise RuntimeError(f"checkpoint identity missing {key}")
        actual = checkpoint[key].item()
        if str(actual) != str(value):
            raise RuntimeError(f"checkpoint identity mismatch: {key}")


def checkpoint_identity_arrays(identity: dict) -> dict:
    return {key: np.asarray(value) for key, value in identity.items()}


def semantic_payload_sha(payload: dict) -> str:
    digest = hashlib.sha256()
    for key in sorted(payload):
        value = np.ascontiguousarray(payload[key]); digest.update(key.encode()); digest.update(str(value.dtype).encode()); digest.update(str(value.shape).encode()); digest.update(value.tobytes())
    return digest.hexdigest()


def plan_arrays(plan: pd.DataFrame) -> dict:
    if set(plan.columns) != set(PLAN_COLUMNS):
        raise RuntimeError("lossless plan column mismatch")
    return {column: np.ascontiguousarray(plan[column].astype(str).to_numpy(dtype="U") if dtype == "U" else plan[column].to_numpy(dtype=dtype))
            for column, dtype in PLAN_COLUMNS.items()}


def plan_semantic_sha256(plan: pd.DataFrame) -> str:
    return semantic_payload_sha(plan_arrays(plan))


def write_lossless_plan(path: Path, plan: pd.DataFrame) -> tuple[str, str]:
    arrays = plan_arrays(plan); atomic_npz(path, **arrays)
    return sha(path), semantic_payload_sha(arrays)


def load_lossless_plan(path: Path, expected_file_sha256: str | None = None,
                       expected_semantic_sha256: str | None = None) -> tuple[pd.DataFrame, str, str]:
    actual_file_sha256 = sha(path)
    if expected_file_sha256 is not None and actual_file_sha256 != expected_file_sha256:
        raise RuntimeError("lossless plan file hash mismatch")
    with np.load(path, allow_pickle=False) as payload:
        if set(payload.files) != set(PLAN_COLUMNS):
            raise RuntimeError("lossless plan payload mismatch")
        arrays = {column: np.ascontiguousarray(payload[column]) for column in PLAN_COLUMNS}
    for column, dtype in PLAN_COLUMNS.items():
        exact = arrays[column].dtype.kind == "U" if dtype == "U" else arrays[column].dtype == np.dtype(dtype)
        if not exact:
            raise RuntimeError(f"lossless plan dtype mismatch: {column}")
    actual_semantic_sha256 = semantic_payload_sha(arrays)
    if expected_semantic_sha256 is not None and actual_semantic_sha256 != expected_semantic_sha256:
        raise RuntimeError("lossless plan semantic hash mismatch")
    return pd.DataFrame({column: arrays[column] for column in PLAN_COLUMNS}), actual_file_sha256, actual_semantic_sha256


def assert_plan_exact(expected: pd.DataFrame, actual: pd.DataFrame) -> None:
    left, right = plan_arrays(expected), plan_arrays(actual)
    for column in PLAN_COLUMNS:
        if not np.array_equal(left[column], right[column]):
            raise RuntimeError(f"lossless plan deterministic rebuild mismatch: {column}")


def checkpoint_payload_sha256(payload: dict) -> str:
    return semantic_payload_sha(payload)


def assert_checkpoint_payload(checkpoint, fields: tuple[str, ...], expected_ledger_sha256: str) -> None:
    payload = {field: np.asarray(checkpoint[field]) for field in fields}
    actual = checkpoint_payload_sha256(payload)
    if "payload_semantic_sha256" not in checkpoint or str(checkpoint["payload_semantic_sha256"].item()) != actual:
        raise RuntimeError("checkpoint payload self-hash mismatch")
    if actual != expected_ledger_sha256:
        raise RuntimeError("checkpoint payload ledger mismatch")


def load_checkpoint_ledger(path: Path, implementation_fingerprint: str, plan_sha256: str,
                           plan_semantic_sha256: str) -> dict:
    expected = {"schema": "full104-checkpoint-payload-ledger-v1", "implementation_fingerprint": implementation_fingerprint,
                "plan_sha256": plan_sha256, "plan_semantic_sha256": plan_semantic_sha256}
    if path.exists():
        ledger = json.loads(path.read_text())
        if any(ledger.get(key) != value for key, value in expected.items()) or not isinstance(ledger.get("entries"), dict):
            raise RuntimeError("checkpoint payload ledger identity mismatch")
        return ledger
    return {**expected, "entries": {}}


def record_checkpoint_payload(ledger_path: Path, ledger: dict, relative_path: str, payload_sha256: str) -> None:
    prior = ledger["entries"].get(relative_path)
    if prior is not None and prior != payload_sha256:
        raise RuntimeError("checkpoint payload ledger overwrite mismatch")
    ledger["entries"][relative_path] = payload_sha256
    atomic_json(ledger_path, ledger)


def verify_gate_implementation(gate: Path) -> tuple[str, str]:
    status_path = gate / "IMPLEMENTATION_PREFLIGHT_STATUS.json"; manifest = gate / "IMPLEMENTATION_GATE_MANIFEST.csv"
    components_path = gate / "IMPLEMENTATION_COMPONENTS.json"
    status = json.loads(status_path.read_text()); component_package = json.loads(components_path.read_text()); components = component_package["components"]
    if status.get("status") != "PASS_IMPLEMENTATION_AND_COMPUTE_GATE" or status.get("freeze_root") != EXPECTED_FREEZE_ROOT:
        raise RuntimeError("implementation preflight gate unavailable")
    if status.get("gate_manifest_sha256") != sha(manifest) or status.get("implementation_fingerprint") != canonical_sha(components):
        raise RuntimeError("implementation gate fingerprint/manifest mismatch")
    core_path = Path(inspect.getsourcefile(fit_basis_checked)).resolve()
    from derive_full104_phase2_shared_state import fit_basis as authenticated_fit_basis
    fit_basis_path = Path(inspect.getsourcefile(authenticated_fit_basis)).resolve()
    current = {"runner_sha256": sha(Path(__file__).resolve()), "core_sha256": sha(core_path),
               "fit_basis_code_sha256": sha(fit_basis_path)}
    if any(components.get(key) != value for key, value in current.items()):
        raise RuntimeError("current implementation does not match approved gate")
    return status["implementation_fingerprint"], sha(manifest)


def diagnostic_summary(diagnostics: list[dict]) -> dict:
    return {"fits": len(diagnostics), "all_finite": all(x["finite"] for x in diagnostics),
            "maximum_condition": max(x["condition"] for x in diagnostics),
            "maximum_generalized_residual": max(x["maximum_generalized_residual"] for x in diagnostics),
            "maximum_metric_orthogonality": max(x["metric_orthogonality"] for x in diagnostics),
            "minimum_metric_eigenvalue": min(x["minimum_metric_eigenvalue"] for x in diagnostics),
            "minimum_tolerance_margin": min(x["tolerance"] - max(x["maximum_generalized_residual"], x["metric_orthogonality"]) for x in diagnostics)}


def aggregate_numerical_diagnostics(out: Path) -> dict:
    records = []
    for path in sorted(out.glob("OBSERVED_FULL512_*.npz")) + sorted(out.glob("null_replicates_*/replicate_*.npz")):
        with np.load(path, allow_pickle=False) as payload:
            item = json.loads(str(payload["numerical_diagnostics_json"].item()))
        item["checkpoint"] = str(path.relative_to(out)); records.append(item)
    if not records:
        raise RuntimeError("no numerical diagnostics available")
    result = {"status": "PASS_ALL_FITS_NUMERICALLY_GATED", "checkpoint_summaries": len(records),
              "total_fits": sum(x["fits"] for x in records), "all_finite": all(x["all_finite"] for x in records),
              "maximum_condition": max(x["maximum_condition"] for x in records),
              "maximum_generalized_residual": max(x["maximum_generalized_residual"] for x in records),
              "maximum_metric_orthogonality": max(x["maximum_metric_orthogonality"] for x in records),
              "minimum_metric_eigenvalue": min(x["minimum_metric_eigenvalue"] for x in records),
              "minimum_tolerance_margin": min(x["minimum_tolerance_margin"] for x in records)}
    if not result["all_finite"] or result["minimum_metric_eigenvalue"] <= 0 or result["minimum_tolerance_margin"] < 0:
        raise RuntimeError("per-cap numerical diagnostic aggregation failed")
    atomic_json(out / "NUMERICAL_FIT_DIAGNOSTICS.json", result)
    return result


def load_authority(freeze_dir: Path, matrix: Path, analytic: Path):
    if sha(freeze_dir / "REFIT_NULL_SENSITIVITY_FREEZE_MANIFEST.csv") != EXPECTED_FREEZE_ROOT:
        raise RuntimeError("sensitivity freeze root mismatch")
    contract = json.loads((freeze_dir / "PROSPECTIVE_REFIT_NULL_NATURAL_WEIGHT_FULL_FEATURE_SENSITIVITY_V1.json").read_text())
    audit = json.loads((matrix / "PHASE2_FEATURE_MATRIX_AUDIT.json").read_text())
    if contract["status"] != "FROZEN_PROSPECTIVELY_BEFORE_ANY_SENSITIVITY_RESULT" or audit["rows"] != 4_553_407 or audit["feature_dim"] != FEATURE_DIM:
        raise RuntimeError("frozen input contract mismatch")
    checks = {
        "feature_matrix_manifest": (matrix / "PHASE2_FEATURE_MATRIX_MANIFEST.csv", contract["input_hashes"]["feature_matrix_manifest"]),
        "analytic_diagnostic_manifest": (analytic / "SHARED_LEVEL4_ANALYTIC_DIAGNOSTIC_MANIFEST.csv", contract["input_hashes"]["analytic_diagnostic_manifest"]),
        "rng_keys": (matrix.parent / "preexpression_freeze/PHASE2_RNG_KEYS.json", contract["input_hashes"]["rng_keys"]),
        "donor_folds": (matrix.parent / "preexpression_freeze/PHASE2_DONOR_FOLDS.csv", contract["input_hashes"]["donor_folds"]),
    }
    for name, (path, expected) in checks.items():
        if sha(path) != expected:
            raise RuntimeError(f"{name} hash mismatch")
    return contract, {name: sha(path) for name, (path, _) in checks.items()}


def fit_observed(mean, within, between, folds, sources, bootstrap_key, context="observed"):
    diagnostics = []
    all_donors = np.arange(len(mean)); basis, diagnostic = fit_basis_checked(mean, within, between, all_donors, RANK, context + ":full"); diagnostics.append(diagnostic)
    eigen = np.empty((256, RANK), np.float64); stability = np.empty_like(eigen)
    for replicate in range(256):
        sampled = source_stratified_bootstrap(sources, bootstrap_key, replicate)
        fitted, diagnostic = fit_basis_checked(mean, within, between, sampled, RANK, f"{context}:bootstrap={replicate}"); diagnostics.append(diagnostic)
        eigen[replicate] = fitted["eigenvalues"]; stability[replicate] = overlap_curve(basis["q"], fitted["q"])
    held = heldout_predictability(mean, within, between, folds, diagnostics=diagnostics, context=context + ":heldout")
    return basis, eigen, stability, held, diagnostic_summary(diagnostics)


def null_replicate(mean, within, between, basis, folds, sources, bootstrap_key, replicate, context="null"):
    diagnostics = []
    all_donors = np.arange(len(mean)); fitted, diagnostic = fit_basis_checked(mean, within, between, all_donors, RANK, context + ":full"); diagnostics.append(diagnostic)
    sampled = source_stratified_bootstrap(sources, bootstrap_key, replicate)
    boot, diagnostic = fit_basis_checked(mean, within, between, sampled, RANK, context + ":paired_bootstrap"); diagnostics.append(diagnostic)
    stability = overlap_curve(fitted["q"], boot["q"])
    held = heldout_predictability(mean, within, between, folds, diagnostics=diagnostics, context=context + ":heldout")
    return fitted["eigenvalues"], boot["eigenvalues"], stability, held, diagnostic_summary(diagnostics)


def aggregate_selection(out: Path, observed: dict) -> dict:
    null_eigen, null_stability, null_held, calibration = {}, {}, {}, []
    for label in "AB":
        files = sorted((out / f"null_replicates_{label}").glob("replicate_*.npz"))
        if len(files) != 256:
            raise RuntimeError(f"incomplete null replicates for {label}")
        payload = [np.load(path, allow_pickle=False) for path in files]
        null_eigen[label] = np.stack([x["null_full_eigenvalues"] for x in payload])
        paired_null_bootstrap_eigen = np.stack([x["paired_null_bootstrap_eigenvalues"] for x in payload])
        null_stability[label] = np.stack([x["stability"] for x in payload])
        null_held[label] = np.stack([x["heldout"] for x in payload])
        oe, ost, oh = observed[label]["eigen"], observed[label]["stability"], observed[label]["held"]
        oe_m, oe_se = oe.mean(0), oe.std(0, ddof=1) / math.sqrt(len(oe))
        signal_curve = signal_supported(oe, paired_null_bootstrap_eigen)
        for j in range(RANK):
            signal = bool(signal_curve[j])
            stability = bool(ost[:, j].mean() - ost[:, j].std(ddof=1) / 16 > null_stability[label][:, j].mean() + null_stability[label][:, j].std(ddof=1) / 16)
            null_donor = null_held[label][:, :, j].mean(0)
            predict = bool(oh[:, j].mean() - oh[:, j].std(ddof=1) / math.sqrt(DONORS) > null_donor.mean() + null_donor.std(ddof=1) / math.sqrt(DONORS))
            calibration.append({"sketch": label, "dimension": j + 1, "signal_supported": signal, "stability_supported": stability,
                                "predictability_supported": predict, "jointly_supported": signal and stability and predict})
    table = pd.DataFrame(calibration); table.to_csv(out / "FULL512_REFIT_NULL_CALIBRATION.csv", index=False, lineterminator="\n")
    selection = select_dimension(table, observed["A"]["held"], observed["B"]["held"])
    selection["calibration_sha256"] = sha(out / "FULL512_REFIT_NULL_CALIBRATION.csv")
    atomic_json(out / "FULL512_REFIT_NULL_SELECTION.json", selection)
    return selection


def run_cap(args, contract, input_hashes, implementation_fingerprint, gate_manifest_sha256):
    matrix, analytic, out = Path(args.matrix).resolve(), Path(args.analytic).resolve(), Path(args.out).resolve()
    cap = None if args.cap.upper() == "ALL" else int(args.cap); cap_label = "ALL" if cap is None else str(cap)
    out.mkdir(parents=True, exist_ok=True)
    state_path = out / "RUN_STATE.json"
    rows = pd.read_csv(matrix / "PHASE2_FEATURE_ROWS.csv", dtype={"donor_id": str})
    rng = json.loads((matrix.parent / "preexpression_freeze/PHASE2_RNG_KEYS.json").read_text())["keys"]
    plan_path = out / "NESTED_WEIGHTED_SELECTION.npz"
    plan_csv = out / "NESTED_WEIGHTED_SELECTION.csv"
    plan_authority_path = out / "LOSSLESS_PLAN_AUTHORITY.json"
    plan_expected = build_nested_plan(rows, cap, rng["matched_null"])
    expected_dtypes = {column: str(array.dtype) for column, array in plan_arrays(plan_expected).items()}
    expected_authority_identity = {"schema": "full104-lossless-plan-authority-v1", "format": "atomic-npz-columnar-v1",
        "cap": cap_label, "rng_key_sha256": hashlib.sha256(rng["matched_null"].encode()).hexdigest(),
        "column_dtypes": expected_dtypes, "csv_authoritative": False, "weights_dtype": "float64"}
    if plan_path.exists():
        if not plan_authority_path.is_file():
            raise RuntimeError("lossless plan authority missing")
        authority = json.loads(plan_authority_path.read_text())
        if any(authority.get(key) != value for key, value in expected_authority_identity.items()):
            raise RuntimeError("lossless plan authority invalid")
        plan, plan_sha256, plan_semantic_sha = load_lossless_plan(
            plan_path, authority["plan_file_sha256"], authority["plan_semantic_sha256"])
        assert_plan_exact(plan_expected, plan)
    else:
        if plan_authority_path.exists():
            raise RuntimeError("lossless plan file missing but authority exists")
        plan_memory = plan_expected
        plan_sha256, plan_semantic_sha = write_lossless_plan(plan_path, plan_memory)
        plan, reloaded_file_sha, reloaded_semantic_sha = load_lossless_plan(plan_path, plan_sha256, plan_semantic_sha)
        memory_arrays, reload_arrays = plan_arrays(plan_memory), plan_arrays(plan)
        if any(not np.array_equal(memory_arrays[column], reload_arrays[column]) for column in PLAN_COLUMNS):
            raise RuntimeError("lossless plan in-memory/reload mismatch")
        if reloaded_file_sha != plan_sha256 or reloaded_semantic_sha != plan_semantic_sha:
            raise RuntimeError("lossless plan immediate reload hash mismatch")
        plan_memory.to_csv(plan_csv, index=False, lineterminator="\n")
        atomic_json(plan_authority_path, {**expected_authority_identity,
                    "plan_file": plan_path.name, "plan_file_sha256": plan_sha256,
                    "plan_semantic_sha256": plan_semantic_sha, "csv_file": plan_csv.name,
                    })
    plan_audit = validate_plan(plan, rows); plan_audit.update({"cap": cap_label, "plan_sha256": plan_sha256,
        "plan_semantic_sha256": plan_semantic_sha, "plan_format": "atomic-npz-columnar-v1", "csv_authoritative": False,
        "implementation_fingerprint": implementation_fingerprint})
    atomic_json(out / "WEIGHT_AND_SELECTION_AUDIT.json", plan_audit)
    code_hash = sha(Path(__file__))
    state = {"schema": "full104-full512-sensitivity-run-state-v2", "cap": cap_label, "code_sha256": code_hash,
             "implementation_fingerprint": implementation_fingerprint, "gate_manifest_sha256": gate_manifest_sha256,
             "plan_sha256": plan_sha256, "plan_semantic_sha256": plan_semantic_sha,
             "freeze_root": EXPECTED_FREEZE_ROOT,
             "input_hashes": input_hashes, "status": "RUNNING"}
    if state_path.exists():
        old = json.loads(state_path.read_text())
        keys = ("schema", "cap", "code_sha256", "freeze_root", "input_hashes", "implementation_fingerprint", "gate_manifest_sha256", "plan_sha256", "plan_semantic_sha256")
        if any(old.get(k) != state.get(k) for k in keys):
            raise RuntimeError("resume state mismatch")
    else:
        atomic_json(state_path, state)
    ledger_path = out / "CHECKPOINT_PAYLOAD_LEDGER.json"
    ledger = load_checkpoint_ledger(ledger_path, implementation_fingerprint, plan_sha256, plan_semantic_sha)
    donor_ids = sorted(rows.donor_id.unique()); donor_sources = np.asarray([rows.loc[rows.donor_id.eq(d), "source"].iloc[0] for d in donor_ids])
    folds_table = pd.read_csv(matrix.parent / "preexpression_freeze/PHASE2_DONOR_FOLDS.csv", dtype={"donor_id": str}).set_index("donor_id")
    folds = np.asarray([int(folds_table.loc[d, "outer_fold"]) for d in donor_ids])
    observed = {}
    for label in "AB":
        obs_path = out / f"OBSERVED_FULL512_{label}.npz"
        views = np.load(matrix / f"{label}_views.npy", mmap_mode="r")
        if obs_path.exists():
            saved = np.load(obs_path, allow_pickle=False); mean, within, between = saved["mean"], saved["within"], saved["between"]
            relative = str(obs_path.relative_to(out)); ledger_sha = ledger["entries"].get(relative)
            if ledger_sha is None: raise RuntimeError("observed checkpoint missing from payload ledger")
            assert_checkpoint_payload(saved, OBSERVED_PAYLOAD_FIELDS, ledger_sha)
            moment_sha256 = array_sha(mean, within, between)
            expected = checkpoint_identity(implementation_fingerprint, gate_manifest_sha256, input_hashes, cap_label, label, -1, plan_sha256, plan_semantic_sha, moment_sha256, "OBSERVED")
            assert_checkpoint_identity(saved, expected)
            basis, _ = fit_basis_checked(mean, within, between, np.arange(DONORS), RANK, f"resume:{cap_label}:{label}:observed:full")
            eigen, stability, held = saved["bootstrap_eigen"], saved["bootstrap_stability"], saved["heldout"]
            observed_diagnostics = json.loads(str(saved["numerical_diagnostics_json"].item()))
        else:
            if cap is None:
                stats = analytic / "sufficient_statistics"
                mean = np.asarray(np.load(stats / f"{label}_mean.npy", mmap_mode="r"), np.float64)
                within = np.asarray(np.load(stats / f"{label}_within.npy", mmap_mode="r"), np.float64)
                between = np.asarray(np.load(stats / f"{label}_between.npy", mmap_mode="r"), np.float64)
            else:
                mean, within, between = weighted_moments(views, plan, donor_ids, args.device)
            moment_sha256 = array_sha(mean, within, between)
            expected = checkpoint_identity(implementation_fingerprint, gate_manifest_sha256, input_hashes, cap_label, label, -1, plan_sha256, plan_semantic_sha, moment_sha256, "OBSERVED")
            basis, eigen, stability, held, observed_diagnostics = fit_observed(
                mean, within, between, folds, donor_sources, rng["donor_bootstrap"], f"{cap_label}:{label}:observed")
            payload = {"mean": mean, "within": within, "between": between, "components": basis["components"].astype(np.float32),
                       "eigenvalues": basis["eigenvalues"], "bootstrap_eigen": eigen, "bootstrap_stability": stability, "heldout": held,
                       "numerical_diagnostics_json": np.asarray(json.dumps(observed_diagnostics, sort_keys=True))}
            payload_sha = checkpoint_payload_sha256(payload)
            atomic_npz(obs_path, **payload, payload_semantic_sha256=np.asarray(payload_sha), **checkpoint_identity_arrays(expected))
            record_checkpoint_payload(ledger_path, ledger, str(obs_path.relative_to(out)), payload_sha)
        observed[label] = {"mean": mean, "within": within, "between": between, "basis": basis, "eigen": eigen, "stability": stability, "held": held}
        rep_dir = out / f"null_replicates_{label}"; rep_dir.mkdir(exist_ok=True)
        for replicate in range(256):
            rep_path = rep_dir / f"replicate_{replicate:03d}.npz"
            expected_map_sha256 = null_mapping_sha256(plan, cap_label, label, replicate, rng["matched_null"])
            expected = checkpoint_identity(implementation_fingerprint, gate_manifest_sha256, input_hashes, cap_label, label, replicate, plan_sha256, plan_semantic_sha, moment_sha256, expected_map_sha256)
            if rep_path.exists():
                prior = np.load(rep_path, allow_pickle=False)
                relative = str(rep_path.relative_to(out)); ledger_sha = ledger["entries"].get(relative)
                if ledger_sha is None: raise RuntimeError("null checkpoint missing from payload ledger")
                assert_checkpoint_payload(prior, NULL_PAYLOAD_FIELDS, ledger_sha)
                assert_checkpoint_identity(prior, expected)
                continue
            started = time.time()
            null_between, map_hash = null_between_one(views, plan, donor_ids, cap_label, label, replicate, rng["matched_null"], args.device)
            if map_hash != expected_map_sha256:
                raise RuntimeError("null mapping plan/hash mismatch")
            full_eigenvalues, boot_eigenvalues, null_stab, null_held, null_diagnostics = null_replicate(
                mean, within, null_between, basis, folds, donor_sources, rng["donor_bootstrap"], replicate,
                f"{cap_label}:{label}:null={replicate}")
            payload = {"null_full_eigenvalues": full_eigenvalues, "paired_null_bootstrap_eigenvalues": boot_eigenvalues,
                       "stability": null_stab, "heldout": null_held.astype(np.float32),
                       "numerical_diagnostics_json": np.asarray(json.dumps(null_diagnostics, sort_keys=True))}
            payload_sha = checkpoint_payload_sha256(payload)
            atomic_npz(rep_path, **payload, payload_semantic_sha256=np.asarray(payload_sha),
                       wall_seconds=np.asarray(time.time() - started), **checkpoint_identity_arrays(expected))
            record_checkpoint_payload(ledger_path, ledger, str(rep_path.relative_to(out)), payload_sha)
            print(f"cap={cap_label} sketch={label} replicate={replicate + 1}/256", flush=True)
    selection = aggregate_selection(out, observed)
    numerical = aggregate_numerical_diagnostics(out)
    state.update({"status": "PASS_CAP_COMPLETE_NONSELECTING" if cap is not None else "PASS_ALL_COMPLETE_AWAITING_VALIDATION",
                  "selection": selection, "numerical_diagnostics": numerical, "completed_at": time.time()})
    atomic_json(state_path, state)
    manifest = out / "FULL512_SENSITIVITY_CAP_MANIFEST.csv"
    files = [path for path in out.rglob("*") if path.is_file() and path != manifest]
    pd.DataFrame([{"path": str(p.relative_to(out)), "bytes": p.stat().st_size, "sha256": sha(p)} for p in files]).to_csv(manifest, index=False, lineterminator="\n")
    print(json.dumps({"status": state["status"], "cap": cap_label, "selection": selection, "manifest_sha256": sha(manifest)}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", required=True); parser.add_argument("--matrix", required=True); parser.add_argument("--analytic", required=True)
    parser.add_argument("--gate", required=True); parser.add_argument("--cap", required=True); parser.add_argument("--out", required=True)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    freeze, matrix, analytic, gate = map(lambda x: Path(x).resolve(), [args.freeze, args.matrix, args.analytic, args.gate])
    contract, input_hashes = load_authority(freeze, matrix, analytic)
    implementation_fingerprint, gate_manifest_sha256 = verify_gate_implementation(gate)
    run_cap(args, contract, input_hashes, implementation_fingerprint, gate_manifest_sha256)


if __name__ == "__main__":
    main()
