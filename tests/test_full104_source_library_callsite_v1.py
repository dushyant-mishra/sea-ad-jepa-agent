import csv
import importlib.util
from pathlib import Path

P = Path(__file__).resolve().parents[0] / "test_bind_full104_expression_blocks_v4.py"
spec = importlib.util.spec_from_file_location("full104_bind_fixture", P)
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)


def _rewrite_library_text(root, bm, audit, value):
    mp = root / "blocks/op00/block-00000.meta.csv"
    with mp.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=t.m.META_COLUMNS)
        w.writeheader()
        w.writerow({
            "selection_row": 0,
            "canonical_cell_id": "c0",
            "donor_id": "d0",
            "expression_row": 0,
            "primary_row_weight": 1.0,
            "source_library": value,
        })
    rows = list(csv.DictReader(bm.open()))
    rows[0]["meta_sha256"] = t.sh(mp)
    t.rewrite_manifest_and_audit(bm, audit, rows)


def test_full_binder_accepts_authenticated_integral_float_text(tmp_path):
    root, db, bm, contract, audit = t.fixture(tmp_path)
    _rewrite_library_text(root, bm, audit, "61129.0")
    out = t.invoke(root, db, bm, contract, audit, tmp_path)
    assert out["status"] == "PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE"


def test_full_binder_rejects_fractional_text_with_block_key(tmp_path):
    root, db, bm, contract, audit = t.fixture(tmp_path)
    _rewrite_library_text(root, bm, audit, "61129.5")
    try:
        t.invoke(root, db, bm, contract, audit, tmp_path)
    except RuntimeError as exc:
        assert "STOP_FULL104_BLOCK_META_VALUE_SEMANTICS:op00/block-00000:source_library" in str(exc)
    else:
        raise AssertionError("fractional source_library must fail with block identity")
