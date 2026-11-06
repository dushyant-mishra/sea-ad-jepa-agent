"""Macha #583 review controls: structurally equivalent states must commit,
and Sol's ID/order identity really matters under positional restore.

These pass on Sol's exact #583 head and must stay green after any repair.
Fake CPU tensors; ``load_state_dict`` only (never a step, backward, EMA,
GPU, real data or training).
"""
from __future__ import annotations

import pytest

from scripts.v5 import jepa_v5_full_state_readonly_audit_v1 as state
from scripts.v5 import jepa_synth2048_attempt_journal_v2 as journal
from tests.test_jepa_v5_structured_journal_preflight_v1 import (
    fake_bundle, open_synthetic, submit,
)
from tests.test_jepa_v5_structured_journal_preflight_v1_macha_583_review_red import (
    _group, _label_moments, positional_restore,
)

SAME_SHAPE = ("online.value_encoder.bias", "online.identity_encoder.bias")


def _commits(tmp_path, bundle):
    root, backup, _ = open_synthetic(tmp_path)
    journal.begin_attempt(root, backup, update=1)
    raw, _ = state.to_verified_bytes(bundle)
    return submit(root, backup, 1, raw)["journal"]["status"]


def _renumber_consistently(bundle):
    """Permute integer IDs everywhere; named order in the group is kept."""
    ids = list(_group(bundle)["params"])
    perm = {old: len(ids) - 1 - old for old in ids}
    for desc in bundle["parameter_layout"].values():
        desc["optimizer_param_id"] = perm[desc["optimizer_param_id"]]
    _group(bundle)["params"] = [perm[i] for i in ids]
    bundle["optimizer"]["state"] = {perm[i]: s for i, s in
                                    bundle["optimizer"]["state"].items()}


def test_control_learning_rate_schedule_change_still_commits(tmp_path):
    bundle = fake_bundle(1)
    _group(bundle)["lr"] = 5e-4  # schedule state, not structure
    assert _commits(tmp_path, bundle) == "UPDATE_COMMITTED"


def test_control_consistent_id_renumbering_is_equivalent_and_commits(tmp_path):
    bundle = fake_bundle(1)
    expected = _label_moments(bundle)
    _renumber_consistently(bundle)
    _fields, moments = positional_restore(bundle)
    # The right fabricated moments still land on the right named parameter.
    assert {n: float(m.flatten()[0]) for n, m in moments.items()} == expected
    assert _commits(tmp_path, bundle) == "UPDATE_COMMITTED"


def test_control_layout_insertion_order_and_betas_list_are_equivalent(tmp_path):
    bundle = fake_bundle(1)
    layout = bundle["parameter_layout"]
    bundle["parameter_layout"] = dict(reversed(list(layout.items())))
    _group(bundle)["betas"] = list(_group(bundle)["betas"])
    assert _commits(tmp_path, bundle) == "UPDATE_COMMITTED"


@pytest.mark.parametrize("swap", ["group_order", "named_ids"])
def test_control_sol_583_mutations_misassign_moments_under_positional_restore(swap):
    """Evidence that Sol's #583 refusals protect a real restore path."""
    bundle = fake_bundle(1)
    expected = _label_moments(bundle)
    layout = bundle["parameter_layout"]
    a, b = (layout[n]["optimizer_param_id"] for n in SAME_SHAPE)
    if swap == "group_order":
        params = _group(bundle)["params"]
        i, j = params.index(a), params.index(b)
        params[i], params[j] = params[j], params[i]
    else:
        layout[SAME_SHAPE[0]]["optimizer_param_id"] = b
        layout[SAME_SHAPE[1]]["optimizer_param_id"] = a
    state.verify_readonly_bundle(bundle)  # the single snapshot looks valid
    _fields, moments = positional_restore(bundle)
    got = {n: float(m.flatten()[0]) for n, m in moments.items()}
    if swap == "group_order":
        # The two biases receive each other's moments on restore.
        assert got[SAME_SHAPE[0]] == expected[SAME_SHAPE[1]]
        assert got[SAME_SHAPE[1]] == expected[SAME_SHAPE[0]]
    else:
        # The restore is unchanged, but the layout now names the wrong
        # moments: the record's name->moment claim no longer matches.
        claimed = {n: float(layout[n]["optimizer_param_id"] + 1)
                   for n in SAME_SHAPE}
        assert all(got[n] != claimed[n] for n in SAME_SHAPE)
