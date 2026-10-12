#!/usr/bin/env python3
"""Validation for the identity-blind V79 V2_CORE fit-contract projection.

The full Contract V2 contains controller-only world/gate labels. Fit processes receive
only this deterministic projection, hash-bound to the immutable source contract.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

SOURCE_CONTRACT_SHA256 = "57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26"
SCHEMA = "V79_V2_CORE_FIT_CONTRACT_VIEW_V1"
RESOURCE_KEYS = {
    "environment", "concurrency", "settle_seconds_between_worlds", "xla_host_devices",
    "checkpoint", "compact_outputs", "engineering_benchmark", "estimate",
}


class FitContractRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise FitContractRefused(f"REFUSED V2_CORE fit contract: {msg}")


def canonical_bytes(view: Mapping) -> bytes:
    return (json.dumps(dict(view), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def view_sha256(view: Mapping) -> str:
    return hashlib.sha256(canonical_bytes(view)).hexdigest()


def validate_fit_contract_view(view: Mapping) -> Mapping:
    if not isinstance(view, Mapping) or view.get("schema") != SCHEMA:
        _refuse("wrong/missing fit-contract schema")
    if view.get("source_contract_sha256") != SOURCE_CONTRACT_SHA256:
        _refuse("source contract hash differs")
    required = {"schema", "source_contract_sha256", "model", "parameterization", "priors", "inference",
                "resources", "seeds", "result_schemas"}
    if set(view) != required:
        _refuse(f"fit-contract key set differs: {sorted(set(view) ^ required)}")
    if view.get("model", {}).get("name") != "V2_CORE":
        _refuse("model is not V2_CORE")
    if set(view.get("priors", {})) != {"detection", "positive"}:
        _refuse("detection/positive priors missing")
    inf = view.get("inference", {})
    if inf.get("recovery_path", {}).get("version") != "V2_CORE_ONE_ESCALATION_ONE_EXTENSION_V1":
        _refuse("recovery authority differs")
    resources = view.get("resources", {})
    if set(resources) != RESOURCE_KEYS:
        _refuse("resource projection differs")
    if set(resources.get("estimate", {})) != {"n_fits"}:
        _refuse("resource estimate projection must expose only n_fits")
    if int(resources.get("xla_host_devices", -1)) != int(inf.get("chains", -2)):
        _refuse("XLA host-device count must equal frozen chain count")
    seeds = view.get("seeds", {})
    if set(seeds) != {"engineering_benchmark_root", "gene_streams"}:
        _refuse("seed projection differs")
    if set(seeds.get("gene_streams", {})) != {"fit_det_primary", "fit_det_escalation", "fit_pos_primary", "fit_pos_escalation"}:
        _refuse("fit seed stream projection differs")
    if set(view.get("result_schemas", {})) != {"fit_record"}:
        _refuse("fit result-schema projection differs")
    # The fit view may describe excluded operator/matrix terms, but may contain no world/gate identity.
    raw = json.dumps(dict(view), sort_keys=True)
    for forbidden in ("Q00_BASELINE", "Q11_OMITTED_OPERATOR", '"world_name"', '"world_index"', '"gates"'):
        if forbidden in raw:
            _refuse(f"controller identity leaked into fit contract: {forbidden}")
    return view


def load_fit_contract_view(path: Path, *, expected_sha256: str) -> dict:
    path = Path(path)
    if not path.is_file():
        _refuse("fit-contract view missing")
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        _refuse(f"fit-contract hash mismatch: {actual} != {expected_sha256}")
    try:
        view = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        _refuse(f"invalid fit-contract JSON: {exc}")
    validate_fit_contract_view(view)
    if canonical_bytes(view) != raw:
        _refuse("fit-contract bytes are not canonical")
    return view
