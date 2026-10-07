from pathlib import Path

import torch

import sea_ad_jepa.v5.inactive_checkpoint_binding_v1 as binding
from sea_ad_jepa.v5.inactive_update_reference import build_reference_modules, capture_reference_checkpoint
from sea_ad_jepa.v5.prefreeze_runtime_authority import PrefreezeOptimizerGuardV1


ROOT = Path(__file__).resolve().parents[1]
PREMISE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"


def _modules():
    return build_reference_modules(
        vocabulary_size=32,
        width=16,
        heads=4,
        blocks=1,
        ffn_width=24,
        dropout=.10,
        learning_rate=3e-4,
        betas=(.9,.999),
        eps=1e-8,
        weight_decay=.01,
        init_seed=8113002,
    )


def _completed_envelope():
    modules = _modules()
    parent = binding.capture_prefreeze_bound_checkpoint(
        modules,
        next_update_index=0,
        presentations_seen=0,
        premise_state_path=PREMISE,
    )
    authority = binding.issue_prefreeze_authority_from_bound_checkpoint(
        modules,
        parent,
        premise_state_path=PREMISE,
    )
    guard = PrefreezeOptimizerGuardV1(authority, modules.optimizer)
    token = guard.begin_step(authority.optimizer_identity, authority.checkpoint_digest)
    modules.optimizer.zero_grad(set_to_none=True)
    for group in modules.optimizer.param_groups:
        for parameter in group["params"]:
            parameter.grad = torch.zeros_like(parameter)
    guard.mark_unscaled(token)
    guard.mark_gradients_valid(token)
    guard.run_optimizer_step(token)
    guard.assert_step_complete(token)
    guard.run_ema(token, lambda: None)
    reference = capture_reference_checkpoint(
        modules,
        next_update_index=1,
        presentations_seen=6,
    )
    logical_digest = binding.reference_checkpoint_sha256(reference)
    receipt = guard.completed_checkpoint_receipt(token, logical_digest)
    guard.close()
    envelope = binding.capture_prefreeze_bound_checkpoint(
        modules,
        next_update_index=1,
        presentations_seen=6,
        premise_state_path=PREMISE,
        completed_guard_receipt=receipt,
    )
    return envelope


def test_physical_completion_proof_exists_only_after_write_hash_reload_and_revalidation(tmp_path):
    assert callable(getattr(binding, "persist_and_verify_completed_prefreeze_checkpoint", None)), (
        "canonical runtime has no durable completion proof boundary"
    )
    envelope = _completed_envelope()
    path = tmp_path / "completed.pt"
    proof = binding.persist_and_verify_completed_prefreeze_checkpoint(
        envelope,
        path,
        premise_state_path=PREMISE,
    )
    assert path.is_file()
    assert proof.schema == "V5_PREFREEZE_PERSISTED_COMPLETION_PROOF_V1"
    assert proof.runtime_contract == binding.PREFREEZE_RUNTIME_CONTRACT
    assert proof.persisted_verified_reload is True
    assert proof.artifact_sha256 == binding._file_sha256(path)
    assert proof.logical_checkpoint_sha256 == binding.reference_checkpoint_sha256(envelope.reference_checkpoint)
    assert proof.completed_guard_receipt_digest == envelope.completed_guard_receipt["receipt_digest"]
    assert proof.next_update_index == 1
    assert proof.presentations_seen == 6
    assert proof.execution_authorized is False
    assert proof.training_authorized is False
    assert proof.production_promotable is False


def test_genesis_checkpoint_cannot_mint_completed_physical_proof(tmp_path):
    modules = _modules()
    genesis = binding.capture_prefreeze_bound_checkpoint(
        modules,
        next_update_index=0,
        presentations_seen=0,
        premise_state_path=PREMISE,
    )
    try:
        binding.persist_and_verify_completed_prefreeze_checkpoint(
            genesis,
            tmp_path / "genesis.pt",
            premise_state_path=PREMISE,
        )
    except RuntimeError as exc:
        assert "noninitial" in str(exc) or "completed" in str(exc)
    else:
        raise AssertionError("genesis checkpoint minted a completed physical proof")
