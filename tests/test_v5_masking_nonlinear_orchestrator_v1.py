from __future__ import annotations

import sys
from pathlib import Path

from sea_ad_jepa.v5.masking_nonlinear_orchestrator_v1 import (
    MODES, run_policy_nonlinear_evidence_fold,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_v5_full104_masking_streaming_executor_v1 import _fixture, budget, parameters
from test_v5_masking_nonlinear_challenge_executor_v1 import nonlinear_authority


def test_nonlinear_orchestrator_emits_all_matched_modes(tmp_path: Path):
    _, stream, _, _ = _fixture(tmp_path)
    params=parameters()
    rows=run_policy_nonlinear_evidence_fold(
        stream=stream,
        fold_index=0,
        parameters=params,
        evidence_budget=budget(),
        nonlinear_authority=nonlinear_authority(params),
        target_col=int(stream.target_cols[0]),
        target_id=stream.target_ids[0],
        method="RIDGE8_CONDITIONAL",
        primary_targeted_cols=(2,3),
        eligible_proxy_cols=stream.universe_cols,
        global_seed=17,
    )
    assert {r["mode"] for r in rows} == set(MODES)
    assert all(r["method"]=="RIDGE8_CONDITIONAL" for r in rows)
    assert all(len(r["donor_scores"])==4 for r in rows)


def test_uniform_nonlinear_orchestration_uses_same_six_modes(tmp_path: Path):
    _, stream, _, _ = _fixture(tmp_path)
    params=parameters()
    rows=run_policy_nonlinear_evidence_fold(
        stream=stream,
        fold_index=0,
        parameters=params,
        evidence_budget=budget(),
        nonlinear_authority=nonlinear_authority(params),
        target_col=int(stream.target_cols[0]),
        target_id=stream.target_ids[0],
        method="UNIFORM_RANDOM",
        primary_targeted_cols=(),
        eligible_proxy_cols=stream.universe_cols,
        global_seed=17,
    )
    assert {r["mode"] for r in rows} == set(MODES)
