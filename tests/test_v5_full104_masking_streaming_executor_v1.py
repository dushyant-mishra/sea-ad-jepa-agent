from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np
import pytest
import scipy.sparse as sp

from sea_ad_jepa.v5.full104_masking_qualification_runner_v1 import (
    QualificationArrays,
    run_primary_fold,
)
from sea_ad_jepa.v5.full104_masking_streaming_executor_v1 import (
    Full104ManifestStreamV1,
    run_primary_fold_streaming,
)
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v1 import (
    MaskingQualificationParametersAuthorityV1,
)
from sea_ad_jepa.v5.target_evidence_budget_authority_v1 import (
    TargetEvidenceBudgetAuthorityV1,
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def parameters() -> MaskingQualificationParametersAuthorityV1:
    return MaskingQualificationParametersAuthorityV1(
        authority_id="V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V1",
        primary_attacker_id="RIDGE_EXPRESSION_PROXY_ATTACKER_V1",
        primary_score_id="SOURCE_BALANCED_MEAN_DONOR_CENTERED_PREDICTION_CORRELATION_SQUARED_V1",
        targeted_partner_cap=2,
        ridge_candidate_pool_count=5,
        ridge_score_feature_count=3,
        ridge_alpha_numerator=1,
        ridge_alpha_denominator=100,
        prefix_inner_fold_count=3,
        prefix_candidate_count=5,
        prefix_floor_numerator=0,
        prefix_floor_denominator=1,
        prefix_reduction_numerator=1,
        prefix_reduction_denominator=2,
    )


def budget() -> TargetEvidenceBudgetAuthorityV1:
    return TargetEvidenceBudgetAuthorityV1(
        authority_id="V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V1",
        support_estimability_authority_sha256=h("support"),
        budget_semantics_id="MASK_FRACTION_OF_ELIGIBLE_NON_TARGET_RNA_V1",
        rounding_policy_id="FLOOR_EXACT_RATIONAL_V1",
        mask_fraction_numerator=1,
        mask_fraction_denominator=2,
        min_retained_non_target_rna_count=1,
        infeasible_policy_id="FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1",
    )


def _fixture(tmp_path: Path):
    n_donors = 12
    cells_per_donor = 4
    donor_ids = [f"D{i:02d}" for i in range(n_donors)]
    source_by_donor = np.array(["A"] * 6 + ["B"] * 6, dtype=object)
    fold_by_donor = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2], dtype=np.int64)
    donor_code = np.repeat(np.arange(n_donors, dtype=np.int64), cells_per_donor)

    rows = []
    for d in range(n_donors):
        for c in range(cells_per_donor):
            # Integer raw counts with donor/cell-specific structure and no tied columns.
            base = 2 + c + (d % 3)
            target0 = 1 + ((3 * c + d) % 7)
            target1 = 2 + ((5 * c + 2 * d + 1) % 9)
            rows.append(
                [
                    target0,
                    target1,
                    base + target0,
                    1 + ((2 * target0 + c + d) % 11),
                    1 + ((3 * target1 + 2 * c + d) % 13),
                    1 + ((target0 + 2 * target1 + d) % 10),
                    1 + ((4 * c + 3 * d) % 12),
                    1 + ((7 * c + d) % 8),
                ]
            )
    raw = np.asarray(rows, dtype=np.int32)
    libraries = raw.sum(axis=1).astype(np.int64)
    normalized = np.log1p(raw.astype(np.float64) * (10000.0 / libraries[:, None]))

    block_root = tmp_path / "blocks_root"
    block_root.mkdir()
    manifest_rows = []
    selection_row = 0
    for d, donor_id in enumerate(donor_ids):
        source = str(source_by_donor[d])
        block_dir = block_root / f"op{d:02d}"
        block_dir.mkdir()
        begin = d * cells_per_donor
        end = begin + cells_per_donor
        matrix = sp.csr_matrix(raw[begin:end])
        counts_rel = Path(f"op{d:02d}") / "block-00000.counts.npz"
        meta_rel = Path(f"op{d:02d}") / "block-00000.meta.csv"
        counts_path = block_root / counts_rel
        meta_path = block_root / meta_rel
        sp.save_npz(counts_path, matrix, compressed=True)
        with meta_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(
                [
                    "selection_row",
                    "canonical_cell_id",
                    "donor_id",
                    "expression_row",
                    "primary_row_weight",
                    "source_library",
                ]
            )
            for local in range(cells_per_donor):
                row_index = begin + local
                writer.writerow(
                    [
                        selection_row,
                        f"cell-{selection_row:04d}",
                        donor_id,
                        row_index,
                        "1.0",
                        int(libraries[row_index]),
                    ]
                )
                selection_row += 1
        manifest_rows.append(
            {
                "block_key": f"op{d:02d}/block-00000",
                "source": source,
                "operator_index": d,
                "matrix_id": f"M{d:02d}",
                "rows": cells_per_donor,
                "nnz": int(matrix.nnz),
                "counts_path": counts_rel.as_posix(),
                "counts_sha256": sha(counts_path),
                "meta_path": meta_rel.as_posix(),
                "meta_sha256": sha(meta_path),
            }
        )

    manifest = tmp_path / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "block_key",
                "source",
                "operator_index",
                "matrix_id",
                "rows",
                "nnz",
                "counts_path",
                "counts_sha256",
                "meta_path",
                "meta_sha256",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    universe = np.arange(raw.shape[1], dtype=np.int64)
    target_cols = np.array([0, 1], dtype=np.int64)
    target_ids = np.array(["q0", "q1"], dtype=object)
    donor_map = {donor_id: i for i, donor_id in enumerate(donor_ids)}
    reference = QualificationArrays(
        X=sp.csr_matrix(normalized),
        donor_code=donor_code,
        source_by_donor=source_by_donor,
        fold_by_donor=fold_by_donor,
        universe_cols=universe,
        target_cols=target_cols,
        target_ids=target_ids,
    )
    stream = Full104ManifestStreamV1(
        manifest_path=manifest,
        block_root=block_root,
        expected_manifest_sha256=sha(manifest),
        donor_id_to_code=donor_map,
        source_by_donor=source_by_donor,
        fold_by_donor=fold_by_donor,
        universe_cols=universe,
        target_cols=target_cols,
        target_ids=target_ids,
        expected_cell_count=raw.shape[0],
        verify_block_hashes=True,
    )
    return reference, stream, normalized, manifest_rows


