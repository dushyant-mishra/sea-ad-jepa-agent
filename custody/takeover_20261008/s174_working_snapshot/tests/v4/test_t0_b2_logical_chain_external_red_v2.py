"""External B2 logical-authority chain attacks.

Target producing head:
24b2c9ffc0ab2d63061c20af8829bcb86114b11a

The membership->closure anti-splice repair is expected to be green. The other
cases remain red on this head because the logical root does not bind its parent
closure root or operational paths, and the verifier does not compare the stored
logical root against recomputation.
"""
from __future__ import annotations

import csv
import hashlib
import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "v4") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_v20_row_count_authority_v1 as rc  # noqa: E402

MATRIX = "sea_ad_mtg_rna_final_2026"
OP = 31
FEATURE_ROOT = "538b73b8414f47c70507cb0c8b46a6d4787e019c49056e07d6b0238382cf99b8"


def _csv(cols, rows):
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(cols)
    w.writerows(rows)
    return s.getvalue().encode("utf-8")


def _membership(order=("C1", "C2")):
    donor = {"C1": "D1", "C2": "D2"}
    return _csv(
        ["cell_id", "donor_id", "operator_index", "matrix_id"],
        [[c, donor[c], OP, MATRIX] for c in order],
    )


def _meta():
    return _csv(
        ["selection_row", "canonical_cell_id", "donor_id", "expression_row",
         "primary_row_weight", "source_library"],
        [[10, "C1", "D1", 100, "1.0", 1000],
         [20, "C2", "D2", 200, "1.0", 2000]],
    )


def _world():
    mem = _membership()
    meta = _meta()
    counts = b"bound-count-payload"
    path = "op31/block-0.meta.csv"
    manifest = _csv(
        ["block_key", "operator_index", "matrix_id", "meta_path", "meta_sha256",
         "counts_path", "counts_sha256"],
        [["op31/block-0", OP, MATRIX, path, hashlib.sha256(meta).hexdigest(),
          "op31/block-0.counts.npz", hashlib.sha256(counts).hexdigest()]],
    )
    closure = rc.build_population_closure(
        membership_bytes=mem,
        expected_membership_sha256=hashlib.sha256(mem).hexdigest(),
        block_manifest_bytes=manifest,
        expected_block_manifest_sha256=hashlib.sha256(manifest).hexdigest(),
        meta_bytes_by_path={path: meta},
        operator_index=OP,
        matrix_id=MATRIX,
    )
    logical = rc.build_logical_row_authority(
        closure=closure,
        membership_bytes=mem,
        feature_authority_root_sha256=FEATURE_ROOT,
    )
    return mem, manifest, closure, logical


def _verify(logical, expected):
    return rc.assert_row_authority_lawful(
        logical=logical,
        expected_logical_row_authority_root_sha256=expected,
        expected_feature_authority_root_sha256=FEATURE_ROOT,
    )


def test_membership_to_closure_to_logical_anti_splice_is_now_closed():
    _mem, _manifest, closure, _logical = _world()
    membership_b = _membership(order=("C2", "C1"))
    with pytest.raises(AssertionError):
        rc.build_logical_row_authority(
            closure=closure,
            membership_bytes=membership_b,
            feature_authority_root_sha256=FEATURE_ROOT,
        )


def test_stored_logical_root_must_equal_recomputed_and_external():
    _mem, _manifest, _closure, logical = _world()
    expected = logical["logical_row_authority_root_sha256"]
    forged = dict(logical)
    forged["logical_row_authority_root_sha256"] = "f" * 64
    with pytest.raises(AssertionError):
        _verify(forged, expected)


def test_logical_root_must_bind_population_closure_root():
    _mem, _manifest, _closure, logical = _world()
    expected = logical["logical_row_authority_root_sha256"]
    forged = dict(logical)
    forged["population_closure_root_sha256"] = "f" * 64
    with pytest.raises(AssertionError):
        _verify(forged, expected)


@pytest.mark.parametrize(
    "field,value",
    [
        ("meta_path", "evil/other.meta.csv"),
        ("counts_path", "evil/other.counts.npz"),
    ],
)
def test_logical_root_must_bind_execution_used_paths(field, value):
    _mem, _manifest, _closure, logical = _world()
    expected = logical["logical_row_authority_root_sha256"]
    forged = dict(logical)
    forged["rows"] = [dict(r) for r in logical["rows"]]
    forged["rows"][0][field] = value
    with pytest.raises(AssertionError):
        _verify(forged, expected)
