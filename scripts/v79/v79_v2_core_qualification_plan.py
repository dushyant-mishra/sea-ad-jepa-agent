#!/usr/bin/env python3
"""Truth-blind deterministic campaign queue and qualification authorization gate."""
from __future__ import annotations

import re
from typing import Mapping

import v79_v2_core_fit_runner as R

AUTH_SCHEMA = "V79_V2_CORE_QUALIFICATION_EXECUTION_AUTHORIZATION_V1"


class QualificationPlanRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise QualificationPlanRefused(f"REFUSED V2_CORE qualification plan: {msg}")


def _genes_per_world(contract: Mapping, world_count: int, n_fits: int) -> int:
    explicit = contract.get("worlds", {}).get("genes_per_world") if isinstance(contract.get("worlds"), Mapping) else None
    if explicit is not None:
        n_gene = int(explicit)
    else:
        denom = int(world_count) * 2
        if denom <= 0 or n_fits <= 0 or n_fits % denom:
            _refuse("cannot derive genes-per-world from fit-only authority")
        n_gene = n_fits // denom
    if n_gene <= 0 or n_gene * int(world_count) * 2 != n_fits:
        _refuse("genes/world arithmetic does not reproduce frozen fit count")
    return n_gene


def build_qualification_queue(contract: Mapping, blinded_index: Mapping) -> list[dict]:
    want = int(contract.get("resources", {}).get("estimate", {}).get("n_fits", -1))
    worlds = blinded_index.get("worlds")
    world_count = int(blinded_index.get("world_count", -1))
    if not isinstance(worlds, list) or world_count != len(worlds):
        _refuse("invalid blinded index")
    n_gene = _genes_per_world(contract, world_count, want)
    records=[]
    for w in sorted(worlds, key=lambda x: str(x.get("opaque_world_id", ""))):
        oid=str(w.get("opaque_world_id", "")); msha=str(w.get("manifest_sha256", ""))
        if not re.fullmatch(r"[0-9a-f]{12}", oid) or not re.fullmatch(r"[0-9a-f]{64}", msha):
            _refuse("non-opaque world or invalid manifest hash")
        for g in range(n_gene):
            for part in ("detection","positive"):
                records.append({"opaque_world_id":oid,"world_manifest_sha256":msha,"gene_index":g,"part":part,
                                "fit_id":R.fit_identity(oid,msha,part,g)})
    if len(records) != want:
        _refuse(f"queue has {len(records)} fits, contract requires {want}")
    return records


def _contains_forbidden_identity(obj) -> bool:
    if isinstance(obj, Mapping):
        for k,v in obj.items():
            lk=str(k).lower()
            if lk in {"world_name","world_index","q_label","truth","operator","matrix"}:
                return True
            if _contains_forbidden_identity(v): return True
    elif isinstance(obj, list):
        return any(_contains_forbidden_identity(x) for x in obj)
    elif isinstance(obj, str):
        if re.search(r"\bQ(?:0[0-9]|1[01])(?:_|\b)", obj): return True
    return False


def require_qualification_execution_authority(auth: Mapping | None, *, expected_contract_sha: str,
                                               expected_blinded_index_sha: str) -> Mapping:
    if not isinstance(auth, Mapping) or auth.get("schema") != AUTH_SCHEMA:
        _refuse("missing/wrong qualification execution authorization")
    if auth.get("qualification_campaign_authorized") is not True:
        _refuse("qualification campaign not authorized")
    if auth.get("benchmark_controller_pass") is not True:
        _refuse("benchmark controller pass absent")
    if auth.get("contract_sha256") != expected_contract_sha or auth.get("blinded_index_sha256") != expected_blinded_index_sha:
        _refuse("authorization authority hashes differ")
    if auth.get("scoring_authorized") is not False or auth.get("training_authorized") is not False:
        _refuse("authorization crosses later gates")
    if _contains_forbidden_identity(auth.get("fit_seed_ledger", [])):
        _refuse("fit-facing seed ledger leaks scientific identity")
    return auth


def bind_seed_ledger(queue: list[Mapping], auth: Mapping) -> list[dict]:
    ledger=auth.get("fit_seed_ledger")
    if not isinstance(ledger,list) or len(ledger)!=len(queue):
        _refuse("seed ledger cardinality differs from queue")
    seeds={str(x.get("fit_id")):x for x in ledger if isinstance(x,Mapping)}
    if len(seeds)!=len(queue) or set(seeds)!={str(x["fit_id"]) for x in queue}:
        _refuse("seed ledger fit identities differ from queue")
    out=[]
    for q in queue:
        s=seeds[q["fit_id"]]
        seed=s.get("primary_seed")
        if not isinstance(seed,int) or seed<0 or seed>0xffffffff:
            _refuse(f"invalid primary seed for {q['fit_id']}")
        x=dict(q); x["primary_seed"]=seed; out.append(x)
    return out
