from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sea_ad_jepa.v5.masking_donor_evidence_v1 import (
    run_reference_fold_with_donor_evidence,
    run_streaming_fold_with_donor_evidence,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_v5_full104_masking_streaming_executor_v1 import _fixture, budget, parameters


def test_donor_evidence_matches_between_reference_and_streaming(tmp_path: Path) -> None:
    reference, stream, _, _ = _fixture(tmp_path)
    ref_rows = run_reference_fold_with_donor_evidence(
        arrays=reference,
        fold_index=0,
        parameters=parameters(),
        evidence_budget=budget(),
        global_seed=17,
    )
    stream_rows = run_streaming_fold_with_donor_evidence(
        stream=stream,
        fold_index=0,
        parameters=parameters(),
        evidence_budget=budget(),
        global_seed=17,
    )
    assert len(ref_rows) == len(stream_rows)
    assert ref_rows
    for got, want in zip(stream_rows, ref_rows):
        assert got.keys() == want.keys()
        assert got["method"] == want["method"]
        assert got["target_id"] == want["target_id"]
        assert got["score"] == pytest.approx(want["score"], abs=1e-12, rel=1e-12)
        assert got["heldout_donor_scores"] == pytest.approx(
            want["heldout_donor_scores"], abs=1e-12, rel=1e-12
        )


def test_default_runner_rows_are_not_mutated_by_donor_companion(tmp_path: Path) -> None:
    reference, _, _, _ = _fixture(tmp_path)
    rows = run_reference_fold_with_donor_evidence(
        arrays=reference,
        fold_index=0,
        parameters=parameters(),
        evidence_budget=budget(),
        global_seed=17,
    )
    assert all("heldout_donor_scores" in row for row in rows)
    assert all(len(row["heldout_donor_scores"]) == 4 for row in rows)
