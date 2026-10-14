from pathlib import Path

import pytest

from sea_ad_jepa.v5.inactive_checkpoint_binding_v1 import capture_prefreeze_bound_checkpoint
from sea_ad_jepa.v5.inactive_update_reference import build_reference_modules
import sea_ad_jepa.v5.ema_bound_runtime_proof_v1 as ema_binding


ROOT = Path(__file__).resolve().parents[1]
PREMISE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"
UNIT = "SUCCESSFUL_BASE_CELL_PRESENTATIONS"


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


def test_presentation_ema_configuration_has_explicit_mechanical_identity_not_authority():
    identity = ema_binding.presentation_ema_configuration_identity(
        half_life_presentations=1000,
        presentation_unit_id=UNIT,
    )
    assert isinstance(identity, str) and identity.startswith("V5_PRESENTATION_EMA:")
    assert identity != ema_binding.presentation_ema_configuration_identity(
        half_life_presentations=1001,
        presentation_unit_id=UNIT,
    )
    with pytest.raises(ValueError):
        ema_binding.presentation_ema_configuration_identity(
            half_life_presentations=0,
            presentation_unit_id=UNIT,
        )


def test_parent_checkpoint_can_issue_digest_bound_presentation_ema_rehearsal_authority():
    modules = _modules()
    parent = capture_prefreeze_bound_checkpoint(
        modules, next_update_index=0, presentations_seen=0, premise_state_path=PREMISE
    )
    issued = ema_binding.issue_presentation_ema_bound_authority_from_checkpoint(
        modules,
        parent,
        premise_state_path=PREMISE,
        half_life_presentations=1000,
        presentation_unit_id=UNIT,
    )
    assert issued.ema_configuration_identity == ema_binding.presentation_ema_configuration_identity(
        half_life_presentations=1000,
        presentation_unit_id=UNIT,
    )
    assert issued.training_authorized is False
    assert issued.execution_authorized is False
    assert issued.production_promotable is False
    assert len(issued.binding_digest) == 64


def test_presentation_ema_bound_authority_rejects_configuration_drift():
    modules = _modules()
    parent = capture_prefreeze_bound_checkpoint(
        modules, next_update_index=0, presentations_seen=0, premise_state_path=PREMISE
    )
    issued = ema_binding.issue_presentation_ema_bound_authority_from_checkpoint(
        modules,
        parent,
        premise_state_path=PREMISE,
        half_life_presentations=1000,
        presentation_unit_id=UNIT,
    )
    assert issued.verify_ema_configuration(
        half_life_presentations=1000,
        presentation_unit_id=UNIT,
    ) is True
    with pytest.raises(RuntimeError, match="EMA|ema"):
        issued.verify_ema_configuration(
            half_life_presentations=1001,
            presentation_unit_id=UNIT,
        )
