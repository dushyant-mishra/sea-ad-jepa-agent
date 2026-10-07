"""The adapter is the instrument for the anti-cheat rehearsal, so it is tested before use.

If planted truth, a hidden value, or operator context could reach the model-facing side through
ordinary plumbing, the rehearsal would report a cheat the harness itself created. These tests pin
that each visibility class is a separate structure, that no hidden value influences anything on
the model side, that the three measurement states survive, that the hidden-target draw depends only
on declared support and cell identity, that observation identity comes from the producer and is
authenticated by name, and that the adapter refuses any world it would have to guess about.

Every test states the value that would make it fail, and the fixture asserts its own
informativeness. Earlier versions of this suite passed against an all-ones mask (S128), targets
drawn from detected values (S132), a denominator that included hidden counts (S167), and full
expression on the model batch (S168); the tests below exist because those could not fail.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import fields, is_dataclass
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
UNIVERSE = np.array([2, 3, 5, 8, 9, 11, 14, 15, 18, 20, 21, 24, 27, 28, 30, 33, 35, 36, 38, 39],
                    dtype=np.int64)            # non-contiguous, so an off-by-one cannot pass
SRC = np.arange(N_CELLS) % 3
OP = SRC * 2 + (np.arange(N_CELLS) // 3) % 2  # six operators, each belonging to one source
DON = np.arange(N_CELLS) % 4
ROSTER = ["SEA_AD", "NPH52", "HVS"]           # truth order, deliberately not the coverage order
OPERATORS = [f"op{i}" for i in range(6)]
IDENTITY = dict(source_roster=ROSTER, operator_ids=OPERATORS,
                operator_source_map=[[o, ROSTER[i // 2]] for i, o in enumerate(OPERATORS)],
                donor_ids=["d0", "d1", "d2", "d3"], support_rule_id="TEST_RULE")


def _support(src, op):
    a = np.arange(N_ADDR)
    cover = {0: a % 3 != 0, 1: a % 4 != 1, 2: np.ones(N_ADDR, dtype=bool)}
    sup = np.stack([cover[int(s)] for s in src])
    sup[np.asarray(op) % 2 == 1] &= (a % 7 != 0)
    return sup


SUPPORT = _support(SRC, OP)


def _dense(seed):
    rng = np.random.default_rng(seed)
    return (rng.random((N_CELLS, N_ADDR)) < 0.5) * rng.integers(1, 9, (N_CELLS, N_ADDR)) * SUPPORT


def _world(tmp_path: Path, seed: int = 0, truth_tweak: float = 0.0, count_seed: int | None = None,
           dense: np.ndarray | None = None, corrupt: str | None = None) -> Path:
    root = tmp_path / "world"
    (root / "hidden_truth").mkdir(parents=True)
    obs = root / "observable_raw" / "TESTOBS"
    obs.mkdir(parents=True)
    n = N_CELLS
    d = np.array(_dense(seed if count_seed is None else count_seed) if dense is None else dense)
    if corrupt == "count_outside_support":
        i, j = np.argwhere(~SUPPORT)[0]
        d[i, j] = 3
    X = sparse.csr_matrix(d.astype(np.int32))
    src, op, don = SRC.copy(), OP.copy(), DON.copy()
    if corrupt == "operator_from_wrong_source":
        op[0] = 2                                  # cell 0 is SEA_AD; operator 2 belongs to NPH52
    if corrupt == "index_outside_roster":
        src[0] = 7
    shard = dict(indices=X.indices.astype(np.int32), data=X.data.astype(np.int32),
                 indptr=X.indptr.astype(np.int64), n_addresses=np.int64(N_ADDR),
                 global_cell_index=np.arange(n, dtype=np.int64),
                 cell_id=np.array([f"c{i}" for i in range(n)]),
                 support_count=SUPPORT.sum(1).astype(np.int32),
                 support_mask_packed=np.packbits(SUPPORT, axis=1),
                 source_index=src.astype(np.int16), operator_index=op.astype(np.int16),
                 donor_index=don.astype(np.int32))
    if corrupt == "no_support":
        del shard["support_mask_packed"]
    if corrupt == "support_count_disagrees":
        shard["support_count"] = shard["support_count"] + 1
    if corrupt == "no_producer_identity":
        del shard["source_index"]
    np.savez_compressed(obs / "RNA_SPARSE_000000000_000000012.npz", **shard)
    man = {"schema": "TEST", "n_addresses": N_ADDR, "n_cells": n, "structural_support_rule": "TEST_RULE",
           "observation_identity": IDENTITY, "shards": [{"file": "RNA_SPARSE_000000000_000000012.npz"}]}
    if corrupt == "no_identity_block":
        del man["observation_identity"]
    (obs / "FULLSCALE_MANIFEST.json").write_text(json.dumps(man))

    rng = np.random.default_rng(seed)
    truth = dict(
        global_cell_index=np.arange(n, dtype=np.int64) + (1 if corrupt == "misaligned_truth" else 0),
        cell_id=np.array([f"c{i}" for i in range(n)]),
        z_global=rng.standard_normal((n, 4)).astype(np.float32),
        z_reg_private=(rng.standard_normal((n, 2)) + truth_tweak).astype(np.float32),
        rare_flags=(rng.random((n, 4)) < 0.2).astype(np.uint8),
        z_partial=rng.standard_normal((n, 5)).astype(np.float32))
    if corrupt != "truth_without_design_fields":
        truth.update(source_index=SRC.astype(np.int8), operator_index=OP.astype(np.int16),
                     donor_index=DON.astype(np.int16))
    if corrupt == "truth_disagrees_with_producer":
        truth["source_index"] = np.roll(SRC, 1).astype(np.int8)
    if corrupt == "undeclared_truth_field":
        truth["z_new_unclassified"] = rng.standard_normal((n, 2)).astype(np.float32)
    np.savez_compressed(root / "hidden_truth" / "TRUTH_000000000_000000012.npz", **truth)
    return root


def _conv(path, **kw):
    return A.build_from_world(path, "TESTOBS", UNIVERSE, **kw)


MODEL_FACING = (A.SyntheticModelBatch, A.SyntheticOperatorContext, A.SyntheticSplitContext)


def test_fixture_is_informative():
    u = SUPPORT[:, UNIVERSE]
    assert not u.all(), "fixture support is all ones; mask tests would be uninformative"
    first_by_source = {int(s): u[(SRC == s) & (OP % 2 == 0)][0] for s in np.unique(SRC)}
    assert len({r.tobytes() for r in first_by_source.values()}) == 3, "sources must differ"
    assert (u[(SRC == 0) & (OP % 2 == 0)][0] != u[(SRC == 0) & (OP % 2 == 1)][0]).any(), (
        "operator attrition must change support within a source")
    assert ROSTER != ["HVS", "NPH52", "SEA_AD"], "roster order must differ from coverage order"


# ------------------------------------------------------------------ separation of classes

def test_no_oracle_field_on_any_model_facing_structure():
    for cls in MODEL_FACING:
        names = {f.name for f in fields(cls)}
        assert not names & A.ORACLE_ONLY_FIELDS, f"{cls.__name__} exposes {sorted(names & A.ORACLE_ONLY_FIELDS)}"


def test_model_batch_holds_only_model_inputs():
    """S162 and S168: no operator context and no hidden value can be represented on the batch."""
    names = {f.name for f in fields(A.SyntheticModelBatch)}
    assert names == {"gene_ids", "student_expression", "measurement_mask", "hidden_target_mask"}


def test_structures_hold_no_reference_to_each_other(tmp_path):
    conv = _conv(_world(tmp_path))
    structures = (conv.model, conv.operator_context, conv.split_context, conv.readout, conv.oracle)
    for s in structures:
        for f in fields(s):
            v = getattr(s, f.name)
            assert not is_dataclass(v), f"{type(s).__name__}.{f.name} holds another structure"
    assert "z_reg_private" in conv.oracle.latents, "the fixture must contain the trap latent"


def test_changing_oracle_truth_does_not_change_model_facing_structures(tmp_path):
    c1 = _conv(_world(tmp_path / "a", seed=1, truth_tweak=0.0))
    c2 = _conv(_world(tmp_path / "b", seed=1, truth_tweak=5.0))
    assert c1.oracle.digest() != c2.oracle.digest(), "the oracle must differ, or this proves nothing"
    for name in ("model", "operator_context", "split_context", "readout"):
        assert getattr(c1, name).digest() == getattr(c2, name).digest(), f"oracle truth leaked into {name}"


def test_hidden_values_cannot_reach_model_or_operator_context(tmp_path):
    """S167 and S168, the q-safety test. Two worlds identical except at the hidden-target
    positions must be identical on every model-facing structure. An adapter that normalises by a
    library including the hidden counts fails this."""
    base = _dense(0)
    c1 = _conv(_world(tmp_path / "a", dense=base), hidden_fraction=0.3)
    hid = c1.model.hidden_target_mask
    changed = base.copy()
    cols = UNIVERSE
    sub = changed[:, cols]
    sub[hid] = sub[hid] + 5                        # change ONLY hidden values, inside support
    changed[:, cols] = sub
    c2 = _conv(_world(tmp_path / "b", dense=changed), hidden_fraction=0.3)
    assert hid.any() and np.array_equal(hid, c2.model.hidden_target_mask)
    assert c1.readout.digest() != c2.readout.digest(), "hidden values must differ, or this proves nothing"
    assert c1.model.digest() == c2.model.digest(), "a hidden value reached the model batch"
    assert c1.operator_context.digest() == c2.operator_context.digest(), "a hidden value reached operator context"


def test_conversion_is_deterministic(tmp_path):
    root = _world(tmp_path)
    assert len({_conv(root).model.digest() for _ in range(3)}) == 1


def test_masks_align_with_gene_ids_and_ordering_is_stable(tmp_path):
    m = _conv(_world(tmp_path)).model
    assert m.gene_ids.shape == m.student_expression.shape == m.measurement_mask.shape == m.hidden_target_mask.shape
    for row in m.gene_ids:
        assert np.array_equal(row, UNIVERSE), "gene ordering is not the frozen universe order"


def test_student_evidence_is_visible_counts_over_the_visible_library(tmp_path):
    dense = _dense(0)
    conv = _conv(_world(tmp_path, dense=dense), hidden_fraction=0.3)
    m, oc = conv.model, conv.operator_context
    ev = m.evidence_mask
    assert ev.any() and (~ev).any()
    assert np.all(m.student_expression[~ev] == 0.0), "a hidden or unmeasured entry carries a value"
    vis_lib = dense.sum(1) - np.where(m.hidden_target_mask, dense[:, UNIVERSE], 0).sum(1)
    assert np.allclose(oc.visible_library_size, vis_lib)
    expect = np.log1p(dense[:, UNIVERSE] / vis_lib[:, None] * 1e4)
    assert np.allclose(m.student_expression[ev], expect[ev], rtol=1e-6)


# ------------------------------------------------------------------ measurement semantics

def test_measurement_mask_is_the_worlds_per_element_support(tmp_path):
    conv = _conv(_world(tmp_path))
    assert np.array_equal(conv.model.measurement_mask, SUPPORT[:, UNIVERSE])
    assert np.array_equal(conv.operator_context.n_measured, SUPPORT[:, UNIVERSE].sum(1))


def test_three_measurement_states_survive_conversion(tmp_path):
    dense = _dense(0)
    conv = _conv(_world(tmp_path, dense=dense), hidden_fraction=0.3)
    m = conv.model
    detected = dense[:, UNIVERSE] > 0
    measured_zero = m.measurement_mask & ~detected
    unmeasured = ~m.measurement_mask
    assert detected.any() and measured_zero.any() and unmeasured.any(), "a state is missing"
    assert not (detected & unmeasured).any(), "a detected value sits on an unmeasured address"
    assert not (m.hidden_target_mask & unmeasured).any(), "an unmeasured address was hidden"
    c = conv.provenance["three_state_counts"]
    assert c["measured_zero"] == int(measured_zero.sum())
    assert c["structurally_unmeasured"] == int(unmeasured.sum())


def test_hidden_mask_is_value_independent(tmp_path):
    c1 = _conv(_world(tmp_path / "a", count_seed=1), hidden_fraction=0.3)
    c2 = _conv(_world(tmp_path / "b", count_seed=2), hidden_fraction=0.3)
    assert not np.array_equal(c1.readout.query_counts > 0, c2.readout.query_counts > 0), (
        "the two worlds must differ in realized values, or this proves nothing")
    assert np.array_equal(c1.model.hidden_target_mask, c2.model.hidden_target_mask), (
        "hidden-target eligibility depends on the realized value")
    assert c1.provenance["hidden_targets"]["on_measured_zero"] > 0, "measured zeros were never eligible"


def test_hidden_draw_follows_cell_identity_not_row_order():
    mm = SUPPORT[:, UNIVERSE]
    gci = np.arange(N_CELLS, dtype=np.int64) * 7 + 3
    h = A.sample_hidden_targets(mm, gci, 0.3, seed=11)
    perm = np.arange(N_CELLS)[::-1]
    assert h.any()
    assert np.array_equal(A.sample_hidden_targets(mm[perm], gci[perm], 0.3, seed=11), h[perm])
    assert not (h & ~mm).any()


# ------------------------------------------------------------------ observation identity

def test_observation_identity_comes_from_the_producer(tmp_path):
    """S161. A truth folder without any design fields changes nothing: the producer supplies them."""
    c1 = _conv(_world(tmp_path / "a"))
    c2 = _conv(_world(tmp_path / "b", corrupt="truth_without_design_fields"))
    assert np.array_equal(c1.operator_context.source_index, SRC)
    assert np.array_equal(c1.operator_context.operator_index, OP)
    assert np.array_equal(c1.split_context.donor_index, DON)
    assert c1.operator_context.digest() == c2.operator_context.digest()
    assert c1.split_context.digest() == c2.split_context.digest()


# ------------------------------------------------------------------ refusals

@pytest.mark.parametrize("corrupt, message", [
    ("no_support", "per-element structural support"),
    ("count_outside_support", "structurally unsupported"),
    ("support_count_disagrees", "disagrees with support_count"),
    ("misaligned_truth", "not aligned"),
    ("undeclared_truth_field", "undeclared truth fields"),
    ("no_producer_identity", "producer-side"),
    ("no_identity_block", "observation_identity"),
    ("truth_disagrees_with_producer", "disagrees with the truth copy"),
    ("operator_from_wrong_source", "different source"),
    ("index_outside_roster", "outside its roster"),
])
def test_adapter_refuses_worlds_it_would_have_to_guess_about(tmp_path, corrupt, message):
    with pytest.raises(A.AdapterContractError, match=message):
        _conv(_world(tmp_path, corrupt=corrupt))


@pytest.mark.parametrize("bad", [np.array([1, 1, 2]), np.array([0, N_ADDR]),
                                 np.array([], dtype=np.int64), np.array([0.0, 1.0])])
def test_adapter_refuses_a_malformed_universe(tmp_path, bad):
    with pytest.raises(A.AdapterContractError):
        A.build_from_world(_world(tmp_path), "TESTOBS", bad)


def test_hidden_fraction_outside_unit_interval_is_refused():
    with pytest.raises(A.AdapterContractError):
        A.sample_hidden_targets(SUPPORT, np.arange(N_CELLS), 1.0, seed=1)


def test_model_batch_round_trips_exactly(tmp_path):
    m = _conv(_world(tmp_path)).model
    p = tmp_path / "batch.npz"
    np.savez_compressed(p, **{f.name: getattr(m, f.name) for f in fields(m)})
    z = np.load(p, allow_pickle=False)
    assert A.SyntheticModelBatch(**{f.name: z[f.name] for f in fields(m)}).digest() == m.digest()


def test_adapter_names_no_runtime_loader_class():
    src = (V77 / "v77_synthetic_batch_adapter.py").read_text(encoding="utf-8")
    assert "ProductionTrainLoader" not in src
    for forbidden in ("optimizer.step", "create_ema_target", "torch.save"):
        assert forbidden not in src, f"adapter must not implement runtime machinery: {forbidden}"
