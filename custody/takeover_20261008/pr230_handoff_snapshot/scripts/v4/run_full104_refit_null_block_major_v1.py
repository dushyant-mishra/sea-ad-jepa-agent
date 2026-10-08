#!/usr/bin/env python3
"""Block-major, replicate-independent executor for frozen FULL104 ALL nulls."""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import re
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch  # Load the authenticated CUDA/runtime DLL stack before SciPy eigensolvers.

import full104_refit_null_sensitivity_core_v1 as core
import run_full104_refit_null_sensitivity_v1 as sequential
from derive_full104_phase2_shared_state import fit_basis


EXPECTED_FREEZE_ROOT = sequential.EXPECTED_FREEZE_ROOT
OLD_FINGERPRINT = "26b8d20a57e107f7bdd56e775c0e5b51adc143a74b44c590bbad081556d54620"
EXPECTED_ALL_PLAN_SHA256 = "fc7249c4e1eafccc6a9535a30cd311e8b6fa6cf980b85c1c0a7607b65d611a21"
EXPECTED_ALL_PLAN_SEMANTIC_SHA256 = "132fa3c3b9594a742daa650497d7f212375056f104fdc087375349bcb35b6b20"
ACCUMULATOR_BYTES_PER_REPLICATE = 2 * core.DONORS * core.FEATURE_DIM * core.FEATURE_DIM * np.dtype(np.float64).itemsize


def sha(path: Path) -> str:
    return sequential.sha(path)


def atomic_json(path: Path, value) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
    os.replace(tmp, path)


def atomic_npy(path: Path, value: np.ndarray) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as stream:
        np.save(stream, value, allow_pickle=False)
        stream.flush(); os.fsync(stream.fileno())
    os.replace(tmp, path)


def sync_device(device: str) -> None:
    if str(device).startswith("cuda"):
        torch.cuda.synchronize(device)


def sorted_physical_host_restore(views: np.ndarray, logical_indices: np.ndarray):
    """Read in physical order and exactly restore float32 logical order on host."""
    logical_indices = np.asarray(logical_indices, dtype=np.int64)
    read_perm = np.argsort(logical_indices, kind="stable")
    physical_indices = logical_indices[read_perm]
    inverse = np.empty(len(logical_indices), np.int64); inverse[read_perm] = np.arange(len(logical_indices), dtype=np.int64)
    started = time.perf_counter(); host_physical = np.asarray(views[physical_indices], dtype=np.float32); read_seconds = time.perf_counter() - started
    started = time.perf_counter(); host_logical = np.ascontiguousarray(host_physical[inverse]); restore_seconds = time.perf_counter() - started
    del host_physical
    hashes = {"logical_row_order_sha256": hashlib.sha256(logical_indices.tobytes()).hexdigest(),
              "physical_read_order_sha256": hashlib.sha256(physical_indices.tobytes()).hexdigest()}
    return host_logical, hashes, read_seconds, restore_seconds


def sorted_physical_read_restore(views: np.ndarray, logical_indices: np.ndarray, device: str):
    """Transfer only the restored authoritative logical float32 buffer to device."""
    host_logical, hashes, read_seconds, restore_seconds = sorted_physical_host_restore(views, logical_indices)
    started = time.perf_counter(); base = torch.as_tensor(host_logical, device=device).double()
    sync_device(device); host_to_device_seconds = time.perf_counter() - started
    del host_logical
    return base, hashes, read_seconds, restore_seconds, host_to_device_seconds


