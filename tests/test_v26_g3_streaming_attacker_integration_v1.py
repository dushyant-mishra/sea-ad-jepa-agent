"""G3 integration red-team: real streamed geometry is SYNTHETIC here.

Import the pre-existing authentic-block-shaped fixture; do not copy the
normalization, source map, or old runner into a new self-confirming test.
"""
from __future__ import annotations

import numpy as np
import pytest

from test_v5_full104_masking_streaming_executor_v1 import _fixture, parameters, budget
from sea_ad_jepa.v5 import full104_masking_streaming_executor_v1 as executor
from sea_ad_jepa.v5.g3_explicit_attacker_fit_objective_v1 import OBJECTIVES


@pytest.mark.parametrize("objective", OBJECTIVES)
def test_every_explicit_g3_objective_produces_separately_labeled_development_rows(tmp_path, objective):
    _, stream, _, _ = _fixture(tmp_path)
    old = executor.run_primary_fold_streaming(
        stream=stream, fold_index=0, parameters=parameters(),
        evidence_budget=budget(), global_seed=17,
    )
    new = executor.run_primary_fold_streaming(
        stream=stream, fold_index=0, parameters=parameters(),
        evidence_budget=budget(), global_seed=17, g3_fit_objective=objective,
    )
    assert len(old) == len(new) == 8
    for a, b in zip(old, new):
        assert "g3_fit_objective_id" not in a
        assert b["g3_fit_objective_id"] == objective
        assert b["g3_scope"] == "DEVELOPMENT_ONLY__UNDEFINED_HELDOUT_TERMS_NOT_QUALIFIED"
        for frozen in ("fold","target_col","target_id","method","targeted_n","mask_cardinality"):
            assert a[frozen] == b[frozen]
        # All 12 donors have 4 cells and each of two sources has 6 donors:
        # 3 policies have exactly identical donor masses on this fixture.
        assert b["score"] == pytest.approx(a["score"],abs=2e-10,rel=2e-10)
        assert b["delta"] == pytest.approx(a["delta"],abs=2e-10,rel=2e-10)


def test_objective_is_forwarded_to_both_ridge8_partner_selection_and_primary_scoring(tmp_path, monkeypatch):
    _, stream, _, _ = _fixture(tmp_path)
    original = executor._fit_ridge_weights
    seen = []
    def spy(*args, **kwargs):
        seen.append((int(kwargs["feature_cols"].size),kwargs.get("fit_objective")))
        return original(*args, **kwargs)
    monkeypatch.setattr(executor,"_fit_ridge_weights",spy)
    out = executor.run_primary_fold_streaming(
        stream=stream, fold_index=0, parameters=parameters(),
        evidence_budget=budget(), global_seed=17,
        g3_fit_objective="PRODUCTION_OBJECTIVE_MATCHED",
    )
    assert len(out) == 8
    assert len(seen) >= 10  # 2 targets x (RIDGE8 partner + 4 masked arms)
    assert all(obj=="PRODUCTION_OBJECTIVE_MATCHED" for _,obj in seen)
    assert any(n==5 for n,_ in seen)  # RIDGE8 partner candidate pool
    assert any(n==3 for n,_ in seen)  # all primary-scoring arms


def test_unknown_fit_mode_rejected_without_starting_attacker(tmp_path, monkeypatch):
    _, stream, _, _ = _fixture(tmp_path)
    def forbidden(*args, **kwargs):
        raise AssertionError("an invalid objective reached real source traversal")
    monkeypatch.setattr(executor,"_collect_stats",forbidden)
    with pytest.raises(ValueError,match="unknown explicit G3"):
        executor.run_primary_fold_streaming(
            stream=stream, fold_index=0, parameters=parameters(),
            evidence_budget=budget(), global_seed=17,
            g3_fit_objective="AUTO_PREFERRED_WINNER",
        )


def test_legacy_default_retains_exact_historical_output_schema(tmp_path):
    _, stream, _, _ = _fixture(tmp_path)
    rows=executor.run_primary_fold_streaming(
        stream=stream, fold_index=0, parameters=parameters(),
        evidence_budget=budget(), global_seed=17,
    )
    assert rows and all("g3_fit_objective_id" not in r for r in rows)
    assert rows and all("g3_scope" not in r for r in rows)


def test_all_fold_wrapper_propagates_explicit_objective_with_no_crossfold_fallback(tmp_path):
    _, stream, _, _ = _fixture(tmp_path)
    rows=executor.run_all_primary_folds_streaming(
        stream=stream, parameters=parameters(), evidence_budget=budget(),
        global_seed=17, g3_fit_objective="PRODUCTION_OBJECTIVE_MATCHED",
    )
    assert len(rows)==24
    assert {int(x["fold"]) for x in rows}=={0,1,2}
    assert all(x["g3_fit_objective_id"]=="PRODUCTION_OBJECTIVE_MATCHED" for x in rows)
    assert all(x["g3_scope"].startswith("DEVELOPMENT_ONLY") for x in rows)
