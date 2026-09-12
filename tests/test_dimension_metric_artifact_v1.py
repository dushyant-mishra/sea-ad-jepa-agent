import copy
import pytest

from sea_ad_jepa.v5.dimension_metric_artifact_v1 import (
    seal_dimension_metric_artifact,
    validate_dimension_metric_artifact,
    seal_dimension_selection_artifact,
    validate_dimension_selection_artifact,
)


def test_shared_metrics_bind_full104_and_execution_receipt():
    rows = [{"rank": 1, "held_donor_cross_view_mean": 0.7}]
    env = seal_dimension_metric_artifact(
        kind="shared",
        rows=rows,
        full104_dimension_input_artifact_sha256="a" * 64,
        execution_receipt_sha256="b" * 64,
    )
    out = validate_dimension_metric_artifact(
        env,
        kind="shared",
        expected_full104_dimension_input_artifact_sha256="a" * 64,
        expected_execution_receipt_sha256="b" * 64,
    )
    assert out["rows"] == rows
    assert out["population_mode"] == "FULL_READER_FIT_STREAM"
    assert out["training_authorized"] is False


def test_private_metrics_require_frozen_shared_selection_parent():
    with pytest.raises(ValueError, match="shared selection"):
        seal_dimension_metric_artifact(
            kind="private",
            rows=[{"rank": 1}],
            full104_dimension_input_artifact_sha256="a" * 64,
            execution_receipt_sha256="b" * 64,
        )
    env = seal_dimension_metric_artifact(
        kind="private",
        rows=[{"rank": 1}],
        full104_dimension_input_artifact_sha256="a" * 64,
        execution_receipt_sha256="b" * 64,
        shared_selection_artifact_sha256="c" * 64,
    )
    out = validate_dimension_metric_artifact(
        env,
        kind="private",
        expected_full104_dimension_input_artifact_sha256="a" * 64,
        expected_execution_receipt_sha256="b" * 64,
        expected_shared_selection_artifact_sha256="c" * 64,
    )
    assert out["kind"] == "private"


def test_shared_or_observation_metrics_cannot_smuggle_private_parent():
    with pytest.raises(ValueError, match="only private"):
        seal_dimension_metric_artifact(
            kind="shared",
            rows=[{"rank": 1}],
            full104_dimension_input_artifact_sha256="a" * 64,
            execution_receipt_sha256="b" * 64,
            shared_selection_artifact_sha256="c" * 64,
        )


def test_metric_parent_substitution_fails():
    env = seal_dimension_metric_artifact(
        kind="observation",
        rows=[{"rank": 1}],
        full104_dimension_input_artifact_sha256="a" * 64,
        execution_receipt_sha256="b" * 64,
    )
    with pytest.raises(RuntimeError, match="PARENT_MISMATCH"):
        validate_dimension_metric_artifact(
            env,
            kind="observation",
            expected_full104_dimension_input_artifact_sha256="f" * 64,
            expected_execution_receipt_sha256="b" * 64,
        )


def test_selection_artifact_binds_exact_metric_artifact():
    selection = {"D_shared": 2, "terminal": "PASS_D_SHARED_SELECTED", "training_authorized": False}
    env = seal_dimension_selection_artifact(
        kind="shared",
        selection=selection,
        metric_artifact_sha256="d" * 64,
    )
    out = validate_dimension_selection_artifact(
        env,
        kind="shared",
        expected_metric_artifact_sha256="d" * 64,
    )
    assert out == selection


def test_selection_payload_tamper_fails():
    env = seal_dimension_selection_artifact(
        kind="observation",
        selection={"D_obs": 3, "terminal": "PASS_D_OBS_SELECTED", "training_authorized": False},
        metric_artifact_sha256="e" * 64,
    )
    bad = copy.deepcopy(env)
    bad["payload"]["D_obs"] = 4
    with pytest.raises(RuntimeError, match="DIGEST_MISMATCH"):
        validate_dimension_selection_artifact(
            bad,
            kind="observation",
            expected_metric_artifact_sha256="e" * 64,
        )
