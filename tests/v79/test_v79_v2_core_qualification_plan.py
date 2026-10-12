from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "scripts" / "v79"
sys.path.insert(0, str(HERE))
import v79_v2_core_qualification_plan as Q  # noqa: E402


def _contract():
    p = Path(__file__).resolve().parents[2] / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _index():
    return {"world_count":12,"worlds":[{"opaque_world_id":f"{i:012x}","manifest_sha256":f"{i+1:064x}"} for i in range(12)]}


def test_queue_reproduces_contract_fit_count_and_is_opaque():
    q = Q.build_qualification_queue(_contract(), _index())
    assert len(q) == 1056
    assert {x["part"] for x in q} == {"detection","positive"}
    assert min(x["gene_index"] for x in q) == 0 and max(x["gene_index"] for x in q) == 43
    text = json.dumps(q)
    assert "Q00" not in text and "Q11" not in text and "world_name" not in text


def test_queue_is_deterministic_and_fit_ids_bind_manifest():
    a = Q.build_qualification_queue(_contract(), _index())
    b = Q.build_qualification_queue(_contract(), _index())
    assert a == b
    assert len({x["fit_id"] for x in a}) == len(a)


def test_qualification_requires_distinct_controller_authorization():
    with pytest.raises(Q.QualificationPlanRefused):
        Q.require_qualification_execution_authority(None, expected_contract_sha="a"*64, expected_blinded_index_sha="b"*64)
    with pytest.raises(Q.QualificationPlanRefused):
        Q.require_qualification_execution_authority({"schema":"V79_V2_CORE_WORLD_REALIZATION_AUTHORIZATION_V1"}, expected_contract_sha="a"*64, expected_blinded_index_sha="b"*64)
