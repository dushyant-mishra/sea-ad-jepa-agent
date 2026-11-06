"""Original PR224 V5 REAL encoder/teacher/predictor and empty U0 AdamW state
-> V2 synthetic journal. CPU model initialization and read-only state capture
ONLY. No forward, backward, optimizer.step, EMA, real human data or V80.

The real public original PR547 ZIP is mandatory; do not fabricate a FIT.
"""
from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import torch

from scripts.v5 import jepa_v5_pipeline_identity_contract_v1 as contract
from scripts.v5 import jepa_v5_live_model_u0_journal_connector_v1 as live
from scripts.v5 import jepa_v5_full_state_readonly_audit_v1 as state
from scripts.v5 import jepa_synth2048_attempt_journal_v2 as journal
from sea_ad_jepa.v5.inactive_update_reference import build_reference_modules

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(autouse=True)
def forbid_all_actual_training_mutations_in_this_module():
    """Safety net: even accidental code paths cannot step, backward or EMA."""
    from contextlib import ExitStack
    with ExitStack() as stack:
        forbidden = AssertionError("REAL_OPTIMIZER_BACKWARD_EMA_EXECUTION_FORBIDDEN")
        stack.enter_context(patch.object(torch.optim.AdamW, "step",
                                         side_effect=forbidden))
        stack.enter_context(patch.object(torch.optim.Optimizer, "step",
                                         side_effect=forbidden))
        stack.enter_context(patch.object(torch.Tensor, "backward",
                                         side_effect=forbidden))
        stack.enter_context(patch.object(torch.autograd, "backward",
                                         side_effect=forbidden))
        stack.enter_context(patch.object(torch.autograd, "grad",
                                         side_effect=forbidden))
        stack.enter_context(patch(
            "sea_ad_jepa.v5.inactive_guarded_update_v1.run_guarded_inactive_reference_update",
            side_effect=forbidden))
        stack.enter_context(patch(
            "sea_ad_jepa.v5.inactive_update_reference.run_inactive_reference_update",
            side_effect=forbidden))
        yield



@pytest.fixture(scope="module")
def public_contract():
    fit = os.environ.get("JEPA_PUBLIC_DEV_FIT_ZIP")
    if not fit:
        pytest.skip("Must SHA verify actual original PR547 public FIT; no fixture substitute")
    doc = contract.load_contract(ROOT / contract.CONTRACT_PATH)
    contract.verify_repository(doc, ROOT)
    contract.verify_dataset(doc, Path(fit))
    contract.verify_run_request(doc, contract.expected_run_request(doc))
    return doc


def real_v5(**overrides):
    opts = dict(live.CONFIG)
    opts.update(overrides)
    return build_reference_modules(**opts)


def caller_reported_probe(snapshot):
    """Journal-required caller report. Deliberately NOT physical biology."""
    return {
        "state_update": 0,
        "state_payload_sha256": snapshot.snapshot_sha256,
        "probe_panel_sha256": snapshot.metadata["panel_sha256"],
        "operator_homogeneous_eval_mode": True,
        "identical_gene_sets": True,
        "metrics": {
            "cell_centered_energy": .20,
            "same_gene_cross_cell_variance": .30,
            "same_cell_expression_shuffle_delta": .10,
        },
        "cell_distinct_row_count": 2,
        "probe_cells": 2,
        "nonfinite_values": 0,
        "measurement_origin": "CALLER_REPORTED__NOT_PHYSICALLY_PROVED",
    }


def capture(modules, receipt):
    return live.capture_real_v5_u0(
        modules=modules, repo_root=ROOT,
        public_fit_zip=Path(os.environ["JEPA_PUBLIC_DEV_FIT_ZIP"]),
        expected_contract=receipt, run_id="real-original-v5-u0",
    )


def test_real_original_v5_module_weights_and_empty_adam_u0_snapshot(public_contract):
    modules = real_v5()
    assert modules.online.tokenizer.vocabulary_size == 2048
    assert len(modules.online.blocks) == 6
    assert len(modules.optimizer.state) == 0
    # Independent RED: legacy fake snapshot expects online.value_encoder.weight,
    # while original PR224 real model has tokenizer.value_encoder.{0,2}.weight.
    with patch.object(torch.optim.AdamW, "step", side_effect=AssertionError("NO_OPTIMIZER")):
        snap = capture(modules, public_contract)
    bundle, readout = state.read_verified_bytes(
        snap.state_bytes, expected_sha256=snap.snapshot_sha256)
    assert snap.completed_updates == 0
    assert readout["optimizer_tensor_count"] == 0
    assert readout["model_modules"] == ["online", "teacher", "predictor"]
    assert "online.tokenizer.value_encoder.0.weight" in bundle["parameter_names"]
    assert "online.tokenizer.value_encoder.2.weight" in bundle["parameter_names"]
    assert "online.value_encoder.weight" not in bundle["parameter_names"]
    assert bundle["metadata"]["training_authorized"] is False
    assert snap.training_authorized is False
    assert len(modules.optimizer.state) == 0
    assert all(p.grad is None for m in (modules.online, modules.teacher, modules.predictor)
               for p in m.parameters())