def verify_block_gate(gate: Path) -> tuple[str, str]:
    status = json.loads((gate / "IMPLEMENTATION_PREFLIGHT_STATUS.json").read_text())
    manifest = gate / "IMPLEMENTATION_GATE_MANIFEST.csv"
    package = json.loads((gate / "IMPLEMENTATION_COMPONENTS.json").read_text()); components = package["components"]
    if status.get("status") != "PASS_IMPLEMENTATION_AND_COMPUTE_GATE" or status.get("freeze_root") != EXPECTED_FREEZE_ROOT:
        raise RuntimeError("block-major implementation gate unavailable")
    if status.get("gate_manifest_sha256") != sha(manifest) or status.get("implementation_fingerprint") != sequential.canonical_sha(components):
        raise RuntimeError("block-major gate hash mismatch")
    paths = {
        "runner_sha256": Path(__file__).resolve(),
        "sequential_helper_sha256": Path(inspect.getsourcefile(sequential)).resolve(),
        "core_sha256": Path(inspect.getsourcefile(core)).resolve(),
        "fit_basis_code_sha256": Path(inspect.getsourcefile(fit_basis)).resolve(),
    }
    if any(components.get(key) != sha(path) for key, path in paths.items()):
        raise RuntimeError("block-major current source mismatch")
    return status["implementation_fingerprint"], sha(manifest)


def load_frozen_all_plan(plan_dir: Path, rows: pd.DataFrame, null_key: str) -> tuple[pd.DataFrame, dict]:
    authority = json.loads((plan_dir / "LOSSLESS_PLAN_AUTHORITY.json").read_text())
    if authority["cap"] != "ALL" or authority["plan_file_sha256"] != EXPECTED_ALL_PLAN_SHA256 or authority["plan_semantic_sha256"] != EXPECTED_ALL_PLAN_SEMANTIC_SHA256:
        raise RuntimeError("ALL plan authority mismatch")
    plan, file_sha, semantic_sha = sequential.load_lossless_plan(
        plan_dir / authority["plan_file"], EXPECTED_ALL_PLAN_SHA256, EXPECTED_ALL_PLAN_SEMANTIC_SHA256)
    expected = core.build_nested_plan(rows, None, null_key)
    sequential.assert_plan_exact(expected, plan)
    core.validate_plan(plan, rows)
    return plan, {"plan_sha256": file_sha, "plan_semantic_sha256": semantic_sha}


def batch_identity(fingerprint: str, gate_manifest_sha256: str, matrix_manifest_sha256: str,
                   sketch: str, replicate_ids: list[int], batch_size: int, checkpoint_every_strata: int, plan_hashes: dict,
                   completed_replicate_hashes: dict | None = None) -> dict:
    return {"schema": "full104-block-major-batch-checkpoint-v1", "implementation_fingerprint": fingerprint,
            "gate_manifest_sha256": gate_manifest_sha256, "matrix_manifest_sha256": matrix_manifest_sha256,
            "plan_sha256": plan_hashes["plan_sha256"], "plan_semantic_sha256": plan_hashes["plan_semantic_sha256"],
            "sketch": sketch, "replicate_ids": replicate_ids, "batch_size": batch_size,
            "checkpoint_every_strata": int(checkpoint_every_strata),
            "completed_replicate_sha256": completed_replicate_hashes or {},
            "accumulator_dtype": "float64", "accumulator_shape": [len(replicate_ids), core.DONORS, core.FEATURE_DIM, core.FEATURE_DIM],
            "stratum_order": "pandas-groupby-donor_id-operator_index-sort-true"}


