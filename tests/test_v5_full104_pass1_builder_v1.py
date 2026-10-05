"""Regressions for the physical FULL104 pass1 builder.

The September-17 pass1 was rejected by the physical verifier because its per-cell
vectors were indexed by block iteration order rather than by the global
``selection_row`` identity. These tests prove the replacement builder is
invariant to storage traversal, and reproduce the original defect as an explicit
negative control so it cannot silently return.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest
import scipy.sparse as sp

from sea_ad_jepa.v5 import full104_pass1_builder_v1 as builder
from sea_ad_jepa.v5 import full104_pass1_physical_binding_v1 as binding

# Real source identities; the builder validates against the frozen tuple.
SRC = ("HVS", "NPH52")
DONORS = ("D-beta", "D-alpha", "D-gamma")   # deliberately NOT lexicographic
N_ADDR = 6
N_ROWS = 8


def write_registry(path: Path, width: int) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=("molecular_address_index", "molecular_address_id")
        )
        writer.writeheader()
        for index in range(width):
            writer.writerow(
                {"molecular_address_index": index, "molecular_address_id": f"addr-{index}"}
            )


def build_substrate(
    root: Path,
    *,
    block_order: list[int] | None = None,
    row_permutation: dict[int, list[int]] | None = None,
) -> Path:
    """Write a small Level-4-shaped substrate.

    ``selection_row`` is deliberately NOT equal to cumulative block position, so
    block-order indexing and selection-row indexing genuinely differ.
    """
    root.mkdir(parents=True, exist_ok=True)

    # block -> (source, donor, [(selection_row, dense_row)])
    blocks = [
        (SRC[0], DONORS[0], [(5, [1, 0, 2, 0, 0, 3]), (0, [0, 4, 0, 1, 0, 0])]),
        (SRC[0], DONORS[1], [(7, [2, 2, 0, 0, 1, 0]), (3, [0, 0, 5, 0, 0, 0])]),
        (SRC[1], DONORS[2], [(1, [9, 0, 0, 2, 0, 1]), (6, [0, 1, 1, 0, 0, 0])]),
        (SRC[1], DONORS[2], [(4, [3, 0, 0, 0, 2, 0]), (2, [0, 0, 7, 1, 0, 0])]),
    ]
    order = block_order if block_order is not None else list(range(len(blocks)))

    manifest_rows = []
    for position, block_index in enumerate(order):
        source, donor, rows = blocks[block_index]
        perm = (row_permutation or {}).get(block_index)
        if perm is not None:
            rows = [rows[i] for i in perm]

        dense = np.asarray([r[1] for r in rows], dtype=np.int64)
        matrix = sp.csr_matrix(dense)
        counts_path = root / f"counts_{block_index}.npz"
        sp.save_npz(counts_path, matrix)

        meta_path = root / f"meta_{block_index}.csv"
        with meta_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=binding.META_COLUMNS)
            writer.writeheader()
            for local, (selection_row, _vals) in enumerate(rows):
                writer.writerow(
                    {
                        "selection_row": selection_row,
                        "canonical_cell_id": f"cell-{block_index}-{local}",
                        "donor_id": donor,
                        "expression_row": local,
                        "primary_row_weight": 1.0,
                        "source_library": 100,
                    }
                )

        manifest_rows.append(
            {
                "block_key": f"block-{block_index}",
                "source": source,
                "operator_index": str(block_index),
                "matrix_id": f"matrix-{block_index}",
                "rows": str(dense.shape[0]),
                "nnz": str(matrix.nnz),
                "counts_path": counts_path.name,
                "counts_sha256": binding.sha256_file(counts_path),
                "meta_path": meta_path.name,
                "meta_sha256": binding.sha256_file(meta_path),
            }
        )

    manifest = root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=binding.MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(manifest_rows)
    return manifest


def write_observation(path: Path) -> None:
    """Four operator rows, matching the four fixture blocks.

    Addresses 0, 2 and 3 are MEASURED_SCALAR in every operator, so the strict
    common core is exactly {0, 2, 3}.
    """
    obs = np.asarray(
        [
            [1, 0, 1, 1, 1, 2],
            [1, 1, 1, 1, 0, 1],
            [1, 1, 1, 1, 1, 0],
            [1, 2, 1, 1, 1, 1],
        ],
        dtype=np.uint8,
    )
    np.savez(path, observation_state=obs)


def make_pass1(tmp_path: Path, name: str, **kwargs) -> tuple[Path, Path, Path, Path]:
    root = tmp_path / f"level4_{name}"
    registry = tmp_path / "registry.csv"
    observation = tmp_path / "observation.npz"
    out = tmp_path / f"pass1_{name}.npz"
    if not registry.exists():
        write_registry(registry, N_ADDR)
    if not observation.exists():
        write_observation(observation)
    build_substrate(root, **kwargs)
    builder.build_pass1_from_physical_full104(
        level4_root=root,
        registry_path=registry,
        observation_state_path=observation,
        out_path=out,
        expect_reference_geometry=False,
    )
    return root, registry, observation, out


def load(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as data:
        return {k: np.asarray(data[k]) for k in data.files}


def test_donor_order_rule_is_sorted_unique_physical_donor_id(tmp_path):
    _root, _reg, _obs, out = make_pass1(tmp_path, "base")
    arrays = load(out)
    assert list(arrays["duniq"].astype(str)) == sorted(set(DONORS))
    # the fixture donor ids are deliberately non-lexicographic in file order
    assert list(arrays["duniq"].astype(str)) != list(DONORS)


def test_donor_source_map_is_derived_from_physical_metadata(tmp_path):
    _root, _reg, _obs, out = make_pass1(tmp_path, "src")
    arrays = load(out)
    ids = list(arrays["duniq"].astype(str))
    src = arrays["donor_src"]
    assert src[ids.index("D-beta")] == 0     # HVS
    assert src[ids.index("D-alpha")] == 0    # HVS
    assert src[ids.index("D-gamma")] == 1    # NPH52


def test_donor_spanning_two_sources_fails_closed(tmp_path):
    root = tmp_path / "level4_bad"
    registry = tmp_path / "registry.csv"
    observation = tmp_path / "observation.npz"
    write_registry(registry, N_ADDR)
    write_observation(observation)
    build_substrate(root)
    # rewrite one NPH52 block's donor to an HVS donor id
    meta = root / "meta_2.csv"
    rows = list(csv.DictReader(meta.open(newline="", encoding="utf-8")))
    for r in rows:
        r["donor_id"] = "D-beta"
    with meta.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=binding.META_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="more than one physical source"):
        builder.derive_canonical_donor_registry(root, expect_hashes=False)


def test_block_order_scramble_leaves_pass1_unchanged(tmp_path):
    _r1, _g1, _o1, base = make_pass1(tmp_path, "order_base")
    _r2, _g2, _o2, scram = make_pass1(
        tmp_path, "order_scram", block_order=[3, 1, 0, 2]
    )
    a, b = load(base), load(scram)
    for key in builder.PASS1_ARRAYS:
        assert np.array_equal(a[key], b[key]), f"{key} changed under block reordering"


def test_row_order_scramble_within_blocks_leaves_pass1_unchanged(tmp_path):
    _r1, _g1, _o1, base = make_pass1(tmp_path, "row_base")
    _r2, _g2, _o2, scram = make_pass1(
        tmp_path,
        "row_scram",
        row_permutation={0: [1, 0], 1: [1, 0], 2: [1, 0], 3: [1, 0]},
    )
    a, b = load(base), load(scram)
    for key in builder.PASS1_ARRAYS:
        assert np.array_equal(a[key], b[key]), f"{key} changed under row reordering"


def test_both_scrambles_together_leave_pass1_unchanged(tmp_path):
    _r1, _g1, _o1, base = make_pass1(tmp_path, "both_base")
    _r2, _g2, _o2, scram = make_pass1(
        tmp_path,
        "both_scram",
        block_order=[2, 0, 3, 1],
        row_permutation={0: [1, 0], 2: [1, 0]},
    )
    a, b = load(base), load(scram)
    for key in builder.PASS1_ARRAYS:
        assert np.array_equal(a[key], b[key]), f"{key} changed under combined reordering"


def test_cells_are_keyed_to_selection_row_not_block_position(tmp_path):
    """The substrate's selection_rows are not cumulative block positions."""
    _root, _reg, _obs, out = make_pass1(tmp_path, "identity")
    arrays = load(out)
    ids = list(arrays["duniq"].astype(str))
    # selection_row 5 and 0 belong to D-beta; 7 and 3 to D-alpha; 1,6,4,2 to D-gamma
    expected = np.empty(N_ROWS, dtype=np.int64)
    for sel, donor in [(5, "D-beta"), (0, "D-beta"), (7, "D-alpha"), (3, "D-alpha"),
                       (1, "D-gamma"), (6, "D-gamma"), (4, "D-gamma"), (2, "D-gamma")]:
        expected[sel] = ids.index(donor)
    assert np.array_equal(arrays["cell_donor"], expected)


