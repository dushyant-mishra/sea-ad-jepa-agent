import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"target_discovery"/"independent_checks"/"20260909_measurement_shortcut_attack"

def load(name):
    return json.loads((BASE/name).read_text(encoding="utf-8"))

def test_td57b_measurement_shortcut_is_nontrivial_but_not_target_redesign():
    o=load("TD57B_EXPLICIT_MEASUREMENT_SHORTCUT_ATTACK_V1.json")
    assert o["summary"]["minimum"] == 0.55234375
    assert o["summary"]["maximum"] == 0.6564968785030993
    assert o["measurable_donors"] == {"HVS":36,"NPH52":16,"SEA_AD":46}
    assert o["pathology_used"] is False
    assert o["training_authorized"] is False
    assert o["target_redesign_authorized"] is False

def test_td59_qc_shortcut_is_smaller_and_firewalled():
    o=load("TD59_EXPLICIT_MEASUREMENT_SHORTCUT_ATTACK_V1.json")
    assert o["summary"]["minimum"] == 0.4804257516370549
    assert o["summary"]["maximum"] == 0.5566964285714286
    assert o["measurable_donors"] == {"HVS":29,"NPH52":16,"SEA_AD":46}
    assert o["summary"]["maximum"] < load("TD57B_EXPLICIT_MEASUREMENT_SHORTCUT_ATTACK_V1.json")["summary"]["maximum"]
    assert o["pathology_used"] is False
    assert o["training_authorized"] is False
    assert o["target_redesign_authorized"] is False

def test_static_identity_shortcuts_are_structurally_blocked_by_triplet_design():
    for name in ("TD57B_EXPLICIT_MEASUREMENT_SHORTCUT_ATTACK_V1.json",
                 "TD59_EXPLICIT_MEASUREMENT_SHORTCUT_ATTACK_V1.json"):
        s=load(name)["structural_shortcuts"]
        assert s["donor_only"].startswith("CONSTANT_WITHIN")
        assert s["operator_only"].startswith("CONSTANT_WITHIN")
        assert s["source_only"].startswith("CONSTANT_WITHIN")
        assert s["support_fingerprint_only"].startswith("CONSTANT_WITHIN_OPERATOR")
        assert s["operator_measurement_mask_only"].startswith("CONSTANT_WITHIN_OPERATOR")