def save_batch_checkpoint(directory: Path, identity: dict, next_stratum: int,
                          between: np.ndarray, compensation: np.ndarray, map_hashes: dict,
                          fail_after: str | None = None) -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    current_path = directory / "CURRENT.json"
    current = json.loads(current_path.read_text()) if current_path.exists() else None
    existing_numbers = []
    for item in directory.glob("generation_*"):
        token = item.name.removesuffix(".staging").split("_")[-1]
        if token.isdigit(): existing_numbers.append(int(token))
    generation_number = (max(existing_numbers) + 1) if existing_numbers else 0
    name = f"generation_{generation_number:06d}"; staging = directory / f"{name}.staging"; generation = directory / name
    if staging.exists() or generation.exists(): raise RuntimeError("checkpoint generation collision")
    staging.mkdir()
    between_path, compensation_path = staging / "between.npy", staging / "compensation.npy"
    atomic_npy(between_path, between)
    if fail_after == "between": raise RuntimeError("injected snapshot failure after between")
    atomic_npy(compensation_path, compensation)
    if fail_after == "compensation": raise RuntimeError("injected snapshot failure after compensation")
    state = {**identity, "status": "INCOMPLETE_BATCH_CHECKPOINT", "next_stratum": int(next_stratum),
             "between_sha256": sha(between_path), "compensation_sha256": sha(compensation_path),
             "replicate_map_sha256": {str(k): v for k, v in map_hashes.items()}}
    atomic_json(staging / "BATCH_STATE.json", state)
    state_sha = sha(staging / "BATCH_STATE.json")
    os.replace(staging, generation)
    if fail_after == "generation": raise RuntimeError("injected snapshot failure after generation publish")
    pointer = {"schema": "full104-block-major-current-generation-v1", "generation": name,
               "generation_number": generation_number, "batch_state_sha256": state_sha}
    if fail_after == "pointer": raise RuntimeError("injected snapshot failure before pointer publish")
    atomic_json(current_path, pointer)
    # A failed new snapshot leaves the prior generation; after pointer publication,
    # older complete generations are no longer needed.
    for old in directory.glob("generation_[0-9][0-9][0-9][0-9][0-9][0-9]"):
        if old != generation and old.resolve().parent == directory.resolve(): shutil.rmtree(old)
    return state


def load_batch_checkpoint(directory: Path, expected_identity: dict, expected_map_hashes: dict) -> tuple[int, np.ndarray, np.ndarray] | None:
    current_path = directory / "CURRENT.json"
    if not current_path.exists():
        return None
    current = json.loads(current_path.read_text()); generation = directory / str(current["generation"])
    if generation.resolve().parent != directory.resolve() or not generation.is_dir(): raise RuntimeError("invalid checkpoint generation pointer")
    state_path = generation / "BATCH_STATE.json"
    if sha(state_path) != current.get("batch_state_sha256"): raise RuntimeError("checkpoint pointer/state hash mismatch")
    state = json.loads(state_path.read_text())
    for key, value in expected_identity.items():
        if state.get(key) != value: raise RuntimeError(f"batch checkpoint identity mismatch: {key}")
    if state.get("replicate_map_sha256") != {str(k): v for k, v in expected_map_hashes.items()}:
        raise RuntimeError("batch checkpoint replicate-map mismatch")
    between_path, compensation_path = generation / "between.npy", generation / "compensation.npy"
    if sha(between_path) != state["between_sha256"] or sha(compensation_path) != state["compensation_sha256"]:
        raise RuntimeError("partial or corrupt accumulator checkpoint")
    between = np.load(between_path, allow_pickle=False); compensation = np.load(compensation_path, allow_pickle=False)
    shape = tuple(expected_identity["accumulator_shape"])
    if between.dtype != np.float64 or compensation.dtype != np.float64 or between.shape != shape or compensation.shape != shape:
        raise RuntimeError("accumulator checkpoint dtype/shape mismatch")
    return int(state["next_stratum"]), between, compensation


def cleanup_stale_checkpoint_artifacts(directory: Path, expected_identity: dict, expected_map_hashes: dict) -> dict:
    """Remove only stale direct-child generations after validating CURRENT."""
    current_path = directory / "CURRENT.json"
    if not current_path.exists(): return {"removed": [], "current": None}
    load_batch_checkpoint(directory, expected_identity, expected_map_hashes)
    current = json.loads(current_path.read_text()); keep = str(current["generation"]); removed=[]
    for child in directory.iterdir():
        if child.name == keep or not child.is_dir(): continue
        if not re.fullmatch(r"generation_\d{6}(?:\.staging)?", child.name): continue
        if child.resolve().parent != directory.resolve(): raise RuntimeError("unsafe stale checkpoint cleanup target")
        shutil.rmtree(child); removed.append(child.name)
    return {"removed": sorted(removed), "current": keep}


