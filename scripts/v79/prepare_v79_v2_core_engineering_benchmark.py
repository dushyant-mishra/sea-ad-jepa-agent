#!/usr/bin/env python3
"""Controller-side preparation for the V79 V2_CORE engineering benchmark.

This process may read the full generation authority and controller world mapping.
It emits only a blinded engineering package plus an identity-blind fit-contract view
and opaque benchmark custody receipt for a separate NUTS process.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

import generate_v79_v2_core_worlds as G
import v79_v2_core_fit_contract as FC
import v79_v2_core_fit_runner as R
import v79_v2_core_world_writer as W

FIT_VIEW_NAME = "V79_V2_CORE_FIT_CONTRACT_VIEW_V1.json"
PREP_RECEIPT_NAME = "V79_V2_CORE_ENGINEERING_BENCHMARK_PREP_V1.json"
PREP_SCHEMA = "V79_V2_CORE_ENGINEERING_BENCHMARK_PREP_V1"


class BenchmarkPrepRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise BenchmarkPrepRefused(f"REFUSED V2_CORE benchmark prep: {msg}")


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _canonical(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _write_once(path: Path, raw: bytes) -> str:
    path = Path(path)
    if path.exists():
        _refuse(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def build_fit_contract_view(contract: dict) -> dict:
    streams = contract["seeds"]["gene_streams"]
    view = {
        "schema": FC.SCHEMA,
        "source_contract_sha256": FC.SOURCE_CONTRACT_SHA256,
        "model": copy.deepcopy(contract["model"]),
        "parameterization": copy.deepcopy(contract["parameterization"]),
        "priors": copy.deepcopy(contract["priors"]),
        "inference": copy.deepcopy(contract["inference"]),
        "resources": {
            "engineering_benchmark": contract["resources"]["engineering_benchmark"],
            "settle_seconds_between_worlds": contract["resources"]["settle_seconds_between_worlds"],
            "estimate": {"n_fits": contract["resources"]["estimate"]["n_fits"]},
        },
        "seeds": {
            "engineering_benchmark_root": contract["seeds"]["engineering_benchmark_root"],
            "gene_streams": {k: streams[k] for k in
                             ("fit_det_primary", "fit_det_escalation", "fit_pos_primary", "fit_pos_escalation")},
        },
        "result_schemas": {"fit_record": contract["result_schemas"]["fit_record"]},
    }
    FC.validate_fit_contract_view(view)
    return view


def _blinded_directory_digest(package_dir: Path) -> str:
    base = Path(package_dir) / W.FIT_ROOT_NAME
    h = hashlib.sha256()
    for p in sorted((p for p in base.rglob("*") if p.is_file()), key=lambda x: x.relative_to(base).as_posix()):
        rel = p.relative_to(base).as_posix()
        h.update(rel.encode("utf-8")); h.update(b"\0")
        h.update(hashlib.sha256(p.read_bytes()).digest()); h.update(b"\0")
    return h.hexdigest()


def _selected_world_and_seed_ledger(contract: dict, root_manifest: dict, blinded_index: dict) -> tuple[str, str, list[dict]]:
    worlds = blinded_index.get("worlds")
    if not isinstance(worlds, list) or not worlds:
        _refuse("blinded engineering index has no worlds")
    # Selection is made from opaque fit-facing records only. Controller mapping is consulted only after selection
    # to derive the frozen SeedSequence world index; it cannot affect which world was selected.
    selected_rec = sorted(worlds, key=lambda x: str(x["opaque_world_id"]))[0]
    oid = str(selected_rec["opaque_world_id"])
    msha = str(selected_rec["manifest_sha256"])
    root_by_oid = {str(x["opaque_world_id"]): x for x in root_manifest.get("worlds", [])}
    if oid not in root_by_oid:
        _refuse("selected opaque world missing from controller root mapping")
    wi = int(root_by_oid[oid]["world_index"])
    eng_root = int(contract["seeds"]["engineering_benchmark_root"])
    streams = contract["seeds"]["gene_streams"]
    ledger = []
    for gene_index in (0, 1):
        for part in ("detection", "positive"):
            stream = int(streams["fit_det_primary" if part == "detection" else "fit_pos_primary"])
            seed = G.seed_for(world_index=wi, gene_index=gene_index, stream=stream, root=eng_root)
            ledger.append({
                "fit_id": R.fit_identity(oid, msha, part, gene_index),
                "primary_seed": int(seed),
            })
    ledger.sort(key=lambda x: x["fit_id"])
    return oid, msha, ledger


def prepare(root: Path, package_dir: Path, custody_dir: Path) -> dict:
    root = Path(root); package_dir = Path(package_dir); custody_dir = Path(custody_dir)
    if package_dir.exists() or custody_dir.exists():
        _refuse("package/custody destination must not already exist")
    contract, qual_payload, cal, _, amendment = W.load_frozen_qualification_inputs(root)
    if hashlib.sha256((root / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json").read_bytes()).hexdigest() != FC.SOURCE_CONTRACT_SHA256:
        _refuse("source contract bytes differ from frozen authority")
    eng_root = int(contract["seeds"]["engineering_benchmark_root"])
    if eng_root == int(qual_payload["seeds"]["root"]):
        _refuse("engineering and qualification seed roots alias")
    payload = copy.deepcopy(qual_payload)
    payload["seeds"]["root"] = eng_root
    designs = G.build_world_designs(root, payload)
    root_manifest = W.write_engineering_world_set(root=root, payload=payload, cal=cal, designs=designs,
                                                  amendment=amendment, out_dir=package_dir)
    if root_manifest.get("mode") != "ENGINEERING_TEST_ONLY" or int(root_manifest.get("seed_root", -1)) != eng_root:
        _refuse("writer did not produce the contract-defined engineering set")
    index_path = package_dir / W.FIT_ROOT_NAME / W.FIT_INDEX_NAME
    index = json.loads(index_path.read_text(encoding="utf-8"))
    oid, msha, seed_ledger = _selected_world_and_seed_ledger(contract, root_manifest, index)

    fit_view = build_fit_contract_view(contract)
    custody_dir.mkdir(parents=True, exist_ok=False)
    fit_view_sha = _write_once(custody_dir / FIT_VIEW_NAME, FC.canonical_bytes(fit_view))
    receipt = {
        "schema": PREP_SCHEMA,
        "source_contract_sha256": FC.SOURCE_CONTRACT_SHA256,
        "fit_contract_view_path": FIT_VIEW_NAME,
        "fit_contract_view_sha256": fit_view_sha,
        "execution_mode": "ENGINEERING_BENCHMARK",
        "engineering_seed_root": eng_root,
        "root_manifest_sha256": _sha(package_dir / W.ROOT_MANIFEST_NAME),
        "blinded_index_sha256": _sha(index_path),
        "blinded_directory_digest": _blinded_directory_digest(package_dir),
        "selected_opaque_world_id": oid,
        "selected_world_manifest_sha256": msha,
        "fit_seed_ledger": seed_ledger,
        "benchmark_fit_count": 4,
        "benchmark_run": False,
        "qualification_fits_run": 0,
        "scoring_run": False,
        "fit_truth_accessed": False,
        "training_authorized": False,
    }
    raw = _canonical(receipt)
    receipt_sha = _write_once(custody_dir / PREP_RECEIPT_NAME, raw)
    receipt["prep_receipt_sha256"] = receipt_sha
    return receipt


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("root")
    p.add_argument("package_dir")
    p.add_argument("custody_dir")
    a = p.parse_args(argv)
    print(json.dumps(prepare(Path(a.root), Path(a.package_dir), Path(a.custody_dir)), indent=2))


if __name__ == "__main__":
    main()
