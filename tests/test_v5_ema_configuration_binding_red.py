from pathlib import Path

import pytest

from sea_ad_jepa.v5.inactive_checkpoint_binding_v1 import capture_prefreeze_bound_checkpoint
from sea_ad_jepa.v5.inactive_update_reference import build_reference_modules


ROOT = Path(__file__).resolve().parents[1]
PREMISE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"


def _ema_binding_module():
    try:
        import sea_ad_jepa.v5.ema_bound_runtime_proof_v1 as module
    except ImportError:
        return None
    return module


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
    module = _ema_binding_module()
    assert module is not None, "canonical rehearsal has no EMA-bound proof successor"
    identity = module.constant_ema_configuration_identity(0.95)
    assert isinstance(identity, str) and identity.startswith("V5_CONSTANT_EMA:")
    assert identity != module.constant_ema_configuration_identity(0.96)
    with pytest.raises(ValueError):
        module.constant_ema_configuration_identity(-0.1)
    with pytest.raises(ValueError):
        module.constant_ema_configuration_identity(1.0)


def test_parent_checkpoint_can_issue_digest_bound_ema_rehearsal_authority():
    module = _ema_binding_module()
    assert module is not None, "canonical rehearsal has no EMA-bound proof successor"
    modules = _modules()
    parent = capture_prefreeze_bound_checkpoint(
        modules, next_update_index=0, presentations_seen=0, premise_state_path=PREMISE
    )
    issued = module.issue_ema_bound_authority_from_checkpoint(
        modules,
        parent,
        premise_state_path=PREMISE,
        ema_momentum=0.95,
    )
    assert issued.ema_configuration_identity == module.constant_ema_configuration_identity(0.95)
    assert issued.training_authorized is False
    assert issued.execution_authorized is False
    assert issued.production_promotable is False
    assert len(issued.binding_digest) == 64


def test_ema_bound_authority_rejects_configuration_drift_before_canonical_update():
    module = _ema_binding_module()
    assert module is not None, "canonical rehearsal has no EMA-bound proof successor"
    modules = _modules()
    parent = capture_prefreeze_bound_checkpoint(
        modules, next_update_index=0, presentations_seen=0, premise_state_path=PREMISE
    )
    issued = module.issue_ema_bound_authority_from_checkpoint(
        modules,
        parent,
        premise_state_path=PREMISE,
        ema_momentum=0.95,
    )
    assert issued.verify_ema_momentum(0.95) is True
    with pytest.raises(RuntimeError, match="EMA|ema"):
        issued.verify_ema_momentum(0.96)
