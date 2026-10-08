"""Parity tests for the Audit B read-only mask-plan generator.

The generator must produce byte-for-byte the same mask the real executor would
apply. It does not reimplement the frozen logic -- it calls it -- but that is an
assertion about the code as written, and code changes. These tests pin it
against the executor's OWN reported values on a fixture, so any future drift in
either path fails here rather than silently changing what Audit B measures.

Three properties are pinned:

1. **Parity** -- identical ``targeted_cols``, ``mask_cardinality`` and
   ``effective_targeted_n`` for every policy, against ``run_primary_fold_streaming``.
2. **Exact address-count parity across policies** -- every policy's mask has the
   same cardinality, which is the premise Audit B exists to interrogate.
3. **STOP boundary** -- the plan generator never touches held-out donors. Tested
   by mutating the held-out donors' data and requiring the plans to be unchanged.

Property 3 is the one that matters most: it is an empirical check that the
factoring is actually held-out-blind, not merely believed to be.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
GEN_PATH = ROOT / "analysis/v5_full104_information_channel_redteam_20260920/scripts/audit_b_mask_plan_generator_20260920.py"
_spec = importlib.util.spec_from_file_location("audit_b_plan", GEN_PATH)
plan_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(plan_mod)

# Reuse the executor test's fixture so the substrate is the frozen one.
_fx_spec = importlib.util.spec_from_file_location(
    "exec_fixture", ROOT / "tests/test_v5_full104_masking_streaming_executor_v1.py")
exec_fixture = importlib.util.module_from_spec(_fx_spec)
_fx_spec.loader.exec_module(exec_fixture)

from sea_ad_jepa.v5.full104_masking_streaming_executor_v1 import (  # noqa: E402
    _METHODS,
    run_primary_fold_streaming,
)

GLOBAL_SEED = 20260920
FOLD = 0


def _setup(tmp_path: Path):
    _, stream, _, _ = exec_fixture._fixture(tmp_path)
    parameters = exec_fixture.parameters()
    budget = exec_fixture.budget()
    parameters.validate()
    budget.validate()
    eligible_non_target = int(stream.universe_cols.size - 1)
    co_mask_count = int(budget.mask_count(eligible_non_target))
    return stream, parameters, budget, co_mask_count


def test_plan_generator_matches_the_real_executor_exactly(tmp_path: Path):
    stream, parameters, budget, co_mask_count = _setup(tmp_path)

    rows = run_primary_fold_streaming(
        stream=stream, fold_index=FOLD, parameters=parameters,
        evidence_budget=budget, global_seed=GLOBAL_SEED,
    )
    by_key = {(r["target_col"], r["method"]): r for r in rows}

    checked = 0
    for target_col, target_id in zip(stream.target_cols, stream.target_ids):
        plans = plan_mod.plan_masks_for_target(
            stream=stream, fold_index=FOLD, target_col=int(target_col), target_id=target_id,
            parameters=parameters, co_mask_count=co_mask_count, global_seed=GLOBAL_SEED,
        )
        for method in _METHODS:
            ref = by_key[(int(target_col), method)]
            got = plans[method]
            assert tuple(got["targeted_cols"]) == tuple(ref["targeted_cols"]), (
                f"{method} target {target_col}: partner selection drifted")
            assert got["mask_cardinality"] == ref["mask_cardinality"], (
                f"{method} target {target_col}: mask cardinality drifted")
            assert got["effective_targeted_n"] == ref["effective_targeted_n"], (
                f"{method} target {target_col}: effective targeted count drifted")
            checked += 1
    assert checked == len(stream.target_cols) * len(_METHODS)


def test_every_policy_mask_has_identical_cardinality(tmp_path: Path):
    """The premise Audit B interrogates: address-count parity holds exactly."""
    stream, parameters, _, co_mask_count = _setup(tmp_path)
    for target_col, target_id in zip(stream.target_cols, stream.target_ids):
        plans = plan_mod.plan_masks_for_target(
            stream=stream, fold_index=FOLD, target_col=int(target_col), target_id=target_id,
            parameters=parameters, co_mask_count=co_mask_count, global_seed=GLOBAL_SEED,
        )
        sizes = {m: plans[m]["mask_cardinality"] for m in _METHODS}
        assert len(set(sizes.values())) == 1, f"address-count parity broken: {sizes}"
        assert set(sizes.values()) == {co_mask_count + 1}, (
            f"expected co_mask_count+1 (target included), got {sizes}")


def test_added_and_dropped_sets_have_equal_size_and_explain_the_whole_difference(tmp_path: Path):
    """Burden differences are carried ONLY by the swapped addresses.

    This is what lets Audit B compute exact burden deltas from per-address
    sufficient statistics instead of re-evaluating every cell against every mask.
    """
    stream, parameters, _, co_mask_count = _setup(tmp_path)
    for target_col, target_id in zip(stream.target_cols, stream.target_ids):
        plans = plan_mod.plan_masks_for_target(
            stream=stream, fold_index=FOLD, target_col=int(target_col), target_id=target_id,
            parameters=parameters, co_mask_count=co_mask_count, global_seed=GLOBAL_SEED,
        )
        base = plans["_base_mask"]["mask"]
        for method in _METHODS:
            added = set(plans[method]["added_vs_base"])
            dropped = set(plans[method]["dropped_vs_base"])
            assert len(added) == len(dropped), (
                f"{method}: swap is not cardinality preserving ({len(added)} vs {len(dropped)})")
            assert plans[method]["mask"] == (base - dropped) | added
            assert int(target_col) not in added and int(target_col) not in dropped
            if method == "UNIFORM_RANDOM":
                assert not added and not dropped


def test_plan_generator_is_blind_to_heldout_donor_data(tmp_path: Path):
    """STOP boundary, tested empirically rather than asserted.

    Every held-out donor's counts are replaced with different values. If any
    plan changes, the generator is reading held-out data and Audit B would be
    contaminated.
    """
    import csv
    import hashlib
    import scipy.sparse as sp

    stream, parameters, _, co_mask_count = _setup(tmp_path)
    heldout = set(np.flatnonzero(stream.fold_by_donor == FOLD).astype(int).tolist())
    assert heldout, "fixture must have held-out donors for this test to mean anything"

    before = {}
    for target_col, target_id in zip(stream.target_cols, stream.target_ids):
        plans = plan_mod.plan_masks_for_target(
            stream=stream, fold_index=FOLD, target_col=int(target_col), target_id=target_id,
            parameters=parameters, co_mask_count=co_mask_count, global_seed=GLOBAL_SEED,
        )
        before[int(target_col)] = {m: (tuple(plans[m]["targeted_cols"]),
                                       tuple(sorted(plans[m]["mask"]))) for m in _METHODS}

    # Perturb held-out donors' stored counts, then re-authenticate the manifest
    # so the stream still validates and the ONLY change is held-out content.
    rows = list(csv.DictReader(stream.manifest_path.open(newline="")))
    donor_of_block = {}
    for row in rows:
        meta = list(csv.DictReader((stream.block_root / row["meta_path"]).open(newline="")))
        donor_of_block[row["block_key"]] = stream.donor_id_to_code[str(meta[0]["donor_id"])]
    changed = 0
    for row in rows:
        if donor_of_block[row["block_key"]] not in heldout:
            continue
        counts_path = stream.block_root / row["counts_path"]
        matrix = sp.load_npz(counts_path).tocsr()
        matrix.data = (matrix.data * 3 + 1).astype(matrix.data.dtype)
        sp.save_npz(counts_path, matrix)
        row["nnz"] = str(int(matrix.nnz))
        row["counts_sha256"] = hashlib.sha256(counts_path.read_bytes()).hexdigest()
        changed += 1
    assert changed, "no held-out block was perturbed; the test would be vacuous"
    with stream.manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    stream.expected_manifest_sha256 = hashlib.sha256(
        stream.manifest_path.read_bytes()).hexdigest()
    stream._manifest_rows = None if hasattr(stream, "_manifest_rows") else None

    for target_col, target_id in zip(stream.target_cols, stream.target_ids):
        plans = plan_mod.plan_masks_for_target(
            stream=stream, fold_index=FOLD, target_col=int(target_col), target_id=target_id,
            parameters=parameters, co_mask_count=co_mask_count, global_seed=GLOBAL_SEED,
        )
        after = {m: (tuple(plans[m]["targeted_cols"]),
                     tuple(sorted(plans[m]["mask"]))) for m in _METHODS}
        assert after == before[int(target_col)], (
            f"target {target_col}: mask plan changed when ONLY held-out donor data changed -- "
            "the generator is not held-out-blind")


def test_deterministic_target_subset_is_reproducible_and_data_independent():
    ids = [f"q{i:05d}" for i in range(500)]
    a = plan_mod.deterministic_target_subset(ids, count=16)
    b = plan_mod.deterministic_target_subset(ids, count=16)
    assert np.array_equal(a, b), "subset rule is not reproducible"
    assert a.size == 16 and len(set(a.tolist())) == 16
    # Prefix property: a larger request extends the same ordering.
    c = plan_mod.deterministic_target_subset(ids, count=32)
    assert np.array_equal(c[:16], a), "subset is not a stable prefix ordering"
    # Changing the salt must change the selection, proving it is hash-driven.
    d = plan_mod.deterministic_target_subset(ids, count=16, salt="DIFFERENT")
    assert not np.array_equal(a, d)


def test_plan_generator_never_references_the_heldout_scorer():
    """Static guard: the module must not import or call the scoring function."""
    source = GEN_PATH.read_text(encoding="utf-8")
    body = source.split('"""', 2)[2] if source.count('"""') >= 2 else source
    assert "_ridge_primary_score" not in body, (
        "the mask-plan generator must never reference the held-out scorer")
    assert "heldout" not in body.lower().replace("held-out", ""), (
        "the mask-plan generator must never construct a held-out donor set")