def test_stream_normalizes_log1p10k_exactly_once_and_preserves_donor_identity(tmp_path: Path) -> None:
    reference, stream, normalized, _ = _fixture(tmp_path)
    stream.validate_layout()
    observed = np.zeros_like(normalized)
    observed_donor = np.full(reference.donor_code.size, -1, dtype=np.int64)
    for block in stream.iter_blocks(columns=np.arange(normalized.shape[1], dtype=np.int64)):
        observed[block.selection_rows] = block.X.toarray()
        observed_donor[block.selection_rows] = block.donor_code
    assert observed == pytest.approx(normalized, abs=1e-12, rel=1e-12)
    assert np.array_equal(observed_donor, reference.donor_code)


def test_streaming_fold_matches_canonical_reference_for_all_policy_arms(tmp_path: Path) -> None:
    reference, stream, _, _ = _fixture(tmp_path)
    expected = run_primary_fold(
        arrays=reference,
        fold_index=0,
        parameters=parameters(),
        evidence_budget=budget(),
        global_seed=17,
    )
    observed = run_primary_fold_streaming(
        stream=stream,
        fold_index=0,
        parameters=parameters(),
        evidence_budget=budget(),
        global_seed=17,
    )
    assert len(observed) == len(expected)
    for got, want in zip(observed, expected):
        for key in (
            "fold",
            "target_index",
            "target_col",
            "target_id",
            "method",
            "primary_attacker_id",
            "primary_score_id",
            "targeted_cols",
            "targeted_n",
            "effective_targeted_n",
            "mask_cardinality",
            "uniform_mask_cardinality",
        ):
            assert got[key] == want[key]
        assert got["score"] == pytest.approx(want["score"], abs=2e-10, rel=2e-10)
        assert got["uniform_score"] == pytest.approx(want["uniform_score"], abs=2e-10, rel=2e-10)
        assert got["delta"] == pytest.approx(want["delta"], abs=2e-10, rel=2e-10)


def test_stream_fails_closed_on_block_hash_mismatch(tmp_path: Path) -> None:
    _, stream, _, rows = _fixture(tmp_path)
    counts = stream.block_root / rows[0]["counts_path"]
    counts.write_bytes(counts.read_bytes() + b"corruption")
    with pytest.raises(ValueError, match="hash"):
        stream.validate_layout()


def test_stream_fails_closed_on_duplicate_selection_row_within_block(tmp_path: Path) -> None:
    _, stream, _, rows = _fixture(tmp_path)
    meta = stream.block_root / rows[0]["meta_path"]
    lines = meta.read_text(encoding="utf-8").splitlines()
    fields = lines[1].split(",")
    duplicate = lines[2].split(",")
    duplicate[0] = fields[0]
    lines[2] = ",".join(duplicate)
    meta.write_text("\\n".join(lines) + "\\n", encoding="utf-8")

    # Rebind the manifest to the deliberately modified fixture so the failure is
    # selection-row identity, not the earlier metadata-hash guard.
    manifest = stream.manifest_path
    manifest_rows = list(csv.DictReader(manifest.open(newline="", encoding="utf-8")))
    manifest_rows[0]["meta_sha256"] = sha(meta)
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=manifest_rows[0].keys(), lineterminator="\\n")
        writer.writeheader()
        writer.writerows(manifest_rows)
    rebound = Full104ManifestStreamV1(
        manifest_path=manifest,
        block_root=stream.block_root,
        expected_manifest_sha256=sha(manifest),
        donor_id_to_code=stream.donor_id_to_code,
        source_by_donor=stream.source_by_donor,
        fold_by_donor=stream.fold_by_donor,
        universe_cols=stream.universe_cols,
        target_cols=stream.target_cols,
        target_ids=stream.target_ids,
        expected_cell_count=stream.expected_cell_count,
        verify_block_hashes=True,
    )
    with pytest.raises(ValueError, match="duplicate selection_row"):
        rebound.validate_layout()


def test_streaming_executor_does_not_construct_a_monolithic_full104_matrix() -> None:
    source = Path("src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py").read_text(encoding="utf-8")
    forbidden = (
        "sp.vstack(",
        "sparse.vstack(",
        "np.vstack(all_blocks",
        "training_authorized=True",
        "protected_outcomes_authorized=True",
    )
    assert [token for token in forbidden if token in source] == []
