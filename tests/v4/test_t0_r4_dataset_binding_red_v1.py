"""R4 red-before regressions for dataset-bound T0 inputs.

These cases are intentionally written against the producer head
ab61cf5599663c417d2b2c5ef95ca7e5a37a312c.  They cover only this project's
own provenance pipeline and use synthetic local fixtures.  No production B2 or
pathology value is accessed.

The governing rule is data-first: decision-bearing values must be derived from
the exact authenticated dataset substrate they claim to summarize, rather than
allowing caller-supplied values to travel beside correct-looking root strings.
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

import t0_estimability_preflight_v1 as pf  # noqa: E402
import t0_technical_completeness_authority_v1 as tc  # noqa: E402
import t0_v20_row_count_authority_v1 as rc  # noqa: E402


def _csv(columns, rows) -> bytes:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


def test_r4_raw_source_proof_rejects_a_fabricated_vector_even_when_every_label_matches() -> None:
    """Correct provenance labels are not authentication of caller-created values."""
    bound = 9470
    logical = {
        "rows": [{
            "canonical_cell_id": "C1",
            "donor_id": "D1",
            "expression_row": 100,
            "source_library": bound,
        }]
    }
    fabricated = [0] * (rc.SOURCE_FEATURE_COUNT - 1) + [bound]

    # On ab61cf55 this returns True: the values were never read from H5 bytes.
    with pytest.raises(AssertionError, match="AUTHENTICATED_SOURCE"):
        rc.prove_source_library(
            logical=logical,
            logical_index=0,
            raw_source_row_values=fabricated,
            raw_source_provenance={
                "source_sha256": rc.MTG_SOURCE_SHA256,
                "source_row_index": 100,
                "source_width": rc.SOURCE_FEATURE_COUNT,
                "canonical_cell_id": "C1",
                "donor_id": "D1",
                "matrix_slot": rc.MTG_SOURCE_MATRIX_SLOT,
            },
        )


def test_r4_manifest_rows_and_nnz_are_required_not_optional_audit_labels() -> None:
    """The frozen Phase2 manifest makes rows/nnz authoritative execution geometry."""
    membership = _csv(
        ["cell_id", "donor_id", "operator_index", "matrix_id"],
        [["C1", "D1", "31", "sea_ad_mtg_rna_final_2026"]],
    )
    meta = _csv(
        ["canonical_cell_id", "donor_id"],
        [["C1", "D1"]],
    )
    meta_sha = hashlib.sha256(meta).hexdigest()
    # Deliberately omit rows and nnz.  ab61cf55 accepts this.
    manifest = _csv(
        ["block_key", "operator_index", "matrix_id", "meta_path", "meta_sha256",
         "counts_path", "counts_sha256"],
        [["op31/block-00000", "31", "sea_ad_mtg_rna_final_2026",
          "op31/block-00000.meta.csv", meta_sha,
          "op31/block-00000.counts.npz", "d" * 64]],
    )

    with pytest.raises(AssertionError, match="MANIFEST.*(rows|nnz)|MANIFEST_COLUMNS"):
        rc.build_population_closure(
            membership_bytes=membership,
            expected_membership_sha256=hashlib.sha256(membership).hexdigest(),
            block_manifest_bytes=manifest,
            expected_block_manifest_sha256=hashlib.sha256(manifest).hexdigest(),
            meta_bytes_by_path={"op31/block-00000.meta.csv": meta},
            operator_index=31,
            matrix_id="sea_ad_mtg_rna_final_2026",
        )


def test_r4_technical_completeness_refuses_detached_values_under_parent_root_strings(
        tmp_path: Path) -> None:
    """Parent root strings must not authorize caller-supplied Q inputs."""
    substrate = {
        "population_closure_root_sha256": "1" * 64,
        "logical_row_authority_root_sha256": "2" * 64,
        "physical_read_plan_root_sha256": "3" * 64,
        "feature_authority_root_sha256": "4" * 64,
        "projection_root_sha256": "5" * 64,
    }

    # On ab61cf55 this packages the fabricated tuple successfully.
    with pytest.raises(AssertionError, match="AUTHENTICATED|SUBSTRATE|DETACHED"):
        tc.build_authority(
            tmp_path / "pkg",
            cells_by_donor={"D1": [(9470, 3000)]},
            substrate=substrate,
            derivation_code_sha256="c" * 64,
            candidate_donors=["D1"],
        )


def _generic_values(n: int, salt: int) -> list[float]:
    import hashlib as _hashlib
    out = []
    for i in range(n):
        h = _hashlib.sha256(("r4|%d|%d" % (salt, i)).encode()).digest()
        out.append(int.from_bytes(h[:6], "big") / float(1 << 48))
    return out


def test_r4_estimability_refuses_unbound_positional_covariates_even_with_donor_ids() -> None:
    """A positional permutation can change rank, so donor identity/order is mandatory."""
    n = 18
    donors = ["D%02d" % i for i in range(n)]
    confirmation = {
        "donor_id": donors,
        "age": [70 + ((i * 7) % 27) for i in range(n)],
        "sex": [i % 2 for i in range(n)],
    }

    # These are all finite generic-position vectors.  On ab61cf55 donor_id is
    # silently ignored and the function accepts positional arrays.
    with pytest.raises(AssertionError, match="DONOR.*(ORDER|IDENTITY|ALIGN)|UNBOUND"):
        pf.stage_b_state_designs(
            confirmation=confirmation,
            state_score=_generic_values(n, 1),
            immune_fraction=_generic_values(n, 2),
            q_depth=[2.0 + v for v in _generic_values(n, 3)],
            q_detect=_generic_values(n, 4),
        )
