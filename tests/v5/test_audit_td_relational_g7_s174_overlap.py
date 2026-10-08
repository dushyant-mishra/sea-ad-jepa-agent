import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5" / "audit_td_relational_g7_s174_overlap.py"


def load_module():
    spec = importlib.util.spec_from_file_location("td_g7", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m


def test_compare_rows_exact_match():
    m = load_module()
    assert m.compare_rows({10: 2, 20: 3}, {10: 2, 20: 3, 30: 9}, {10, 20}) == {"checked": 2, "mismatches": 0}


def test_compare_rows_treats_missing_as_zero():
    m = load_module()
    assert m.compare_rows({10: 2}, {10: 2, 20: 3}, {10, 20}) == {"checked": 2, "mismatches": 1}
    assert m.compare_rows({}, {}, {10, 20}) == {"checked": 2, "mismatches": 0}


def test_verify_cache_hashes(tmp_path):
    m = load_module()
    cache = tmp_path / "cache"; cache.mkdir()
    (cache / "abc.counts.npz").write_bytes(b"counts")
    (cache / "abc.meta.npz").write_bytes(b"meta")
    freeze = {"rebuilt_cache": {"shards": {"abc": {
        "counts": m.sha256_file(cache / "abc.counts.npz"),
        "meta": m.sha256_file(cache / "abc.meta.npz"),
    }}}}
    assert m.verify_cache_hashes(cache, freeze) == 1
    (cache / "abc.counts.npz").write_bytes(b"changed")
    try:
        m.verify_cache_hashes(cache, freeze)
    except RuntimeError:
        pass
    else:
        raise AssertionError("changed G1b-authorized cache must fail closed")


def test_no_overlap_is_not_fabricated():
    m = load_module()
    assert m.overlap_status(0, 0) == "NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP"
    assert m.overlap_status(3, 0) == "PASS_TD_G7_S174_EXACT_OVERLAP"
    assert m.overlap_status(3, 1) == "STOP_TD_G7_S174_CROSSCHECK_MISMATCH"