def test_true_original_v5_u0_bytes_recorded_in_integrated_v2_journal(
        tmp_path, public_contract):
    modules = real_v5()
    snapshot = capture(modules, public_contract)
    root, custody = tmp_path/"real-u0", tmp_path/"outside-head"
    with patch.object(torch.optim.AdamW, "step", side_effect=AssertionError("NO_OPTIMIZER")):
        outcome = live.record_real_v5_u0_to_journal(
            snapshot=snapshot, modules=modules, repo_root=ROOT,
            public_fit_zip=Path(os.environ["JEPA_PUBLIC_DEV_FIT_ZIP"]),
            expected_contract=public_contract, journal_root=root,
            external_custody=custody, horizon=2,
            caller_reported_probe=caller_reported_probe(snapshot))
    assert outcome["status"] == "ACTUAL_ORIGINAL_V5_INITIALIZED_U0_BYTES_RECORDED"
    assert outcome["completed_optimizer_steps"] == 0
    assert outcome["actual_model_forward_executed_by_connector"] is False
    assert outcome["probe_measurement_origin"] == journal.MEASUREMENT_ORIGIN
    assert outcome["physical_c1_c6_biology_or_collapse_proved"] is False
    assert outcome["training_authorized"] is False
    assert outcome["data_class"] == "PR547_PUBLIC_SYNTHETIC_DEV2048_ONLY"
    assert outcome["checkpoint_class"].startswith("DEV_ONLY_U0_INITIALIZATION")
    assert outcome["source_rights_issuer_verified"] is False
    assert outcome["qualified_teacher_target_bound"] is False
    assert outcome["physical_probe_panel_bound"] is False
    assert outcome["synthetic_fixture_model_used"] is False
    assert (root/"u00000.state.bin").read_bytes() == snapshot.state_bytes
    assert sha256((root/"u00000.state.bin").read_bytes()).hexdigest() == snapshot.snapshot_sha256
    assert journal.inspect_journal(root, custody)["resume_authorized"] is False
    # The original U0 checkpoint may NEVER become a fabricated U1.
    from scripts.v5 import jepa_v5_structured_journal_preflight_v1 as bridge
    with pytest.raises(bridge.StructuredJournalRefusal,
                       match="ORIGINAL_REAL_V5_U0_JOURNAL_CANNOT_COMMIT_FAKE_U1"):
        bridge.commit_synthetic_preflight(
            root=root, custody=custody, update=1,
            state_bytes=snapshot.state_bytes,
            reported_probe=caller_reported_probe(snapshot),
            expected_gene_axis_sha256=snapshot.metadata["gene_axis_sha256"],
            expected_source_manifest_sha256=snapshot.metadata["source_manifest_sha256"],
            expected_philox_contract_sha256=snapshot.metadata["keyed_philox_contract_sha256"],
            expected_keyed_run_seed=snapshot.metadata["keyed_run_seed"])
    assert not (root/"u00001.state.bin").exists()
    assert len(modules.optimizer.state) == 0


@pytest.mark.parametrize("settings", [
    {"vocabulary_size": 2044},
    {"blocks": 1},
    {"heads": 2},
    {"width": 128, "heads": 4},
    {"ffn_width": 256},
    {"dropout": 0.0},
    {"learning_rate": 3e-4},
    {"weight_decay": 0.0},
])
def test_wrong_v4_or_dev_model_geometry_optimizer_and_q_vocab_fail_closed(
        public_contract, settings):
    modules = real_v5(**settings)
    with pytest.raises(live.LiveV5JournalRefusal):
        capture(modules, public_contract)


def test_modified_live_model_between_capture_and_write_does_not_get_journal(
        tmp_path, public_contract):
    modules = real_v5()
    snapshot = capture(modules, public_contract)
    with torch.no_grad():
        modules.online.cell_token.add_(.001)
    root, custody = tmp_path/"bad-u0", tmp_path/"head"
    with pytest.raises(live.LiveV5JournalRefusal,
                       match="(LIVE_MODEL_WEIGHTS_CHANGED_SINCE_CAPTURE|INITIAL_WEIGHTS_NOT_PR548_EXACT_SEED)"):
        live.record_real_v5_u0_to_journal(
            snapshot=snapshot, modules=modules, repo_root=ROOT,
            public_fit_zip=Path(os.environ["JEPA_PUBLIC_DEV_FIT_ZIP"]),
            expected_contract=public_contract, journal_root=root,
            external_custody=custody, horizon=2,
            caller_reported_probe=caller_reported_probe(snapshot))
    assert not root.exists() and not custody.exists()


