"""V8c no-repeat hostile mutations against new RED, CI and authority records."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.v5.verify_jepa_lane_audit_v8c import DELTA, validate

ROOT = Path(__file__).resolve().parents[2]


def original():
    return json.loads((ROOT / DELTA).read_text(encoding="utf-8"))


def test_v8c_current_exact_static_snapshot_passes():
    validate(original(), ROOT)


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(authority="REAL_TRAINING_ON"),
    lambda d: d.update(no_qualification_promotion=False),
    lambda d: d.update(append_only=False),
    lambda d: d.update(prior_audit_head="f"*40),
    lambda d: d["current"][0].update(head="0"*40),
    lambda d: d["current"][1].update(classification="PS_TASKS1_2_ACCEPTED"),
    lambda d: d["current"][2].update(classification="TASK4_CUMULATIVELY_ACCEPTED"),
    lambda d: d["current"][3].update(head="f"*40),
    lambda d: d["current"][4].update(classification="UNIFIED_TASK1_ACCEPTED_UNQUALIFIED"),
    lambda d: d["current"][5].update(classification="X1_ACCEPTED"),
    lambda d: d["current"][5]["ci"][2].update(run_id=40518058012),
    lambda d: d["current"][5]["ci"][0].update(exact_head="f"*40),
    lambda d: d["evidence_boundaries"].update(e2g="causal TF verified"),
    lambda d: d["evidence_boundaries"].update(ps_task1_2="attestations trusted"),
])
def test_promotions_and_false_lineage_refused(mutate):
    d = deepcopy(original())
    mutate(d)
    with pytest.raises(ValueError):
        validate(d, ROOT)


def test_v8c_references_frozen_v8b_and_v8a_without_rewriting():
    d = original()
    assert "JEPA_POST_V8A_DELTA_V8B_20261027.json" in " ".join(d["prior_files"])
    assert "JEPA_COMPLETE_TAKEOVER_FILE_INDEX_V8A_20261027.json" in " ".join(d["prior_files"])
    assert d["prior_audit_head"] == "c07659ccce04bec18a43cc4a371ec0bf277c9255"
