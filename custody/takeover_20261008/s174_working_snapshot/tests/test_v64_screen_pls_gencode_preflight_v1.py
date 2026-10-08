from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_screen_pls_is_annotation_not_candidate_filter():
    p=json.loads((ROOT/"results/v64/V64_SCREEN_PLS_GENCODE_TSS_PREFLIGHT_V1.json").read_text())
    assert p["status"]=="STRUCTURAL_ANNOTATION_ONLY__NO_CANDIDATE_PRUNING"
    assert p["results"]["gencode_exact_tss_candidates"]==389280
    assert p["results"]["candidates_overlapping_screen_pls"]==178778
    assert 0 < p["results"]["fraction_candidates_overlapping_screen_pls"] < 1
    assert "SCREEN_PLS_OVERLAP_DEFINES_PROMOTER_EXISTENCE" in p["forbidden_inference"]
    assert p["governance"]["promoter_selection_executed"] is False
