"""The adapter is the instrument for the anti-cheat rehearsal, so it is tested before use.

If planted truth could reach a model-facing structure through ordinary plumbing, the rehearsal
would report a cheat the harness itself created. These tests pin that it cannot, that the three
measurement states survive conversion, that the hidden-target draw depends only on declared
support and cell identity, and that the adapter refuses any world it would have to guess about.

Every test states the value that would make it fail, and the fixture asserts its own
informativeness, so none can pass vacuously. The original ten tests all passed against an
adapter whose measurement mask was all ones (S128) and whose hidden targets were drawn only
from detected values (S132); the tests after them exist because those ten could not fail.
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
N_CELLS = 12
# a deliberately non-contiguous slice, so a positional off-by-one cannot pass
UNIVERSE = np.array([2, 3, 5, 8, 9, 11, 14, 15, 18, 20, 21, 24, 27, 28, 30, 33, 35, 36, 38, 39],
                    dtype=np.int64)
SRC = np.arange(N_CELLS) % 3
OP = (np.arange(N_CELLS) // 3) % 2


def _support(src, op):
    """Source-dependent coverage plus operator attrition, the structure the observer writes."""
    a = np.arange(N_ADDR)
    cover = {0: a % 3 != 0, 1: a % 4 != 1, 2: np.ones(N_ADDR, dtype=bool)}
    sup = np.stack([cover[int(s)] for s in src])
    sup[np.asarray(op) == 1] &= (a % 7 != 0)
    return sup


SUPPORT = _support(SRC, OP)


def _world(tmp_path: Path, seed: int = 0, truth_tweak: float = 0.0,
           count_seed: int | None = None, corrupt: str | None = None) -> Path:
    """A tiny world with the canonical observer's layout: sparse counts confined to
    per-element structural support, which each shard carries, plus hidden truth."""
    root = tmp_path / "world"
    (root / "hidden_truth").mkdir(parents=True)
    obs = root / "observable_raw" / "TESTOBS"
    obs.mkdir(parents=True)

    n = N_CELLS
    crng = np.random.default_rng(seed if count_seed is None else count_seed)
    dense = (crng.random((n, N_ADDR)) < 0.5) * crng.integers(1, 9, (n, N_ADDR)) * SUPPORT
    if corrupt == "count_outside_support":
        i, j = np.argwhere(~SUPPORT)[0]
        dense[i, j] = 3
    X = sparse.csr_matrix(dense.astype(np.int32))
    shard = dict(indices=X.indices.astype(np.int32), data=X.data.astype(np.int32),
                 indptr=X.indptr.astype(np.int64), n_addresses=np.int64(N_ADDR),
                 global_cell_index=np.arange(n, dtype=np.int64),
                 cell_id=np.array([f"c{i}" for i in range(n)]),
                 support_count=SUPPORT.sum(1).astype(np.int32),
                 support_mask_packed=np.packbits(SUPPORT, axis=1))
    if corrupt == "no_support":
        del shard["support_mask_packed"]
    if corrupt == "support_count_disagrees":
        shard["support_count"] = shard["support_count"] + 1
    np.savez_compressed(obs / "RNA_SPARSE_000000000_000000012.npz", **shard)
    (obs / "FULLSCALE_MANIFEST.json").write_text(json.dumps({
        "schema": "TEST", "n_addresses": N_ADDR, "n_cells": n,
        "shards": [{"file": "RNA_SPARSE_000000000_000000012.npz"}]}))

    rng = np.random.default_rng(seed)
    truth = dict(
        global_cell_index=np.arange(n, dtype=np.int64) + (1 if corrupt == "misaligned_truth" else 0),
        cell_id=np.array([f"c{i}" for i in range(n)]),
        operator_index=OP.astype(np.int16),
        source_index=SRC.astype(np.int8),
        donor_index=(np.arange(n) % 4).astype(np.int16),
        z_global=rng.standard_normal((n, 4)).astype(np.float32),
        z_reg_private=(rng.standard_normal((n, 2)) + truth_tweak).astype(np.float32),
        rare_flags=(rng.random((n, 4)) < 0.2).astype(np.uint8),
        z_partial=rng.standard_normal((n, 5)).astype(np.float32))
    if corrupt == "undeclared_truth_field":
        truth["z_new_unclassified"] = rng.standard_normal((n, 2)).astype(np.float32)
    if corrupt == "missing_source_index":
        del truth["source_index"]
    np.savez_compressed(root / "hidden_truth" / "TRUTH_000000000_000000012.npz", **truth)
    return root


# ---------------------------------------------------------------- the fixture is informative

def test_fixture_is_informative():
    """Guards S137: the first S128 regression test used a fixture whose universe every source
    covered, so it could not distinguish a correct mask from a wrong one."""
    u = SUPPORT[:, UNIVERSE]
    assert not u.all(), "fixture support is all ones; mask tests would be uninformative"
    rows_by_source = {int(s): u[(SRC == s) & (OP == 0)][0] for s in np.unique(SRC)}
    assert len({r.tobytes() for r in rows_by_source.values()}) == 3, "sources must differ"
    same_src_diff_op = u[(SRC == 0) & (OP == 0)][0] != u[(SRC == 0) & (OP == 1)][0]
    assert same_src_diff_op.any(), "operator attrition must change support within a source"


# ---------------------------------------------------------------- separation (original ten)

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
    assert "donor_index" in oracle.latents, "donor identity must route to the oracle, not vanish"


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
    assert batch.measurement_mask.shape == batch.expression.shape
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


# ---------------------------------------------------------------- measurement semantics

def test_measurement_mask_is_the_worlds_per_element_support(tmp_path):
    """S128 and S134. Fails on the all-ones mask (5c644ced) and on a reconstruction from
    registry coverage, because neither equals the support the world actually used."""
    batch, _, _ = A.build_from_world(_world(tmp_path), "TESTOBS", UNIVERSE)
    assert np.array_equal(batch.measurement_mask, SUPPORT[:, UNIVERSE])
    assert np.array_equal(batch.n_measured, SUPPORT[:, UNIVERSE].sum(1)), (
        "n_measured must count measurable addresses, measured zeros included")


def test_three_measurement_states_survive_conversion(tmp_path):
    batch, _, prov = A.build_from_world(_world(tmp_path), "TESTOBS", UNIVERSE, hidden_fraction=0.3)
    detected = batch.expression > 0
    measured_zero = batch.measurement_mask & ~detected
    unmeasured = ~batch.measurement_mask
    assert detected.any() and measured_zero.any() and unmeasured.any(), "a state is missing"
    assert not (detected & unmeasured).any(), "a detected value sits on an unmeasured address"
    assert not (batch.hidden_target_mask & unmeasured).any(), "an unmeasured address was hidden"
    c = prov["three_state_counts"]
    assert c["measured_zero"] == int(measured_zero.sum())
    assert c["structurally_unmeasured"] == int(unmeasured.sum())


def test_hidden_mask_is_value_independent(tmp_path):
    """S132. Two worlds with identical support and cells but different realized counts must
    hide exactly the same entries. The version this replaces compared means within three SD and
    passed while every hidden target was a detected value."""
    b1, _, p1 = A.build_from_world(_world(tmp_path / "a", count_seed=1), "TESTOBS", UNIVERSE,
                                   hidden_fraction=0.3)
    b2, _, _ = A.build_from_world(_world(tmp_path / "b", count_seed=2), "TESTOBS", UNIVERSE,
                                  hidden_fraction=0.3)
    assert not np.array_equal(b1.expression > 0, b2.expression > 0), (
        "the two worlds must differ in realized values, or this proves nothing")
    assert np.array_equal(b1.hidden_target_mask, b2.hidden_target_mask), (
        "hidden-target eligibility depends on the realized value")
    assert p1["hidden_targets"]["on_measured_zero"] > 0, "measured zeros were never eligible"


def test_hidden_draw_follows_cell_identity_not_row_order():
    """S133. Reordering cells must reorder, not change, each cell's hidden targets."""
    mm = SUPPORT[:, UNIVERSE]
    gci = np.arange(N_CELLS, dtype=np.int64) * 7 + 3
    h = A.sample_hidden_targets(mm, gci, 0.3, seed=11)
    perm = np.arange(N_CELLS)[::-1]
    h_perm = A.sample_hidden_targets(mm[perm], gci[perm], 0.3, seed=11)
    assert h.any(), "nothing hidden; the test would be vacuous"
    assert np.array_equal(h_perm, h[perm]), "a cell's hidden targets depend on its row position"
    assert not (h & ~mm).any(), "a hidden target fell outside structural support"


