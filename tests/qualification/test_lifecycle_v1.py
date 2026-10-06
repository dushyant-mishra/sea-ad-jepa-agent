import pytest

from sea_ad_jepa.qualification.lifecycle import (
    ExperimentRunV1,
    LifecycleError,
    RunMode,
    RunState,
)


def _zero_run(run_id="run-001"):
    return ExperimentRunV1(
        experiment_run_id=run_id,
        protocol_digest="a" * 64,
        mode=RunMode.ZERO_UPDATE_QUALIFICATION,
    )


def _mutation_run(run_id="run-002"):
    return ExperimentRunV1(
        experiment_run_id=run_id,
        protocol_digest="b" * 64,
        mode=RunMode.BOUNDED_MUTATION_REHEARSAL,
    )


def test_zero_update_lifecycle_reaches_verified_without_mutation_states():
    run = _zero_run()
    run.prepare()
    run.freeze_outputs()
    run.verify()
    assert run.state is RunState.VERIFIED
    assert run.event_names == ("PREPARED", "QUALIFICATION_OUTPUTS_FROZEN", "VERIFIED")


def test_illegal_jump_to_ema_without_mutation_is_rejected():
    run = _mutation_run()
    run.prepare()
    with pytest.raises(LifecycleError, match="EMA"):
        run.record_ema_applied()


def test_zero_update_mode_rejects_mutation_event():
    run = _zero_run()
    run.prepare()
    with pytest.raises(LifecycleError, match="zero-update"):
        run.record_mutation()


def test_partial_failure_preserves_last_proven_state_and_is_terminal():
    run = _mutation_run()
    run.prepare()
    run.record_mutation()
    failure = run.fail("checkpoint write failed")
    assert failure.last_proven_state is RunState.MUTATED
    assert failure.reason == "checkpoint write failed"
    assert run.state is RunState.FAILED
    with pytest.raises(LifecycleError, match="terminal"):
        run.record_ema_applied()


def test_restart_verification_failure_never_becomes_verified():
    run = _mutation_run()
    run.prepare()
    run.record_mutation()
    run.record_ema_applied()
    run.record_checkpointed()
    run.freeze_outputs()
    run.fail("restart verification failed")
    assert run.state is RunState.FAILED
    with pytest.raises(LifecycleError):
        run.verify()


def test_event_from_different_run_id_is_rejected():
    run = _zero_run("run-a")
    run.prepare()
    with pytest.raises(LifecycleError, match="run identity"):
        run.freeze_outputs(event_run_id="run-b")


def test_retry_is_explicit_child_run_with_parent_and_reason():
    run = _zero_run("run-parent")
    run.prepare()
    run.fail("readout failed")
    child = run.retry_as_child("run-child", reason="correct readout defect")
    assert child.parent_run_id == "run-parent"
    assert child.retry_reason == "correct readout defect"
    assert child.state is RunState.NOT_STARTED


def test_no_arbitrary_set_state_escape_hatch_exists():
    run = _zero_run()
    assert not hasattr(run, "set_state")
