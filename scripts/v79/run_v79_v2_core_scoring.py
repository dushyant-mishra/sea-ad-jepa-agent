#!/usr/bin/env python3
"""Controller-only physical scoring runner primitives for V79 V2_CORE.

This module is engineering-only until a separate post-campaign scoring authorization
exists. It does not fit models. Its first responsibility is custody: verify the exact
completed fit ledger, exact canonical scoring authorization, write-once controller
outputs, and keep every downstream authority false.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Mapping

import v79_v2_core_score_authority as A


class ScoringRunRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise ScoringRunRefused(f"REFUSED V2_CORE scoring run: {msg}")


def _canon(obj: Mapping) -> bytes:
    return (json.dumps(dict(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _hex64(value) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _git_sha(value) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _safe_fit_record_path(result_dir: Path, rel: str) -> Path:
    if not isinstance(rel, str):
        _refuse("fit-record path must be a string")
    p = Path(rel)
    if p.is_absolute() or len(p.parts) != 1 or p.name != rel or not re.fullmatch(r"fit_[0-9a-f]{64}\.json", rel):
        _refuse(f"unsafe/noncanonical fit-record path {rel!r}")
    out = result_dir / p
    if not out.is_file():
        _refuse(f"missing fit record {rel}")
    try:
        out.resolve(strict=True).relative_to(result_dir.resolve(strict=True))
    except Exception:
        _refuse(f"fit-record path escapes result directory: {rel}")
    return out


def load_fit_receipts(campaign: Mapping, result_dir: Path) -> list[dict]:
    """Load exactly the campaign-ledger JSON fit receipts, hash-first and with no extras."""
    if not isinstance(campaign, Mapping):
        _refuse("campaign object required")
    rows = campaign.get("fit_records")
    if not isinstance(rows, list) or not rows:
        _refuse("campaign fit-record ledger missing")
    result_dir = Path(result_dir)
    if not result_dir.is_dir():
        _refuse("fit result directory missing")

    expected_names = set()
    loaded = []
    seen_ids = set()
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {"fit_id", "path", "sha256"}:
            _refuse("campaign fit-record ledger schema differs")
        fid = row.get("fit_id"); rel = row.get("path"); expected_sha = row.get("sha256")
        if not _hex64(fid) or not _hex64(expected_sha) or fid in seen_ids:
            _refuse("fit-record identity/hash differs or duplicates")
        path = _safe_fit_record_path(result_dir, rel)
        if path.name != f"fit_{fid}.json":
            _refuse("fit-record path does not match fit identity")
        actual_sha = _sha(path)
        if actual_sha != expected_sha:
            _refuse(f"fit-record SHA-256 mismatch for {fid}")
        raw = path.read_bytes()
        try:
            rec = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            _refuse(f"invalid fit-record JSON for {fid}: {exc}")
        if not isinstance(rec, dict) or rec.get("fit_id") != fid:
            _refuse(f"fit-record payload identity differs for {fid}")
        expected_names.add(path.name); seen_ids.add(fid); loaded.append(rec)

    physical = {p.name for p in result_dir.iterdir() if p.is_file() and re.fullmatch(r"fit_[0-9a-f]{64}\.json", p.name)}
    if physical != expected_names:
        _refuse(f"fit-record physical set differs; extra={sorted(physical-expected_names)}, missing={sorted(expected_names-physical)}")
    return loaded


def load_scoring_authorization(path: Path, *, expected_sha256: str,
                               campaign_receipt_sha256: str, scorer_code_sha: str) -> dict:
    path = Path(path)
    if not _hex64(expected_sha256) or not path.is_file():
        _refuse("scoring authorization path/hash missing")
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        _refuse("scoring authorization SHA-256 mismatch")
    try:
        auth = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        _refuse(f"invalid scoring authorization JSON: {exc}")
    if not isinstance(auth, dict) or _canon(auth) != raw:
        _refuse("scoring authorization bytes are not canonical")
    return A.validate_scoring_authorization(auth, campaign_receipt_sha256=campaign_receipt_sha256,
                                            scorer_code_sha=scorer_code_sha)


def write_json_once(path: Path, obj: Mapping) -> str:
    if not isinstance(obj, Mapping):
        _refuse("write-once JSON payload must be an object")
    path = Path(path); raw = _canon(obj); digest = hashlib.sha256(raw).hexdigest()
    if path.exists():
        if path.read_bytes() != raw:
            _refuse(f"refusing to overwrite changed scoring artifact {path.name}")
        return digest
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return digest


def q10_q11_heldout_model_metric(fit_receipt: Mapping) -> float:
    if not isinstance(fit_receipt, Mapping):
        _refuse("fit receipt required for held-out metric")
    part = fit_receipt.get("part")
    held = fit_receipt.get("heldout_predictive")
    if not isinstance(held, Mapping) or not isinstance(held.get("new_donor"), Mapping):
        _refuse("new-donor held-out summary missing")
    rec = held["new_donor"]
    key = "mean_log_loss" if part == "detection" else "mean_lpd" if part == "positive" else None
    if key is None or key not in rec:
        _refuse("held-out metric missing for fit part")
    value = rec[key]
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        _refuse("held-out metric must be finite")
    return float(value)


def scoring_run_receipt(*, scorer_code_sha: str, campaign_receipt_sha256: str,
                        scoring_authorization_sha256: str, scored_rows_sha256: str,
                        gate_table_sha256: str, descriptive_metrics_sha256: str,
                        adjudication_sha256: str) -> dict:
    if not _git_sha(scorer_code_sha):
        _refuse("scorer code head must be exact 40-hex Git SHA")
    hashes = {
        "campaign_receipt_sha256": campaign_receipt_sha256,
        "scoring_authorization_sha256": scoring_authorization_sha256,
        "scored_rows": scored_rows_sha256,
        "gate_table": gate_table_sha256,
        "descriptive_metrics": descriptive_metrics_sha256,
        "adjudication": adjudication_sha256,
    }
    if any(not _hex64(v) for v in hashes.values()):
        _refuse("scoring receipt hash binding must be 64-hex")
    return {
        "schema": "V79_V2_CORE_QUALIFICATION_SCORING_RUN_RECEIPT_V1",
        "contract_sha256": A.CONTRACT_SHA256,
        "root_manifest_sha256": A.ROOT_MANIFEST_SHA256,
        "blinded_index_sha256": A.BLINDED_INDEX_SHA256,
        "realization_audit_receipt_sha256": A.REALIZATION_AUDIT_RECEIPT_SHA256,
        "campaign_receipt_sha256": campaign_receipt_sha256,
        "scoring_authorization_sha256": scoring_authorization_sha256,
        "scorer_code_sha": scorer_code_sha,
        "outputs": {
            "scored_rows": scored_rows_sha256,
            "gate_table": gate_table_sha256,
            "descriptive_metrics": descriptive_metrics_sha256,
            "adjudication": adjudication_sha256,
        },
        "qualification_scoring_run": True,
        "real_train_posterior_authorized": False,
        "factorial_science_authorized": False,
        "training_authorized": False,
    }
