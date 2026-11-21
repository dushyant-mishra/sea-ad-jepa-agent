"""Hostile mutation tests for archival PR480 independent Task3 RED custody."""
from copy import deepcopy
import json

import pytest

from scripts.v5.verify_ps_task3_chatgpt_review_20261028 import (
    ROOT, DATA, PROBE_BLOB, REPORT_BLOB, validate_root, verify,
)

def original():
    return json.loads((ROOT/DATA).read_text())

def test_original_source_bound_independent_red():
    validate_root()

@pytest.mark.parametrize("tamper", [
    lambda x: x.update(authority="REAL_TRAINING_AUTHORIZED"),
    lambda x: x.update(kind="CALIBRATION_ISSUER_ACCEPTED"),
    lambda x: x.update(source_unchanged=False),
    lambda x: x.update(source_git_blob="f"*40),
    lambda x: x.update(verdict="ACCEPT_REAL_CALIBRATION"),
    lambda x: x["findings"].pop(),
    lambda x: x["findings"][0].update(real_data_executed=True),
    lambda x: x["ci"].update(review_hostile_failed=0),
    lambda x: x["ci"].update(review_expected_red_conclusion="SUCCESS_ALL_TESTS_PASS"),
    lambda x: x["ci"].update(original_macha_unchanged_tests_passed=0),
    lambda x: x["ci"].update(full_task3_conclusion="SUCCESS"),
    lambda x: x["ci"].update(full_task3_failed=0),
    lambda x: x.update(external_blockers=[]),
])
def test_tampered_evidence_cannot_grant_authority(tamper):
    d=deepcopy(original())
    tamper(d)
    with pytest.raises(ValueError, match="PS_TASK3_INDEPENDENT_REVIEW_NONPROMOTION_REFUSAL"):
        verify(d, PROBE_BLOB, REPORT_BLOB)

def test_mutated_blob_identity_is_refused():
    d=original()
    with pytest.raises(ValueError, match="PS_TASK3_INDEPENDENT_REVIEW_NONPROMOTION_REFUSAL"):
        verify(d, "0"*40, REPORT_BLOB)
    with pytest.raises(ValueError, match="PS_TASK3_INDEPENDENT_REVIEW_NONPROMOTION_REFUSAL"):
        verify(d, PROBE_BLOB, "0"*40)
