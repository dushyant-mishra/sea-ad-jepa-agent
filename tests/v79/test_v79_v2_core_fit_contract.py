from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "v79"
sys.path.insert(0, str(HERE))

import prepare_v79_v2_core_engineering_benchmark as P  # noqa: E402
import v79_v2_core_fit_contract as FC  # noqa: E402


def _contract():
    return json.loads((ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json").read_text(encoding="utf-8"))


def test_fit_contract_projection_is_identity_blind_and_contract_derived(tmp_path):
    c = _contract(); view = P.build_fit_contract_view(c)
    FC.validate_fit_contract_view(view)
    assert view["source_contract_sha256"] == FC.SOURCE_CONTRACT_SHA256
    assert view["resources"]["qualification_world_count"] == 12
    assert view["resources"]["estimate"]["n_fits"] == 1056
    assert view["resources"]["xla_host_devices"] == view["inference"]["chains"] == 4
    raw = FC.canonical_bytes(view)
    text = raw.decode("utf-8")
    for forbidden in ("Q00_BASELINE", "Q11_OMITTED_OPERATOR", '"world_name"', '"world_index"', '"gates"'):
        assert forbidden not in text
    p = tmp_path / "fit_view.json"; p.write_bytes(raw)
    assert FC.load_fit_contract_view(p, expected_sha256=FC.view_sha256(view)) == view


def test_fit_contract_tamper_is_refused():
    view = P.build_fit_contract_view(_contract())
    bad = json.loads(json.dumps(view)); bad["world_name"] = "Q00_BASELINE"
    with pytest.raises(FC.FitContractRefused):
        FC.validate_fit_contract_view(bad)
    bad = json.loads(json.dumps(view)); bad["source_contract_sha256"] = "0" * 64
    with pytest.raises(FC.FitContractRefused):
        FC.validate_fit_contract_view(bad)
