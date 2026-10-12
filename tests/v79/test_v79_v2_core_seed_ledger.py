from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "v79"
sys.path.insert(0, str(HERE))

import v79_v2_core_seed_ledger as S  # noqa: E402


def _contract():
    return json.loads((ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json").read_text(encoding="utf-8"))


def _root_manifest():
    return json.loads((ROOT / "results/v79/v2_core_realization_audit_freeze_v1/package/V79_V2_CORE_WORLD_SET_MANIFEST_V1.json").read_text(encoding="utf-8"))


def _index():
    return json.loads((ROOT / "results/v79/v2_core_realization_audit_freeze_v1/package/blinded_fit_inputs/V79_V2_CORE_BLINDED_FIT_INDEX_V1.json").read_text(encoding="utf-8"))


def test_seed_ledger_is_opaque_and_covers_all_1056_fits():
    ledger = S.build_seed_ledger(_contract(), _root_manifest(), _index())
    assert len(ledger) == 1056
    assert len({x["fit_id"] for x in ledger}) == 1056
    text = json.dumps(ledger)
    for forbidden in ("Q00", "Q11", "world_index", "world_name", "truth"):
        assert forbidden not in text
    assert all(isinstance(x["primary_seed"], int) and 0 <= x["primary_seed"] <= 0xffffffff for x in ledger)


def test_seeds_match_frozen_world_index_scheme_without_exposing_index():
    c = _contract(); rm = _root_manifest(); idx = _index()
    ledger = S.build_seed_ledger(c, rm, idx)
    by_fit = {x["fit_id"]: x for x in ledger}
    first = rm["worlds"][0]
    rec = next(x for x in idx["worlds"] if x["opaque_world_id"] == first["opaque_world_id"])
    det = S.expected_fit_entry(c, world_index=0, opaque_world_id=first["opaque_world_id"], manifest_sha=rec["manifest_sha256"], gene_index=0, part="detection")
    pos = S.expected_fit_entry(c, world_index=0, opaque_world_id=first["opaque_world_id"], manifest_sha=rec["manifest_sha256"], gene_index=0, part="positive")
    assert by_fit[det["fit_id"]] == det
    assert by_fit[pos["fit_id"]] == pos
