"""Hostile mutations of final JEPA takeover custody; no human data."""
from copy import deepcopy
import json
import pytest
from scripts.v5.verify_jepa_final_lane_takeover_freeze_20261028 import ROOT,DATA,validate,validate_root

def original():
    return json.loads((ROOT/DATA).read_text())

def test_original_final_freeze_validates():
    validate_root()

@pytest.mark.parametrize("attack",[
    lambda d:d.update(scientific_authority="REAL_TRAINING_ON"),
    lambda d:d.update(classification="INDEPENDENT_BIOLOGICAL_ACCEPTANCE"),
    lambda d:d.update(frozen_independently_reviewed_v8e_head="0"*40),
    lambda d:d["current_independent_review_state"][0].update(verdict="ACCEPT"),
    lambda d:d["current_independent_review_state"][1].update(verdict="FULL_G7_ACCEPT"),
    lambda d:d["current_independent_review_state"][2].update(verdict="TASK12_ACCEPT"),
    lambda d:d["current_independent_review_state"][3].update(verdict="TASK3_ACCEPT"),
    lambda d:d["current_independent_review_state"][4].update(independent_chatgpt_acceptance=True),
    lambda d:d["current_independent_review_state"][4].update(limitations=[]),
    lambda d:d["observation_contract_decision_status"].update(status="DECIDING_LANE_ACCEPTED"),
    lambda d:d["observation_contract_decision_status"]["D2"].update(recommended_default=True),
    lambda d:d["observation_contract_decision_status"]["g7_cross_head"].update(schema_compatible=True),
    lambda d:d["observation_contract_decision_status"]["g7_cross_head"].update(v3_reachable=True),
    lambda d:d.update(production_synthetic_blockers=[]),
    lambda d:d["source_and_data_custody"].update(original_large_binaries_in_github=True),
    lambda d:d["source_and_data_custody"].update(raw_binaries_recoverable_from_hash_alone=True),
    lambda d:d["source_and_data_custody"].update(raw_donor_or_per_cell_values_added_by_final_freeze=True),
    lambda d:d["source_and_data_custody"]["pasted_text_archived_extract"].update(known_correction="C3_IS_RARE"),
    lambda d:d.update(do_not_repeat=[]),
    lambda d:d.update(next_agent_order=[]),
])
def test_false_promotion_or_erasure_rejected(attack):
    d=deepcopy(original())
    attack(d)
    with pytest.raises(ValueError,match="JEPA_FINAL_TAKEOVER_FREEZE_REFUSAL"):
        validate(d)
