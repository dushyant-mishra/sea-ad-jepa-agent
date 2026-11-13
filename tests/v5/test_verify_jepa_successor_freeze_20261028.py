"""Hostile custody mutations; no real data, no replay of independent RED tests."""
from copy import deepcopy
import json

import pytest

from scripts.v5.verify_jepa_successor_freeze_20261028 import ROOT, DATA, validate, validate_root

def original():
    return json.loads((ROOT/DATA).read_text(encoding="utf-8"))

def test_all_12_source_blobs_and_original_unpromoted_results():
    validate_root()

@pytest.mark.parametrize("attack", [
    lambda d:d.update(scientific_standing="STAGE4_AUTHORIZED"),
    lambda d:d.update(kind="INDEPENDENT_BIOLOGICAL_ACCEPTANCE"),
    lambda d:d.update(frozen_prior_independent_V8e_head="0"*40),
    lambda d:d["existing_historical_no_repeat"][0].update(status="TD57C_PASS"),
    lambda d:d["new_independent_review"].update(head="0"*40),
    lambda d:d["new_independent_review"]["original_files"][0].__setitem__(1,"f"*40),
    lambda d:d["new_independent_review"]["verdicts"][0].update(verdict="ACCEPT"),
    lambda d:d["new_independent_review"]["verdicts"][0].update(new_red_failed=0),
    lambda d:d["new_independent_review"]["verdicts"][1].update(remaining_external_hostiles=0),
    lambda d:d["new_independent_review"]["verdicts"][2].update(new_red_failed_each_platform=0),
    lambda d:d["original_red_tests_archived_outside_collection"][0].update(blob="0"*40),
    lambda d:d["task3_repair_candidate"].update(independently_accepted=True),
    lambda d:d["task3_repair_candidate"].update(source_git_blob="0"*40),
    lambda d:d["task3_repair_candidate"].update(limitations=[]),
    lambda d:d["task3_repair_candidate"]["ci"][0].update(result="FAILURE"),
    lambda d:d["new_observation_decision_proposed"].update(status="DECIDING_LANE_ACCEPTED"),
    lambda d:d["new_observation_decision_proposed"]["D2"].update(default_recommendation=True),
    lambda d:d["new_observation_decision_proposed"]["crosshead"].update(v3_reachable=True),
    lambda d:d["new_observation_decision_proposed"]["crosshead"].update(rename_adapter_accepted=200),
    lambda d:d["new_observation_decision_proposed"].update(blocked=[]),
    lambda d:d["data_custody"].update(original_binaries_in_github=True),
    lambda d:d["data_custody"].update(human_raw_values_or_donor_identifiers_committed_by_this_freeze=True),
])
def test_false_promotion_erasure_of_red_or_source_drift_rejected(attack):
    d=deepcopy(original())
    attack(d)
    with pytest.raises(ValueError,match="JEPA_OCT28_SUCCESSOR_FREEZE_NO_PROMOTION"):
        validate(d)
