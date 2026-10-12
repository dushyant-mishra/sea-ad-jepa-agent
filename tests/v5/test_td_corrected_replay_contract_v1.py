import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

from td_corrected_replay_contract_v1 import (  # noqa: E402
    ContractError,
    load_contract,
    validate_contract,
)

CONTRACT = ROOT / "target_discovery" / "iterations" / "corrected_replay_20261012" / "TD_CORRECTED_REPLAY_CONTRACT_V1.json"


def test_frozen_contract_exact_lineage_and_authority(monkeypatch):
    contract = load_contract(CONTRACT)
    # Repository file hashing is integration-qualified later; unit test pins identity map.
    monkeypatch.setattr("td_corrected_replay_contract_v1._sha256_path", lambda path: {
        "td57b_fixed_relational_recurrence.py": "1654011ca1aeb20dab8e707b229ec3de00106b937ed49b33b2432b789d8c4e0e",
        "td59_replay_closure_executor_v1.py": "870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085",
    }[path.name])
    out = validate_contract(contract, ROOT)
    assert out["schema"] == "JEPA_TD_CORRECTED_REPLAY_CONTRACT_V1"
    assert out["predecessors"]["g6"]["producer_commit"] == "ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0"
    assert out["predecessors"]["g7"]["implementation_commit"] == "8d41fb9838b425ddcb704ecbdf5cd51f3eeb9f27"
    assert out["predecessors"]["g7"]["terminal"] == "NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP"
    assert out["predecessors"]["diagnostic"]["commit"] == "0b50938e48f7c257b362a0c66899bc1caa0d27a1"
    assert out["predecessors"]["diagnostic"]["classification"] == "GENUINELY_DISJOINT_NATURAL_CELL_SETS"
    assert [x["id"] for x in out["stages"]] == ["TD56", "TD57B", "TD57C", "TD59"]
    assert out["executors"]["TD57B"]["sha256"] == "1654011ca1aeb20dab8e707b229ec3de00106b937ed49b33b2432b789d8c4e0e"
    assert out["executors"]["TD57C"]["sha256"] == "530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c"
    assert out["executors"]["TD59"]["sha256"] == "870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085"
    assert len(out["executors"]["TD56"]["selected_artifacts"]) == 3
    assert all(v is False for v in out["downstream_authority"].values())


def test_rejects_g7_not_estimable_relabel_to_pass():
    contract = load_contract(CONTRACT)
    mutated = copy.deepcopy(contract)
    mutated["predecessors"]["g7"]["terminal"] = "PASS_TD_G7_S174_EXACT_OVERLAP"
    with pytest.raises(ContractError, match="G7 terminal"):
        validate_contract(mutated, ROOT)


def test_rejects_wrong_stage_order():
    contract = load_contract(CONTRACT)
    mutated = copy.deepcopy(contract)
    mutated["stages"][1], mutated["stages"][2] = mutated["stages"][2], mutated["stages"][1]
    with pytest.raises(ContractError, match="stage order"):
        validate_contract(mutated, ROOT)


def test_rejects_any_true_downstream_authority():
    contract = load_contract(CONTRACT)
    mutated = copy.deepcopy(contract)
    mutated["downstream_authority"]["training_authorized"] = True
    with pytest.raises(ContractError, match="downstream authority"):
        validate_contract(mutated, ROOT)


def test_rejects_ambiguous_td56_selection():
    contract = load_contract(CONTRACT)
    mutated = copy.deepcopy(contract)
    mutated["executors"]["TD56"]["selected_artifacts"].append(
        {"source": "HVS", "artifact_id": "alternate", "sha256": "0" * 64, "storage": "external_frozen_artifact"}
    )
    with pytest.raises(ContractError, match="TD56"):
        validate_contract(mutated, ROOT)
