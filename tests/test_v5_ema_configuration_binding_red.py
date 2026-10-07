from pathlib import Path

import pytest

import sea_ad_jepa.v5.inactive_checkpoint_binding_v1 as binding
import sea_ad_jepa.v5.prefreeze_runtime_authority as authority_module
from sea_ad_jepa.v5.inactive_update_reference import build_reference_modules


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
        betas=(.9, .999),
        eps=1e-8,
        weight_decay=.01,
        init_seed=8113002,
    )


def test_constant_ema_configuration_has_explicit_mechanical_identity_not_authority():
    identity_fn = getattr(authority_module, "constant_ema_configuration_identity", None)
    assert callable(identity_fn), "canonical rehearsal has no typed EMA-configuration identity"
    identity = identity_fn(0.95)
    assert isinstance(identity, str) and identity.startswith("V5_CONSTANT_EMA:")
    assert identity != identity_fn(0.96)
    with pytest.raises(Exception):
        identity_fn(-0.1)
    with pytest.raises(Exception):
        identity_fn(1.0)


def test_bound_checkpoint_and_authority_carry_same_explicit_ema_configuration_identity():
    identity_fn = getattr(authority_module, "constant_ema_configuration_identity", None)
    assert callable(identity_fn), "canonical rehearsal has no typed EMA-configuration identity"
    ema_identity = identity_fn(0.95)
    modules = _modules()
    envelope = binding.capture_prefreeze_bound_checkpoint(
        modules,
        next_update_index=0,
        presentations_seen=0,
        premise_state_path=PREMISE,
        ema_configuration_identity=ema_identity,
    )
    assert envelope.ema_configuration_identity == ema_identity
    issued = binding.issue_prefreeze_authority_from_bound_checkpoint(
        modules,
        envelope,
        premise_state_path=PREMISE,
    )
    assert issued.ema_configuration_identity == ema_identity


def test_guarded_runtime_rejects_changed_ema_configuration_before_teacher_mutation():
    identity_fn = getattr(authority_module, "constant_ema_configuration_identity", None)
    assert callable(identity_fn), "canonical rehearsal has no typed EMA-configuration identity"
    ema_identity = identity_fn(0.95)
    modules = _modules()
    envelope = binding.capture_prefreeze_bound_checkpoint(
        modules,
        next_update_index=0,
        presentations_seen=0,
        premise_state_path=PREMISE,
        ema_configuration_identity=ema_identity,
    )
    issued = binding.issue_prefreeze_authority_from_bound_checkpoint(
        modules,
        envelope,
        premise_state_path=PREMISE,
    )
    observed = identity_fn(0.96)
    assert observed != issued.ema_configuration_identity
    verifier = getattr(issued, "verify_ema_configuration_identity", None)
    assert callable(verifier), "mechanical authority cannot reject EMA-configuration drift"
    with pytest.raises(Exception, match="EMA|ema"):
        verifier(observed)
