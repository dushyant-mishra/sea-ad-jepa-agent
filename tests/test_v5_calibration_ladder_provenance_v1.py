from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from scripts.agent.evaluate_full104_nonlinear_capacity_from_cache_v1 import (
    load_prior_evidence as load_prior_nonlinear_evidence,
)
from scripts.agent.evaluate_full104_target_panel_capacity_from_cache_v1 import (
    load_prior_evidence as load_prior_panel_evidence,
)
from sea_ad_jepa.v5.control_capacity_calibration_receipt_v1 import (
    ControlCapacityCalibrationReceiptV1,
)
from sea_ad_jepa.v5.full104_census_receipt_v2 import sha256_file
from sea_ad_jepa.v5.full104_control_calibration_cache_v1 import CACHE_ROLE_ID
from sea_ad_jepa.v5.nonlinear_sampling_calibration_authority_v1 import (
    NonlinearCapControlVerdictV1,
)
from sea_ad_jepa.v5.target_panel_sizing_authority_v2 import (
    TargetPanelControlVerdictV2,
)


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class PrecisionStub:
    def __init__(self, digest: str, *, mean: float, lower: float):
        self._digest = digest
        self._mean = mean
        self._lower = lower

    def canonical_digest(self) -> str:
        return self._digest

    def interval(self, matrix, donor_source_code, **kwargs):
        arr = np.asarray(matrix)
        assert arr.shape[1] == 104
        assert np.asarray(donor_source_code).shape == (104,)
        return SimpleNamespace(mean=self._mean, lower_one_sided=self._lower)


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def write_matrix_pair(root: Path, stem: str, shape: tuple[int, int]):
    arr = np.zeros(shape, dtype=np.float64)
    raw = root / f"{stem}.raw.npy"
    replay = root / f"{stem}.replay.npy"
    np.save(raw, arr, allow_pickle=False)
    np.save(replay, arr, allow_pickle=False)
    assert sha256_file(raw) == sha256_file(replay)
    return raw, replay


def panel_bundle(tmp_path: Path):
    cache_root = h("cache")
    precision_root = h("precision")
    planted, replay_planted = write_matrix_pair(tmp_path, "panel-planted", (128, 104))
    shuffled, replay_shuffled = write_matrix_pair(tmp_path, "panel-shuffled", (128, 104))
    capacity = ControlCapacityCalibrationReceiptV1(
        scope_id="TARGET_PANEL_SIZE_CAPACITY_CALIBRATION_V1",
        candidate_value=128,
        calibration_cache_manifest_sha256=cache_root,
        calibration_cache_role_id=CACHE_ROLE_ID,
        raw_planted_evidence_sha256=sha256_file(planted),
        raw_shuffled_evidence_sha256=sha256_file(shuffled),
        precision_root_sha256=precision_root,
        planted_minus_shuffled_mean=0.0,
        planted_minus_shuffled_lower_one_sided=-0.001,
        donor_count=104,
        target_count=128,
        bootstrap_replicates=4096,
        confidence_level_numerator=95,
        confidence_level_denominator=100,
        replay_exact=True,
    )
    verdict = TargetPanelControlVerdictV2(
        target_count=128,
        capacity_receipt_sha256=capacity.canonical_digest(),
        planted_minus_shuffled_lower_one_sided=-0.001,
        replay_exact=True,
        donor_coverage_complete=True,
        bootstrap_finite=True,
    )
    capacity_path = write_json(
        tmp_path / "panel.capacity.json",
        {
            "schema": "V5_CONTROL_CAPACITY_CALIBRATION_RECEIPT_V1",
            **capacity.__dict__,
            "detects_planted_shortcut": capacity.detects_planted_shortcut,
            "receipt_sha256": capacity.canonical_digest(),
        },
    )
    verdict_path = write_json(
        tmp_path / "panel.verdict.json",
        {
            "schema": "V5_TARGET_PANEL_CONTROL_VERDICT_V2",
            **verdict.__dict__,
            "qualified": verdict.qualified,
            "verdict_sha256": verdict.canonical_digest(),
        },
    )
    cache = SimpleNamespace(
        manifest_sha256=cache_root,
        donor_source_code=np.zeros(104, dtype=np.int64),
    )
    precision = PrecisionStub(precision_root, mean=0.0, lower=-0.001)
    return (
        verdict_path,
        capacity_path,
        planted,
        shuffled,
        replay_planted,
        replay_shuffled,
        cache,
        precision,
    )


