"""V8a remains evidence, not independent acceptance or science."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts.v5.verify_jepa_lane_audit_v8a import BASE,DELTA,INDEX,validate_delta,validate_index

ROOT=Path(__file__).resolve().parents[2]


def sources():
    return json.loads((ROOT/DELTA).read_text()),json.loads((ROOT/BASE).read_text())


def index_source():
    return json.loads((ROOT/INDEX).read_text())


def test_original_v8_plus_v8a_pass_without_promotion():
    validate_delta(*sources())


@pytest.mark.parametrize("mutate",[
    lambda x:x.update(authority="STAGE4_AUTHORIZED"),
    lambda x:x.update(original_v8_remains_immutable_historical_event=False),
    lambda x:next(r for r in x["records"] if r["pr"]==459).update(status="TASK4_CUMULATIVELY_ACCEPTED"),
    lambda x:next(r for r in x["records"] if r["pr"]==459).update(ci_green=[]),
    lambda x:next(r for r in x["records"] if r["pr"]==458).update(ci_red=[]),
    lambda x:next(r for r in x["records"] if r["pr"]==457).update(source_role="CAUSAL_BIOLOGY_PASS"),
    lambda x:x["clear_new_work"].update(ps_task1_2="FULLY_ACCEPTED"),
    lambda x:x["clear_new_work"].update(task4="INDEPENDENTLY_ACCEPTED"),
    lambda x:x["clear_new_work"].update(g7="QUALIFIED"),
    lambda x:x["clear_new_work"].update(e2g="CAUSAL_TF_BINDING"),
    lambda x:x["preserved_old_red"].remove(448),
    lambda x:x["new_red_ci_counts"]["ps_tasks_1_2"].update(failed=0),
    lambda x:x["task4_author_green_counts"].update(windows_skipped=0),
    lambda x:x.update(cannot_upgrade_from_ci=False),
])
def test_tampered_current_evidence_refused(mutate):
    delta,base=sources()
    tampered=deepcopy(delta)
    mutate(tampered)
    with pytest.raises(ValueError):
        validate_delta(tampered,base)


def test_v8a_delta_does_not_rewrite_the_v8_historical_recipient_list():
    delta,base=sources()
    before={r["pr"] for r in base["records"]}
    assert before.isdisjoint({457,458,459})
    assert {r["pr"] for r in delta["records"]}=={457,458,459}



def test_complete_takeover_file_index_is_machine_validated():
    validate_index(index_source())


@pytest.mark.parametrize("mutate",[
    lambda x:x.update(authority="TARGET_WINNER_C1"),
    lambda x:x["latest_post_v8_prs"][1].update(head="0"*40),
    lambda x:x["counts"].update(historical_audit_docs=1),
    lambda x:x["categories"]["historical_audit_docs"].remove("docs/agent/JEPA_LANE_AUDIT_SNAPSHOT_V8_20261027.md"),
    lambda x:x.update(raw_binary_policy="UPLOAD_ALL_ARCHIVES_TO_GITHUB"),
    lambda x:x.update(reviewer_independence="AUTHORS_MAY_SELF_ACCEPT"),
])
def test_complete_takeover_index_tampering_is_refused(mutate):
    item=deepcopy(index_source())
    mutate(item)
    with pytest.raises(ValueError):
        validate_index(item)
