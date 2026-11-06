"""Sol independent RED on Macha #581 and integrated #582: u0 must bind
the optimizer's *named parameter IDs and group membership*, not only tensor
names/shapes/dtypes and number of parameters in each group.

Fake CPU tensor snapshots only; no forward, backward, optimizer.step, EMA,
GPU, real biological data, private controller, or training.
Original Macha/Sol tests are unchanged.
"""
from __future__ import annotations

import pytest

from scripts.v5 import jepa_v5_full_state_readonly_audit_v1 as state
from scripts.v5 import jepa_v5_structured_journal_preflight_v1 as bridge
from scripts.v5 import jepa_synth2048_attempt_journal_v2 as journal
from tests.test_jepa_v5_structured_journal_preflight_v1 import (
    fake_bundle, fake_bytes, open_synthetic, submit,
)

SAME_SHAPE_PARAMETERS = ("online.value_encoder.bias", "online.identity_encoder.bias")


def _swapped_ids(bundle):
    layout = bundle["parameter_layout"]
    a, b = (layout[name]["optimizer_param_id"] for name in SAME_SHAPE_PARAMETERS)
    assert a != b
    assert layout[SAME_SHAPE_PARAMETERS[0]]["shape"] == layout[SAME_SHAPE_PARAMETERS[1]]["shape"]
    return a, b


def _reorder_optimizer_group(bundle):
    a, b = _swapped_ids(bundle)
    group = bundle["optimizer"]["param_groups"][0]["params"]
    i, j = group.index(a), group.index(b)
    group[i], group[j] = group[j], group[i]
    # No tensor was altered, and every optimizer ID still appears exactly once.


def _relabel_named_parameter_to_optimizer_id(bundle):
    a, b = _swapped_ids(bundle)
    layout = bundle["parameter_layout"]
    layout[SAME_SHAPE_PARAMETERS[0]]["optimizer_param_id"] = b
    layout[SAME_SHAPE_PARAMETERS[1]]["optimizer_param_id"] = a
    # Names and shapes are unchanged. IDs are still complete and unique.
    # Under positional AdamW load this changes which moments belong to a name.


@pytest.mark.parametrize("mutation", [
    _reorder_optimizer_group,
    _relabel_named_parameter_to_optimizer_id,
], ids=["reorder_named_optimizer_group", "swap_named_optimizer_parameter_ids"])
def test_red_u1_optimizer_parameter_identity_drift_must_refuse_before_any_publication(
        tmp_path, mutation):
    root, backup, _ = open_synthetic(tmp_path)
    journal.begin_attempt(root, backup, update=1)
    bundle = fake_bundle(1)
    mutation(bundle)
    raw, _digest = state.to_verified_bytes(bundle)  # independent single-snapshot check
    with pytest.raises(bridge.StructuredJournalRefusal,
                       match="MODEL_OR_OPTIMIZER_STRUCTURE_CHANGED_SINCE_U0"):
        submit(root, backup, 1, raw)
    assert not (root / "u00001.state.bin").exists()
    assert not (root / "u00001.telemetry.json").exists()


def test_control_unchanged_u0_model_and_optimizer_identity_can_commit(tmp_path):
    root, backup, _ = open_synthetic(tmp_path)
    journal.begin_attempt(root, backup, update=1)
    assert submit(root, backup, 1, fake_bytes(1))["journal"]["status"] == "UPDATE_COMMITTED"