OBSERVED_PAYLOAD_FIELDS = ("mean","within","between","components","eigenvalues","bootstrap_eigen","bootstrap_stability","heldout","numerical_diagnostics_json")
NULL_PAYLOAD_FIELDS = ("null_full_eigenvalues","paired_null_bootstrap_eigenvalues","stability","heldout","numerical_diagnostics_json")


def validate_scientific_payload(saved, fields: tuple[str, ...]) -> str:
    if any(field not in saved.files for field in fields) or "payload_semantic_sha256" not in saved.files:
        raise RuntimeError("scientific payload fields/hash missing")
    payload = {field: saved[field] for field in fields}
    actual = sequential.checkpoint_payload_sha256(payload); expected = str(saved["payload_semantic_sha256"])
    if actual != expected: raise RuntimeError("scientific payload semantic hash mismatch")
    return actual


def block_major_null_between_batch(views: np.ndarray, plan: pd.DataFrame, donor_ids: list[str], sketch: str,
                                   replicate_ids: list[int], null_key: str, device: str,
                                   start_stratum: int = 0, between: np.ndarray | None = None,
                                   compensation: np.ndarray | None = None, checkpoint_every: int = 0,
                                   checkpoint_callback=None) -> tuple[np.ndarray, dict, dict]:
    """Exact old arithmetic per replicate; only the stratum read is shared."""
    if len(replicate_ids) != len(set(replicate_ids)) or replicate_ids != sorted(replicate_ids):
        raise RuntimeError("replicate IDs must be unique and sorted")
    donor_ix = {d: i for i, d in enumerate(donor_ids)}; dim = int(views.shape[-1]); k = len(replicate_ids)
    shape = (k, len(donor_ids), dim, dim)
    if between is None: between = np.zeros(shape, np.float64)
    if compensation is None: compensation = np.zeros(shape, np.float64)
    if between.shape != shape or compensation.shape != shape or between.dtype != np.float64 or compensation.dtype != np.float64:
        raise RuntimeError("live accumulator dtype/shape mismatch")
    started = time.time(); logical_bytes = 0; strata_done = 0; read_seconds = 0.0; host_restore_seconds = 0.0; host_to_device_seconds = 0.0; null_compute_seconds = 0.0
    groups = plan.groupby(["donor_id", "operator_index"], sort=True)
    stratum_total = int(groups.ngroups)
    if start_stratum < 0 or start_stratum > stratum_total:
        raise RuntimeError("invalid checkpoint stratum position")
    for stratum, ((donor, _operator), group) in enumerate(groups):
        if stratum < start_stratum: continue
        d = donor_ix[str(donor)]; indices = group.row_index.to_numpy(np.int64); n = len(indices)
        # Disk traversal is physical-row-major; restore the frozen plan order before
        # any null mapping or arithmetic. Values and per-replicate operation order
        # are therefore identical to the sequential authority.
        base, _order_hashes, local_read, local_restore, local_h2d = sorted_physical_read_restore(views, indices, device)
        read_seconds += local_read; host_restore_seconds += local_restore; host_to_device_seconds += local_h2d
        logical_bytes += n * core.VIEWS * dim * 4
        compute_started = time.perf_counter()
        positions = np.arange(n); weight = float(group.within_donor_weight.iloc[0])
        for local, replicate in enumerate(replicate_ids):
            _os, _fs, order, offsets = core.null_stratum_mapping(n, null_key, "ALL", sketch, stratum, replicate)
            x = base[torch.as_tensor(order, device=device)]
            shifted = [x[torch.as_tensor((positions + offsets[v]) % n, device=device), v] for v in range(core.VIEWS)]
            cross = torch.zeros((dim, dim), dtype=torch.float64, device=device)
            for v in range(core.VIEWS):
                for w in range(v + 1, core.VIEWS):
                    product = shifted[v].T @ shifted[w]; cross += product + product.T
            core.kahan_add(between[local], compensation[local], weight * cross.cpu().numpy() / (core.VIEWS * (core.VIEWS - 1)), d)
            del x, shifted, cross
        sync_device(device); null_compute_seconds += time.perf_counter() - compute_started
        del base; strata_done = stratum + 1
        if checkpoint_every and checkpoint_callback and strata_done < stratum_total and strata_done % checkpoint_every == 0:
            checkpoint_callback(strata_done, between, compensation)
    map_hashes = {rep: core.null_mapping_sha256(plan, "ALL", sketch, rep, null_key) for rep in replicate_ids}
    metrics = {"strata_completed": strata_done, "logical_matrix_bytes_read": logical_bytes,
               "T_read_seconds": read_seconds, "T_host_to_device_seconds": host_to_device_seconds,
               "T_host_restore_seconds": host_restore_seconds,
               "T_null_compute_seconds": null_compute_seconds,
               "wall_seconds": time.time() - started, "replicate_ids": replicate_ids}
    return between, map_hashes, metrics


