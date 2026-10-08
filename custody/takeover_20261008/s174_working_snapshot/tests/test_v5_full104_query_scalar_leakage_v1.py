"""Counterfactual leakage test: can the target's own value reach the features?

Why a counterfactual and not a structural check
-----------------------------------------------
``_collect_stats`` already refuses ``target_col in feature_cols``. That guards
column *identity*, which is necessary and not sufficient: a feature can carry the
target's value without being the target's column. The classic route is a shared
normalization denominator. FULL104 applies ``log1p(10000 * count / L)``, and if
``L`` were the row total recomputed from the data, it would include the target's
own count -- so changing the target would change *every* feature, and the target
would be partly recoverable from features that never name it.

So the property that actually matters is behavioural, and it is a same-cell
counterfactual: **change only the target address's value for a cell, hold
everything else fixed, and no feature the model sees may move.**

What these tests establish
--------------------------
``test_target_counterfactual_moves_no_feature``
    The as-built pipeline satisfies the invariant. ``L`` is read from the
    authenticated ``source_library`` metadata field, not recomputed from the
    matrix, so perturbing the target column changes no feature value.

``test_the_test_has_power_when_the_denominator_is_recomputed``
    The negative control. With ``L`` recomputed as the row sum -- the natural
    "improvement" someone might make -- the same perturbation moves every
    feature. Without this arm, a pass above would be uninformative: it would not
    distinguish a real invariant from a test too weak to detect its violation.

What these tests do NOT establish
---------------------------------
They constrain the *implementation*. They do not show that the recorded
``source_library`` is independent of the target in the underlying biology -- it
is not. A cell's library size is its total UMI count across all addresses, which
includes the target's. That shared-denominator dependency is real, is present in
the data rather than in the code, and is not removable by masking. It is a
candidate mechanism for residual predictability that survives every burden rung,
and is tracked as such rather than being asserted here.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np
import pytest
import scipy.sparse as sp

from sea_ad_jepa.v5.full104_masking_streaming_executor_v1 import Full104ManifestStreamV1

N_DONORS = 6
CELLS_PER_DONOR = 4
N_COLS = 8
TARGET_COL = 0
FEATURE_COLS = np.arange(1, N_COLS, dtype=np.int64)

MANIFEST_FIELDS = (
    "block_key", "source", "operator_index", "matrix_id", "rows", "nnz",
    "counts_path", "counts_sha256", "meta_path", "meta_sha256",
)
META_FIELDS = (
    "selection_row", "canonical_cell_id", "donor_id",
    "expression_row", "primary_row_weight", "source_library",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _raw_counts() -> np.ndarray:
    """Deterministic positive integer counts with no tied columns."""
    rows = []
    for d in range(N_DONORS):
        for c in range(CELLS_PER_DONOR):
            rows.append([
                1 + ((3 * c + d) % 7),                      # target
                2 + ((5 * c + 2 * d + 1) % 9),
                3 + ((7 * c + d) % 11),
                1 + ((2 * c + 3 * d) % 13),
                4 + ((11 * c + 5 * d) % 8),
                2 + ((13 * c + 7 * d) % 10),
                5 + ((17 * c + 11 * d) % 12),
                1 + ((19 * c + 13 * d) % 6),
            ])
    return np.asarray(rows, dtype=np.int32)


def _build(tmp_path: Path, raw: np.ndarray, *, recompute_library: bool) -> Full104ManifestStreamV1:
    """Materialize a Level-4-shaped store and a stream over it.

    ``recompute_library=False`` mirrors production: the ``source_library`` written
    to metadata is the authenticated library size, fixed independently of any
    later perturbation of the matrix. ``True`` is the negative-control arm, where
    the denominator is derived from the row sum of the stored counts.
    """
    donor_ids = [f"D{i:02d}" for i in range(N_DONORS)]
    source_by_donor = np.array(["A"] * (N_DONORS // 2) + ["B"] * (N_DONORS - N_DONORS // 2),
                               dtype=object)
    fold_by_donor = np.arange(N_DONORS, dtype=np.int64) % 3

    if recompute_library:
        libraries = raw.sum(axis=1).astype(np.int64)
    else:
        # Authenticated library size, pinned to the UNPERTURBED counts.
        libraries = _raw_counts().sum(axis=1).astype(np.int64)

    block_root = tmp_path / "blocks"
    block_root.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    for d, donor_id in enumerate(donor_ids):
        block_dir = block_root / f"op{d:02d}"
        block_dir.mkdir(exist_ok=True)
        begin, end = d * CELLS_PER_DONOR, (d + 1) * CELLS_PER_DONOR
        matrix = sp.csr_matrix(raw[begin:end])
        counts_rel = Path(f"op{d:02d}") / "block-00000.counts.npz"
        meta_rel = Path(f"op{d:02d}") / "block-00000.meta.csv"
        sp.save_npz(block_root / counts_rel, matrix)
        with (block_root / meta_rel).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(META_FIELDS), lineterminator="\n")
            writer.writeheader()
            for local, selection in enumerate(range(begin, end)):
                writer.writerow({
                    "selection_row": selection,
                    "canonical_cell_id": f"{donor_id}-{local:04d}",
                    "donor_id": donor_id,
                    "expression_row": selection,
                    "primary_row_weight": 1.0,
                    "source_library": int(libraries[selection]),
                })
        manifest_rows.append({
            "block_key": f"op{d:02d}/block-00000",
            "source": str(source_by_donor[d]),
            "operator_index": d,
            "matrix_id": f"m{d:02d}",
            "rows": matrix.shape[0],
            "nnz": int(matrix.nnz),
            "counts_path": counts_rel.as_posix(),
            "counts_sha256": _sha(block_root / counts_rel),
            "meta_path": meta_rel.as_posix(),
            "meta_sha256": _sha(block_root / meta_rel),
        })

    manifest = tmp_path / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(MANIFEST_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(manifest_rows)

    return Full104ManifestStreamV1(
        manifest_path=manifest,
        block_root=block_root,
        expected_manifest_sha256=_sha(manifest),
        donor_id_to_code={donor_id: i for i, donor_id in enumerate(donor_ids)},
        source_by_donor=source_by_donor,
        fold_by_donor=fold_by_donor,
        universe_cols=np.arange(N_COLS, dtype=np.int64),
        target_cols=np.array([TARGET_COL], dtype=np.int64),
        target_ids=np.array(["q0"], dtype=object),
        expected_cell_count=raw.shape[0],
        verify_block_hashes=True,
    )


def _feature_matrix(stream: Full104ManifestStreamV1) -> np.ndarray:
    """Dense normalized features, ordered by selection_row, exactly as fitted."""
    rows: dict[int, np.ndarray] = {}
    for block in stream.iter_blocks(columns=FEATURE_COLS):
        dense = np.asarray(block.X.todense())
        for local, selection in enumerate(block.selection_rows):
            rows[int(selection)] = dense[local]
    return np.stack([rows[i] for i in sorted(rows)])


def _perturb_target(raw: np.ndarray) -> np.ndarray:
    """Counterfactual: change ONLY the target address, for every cell."""
    perturbed = raw.copy()
    perturbed[:, TARGET_COL] = perturbed[:, TARGET_COL] + 17
    assert np.array_equal(perturbed[:, 1:], raw[:, 1:]), "only the target may change"
    assert not np.array_equal(perturbed[:, TARGET_COL], raw[:, TARGET_COL])
    return perturbed


def test_target_counterfactual_moves_no_feature(tmp_path: Path) -> None:
    """Changing only the target's value must not move any feature the model sees."""
    raw = _raw_counts()
    before = _feature_matrix(_build(tmp_path / "before", raw, recompute_library=False))
    after = _feature_matrix(
        _build(tmp_path / "after", _perturb_target(raw), recompute_library=False)
    )

    assert before.shape == after.shape
    assert np.array_equal(before, after), (
        "the target's value reached the features: max abs delta "
        f"{np.max(np.abs(before - after)):.3e}. Feature values must not depend on "
        "the target address, or the shortcut evaluation is measuring leakage."
    )


