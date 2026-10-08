#!/usr/bin/env python3
"""End-to-end FULL104 gold-replicate parity for block-major executor."""
from __future__ import annotations

import argparse
import faulthandler
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import full104_refit_null_sensitivity_core_v1 as core
import run_full104_refit_null_block_major_v1 as block
import run_full104_refit_null_sensitivity_v1 as sequential


def main() -> None:
    faulthandler.enable()
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", required=True); parser.add_argument("--analytic", required=True)
    parser.add_argument("--plan-dir", required=True); parser.add_argument("--old-cap-all", required=True)
    parser.add_argument("--out", required=True); parser.add_argument("--device", default="cuda")
    args = parser.parse_args(); out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    if (out/"FULL104_GOLD_REPLICATE_PARITY.json").exists():raise RuntimeError("refusing to overwrite completed gold report")
    matrix, analytic, plan_dir, old = map(lambda x: Path(x).resolve(),
        (args.matrix, args.analytic, args.plan_dir, args.old_cap_all))
    rows = pd.read_csv(matrix / "PHASE2_FEATURE_ROWS.csv", dtype={"donor_id": str})
    rng = json.loads((matrix.parent / "preexpression_freeze/PHASE2_RNG_KEYS.json").read_text())["keys"]
    plan, plan_hashes = block.load_frozen_all_plan(plan_dir, rows, rng["matched_null"])
    donors = sorted(rows.donor_id.unique())
    donor_sources = np.asarray([rows.loc[rows.donor_id.eq(d), "source"].iloc[0] for d in donors])
    folds_table = pd.read_csv(matrix.parent / "preexpression_freeze/PHASE2_DONOR_FOLDS.csv", dtype={"donor_id": str}).set_index("donor_id")
    folds = np.asarray([int(folds_table.loc[d, "outer_fold"]) for d in donors])
    observed_path=old/"OBSERVED_FULL512_A.npz"
    with np.load(observed_path,allow_pickle=False) as authenticated:
        block.validate_scientific_payload(authenticated,block.OBSERVED_PAYLOAD_FIELDS)
        identity={name:str(authenticated[name]) for name in ("freeze_root","implementation_fingerprint","gate_manifest_sha256","input_hashes_sha256","cap","sketch","replicate","plan_sha256","plan_semantic_sha256","mapping_sha256","moment_sha256")}
        expected_identity={"freeze_root":block.EXPECTED_FREEZE_ROOT,"implementation_fingerprint":block.OLD_FINGERPRINT,"gate_manifest_sha256":"0de3e07f44b7a8501fe812ec689307b7da14ccf98d330243406eebfd3d2e75c8","input_hashes_sha256":"e13da16b9581166795dcc47b1639c6d3749b8ff682a845731d8ad2beb5a0d60b","cap":"ALL","sketch":"A","replicate":"-1","plan_sha256":plan_hashes["plan_sha256"],"plan_semantic_sha256":plan_hashes["plan_semantic_sha256"],"mapping_sha256":"OBSERVED","moment_sha256":str(authenticated["moment_sha256"])}
        if identity!=expected_identity:raise RuntimeError("authenticated old observed identity mismatch")
        mean=authenticated["mean"].copy();within=authenticated["within"].copy();observed_between=authenticated["between"].copy();components=authenticated["components"].copy();observed_eigen=authenticated["eigenvalues"].copy();observed_diagnostics=json.loads(str(authenticated["numerical_diagnostics_json"]));observed_payload_sha=str(authenticated["payload_semantic_sha256"])
    if sequential.array_sha(mean,within,observed_between)!=identity["moment_sha256"]:raise RuntimeError("authenticated old observed moment hash mismatch")
    basis_ok=bool(components.dtype==np.float32 and components.shape==(512,320) and observed_eigen.dtype==np.float64 and observed_eigen.shape==(320,) and np.isfinite(components).all() and np.isfinite(observed_eigen).all() and observed_diagnostics.get("all_finite") is True and float(observed_diagnostics["maximum_metric_orthogonality"])<1e-10)
    basis_audit={"status":"PASS_AUTHENTICATED_OLD_OBSERVED_BASIS_INTERFACE" if basis_ok else "STOP_OLD_OBSERVED_BASIS_INTERFACE","observed_file_sha256":block.sha(observed_path),"payload_semantic_sha256":observed_payload_sha,"moment_sha256":identity["moment_sha256"],"components_dtype":str(components.dtype),"components_shape":list(components.shape),"eigenvalues_dtype":str(observed_eigen.dtype),"eigenvalues_shape":list(observed_eigen.shape),"finite":basis_ok,"stored_numerical_diagnostics":observed_diagnostics,"observed_refit_performed":False}
    (out/"AUTHENTICATED_OLD_OBSERVED_BASIS_AUDIT.json").write_text(json.dumps(basis_audit,indent=2,sort_keys=True)+"\n")
    if not basis_ok:raise RuntimeError("old observed basis interface failed")
    observed_basis={"components":components,"eigenvalues":observed_eigen}
    views = np.load(matrix / "A_views.npy", mmap_mode="r")
    checkpoint = out / "accumulator_checkpoint"
    identity = block.batch_identity("gold-parity-v1", "not-a-production-gate", block.sha(matrix / "PHASE2_FEATURE_MATRIX_MANIFEST.csv"),
                                    "A", [0], 1, 10, plan_hashes)
    map_hash = {0: core.null_mapping_sha256(plan, "ALL", "A", 0, rng["matched_null"])}
    restored = block.load_batch_checkpoint(checkpoint, identity, map_hash)
    start, between, compensation = (0, None, None) if restored is None else restored
    def save(position, b, c): block.save_batch_checkpoint(checkpoint, identity, position, b, c, map_hash)
    full_started=time.perf_counter();between, actual_maps, metrics = block.block_major_null_between_batch(
        views, plan, donors, "A", [0], rng["matched_null"], args.device,
        start_stratum=start, between=between, compensation=compensation,
        checkpoint_every=10, checkpoint_callback=save)
    if actual_maps != map_hash: raise RuntimeError("gold parity mapping mismatch")
    finalize_started=time.perf_counter();full, bootstrap, stability, heldout, diagnostics = sequential.null_replicate(
        mean, within, between[0], observed_basis, folds, donor_sources,
        rng["donor_bootstrap"], 0, "ALL:A:null=0")
    finalize_seconds=time.perf_counter()-finalize_started;total_seconds=time.perf_counter()-full_started
    payload = {"null_full_eigenvalues": full, "paired_null_bootstrap_eigenvalues": bootstrap,
               "stability": stability, "heldout": heldout.astype(np.float32),
               "numerical_diagnostics_json": np.asarray(json.dumps(diagnostics, sort_keys=True))}
    payload_sha = sequential.checkpoint_payload_sha256(payload)
    sequential.atomic_npz(out/"NEW_WSL_REPLICATE_000_SCIENTIFIC_PAYLOAD.npz",**payload,payload_semantic_sha256=np.asarray(payload_sha))
    gold_path = old / "null_replicates_A/replicate_000.npz"
    with np.load(gold_path, allow_pickle=False) as gold:
        comparisons = {name: bool(np.array_equal(payload[name], gold[name])) for name in payload}
        numeric_deltas={name:{"max_abs":float(np.max(np.abs(np.asarray(payload[name],np.float64)-np.asarray(gold[name],np.float64)))),"max_rel":float(np.max(np.abs(np.asarray(payload[name],np.float64)-np.asarray(gold[name],np.float64))/np.maximum(np.abs(np.asarray(gold[name],np.float64)),np.finfo(np.float64).tiny)))} for name in payload if name!="numerical_diagnostics_json"}
        gold_payload_sha = str(gold["payload_semantic_sha256"])
        gold_map_sha = str(gold["mapping_sha256"])
    report = {"status": "PASS_FULL104_GOLD_REPLICATE_EXACT_PARITY" if all(comparisons.values()) and payload_sha == gold_payload_sha and map_hash[0] == gold_map_sha else "STOP_FULL104_GOLD_REPLICATE_PARITY",
              "replicate": 0, "sketch": "A", "comparisons": comparisons,
              "new_payload_semantic_sha256": payload_sha, "gold_payload_semantic_sha256": gold_payload_sha,
              "new_mapping_sha256": map_hash[0], "gold_mapping_sha256": gold_map_sha,
              "numeric_deltas":numeric_deltas,"new_eigenvalue_order_descending":bool(np.all(np.diff(full)<=0) and np.all(np.diff(bootstrap)<=0)),
              "executor_metrics": {**metrics,"T_finalize_seconds":finalize_seconds,"full_gold_wall_seconds":total_seconds}, "plan_hashes": plan_hashes,
              "old_between_accumulator_preserved":False,"aggregate_D1_D320_support_available_from_old_run":False,
              "aggregate_support_note":"The old ALL run preserved only atomic replicate A/0, not 256-replicate aggregate support. Exact scientific payload parity preserves this replicate's contribution without inventing an aggregate decision."}
    (out / "FULL104_GOLD_REPLICATE_PARITY.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2))
    if not report["status"].startswith("PASS_"): raise SystemExit(2)


if __name__ == "__main__":
    main()
