"""Adversarial read-only CPU snapshot -> fake-byte V2 journal integration.

No forward/backward, optimizer.step, model restore, GPU, real data or training.
Adam slots are assigned manually to tiny synthetic PyTorch modules.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import os

import pytest
import torch

from scripts.v5 import jepa_v5_structured_journal_preflight_v1 as bridge
from scripts.v5 import jepa_v5_full_state_readonly_audit_v1 as state
from scripts.v5 import jepa_synth2048_attempt_journal_v2 as journal
from tests.test_jepa_v5_full_state_readonly_audit_v1 import fixture

RUN_ID = "v5-synthetic-bridge"
PANEL = "c" * 64
CONFIG = "d" * 64
RIGHTS = "b" * 64
GENES = "a" * 64
SOURCES = "f" * 64
PHILOX = "e" * 64
SEED = 73
METRICS = {
    "cell_centered_energy": .25,
    "same_gene_cross_cell_variance": .50,
    "same_cell_expression_shuffle_delta": .125,
}


def fake_bundle(u):
    online, teacher, predictor, optimizer, metadata = fixture(updates=u)
    metadata["run_id"] = RUN_ID
    return state.capture_readonly_bundle(
        online=online, teacher=teacher, predictor=predictor,
        optimizer=optimizer, metadata=metadata)


def bytes_of(bundle):
    output = BytesIO()
    torch.save(bundle, output)
    return output.getvalue()


def fake_bytes(u):
    return state.to_verified_bytes(fake_bundle(u))[0]


def probe(u, raw, metrics=None, panel=PANEL):
    values = dict(METRICS)
    if metrics:
        values.update(metrics)
    return {
        "state_update": u,
        "state_payload_sha256": sha256(raw).hexdigest(),
        "probe_panel_sha256": panel,
        "operator_homogeneous_eval_mode": True,
        "identical_gene_sets": True,
        "metrics": values,
        "cell_distinct_row_count": 1 if values["cell_centered_energy"] == 0 else 64,
        "probe_cells": 64,
        "nonfinite_values": 0,
        "measurement_origin": "CALLER_REPORTED__NOT_PHYSICALLY_PROVED",
    }


def open_synthetic(tmp_path, horizon=3):
    root, backup = tmp_path / "fake-run", tmp_path / "external-head"
    raw = fake_bytes(0)
    outcome = bridge.open_synthetic_journal(
        root=root, custody=backup, run_id=RUN_ID, horizon=horizon,
        panel_sha256=PANEL, config_sha256=CONFIG,
        rights_sha256=RIGHTS, gene_axis_sha256=GENES,
        source_manifest_sha256=SOURCES, philox_contract_sha256=PHILOX,
        keyed_run_seed=SEED, state_bytes=raw, reported_probe=probe(0, raw))
    return root, backup, outcome


def submit(root, backup, u, raw, supplied_probe=None, **overrides):
    args = {
        "expected_gene_axis_sha256": GENES,
        "expected_source_manifest_sha256": SOURCES,
        "expected_philox_contract_sha256": PHILOX,
        "expected_keyed_run_seed": SEED,
    }
    args.update(overrides)
    return bridge.commit_synthetic_preflight(
        root=root, custody=backup, update=u,
        state_bytes=raw, reported_probe=supplied_probe or probe(u, raw),
        **args)


def test_u0_and_every_success_hold_named_adam_model_teacher_and_state_digest(tmp_path):
    root, backup, opened = open_synthetic(tmp_path, horizon=2)
    assert opened["status"] == "SYNTHETIC_U0_STRUCTURED_BYTES_RECORDED"
    assert opened["state"]["optimizer_tensor_count"] == 0
    assert opened["state"]["has_expression_value_encoder"] is True
    assert opened["state"]["resume_authorized"] is False
    for u in (1, 2):
        journal.begin_attempt(root, backup, update=u)
        raw = fake_bytes(u)
        result = submit(root, backup, u, raw)
        assert result["journal"]["state_sha256"] == sha256(raw).hexdigest()
        assert result["state"]["optimizer_tensor_count"] == 6
        assert result["state"]["has_expression_value_encoder"] is True
        assert result["biological_health_proved"] is False
        assert result["optimizer_step_executed_by_bridge"] is False
        assert (root / f"u{u:05d}.state.bin").read_bytes() == raw
        inspection = bridge.inspect_stored_structured_snapshot(
            root=root, custody=backup, update=u,
            expected_gene_axis_sha256=GENES,
            expected_source_manifest_sha256=SOURCES,
            expected_philox_contract_sha256=PHILOX,
            expected_keyed_run_seed=SEED)
        assert inspection["state"]["state_update"] == u
        assert inspection["resume_authorized"] is False
    outcome = journal.close_run(root, backup)
    assert outcome["status"] == "COMPLETE_REPORTED_ONLY"
    report = journal.inspect_journal(root, backup)
    assert report["last_reported_probe_pass_checkpoint_update"] == 2
    assert report["actual_neural_health_proved"] is False
    assert report["resume_authorized"] is False


@pytest.mark.parametrize("damage", [
    "missing_adam_exp_avg", "missing_adam_tensor",
    "wrong_adam_step", "wrong_adam_shape",
    "wrong_update_count", "wrong_ema_count",
    "wrong_rights", "wrong_config", "wrong_run_id",
    "wrong_gene_axis", "wrong_source_manifest",
    "wrong_philox_contract", "wrong_keyed_seed",
    "missing_value_encoder", "teacher_wrong_shape",
])
def test_corrupt_or_incompatible_state_refused_before_any_state_or_telemetry_write(
        tmp_path, damage):
    root, backup, _ = open_synthetic(tmp_path)
    journal.begin_attempt(root, backup, update=1)
    bundle = fake_bundle(1)
    if damage == "missing_adam_exp_avg":
        bundle["optimizer"]["state"][0].pop("exp_avg")
    elif damage == "missing_adam_tensor":
        bundle["optimizer"]["state"].pop(0)
    elif damage == "wrong_adam_step":
        bundle["optimizer"]["state"][0]["step"] = torch.tensor(2.0)
    elif damage == "wrong_adam_shape":
        bundle["optimizer"]["state"][0]["exp_avg"] = torch.zeros(123)
    elif damage == "wrong_update_count":
        bundle["metadata"]["completed_updates"] = 2
        bundle["metadata"]["ema_updates"] = 2
        for item in bundle["optimizer"]["state"].values():
            item["step"] = torch.tensor(2.0)
    elif damage == "wrong_ema_count":
        bundle["metadata"]["ema_updates"] = 2
    elif damage == "wrong_rights":
        bundle["metadata"]["source_rights_sha256"] = "1" * 64
    elif damage == "wrong_config":
        bundle["metadata"]["config_sha256"] = "1" * 64
    elif damage == "wrong_run_id":
        bundle["metadata"]["run_id"] = "different-run"
    elif damage == "wrong_gene_axis":
        bundle["metadata"]["gene_axis_sha256"] = "1" * 64
    elif damage == "wrong_source_manifest":
        bundle["metadata"]["source_manifest_sha256"] = "1" * 64
    elif damage == "wrong_philox_contract":
        bundle["metadata"]["keyed_philox_contract_sha256"] = "1" * 64
    elif damage == "wrong_keyed_seed":
        bundle["metadata"]["keyed_run_seed"] = 72
        bundle["rng_state"]["keyed_run_seed"] = 72
    elif damage == "missing_value_encoder":
        # A different but otherwise structurally valid model is inadmissible.
        bundle["parameter_names"].remove("online.value_encoder.weight")
        bundle["parameter_layout"].pop("online.value_encoder.weight")
        del bundle["modules"]["online"]["value_encoder.weight"]
        # Reconcile fake optimizer ID coverage to leave the higher-level
        # expression-encoder requirement as the intended diagnostic.
    elif damage == "teacher_wrong_shape":
        bundle["modules"]["teacher"]["value_encoder.weight"] = torch.zeros(9, 9)
    raw = bytes_of(bundle)
    with pytest.raises((state.FullStateRefusal, bridge.StructuredJournalRefusal)):
        submit(root, backup, 1, raw)
    assert not (root / "u00001.state.bin").exists(), damage
    assert not (root / "u00001.telemetry.json").exists(), damage
    assert journal.inspect_journal(root, backup)["status"].startswith(
        "TERMINATED_UNEXPECTEDLY")
    # After refused evidence, the attempt may still record an actually
    # valid synthetic outcome; refused preflight never manufactured one.
    good = fake_bytes(1)
    assert submit(root, backup, 1, good)["journal"]["status"] == "UPDATE_COMMITTED"


@pytest.mark.parametrize("bad", [
    "wrong_state_sha", "wrong_panel", "collapsed", "wrong_update",
    "false_origin", "missing_exact_count", "nonfinite",
])
def test_bad_reported_probe_refused_before_bytes_with_complete_adam(tmp_path, bad):
    root, backup, _ = open_synthetic(tmp_path)
    journal.begin_attempt(root, backup, update=1)
    raw = fake_bytes(1)
    p = probe(1, raw)
    if bad == "wrong_state_sha":
        p["state_payload_sha256"] = "0" * 64
    elif bad == "wrong_panel":
        p["probe_panel_sha256"] = "9" * 64
    elif bad == "collapsed":
        p["metrics"]["cell_centered_energy"] = 0
        p["cell_distinct_row_count"] = 1
    elif bad == "wrong_update":
        p["state_update"] = 0
    elif bad == "false_origin":
        p["measurement_origin"] = "PHYSICALLY_PROVED"
    elif bad == "missing_exact_count":
        del p["cell_distinct_row_count"]
    elif bad == "nonfinite":
        p["nonfinite_values"] = 1
    with pytest.raises(journal.JournalRefusal):
        submit(root, backup, 1, raw, supplied_probe=p)
    assert not (root / "u00001.state.bin").exists()
    assert not (root / "u00001.telemetry.json").exists()
    assert journal.inspect_journal(root, backup)["journal_records"] == 2


def test_u0_wrong_state_or_probe_never_creates_run_directory(tmp_path):
    root, backup = tmp_path / "run", tmp_path / "custody"
    raw = fake_bytes(1)  # Adam step=1, but U0 requires empty Adam
    with pytest.raises(bridge.StructuredJournalRefusal):
        bridge.open_synthetic_journal(
            root=root, custody=backup, run_id=RUN_ID, horizon=3,
            panel_sha256=PANEL, config_sha256=CONFIG,
            rights_sha256=RIGHTS, gene_axis_sha256=GENES,
            source_manifest_sha256=SOURCES, philox_contract_sha256=PHILOX,
            keyed_run_seed=SEED, state_bytes=raw, reported_probe=probe(0, raw))
    assert not root.exists() and not backup.exists()


def test_cannot_change_keyed_contract_between_updates(tmp_path):
    root, backup, _ = open_synthetic(tmp_path)
    journal.begin_attempt(root, backup, update=1)
    raw = fake_bytes(1)
    with pytest.raises(bridge.StructuredJournalRefusal,
                       match="OPENING_PROCESS_CONTRACT_CHANGED_OR_UNKNOWN"):
        submit(root, backup, 1, raw, expected_keyed_run_seed=72)
    assert not (root / "u00001.state.bin").exists()
    assert submit(root, backup, 1, raw)["journal"]["status"] == "UPDATE_COMMITTED"


def test_incomplete_run_does_not_create_a_proven_recovery_state(tmp_path):
    root, backup, _ = open_synthetic(tmp_path)
    journal.begin_attempt(root, backup, update=1)
    assert journal.inspect_journal(root, backup)["status"].startswith(
        "TERMINATED_UNEXPECTEDLY")
    assert journal.inspect_forensic_prefix(root, backup)[
        "last_neurally_healthy_checkpoint_proved"] is False
    assert not (root / "u00001.state.bin").exists()
    assert bridge.AUTHORITY.endswith("REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED")


@pytest.mark.skipif(not hasattr(os, "fork"), reason="POSIX only")
def test_forked_child_cannot_inherit_structured_writer_capability(tmp_path):
    root, backup, _ = open_synthetic(tmp_path)
    journal.begin_attempt(root, backup, update=1)
    raw = fake_bytes(1)
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            try:
                submit(root, backup, 1, raw)
            except (bridge.StructuredJournalRefusal, journal.JournalRefusal):
                os.write(write_fd, b"DENIED")
            else:
                os.write(write_fd, b"FORK_COMMITTED")
        finally:
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    try:
        outcome = os.read(read_fd, 100)
    finally:
        os.close(read_fd)
    _pid, status = os.waitpid(pid, 0)
    assert status == 0 and outcome == b"DENIED"
    assert not (root / "u00001.state.bin").exists()
    assert submit(root, backup, 1, raw)["journal"]["status"] == "UPDATE_COMMITTED"
