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
    donors = []
    for d in range(104):
        retained = 1024 if d != 103 else 81
        tail, triplet_tail, triplet_population, sampled_triplets = (
            v._expected_operator_capacity(retained)
        )
        donors.append(
            {
                "donor_code": d,
                "source_code": 0 if d < 41 else (1 if d < 58 else 2),
                "fold_index": d % 4,
                "retained_cells": retained,
                "represented_operators": 1,
                "q95_tail_anchor_upper_bound": tail,
                "triplet_capable_tail_anchor_upper_bound": triplet_tail,
                "tail_triplet_population_upper_bound": triplet_population,
                "sampled_tail_triplet_upper_bound": sampled_triplets,
                "structurally_eligible": tail >= 5 and sampled_triplets >= 20,
            }
        )
    cases = []
    for s in range(3):
        for f in range(4):
            rows = [
                x for x in donors
                if x["source_code"] == s and x["fold_index"] == f
            ]
            cases.append(
                {
                    "source_code": s,
                    "fold_index": f,
                    "donors_total": len(rows),
                    "donors_structurally_eligible": len(rows),
                    "structurally_possible": len(rows) >= 4,
                }
            )
    assert all(x["structurally_possible"] for x in cases)

    operator_capacity = []
    for d in range(104):
        tail, triplet_tail, triplet_population, sampled_triplets = (
            v._expected_operator_capacity(donors[d]["retained_cells"])
        )
        operator_capacity.append(
            {
                "donor_code": d,
                "source_code": donors[d]["source_code"],
                "fold_index": donors[d]["fold_index"],
                "operator_code": d % 42,
                "retained_cells": donors[d]["retained_cells"],
                "q95_tail_anchor_upper_bound": tail,
                "triplet_capable_tail_anchor_upper_bound": triplet_tail,
                "tail_triplet_population_upper_bound": triplet_population,
                "sampled_tail_triplet_upper_bound": sampled_triplets,
            }
        )
    payload = {
        "schema": "V5_FULL104_RARE_TAIL_STRUCTURAL_SUPPORT_PREFLIGHT_V1",
        "status": "STRUCTURALLY_POSSIBLE__MOLECULAR_ESTIMABILITY_UNPROVEN",
        "structurally_possible_all_source_fold_cases": True,
        "operator_capacity": operator_capacity,
        "donor_capacity": donors,
        "source_fold_cases": cases,
        "tail_anchor_minimum_per_donor": 5,
        "resolved_triplet_minimum_per_donor": 20,
        "triplets_per_stratum_cap": 64,
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
        "evaluator_source_normalized_text_sha256": v.normalized_text_sha256(v.EVALUATOR),
        "runner_source_normalized_text_sha256": v.normalized_text_sha256(v.RUNNER),
        "source_hash_normalization": "UTF8_TEXT__CRLF_CR_TO_LF_V1",
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


def test_validator_rejects_resealed_capacity_arithmetic_drift() -> None:
    v = _load_validator()
    payload = _payload(v)
    payload["operator_capacity"][0]["sampled_tail_triplet_upper_bound"] += 1
    payload["donor_capacity"][0]["sampled_tail_triplet_upper_bound"] += 1
    payload["structural_preflight_sha256"] = v.canonical_sha256(
        {k: value for k, value in payload.items() if k != "structural_preflight_sha256"}
    )
    with pytest.raises(ValueError, match="sampled triplet capacity disagrees with frozen arithmetic"):
        v.validate_structural_receipt(payload, sample_dir=SAMPLE_DIR)


def test_normalized_source_hash_is_crlf_lf_stable(tmp_path: Path) -> None:
    v = _load_validator()
    lf = tmp_path / "lf.py"
    crlf = tmp_path / "crlf.py"
    lf.write_bytes(b"print('x')\nprint('y')\n")
    crlf.write_bytes(b"print('x')\r\nprint('y')\r\n")
    assert v.normalized_text_sha256(lf) == v.normalized_text_sha256(crlf)
