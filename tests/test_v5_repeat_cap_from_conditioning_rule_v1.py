import hashlib
import importlib.util
import sqlite3
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "v5_anticheat" / "derive_repeat_cap_from_conditioning_rule_v1.py"
spec = importlib.util.spec_from_file_location("caprule", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def make_db(tmp_path: Path) -> Path:
    p = tmp_path / "meta.sqlite"
    con = sqlite3.connect(p)
    con.execute("create table cells(donor_id text, partition text)")
    con.executemany(
        "insert into cells values(?,?)",
        [("small", "reader_fit")] * 2 + [("large", "reader_fit")] * 20,
    )
    con.commit()
    con.close()
    return p


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_minimum_cap_is_derived_not_typed(tmp_path):
    db = make_db(tmp_path)
    out = m.derive(
        metadata_sqlite=db,
        expected_metadata_sha256=sha(db),
        partition="reader_fit",
        conditioning_ceiling=Fraction(4, 1),
    )
    assert out["derived_boundary"]["minimum_compatible_cell_repeat_cap"] == 3
    assert out["derived_boundary"]["ratio_at_cap"]["passes"] is True
    assert out["derived_boundary"]["ratio_at_previous_cap"]["passes"] is False
    assert out["training_authorized"] is False


def test_metadata_hash_mismatch_fails(tmp_path):
    db = make_db(tmp_path)
    with pytest.raises(RuntimeError, match="SHA_MISMATCH"):
        m.derive(
            metadata_sqlite=db,
            expected_metadata_sha256="0" * 64,
            partition="reader_fit",
            conditioning_ceiling=Fraction(4, 1),
        )


def test_conditioning_ceiling_is_explicit_input(tmp_path):
    db = make_db(tmp_path)
    loose = m.derive(
        metadata_sqlite=db,
        expected_metadata_sha256=sha(db),
        partition="reader_fit",
        conditioning_ceiling=Fraction(5, 1),
    )
    strict = m.derive(
        metadata_sqlite=db,
        expected_metadata_sha256=sha(db),
        partition="reader_fit",
        conditioning_ceiling=Fraction(2, 1),
    )
    assert loose["derived_boundary"]["minimum_compatible_cell_repeat_cap"] == 2
    assert strict["derived_boundary"]["minimum_compatible_cell_repeat_cap"] == 5
