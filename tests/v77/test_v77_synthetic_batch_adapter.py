"""The adapter is the instrument for the anti-cheat rehearsal, so it is tested before use.

If planted truth could reach a model-facing structure through ordinary plumbing, the rehearsal
would report a cheat the harness itself created. These tests pin that it cannot, and that the
batch is deterministic, aligned and serializable.

Every test states the value that would make it fail, so none of them can pass vacuously.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import fields
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
V77 = ROOT / "scripts" / "v77"
sys.path.insert(0, str(V77))


def _mod():
    spec = importlib.util.spec_from_file_location(
        "v77_synthetic_batch_adapter", V77 / "v77_synthetic_batch_adapter.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["v77_synthetic_batch_adapter"] = m
    spec.loader.exec_module(m)
    return m


A = _mod()

N_ADDR = 40
UNIVERSE = np.arange(5, 25, dtype=np.int64)     # a deliberately non-contiguous slice


def _world(tmp_path: Path, seed: int = 0, truth_tweak: float = 0.0) -> Path:
    """A tiny but structurally faithful world: sparse observer shards plus hidden truth."""
    root = tmp_path / "world"
    (root / "hidden_truth").mkdir(parents=True)
    obs = root / "observable_raw" / "TESTOBS"
    obs.mkdir(parents=True)

    rng = np.random.default_rng(seed)
    n = 12
    dense = (rng.random((n, N_ADDR)) < 0.4) * rng.integers(1, 9, (n, N_ADDR))
    X = sparse.csr_matrix(dense.astype(np.int32))
    np.savez_compressed(obs / "RNA_SPARSE_000000000_000000012.npz",
                        indices=X.indices.astype(np.int32), data=X.data.astype(np.int32),
                        indptr=X.indptr.astype(np.int64), n_addresses=np.int64(N_ADDR),
                        global_cell_index=np.arange(n, dtype=np.int64),
                        cell_id=np.array([f"c{i}" for i in range(n)]))
    (obs / "FULLSCALE_MANIFEST.json").write_text(json.dumps({
        "schema": "TEST", "n_addresses": N_ADDR, "n_cells": n,
        "shards": [{"file": "RNA_SPARSE_000000000_000000012.npz"}]}))

    np.savez_compressed(root / "hidden_truth" / "TRUTH_000000000_000000012.npz",
                        global_cell_index=np.arange(n, dtype=np.int64),
                        cell_id=np.array([f"c{i}" for i in range(n)]),
                        operator_index=np.arange(n, dtype=np.int16) % 3,
                        source_index=np.arange(n, dtype=np.int8) % 2,
                        z_global=rng.standard_normal((n, 4)).astype(np.float32),
                        z_reg_private=(rng.standard_normal((n, 2)) + truth_tweak).astype(np.float32),
                        rare_flags=(rng.random((n, 4)) < 0.2).astype(np.uint8),
                        z_partial=rng.standard_normal((n, 5)).astype(np.float32))
    return root


def test_oracle_fields_can_never_appear_on_the_model_batch():
    """THE CENTRAL GUARANTEE. If this fails, every anti-cheat result is suspect."""
    batch_fields = {f.name for f in fields(A.SyntheticModelBatch)}
    overlap = batch_fields & A.ORACLE_ONLY_FIELDS
    assert not overlap, f"oracle fields reachable on the model batch: {sorted(overlap)}"
    assert "z_reg_private" not in batch_fields
    assert batch_fields <= (A.PERMITTED_METADATA | {
        "gene_ids", "expression", "measurement_mask", "hidden_target_mask"}), (
        f"model batch carries unpermitted fields: {sorted(batch_fields - A.PERMITTED_METADATA)}")


def test_model_batch_holds_no_reference_to_the_oracle(tmp_path):
    batch, oracle, _ = A.build_from_world(_world(tmp_path), "TESTOBS", UNIVERSE)
    for f in fields(batch):
        assert not isinstance(getattr(batch, f.name), A.SyntheticOracleRecord)
    assert "z_reg_private" in oracle.latents, "the fixture must actually contain the trap latent"


def test_changing_oracle_truth_does_not_change_model_visible_inputs(tmp_path):
    """Perturb a latent that no observer consumes; the batch must be byte-identical."""
    b1, o1, _ = A.build_from_world(_world(tmp_path / "a", seed=1, truth_tweak=0.0), "TESTOBS", UNIVERSE)
    b2, o2, _ = A.build_from_world(_world(tmp_path / "b", seed=1, truth_tweak=5.0), "TESTOBS", UNIVERSE)
    assert o1.digest() != o2.digest(), "the oracle must actually differ, or this proves nothing"
    assert b1.digest() == b2.digest(), "oracle truth leaked into model-visible inputs"


def test_conversion_is_deterministic(tmp_path):
    root = _world(tmp_path)
    d = [A.build_from_world(root, "TESTOBS", UNIVERSE)[0].digest() for _ in range(3)]
    assert len(set(d)) == 1


def test_masks_align_with_gene_ids_and_ordering_is_stable(tmp_path):
    batch, _, _ = A.build_from_world(_world(tmp_path), "TESTOBS", UNIVERSE)
    assert batch.gene_ids.shape == batch.expression.shape == batch.hidden_target_mask.shape
    for row in batch.gene_ids:
        assert np.array_equal(row, UNIVERSE), "gene ordering is not the frozen universe order"
    assert np.array_equal(batch.global_cell_index, np.arange(len(batch.global_cell_index)))


def test_hidden_targets_are_removed_from_student_evidence(tmp_path):
    batch, _, _ = A.build_from_world(_world(tmp_path), "TESTOBS", UNIVERSE, hidden_fraction=0.4)
    assert batch.hidden_target_mask.any(), "no hidden targets drawn; the test would be vacuous"
    vis = batch.student_visible_expression()
    assert np.all(vis[batch.hidden_target_mask] == 0.0), "hidden target values visible to the student"
    kept = batch.measurement_mask & ~batch.hidden_target_mask
    assert np.allclose(vis[kept], batch.expression[kept]), "permitted evidence was altered"


def test_hidden_mask_is_value_independent(tmp_path):
    """Eligibility must follow declared support, never the realized value."""
    batch, _, _ = A.build_from_world(_world(tmp_path), "TESTOBS", UNIVERSE, hidden_fraction=0.3)
    hidden_expr = batch.expression[batch.hidden_target_mask]
    open_expr = batch.expression[~batch.hidden_target_mask]
    if len(hidden_expr) > 20 and len(open_expr) > 20:
        # means may differ by chance; a gross difference would indicate value-dependent selection
        assert abs(hidden_expr.mean() - open_expr.mean()) < 3.0 * open_expr.std()


def test_metadata_is_exactly_the_permitted_set(tmp_path):
    batch, _, _ = A.build_from_world(_world(tmp_path), "TESTOBS", UNIVERSE)
    meta = {f.name for f in fields(batch)} - {
        "gene_ids", "expression", "measurement_mask", "hidden_target_mask"}
    assert meta == set(A.PERMITTED_METADATA), f"metadata drift: {sorted(meta)}"


def test_serialization_round_trip_preserves_the_batch_exactly(tmp_path):
    batch, _, _ = A.build_from_world(_world(tmp_path), "TESTOBS", UNIVERSE)
    p = tmp_path / "batch.npz"
    np.savez_compressed(p, **{f.name: getattr(batch, f.name) for f in fields(batch)})
    z = np.load(p, allow_pickle=False)
    restored = A.SyntheticModelBatch(**{f.name: z[f.name] for f in fields(batch)})
    assert restored.digest() == batch.digest()


def test_adapter_names_no_runtime_loader_class():
    """The boundary must stay runtime-agnostic until the canonical consumer is frozen."""
    src = (V77 / "v77_synthetic_batch_adapter.py").read_text(encoding="utf-8")
    assert "ProductionTrainLoader" not in src
    for forbidden in ("optimizer.step", "create_ema_target", "torch.save"):
        assert forbidden not in src, f"adapter must not implement runtime machinery: {forbidden}"
