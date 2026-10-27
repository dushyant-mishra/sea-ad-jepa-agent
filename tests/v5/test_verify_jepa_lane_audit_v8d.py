"""Hostile static mutations for the append-only V8d review delta."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts.v5.verify_jepa_lane_audit_v8d import MACHINE, validate

ROOT=Path(__file__).resolve().parents[2]

def src():
    return json.loads((ROOT/MACHINE).read_text(encoding="utf-8"))

def test_exact_v8d_passes_without_source_promotion():
    validate(src(),ROOT)

@pytest.mark.parametrize("mut",[
    lambda a:a.update(authority="TARGET_WINNER_SELECTED"),
    lambda a:a.update(stage4_authorized=True),
    lambda a:a.update(training_authorized=True),
    lambda a:a.update(source_authenticated_biology=True),
    lambda a:a.update(append_only=False),
    lambda a:a.update(prior_audit_head="0"*40),
    lambda a:a.update(snapshots_frozen=["V8d"]),
    lambda a:a["live_ledger"][0].update(head="0"*40),
    lambda a:a["live_ledger"][0].update(status="BIOLOGICAL_E2G_PASS"),
    lambda a:a["live_ledger"][0].update(evidence="Source fully authenticated"),
    lambda a:a["live_ledger"][0].update(caveats="No concerns"),
    lambda a:a["live_ledger"][1].update(status="13_HOSTILE_RED_ACCEPTED"),
    lambda a:a["live_ledger"][6].update(status="CUMULATIVE_TASK1_ACCEPTED"),
    lambda a:a["live_ledger"][7].update(status="ALL_13_RED_REPAIRED"),
    lambda a:a["live_ledger"][7]["ci"][1].update(conclusion="success"),
    lambda a:a["live_ledger"][7]["ci"][0].update(run=123),
    lambda a:a.update(material_source_limitations=[]),
    lambda a:a.update(audit_rounds=[]),
])
def test_unearned_promotions_and_forged_exact_receipts_refused(mut):
    a=deepcopy(src())
    mut(a)
    with pytest.raises(ValueError):
        validate(a,ROOT)

def test_old_v8c_and_v8a_remain_indexed():
    a=src()
    assert a["snapshots_frozen"] == ["V8","V8a","V8b","V8c"]
    assert a["prior_audit_head"] == "1a6e59d338906fa9da1cbbc4b93c918349a4a3c5"
