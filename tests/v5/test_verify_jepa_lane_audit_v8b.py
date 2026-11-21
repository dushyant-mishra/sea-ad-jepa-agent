"""Hostile mutations for V8b active-head and authority drift."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts.v5.verify_jepa_lane_audit_v8b import DELTA,SUP,validate
ROOT=Path(__file__).resolve().parents[2]
def load():
    return json.loads((ROOT/DELTA).read_text()),json.loads((ROOT/SUP).read_text())

def test_current_v8b_passes():
    validate(*load(),ROOT)

@pytest.mark.parametrize("mut",[
 lambda d,s:d.update(authority="REAL_TRAINING_ON"),
 lambda d,s:d["changes"][0].update(head="f"*40),
 lambda d,s:d["changes"][0].update(classification="E2G_CAUSAL_PASS"),
 lambda d,s:d["changes"][1].update(classification="PS_TASK1_2_ACCEPTED"),
 lambda d,s:d["changes"][2].update(classification="TASK4_ACCEPTED"),
 lambda d,s:d["changes"][3].update(classification="SCIENTIFIC_AUTHORITY"),
 lambda d,s:s["active_heads"].update({"459":"0"*40}),
 lambda d,s:s["exact_classification"].update({"458":"GREEN"}),
 lambda d,s:s.update(authority="TARGET_WINNER_C1"),
])
def test_promotion_or_stale_head_rejected(mut):
    d,s=load()
    d,s=deepcopy(d),deepcopy(s)
    mut(d,s)
    with pytest.raises(ValueError):
        validate(d,s,ROOT)

def test_v8b_preserves_v8a_as_prior_source():
    _,s=load()
    assert "docs/agent/JEPA_POST_V8_SNAPSHOT_DELTA_V8A_20261027.md" in s["required_prior_files"]
    assert "results/target_discovery/unified_qualification_v1/JEPA_COMPLETE_TAKEOVER_FILE_INDEX_V8A_20261027.json" in s["required_prior_files"]
