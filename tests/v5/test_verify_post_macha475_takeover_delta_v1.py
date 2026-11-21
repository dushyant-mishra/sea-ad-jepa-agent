"""Hostile source-drift and nonpromotion mutations of Macha475 evidence."""
from copy import deepcopy
import json

import pytest

from scripts.v5.verify_post_macha475_takeover_delta_v1 import (
    ROOT, DELTA, MACHA, BLOBS, validate_root, verify,
)

def sources():
    d=json.loads((ROOT/DELTA).read_text())
    m=json.loads((ROOT/MACHA).read_text())
    return [d,m,dict(BLOBS)]

def test_original_review_exact_source_and_new_scope_validate():
    validate_root()

@pytest.mark.parametrize("attack",[
    lambda a:a[0].update(authority="TRAIN_ON"),
    lambda a:a[0].update(record_kind="INDEPENDENT_REAL_G7_PASS"),
    lambda a:a[1]["verdicts"][0].update(verdict="ACCEPT"),
    lambda a:a[2].update({"docs/agent/JEPA_MACHA_REVIEW_AND_READINESS_DELTA_20261027.md":"f"*40}),
    lambda a:a[0]["macha_review"]["original_verdicts"].update({"470":"ACCEPT"}),
    lambda a:a[0]["chatgpt_repairs"][0].update(targeted_passed=71),
    lambda a:a[0]["chatgpt_repairs"][0].update(original_11_external_trust_red_preserved=False),
    lambda a:a[0]["chatgpt_repairs"][0].update(full_g7_authorized=True),
    lambda a:a[0]["chatgpt_repairs"][0].update(independently_accepted=True),
    lambda a:a[0]["chatgpt_repairs"][1].update(original_T2D_red_preserved=False),
    lambda a:a[0]["chatgpt_repairs"][1].update(ps_task12_cumulative_authorized=True),
    lambda a:a[0]["independent_review"].update(externally_authenticated=True),
    lambda a:a[0]["independent_review"].update(real_g7_authorized=True),
    lambda a:a[0]["independent_review"].update(total_hostile_and_original_passed=200),
    lambda a:a[0]["independent_review"].update(counterexample_limits=[]),
    lambda a:a[0]["existing_biological_results_preserved"].update(candidate_C2="WINNER"),
    lambda a:a[0]["existing_biological_results_preserved"].update(production_synthetic_task4_biology_generator="READY"),
    lambda a:a[0]["privacy_firewall"].update(values_preserved_or_repeated=True),
])
def test_promotion_or_original_source_forgery_refused(attack):
    state=deepcopy(sources())
    attack(state)
    with pytest.raises(ValueError,match="POST_MACHA475_AUDIT_NONPROMOTION_REFUSAL"):
        verify(*state)
