"""V40 exact output parity between physical frozen pre-G3 source and G3 default.

Only a synthetic, source-balanced, donor-disjoint 12-donor / 48-cell fixture
with eight columns is used. This does NOT validate actual FULL104, approve a
new Phase-IV freeze, compute terminal Audit-B N1, or authorize training.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from test_v5_full104_masking_streaming_executor_v1 import (
    _fixture, parameters, budget,
)
from sea_ad_jepa.v5 import full104_masking_streaming_executor_v1 as current
from sea_ad_jepa.v5.g3_explicit_attacker_fit_objective_v1 import OBJECTIVES

ROOT = Path(__file__).resolve().parents[1]
EXEC = "src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py"
ORIGINAL = "2ebfd6ad52b0e2a99a4917391d3f0d97a667d79b"
ORIGINAL_SHA = "143645becff6f6142d99224bfe188702b2400228b4af121738341ed4e3ebb86d"
G3_SHA = "de2f019e28675e3258cfeede65f77557210f5fcd083f94ae09f97b1c8629f9f8"
FREEZE = ROOT / "analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/AUDIT_B_FROZEN_TARGET_SAMPLE.json"


@pytest.fixture(scope="module")
def historical_source(tmp_path_factory):
    old = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{ORIGINAL}:{EXEC}"])
    assert hashlib.sha256(old).hexdigest() == ORIGINAL_SHA
    assert hashlib.sha256((ROOT / EXEC).read_bytes()).hexdigest() == G3_SHA
    freeze = json.loads(FREEZE.read_text())
    assert freeze["bound_inputs"]["planner_source"]["sha256"] == ORIGINAL_SHA
    path = tmp_path_factory.mktemp("v40_historic") / "_v40_historic_executor.py"
    path.write_bytes(old)
    # The original source is imported as a new module IN THE SAME PACKAGE so
    # historical relative imports retain their original semantics. No
    # monkeypatching of any historical or current selection or score function.
    spec = importlib.util.spec_from_file_location(
        "sea_ad_jepa.v5._v40_historical_executor", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves annotations through sys.modules during import.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("fold", [0, 1, 2])
def test_historical_and_g3_default_exact_row_and_score_parity(tmp_path, historical_source, fold):
    _, stream, _, _ = _fixture(tmp_path)
    kwargs = dict(
        stream=stream, fold_index=fold, parameters=parameters(),
        evidence_budget=budget(), global_seed=17,
    )
    historical = historical_source.run_primary_fold_streaming(**kwargs)
    successor = current.run_primary_fold_streaming(**kwargs)
    # Strict literal dict/float equality; not approximate and no rounding.
    # Also catches any silent new G3 output schema in legacy/default mode.
    assert historical == successor
    assert len(historical) == 8
    assert {r["fold"] for r in successor} == {fold}
    assert {r["method"] for r in successor} == {
        "UNIFORM_RANDOM", "TOP8_CORRELATION",
        "RIDGE8_CONDITIONAL", "PREFIX3_SELECTIVE",
    }
    assert not any("g3_fit_objective_id" in r for r in successor)


def test_historical_and_g3_default_full_wrapper_parity(tmp_path, historical_source):
    _, stream, _, _ = _fixture(tmp_path)
    kwargs = dict(stream=stream, parameters=parameters(),
                  evidence_budget=budget(), global_seed=17)
    historical = historical_source.run_all_primary_folds_streaming(**kwargs)
    successor = current.run_all_primary_folds_streaming(**kwargs)
    assert historical == successor
    assert len(historical) == 24
    assert {r["fold"] for r in historical} == {0, 1, 2}
    print("V40_HISTORICAL_G3_DEFAULT_EXACT_24_ROW_PARITY_NONAUTHORIZING")


def test_explicit_g3_is_labeled_and_not_silently_default(tmp_path, historical_source):
    _, stream, _, _ = _fixture(tmp_path)
    kwargs = dict(stream=stream, fold_index=0, parameters=parameters(),
                  evidence_budget=budget(), global_seed=17)
    original = historical_source.run_primary_fold_streaming(**kwargs)
    current_default = current.run_primary_fold_streaming(**kwargs)
    assert original == current_default
    for objective in OBJECTIVES:
        trial = current.run_primary_fold_streaming(
            **kwargs, g3_fit_objective=objective
        )
        assert len(trial) == len(original) == 8
        assert all(row["g3_fit_objective_id"] == objective for row in trial)
        assert all(
            row["g3_scope"]
            == "DEVELOPMENT_ONLY__UNDEFINED_HELDOUT_TERMS_NOT_QUALIFIED"
            for row in trial
        )


def test_unknown_objective_rejected_before_any_fold_result(tmp_path, historical_source):
    _, stream, _, _ = _fixture(tmp_path)
    with pytest.raises(ValueError, match="unknown explicit G3 fit objective"):
        current.run_primary_fold_streaming(
            stream=stream, fold_index=0, parameters=parameters(),
            evidence_budget=budget(), global_seed=17,
            g3_fit_objective="NOT_A_REGISTERED_SCIENTIFIC_OBJECTIVE",
        )


def test_original_immutable_freeze_hash_must_not_be_rewritten(tmp_path, historical_source):
    payload = json.loads(FREEZE.read_text())
    assert payload["bound_inputs"]["planner_source"]["sha256"] == ORIGINAL_SHA
    assert hashlib.sha256((ROOT / EXEC).read_bytes()).hexdigest() == G3_SHA
    assert ORIGINAL_SHA != G3_SHA
    # Passing this negative control does NOT make the old sample freeze valid
    # on the current G3 source. It proves the old expected STOP is real.
