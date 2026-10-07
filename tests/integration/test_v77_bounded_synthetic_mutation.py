import inspect
from dataclasses import replace

import pytest

from tests.integration.test_v77_canonical_zero_update import _batch, _bindings, _proof


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
    assert receipt["half_life_presentations"] == 1000
    assert receipt["training_authorized"] is False
    assert receipt["production_promotable"] is False


def test_bounded_mutation_rejects_self_consistent_fake_adapter_binding_before_mutation(tmp_path):
    from sea_ad_jepa.qualification import v77_bound_zero_update, v77_bounded_mutation

    real_digest = v77_bound_zero_update.canonical_v77_adapter_source_sha256()
    fake_batch = replace(_batch(real_digest), adapter_digest="0" * 64)
    runtime_digest = v77_bound_zero_update.canonical_v5_runtime_source_sha256()

    with pytest.raises(ValueError, match="adapter source digest"):
        v77_bounded_mutation.run_bounded_synthetic_mutation(
            fake_batch,
            _bindings(fake_batch),
            _proof(fake_batch, runtime_digest),
            runtime_digest,
            8113002,
            tmp_path / "fake-adapter.pt",
        )
    assert not (tmp_path / "fake-adapter.pt").exists()


def test_bounded_mutation_rejects_reuse_of_completed_rehearsal_path(tmp_path):
    from sea_ad_jepa.qualification import v77_bound_zero_update, v77_bounded_mutation

    adapter_digest = v77_bound_zero_update.canonical_v77_adapter_source_sha256()
    batch = _batch(adapter_digest)
    runtime_digest = v77_bound_zero_update.canonical_v5_runtime_source_sha256()
    path = tmp_path / "single-use.pt"
    args = (batch, _bindings(batch), _proof(batch, runtime_digest), runtime_digest, 8113002, path)

    first = v77_bounded_mutation.run_bounded_synthetic_mutation(*args)
    assert first["optimizer_step_after"] == 1
    with pytest.raises(ValueError, match="already exists"):
        v77_bounded_mutation.run_bounded_synthetic_mutation(*args)
