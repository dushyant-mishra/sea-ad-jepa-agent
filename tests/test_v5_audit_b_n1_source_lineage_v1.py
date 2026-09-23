"""Synthetic-only tests for the missing per-cell/donor/source lineage check."""
from __future__ import annotations

import csv

import numpy as np
import pytest

from sea_ad_jepa.v5 import audit_b_n1_source_lineage_v1 as gate

from sea_ad_jepa.v5.audit_b_n1_source_lineage_v1 import (
    SOURCES,
    assess_source_vectors,
)


@pytest.fixture
def inputs():
    donors = [f"D{i:03}" for i in range(104)]
    donor_src = np.array([0] * 41 + [1] * 17 + [2] * 46, dtype=np.int64)
    cell_donor = np.array([0, 1, 41, 58], dtype=np.int64)
    metadata_source = donor_src[cell_donor]
    return dict(
        donor_names=donors,
        donor_source_code=donor_src,
        stored_source_names=list(SOURCES),
        stored_per_cell_source=metadata_source.copy(),
        metadata_cell_donor=cell_donor,
        metadata_cell_source=metadata_source,
        expected_cells=4,
        expected_source_cells=(2, 1, 1),
    )


def test_canonical_alignment_is_diagnostic_only_never_n1_authority(inputs):
    out = assess_source_vectors(**inputs)
    assert out["state"] == "CANONICAL_SOURCE_ALIGNMENT_OBSERVED__DIAGNOSTIC_ONLY"
    assert out["source_name_order_matches"] is True
    assert out["src_of_cell_equals_donor_src_at_metadata_donor"] is True
    assert out["src_of_cell_mismatch_count"] == 0


def test_real_discovered_first_appearance_bug_is_quarantined(inputs):
    old = dict(
        inputs,
        stored_source_names=["HVS", "SEA_AD", "NPH52"],
        stored_per_cell_source=np.array([0, 0, 2, 1], dtype=np.int64),
    )
    out = assess_source_vectors(**old)
    assert out["state"] == "QUARANTINED_SOURCE_ENCODING__N1_STOP"
    assert out["source_name_order_matches"] is False
    assert out["src_of_cell_equals_donor_src_at_metadata_donor"] is False
    assert out["src_of_cell_mismatch_count"] == 2


def test_only_fixing_names_does_not_hide_bad_src_of_cell(inputs):
    wrong = dict(
        inputs,
        stored_per_cell_source=np.array([0, 0, 2, 1], dtype=np.int64),
    )
    out = assess_source_vectors(**wrong)
    assert out["state"] == "QUARANTINED_SOURCE_ENCODING__N1_STOP"
    assert out["source_name_order_matches"] is True
    assert out["src_of_cell_mismatch_count"] == 2


def test_only_fixing_per_cell_vector_does_not_hide_wrong_names(inputs):
    wrong = dict(inputs, stored_source_names=["HVS", "SEA_AD", "NPH52"])
    out = assess_source_vectors(**wrong)
    assert out["state"] == "QUARANTINED_SOURCE_ENCODING__N1_STOP"
    assert out["src_of_cell_mismatch_count"] == 0
    assert out["source_name_order_matches"] is False


def test_coordinated_source_permutation_that_preserves_histogram_fails(inputs):
    switched = inputs["donor_source_code"].copy()
    switched[41], switched[58] = switched[58], switched[41]
    assert tuple(np.bincount(switched, minlength=3)) == (41, 17, 46)
    fake = dict(
        inputs,
        donor_source_code=switched,
        stored_per_cell_source=switched[inputs["metadata_cell_donor"]],
    )
    with pytest.raises(ValueError, match="authenticated Level-4 donor/source"):
        assess_source_vectors(**fake)


def test_untrusted_float_source_or_out_of_range_donor_is_rejected(inputs):
    fake = dict(
        inputs,
        stored_per_cell_source=inputs["stored_per_cell_source"].astype(np.float64),
    )
    with pytest.raises(ValueError, match="exact int64"):
        assess_source_vectors(**fake)
    bad = inputs["metadata_cell_donor"].copy()
    bad[0] = 104
    fake = dict(inputs, metadata_cell_donor=bad)
    with pytest.raises(ValueError, match="outside canonical donor"):
        assess_source_vectors(**fake)