def test_builder_refuses_to_overwrite(tmp_path):
    root, registry, observation, out = make_pass1(tmp_path, "overwrite")
    with pytest.raises(ValueError, match="refuse to overwrite"):
        builder.build_pass1_from_physical_full104(
            level4_root=root,
            registry_path=registry,
            observation_state_path=observation,
            out_path=out,
            expect_reference_geometry=False,
        )


def test_duplicate_selection_row_across_blocks_fails_closed(tmp_path):
    root = tmp_path / "level4_dup"
    registry = tmp_path / "registry.csv"
    observation = tmp_path / "observation.npz"
    write_registry(registry, N_ADDR)
    write_observation(observation)
    build_substrate(root)
    meta = root / "meta_1.csv"
    rows = list(csv.DictReader(meta.open(newline="", encoding="utf-8")))
    rows[0]["selection_row"] = "5"          # collides with block 0
    with meta.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=binding.META_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="duplicate physical selection_row"):
        builder.build_pass1_from_physical_full104(
            level4_root=root,
            registry_path=registry,
            observation_state_path=observation,
            out_path=tmp_path / "pass1_dup.npz",
            expect_reference_geometry=False,
        )


def test_september17_block_position_indexing_fails_physical_verification(
    tmp_path, monkeypatch
):
    """NEGATIVE CONTROL reproducing the September-17 defect.

    Build a pass1 whose cell vectors are indexed by cumulative block position
    instead of selection_row, and require the unchanged physical verifier to
    reject it.
    """
    root, registry, observation, good = make_pass1(tmp_path, "negctl")
    arrays = load(good)

    # Rebuild cell vectors the wrong way: sequential block traversal order.
    manifest = list(
        csv.DictReader(
            (root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv").open(
                newline="", encoding="utf-8"
            )
        )
    )
    ids = list(arrays["duniq"].astype(str))
    bad_donor = np.empty(N_ROWS, dtype=np.int64)
    bad_core = np.empty(N_ROWS, dtype=np.int64)
    core = arrays["core"]
    pos = 0
    for row in manifest:
        meta_rows = list(
            csv.DictReader((root / row["meta_path"]).open(newline="", encoding="utf-8"))
        )
        matrix = sp.load_npz(root / row["counts_path"]).tocsr()
        block_core = matrix[:, core].tocsr()
        per_row = np.diff(block_core.indptr).astype(np.int64)
        for local, meta in enumerate(meta_rows):
            bad_donor[pos] = ids.index(str(meta["donor_id"]))
            bad_core[pos] = per_row[local]
            pos += 1
    assert pos == N_ROWS
    # the defect must actually differ from the correct artifact
    assert not np.array_equal(bad_donor, arrays["cell_donor"])

    bad = tmp_path / "pass1_block_position.npz"
    np.savez(
        bad,
        cell_donor=bad_donor,
        cell_nnz_core=bad_core,
        donor_addr_nnz=arrays["donor_addr_nnz"],
        donor_src=arrays["donor_src"],
        duniq=arrays["duniq"],
        core=core,
    )

    monkeypatch.setattr(
        binding, "FULL104_BLOCK_MANIFEST_SHA256",
        binding.sha256_file(root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"),
    )
    monkeypatch.setattr(binding, "CANONICAL_REGISTRY_SHA256", binding.sha256_file(registry))
    monkeypatch.setattr(binding, "OBSERVATION_STATE_SHA256", binding.sha256_file(observation))
    monkeypatch.setattr(binding, "EXPECTED_BLOCKS", 4)
    monkeypatch.setattr(binding, "EXPECTED_ROWS", N_ROWS)
    monkeypatch.setattr(binding, "EXPECTED_DONORS", 3)
    monkeypatch.setattr(binding, "EXPECTED_OPERATORS", 4)
    monkeypatch.setattr(binding, "EXPECTED_ADDRESSES", N_ADDR)
    monkeypatch.setattr(binding, "EXPECTED_CORE", int(core.size))
    monkeypatch.setattr(binding, "SOURCE_NAMES", SRC)

    with pytest.raises(ValueError, match="cell_donor does not rederive"):
        binding.verify_pass1_against_physical_full104(
            pass1_path=bad,
            level4_root=root,
            registry_path=registry,
            observation_state_path=observation,
        )


def test_correctly_built_pass1_passes_the_unchanged_verifier(tmp_path, monkeypatch):
    root, registry, observation, good = make_pass1(tmp_path, "positive")
    core = load(good)["core"]
    monkeypatch.setattr(
        binding, "FULL104_BLOCK_MANIFEST_SHA256",
        binding.sha256_file(root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"),
    )
    monkeypatch.setattr(binding, "CANONICAL_REGISTRY_SHA256", binding.sha256_file(registry))
    monkeypatch.setattr(binding, "OBSERVATION_STATE_SHA256", binding.sha256_file(observation))
    monkeypatch.setattr(binding, "EXPECTED_BLOCKS", 4)
    monkeypatch.setattr(binding, "EXPECTED_ROWS", N_ROWS)
    monkeypatch.setattr(binding, "EXPECTED_DONORS", 3)
    monkeypatch.setattr(binding, "EXPECTED_OPERATORS", 4)
    monkeypatch.setattr(binding, "EXPECTED_ADDRESSES", N_ADDR)
    monkeypatch.setattr(binding, "EXPECTED_CORE", int(core.size))
    monkeypatch.setattr(binding, "SOURCE_NAMES", SRC)

    receipt = binding.verify_pass1_against_physical_full104(
        pass1_path=good,
        level4_root=root,
        registry_path=registry,
        observation_state_path=observation,
    )
    assert receipt.row_count == N_ROWS
    assert receipt.donor_count == 3
