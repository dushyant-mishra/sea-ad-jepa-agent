"""Hostile mutation tests: don't erase historic RED or forge source custody."""
from __future__ import annotations
from copy import deepcopy
import pytest
from scripts.v5.verify_jepa_lane_takeover_master_20261028 import validate_root, verify, ROOT, ORIGINALS

def original():
 import json
 from scripts.v5.verify_jepa_lane_takeover_master_20261028 import LEDGER, AUDIT
 return json.loads((ROOT/LEDGER).read_text()),(ROOT/AUDIT).read_text(),dict(ORIGINALS)

def test_original_archive_and_source_blobs_are_nonpromoting():
 data=validate_root()
 assert data["science_gates"]["real_training_authorized"] is False
 assert data["ci_pins"]["pr480"]["review_expected_failed"]==3
 assert data["central_source_artifacts"]["source_binary_boundary"].endswith("NOT_HOSTED_IN_GITHUB")

@pytest.mark.parametrize("mutate",[
 lambda a:a[0].update(standing_authority="TARGET_C3_WINNER"),
 lambda a:a[0].update(classification="INDEPENDENT_HUMAN_BIOLOGY_ACCEPTED"),
 lambda a:a[0].update(frozen_accepted_v8e_head="0"*40),
 lambda a:a[0]["authoritative_source_pointers"][0].update(head="0"*40),
 lambda a:a[0]["central_source_artifacts"].update(source_binary_boundary="ALL_RAW_DATA_IN_GITHUB"),
 lambda a:a[0]["central_source_artifacts"]["original_local_g7_reports"][0].update(role="G7_E3_PASS"),
 lambda a:a[0]["central_source_artifacts"]["pasted_20261027_handoff"].update(status="CURRENT_C3_RARE_PRODUCTION_AUTHORITY"),
 lambda a:a[2].update({next(iter(a[2])):"f"*40}),
 lambda a:a[0]["science_decisions"][0].update(status="QUALIFIED_TARGET"),
 lambda a:a[0]["science_decisions"][1].update(name="RARE_MICROGLIA"),
 lambda a:a[0]["reviewer_verdicts"][0].update(verdict="ACCEPT_CUMULATIVE"),
 lambda a:a[0]["reviewer_verdicts"][1].update(verdict="ACCEPT_CUMULATIVE"),
 lambda a:a[0]["reviewer_verdicts"][5].update(repair_status="ACCEPTED"),
 lambda a:a[0]["ci_pins"]["pr480"].update(review_expected_failed=0),
 lambda a:a[0]["ci_pins"]["pr480"].update(not_promoted=False),
 lambda a:a[0]["ci_pins"]["pr479"].update(real_g7_cross_head_executed=True),
 lambda a:a[0]["science_gates"].update(real_training_authorized=True),
 lambda a:a[0]["science_gates"].update(g7_q_excluded_normalization_issuer="PASS"),
 lambda a:a[0]["science_gates"].update(g7_donor_specimen_independence="PASS"),
 lambda a:a[0]["science_gates"].update(production_synthetic_t2_external_scan_issuer="PASS"),
 lambda a:a[0]["science_gates"].update(production_synthetic_task4_candidate_neutral_biology="QUALIFIED"),
 lambda a:a[0]["current_source_supersession"].update(original_ledger_role="LATEST_ACCEPTED_BIOLOGY"),
 lambda a:a[0]["current_source_supersession"]["new_reviews"][0].update(verdict="ACCEPT"),
 lambda a:a[0]["current_source_supersession"]["new_reviews"][1].update(new_hostile_red=0),
 lambda a:a[0]["current_source_supersession"]["new_reviews"][2].update(verdict="FULL_PS_TASK1_2_ACCEPTED"),
 lambda a:a[0]["current_source_supersession"]["recent_task3_author_repair"].update(ci_status="INDEPENDENT_REAL_CALIBRATION_ACCEPTED"),
 lambda a:a[0]["current_source_supersession"]["recent_task3_author_repair"].update(observation_parameter_semantics_bound=True),
 lambda a:a[0]["current_source_supersession"]["observation_depth_decision"].update(status="APPROVED_HUMAN_R2"),
 lambda a:a[0]["current_source_supersession"]["observation_depth_decision"].update(same_code_path_v3_authorized=True),
 lambda a:a[0].update(next_actions=[]),
])
def test_false_promotion_or_source_mutation_refused(mutate):
 p=list(deepcopy(original()))
 mutate(p)
 with pytest.raises(ValueError,match="JEPA_TAKEOVER_NO_PROMOTION_REFUSAL"):
  verify(*p)
