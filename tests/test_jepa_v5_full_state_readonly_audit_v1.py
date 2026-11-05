"""Read-only synthetic CPU tensor checkpoint tests. NO optimizer.step or training.

Manually seeded Adam moment fixtures are NOT evidence that an optimizer ran.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from io import BytesIO

import pytest
import torch

from scripts.v5 import jepa_v5_full_state_readonly_audit_v1 as c


class TinyStudent(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.value_encoder = torch.nn.Linear(3, 2)
        self.identity_encoder = torch.nn.Linear(2, 2)

    def forward(self, x):  # pragma: no cover - no forward execution here
        raise AssertionError("V5 READONLY TEST MUST NOT DO A FORWARD PASS")


def fixture(*, updates=1):
    online = TinyStudent()
    teacher = deepcopy(online).eval()
    for p in teacher.parameters():
        p.requires_grad_(False)
    predictor = torch.nn.Linear(2, 1)
    opt = torch.optim.AdamW(
        list(online.parameters()) + list(predictor.parameters()),
        lr=1e-3, betas=(0.9, 0.999), eps=1e-8)
    # If any accidental training call reaches this fixture, fail immediately.
    opt.step = lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("NEVER RUN AN OPTIMIZER STEP"))
    if updates:
        for group in opt.param_groups:
            for p in group["params"]:
                opt.state[p] = {
                    "step": torch.tensor(float(updates)),
                    "exp_avg": torch.zeros_like(p),
                    "exp_avg_sq": torch.ones_like(p),
                }
    meta = {
        "schema": c.SCHEMA, "run_id": "fake-v5-cpu-inspection",
        "completed_updates": updates, "ema_updates": updates,
        "presentations_seen": updates * 8, "keyed_run_seed": 73,
        "gene_axis_sha256": "a" * 64, "source_rights_sha256": "b" * 64,
        "panel_sha256": "c" * 64, "config_sha256": "d" * 64,
        "keyed_philox_contract_sha256": "e" * 64,
        "source_manifest_sha256": "f" * 64,
        "training_authorized": False, "execution_authorized": False,
    }
    return online, teacher, predictor, opt, meta


def capture(*, updates=1):
    online, teacher, predictor, opt, meta = fixture(updates=updates)
    return c.capture_readonly_bundle(online=online, teacher=teacher,
                                     predictor=predictor, optimizer=opt,
                                     metadata=meta)


@pytest.mark.parametrize("updates", [0, 1, 3])
def test_readonly_cpu_snapshot_complete_adam_and_byte_sha(updates):
    bundle = capture(updates=updates)
    r = c.verify_readonly_bundle(bundle)
    assert r["completed_updates"] == updates
    assert r["optimizer_tensor_count"] == (0 if updates == 0 else 6)
    assert r["actual_step_or_bitwise_resume_proved"] is False
    assert r["training_authorized"] is False
    assert r["biological_health_proved"] is False
    assert "online.value_encoder.weight" in bundle["parameter_names"]
    assert set(bundle["parameter_layout"]) == set(bundle["parameter_names"])
    raw, digest = c.to_verified_bytes(bundle)
    loaded, report = c.read_verified_bytes(raw, expected_sha256=digest)
    assert loaded["metadata"] == bundle["metadata"]
    assert report == r
    assert "teacher" in loaded["modules"]
    assert loaded["optimizer"]["param_groups"]
    assert loaded["rng_state"]["keyed_run_seed"] == 73
    assert report["execution_authorized"] is False


@pytest.mark.parametrize("mutator,expect", [
    (lambda b: b["optimizer"]["state"].pop(next(iter(b["optimizer"]["state"]))),
     "ADAM_STATE_CARDINALITY"),
    (lambda b: b["optimizer"]["state"][0].pop("exp_avg"),
     "ADAM_SLOT_FIELDS"),
    (lambda b: b["optimizer"]["state"][0].update(step=torch.tensor(2.0)),
     "ADAM_STEP_NOT_EQUAL_COMPLETED"),
    (lambda b: b["optimizer"]["state"][0].update(exp_avg=torch.ones(99)),
     "TENSOR_SHAPE_MISMATCH"),
    (lambda b: b["optimizer"]["state"][0].update(
        exp_avg_sq=torch.full_like(b["optimizer"]["state"][0]["exp_avg_sq"], -1)),
     "ADAM_SECOND_MOMENT_NEGATIVE"),
    (lambda b: b["optimizer"]["state"][0].update(
        exp_avg=torch.full_like(b["optimizer"]["state"][0]["exp_avg"], float("nan"))),
     "NONFINITE_TENSOR"),
    (lambda b: b["parameter_layout"]["online.value_encoder.weight"].update(
        optimizer_param_id=999), "OPTIMIZER_PARAM_ID_TO_NAME_MISMATCH"),
    (lambda b: b["parameter_layout"]["online.value_encoder.weight"].update(
        shape=[999,999]), "PARAMETER_LAYOUT_MISMATCH"),
    (lambda b: b["parameter_layout"].pop("online.value_encoder.weight"),
     "PARAMETER_LAYOUT_COVERAGE"),
    (lambda b: b["metadata"].update(ema_updates=0), "EMA_COUNTER_DIVERGED"),
    (lambda b: b["metadata"].update(source_rights_sha256="bad"),
     "SOURCE_RIGHTS_SHA256_INVALID"),
    (lambda b: b["metadata"].update(training_authorized=True),
     "AUTHORITY_PROMOTION"),
    (lambda b: b["rng_state"].update(keyed_run_seed=999),
     "RNG_STATE_MISMATCH"),
])
def test_missing_or_mutated_optimizer_model_rights_never_passes(mutator, expect):
    bundle = capture()
    mutator(bundle)
    with pytest.raises(c.FullStateRefusal, match=expect):
        c.verify_readonly_bundle(bundle)


def test_bytes_sha_change_always_refused_before_safe_load():
    raw, digest = c.to_verified_bytes(capture())
    bad = raw[:-1] + bytes([raw[-1] ^ 0xFF])
    with pytest.raises(c.FullStateRefusal, match="CHECKPOINT_SHA_CHANGED"):
        c.read_verified_bytes(bad, expected_sha256=digest)


def test_invalid_optimizer_state_shape_refused_at_capture_not_saved():
    online, teacher, predictor, opt, meta = fixture()
    p = opt.param_groups[0]["params"][0]
    opt.state[p]["exp_avg"] = torch.zeros(7)
    with pytest.raises(c.FullStateRefusal, match="TENSOR_SHAPE_MISMATCH"):
        c.capture_readonly_bundle(online=online, teacher=teacher,
                                  predictor=predictor, optimizer=opt,
                                  metadata=meta)


def test_uninitialized_adam_in_successful_update_refused():
    online, teacher, predictor, opt, meta = fixture()
    opt.state.clear()
    with pytest.raises(c.FullStateRefusal, match="OPTIMIZER_STATE_COVERAGE"):
        c.capture_readonly_bundle(online=online, teacher=teacher,
                                  predictor=predictor, optimizer=opt,
                                  metadata=meta)


def test_teacher_gradient_or_train_mode_refused_before_state_capture():
    online, teacher, predictor, opt, meta = fixture()
    teacher.train()
    with pytest.raises(c.FullStateRefusal, match="TEACHER_NOT_EVAL"):
        c.capture_readonly_bundle(online=online, teacher=teacher,
                                  predictor=predictor, optimizer=opt,
                                  metadata=meta)
    teacher.eval()
    next(teacher.parameters()).grad = torch.ones_like(next(teacher.parameters()))
    with pytest.raises(c.FullStateRefusal, match="TEACHER_GRADIENT_OR_MUTATION"):
        c.capture_readonly_bundle(online=online, teacher=teacher,
                                  predictor=predictor, optimizer=opt,
                                  metadata=meta)


def test_missing_expression_value_encoder_from_optimizer_refused():
    online, teacher, predictor, opt, meta = fixture()
    opt.param_groups[0]["params"] = [
        p for p in opt.param_groups[0]["params"]
        if p is not online.value_encoder.weight]
    with pytest.raises(c.FullStateRefusal, match="OPTIMIZER_PARAM_GROUP_COVERAGE"):
        c.capture_readonly_bundle(online=online, teacher=teacher,
                                  predictor=predictor, optimizer=opt,
                                  metadata=meta)


def test_duplicate_optimizer_param_id_refused_in_loaded_bundle():
    bundle = capture()
    group = bundle["optimizer"]["param_groups"][0]
    group["params"][-1] = group["params"][0]
    with pytest.raises(c.FullStateRefusal, match="OPTIMIZER_PARAM_IDS_DUPLICATE_OR_MISSING"):
        c.verify_readonly_bundle(bundle)


def test_safe_load_refuses_missing_adam_even_if_new_file_sha_matches():
    bundle = capture()
    bundle["optimizer"]["state"][0].pop("exp_avg_sq")
    bio = BytesIO()
    torch.save(bundle, bio)
    raw = bio.getvalue()
    with pytest.raises(c.FullStateRefusal, match="ADAM_SLOT_FIELDS"):
        c.read_verified_bytes(raw, expected_sha256=sha256(raw).hexdigest())


def test_snapshot_does_not_mutate_teacher_student_or_optimizer():
    online, teacher, predictor, opt, meta = fixture()
    before = {k: t.clone() for k,t in online.state_dict().items()}
    before_steps = [float(s["step"].item()) for s in opt.state.values()]
    c.capture_readonly_bundle(online=online, teacher=teacher,
                              predictor=predictor, optimizer=opt,
                              metadata=meta)
    assert all(torch.equal(before[k], v) for k,v in online.state_dict().items())
    assert before_steps == [float(s["step"].item()) for s in opt.state.values()]
    assert not any(p.grad is not None for p in teacher.parameters())



def test_physically_read_all_supplied_gradient_tensors_including_expression_value_encoder():
    online, teacher, predictor, _, _ = fixture(updates=0)
    for p in list(online.parameters()) + list(predictor.parameters()):
        p.grad = torch.ones_like(p) * 0.5
    seen = c.inspect_existing_trainable_gradients(
        online=online, teacher=teacher, predictor=predictor, update_index=1)
    assert seen["all_trainable_tensor_count"] == 6
    assert seen["status_counts"]["NONZERO_FINITE"] == 6
    assert seen["per_tensor"]["online.value_encoder.weight"]["status"] == "NONZERO_FINITE"
    assert seen["per_tensor"]["online.value_encoder.weight"]["l2_norm_float64"] > 0
    assert seen["teacher_gradients_reported"] == []
    assert seen["intended_loss_or_panel_identity_proved"] is False
    assert seen["representation_learned_biology_proved"] is False
    assert seen["optimizer_step_executed_by_this_inspection"] is False


def test_gradient_onset_missing_exact_zero_nonfinite_are_not_silently_dropped():
    online, teacher, predictor, _, _ = fixture(updates=0)
    params = list(online.parameters()) + list(predictor.parameters())
    params[0].grad = None
    params[1].grad = torch.zeros_like(params[1])
    params[2].grad = torch.full_like(params[2], float("nan"))
    for p in params[3:]:
        p.grad = torch.ones_like(p)
    # Record the teacher violation as evidence, not as a fake passing probe.
    next(teacher.parameters()).grad = torch.ones_like(next(teacher.parameters()))
    seen = c.inspect_existing_trainable_gradients(
        online=online, teacher=teacher, predictor=predictor, update_index=2)
    assert seen["status_counts"] == {
        "MISSING": 1, "NONFINITE": 1, "EXACT_ZERO": 1, "NONZERO_FINITE": 3,
    }
    assert seen["per_tensor"]["online.value_encoder.weight"]["status"] == "MISSING"
    assert seen["per_tensor"]["online.value_encoder.bias"]["status"] == "EXACT_ZERO"
    assert seen["teacher_gradients_reported"]
    assert seen["training_authorized"] is False


def test_tiny_positive_gradient_stays_positive_without_threshold():
    online, teacher, predictor, _, _ = fixture(updates=0)
    p = online.value_encoder.weight
    p.grad = torch.full_like(p, 1e-18)
    result = c.inspect_existing_trainable_gradients(
        online=online, teacher=teacher, predictor=predictor, update_index=1)
    assert result["per_tensor"]["online.value_encoder.weight"]["status"] == "NONZERO_FINITE"
    assert result["per_tensor"]["online.value_encoder.weight"]["l2_norm_float64"] > 0
    assert result["per_tensor"]["online.value_encoder.weight"]["nonzero_elements"] == p.numel()


def test_gradient_probe_rejects_fake_update_or_mismatched_grad_shape():
    online, teacher, predictor, _, _ = fixture(updates=0)
    with pytest.raises(c.FullStateRefusal, match="GRADIENT_PROBE_UPDATE"):
        c.inspect_existing_trainable_gradients(
            online=online, teacher=teacher, predictor=predictor, update_index=0)
    online.value_encoder.weight.requires_grad_(False)
    with pytest.raises(c.FullStateRefusal, match="GRADIENT_PARAMETER_INVALID"):
        c.inspect_existing_trainable_gradients(
            online=online, teacher=teacher, predictor=predictor, update_index=1)
