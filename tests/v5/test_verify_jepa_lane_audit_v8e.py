"""V8e append-only machine-evidence hostile mutation tests."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts.v5.verify_jepa_lane_audit_v8e import MACHINE,validate
ROOT=Path(__file__).resolve().parents[2]
def source():
    return json.loads((ROOT/MACHINE).read_text(encoding="utf-8"))
def test_ledger_validates():
    validate(source(),ROOT)
@pytest.mark.parametrize("change",[
    lambda d:d.update(authority="REAL_TRAINING_ON"),
    lambda d:d.update(append_only=False),
    lambda d:d.update(prior_audit_head="f"*40),
    lambda d:d.update(frozen_history=[]),
    lambda d:d["evidence"][0].update(result="TASK4_CUMULATIVE_ACCEPTED"),
    lambda d:d["evidence"][0].update(review_comment_id=0),
    lambda d:d["evidence"][0].update(parent_review_sha="0"*40),
    lambda d:d["evidence"][0].update(limitations=[]),
    lambda d:d["evidence"][1].update(result="UNIFIED_TASK1_ACCEPTED"),
    lambda d:d["evidence"][1].update(test_only=False),
    lambda d:d["evidence"][1]["ci"].update(hostile_red=999),
    lambda d:d["evidence"][2].update(result="ENCODER_ACCEPTED"),
    lambda d:d["evidence"][2].update(head="0"*40),
    lambda d:d["evidence"][2]["ci"].update(focused=999),
    lambda d:d["evidence"][3].update(result="PS_T1_T2_ACCEPTED"),
    lambda d:d["evidence"][4].update(result="CAUSAL_MICROGLIA_REGULATION"),
    lambda d:d["evidence"][4].update(source_limit="independently verified"),
    lambda d:d["governance"].update(task4_cumulative_accepted=True),
    lambda d:d["governance"].update(real_training=True),
    lambda d:d["governance"].update(macha_reviews=[]),
])
def test_hostile_rewrite_rejected(change):
    d=deepcopy(source())
    change(d)
    with pytest.raises(ValueError):
        validate(d,ROOT)
def test_v8d_and_reviewer_red_remain_separately_pinned():
    d=source()
    assert d["prior_audit_head"]=="a4c86fa83adf0cd718105807e9d254e09c989610"
    assert next(x for x in d["evidence"] if x["pr"]==466)["test_only"] is True