def test_mismatched_reported_probe_never_creates_a_run(tmp_path, public_contract):
    modules = real_v5()
    snapshot = capture(modules, public_contract)
    probe = caller_reported_probe(snapshot)
    probe["measurement_origin"] = "PHYSICALLY_PROVED"
    root, custody = tmp_path/"bad-probe", tmp_path/"head"
    with pytest.raises(live.LiveV5JournalRefusal,
                       match="CALLER_REPORTED_ONLY_PROBE_REQUIRED"):
        live.record_real_v5_u0_to_journal(
            snapshot=snapshot, modules=modules, repo_root=ROOT,
            public_fit_zip=Path(os.environ["JEPA_PUBLIC_DEV_FIT_ZIP"]),
            expected_contract=public_contract, journal_root=root,
            external_custody=custody, horizon=2,
            caller_reported_probe=probe)
    assert not root.exists() and not custody.exists()


def test_wrong_source_data_claim_rejected_before_capture(tmp_path, public_contract):
    modules = real_v5()
    import copy
    fake = copy.deepcopy(public_contract)
    fake["components"]["dataset"]["measured"]["addresses"] = 41238
    body = {k: v for k, v in fake.items() if k != "contract_sha256"}
    fake["contract_sha256"] = contract.canonical_sha256(body)
    with pytest.raises(live.LiveV5JournalRefusal,
                       match="WRONG_OR_ALTERNATE_V5_CONTRACT_V585_NOT_ALLOWED"):
        live.capture_real_v5_u0(
            modules=modules, repo_root=ROOT,
            public_fit_zip=Path(os.environ["JEPA_PUBLIC_DEV_FIT_ZIP"]),
            expected_contract=fake, run_id="real-original-v5-u0")


def test_no_fabricated_adam_moments_at_u0(public_contract):
    modules = real_v5()
    first = next(iter(modules.online.parameters()))
    modules.optimizer.state[first] = {
        "step": torch.tensor(1.),
        "exp_avg": torch.zeros_like(first),
        "exp_avg_sq": torch.zeros_like(first),
    }
    with pytest.raises(live.LiveV5JournalRefusal, match="U0_ADAM_STATE_MUST_BE_EMPTY"):
        capture(modules, public_contract)



def test_wrong_initialization_seed_cannot_launder_as_original_PR548_U0(public_contract):
    """Independent RED: same V5 code/shapes but wrong seed is wrong frozen U0."""
    modules = real_v5(init_seed=8113003)
    with pytest.raises(live.LiveV5JournalRefusal,
                       match="INITIAL_WEIGHTS_NOT_PR548_EXACT_SEED"):
        capture(modules, public_contract)



def test_toy_model_substitute_never_bypasses_exact_original_v5_type(public_contract):
    from types import SimpleNamespace
    fake = SimpleNamespace(online=object(), teacher=object(), predictor=object(),
                           optimizer=object())
    with pytest.raises(live.LiveV5JournalRefusal,
                       match="NOT_ORIGINAL_V5_REFERENCE_MODULES"):
        capture(fake, public_contract)


def test_gene_identity_width_48_is_bound_to_original_v5_computation(public_contract):
    modules = real_v5()
    modules.online.tokenizer.gene_identity.embedding_dim = 49
    with pytest.raises(live.LiveV5JournalRefusal,
                       match="GENE_IDENTITY_EMBEDDING_WIDTH_48_REQUIRED"):
        capture(modules, public_contract)


@pytest.mark.parametrize(("key", "value"), [
    ("maximize", True), ("foreach", True), ("fused", True),
])
def test_optimizer_ascent_or_unapproved_fused_mode_refused_at_u0(
        public_contract, key, value):
    modules = real_v5()
    modules.optimizer.param_groups[0][key] = value
    with pytest.raises(live.LiveV5JournalRefusal,
                       match="ORIGINAL_V5_ADAMW_HYPERPARAMETERS_CHANGED"):
        capture(modules, public_contract)


def test_caller_reported_probe_with_wrong_model_state_sha_refused_before_write(
        tmp_path, public_contract):
    modules = real_v5()
    snapshot = capture(modules, public_contract)
    report = caller_reported_probe(snapshot)
    report["state_payload_sha256"] = "f" * 64
    root, custody = tmp_path / "tampered", tmp_path / "outside"
    with pytest.raises(live.LiveV5JournalRefusal,
                       match="CALLER_REPORTED_ONLY_PROBE_REQUIRED"):
        live.record_real_v5_u0_to_journal(
            snapshot=snapshot, modules=modules, repo_root=ROOT,
            public_fit_zip=Path(os.environ["JEPA_PUBLIC_DEV_FIT_ZIP"]),
            expected_contract=public_contract, journal_root=root,
            external_custody=custody, horizon=2,
            caller_reported_probe=report)
    assert not root.exists() and not custody.exists()


def test_post_step_connector_is_unavailable_until_separate_owner_authority():
    with pytest.raises(live.LiveV5JournalRefusal,
                       match="POST_STEP_REAL_TRAINING_NOT_AUTHORIZED"):
        live.refuse_post_step_without_separate_authority()