def verified_completed_replicates(rep_dir: Path, sketch: str, fingerprint: str, gate_manifest_sha: str,
                                  input_hashes: dict, plan_hashes: dict, moment_sha: str,
                                  plan: pd.DataFrame, null_key: str) -> dict[int, str]:
    completed = {}
    for path in sorted(rep_dir.glob("replicate_*.npz")):
        replicate = int(path.stem.split("_")[-1])
        if replicate < 0 or replicate >= 256 or replicate in completed:
            raise RuntimeError("invalid or duplicate completed replicate")
        map_sha = core.null_mapping_sha256(plan, "ALL", sketch, replicate, null_key)
        identity = sequential.checkpoint_identity(
            fingerprint, gate_manifest_sha, input_hashes, "ALL", sketch, replicate,
            plan_hashes["plan_sha256"], plan_hashes["plan_semantic_sha256"], moment_sha, map_sha)
        with np.load(path, allow_pickle=False) as saved:
            validate_scientific_payload(saved, NULL_PAYLOAD_FIELDS)
            sequential.assert_checkpoint_identity(saved, identity)
        completed[replicate] = sha(path)
    return completed


def remove_completed_batch_checkpoint(batch_dir: Path, root: Path) -> None:
    resolved = batch_dir.resolve()
    checkpoint_root = (root / "batch_checkpoints").resolve()
    if resolved.parent != checkpoint_root or not resolved.name:
        raise RuntimeError("refusing unsafe batch-checkpoint removal")
    # Cadence equal to the full stratum count intentionally creates no
    # in-batch snapshot.  In that accepted mode there is nothing to remove.
    if not resolved.exists():
        return
    shutil.rmtree(resolved)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", required=True); parser.add_argument("--matrix", required=True); parser.add_argument("--analytic", required=True)
    parser.add_argument("--plan-authority-dir", required=True); parser.add_argument("--gate", required=True); parser.add_argument("--out", required=True)
    parser.add_argument("--batch-size", type=int, required=True); parser.add_argument("--checkpoint-every-strata", type=int, required=True)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    freeze, matrix, analytic, plan_dir, gate, out = [Path(x).resolve() for x in (args.freeze,args.matrix,args.analytic,args.plan_authority_dir,args.gate,args.out)]
    if args.batch_size < 1 or args.batch_size > 256: raise RuntimeError("invalid batch size")
    contract, input_hashes = sequential.load_authority(freeze, matrix, analytic)
    fingerprint, gate_manifest_sha = verify_block_gate(gate)
    out.mkdir(parents=True, exist_ok=True)
    rows = pd.read_csv(matrix / "PHASE2_FEATURE_ROWS.csv", dtype={"donor_id": str})
    rng = json.loads((matrix.parent / "preexpression_freeze/PHASE2_RNG_KEYS.json").read_text())["keys"]
    plan, plan_hashes = load_frozen_all_plan(plan_dir, rows, rng["matched_null"])
    donor_ids=sorted(rows.donor_id.unique()); donor_sources=np.asarray([rows.loc[rows.donor_id.eq(d),"source"].iloc[0] for d in donor_ids])
    folds_table=pd.read_csv(matrix.parent/"preexpression_freeze/PHASE2_DONOR_FOLDS.csv",dtype={"donor_id":str}).set_index("donor_id"); folds=np.asarray([int(folds_table.loc[d,"outer_fold"]) for d in donor_ids])
    matrix_manifest_sha=sha(matrix/"PHASE2_FEATURE_MATRIX_MANIFEST.csv")
    run_state={"schema":"full104-block-major-all-run-v1","status":"RUNNING","implementation_fingerprint":fingerprint,
               "gate_manifest_sha256":gate_manifest_sha,"batch_size":args.batch_size,"checkpoint_every_strata":args.checkpoint_every_strata,
               **plan_hashes,"matrix_manifest_sha256":matrix_manifest_sha,"input_hashes":input_hashes}
    state_path=out/"RUN_STATE.json"
    if state_path.exists():
        old=json.loads(state_path.read_text());
        for key,value in run_state.items():
            if key!="status" and old.get(key)!=value: raise RuntimeError(f"run resume mismatch: {key}")
    else: atomic_json(state_path,run_state)
    observed={}
    for sketch in "AB":
        obs_path=out/f"OBSERVED_FULL512_{sketch}.npz"; stats=analytic/"sufficient_statistics"
        mean=np.asarray(np.load(stats/f"{sketch}_mean.npy",mmap_mode="r"),np.float64); within=np.asarray(np.load(stats/f"{sketch}_within.npy",mmap_mode="r"),np.float64); between=np.asarray(np.load(stats/f"{sketch}_between.npy",mmap_mode="r"),np.float64)
        moment_sha=sequential.array_sha(mean,within,between)
        identity=sequential.checkpoint_identity(fingerprint,gate_manifest_sha,input_hashes,"ALL",sketch,-1,plan_hashes["plan_sha256"],plan_hashes["plan_semantic_sha256"],moment_sha,"OBSERVED")
        if obs_path.exists():
            saved=np.load(obs_path,allow_pickle=False); validate_scientific_payload(saved,OBSERVED_PAYLOAD_FIELDS); sequential.assert_checkpoint_identity(saved,identity); basis,_=core.fit_basis_checked(mean,within,between,np.arange(core.DONORS),core.RANK,f"resume:ALL:{sketch}:observed")
            eigen,stability,held=saved["bootstrap_eigen"],saved["bootstrap_stability"],saved["heldout"]
        else:
            basis,eigen,stability,held,diagnostics=sequential.fit_observed(mean,within,between,folds,donor_sources,rng["donor_bootstrap"],f"ALL:{sketch}:observed")
            payload={"mean":mean,"within":within,"between":between,"components":basis["components"].astype(np.float32),"eigenvalues":basis["eigenvalues"],"bootstrap_eigen":eigen,"bootstrap_stability":stability,"heldout":held,"numerical_diagnostics_json":np.asarray(json.dumps(diagnostics,sort_keys=True))}; payload_sha=sequential.checkpoint_payload_sha256(payload)
            sequential.atomic_npz(obs_path,**payload,payload_semantic_sha256=np.asarray(payload_sha),**sequential.checkpoint_identity_arrays(identity))
        observed[sketch]={"mean":mean,"within":within,"between":between,"basis":basis,"eigen":eigen,"stability":stability,"held":held,"moment_sha":moment_sha}
    performance=[]
    for sketch in "AB":
        views=np.load(matrix/f"{sketch}_views.npy",mmap_mode="r"); rep_dir=out/f"null_replicates_{sketch}"; rep_dir.mkdir(exist_ok=True)
        while True:
            completed_hashes = verified_completed_replicates(
                rep_dir, sketch, fingerprint, gate_manifest_sha, input_hashes, plan_hashes,
                observed[sketch]["moment_sha"], plan, rng["matched_null"])
            completed=set(completed_hashes); remaining=[r for r in range(256) if r not in completed]
            if not remaining: break
            reps=remaining[:args.batch_size]; batch_dir=out/"batch_checkpoints"/f"{sketch}_{reps[0]:03d}_{reps[-1]:03d}"
            map_hashes={r:core.null_mapping_sha256(plan,"ALL",sketch,r,rng["matched_null"]) for r in reps}
            identity=batch_identity(fingerprint,gate_manifest_sha,matrix_manifest_sha,sketch,reps,args.batch_size,args.checkpoint_every_strata,plan_hashes,
                                    {str(k): v for k, v in completed_hashes.items()})
            restored=load_batch_checkpoint(batch_dir,identity,map_hashes)
            if restored is not None: cleanup_stale_checkpoint_artifacts(batch_dir,identity,map_hashes)
            start_stratum,between,compensation=(0,None,None) if restored is None else restored
            def checkpoint(position,b,c): save_batch_checkpoint(batch_dir,identity,position,b,c,map_hashes)
            between,map_hashes_actual,metrics=block_major_null_between_batch(views,plan,donor_ids,sketch,reps,rng["matched_null"],args.device,start_stratum,between,compensation,args.checkpoint_every_strata,checkpoint)
            if map_hashes_actual!=map_hashes: raise RuntimeError("final map hash mismatch")
            for local,replicate in enumerate(reps):
                finalize_started=time.perf_counter(); full_eigen,boot_eigen,null_stab,null_held,diagnostics=sequential.null_replicate(observed[sketch]["mean"],observed[sketch]["within"],between[local],observed[sketch]["basis"],folds,donor_sources,rng["donor_bootstrap"],replicate,f"ALL:{sketch}:null={replicate}"); finalize_seconds=time.perf_counter()-finalize_started
                expected=sequential.checkpoint_identity(fingerprint,gate_manifest_sha,input_hashes,"ALL",sketch,replicate,plan_hashes["plan_sha256"],plan_hashes["plan_semantic_sha256"],observed[sketch]["moment_sha"],map_hashes[replicate])
                payload={"null_full_eigenvalues":full_eigen,"paired_null_bootstrap_eigenvalues":boot_eigen,"stability":null_stab,"heldout":null_held.astype(np.float32),"numerical_diagnostics_json":np.asarray(json.dumps(diagnostics,sort_keys=True))}; payload_sha=sequential.checkpoint_payload_sha256(payload)
                sequential.atomic_npz(rep_dir/f"replicate_{replicate:03d}.npz",**payload,payload_semantic_sha256=np.asarray(payload_sha),**sequential.checkpoint_identity_arrays(expected))
                performance.append({"sketch":sketch,"replicate":replicate,"T_finalize_seconds":finalize_seconds})
            performance.append({"sketch":sketch,"replicate_ids":reps,**metrics}); remove_completed_batch_checkpoint(batch_dir,out)
            atomic_json(out/"BLOCK_MAJOR_PERFORMANCE.json",performance)
            print(json.dumps({"sketch":sketch,"completed":len(completed)+len(reps),"batch":reps,"wall_seconds":metrics["wall_seconds"]}),flush=True)
    selection=sequential.aggregate_selection(out,observed); numerical=sequential.aggregate_numerical_diagnostics(out)
    run_state.update({"status":"ALL_COMPLETE_AWAITING_INDEPENDENT_REAL_RESULT_VALIDATION","selection":selection,"numerical_diagnostics":numerical,"completed_at":time.time()});atomic_json(state_path,run_state)
    manifest=out/"FULL104_BLOCK_MAJOR_ALL_MANIFEST.csv"; files=[p for p in out.rglob("*") if p.is_file() and p!=manifest];pd.DataFrame([{"path":str(p.relative_to(out)),"bytes":p.stat().st_size,"sha256":sha(p)} for p in files]).to_csv(manifest,index=False,lineterminator="\n")
    print(json.dumps({"status":run_state["status"],"manifest_sha256":sha(manifest)},indent=2))


if __name__ == "__main__": main()