@pytest.fixture
def synthetic_physical_layout(tmp_path, monkeypatch):
    """Three independent SHA-verified metadata blocks, zero count matrices."""
    donors = [f"D{i:03}" for i in range(104)]
    donor_src = np.array([0] * 41 + [1] * 17 + [2] * 46, dtype=np.int64)
    root = tmp_path / "level4"
    root.mkdir()
    heavy = tmp_path / "original-synthetic.npz"
    np.savez(
        heavy,
        duniq=np.asarray(donors, dtype=object),
        donor_src=donor_src,
        source_names=np.asarray(["HVS", "SEA_AD", "NPH52"], dtype=object),
        src_of_cell=np.asarray([0, 0, 2, 1], dtype=np.int64),
    )
    monkeypatch.setattr(gate, "N_CELLS", 4)
    monkeypatch.setattr(gate, "N_BLOCKS", 3)
    monkeypatch.setattr(gate, "SOURCE_CELLS", (2, 1, 1))
    monkeypatch.setattr(gate, "ORIGINAL_HEAVY_SHA256", gate.sha256_file(heavy))
    rows = []
    meta_files = {}
    for source, pairs in (
        ("HVS", [(0, "D000"), (1, "D001")]),
        ("NPH52", [(2, "D041")]),
        ("SEA_AD", [(3, "D058")]),
    ):
        meta = root / f"{source}.csv"
        with meta.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=gate.META_COLUMNS)
            writer.writeheader()
            for selection, donor in pairs:
                writer.writerow({
                    "selection_row": selection,
                    "canonical_cell_id": f"C{selection}",
                    "donor_id": donor,
                    "expression_row": selection,
                    "primary_row_weight": 1,
                    "source_library": 100,
                })
        meta_files[source] = meta
        rows.append({
            "block_key": source,
            "source": source,
            "rows": len(pairs),
            "meta_path": meta.name,
            "meta_sha256": gate.sha256_file(meta),
        })
    manifest = root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    def write_manifest():
        with manifest.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        monkeypatch.setattr(gate, "MANIFEST_SHA256", gate.sha256_file(manifest))
    write_manifest()
    return heavy, root, rows, meta_files, write_manifest


def test_physical_metadata_auditor_quarantines_original_mislabel_without_count_files(
    synthetic_physical_layout,
):
    heavy, root, _, _, _ = synthetic_physical_layout
    assert not list(root.glob("*.npz"))
    record = gate.audit_original_heavy_source_lineage(
        heavy_artifact=heavy, level4_root=root,
    )
    assert record["state"] == "QUARANTINED_SOURCE_ENCODING__N1_STOP"
    assert record["metadata_blocks_sha_verified"] == 3
    assert record["metadata_cells_accounted_exactly_once"] == 4
    assert record["src_of_cell_mismatch_count"] == 2
    assert record["n1_targets_selected"] is False
    assert record["training_authorized"] is False
    assert record["receipt_sha256"] == gate.canonical_digest({
        k: v for k, v in record.items() if k != "receipt_sha256"
    })


def test_physical_metadata_auditor_rejects_tampered_metadata_sha(
    synthetic_physical_layout,
):
    heavy, root, _, meta_files, _ = synthetic_physical_layout
    with meta_files["NPH52"].open("a", encoding="utf-8") as handle:
        handle.write("TAMPER\n")
    with pytest.raises(ValueError, match="metadata physical SHA"):
        gate.audit_original_heavy_source_lineage(
            heavy_artifact=heavy, level4_root=root,
        )


def test_physical_metadata_auditor_rejects_resealed_wrong_donor_source(
    synthetic_physical_layout,
):
    heavy, root, rows, meta_files, write_manifest = synthetic_physical_layout
    path = meta_files["NPH52"]
    with path.open(newline="", encoding="utf-8") as handle:
        records = list(csv.DictReader(handle))
    records[0]["donor_id"] = "D058"  # SEA_AD donor inside NPH52 block
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=gate.META_COLUMNS)
        writer.writeheader()
        writer.writerows(records)
    next(row for row in rows if row["source"] == "NPH52")["meta_sha256"] = gate.sha256_file(path)
    write_manifest()  # simulate an attacker also resealing the outer manifest
    with pytest.raises(ValueError, match="authenticated Level-4 donor/source"):
        gate.audit_original_heavy_source_lineage(
            heavy_artifact=heavy, level4_root=root,
        )