def test_the_test_has_power_when_the_denominator_is_recomputed(tmp_path: Path) -> None:
    """Negative control: a row-sum denominator makes the same perturbation visible.

    Without this arm the test above proves nothing -- a test that cannot fail is
    not evidence. Here the only change is where the normalization denominator
    comes from, and every feature moves.
    """
    raw = _raw_counts()
    before = _feature_matrix(_build(tmp_path / "before", raw, recompute_library=True))
    after = _feature_matrix(
        _build(tmp_path / "after", _perturb_target(raw), recompute_library=True)
    )

    assert not np.array_equal(before, after), (
        "negative control failed to fire: with a recomputed row-sum denominator the "
        "target's value MUST reach the features, so this arm proves the counterfactual "
        "above has the power to detect leakage"
    )
    moved = np.mean(np.abs(before - after) > 0.0)
    assert moved > 0.99, f"expected essentially every feature to move, got {moved:.3f}"


def test_feature_columns_cannot_contain_the_target_column(tmp_path: Path) -> None:
    """The structural guard still holds: necessary, though not sufficient on its own."""
    from sea_ad_jepa.v5.full104_masking_streaming_executor_v1 import _collect_stats

    stream = _build(tmp_path, _raw_counts(), recompute_library=False)
    with pytest.raises(ValueError, match="feature_cols cannot contain target_col"):
        _collect_stats(
            stream,
            donors=np.arange(N_DONORS, dtype=np.int64),
            target_col=TARGET_COL,
            feature_cols=np.array([TARGET_COL, 2, 3], dtype=np.int64),
            need_xx=False,
        )
