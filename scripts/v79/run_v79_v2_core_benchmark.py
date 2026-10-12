#!/usr/bin/env python3
"""Identity-blind V79 V2_CORE engineering benchmark fit process.

Controller-side world generation and opaque selection happen in
prepare_v79_v2_core_engineering_benchmark.py. This process can read only the
sanitized custody receipt, fit-contract view and blinded_fit_inputs surface.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import numpy as np

import v79_v2_core_fit_contract as FC
import v79_v2_core_fit_runner as R
import v79_v2_core_fit_surface as F
import v79_v2_core_resource_monitor as RM
import v79_v2_core_runtime as RT
import v79_v2_core_runtime_lock as RL

PREP_RECEIPT_NAME = "V79_V2_CORE_ENGINEERING_BENCHMARK_PREP_V1.json"
FIT_VIEW_NAME = "V79_V2_CORE_FIT_CONTRACT_VIEW_V1.json"
RESULT_RECEIPT_NAME = "V79_V2_CORE_ENGINEERING_BENCHMARK_RECEIPT_V1.json"


class BenchmarkRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise BenchmarkRefused(f"REFUSED V2_CORE engineering benchmark: {msg}")


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _canonical(obj: Mapping) -> bytes:
    return (json.dumps(dict(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _blinded_directory_digest(package_dir: Path) -> str:
    base = Path(package_dir) / F.FIT_ROOT_NAME
    if not base.is_dir():
        _refuse("blinded fit root missing")
    h = hashlib.sha256()
    for p in sorted((p for p in base.rglob("*") if p.is_file()), key=lambda x: x.relative_to(base).as_posix()):
        rel = p.relative_to(base).as_posix()
        h.update(rel.encode("utf-8")); h.update(b"\0")
        h.update(hashlib.sha256(p.read_bytes()).digest()); h.update(b"\0")
    return h.hexdigest()


def _contains_controller_identity(obj) -> bool:
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            if str(k).lower() in {"world_name", "world_index", "q_label", "truth", "operator", "matrix"}:
                return True
            if _contains_controller_identity(v):
                return True
    elif isinstance(obj, list):
        return any(_contains_controller_identity(x) for x in obj)
    elif isinstance(obj, str) and re.search(r"\bQ(?:0[0-9]|1[01])(?:_|\b)", obj):
        return True
    return False


def load_prep_receipt(custody_dir: Path) -> tuple[dict, str]:
    path = Path(custody_dir) / PREP_RECEIPT_NAME
    if not path.is_file():
        _refuse("benchmark prep receipt missing")
    raw = path.read_bytes()
    try:
        receipt = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        _refuse(f"invalid prep receipt JSON: {exc}")
    if _canonical(receipt) != raw:
        _refuse("prep receipt is not canonical")
    required = {
        "schema", "source_contract_sha256", "fit_contract_view_path", "fit_contract_view_sha256",
        "execution_mode", "engineering_seed_root", "root_manifest_sha256", "blinded_index_sha256",
        "blinded_directory_digest", "selected_opaque_world_id", "selected_world_manifest_sha256",
        "fit_seed_ledger", "benchmark_fit_count", "benchmark_run", "qualification_fits_run",
        "scoring_run", "fit_truth_accessed", "training_authorized",
    }
    if set(receipt) != required or receipt.get("schema") != "V79_V2_CORE_ENGINEERING_BENCHMARK_PREP_V1":
        _refuse("prep receipt schema/key set differs")
    if receipt.get("source_contract_sha256") != FC.SOURCE_CONTRACT_SHA256:
        _refuse("prep receipt source contract differs")
    if receipt.get("execution_mode") != "ENGINEERING_BENCHMARK" or receipt.get("benchmark_fit_count") != 4:
        _refuse("prep receipt benchmark scope differs")
    if receipt.get("benchmark_run") is not False or receipt.get("qualification_fits_run") != 0 or \
            receipt.get("scoring_run") is not False or receipt.get("fit_truth_accessed") is not False or \
            receipt.get("training_authorized") is not False:
        _refuse("prep receipt crosses an execution/truth boundary")
    if receipt.get("fit_contract_view_path") != FIT_VIEW_NAME:
        _refuse("unexpected fit-contract view path")
    if not re.fullmatch(r"[0-9a-f]{12}", str(receipt.get("selected_opaque_world_id", ""))):
        _refuse("invalid selected opaque world ID")
    if _contains_controller_identity(receipt):
        _refuse("controller identity leaked into prep receipt")
    ledger = receipt.get("fit_seed_ledger")
    if not isinstance(ledger, list) or len(ledger) != 4:
        _refuse("prep seed ledger must contain exactly four fits")
    if any(set(x) != {"fit_id", "primary_seed"} for x in ledger if isinstance(x, Mapping)) or \
            len({str(x.get("fit_id")) for x in ledger if isinstance(x, Mapping)}) != 4:
        _refuse("malformed/duplicate prep seed ledger")
    return receipt, hashlib.sha256(raw).hexdigest()


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


def execute_benchmark(root: Path, package_dir: Path, custody_dir: Path, result_dir: Path) -> dict:
    root=Path(root); package_dir=Path(package_dir); custody_dir=Path(custody_dir); result_dir=Path(result_dir)
    prep, prep_sha = load_prep_receipt(custody_dir)
    fit_view = FC.load_fit_contract_view(custody_dir/FIT_VIEW_NAME, expected_sha256=prep["fit_contract_view_sha256"])
    if int(prep["engineering_seed_root"]) != int(fit_view["seeds"]["engineering_benchmark_root"]):
        _refuse("prep and fit-contract engineering roots differ")

    # Configure CPU host devices before any JAX-importing model code is imported.
    RT.configure_before_jax_import(fit_view)
    runtime_receipt = RL.validate_runtime(root, require_windows=True,
        required_cpu_devices=int(fit_view["resources"]["xla_host_devices"]))
    jax_receipt = RT.validate_imported_jax(fit_view)
    import v79_v2_core_fit_model as M

    root_path = package_dir/F.ROOT_MANIFEST_NAME
    index_path = package_dir/F.FIT_ROOT_NAME/F.FIT_INDEX_NAME
    if _sha(root_path) != prep["root_manifest_sha256"] or _sha(index_path) != prep["blinded_index_sha256"]:
        _refuse("engineering package root/index hashes differ from prep receipt")
    if _blinded_directory_digest(package_dir) != prep["blinded_directory_digest"]:
        _refuse("blinded engineering directory digest differs from prep receipt")
    idx = F.load_blinded_index(package_dir, expected_mode="ENGINEERING_TEST_ONLY",
        expected_root_manifest_sha=prep["root_manifest_sha256"], expected_index_sha=prep["blinded_index_sha256"])
    oid = str(prep["selected_opaque_world_id"])
    world = F.load_blinded_world(idx, oid)
    if world.manifest_sha256 != prep["selected_world_manifest_sha256"]:
        _refuse("selected world manifest differs from prep receipt")

    plan = benchmark_plan(fit_view, opaque_world_id=oid, world_manifest_sha=world.manifest_sha256)
    seeds = {str(x["fit_id"]): int(x["primary_seed"]) for x in prep["fit_seed_ledger"]}
    if set(seeds) != {x["fit_id"] for x in plan}:
        _refuse("prep seed ledger does not exactly cover benchmark plan")
    code_sha = _git_head(root)
    receipt = {
        "schema":"V79_V2_CORE_ENGINEERING_BENCHMARK_RECEIPT_V1",
        "source_contract_sha256":FC.SOURCE_CONTRACT_SHA256,
        "fit_contract_view_sha256":prep["fit_contract_view_sha256"],
        "prep_receipt_sha256":prep_sha,
        "code_sha":code_sha,
        "package_hashes":{"root_manifest":prep["root_manifest_sha256"],
                          "blinded_index":prep["blinded_index_sha256"],
                          "blinded_directory_digest":prep["blinded_directory_digest"],
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
            seed=seeds[item["fit_id"]]
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
    p=argparse.ArgumentParser(); p.add_argument("root"); p.add_argument("package_dir"); p.add_argument("custody_dir"); p.add_argument("result_dir")
    a=p.parse_args(argv); r=execute_benchmark(Path(a.root),Path(a.package_dir),Path(a.custody_dir),Path(a.result_dir)); print(json.dumps(r,indent=2))


if __name__ == "__main__": main()
