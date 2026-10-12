import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

from td_corrected_replay_contract_v1 import load_contract  # noqa: E402
from td_corrected_replay_qualify_v1 import (  # noqa: E402
    QualificationError,
    QualificationInputs,
    qualify_replay,
)

CONTRACT = ROOT / "target_discovery" / "iterations" / "corrected_replay_20261012" / "TD_CORRECTED_REPLAY_CONTRACT_V1.json"


def _pred():
    return {
        "schema": "JEPA_TD_CORRECTED_REPLAY_PREFLIGHT_RECEIPT_V1",
        "technical_prerequisite_closed": True,
        "g7_pass": False,
        "g7_terminal": "NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP",
        "diagnostic_classification": "GENUINELY_DISJOINT_NATURAL_CELL_SETS",
        "closure_reason": "G7_NOT_ESTIMABLE__GENUINELY_DISJOINT_NATURAL_CELL_SETS",
        "biological_replay_authorized": False,
    }


def _inputs(tmp_path: Path):
    names = {
        "TD56:HVS": "td56_hvs.py",
        "TD56:NPH52": "td56_nph52.py",
        "TD56:SEA_AD": "td56_seaad.py",
        "TD57C": "td57c.py",
    }
    external = {}
    for key, name in names.items():
        p = tmp_path / name
        p.write_text("# frozen executor\n")
        external[key] = p
    return QualificationInputs(
        external_executors=external,
        comparison_population_n={"TD56": 92, "TD57B": 92, "TD57C": 17, "TD59": 29},
        namespace_probe=tmp_path / "future_namespace",
    )


def _external_hash(path: Path):
    return {
        "td56_hvs.py": "a1ea8653e24213a3b14ccc52ea64011c92553aec4df5edb7b55d6ba309f61b43",
        "td56_nph52.py": "a1ea8653e24213a3b14ccc52ea64011c92553aec4df5edb7b55d6ba309f61b43",
        "td56_seaad.py": "c77ceac26f0ff4c3ae7a3955c39218af56339adda0225b9c663c9d92710c8866",
        "td57c.py": "530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c",
    }[path.name]


def test_qualify_exact_four_stages_without_side_effects(tmp_path, monkeypatch):
    contract = load_contract(CONTRACT)
    monkeypatch.setattr("td_corrected_replay_qualify_v1.validate_contract", lambda c, r: c)
    monkeypatch.setattr("td_corrected_replay_qualify_v1._sha256_path", _external_hash)
    inputs = _inputs(tmp_path)
    receipt = qualify_replay(contract, _pred(), ROOT, inputs)
    assert [x["id"] for x in receipt["stages"]] == ["TD56", "TD57B", "TD57C", "TD59"]
    assert receipt["terminal"] == "PASS_TD_CORRECTED_REPLAY_TURNKEY_QUALIFICATION__NO_BIOLOGICAL_REPLAY_RUN__LAUNCH_AUDIT_REQUIRED"
    assert receipt["biological_replay_run"] is False
    assert receipt["start_marker_created"] is False
    assert not inputs.namespace_probe.exists()


def test_reject_altered_external_executor(tmp_path, monkeypatch):
    contract = load_contract(CONTRACT)
    monkeypatch.setattr("td_corrected_replay_qualify_v1.validate_contract", lambda c, r: c)
    def bad(path):
        if path.name == "td57c.py":
            return "0" * 64
        return _external_hash(path)
    monkeypatch.setattr("td_corrected_replay_qualify_v1._sha256_path", bad)
    with pytest.raises(QualificationError, match="TD57C"):
        qualify_replay(contract, _pred(), ROOT, _inputs(tmp_path))


def test_reject_missing_or_zero_comparison_population(tmp_path, monkeypatch):
    contract = load_contract(CONTRACT)
    monkeypatch.setattr("td_corrected_replay_qualify_v1.validate_contract", lambda c, r: c)
    monkeypatch.setattr("td_corrected_replay_qualify_v1._sha256_path", _external_hash)
    inputs = _inputs(tmp_path)
    bad = QualificationInputs(inputs.external_executors, {"TD56": 1, "TD57B": 1, "TD57C": 1}, inputs.namespace_probe)
    with pytest.raises(QualificationError, match="comparison_population_n"):
        qualify_replay(contract, _pred(), ROOT, bad)
    bad2 = QualificationInputs(inputs.external_executors, {"TD56": 1, "TD57B": 1, "TD57C": 0, "TD59": 1}, inputs.namespace_probe)
    with pytest.raises(QualificationError, match="zero comparison population"):
        qualify_replay(contract, _pred(), ROOT, bad2)


def test_reject_bad_predecessor_receipt_or_existing_namespace(tmp_path, monkeypatch):
    contract = load_contract(CONTRACT)
    monkeypatch.setattr("td_corrected_replay_qualify_v1.validate_contract", lambda c, r: c)
    monkeypatch.setattr("td_corrected_replay_qualify_v1._sha256_path", _external_hash)
    pred = _pred()
    pred["g7_pass"] = True
    with pytest.raises(QualificationError, match="G7 PASS"):
        qualify_replay(contract, pred, ROOT, _inputs(tmp_path))
    inputs = _inputs(tmp_path)
    inputs.namespace_probe.mkdir()
    with pytest.raises(QualificationError, match="namespace"):
        qualify_replay(contract, _pred(), ROOT, inputs)
