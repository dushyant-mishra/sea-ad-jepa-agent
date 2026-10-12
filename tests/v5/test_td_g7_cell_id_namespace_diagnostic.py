"""Decision-rule tests for the read-only cell-ID namespace diagnostic, on synthetic identifiers only."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5" / "diagnose_td_g7_cell_id_namespace.py"
SPEC = ROOT / "docs" / "agent" / "TD_G7_CELL_ID_NAMESPACE_DIAGNOSTIC_20261012" / "STAGE3_TRANSFORM_SPEC.json"
spec_ = importlib.util.spec_from_file_location("idns_diag", SCRIPT)
D = importlib.util.module_from_spec(spec_)
spec_.loader.exec_module(D)


def ns(sample: dict, s174: dict, join: dict) -> dict:
    return {"sample": sample, "s174": {k: {"ids": v} for k, v in s174.items()}, "join": join,
            "study": {m: "SEA_AD" for m in sample}}


def run(n):
    return D.classify({name: D.evaluate_transform(name, n) for name in D.TRANSFORMS})


def test_spec_names_exactly_the_registered_transforms():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    assert [t["name"] for t in spec["transforms"]] == list(D.TRANSFORMS)
    assert set(D.CAN_ESTABLISH) | set(D.BLOCKS_DISJOINTNESS) | {"IDENTITY", "BARCODE_ONLY"} == set(D.TRANSFORMS)


def test_disjoint_namespaces_classify_as_genuinely_disjoint():
    n = ns({"m1": ["AAAA-L1_W1-100", "CCCC-L1_W1-100"]}, {"s1": ["GGGG-L1_W2-101", "TTTT-L2_W1-102"]}, {"m1": "s1"})
    assert run(n) == "GENUINELY_DISJOINT_NATURAL_CELL_SETS"


def test_barcode_only_chance_reuse_never_changes_the_classification():
    n = ns({"m1": ["AAAA-L1_W1-100"]}, {"s1": ["AAAA-L9_W9-999"]}, {"m1": "s1"})
    r = D.evaluate_transform("BARCODE_ONLY", n)
    assert r["global_overlap"] == 1
    assert run(n) == "GENUINELY_DISJOINT_NATURAL_CELL_SETS"


def test_case_only_difference_is_a_namespace_mismatch():
    n = ns({"m1": ["AAAA-L1_W1-100"]}, {"s1": ["aaaa-l1_w1-100"]}, {"m1": "s1"})
    assert run(n) == "IDENTIFIER_NAMESPACE_MISMATCH"


def test_a_colliding_lossless_transform_cannot_establish_overlap():
    n = ns({"m1": ["AAAA-L1_W1-100", "aaaa-l1_w1-100"]}, {"s1": ["Aaaa-L1_w1-100"]}, {"m1": "s1"})
    r = D.evaluate_transform("UPPERCASE", n)
    assert r["collision_free_both_sides"] is False and r["global_overlap"] == 1
    assert run(n) != "IDENTIFIER_NAMESPACE_MISMATCH"


def test_same_barcode_and_chip_well_with_a_different_trailing_field_is_not_estimable():
    n = ns({"m1": ["AAAA-L1_W1-100"]}, {"s1": ["AAAA-L1_W1-555"]}, {"m1": "s1"})
    assert run(n) == "ID_NAMESPACE_DIAGNOSTIC_NOT_ESTIMABLE"


def test_script_reads_no_values():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "counts.npz" not in text and "import h5py" not in text and "G6_VALUES" not in text
    assert 'usecols=["sample", "source", "matrix_id", "cell_id"]' in text
