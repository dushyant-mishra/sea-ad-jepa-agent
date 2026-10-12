#!/usr/bin/env python3
"""Identity-blind V79 V2_CORE engineering benchmark fit process.

Controller-side generation/selection is performed separately. This process accepts
only fit-only custody: blinded_fit_inputs, fit-contract view, opaque seed ledger and
a hash-pinned prep receipt. It never imports generator, writer, scoring, or world
mapping authority.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import numpy as np

import v79_v2_core_fit_contract as FC
import v79_v2_core_fit_custody as C
import v79_v2_core_fit_runner as R
import v79_v2_core_fit_surface as F
import v79_v2_core_resource_monitor as RM
import v79_v2_core_runtime as RT
import v79_v2_core_runtime_lock as RL

RESULT_RECEIPT_NAME = "V79_V2_CORE_ENGINEERING_BENCHMARK_RECEIPT_V1.json"


class BenchmarkRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise BenchmarkRefused(f"REFUSED V2_CORE engineering benchmark: {msg}")


def _canonical(obj: Mapping) -> bytes:
    return (json.dumps(dict(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _max_projected_hours(contract: Mapping) -> float:
    text = str(contract.get("resources", {}).get("engineering_benchmark", ""))
    m = re.search(r"exceeds\s+([0-9]+(?:\.[0-9]+)?)\s*h", text)
    if not m:
        _refuse("fit contract benchmark runtime ceiling is not parseable")
    return float(m.group(1))


def check_projected_hours(contract: Mapping, projected_hours: float) -> float:
    ceiling = _max_projected_hours(contract)
    if float(projected_hours) > ceiling:
        raise BenchmarkRefused(f"projected qualification runtime {projected_hours:.3f} h exceeds frozen {ceiling:g} h ceiling")
    return float(projected_hours)


def benchmark_plan(contract: Mapping, *, opaque_world_id: str, world_manifest_sha: str) -> list[dict]:
    text = str(contract.get("resources", {}).get("engineering_benchmark", ""))
    if "2 genes x 2 parts" not in text:
        _refuse("fit contract no longer specifies 2 genes x 2 parts")
    return [{"execution_mode":"ENGINEERING_BENCHMARK", "opaque_world_id":opaque_world_id,
             "world_manifest_sha256":world_manifest_sha, "gene_index":g, "part":part,
             "fit_id":R.fit_identity(opaque_world_id, world_manifest_sha, part, g)}
            for g in (0,1) for part in ("detection","positive")]


def _git_head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _require_clean(root: Path) -> None:
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
    if status.strip():
        _refuse("repository working tree is not clean")


def _one_attempt(contract, model, seed, stage, *, post_state=None, previous_ta=None):
    started = datetime.now(timezone.utc).isoformat()
    with RM.ResourceMonitor() as mon:
        run = R.run_nuts_attempt(contract=contract, model=model, seed=seed, stage=stage,
                                 post_warmup_state=post_state, previous_target_accept=previous_ta)
    ended = datetime.now(timezone.utc).isoformat()
    diag, samples = R.attempt_diagnostics(run)
    rec = dict(run["spec"]); rec.update(diag)
    rec.update({"seed":int(seed), "started_at_utc":started, "ended_at_utc":ended,
                "wall_seconds":float(mon.wall_seconds), "process_cpu_seconds":float(mon.process_cpu_seconds),
                "peak_working_set_bytes":int(mon.peak_rss)})
    import jax
    rec["jax_devices"] = [str(x) for x in jax.devices()]
    return rec, samples, run["mcmc"]


def _active_lineage(attempts: list[dict]) -> list[dict]:
    escalation = [i for i, a in enumerate(attempts) if a.get("stage") == "ESCALATION"]
    return attempts[escalation[-1]:] if escalation else attempts


def execute_benchmark(root: Path, custody_dir: Path, result_dir: Path, *, expected_prep_receipt_sha256: str) -> dict:
    root=Path(root); custody_dir=Path(custody_dir); result_dir=Path(result_dir)
    _require_clean(root)
    custody = C.load_engineering_custody(custody_dir, expected_prep_receipt_sha256=expected_prep_receipt_sha256)
    fit_view = custody.fit_contract
    code_sha = _git_head(root)
    if custody.receipt.get("executor_code_head") != code_sha:
        _refuse(f"prep code head {custody.receipt.get('executor_code_head')} != executing head {code_sha}")
    if int(custody.receipt["engineering_seed_root"]) != int(fit_view["seeds"]["engineering_benchmark_root"]):
        _refuse("prep and fit-contract engineering roots differ")

    # Package-lock validation does not import JAX. Configure all JAX authority first.
    runtime_receipt = RL.validate_runtime(root, require_windows=True, required_cpu_devices=None)
    RT.configure_before_jax_import(fit_view)
    import jax
    jax_receipt = RT.validate_imported_jax(fit_view)
    import v79_v2_core_fit_model as M

    oid = custody.selected_opaque_world_id
    world = F.load_blinded_world(custody.blinded_index, oid)
    if world.manifest_sha256 != custody.selected_world_manifest_sha256:
        _refuse("selected world manifest differs from prep receipt")
    plan = benchmark_plan(fit_view, opaque_world_id=oid, world_manifest_sha=world.manifest_sha256)
    if set(custody.seed_by_fit_id) != {x["fit_id"] for x in plan}:
        _refuse("prep seed ledger does not exactly cover benchmark plan")

    receipt = {
        "schema":"V79_V2_CORE_ENGINEERING_BENCHMARK_RECEIPT_V1",
        "source_contract_sha256":FC.SOURCE_CONTRACT_SHA256,
        "fit_contract_view_sha256":custody.receipt["fit_contract_view_sha256"],
        "prep_receipt_sha256":custody.receipt_sha256,
        "code_sha":code_sha,
        "package_hashes":{"root_manifest":custody.receipt["root_manifest_sha256"],
                          "blinded_index":custody.receipt["blinded_index_sha256"],
                          "blinded_directory_digest":custody.receipt["blinded_directory_digest"],
                          "selected_world_manifest":world.manifest_sha256},
        "runtime_environment_receipt":runtime_receipt,
        "jax_runtime_receipt":jax_receipt,
        "fit_records":[], "benchmark_run":True, "qualification_fits_run":0,
        "scoring_run":False, "truth_accessed":False, "training_authorized":False,
    }
    if result_dir.exists():
        _refuse("benchmark result directory already exists")
    result_dir.mkdir(parents=True, exist_ok=False)
    total_seconds=0.0
    with RM.single_heavy_fit_lock(result_dir/"HEAVY_FIT.lock"):
        for item in plan:
            gene=F.load_gene_inputs(world, gene_index=item["gene_index"], replicate="train")
            model=M.build_detection_model(fit_view,gene) if item["part"]=="detection" else M.build_positive_model(fit_view,gene)
            seed=int(custody.seed_by_fit_id[item["fit_id"]])
            frec=R.new_fit_receipt(execution_mode="ENGINEERING_BENCHMARK", fit_id=item["fit_id"],
                opaque_world_id=oid, gene_index=item["gene_index"], part=item["part"],
                input_manifest_sha=world.manifest_sha256, contract_sha=FC.SOURCE_CONTRACT_SHA256, code_sha=code_sha)
            attempts=[]; all_samples=None; last_mcmc=None; previous_ta=None; stage="PRIMARY"
            while True:
                arec,samples,mcmc=_one_attempt(fit_view,model,seed,stage,
                    post_state=(last_mcmc.last_state if stage=="EXTENSION" and last_mcmc is not None else None),
                    previous_ta=previous_ta)
                attempts.append(arec); total_seconds += arec["wall_seconds"]
                if stage=="EXTENSION" and all_samples is not None:
                    all_samples=R.combine_samples(all_samples,samples); lineage=_active_lineage(attempts)
                    diag=R.diagnostics_from_samples(all_samples,
                        divergences=sum(a["divergences"] for a in lineage),
                        mean_tree_steps=float(np.mean([a["mean_tree_steps"] for a in lineage])))
                else:
                    all_samples=samples
                    diag={k:arec[k] for k in ("divergences","worst_rhat","worst_ess_bulk","worst_ess_tail","mean_tree_steps")}
                action=R.next_recovery_action(fit_view,attempts,diag)
                if action in {"COMPLETE","NOT_DIAGNOSED"}:
                    frec["final_diagnosis"]=action; frec["attempts"]=attempts; break
                previous_ta=arec["target_accept"]; last_mcmc=mcmc
                stage="ESCALATION" if action=="ESCALATE" else "EXTENSION"
            frec["posterior_summary"]=R.posterior_summary(all_samples)
            fpath=result_dir/f"fit_{item['fit_id']}.json"; fsha=R.write_receipt_atomic(fpath,frec)
            receipt["fit_records"].append({"fit_id":item["fit_id"],"path":fpath.name,"sha256":fsha,
                                           "final_diagnosis":frec["final_diagnosis"]})
    nfits=int(fit_view["resources"]["estimate"]["n_fits"]); mean_fit=total_seconds/len(plan)
    settle=float(fit_view["resources"]["settle_seconds_between_worlds"])
    worlds=int(fit_view["resources"]["qualification_world_count"])
    projected=mean_fit*nfits/3600.0 + settle*worlds/3600.0
    ceiling=_max_projected_hours(fit_view)
    receipt.update({"benchmark_fit_count":len(plan),"total_fit_wall_seconds":total_seconds,
                    "mean_fit_wall_seconds":mean_fit,"projected_qualification_hours":projected,
                    "projected_runtime_ceiling_hours":ceiling,"stop_required":projected>ceiling})
    raw=_canonical(receipt); (result_dir/RESULT_RECEIPT_NAME).write_bytes(raw)
    if receipt["stop_required"]:
        raise BenchmarkRefused(f"benchmark complete but projected runtime {projected:.3f} h exceeds ceiling; STOP, no settings changes")
    return receipt


def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("root"); p.add_argument("custody_dir"); p.add_argument("result_dir")
    p.add_argument("expected_prep_receipt_sha256")
    a=p.parse_args(argv)
    r=execute_benchmark(Path(a.root),Path(a.custody_dir),Path(a.result_dir),
                        expected_prep_receipt_sha256=a.expected_prep_receipt_sha256)
    print(json.dumps(r,indent=2))


if __name__ == "__main__": main()
