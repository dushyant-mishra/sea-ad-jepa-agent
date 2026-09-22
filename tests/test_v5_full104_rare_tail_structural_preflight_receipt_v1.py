from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/agent/validate_full104_rare_tail_structural_preflight_v1_20260922.py"
SAMPLE_DIR = ROOT / "analysis/v5_full104_target_qualification_20260921/evidence/real_sample"


def _load_validator():
    spec = importlib.util.spec_from_file_location("structural_receipt_validator", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _payload(v):
    sample_digest, sample_file_sha = v._sample_receipt_digest(SAMPLE_DIR)
    donors = [
        {
            "donor_code": d,
            "source_code": 0 if d < 41 else (1 if d < 58 else 2),
            "fold_index": d % 4,
            "retained_cells": 1024 if d != 103 else 81,
            "represented_operators": 1,
            "q95_tail_anchor_upper_bound": 5,
            "triplet_capable_tail_anchor_upper_bound": 5,
            "tail_triplet_upper_bound": 100,
            "structurally_eligible": True,
        }
        for d in range(104)
    ]
    cases = [
        {
            "source_code": s,
            "fold_index": f,
            "donors_total": 4,
            "donors_structurally_eligible": 4,
            "structurally_possible": True,
        }
        for s in range(3)
        for f in range(4)
    ]
    payload = {
        "schema": "V5_FULL104_RARE_TAIL_STRUCTURAL_SUPPORT_PREFLIGHT_V1",
        "status": "STRUCTURALLY_POSSIBLE__MOLECULAR_ESTIMABILITY_UNPROVEN",
        "structurally_possible_all_source_fold_cases": True,
        "operator_capacity": [
            {
                "donor_code": 0,
                "source_code": 0,
                "fold_index": 0,
                "operator_code": 0,
                "retained_cells": 105553,
                "q95_tail_anchor_upper_bound": 5278,
                "triplet_capable_tail_anchor_upper_bound": 5278,
                "tail_triplet_upper_bound": 999999,
            }
        ],
        "donor_capacity": donors,
        "source_fold_cases": cases,
        "tail_anchor_minimum_per_donor": 5,
        "resolved_triplet_minimum_per_donor": 20,
        "measurable_donor_minimum_per_source_fold": 4,
        "zxy_molecular_outcome_opened": False,
        "rare_tail_molecular_pass_claimed": False,
        "teacher_tail_evaluation_authorized": False,
        "training_authorized": False,
        "sample_receipt_sha256": sample_digest,
        "sample_receipt_file_sha256": sample_file_sha,
        "full104_block_manifest_sha256": v.EXPECTED_BLOCK_MANIFEST_SHA256,
        "retained_cells": 105553,
        "retained_donors": 104,
        "operators_present": 42,
        "blocks_by_operator": {str(i): 1 for i in range(42)},
        "operator_derivation": "test fixture",
        "sample_role_id": "FULL104_TARGET_QUALIFICATION_ONLY__NOT_MASKING__NOT_TRAINING_V1",
        "evaluator_source_sha256": v.sha256_file(v.EVALUATOR),
        "runner_source_sha256": v.sha256_file(v.RUNNER),
        "result_role": "METADATA_ONLY_STRUCTURAL_SUPPORT__NOT_MOLECULAR_QUALIFICATION",
        "expression_opened": False,
        "count_matrix_opened": False,
        "molecular_distance_computed": False,
    }
    payload["structural_preflight_sha256"] = v.canonical_sha256(payload)
    return payload


def test_validator_accepts_content_addressed_structural_only_receipt() -> None:
    v = _load_validator()
    payload = _payload(v)
    out = v.validate_structural_receipt(payload, sample_dir=SAMPLE_DIR)
    assert out["status"] == "PASS_FULL104_RARE_TAIL_STRUCTURAL_PREFLIGHT_RECEIPT_V1"
    assert out["molecular_outcome_opened"] is False
    assert out["training_authorized"] is False


def test_validator_rejects_digest_tamper() -> None:
    v = _load_validator()
    payload = _payload(v)
    payload["operators_present"] = 41
    with pytest.raises(ValueError, match="canonical digest mismatch"):
        v.validate_structural_receipt(payload, sample_dir=SAMPLE_DIR)


def test_validator_rejects_molecular_promotion_even_if_resealed() -> None:
    v = _load_validator()
    payload = _payload(v)
    payload["rare_tail_molecular_pass_claimed"] = True
    payload["structural_preflight_sha256"] = v.canonical_sha256(
        {k: value for k, value in payload.items() if k != "structural_preflight_sha256"}
    )
    with pytest.raises(ValueError, match="rare_tail_molecular_pass_claimed must remain false"):
        v.validate_structural_receipt(payload, sample_dir=SAMPLE_DIR)


def test_validator_rejects_incomplete_source_fold_grid_even_if_resealed() -> None:
    v = _load_validator()
    payload = _payload(v)
    payload["source_fold_cases"] = payload["source_fold_cases"][:-1]
    payload["structural_preflight_sha256"] = v.canonical_sha256(
        {k: value for k, value in payload.items() if k != "structural_preflight_sha256"}
    )
    with pytest.raises(ValueError, match="exactly 12 source x fold cases"):
        v.validate_structural_receipt(payload, sample_dir=SAMPLE_DIR)
