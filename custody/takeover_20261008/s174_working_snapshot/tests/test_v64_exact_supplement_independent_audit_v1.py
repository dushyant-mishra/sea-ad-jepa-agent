from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_exact_supplement_independent_audit_reconciles_and_stays_blocked():
    p=json.loads((ROOT/"results/v64/V64_EXACT_SUPPLEMENT_INDEPENDENT_SHARD_AUDIT_V1.json").read_text())
    s=p["independent_receipt_sum"]
    assert s["safe_affine_positions"]+s["supplement_candidates"]==s["band_positions"]
    assert s["A_interior_card"]+s["A_supplement_card"]==s["A_exact_card"]
    assert s["uncovered"]==0
    assert s["A_supplement_card"]==177442
    assert p["verification"]["all_canonical_payload_sha256_match_receipts"] is True
    assert p["verdict"].endswith("SAMPLER_NOT_YET_QUALIFIED")
    assert p["phaseA_status"]=="BLOCKED_UNTIL_FULL_SAMPLER_QUALIFICATION"
    assert p["governance"]["training"]=="OFF"

def test_s50_no_op_does_not_generalize_beyond_production_chain():
    p=json.loads((ROOT/"results/v64/V64_EXACT_SUPPLEMENT_INDEPENDENT_SHARD_AUDIT_V1.json").read_text())
    s=p["S50_status"]
    assert s["production_shard0_payload_before_after_identical"] is True
    assert s["production_target_span_shadowed_by_other_chain_blocks_bp"]==0
    assert s["positive_control_planted_overlap_bp"]==4000
    assert "does not imply" in s["interpretation"]
