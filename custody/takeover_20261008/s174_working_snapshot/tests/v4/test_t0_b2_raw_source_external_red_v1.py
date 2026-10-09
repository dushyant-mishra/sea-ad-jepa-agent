"""External B2 raw-source authenticity attack.

Target producing head:
24b2c9ffc0ab2d63061c20af8829bcb86114b11a

The current prove_source_library() validates caller-declared provenance fields,
but receives no H5AD bytes/path/reader object from which the row was actually
extracted. A fabricated 36,601-wide vector can therefore be labelled with the
frozen source SHA, row, cell, donor and layers/UMIs slot and be accepted solely
because its integer sum matches source_library.

This test must turn green only when the proof is coupled to an authenticated
read from the exact frozen H5AD source.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "v4") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_v20_row_count_authority_v1 as rc  # noqa: E402


def test_fabricated_row_plus_correct_provenance_labels_must_not_prove_source_library():
    logical = {
        "rows": [{
            "logical_index": 0,
            "canonical_cell_id": "C1",
            "donor_id": "D1",
            "expression_row": 123,
            "source_library": 1000,
        }]
    }

    # These values were not read from any H5AD. They are synthesized here.
    forged = [0] * rc.SOURCE_FEATURE_COUNT
    forged[0] = 1000

    labels = {
        "source_sha256": rc.MTG_SOURCE_SHA256,
        "source_row_index": 123,
        "source_width": rc.SOURCE_FEATURE_COUNT,
        "canonical_cell_id": "C1",
        "donor_id": "D1",
        "matrix_slot": rc.MTG_SOURCE_MATRIX_SLOT,
    }

    with pytest.raises(AssertionError):
        rc.prove_source_library(
            logical=logical,
            logical_index=0,
            raw_source_row_values=forged,
            raw_source_provenance=labels,
        )


def test_source_library_proof_api_must_receive_authenticated_source_material():
    import inspect

    names = set(inspect.signature(rc.prove_source_library).parameters)
    assert (
        "source_bytes" in names
        or "source_path" in names
        or "authenticated_source_reader" in names
        or "source_handle" in names
    ), (
        "provenance labels are not authentication; the proof API must be coupled "
        "to the exact frozen H5AD source material or an authenticated reader "
        "whose construction is externally bound"
    )
