from __future__ import annotations
import json
from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]

def _load_split():
    p=ROOT/"scripts/v64/freeze_nihcard_paired_donor_split_v1.py"
    spec=importlib.util.spec_from_file_location("splitmod",p)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_donor_split_is_deterministic_disjoint_and_outcome_blind():
    m=_load_split()
    donors=["d"+str(i) for i in range(24)]
    a=m.make_split(donors,20260930); b=m.make_split(list(reversed(donors)),20260930)
    assert a==b
    assert len(a["train"])==16 and len(a["validation"])==4 and len(a["test"])==4
    assert not (set(a["train"])&set(a["validation"]))
    assert not (set(a["train"])&set(a["test"]))
    assert not (set(a["validation"])&set(a["test"]))

def test_frozen_real_split_does_not_authorize_correspondence():
    p=json.loads((ROOT/"results/v64/V64_NIHCARD_PAIRED_DONOR_SPLIT_V1.json").read_text())
    assert p["selection_inputs"]==["donor_id"]
    assert p["governance"]["cross_modal_biological_correspondence_opened"] is False
    assert p["governance"]["stage4"]=="NOT_AUTHORIZED"
    assert p["nuclei"]=={"train":1440,"validation":360,"test":360}

def test_dong_bridge_keeps_gencode_as_denominator_and_version_drift_explicit():
    p=json.loads((ROOT/"results/v64/V64_DONG_ROUSSOS_PROMOTER_RESOURCE_CUSTODY_AND_BRIDGE_AUDIT_V1.json").read_text())
    assert p["gencode_v50_bridge"]["data7_present_pct"]>98.0
    assert p["cross_resource_transcript_bridge"]["Data10"]["in_data7"]==24992
    assert "GENCODE v50 remains the candidate denominator" in p["gencode_v50_bridge"]["interpretation"]
    assert p["scientific_scope"]["Data10"].startswith("contextual")
