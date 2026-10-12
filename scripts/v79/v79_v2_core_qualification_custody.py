#!/usr/bin/env python3
"""Qualification execution custody helpers for V79 V2_CORE.

Controller-side only. This module binds the future qualification authorization to
exact frozen qualification bytes and to the controller-derived opaque seed ledger.
The returned authorization view contains no Q labels, world indices, truth, operator
or matrix identity and does not authorize scoring/training.
"""
from __future__ import annotations

import copy
import json
from typing import Mapping

from v79_v2_core_fit_contract import SOURCE_CONTRACT_SHA256
from v79_v2_core_fit_surface import QUALIFICATION_INDEX_SHA256

AUTH_SCHEMA = "V79_V2_CORE_QUALIFICATION_EXECUTION_AUTHORIZATION_V1"
EXPECTED_FITS = 1056


class QualificationCustodyRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise QualificationCustodyRefused(f"REFUSED V2_CORE qualification custody: {msg}")


def _canonical_ledger(ledger) -> list[dict]:
    if not isinstance(ledger, list) or len(ledger) != EXPECTED_FITS:
        _refuse(f"fit seed ledger must contain exactly {EXPECTED_FITS} records")
    out = []
    seen = set()
    for rec in ledger:
        if not isinstance(rec, Mapping) or set(rec) != {"fit_id", "primary_seed"}:
            _refuse("fit seed ledger record schema differs")
        fid = str(rec["fit_id"]); seed = rec["primary_seed"]
        if len(fid) != 64 or any(c not in "0123456789abcdef" for c in fid):
            _refuse("fit seed ledger contains invalid fit_id")
        if fid in seen or not isinstance(seed, int) or not (0 <= seed <= 0xffffffff):
            _refuse("fit seed ledger contains duplicate identity or invalid seed")
        seen.add(fid); out.append({"fit_id": fid, "primary_seed": int(seed)})
    out.sort(key=lambda x: x["fit_id"])
    return out


def _contains_forbidden_identity(obj) -> bool:
    text = json.dumps(obj, sort_keys=True)
    forbidden = ("Q00", "Q01", "Q02", "Q03", "Q04", "Q05", "Q06", "Q07", "Q08", "Q09", "Q10", "Q11",
                 "world_name", "world_index", "controller_truth", "operator", "matrix")
    return any(x in text for x in forbidden)


def sanitize_execution_authorization(auth: Mapping | None, *, expected_seed_ledger: list[Mapping]) -> dict:
    if not isinstance(auth, Mapping) or auth.get("schema") != AUTH_SCHEMA:
        _refuse("missing/wrong qualification execution authorization")
    if auth.get("qualification_campaign_authorized") is not True or auth.get("benchmark_controller_pass") is not True:
        _refuse("qualification campaign requires explicit authorization and benchmark controller pass")
    if auth.get("contract_sha256") != SOURCE_CONTRACT_SHA256 or auth.get("blinded_index_sha256") != QUALIFICATION_INDEX_SHA256:
        _refuse("authorization does not bind frozen contract/index")
    if auth.get("scoring_authorized") is not False or auth.get("training_authorized") is not False:
        _refuse("authorization crosses later scoring/training gates")
    expected = _canonical_ledger(list(expected_seed_ledger))
    observed = _canonical_ledger(copy.deepcopy(auth.get("fit_seed_ledger")))
    if observed != expected:
        _refuse("authorization seed ledger differs from controller-derived frozen ledger")
    out = {
        "schema": AUTH_SCHEMA,
        "qualification_campaign_authorized": True,
        "benchmark_controller_pass": True,
        "contract_sha256": SOURCE_CONTRACT_SHA256,
        "blinded_index_sha256": QUALIFICATION_INDEX_SHA256,
        "fit_seed_ledger": observed,
        "scoring_authorized": False,
        "training_authorized": False,
    }
    if _contains_forbidden_identity(out):
        _refuse("sanitized authorization leaks controller identity")
    return out
