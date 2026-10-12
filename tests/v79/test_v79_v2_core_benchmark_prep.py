from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "v79"
sys.path.insert(0, str(HERE))

import prepare_v79_v2_core_engineering_benchmark as P  # noqa: E402


def _contract():
    return json.loads((ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json").read_text(encoding="utf-8"))


def test_engineering_selection_depends_only_on_opaque_order_not_q_mapping():
    c = _contract()
    blinded = {"worlds":[
        {"opaque_world_id":"ffffffffffff","manifest_sha256":"f"*64},
        {"opaque_world_id":"000000000001","manifest_sha256":"a"*64},
    ]}
    # Deliberately associate the lexically first opaque ID with a different scientific label/index than list order.
    root = {"worlds":[
        {"world_name":"Q11_OMITTED_OPERATOR","world_index":11,"opaque_world_id":"000000000001"},
        {"world_name":"Q00_BASELINE","world_index":0,"opaque_world_id":"ffffffffffff"},
    ]}
    oid, msha, ledger = P._selected_world_and_seed_ledger(c, root, blinded)
    assert oid == "000000000001" and msha == "a"*64
    assert len(ledger) == 4 and len({x["fit_id"] for x in ledger}) == 4
    serialized = json.dumps(ledger)
    assert "Q00" not in serialized and "Q11" not in serialized
    assert "world_index" not in serialized and "world_name" not in serialized


def test_fit_contract_projection_keeps_benchmark_scope_and_no_world_labels():
    view = P.build_fit_contract_view(_contract())
    assert "2 genes x 2 parts" in view["resources"]["engineering_benchmark"]
    assert view["resources"]["qualification_world_count"] == 12
    text = json.dumps(view)
    assert "Q00_BASELINE" not in text and "Q11_OMITTED_OPERATOR" not in text
