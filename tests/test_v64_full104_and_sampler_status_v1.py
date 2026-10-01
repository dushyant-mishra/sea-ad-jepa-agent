from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_full104_discovery_subset_preflight_is_hash_bound_and_non_authorizing():
    p=json.loads((ROOT/"results/v64/V64_FULL104_DISCOVERY_SUBSET_PREFLIGHT_V1.json").read_text())
    assert p["source"]["hash_matches_claude_manifest"] is True
    assert p["source"]["bytes"]==50646637
    assert p["shape"]["cells"]==6000
    assert p["shape"]["donors"]==104
    assert p["shape"]["operators"]==42
    assert p["shape"]["addresses"]==17186
    assert p["address_space"]["zero_observed_local_addresses_in_subset"]==0
    assert p["sampling_design"]["population_prevalence_estimation_allowed"] is False
    assert p["governance"]["training"]=="OFF"
    assert p["governance"]["stage4"]=="NOT_AUTHORIZED"

def test_full104_reuses_existing_outer_donor_split():
    p=json.loads((ROOT/"results/v64/V64_FULL104_DISCOVERY_SUBSET_PREFLIGHT_V1.json").read_text())
    s=p["canonical_outer_split"]
    assert s["existing_split_id"]=="SOURCE_STRATIFIED_DONOR_HELD_OUT_V1"
    assert s["fold_sizes_donors"]==[28,26,25,25]
    assert len(s["source_receipt_sha256"])==64

def test_claude_sampler_sync_keeps_phaseA_blocked_until_real_edge_gate_finishes():
    p=json.loads((ROOT/"results/v64/V64_CLAUDE_EXACT_SAMPLER_STATUS_SYNC_V1.json").read_text())
    assert p["s50_production_no_op_evidence"]["payloads_identical"] is True
    assert p["s50_production_no_op_evidence"]["positive_control_reported_overlap_bp"]==4000
    assert p["supplement_rollup"]["A_supplement"]==177442
    assert p["supplement_rollup"]["uncovered"]==0
    assert p["real_edge_qualification"]["final_status"]=="IN_PROGRESS"
    assert p["phaseA_rerun"].startswith("BLOCKED")
