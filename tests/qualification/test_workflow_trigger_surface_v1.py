from pathlib import Path


WORKFLOW = Path('.github/workflows/shared-qualification-interface-v1.yml')


def test_shared_interface_workflow_retriggers_on_governance_contract_changes():
    text = WORKFLOW.read_text(encoding='utf-8')
    assert "'tests/governance/**'" in text
    assert "'docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json'" in text
