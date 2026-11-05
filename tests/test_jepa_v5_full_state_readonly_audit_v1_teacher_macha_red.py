"""Macha RED for #571: the EMA teacher must mirror the online encoder exactly.

Fake CPU tensors only. No forward, backward, optimizer step or EMA update.
The teacher produces the JEPA targets; a checkpoint whose teacher lacks the
expression-value encoder (or has other shapes) cannot reproduce those targets,
so it must not verify as a complete state.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO

import pytest
import torch

from scripts.v5 import jepa_v5_full_state_readonly_audit_v1 as c
from tests.test_jepa_v5_full_state_readonly_audit_v1 import capture, fixture


def _drop_value_encoder(b):
    for k in [k for k in b["modules"]["teacher"] if k.startswith("value_encoder")]:
        b["modules"]["teacher"].pop(k)


@pytest.mark.parametrize("mutate", [
    _drop_value_encoder,
    lambda b: b["modules"]["teacher"].__setitem__("value_encoder.weight", torch.zeros(5, 5)),
    lambda b: b["modules"]["teacher"].__setitem__(
        "value_encoder.weight", b["modules"]["teacher"]["value_encoder.weight"].double()),
    lambda b: b["modules"]["teacher"].__setitem__("extra.weight", torch.ones(2)),
    lambda b: b["modules"].__setitem__("teacher", {"junk": torch.ones(1)}),
], ids=["missing_value_encoder", "wrong_shape", "wrong_dtype", "extra_tensor", "unrelated"])
def test_red_bundle_with_incomplete_or_mismatched_teacher_is_refused(mutate):
    bundle = capture(updates=1)
    mutate(bundle)
    with pytest.raises(c.FullStateRefusal, match="TEACHER_DOES_NOT_MIRROR_ONLINE"):
        c.verify_readonly_bundle(bundle)
    stream = BytesIO()
    torch.save(bundle, stream)
    raw = stream.getvalue()
    with pytest.raises(c.FullStateRefusal, match="TEACHER_DOES_NOT_MIRROR_ONLINE"):
        c.read_verified_bytes(raw, expected_sha256=sha256(raw).hexdigest())


def test_red_live_capture_refuses_a_teacher_without_the_value_encoder():
    online, teacher, predictor, opt, meta = fixture(updates=1)
    del teacher.value_encoder
    with pytest.raises(c.FullStateRefusal, match="TEACHER_DOES_NOT_MIRROR_ONLINE"):
        c.capture_readonly_bundle(online=online, teacher=teacher, predictor=predictor,
                                  optimizer=opt, metadata=meta)


def test_teacher_with_different_ema_values_but_same_structure_still_verifies():
    online, teacher, predictor, opt, meta = fixture(updates=1)
    with torch.no_grad():
        for p in teacher.parameters():
            p.add_(0.25)  # EMA values legitimately differ from online values
    bundle = c.capture_readonly_bundle(online=online, teacher=teacher, predictor=predictor,
                                       optimizer=opt, metadata=meta)
    assert c.verify_readonly_bundle(bundle)["biological_health_proved"] is False
