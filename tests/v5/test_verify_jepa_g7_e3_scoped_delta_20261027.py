"""Hostile audit mutation regressions; never human biology or sealed data."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.v5.verify_jepa_g7_e3_macha449_scoped_delta_20261027 import RELATIVE, validate

ROOT = Path(__file__).resolve().parents[2]

def original():
    return json.loads((ROOT/RELATIVE).read_text(encoding="utf-8"))

def test_authentic_appended_delta_is_source_limited():
    record=original()
    validate(record)
    assert record["authority"].endswith("STAGE4_NOT_AUTHORIZED")
    assert {v["finding"] for v in record["known_unresolved"]} == {"R1","R2"}
    assert record["ci"]["full_conclusion"] == "FAILURE"
    assert record["ci"]["full_failed"] == 10
    assert record["ci"]["independent_acceptance"] is False

@pytest.mark.parametrize("tamper", [
    lambda d:d.update(authority="TRAINING_AUTHORIZED"),
    lambda d:d.update(document_kind="INDEPENDENT_G7_E3_ACCEPTANCE"),
    lambda d:d["parent_qualified_audit"].update(previous_head="f"*40),
    lambda d:d["repair_candidate"].update(status="ACCEPTED_CUMULATIVELY"),
    lambda d:d["repair_candidate"].update(head="f"*40),
    lambda d:d["source_review"].update(verdict="GREEN"),
    lambda d:d["unchanged_tests"].update(macha_recheck_git_blob="0"*40),
    lambda d:d["changes"][0].update(independent_acceptance=True),
    lambda d:d["changes"][0].update(finding="R1"),
    lambda d:d["known_unresolved"].pop(),
    lambda d:d["known_unresolved"][0].update(must_remain_red=False),
    lambda d:d["known_unresolved"][1].update(classification="Q_LIBRARY_PROVEN"),
    lambda d:d["ci"].update(full_conclusion="SUCCESS"),
    lambda d:d["ci"].update(full_failed=0),
    lambda d:d["ci"].update(scoped_passed=55),
    lambda d:d["ci"].update(independent_acceptance=True),
    lambda d:d["ci"].update(no_promoting_inference=False),
    lambda d:d["synthetic_execution"].update(status="KNOWN_TRUTH_QUALIFIED"),
    lambda d:d["target_science"].update(target_winner="C3"),
    lambda d:d["target_science"].update(real_training_authorized=True),
    lambda d:d["target_science"].update(teacher_guard="SECOND_PREDICTOR"),
    lambda d:d.update(review_actions=[]),
])
def test_forged_promotion_or_erased_failure_is_rejected(tamper):
    d=deepcopy(original())
    tamper(d)
    with pytest.raises(ValueError, match="G7_E3_AUDIT_NONPROMOTION_REFUSAL"):
        validate(d)

def test_record_does_not_reinterpret_synthetic_fixture_as_real_biology():
    d=original()
    assert d["synthetic_execution"]["source_fixture_pr"] == 328
    assert d["synthetic_execution"]["interop_pr"] == 469
    assert d["synthetic_execution"]["status"] == "NOT_FULL_KNOWN_TRUTH_QUALIFIED"
    assert d["target_science"]["historical_replay_pr"] == 314
