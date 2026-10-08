from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_nihcard_recoverability_split_is_donor_disjoint_and_deterministic():
    p=json.loads((ROOT/"results/v64/V64_NIHCARD_PAIRED_RECOVERABILITY_PREFLIGHT_V1.json").read_text())
    s=p["split"]
    train=set(s["train_donors"]); val=set(s["validation_donors"]); test=set(s["test_donors"])
    assert not (train & val or train & test or val & test)
    assert len(train)==16 and len(val)==4 and len(test)==4
    donors=sorted(train|val|test)
    ranked=sorted(donors,key=lambda d:hashlib.sha256((s["seed_string"]+"|"+d).encode()).hexdigest())
    assert ranked[:16]==s["train_donors"]
    assert ranked[16:20]==s["validation_donors"]
    assert ranked[20:]==s["test_donors"]

def test_nihcard_preflight_did_not_open_crossmodal_outcome():
    p=json.loads((ROOT/"results/v64/V64_NIHCARD_PAIRED_RECOVERABILITY_PREFLIGHT_V1.json").read_text())
    assert "RNA-to-ATAC prediction" in p["explicitly_not_computed"]
    assert p["governance"]["stage4"]=="NOT_AUTHORIZED"
    assert p["governance"]["training"]=="OFF"
    assert p["pairing"]["rule_fail"]==0