# ---------------------------------------------------------------- refusals (fail closed)

@pytest.mark.parametrize("corrupt, message", [
    ("no_support", "per-element structural support"),
    ("count_outside_support", "structurally unsupported"),
    ("support_count_disagrees", "disagrees with support_count"),
    ("misaligned_truth", "not aligned"),
    ("undeclared_truth_field", "undeclared truth fields"),
    ("missing_source_index", "required fields"),
])
def test_adapter_refuses_worlds_it_would_have_to_guess_about(tmp_path, corrupt, message):
    with pytest.raises(A.AdapterContractError, match=message):
        A.build_from_world(_world(tmp_path, corrupt=corrupt), "TESTOBS", UNIVERSE)


@pytest.mark.parametrize("bad", [np.array([1, 1, 2]), np.array([0, N_ADDR]),
                                 np.array([], dtype=np.int64), np.array([0.0, 1.0])])
def test_adapter_refuses_a_malformed_universe(tmp_path, bad):
    with pytest.raises(A.AdapterContractError):
        A.build_from_world(_world(tmp_path), "TESTOBS", bad)


def test_hidden_fraction_outside_unit_interval_is_refused():
    with pytest.raises(A.AdapterContractError):
        A.sample_hidden_targets(SUPPORT, np.arange(N_CELLS), 1.0, seed=1)
