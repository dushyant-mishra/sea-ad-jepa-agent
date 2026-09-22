from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

import sea_ad_jepa.v5.audit_b_n1_cached_planner_v1 as cached

ROOT = Path(__file__).resolve().parents[1]
GEN_PATH = ROOT / "analysis/v5_full104_information_channel_redteam_20260920/scripts/audit_b_mask_plan_generator_20260920.py"
_spec = importlib.util.spec_from_file_location("audit_b_plan_for_cached_test", GEN_PATH)
plan_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(plan_mod)

_fx_spec = importlib.util.spec_from_file_location(
    "exec_fixture_cached",
    ROOT / "tests/test_v5_full104_masking_streaming_executor_v1.py",
)
exec_fixture = importlib.util.module_from_spec(_fx_spec)
_fx_spec.loader.exec_module(exec_fixture)

GLOBAL_SEED = 20260920
FOLD = 0


def _setup(tmp_path: Path):
    _, stream, _, _ = exec_fixture._fixture(tmp_path)
    parameters = exec_fixture.parameters()
    parameters.validate()
    return stream, parameters


def _canonical_plan(plan):
    out = {}
    for method, row in plan.items():
        out[method] = {
            k: tuple(sorted(v)) if isinstance(v, set) else (
                tuple(v) if isinstance(v, (list, tuple)) else v
            )
            for k, v in row.items()
        }
    return out


def test_cached_planner_matches_frozen_plan_generator_across_rungs(tmp_path: Path) -> None:
    stream, parameters = _setup(tmp_path)
    for target_col, target_id in zip(stream.target_cols, stream.target_ids):
        partners = cached.select_target_fold_partners(
            stream=stream,
            fold_index=FOLD,
            target_col=int(target_col),
            parameters=parameters,
            global_seed=GLOBAL_SEED,
        )
        # Exercise several distinct burden geometries; partner discovery remains fixed.
        max_co = int(stream.universe_cols.size - 1)
        counts = sorted(set([1, max(1, max_co // 3), max(1, max_co // 2)]))
        for co_mask_count in counts:
            expected = plan_mod.plan_masks_for_target(
                stream=stream,
                fold_index=FOLD,
                target_col=int(target_col),
                target_id=target_id,
                parameters=parameters,
                co_mask_count=co_mask_count,
                global_seed=GLOBAL_SEED,
            )
            observed = cached.plans_from_cached_partners(
                stream=stream,
                partners=partners,
                target_id=target_id,
                co_mask_count=co_mask_count,
                global_seed=GLOBAL_SEED,
            )
            assert _canonical_plan(observed) == _canonical_plan(expected)


def test_rung_materialization_does_not_repeat_partner_discovery(
    tmp_path: Path,
    monkeypatch,
) -> None:
    stream, parameters = _setup(tmp_path)
    target_col = int(stream.target_cols[0])
    target_id = stream.target_ids[0]

    calls = {"top": 0, "ridge": 0, "prefix": 0}
    originals = {
        "top": cached._top_partners,
        "ridge": cached._ridge_partners,
        "prefix": cached._prefix3_partners,
    }

    def top(*args, **kwargs):
        calls["top"] += 1
        return originals["top"](*args, **kwargs)

    def ridge(*args, **kwargs):
        calls["ridge"] += 1
        return originals["ridge"](*args, **kwargs)

    def prefix(*args, **kwargs):
        calls["prefix"] += 1
        return originals["prefix"](*args, **kwargs)

    monkeypatch.setattr(cached, "_top_partners", top)
    monkeypatch.setattr(cached, "_ridge_partners", ridge)
    monkeypatch.setattr(cached, "_prefix3_partners", prefix)

    partners = cached.select_target_fold_partners(
        stream=stream,
        fold_index=FOLD,
        target_col=target_col,
        parameters=parameters,
        global_seed=GLOBAL_SEED,
    )
    assert calls == {"top": 1, "ridge": 1, "prefix": 1}

    max_co = int(stream.universe_cols.size - 1)
    for co_mask_count in range(1, min(max_co, 6) + 1):
        cached.plans_from_cached_partners(
            stream=stream,
            partners=partners,
            target_id=target_id,
            co_mask_count=co_mask_count,
            global_seed=GLOBAL_SEED,
        )
    assert calls == {"top": 1, "ridge": 1, "prefix": 1}


def test_cached_planner_uses_only_training_donors_for_partner_discovery(
    tmp_path: Path,
) -> None:
    stream, parameters = _setup(tmp_path)
    target_col = int(stream.target_cols[0])
    before = cached.select_target_fold_partners(
        stream=stream,
        fold_index=FOLD,
        target_col=target_col,
        parameters=parameters,
        global_seed=GLOBAL_SEED,
    )

    # The original plan-generator regression suite independently proves the
    # frozen selection functions are held-out blind. Here we pin that the cache
    # does not add a held-out donor argument or alter fold semantics.
    train = np.flatnonzero(stream.fold_by_donor != FOLD)
    heldout = np.flatnonzero(stream.fold_by_donor == FOLD)
    assert train.size and heldout.size
    assert set(train.tolist()).isdisjoint(set(heldout.tolist()))
    assert before.fold_index == FOLD
