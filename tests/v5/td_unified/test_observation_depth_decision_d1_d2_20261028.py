"""Governance guard for the October 28 D1/D2 observation-depth decision.

This test validates the frozen decision artifact only. It does not qualify a
real observation issuer or scientific target.
"""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DECISION = ROOT / "results/target_discovery/unified_qualification_v1/JEPA_OBSERVATION_DEPTH_DECISION_D1_D2_20261028.json"


def test_d1_d2_decision_is_fail_closed_and_does_not_redefine_physical_library():
    d = json.loads(DECISION.read_text(encoding="utf-8"))

    assert d["D1"]["status"] == "ACCEPTED_AS_VERSIONED_RELEASED_NORMALIZATION_DEPTH_CONTRACT"
    assert d["D1"]["depth_rule"] == "VISIBLE_BASE_MAPPED_SUM_V1"
    assert d["D1"]["field_name"] == "normalization_depth"
    assert d["D1"]["requires_private_physical_total"] is False
    assert d["D1"]["consumer_exactly_recomputable"] is True
    assert d["D1"]["real_execution_qualified"] is False

    assert d["D2"]["status"] == "REJECTED_FROM_CURRENT_RELEASED_CONTRACT"
    assert d["D2"]["current_version_admissible"] is False
    assert d["D2"]["default_allowed"] is False
    assert d["D2"]["consumer_exactly_recomputable"] is False

    assert d["physical_library_size"]["semantics"] == "UNCHANGED_PHYSICAL_TOTAL"
    assert d["physical_library_size"]["casebundle_v1_preserved"] is True
    assert d["physical_library_size"]["g7_e3_v1_preserved"] is True
    assert d["physical_library_size"]["d1_may_be_renamed_library_size"] is False

    assert d["g7"]["d1_requires_new_versioned_g7_e3_v2"] is True
    assert d["g7"]["terminal_v3_decision_law_changed"] is False
    assert d["real_target_qualification_authorized"] is False
    assert d["stage4_authorized"] is False
    assert d["training_authorized"] is False
    assert d["project_stop"] == (
        "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__"
        "REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
    )
