import inspect
import json
from dataclasses import replace

import pytest

from tests.integration.test_v77_canonical_zero_update import _batch, _bindings, _proof


def _run_marker(path, batch):
    from sea_ad_jepa.qualification import v77_bounded_mutation

    return v77_bounded_mutation.rehearsal_run_receipt_path(path, batch.experiment_run_id)


def test_bounded_mutation_surface_matches_preregistered_contract():
    from sea_ad_jepa.qualification import v77_bounded_mutation

    assert v77_bounded_mutation.HALF_LIFE_PRESENTATIONS == 1000
    assert v77_bounded_mutation.PRESENTATIONS_PER_SUCCESSFUL_REHEARSAL == 2
    assert (
        v77_bounded_mutation.SUCCESS_VERDICT
        == "PASS__ONE_SYNTHETIC_GUARDED_UPDATE_PHYSICALLY_BOUND__NON_PRODUCTION"
    )

    parameters = inspect.signature(v77_bounded_mutation.run_bounded_synthetic_mutation).parameters
    assert tuple(parameters) == (
        "batch",
        "physical_bindings",
        "q_safety_proof",
        "runtime_source_sha256",
        "init_seed",
        "persistence_path",
    )


def test_bounded_mutation_executes_exactly_one_guarded_step_and_typed_reload(tmp_path):
    from sea_ad_jepa.qualification import v77_bound_zero_update, v77_bounded_mutation

    adapter_digest = v77_bound_zero_update.canonical_v77_adapter_source_sha256()
    batch = _batch(adapter_digest)
    runtime_digest = v77_bound_zero_update.canonical_v5_runtime_source_sha256()
    path = tmp_path / "v77-bounded-mutation-continuation.pt"

    receipt = v77_bounded_mutation.run_bounded_synthetic_mutation(
        batch,
        _bindings(batch),
        _proof(batch, runtime_digest),
        runtime_digest,
        8113002,
        path,
    )

    print("V77_BOUNDED_MUTATION_RECEIPT=" + json.dumps(receipt, sort_keys=True))
    assert receipt["verdict"] == v77_bounded_mutation.SUCCESS_VERDICT
    assert receipt["optimizer_step_before"] == 0
    assert receipt["optimizer_step_after"] == 1
    assert receipt["teacher_presentations_before"] == 0
    assert receipt["teacher_presentations_after"] == 2
    assert receipt["online_parameters_changed"] is True
    assert receipt["predictor_parameters_changed"] is True
    assert receipt["teacher_parameters_changed"] is True
    assert receipt["typed_continuation_persisted"] is True
    assert receipt["deterministic_reload_verified"] is True
    assert path.is_file()
    assert len(receipt["typed_continuation_sha256"]) == 64
    assert len(receipt["completed_guard_receipt_digest"]) == 64
    assert len(receipt["presentation_ema_completion_proof_digest"]) == 64
    assert receipt["adapter_source_sha256"] == adapter_digest
    assert len(receipt["mutation_runtime_source_sha256"]) == 64
    for component in ("online", "predictor", "teacher", "optimizer", "checkpoint"):
        before = receipt[f"{component}_digest_before"]
        after = receipt[f"{component}_digest_after"]
        assert len(before) == 64
        assert len(after) == 64
        assert before != after
    assert receipt["restored_checkpoint_digest"] == receipt["checkpoint_digest_after"]
    assert receipt["restored_online_digest"] == receipt["online_digest_after"]
    assert receipt["restored_predictor_digest"] == receipt["predictor_digest_after"]
    assert receipt["restored_teacher_digest"] == receipt["teacher_digest_after"]
    assert receipt["restored_optimizer_digest"] == receipt["optimizer_digest_after"]
    assert receipt["half_life_presentations"] == 1000
    assert receipt["training_authorized"] is False
    assert receipt["production_promotable"] is False
    marker = _run_marker(path, batch)
    assert marker.is_file()
    marker_payload = json.loads(marker.read_text(encoding="utf-8"))
    assert marker_payload["verdict"] == receipt["verdict"]
    assert marker_payload["experiment_run_id"] == batch.experiment_run_id


