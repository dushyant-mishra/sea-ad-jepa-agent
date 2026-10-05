from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_fantom_screen_are_evidence_layers_not_candidate_filters():
    p=json.loads((ROOT/"results/v64/V64_FANTOM_SCREEN_GENCODE_PROMOTER_EVIDENCE_PREFLIGHT_V1.json").read_text())
    assert p["status"]=="STRUCTURAL_EVIDENCE_ANNOTATION_ONLY__NO_PROMOTER_SELECTION"
    states=p["screen_fantom_joint_states"]
    assert sum(states[k] for k in ["screen_pls_and_fantom_peak","screen_pls_only","fantom_peak_only","neither"])==389280
    assert p["fantom_results"]["candidates_same_strand_within_fantom_peak"]==126712
    assert p["fantom_results"]["candidates_exact_same_strand_representative_tss"]==25321
    assert "maximum_tss_distance_for_promoter_merging" in p["thresholds_not_frozen"]
    assert p["governance"]["promoter_selection_executed"] is False

def test_fantom_distance_tail_does_not_imply_fuzzy_merge_rule():
    p=json.loads((ROOT/"results/v64/V64_FANTOM_SCREEN_GENCODE_PROMOTER_EVIDENCE_PREFLIGHT_V1.json").read_text())
    q=p["nearest_same_strand_representative_tss_distance_bp"]
    assert q["median"]==133
    assert q["p75"]>10000
    assert q["p99"]>400000
