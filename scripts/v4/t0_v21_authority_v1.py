#!/usr/bin/env python3
"""Fail-closed production authority for the V21 decision path.

This module intentionally wraps, rather than rewrites, the numerical V21 executor.
A self-consistent score artifact is not sufficient production evidence: callers must
also present an externally expected source/model authority, fold-level provenance,
a matching nested-permutation result, and a prospectively sourced confirmation-design
receipt.  Protected reader partitions are never valid calibration-design sources.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import math
from typing import Any, Mapping, Sequence

import numpy as np

STOP = "STOP_T0_V21_AUTHORITY_NOT_VALID"
KIND = "t0_v21_authoritative_crossfit_v1"
PERM_KIND = "t0_v21_nested_permutation_evidence_v1"
DESIGN_KIND = "t0_v21_confirmation_design_receipt_v1"
N_DISCOVERY = 28
N_CONFIRMATION = 12
ALPHA = 0.025
FROZEN_PERMUTATIONS = 9999
PROTECTED_ROLES = frozenset({"reader_validation", "reader_oracle"})
AUTHORITY_FIELDS = (
    "expression_root_digest", "donor_role_ledger_digest", "donor_order_digest",
    "molecular_address_digest", "transformation_digest", "nuisance_spec_digest",
    "estimator_id", "target_code_sha", "contract_sha",
)
FOLD_FIELDS = (
    "held_out_donor_id", "train_donor_ids", "training_data_digest",
    "ridge_trace_digest", "fitted_target_digest", "prediction",
)


def _fail(message: str) -> None:
    raise RuntimeError(f"{STOP}: {message}")


def _plain(value: Any) -> Any:
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    if isinstance(value, Mapping): return {str(k): _plain(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (tuple, list)): return [_plain(v) for v in value]
    if isinstance(value, (str, int, bool)) or value is None: return value
    if isinstance(value, float):
        if not math.isfinite(value): _fail("nonfinite value cannot be hashed")
        return value
    _fail(f"unsupported canonical value type {type(value).__name__}")


def canonical_digest(value: Any, *, domain: str) -> str:
    payload = json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(domain.encode("ascii") + b"\0" + payload).hexdigest()


def _require_hex_digest(name: str, value: Any) -> str:
    text = str(value)
    if len(text) != 64 or any(c not in "0123456789abcdef" for c in text):
        _fail(f"{name} must be a lowercase SHA-256 digest")
    return text


def validate_source_authority(authority: Mapping[str, Any], expected: Mapping[str, Any]) -> str:
    if not isinstance(authority, Mapping) or not isinstance(expected, Mapping): _fail("source authority and expected authority must be mappings")
    missing = [k for k in AUTHORITY_FIELDS if k not in authority]
    expected_missing = [k for k in AUTHORITY_FIELDS if k not in expected]
    if missing or expected_missing: _fail(f"source authority fields missing: artifact={missing}, expected={expected_missing}")
    extra = sorted(set(authority) - set(AUTHORITY_FIELDS))
    if extra: _fail(f"unexpected source-authority fields {extra}")
    for field in AUTHORITY_FIELDS:
        if str(authority[field]) != str(expected[field]): _fail(f"source authority mismatch for {field}")
    for field in AUTHORITY_FIELDS:
        if field.endswith("_digest") or field.endswith("_sha"): _require_hex_digest(field, authority[field])
    return canonical_digest(dict(authority), domain="T0_V21_SOURCE_AUTHORITY_V1")


def seal_authoritative_crossfit(*, cross_fit_artifact: Mapping[str, Any], source_authority: Mapping[str, Any], fold_provenance: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    donor_ids = tuple(str(x) for x in cross_fit_artifact.get("donor_ids", ()))
    folds = tuple(cross_fit_artifact.get("folds", ()))
    scores = np.asarray(cross_fit_artifact.get("oof_scores", ()), dtype=np.float64)
    if len(donor_ids) != N_DISCOVERY or len(set(donor_ids)) != N_DISCOVERY: _fail("cross-fit must carry exactly 28 unique donor identifiers")
    if len(folds) != N_DISCOVERY or scores.shape != (N_DISCOVERY,) or not np.isfinite(scores).all(): _fail("cross-fit fold/score geometry is not exactly 28 finite OOF values")
    if len(fold_provenance) != N_DISCOVERY: _fail("exactly 28 fold-provenance records are required")
    expected_donors = set(donor_ids); normalized = []; seen = set()
    fold_by_held = {int(f["held_out_index"]): f for f in folds}
    if set(fold_by_held) != set(range(N_DISCOVERY)): _fail("cross-fit folds must hold out indexes 0..27 exactly once")
    for record in fold_provenance:
        missing = [k for k in FOLD_FIELDS if k not in record]
        if missing: _fail(f"fold provenance missing fields {missing}")
        held = str(record["held_out_donor_id"])
        if held in seen or held not in expected_donors: _fail(f"invalid/duplicate held-out donor {held}")
        seen.add(held); held_idx = donor_ids.index(held); legal_train = expected_donors - {held}
        train = tuple(str(x) for x in record["train_donor_ids"])
        if len(train) != N_DISCOVERY - 1 or set(train) != legal_train: _fail(f"fold for {held} does not bind the exact 27-donor complement")
        old_fold = fold_by_held[held_idx]
        old_train_ids = {donor_ids[int(i)] for i in old_fold["train_indices"]}
        if old_train_ids != legal_train: _fail(f"underlying cross-fit fold for {held} is not the legal complement")
        prediction = float(record["prediction"])
        if not math.isfinite(prediction) or prediction != float(scores[held_idx]): _fail(f"fold provenance prediction mismatch for {held}")
        for name in ("training_data_digest", "ridge_trace_digest", "fitted_target_digest"): _require_hex_digest(name, record[name])
        normalized.append({k: _plain(record[k]) for k in FOLD_FIELDS})
    if seen != expected_donors: _fail("not every discovery donor has fold provenance")
    source_digest = canonical_digest(dict(source_authority), domain="T0_V21_SOURCE_AUTHORITY_V1")
    body = {"kind": KIND, "cross_fit_artifact": _plain(cross_fit_artifact), "source_authority": _plain(source_authority), "source_authority_digest": source_digest, "fold_provenance": sorted(normalized, key=lambda r: r["held_out_donor_id"])}
    body["artifact_digest"] = canonical_digest(body, domain="T0_V21_AUTHORITATIVE_CROSSFIT_V1")
    return body


def validate_authoritative_crossfit(artifact: Mapping[str, Any], *, expected_source_authority: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(artifact, Mapping) or artifact.get("kind") != KIND: _fail("production decisions require t0_v21_authoritative_crossfit_v1")
    recorded = str(artifact.get("artifact_digest", "")); body = {k: artifact[k] for k in artifact if k != "artifact_digest"}
    recomputed = canonical_digest(body, domain="T0_V21_AUTHORITATIVE_CROSSFIT_V1")
    if recorded != recomputed: _fail("authoritative cross-fit digest does not recompute")
    source_digest = validate_source_authority(artifact.get("source_authority", {}), expected_source_authority)
    if artifact.get("source_authority_digest") != source_digest: _fail("source-authority digest mismatch")
    rebuilt = seal_authoritative_crossfit(cross_fit_artifact=artifact.get("cross_fit_artifact", {}), source_authority=artifact.get("source_authority", {}), fold_provenance=artifact.get("fold_provenance", ()))
    if rebuilt["artifact_digest"] != recorded: _fail("cross-fit structure differs from sealed authority")
    return {"verified": True, "artifact_digest": recorded, "source_authority_digest": source_digest}


def seal_nested_permutation_evidence(*, authoritative_crossfit_digest: str, source_authority_digest: str, nested_pipeline_code_sha: str, contract_sha: str, n_permutations: int, seed: int, p_upper: float, null_digest: str) -> dict[str, Any]:
    for n, v in (("authoritative_crossfit_digest", authoritative_crossfit_digest), ("source_authority_digest", source_authority_digest), ("nested_pipeline_code_sha", nested_pipeline_code_sha), ("contract_sha", contract_sha), ("null_digest", null_digest)): _require_hex_digest(n, v)
    if int(n_permutations) != FROZEN_PERMUTATIONS: _fail(f"decision evidence requires frozen B={FROZEN_PERMUTATIONS}")
    p = float(p_upper)
    if not (0.0 < p <= 1.0): _fail("nested-permutation p_upper must lie in (0,1]")
    body = {"kind": PERM_KIND, "authoritative_crossfit_digest": authoritative_crossfit_digest, "source_authority_digest": source_authority_digest, "nested_pipeline_code_sha": nested_pipeline_code_sha, "contract_sha": contract_sha, "n_permutations": int(n_permutations), "seed": int(seed), "alpha": ALPHA, "p_upper": p, "null_digest": null_digest}
    body["evidence_digest"] = canonical_digest(body, domain="T0_V21_NESTED_PERMUTATION_EVIDENCE_V1")
    return body


def validate_nested_permutation_evidence(evidence: Mapping[str, Any], *, artifact_digest: str, source_authority_digest: str, expected_pipeline_code_sha: str, expected_contract_sha: str) -> dict[str, Any]:
    if not isinstance(evidence, Mapping) or evidence.get("kind") != PERM_KIND: _fail("matching nested-permutation evidence is required")
    body = {k: evidence[k] for k in evidence if k != "evidence_digest"}
    if evidence.get("evidence_digest") != canonical_digest(body, domain="T0_V21_NESTED_PERMUTATION_EVIDENCE_V1"): _fail("nested-permutation evidence digest does not recompute")
    checks = {"authoritative_crossfit_digest": artifact_digest, "source_authority_digest": source_authority_digest, "nested_pipeline_code_sha": expected_pipeline_code_sha, "contract_sha": expected_contract_sha, "n_permutations": FROZEN_PERMUTATIONS, "alpha": ALPHA}
    for key, expected in checks.items():
        if str(evidence.get(key)) != str(expected): _fail(f"nested-permutation evidence mismatch for {key}")
    if float(evidence["p_upper"]) > ALPHA: _fail("nested discovery permutation test does not reject at frozen alpha")
    return {"verified": True, "evidence_digest": evidence["evidence_digest"], "p_upper": float(evidence["p_upper"])}


def seal_confirmation_design_receipt(*, age: Sequence[float], sex: Sequence[float], source_role: str, source_digest: str, contract_sha: str) -> dict[str, Any]:
    if source_role in PROTECTED_ROLES: _fail(f"protected role {source_role} cannot supply pre-unblinding calibration design")
    age_arr = np.asarray(age, dtype=np.float64); sex_arr = np.asarray(sex, dtype=np.float64)
    if age_arr.shape != (N_CONFIRMATION,) or sex_arr.shape != (N_CONFIRMATION,): _fail("confirmation design must contain exactly 12 donors")
    if not np.isfinite(age_arr).all() or not np.isfinite(sex_arr).all(): _fail("confirmation design must be finite")
    if not set(np.unique(sex_arr)).issubset({0.0, 1.0}) or len(np.unique(sex_arr)) != 2: _fail("confirmation sex design must contain both binary levels 0/1")
    _require_hex_digest("source_digest", source_digest); _require_hex_digest("contract_sha", contract_sha)
    body = {"kind": DESIGN_KIND, "source_role": str(source_role), "source_digest": source_digest, "contract_sha": contract_sha, "n": N_CONFIRMATION, "age_digest": canonical_digest(age_arr, domain="T0_V21_CONFIRMATION_AGE_V1"), "sex_digest": canonical_digest(sex_arr, domain="T0_V21_CONFIRMATION_SEX_V1")}
    body["receipt_digest"] = canonical_digest(body, domain="T0_V21_CONFIRMATION_DESIGN_RECEIPT_V1")
    return body


def validate_confirmation_design_receipt(receipt: Mapping[str, Any], *, age: Sequence[float], sex: Sequence[float], expected_contract_sha: str) -> dict[str, Any]:
    if not isinstance(receipt, Mapping) or receipt.get("kind") != DESIGN_KIND: _fail("a confirmation-design receipt is required")
    if receipt.get("source_role") in PROTECTED_ROLES: _fail("protected reader partitions cannot supply pre-unblinding design calibration")
    body = {k: receipt[k] for k in receipt if k != "receipt_digest"}
    if receipt.get("receipt_digest") != canonical_digest(body, domain="T0_V21_CONFIRMATION_DESIGN_RECEIPT_V1"): _fail("confirmation-design receipt digest does not recompute")
    if receipt.get("contract_sha") != expected_contract_sha: _fail("confirmation-design contract mismatch")
    expected_age = canonical_digest(np.asarray(age, dtype=np.float64), domain="T0_V21_CONFIRMATION_AGE_V1"); expected_sex = canonical_digest(np.asarray(sex, dtype=np.float64), domain="T0_V21_CONFIRMATION_SEX_V1")
    if receipt.get("age_digest") != expected_age or receipt.get("sex_digest") != expected_sex: _fail("confirmation design arrays do not match their prospective receipt")
    return {"verified": True, "receipt_digest": receipt["receipt_digest"]}


def decision_capable_power_gate(*, artifact: Mapping[str, Any], expected_source_authority: Mapping[str, Any], permutation_evidence: Mapping[str, Any], expected_nested_pipeline_code_sha: str, confirmation_age: Sequence[float], confirmation_sex: Sequence[float], confirmation_design_receipt: Mapping[str, Any], n_simulations: int = 2000, n_permutations: int = FROZEN_PERMUTATIONS, seed: int = 20260911) -> dict[str, Any]:
    """Only production-authoritative V21 power entry point; does not authorize holdout opening."""
    verified = validate_authoritative_crossfit(artifact, expected_source_authority=expected_source_authority)
    expected_contract = str(expected_source_authority["contract_sha"])
    perm = validate_nested_permutation_evidence(permutation_evidence, artifact_digest=verified["artifact_digest"], source_authority_digest=verified["source_authority_digest"], expected_pipeline_code_sha=expected_nested_pipeline_code_sha, expected_contract_sha=expected_contract)
    design = validate_confirmation_design_receipt(confirmation_design_receipt, age=confirmation_age, sex=confirmation_sex, expected_contract_sha=expected_contract)
    legacy = importlib.import_module("t0_v21_selection_and_power_v1")
    result = legacy.power_gate(artifact=artifact["cross_fit_artifact"], confirmation_age=np.asarray(confirmation_age, dtype=np.float64), confirmation_sex=np.asarray(confirmation_sex, dtype=np.float64), n_simulations=n_simulations, n_permutations=n_permutations, seed=seed)
    result["production_authority"] = {"crossfit": verified, "permutation": perm, "confirmation_design": design}
    return result