def test_bounded_mutation_rejects_self_consistent_fake_adapter_binding_before_mutation_and_preserves_failure(tmp_path):
    from sea_ad_jepa.qualification import v77_bound_zero_update, v77_bounded_mutation

    real_digest = v77_bound_zero_update.canonical_v77_adapter_source_sha256()
    fake_batch = replace(_batch(real_digest), adapter_digest="0" * 64)
    runtime_digest = v77_bound_zero_update.canonical_v5_runtime_source_sha256()
    path = tmp_path / "fake-adapter.pt"

    with pytest.raises(ValueError, match="adapter source digest"):
        v77_bounded_mutation.run_bounded_synthetic_mutation(
            fake_batch,
            _bindings(fake_batch),
            _proof(fake_batch, runtime_digest),
            runtime_digest,
            8113002,
            path,
        )
    assert not path.exists()
    failure = json.loads(_run_marker(path, fake_batch).read_text(encoding="utf-8"))
    assert failure["verdict"] == "FAIL__NO_COMPLETED_MUTATION_CONTINUATION"
    assert failure["experiment_run_id"] == fake_batch.experiment_run_id
    assert failure["training_authorized"] is False
    assert failure["production_promotable"] is False


def test_bounded_mutation_rejects_wrong_runtime_and_wrong_consumed_values_before_mutation(tmp_path):
    from sea_ad_jepa.qualification import v77_bound_zero_update, v77_bounded_mutation

    adapter_digest = v77_bound_zero_update.canonical_v77_adapter_source_sha256()
    runtime_digest = v77_bound_zero_update.canonical_v5_runtime_source_sha256()

    runtime_batch = replace(_batch(adapter_digest), experiment_run_id="v77-bounded-wrong-runtime")
    runtime_path = tmp_path / "wrong-runtime.pt"
    with pytest.raises(ValueError, match="runtime source digest"):
        v77_bounded_mutation.run_bounded_synthetic_mutation(
            runtime_batch,
            _bindings(runtime_batch),
            _proof(runtime_batch, runtime_digest),
            "f" * 64,
            8113002,
            runtime_path,
        )
    assert not runtime_path.exists()
    assert _run_marker(runtime_path, runtime_batch).is_file()

    values_batch = replace(_batch(adapter_digest), experiment_run_id="v77-bounded-wrong-values")
    bindings = list(_bindings(values_batch))
    wrong = "f" * 64
    bindings[0] = replace(
        bindings[0],
        authenticated_values_sha256=wrong,
        consumed_values_sha256=wrong,
    )
    values_path = tmp_path / "wrong-values.pt"
    with pytest.raises(ValueError, match="consumed values.*executed batch"):
        v77_bounded_mutation.run_bounded_synthetic_mutation(
            values_batch,
            tuple(bindings),
            _proof(values_batch, runtime_digest),
            runtime_digest,
            8113002,
            values_path,
        )
    assert not values_path.exists()
    assert _run_marker(values_path, values_batch).is_file()


def test_bounded_mutation_rejects_q_safety_proof_from_another_batch_before_mutation(tmp_path):
    from sea_ad_jepa.qualification import v77_bound_zero_update, v77_bounded_mutation

    adapter_digest = v77_bound_zero_update.canonical_v77_adapter_source_sha256()
    batch = replace(_batch(adapter_digest), experiment_run_id="v77-bounded-q-replay")
    runtime_digest = v77_bound_zero_update.canonical_v5_runtime_source_sha256()
    replayed = replace(_proof(batch, runtime_digest), batch_scientific_identity_digest="0" * 64)
    path = tmp_path / "q-replay.pt"

    with pytest.raises(ValueError, match="batch|scientific|identity|q-safety|proof"):
        v77_bounded_mutation.run_bounded_synthetic_mutation(
            batch,
            _bindings(batch),
            replayed,
            runtime_digest,
            8113002,
            path,
        )
    assert not path.exists()
    assert _run_marker(path, batch).is_file()


def test_bounded_mutation_rejects_reuse_of_same_run_identity_even_with_different_path(tmp_path):
    from sea_ad_jepa.qualification import v77_bound_zero_update, v77_bounded_mutation

    adapter_digest = v77_bound_zero_update.canonical_v77_adapter_source_sha256()
    batch = _batch(adapter_digest)
    runtime_digest = v77_bound_zero_update.canonical_v5_runtime_source_sha256()
    first_path = tmp_path / "single-use.pt"
    second_path = tmp_path / "attempted-second-step.pt"
    first = v77_bounded_mutation.run_bounded_synthetic_mutation(
        batch, _bindings(batch), _proof(batch, runtime_digest), runtime_digest, 8113002, first_path
    )
    assert first["optimizer_step_after"] == 1
    with pytest.raises(ValueError, match="run identity|already.*completed|already.*recorded"):
        v77_bounded_mutation.run_bounded_synthetic_mutation(
            batch, _bindings(batch), _proof(batch, runtime_digest), runtime_digest, 8113002, second_path
        )
    assert not second_path.exists()
