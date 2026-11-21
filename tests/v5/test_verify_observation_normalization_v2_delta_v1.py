"""Hostile static audit mutation tests: no source drift, false issuer, erased blockers."""
from copy import deepcopy
import json
from pathlib import Path

import pytest
from scripts.v5.verify_observation_normalization_v2_delta_v1 import ROOT, DATA, verify

def original():
    return json.loads((ROOT/DATA).read_text())

def test_original_exact_v2_hosted_audit_receipt():
    verify(original())

@pytest.mark.parametrize("tamper",[
    lambda d:d.update(standing_authority="REAL_TRAINING_APPROVED"),
    lambda d:d.update(classification="INDEPENDENT_BIOLOGICAL_TARGET_PASS"),
    lambda d:d["source_work"].update(head="f"*40),
    lambda d:d["source_work"].update(original_producer_unchanged=False),
    lambda d:d["source_work"]["new_files"][0].update(git_blob="f"*40),
    lambda d:d["mechanics"].update(legacy_library_size_field_reused=True),
    lambda d:d["mechanics"].update(original_g7_modified=True),
    lambda d:d["mechanics"].update(real_issuer_authenticated=True),
    lambda d:d["mechanics"].update(independent_scientific_acceptance=True),
    lambda d:d["mechanics"].update(unaccounted_source_mass="PASS"),
    lambda d:d["run_receipts"].update(initial_red_run=0),
    lambda d:d["run_receipts"].update(total_tests_passed=400),
    lambda d:d["run_receipts"].update(g7_cross_head_executed=True),
    lambda d:d["upstream_blockers"].update(g7_R1_R1D_R2="PASS"),
    lambda d:d["upstream_blockers"].update(ps_T2D="PASS"),
    lambda d:d["upstream_blockers"].update(ps_task4_biological_generator="READY"),
    lambda d:d["upstream_blockers"].update(cross_head_g7_v2="PASS"),
])
def test_forged_acceptance_or_erased_red_is_refused(tamper):
    d=deepcopy(original())
    tamper(d)
    with pytest.raises(ValueError,match="V2_NORMALIZATION_AUDIT_NONPROMOTION_REFUSAL"):
        verify(d)
