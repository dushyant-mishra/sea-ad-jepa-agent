"""Macha RED for #575: the model/optimizer structure must stay the run's u0
structure at every later commit.

Fake CPU tensors only. No forward, backward, optimizer step or EMA update.
Each bundle is checked on its own, so a u1 snapshot whose expression-value
encoder changed shape, or which lost a whole module, is accepted as the next
probe-pass checkpoint of the same run; "last healthy state" could then name a
checkpoint that cannot be loaded into the model that produced u0.
"""
from __future__ import annotations

from copy import deepcopy

import pytest
import torch

from scripts.v5 import jepa_v5_full_state_readonly_audit_v1 as state
from scripts.v5 import jepa_v5_structured_journal_preflight_v1 as bridge
from scripts.v5 import jepa_synth2048_attempt_journal_v2 as journal
from tests.test_jepa_v5_full_state_readonly_audit_v1 import fixture
from tests.test_jepa_v5_structured_journal_preflight_v1 import (
    RUN_ID, fake_bytes, open_synthetic, submit,
)


class _Wider(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.value_encoder = torch.nn.Linear(4, 2)  # u0 had Linear(3, 2)
        self.identity_encoder = torch.nn.Linear(2, 2)


class _NoIdentity(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.value_encoder = torch.nn.Linear(3, 2)  # identity_encoder dropped


def _bytes_with(student_cls, u):
    _o, _t, _p, _opt, meta = fixture(updates=u)
    online = student_cls()
    teacher = deepcopy(online).eval()
    for p in teacher.parameters():
        p.requires_grad_(False)
    predictor = torch.nn.Linear(2, 1)
    opt = torch.optim.AdamW(list(online.parameters()) + list(predictor.parameters()),
                            lr=1e-3, betas=(0.9, 0.999), eps=1e-8)
    opt.step = lambda *a, **k: (_ for _ in ()).throw(AssertionError("NO STEP"))
    for group in opt.param_groups:
        for p in group["params"]:
            opt.state[p] = {"step": torch.tensor(float(u)),
                            "exp_avg": torch.zeros_like(p),
                            "exp_avg_sq": torch.ones_like(p)}
    meta["run_id"] = RUN_ID
    bundle = state.capture_readonly_bundle(online=online, teacher=teacher,
                                           predictor=predictor, optimizer=opt,
                                           metadata=meta)
    return state.to_verified_bytes(bundle)[0]


@pytest.mark.parametrize("student", [_Wider, _NoIdentity], ids=["reshaped", "dropped"])
def test_red_u1_with_a_different_model_structure_is_refused_before_any_write(
        tmp_path, student):
    root, backup, _ = open_synthetic(tmp_path)
    journal.begin_attempt(root, backup, update=1)
    raw = _bytes_with(student, 1)
    with pytest.raises(bridge.StructuredJournalRefusal,
                       match="MODEL_OR_OPTIMIZER_STRUCTURE_CHANGED_SINCE_U0"):
        submit(root, backup, 1, raw)
    assert not (root / "u00001.state.bin").exists()
    assert not (root / "u00001.telemetry.json").exists()


def test_same_structure_with_new_values_still_commits(tmp_path):
    root, backup, _ = open_synthetic(tmp_path)
    for u in (1, 2):
        journal.begin_attempt(root, backup, update=u)
        assert submit(root, backup, u, fake_bytes(u))["journal"]["status"] == "UPDATE_COMMITTED"
