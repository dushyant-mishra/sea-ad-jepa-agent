import pytest

from sea_ad_jepa.qualification.lifecycle import ExperimentRunV1, RunMode, RunState
from sea_ad_jepa.qualification.oracle import (
    ChallengeStatus,
    FrozenQualificationOutputsV1,
    SyntheticOracleTruthV1,
    mark_post_unblinding_retune,
    unblind_oracle,
)


def _run(run_id="run-oracle"):
    return ExperimentRunV1(
        experiment_run_id=run_id,
        protocol_digest="c" * 64,
        mode=RunMode.ZERO_UPDATE_QUALIFICATION,
    )


def _outputs(run_id="run-oracle"):
    return FrozenQualificationOutputsV1(
        run_id=run_id,
        output_digest="d" * 64,
        provenance_receipt_digest="e" * 64,
    )


def _oracle():
    return SyntheticOracleTruthV1(
        realization_id="v77-challenge-001",
        truth_payload=(("z_reg_private", "sealed"), ("b6_level", 3)),
    )


def test_oracle_cannot_unblind_before_ordinary_outputs_are_frozen():
    run = _run()
    run.prepare()
    with pytest.raises(ValueError, match="frozen"):
        unblind_oracle(run, _outputs(), _oracle())


def test_oracle_run_identity_must_match_frozen_outputs():
    run = _run("run-a")
    run.prepare()
    run.freeze_outputs()
    with pytest.raises(ValueError, match="run identity"):
        unblind_oracle(run, _outputs("run-b"), _oracle())


def test_unblinding_records_one_way_receipt_after_frozen_outputs():
    run = _run()
    run.prepare()
    run.freeze_outputs()
    receipt = unblind_oracle(run, _outputs(), _oracle())
    assert receipt.run_id == run.experiment_run_id
    assert receipt.output_digest == "d" * 64
    assert receipt.challenge_status is ChallengeStatus.PROSPECTIVE_SEALED_CHALLENGE
    assert "ORACLE_UNBLINDED" in run.event_names
    assert run.state is RunState.QUALIFICATION_OUTPUTS_FROZEN


def test_post_unblinding_retune_demotes_challenge_to_development_calibration():
    run = _run()
    run.prepare()
    run.freeze_outputs()
    receipt = unblind_oracle(run, _outputs(), _oracle())
    demoted = mark_post_unblinding_retune(receipt, reason="changed score threshold after oracle inspection")
    assert demoted.challenge_status is ChallengeStatus.DEVELOPMENT_CALIBRATION
    assert demoted.retune_reason == "changed score threshold after oracle inspection"


def test_oracle_truth_is_immutable_and_has_no_upstream_callback_surface():
    oracle = _oracle()
    assert not hasattr(oracle, "apply_to_preprocessing")
    assert not hasattr(oracle, "apply_to_model")
    with pytest.raises(Exception):
        oracle.realization_id = "changed"  # type: ignore[misc]
