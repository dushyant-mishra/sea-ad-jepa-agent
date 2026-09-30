from __future__ import annotations
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
AUDITED_CLAUDE_SHA="0d3874cb198f0fdeddff5a41777e3e0e9d0db5ab"
EXECUTOR_PATH="scripts/v64/nihcard_stage3_phase_a_exact_executor_v2.py"

def _audited_executor_source()->str:
    return subprocess.check_output(
        ["git","show",f"{AUDITED_CLAUDE_SHA}:{EXECUTOR_PATH}"],
        cwd=ROOT,text=True
    )

def test_sampler_and_exact_control_selection_are_accepted_but_full_phase_a_is_not():
    p=json.loads((ROOT/"results/v64/V64_PHASE_A_EXACT_INDEPENDENT_AUDIT_V1.json").read_text())
    assert p["sampler_qualification"]["status"]=="QUALIFIED"
    assert p["exact_control_selection"]["CONTROL_A_success"]==13510
    assert p["exact_control_selection"]["CONTROL_B_success_A_failure_not_rescued"]==2271
    assert p["full_phase_A_contract_gap"]["status"]=="BLOCKING"
    assert p["feature_artifact_and_provenance_gap"]["status"]=="BLOCKING"
    assert p["governance"]["phase_B"]=="STOPPED"

def test_audited_executor_is_missing_frozen_linked_side_funnel_stages():
    contract=json.loads((ROOT/"results/v64/V64_NIH_CARD_STAGE3_PHASE_A_SUCCESSOR_CONTRACT_V2.json").read_text())
    src=_audited_executor_source()
    required=set(contract["funnel_reporting"]["primary_drop_reasons"])
    expected_linked={
        "DROP_GENE_NOT_IN_NIHCARD",
        "DROP_GENE_AMBIGUOUS_IN_NIHCARD",
        "DROP_NO_CONSENSUS_PEAK_OVER_LINKED_DISTAL",
    }
    assert expected_linked <= required
    assert "DROP_GENE_NOT_IN_NIHCARD" not in src
    assert "DROP_GENE_AMBIGUOUS_IN_NIHCARD" not in src
    assert "DROP_NO_CONSENSUS_PEAK_OVER_LINKED_DISTAL" not in src
    assert 'retained = bool(draws["A"].get("ok"))' in src

def test_audited_rows_do_not_implement_full_v2_feature_schema():
    schema=json.loads((ROOT/"results/v64/V64_NIH_CARD_STAGE3_FEATURE_ARTIFACT_CONTRACT_V2.json").read_text())
    src=_audited_executor_source()
    for field in ["promoter_key","promoter_index","pair_key","promoter_degree","re_density","anchor_frequency"]:
        assert field in schema["required_structural_fields"]
        assert f'"{field}"' not in src and f"'{field}'" not in src

def test_prior_acceptance_is_explicitly_retracted():
    p=json.loads((ROOT/"results/v64/V64_PHASE_A_EXACT_INDEPENDENT_AUDIT_V1.json").read_text())
    assert p["retraction"]["status"]=="RETRACTED"
    assert p["verdict"]=="EXACT_CONTROL_SELECTION_ACCEPTED_AT_13510__FULL_PHASE_A_NOT_CONTRACT_COMPLIANT"

def test_singleton_contract_remains_frozen():
    t=(ROOT/"docs/agent/V64_DOWNSTREAM_CONTROL_RANDOMNESS_STRATA_CONTRACT_20260930.md").read_text()
    assert "FORCED_SINGLETON_SUPPORT_1" in t
    assert "not described as randomized" in t
    assert "before Phase B" in t
