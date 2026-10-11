#!/usr/bin/env python3
"""Fail-closed validator for the finalized V79 V2_CORE launch-authority envelope."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import finalize_v79_v2_core_contract as F


def validate_launch_contract(contract_path: Path, sha_path: Path, root: Path) -> dict:
    if contract_path.name != Path(F.FINAL_REL).name:
        raise SystemExit("STOP: only the finalized V2 authority filename is eligible")
    raw = contract_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if not sha_path.exists() or sha_path.read_text(encoding="utf-8").strip() != f"{digest}  {contract_path.name}":
        raise SystemExit("STOP: launch-authority SHA sidecar mismatch")
    expected = F.serialize_contract(F.build_final_contract(root))
    if raw != expected:
        raise SystemExit("STOP: launch authority differs from controller-ratified deterministic rebuild")
    c = json.loads(raw)
    if c.get("schema") != "V79_V2_CORE_QUALIFICATION_CONTRACT_V2_FINAL_AUTHORITY":
        raise SystemExit("STOP: wrong final authority schema")
    if c.get("status") != F.FINAL_STATUS or c.get("launch_authority") is not True:
        raise SystemExit("STOP: contract is not final launch authority")
    if c.get("world_generation_authorized") is not False or c.get("qualification_fits_run") != 0:
        raise SystemExit("STOP: finalization may not itself authorize or run qualification")
    ca = c.get("controller_authority", {})
    if ca.get("ruling_comment") != F.CONTROLLER_RULING_COMMENT or ca.get("model_decision") != F.CONTROLLER_MODEL_DECISION:
        raise SystemExit("STOP: controller authority binding mismatch")
    return c