def nonlinear_bundle(tmp_path: Path):
    cache_root = h("nl-cache")
    precision_root = h("nl-precision")
    planted, replay_planted = write_matrix_pair(tmp_path, "nl-planted", (128, 104))
    shuffled, replay_shuffled = write_matrix_pair(tmp_path, "nl-shuffled", (128, 104))
    capacity = ControlCapacityCalibrationReceiptV1(
        scope_id="NONLINEAR_CAP_CAPACITY_CALIBRATION_V1",
        candidate_value=64,
        calibration_cache_manifest_sha256=cache_root,
        calibration_cache_role_id=CACHE_ROLE_ID,
        raw_planted_evidence_sha256=sha256_file(planted),
        raw_shuffled_evidence_sha256=sha256_file(shuffled),
        precision_root_sha256=precision_root,
        planted_minus_shuffled_mean=0.0,
        planted_minus_shuffled_lower_one_sided=-0.001,
        donor_count=104,
        target_count=128,
        bootstrap_replicates=4096,
        confidence_level_numerator=95,
        confidence_level_denominator=100,
        replay_exact=True,
    )
    verdict = NonlinearCapControlVerdictV1(
        max_cells_per_donor=64,
        capacity_receipt_sha256=capacity.canonical_digest(),
        planted_minus_shuffled_lower_one_sided=-0.001,
        replay_exact=True,
        all_donors_represented=True,
    )
    capacity_path = write_json(
        tmp_path / "nl.capacity.json",
        {
            "schema": "V5_CONTROL_CAPACITY_CALIBRATION_RECEIPT_V1",
            **capacity.__dict__,
            "detects_planted_shortcut": capacity.detects_planted_shortcut,
            "receipt_sha256": capacity.canonical_digest(),
        },
    )
    verdict_path = write_json(
        tmp_path / "nl.verdict.json",
        {
            "schema": "V5_NONLINEAR_CAP_CONTROL_VERDICT_V1",
            **verdict.__dict__,
            "qualified": verdict.qualified,
            "verdict_sha256": verdict.canonical_digest(),
        },
    )
    cache = SimpleNamespace(
        manifest_sha256=cache_root,
        donor_source_code=np.zeros(104, dtype=np.int64),
    )
    precision = PrecisionStub(precision_root, mean=0.0, lower=-0.001)
    return (
        verdict_path,
        capacity_path,
        planted,
        shuffled,
        replay_planted,
        replay_shuffled,
        cache,
        precision,
    )


def test_panel_prior_rung_requires_raw_capacity_and_exact_replay(tmp_path):
    v, c, p, s, rp, rs, cache, precision = panel_bundle(tmp_path)
    out = load_prior_panel_evidence(
        verdict_paths=[v],
        capacity_paths=[c],
        planted_paths=[p],
        shuffled_paths=[s],
        replay_planted_paths=[rp],
        replay_shuffled_paths=[rs],
        cache=cache,
        precision=precision,
    )
    assert tuple(out) == (128,)

    with pytest.raises(SystemExit, match="requires verdict, capacity receipt"):
        load_prior_panel_evidence(
            verdict_paths=[v],
            capacity_paths=[],
            planted_paths=[],
            shuffled_paths=[],
            replay_planted_paths=[],
            replay_shuffled_paths=[],
            cache=cache,
            precision=precision,
        )


def test_panel_forged_verdict_cannot_advance_without_matching_capacity(tmp_path):
    v, c, p, s, rp, rs, cache, precision = panel_bundle(tmp_path)
    payload = json.loads(v.read_text(encoding="utf-8"))
    payload["capacity_receipt_sha256"] = h("forged-capacity")
    verdict = TargetPanelControlVerdictV2(
        **{
            name: payload[name]
            for name in TargetPanelControlVerdictV2.__dataclass_fields__
        }
    )
    payload["verdict_sha256"] = verdict.canonical_digest()
    write_json(v, payload)
    with pytest.raises(ValueError, match="capacity receipt root mismatch"):
        load_prior_panel_evidence(
            verdict_paths=[v],
            capacity_paths=[c],
            planted_paths=[p],
            shuffled_paths=[s],
            replay_planted_paths=[rp],
            replay_shuffled_paths=[rs],
            cache=cache,
            precision=precision,
        )


def test_panel_historical_matrix_cannot_advance_current_cache_ladder(tmp_path):
    v, c, p, s, rp, rs, cache, precision = panel_bundle(tmp_path)
    historical = tmp_path / "historical.npy"
    np.save(historical, np.ones((128, 104), dtype=np.float64), allow_pickle=False)
    with pytest.raises(SystemExit, match="matrix hash mismatch"):
        load_prior_panel_evidence(
            verdict_paths=[v],
            capacity_paths=[c],
            planted_paths=[historical],
            shuffled_paths=[s],
            replay_planted_paths=[rp],
            replay_shuffled_paths=[rs],
            cache=cache,
            precision=precision,
        )


def test_nonlinear_prior_rung_requires_raw_capacity_and_exact_replay(tmp_path):
    v, c, p, s, rp, rs, cache, precision = nonlinear_bundle(tmp_path)
    out = load_prior_nonlinear_evidence(
        verdict_paths=[v],
        capacity_paths=[c],
        planted_paths=[p],
        shuffled_paths=[s],
        replay_planted_paths=[rp],
        replay_shuffled_paths=[rs],
        cache=cache,
        precision=precision,
        target_count=128,
    )
    assert tuple(out) == (64,)

    with pytest.raises(SystemExit, match="requires verdict, capacity receipt"):
        load_prior_nonlinear_evidence(
            verdict_paths=[v],
            capacity_paths=[],
            planted_paths=[],
            shuffled_paths=[],
            replay_planted_paths=[],
            replay_shuffled_paths=[],
            cache=cache,
            precision=precision,
            target_count=128,
        )


def test_nonlinear_historical_matrix_cannot_advance_current_cache_ladder(tmp_path):
    v, c, p, s, rp, rs, cache, precision = nonlinear_bundle(tmp_path)
    historical = tmp_path / "historical-nl.npy"
    np.save(historical, np.ones((128, 104), dtype=np.float64), allow_pickle=False)
    with pytest.raises(SystemExit, match="matrix hash mismatch"):
        load_prior_nonlinear_evidence(
            verdict_paths=[v],
            capacity_paths=[c],
            planted_paths=[historical],
            shuffled_paths=[s],
            replay_planted_paths=[rp],
            replay_shuffled_paths=[rs],
            cache=cache,
            precision=precision,
            target_count=128,
        )
