from __future__ import annotations

import importlib.util
from pathlib import Path

from sea_ad_jepa.v5.audit_b_n1_crossfold_planner_v1 import (
    select_all_fold_partners_two_pass,
)
from sea_ad_jepa.v5.audit_b_n1_cached_planner_v1 import (
    select_target_fold_partners,
)

ROOT = Path(__file__).resolve().parents[1]
_fx_spec = importlib.util.spec_from_file_location(
    "exec_fixture_crossfold",
    ROOT / "tests/test_v5_full104_masking_streaming_executor_v1.py",
)
exec_fixture = importlib.util.module_from_spec(_fx_spec)
_fx_spec.loader.exec_module(exec_fixture)

GLOBAL_SEED = 20260920


def test_two_pass_all_fold_planner_matches_original_foldwise_selection(
    tmp_path: Path,
) -> None:
    _, stream, _, _ = exec_fixture._fixture(tmp_path)
    parameters = exec_fixture.parameters()
    parameters.validate()

    for target_col in stream.target_cols:
        observed = select_all_fold_partners_two_pass(
            stream=stream,
            target_col=int(target_col),
            parameters=parameters,
            global_seed=GLOBAL_SEED,
        )
        assert len(observed) == 4
        for fold in range(4):
            expected = select_target_fold_partners(
                stream=stream,
                fold_index=fold,
                target_col=int(target_col),
                parameters=parameters,
                global_seed=GLOBAL_SEED,
            )
            assert observed[fold] == expected


def test_two_pass_planner_has_one_result_for_every_authenticated_fold(
    tmp_path: Path,
) -> None:
    _, stream, _, _ = exec_fixture._fixture(tmp_path)
    observed = select_all_fold_partners_two_pass(
        stream=stream,
        target_col=int(stream.target_cols[0]),
        parameters=exec_fixture.parameters(),
        global_seed=GLOBAL_SEED,
    )
    assert tuple(x.fold_index for x in observed) == (0, 1, 2, 3)
    assert all(x.target_col == int(stream.target_cols[0]) for x in observed)
