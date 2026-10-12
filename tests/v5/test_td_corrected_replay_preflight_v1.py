import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

from td_corrected_replay_contract_v1 import load_contract  # noqa: E402
from td_corrected_replay_preflight_v1 import (  # noqa: E402
    PreflightError,
    PreflightInputs,
    authenticate_predecessors,
)

CONTRACT = ROOT / "target_discovery" / "iterations" / "corrected_replay_20261012" / "TD_CORRECTED_REPLAY_CONTRACT_V1.json"


def _inputs(tmp_path: Path) -> PreflightInputs:
    files = {
        "g6_acceptance": b"accepted-g6",
        "g6_receipt": b'{"terminal":"PASS_TD_G6_SOURCE_LIBRARY_EXACT"}',
        "g7_marker": b'{"started":true}',
        "g7_receipt": json.dumps({
            "terminal": "NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP",
            "spent_authority": True,
            "g7_execution_authorized": False,
            "biological_replay_authorized": False,
        }).encode(),
        "diagnostic": json.dumps({
            "classification": "GENUINELY_DISJOINT_NATURAL_CELL_SETS",
            "claims_value_agreement": False,
            "biological_replay_authorized": False,
        }).encode(),
    }
    paths = {}
    for name, data in files.items():
        p = tmp_path / f"{name}.json"
        p.write_bytes(data)
        paths[name] = p
    return PreflightInputs(
        g6_acceptance=paths["g6_acceptance"],
        g6_receipt=paths["g6_receipt"],
        g7_marker=paths["g7_marker"],
        g7_receipt=paths["g7_receipt"],
        diagnostic=paths["diagnostic"],
        diagnostic_commit="0b50938e48f7c257b362a0c66899bc1caa0d27a1",
    )


def _hash_stub(path: Path) -> str:
    mapping = {
        "g6_acceptance.json": "89932183a2c7b56d1e3ae42264ea3f3b3ae9001d865cfa93604b46f0db2129fb",
        "g6_receipt.json": "2edaa2d2e03b8d862172e97b35fb94888305ef0e843cd71206ee56f53b28a52b",
        "g7_marker.json": "2579b9a6a5cbfc89f4dd38082515a290681fc5413afeb95536b62bbfd46f2667",
        "g7_receipt.json": "47f9be6e8fef3fa70c07fbe8011fa1360df72e26b8259fc9655a369768a97fcf",
    }
    return mapping[path.name]


def test_authenticate_exact_predecessors(tmp_path, monkeypatch):
    contract = load_contract(CONTRACT)
    monkeypatch.setattr("td_corrected_replay_preflight_v1._sha256_path", _hash_stub)
    receipt = authenticate_predecessors(contract, _inputs(tmp_path))
    assert receipt["technical_prerequisite_closed"] is True
    assert receipt["g7_pass"] is False
    assert receipt["g7_terminal"] == "NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP"
    assert receipt["closure_reason"] == "G7_NOT_ESTIMABLE__GENUINELY_DISJOINT_NATURAL_CELL_SETS"
    assert receipt["biological_replay_authorized"] is False


def test_reject_wrong_g6_receipt_hash(tmp_path, monkeypatch):
    contract = load_contract(CONTRACT)
    def bad(path):
        if path.name == "g6_receipt.json":
            return "0" * 64
        return _hash_stub(path)
    monkeypatch.setattr("td_corrected_replay_preflight_v1._sha256_path", bad)
    with pytest.raises(PreflightError, match="G6 receipt"):
        authenticate_predecessors(contract, _inputs(tmp_path))


def test_reject_g7_pass_relabel(tmp_path, monkeypatch):
    contract = load_contract(CONTRACT)
    inputs = _inputs(tmp_path)
    data = json.loads(inputs.g7_receipt.read_text())
    data["terminal"] = "PASS_TD_G7_S174_EXACT_OVERLAP"
    inputs.g7_receipt.write_text(json.dumps(data))
    monkeypatch.setattr("td_corrected_replay_preflight_v1._sha256_path", _hash_stub)
    with pytest.raises(PreflightError, match="G7 terminal"):
        authenticate_predecessors(contract, inputs)


def test_reject_wrong_diagnostic_commit_or_classification(tmp_path, monkeypatch):
    contract = load_contract(CONTRACT)
    monkeypatch.setattr("td_corrected_replay_preflight_v1._sha256_path", _hash_stub)
    inputs = _inputs(tmp_path)
    inputs = PreflightInputs(**{**inputs.__dict__, "diagnostic_commit": "deadbeef"})
    with pytest.raises(PreflightError, match="diagnostic commit"):
        authenticate_predecessors(contract, inputs)
    inputs = _inputs(tmp_path)
    data = json.loads(inputs.diagnostic.read_text())
    data["classification"] = "AMBIGUOUS_NAMESPACE"
    inputs.diagnostic.write_text(json.dumps(data))
    with pytest.raises(PreflightError, match="diagnostic classification"):
        authenticate_predecessors(contract, inputs)


def test_reject_unspent_g7_or_diagnostic_value_claim(tmp_path, monkeypatch):
    contract = load_contract(CONTRACT)
    monkeypatch.setattr("td_corrected_replay_preflight_v1._sha256_path", _hash_stub)
    inputs = _inputs(tmp_path)
    g7 = json.loads(inputs.g7_receipt.read_text())
    g7["spent_authority"] = False
    inputs.g7_receipt.write_text(json.dumps(g7))
    with pytest.raises(PreflightError, match="spent authority"):
        authenticate_predecessors(contract, inputs)
    inputs = _inputs(tmp_path)
    diag = json.loads(inputs.diagnostic.read_text())
    diag["claims_value_agreement"] = True
    inputs.diagnostic.write_text(json.dumps(diag))
    with pytest.raises(PreflightError, match="value agreement"):
        authenticate_predecessors(contract, inputs)
