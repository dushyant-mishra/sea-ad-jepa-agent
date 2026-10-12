#!/usr/bin/env python3
"""Engineering-only V79 V2_CORE benchmark. Never fits a realized qualification world."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

import numpy as np

import generate_v79_v2_core_worlds as G
import v79_v2_core_fit_model as M
import v79_v2_core_fit_runner as R
import v79_v2_core_fit_surface as F
import v79_v2_core_launch as L
import v79_v2_core_resource_monitor as RM
import v79_v2_core_world_writer as W


class BenchmarkRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise BenchmarkRefused(f"REFUSED V2_CORE engineering benchmark: {msg}")


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _max_projected_hours(contract: dict) -> float:
    text = str(contract.get("resources", {}).get("engineering_benchmark", ""))
    m = re.search(r"exceeds\s+([0-9]+(?:\.[0-9]+)?)\s*h", text)
    if not m: _refuse("contract engineering benchmark runtime ceiling is not parseable")
    return float(m.group(1))


def check_projected_hours(contract: dict, projected_hours: float) -> float:
    ceiling = _max_projected_hours(contract)
    if float(projected_hours) > ceiling:
        raise BenchmarkRefused(f"projected qualification runtime {projected_hours:.3f} h exceeds frozen {ceiling:g} h ceiling")
    return float(projected_hours)


def benchmark_plan(contract: dict, *, opaque_world_id: str, world_manifest_sha: str) -> list[dict]:
    text = str(contract.get("resources", {}).get("engineering_benchmark", ""))
    if "2 genes x 2 parts" not in text:
        _refuse("contract no longer specifies 2 genes x 2 parts")
    return [{"execution_mode":"ENGINEERING_BENCHMARK", "opaque_world_id":opaque_world_id,
             "world_manifest_sha256":world_manifest_sha, "gene_index":g, "part":part,
             "fit_id":R.fit_identity(opaque_world_id, world_manifest_sha, part, g)}
            for g in (0,1) for part in ("detection","positive")]


def benchmark_receipt_skeleton(contract: dict, *, code_sha: str, package_hashes: dict) -> dict:
    return {"schema":"V79_V2_CORE_ENGINEERING_BENCHMARK_RECEIPT_V1",
            "contract_sha256":L.FINAL_CONTRACT_SHA256, "code_sha":code_sha,
            "engineering_seed_root":int(contract["seeds"]["engineering_benchmark_root"]),
            "package_hashes":dict(package_hashes), "fit_records":[],
            "benchmark_run":True, "qualification_fits_run":0, "scoring_run":False,
            "truth_accessed":False, "training_authorized":False}


def _git_head(root: Path) -> str:
    return subprocess.check_output(["git","rev-parse","HEAD"], cwd=root, text=True).strip()


def prepare_engineering_package(root: Path, out_dir: Path) -> tuple[dict, F.BlindedIndex, str, dict]:
    """Fresh contract-defined engineering package; select by opaque ordering only, never Q identity."""
    root = Path(root); out_dir = Path(out_dir)
    contract, qual_payload, cal, _, amendment = W.load_frozen_qualification_inputs(root)
    eng_root = int(contract["seeds"]["engineering_benchmark_root"])
    if eng_root == int(qual_payload["seeds"]["root"]):
        _refuse("engineering seed aliases qualification seed")
    payload = copy.deepcopy(qual_payload); payload["seeds"]["root"] = eng_root
    designs = G.build_world_designs(root, payload)
    manifest = W.write_engineering_world_set(root=root, payload=payload, cal=cal, designs=designs,
                                             amendment=amendment, out_dir=out_dir)
    if manifest.get("mode") != "ENGINEERING_TEST_ONLY" or int(manifest.get("seed_root", -1)) != eng_root:
        _refuse("writer did not produce the contract-defined engineering package")
    root_sha = _sha(out_dir/F.ROOT_MANIFEST_NAME)
    index_sha = _sha(out_dir/F.FIT_ROOT_NAME/F.FIT_INDEX_NAME)
    idx = F.load_blinded_index(out_dir, expected_mode="ENGINEERING_TEST_ONLY",
                               expected_root_manifest_sha=root_sha, expected_index_sha=index_sha)
    if not idx.opaque_world_ids: _refuse("engineering package has no blinded worlds")
    selected = sorted(idx.opaque_world_ids)[0]
    rec = next(x for x in idx.index["worlds"] if x["opaque_world_id"] == selected)
    hashes = {"root_manifest":root_sha,
              "directory_digest":W.directory_digest(out_dir),
              "blinded_index":index_sha,
              "selected_world_manifest":rec["manifest_sha256"]}
    return contract, idx, selected, hashes


def benchmark_seed(contract: dict, *, gene_index: int, part: str) -> int:
    """Single engineering world has engineering ordinal 0; qualification seed ledger is separate."""
    root = int(contract["seeds"]["engineering_benchmark_root"])
    stream = int(contract["seeds"]["gene_streams"]["fit_det_primary" if part=="detection" else "fit_pos_primary"])
    ss = np.random.SeedSequence(entropy=root, spawn_key=(0, int(gene_index), stream))
    return int(ss.generate_state(1, np.uint32)[0])


def _one_attempt(contract, model, seed, stage, *, post_state=None, previous_ta=None):
    with RM.ResourceMonitor() as mon:
        run = R.run_nuts_attempt(contract=contract, model=model, seed=seed, stage=stage,
                                 post_warmup_state=post_state, previous_target_accept=previous_ta)
    diag, samples = R.attempt_diagnostics(run)
    spec = run["spec"]
    rec = dict(spec)
    rec.update(diag)
    rec.update({"seed":int(seed), "wall_seconds":float(mon.wall_seconds),
                "process_cpu_seconds":float(mon.process_cpu_seconds),
                "peak_working_set_bytes":int(mon.peak_rss)})
    try:
        import jax
        rec["jax_devices"] = [str(x) for x in jax.devices()]
    except Exception:
        rec["jax_devices"] = []
    return rec, samples, run["mcmc"]


def execute_benchmark(root: Path, package_dir: Path, result_dir: Path) -> dict:
    root=Path(root); package_dir=Path(package_dir); result_dir=Path(result_dir)
    contract = L.require_launch_authority(root/"results/v79/v2_core_qualification"/L.FINAL_CONTRACT_NAME, root=root)
    env_receipt = W.validate_runtime_package_lock(root)
    contract2, idx, oid, package_hashes = prepare_engineering_package(root, package_dir)
    if contract2 != contract: _refuse("engineering package contract differs from launch authority")
    world = F.load_blinded_world(idx, oid)
    plan = benchmark_plan(contract, opaque_world_id=oid, world_manifest_sha=world.manifest_sha256)
    code_sha = _git_head(root); receipt = benchmark_receipt_skeleton(contract, code_sha=code_sha, package_hashes=package_hashes)
    receipt["runtime_environment_receipt"] = env_receipt
    result_dir.mkdir(parents=True, exist_ok=False)
    total_seconds = 0.0
    with RM.single_heavy_fit_lock(result_dir/"HEAVY_FIT.lock"):
        for item in plan:
            gene = F.load_gene_inputs(world, gene_index=item["gene_index"], replicate="train")
            model = M.build_detection_model(contract, gene) if item["part"]=="detection" else M.build_positive_model(contract, gene)
            seed = benchmark_seed(contract, gene_index=item["gene_index"], part=item["part"])
            frec = R.new_fit_receipt(execution_mode="ENGINEERING_BENCHMARK", fit_id=item["fit_id"],
                    opaque_world_id=oid, gene_index=item["gene_index"], part=item["part"],
                    input_manifest_sha=world.manifest_sha256, contract_sha=L.FINAL_CONTRACT_SHA256, code_sha=code_sha)
            attempts=[]; all_samples=None; last_mcmc=None; previous_ta=None; stage="PRIMARY"
            while True:
                arec, samples, mcmc = _one_attempt(contract, model, seed, stage,
                    post_state=(last_mcmc.last_state if stage=="EXTENSION" and last_mcmc is not None else None),
                    previous_ta=previous_ta)
                attempts.append(arec); total_seconds += arec["wall_seconds"]
                if stage=="EXTENSION" and all_samples is not None:
                    all_samples = R.combine_samples(all_samples, samples)
                    diag = R.diagnostics_from_samples(all_samples, divergences=sum(a["divergences"] for a in attempts),
                                                      mean_tree_steps=float(np.mean([a["mean_tree_steps"] for a in attempts])))
                else:
                    all_samples = samples; diag = {k:arec[k] for k in ("divergences","worst_rhat","worst_ess_bulk","worst_ess_tail","mean_tree_steps")}
                action = R.next_recovery_action(contract, attempts, diag)
                if action in {"COMPLETE","NOT_DIAGNOSED"}:
                    frec["final_diagnosis"] = action; frec["attempts"] = attempts; break
                previous_ta = arec["target_accept"]; last_mcmc = mcmc
                stage = "ESCALATION" if action=="ESCALATE" else "EXTENSION"
            frec["posterior_summary"] = R.posterior_summary(all_samples)
            fpath = result_dir/f"fit_{item['fit_id']}.json"
            fsha = R.write_receipt_atomic(fpath, frec)
            receipt["fit_records"].append({"fit_id":item["fit_id"],"path":fpath.name,"sha256":fsha,
                                           "final_diagnosis":frec["final_diagnosis"]})
    nfits = int(contract["resources"]["estimate"]["n_fits"])
    mean_fit = total_seconds / len(plan)
    settle = float(contract["resources"]["settle_seconds_between_worlds"])
    projected = mean_fit*nfits/3600.0 + settle*int(idx.index["world_count"])/3600.0
    receipt["benchmark_fit_count"] = len(plan); receipt["total_fit_wall_seconds"] = total_seconds
    receipt["mean_fit_wall_seconds"] = mean_fit; receipt["projected_qualification_hours"] = projected
    receipt["projected_runtime_ceiling_hours"] = _max_projected_hours(contract)
    receipt["stop_required"] = projected > receipt["projected_runtime_ceiling_hours"]
    raw=(json.dumps(receipt,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
    (result_dir/"V79_V2_CORE_ENGINEERING_BENCHMARK_RECEIPT_V1.json").write_bytes(raw)
    if receipt["stop_required"]:
        raise BenchmarkRefused(f"benchmark complete but projected runtime {projected:.3f} h exceeds ceiling; STOP, no settings changes")
    return receipt


def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("root"); p.add_argument("package_dir"); p.add_argument("result_dir")
    a=p.parse_args(argv); r=execute_benchmark(Path(a.root),Path(a.package_dir),Path(a.result_dir)); print(json.dumps(r,indent=2))

if __name__ == "__main__": main()
