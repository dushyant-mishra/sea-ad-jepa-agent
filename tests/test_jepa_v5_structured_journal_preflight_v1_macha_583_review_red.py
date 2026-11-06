"""Macha independent review of Sol #583 (exact head 76eddf86).

#583 binds ordered named AdamW group membership to u0. It still leaves
every other per-group optimizer field (betas, eps, weight_decay, maximize,
foreach, fused, ...) free to change after u0. PyTorch's positional
``Optimizer.load_state_dict`` copies every saved group field except
``params`` into the live optimizer, so a later restore from such a
snapshot silently runs a different optimizer, even gradient ascent.

Fake CPU tensor snapshots only. ``load_state_dict`` is used purely to show
what a positional restore would do; no forward, backward, optimizer.step,
EMA, GPU, real data or training. Sol's and Macha's original tests are
unchanged.
"""
from __future__ import annotations

import pytest
import torch

from scripts.v5 import jepa_v5_full_state_readonly_audit_v1 as state
from scripts.v5 import jepa_v5_structured_journal_preflight_v1 as bridge
from scripts.v5 import jepa_synth2048_attempt_journal_v2 as journal
from tests.test_jepa_v5_full_state_readonly_audit_v1 import fixture
from tests.test_jepa_v5_structured_journal_preflight_v1 import (
    fake_bundle, open_synthetic, probe, submit,
)

CHANGED = "MODEL_OR_OPTIMIZER_STRUCTURE_CHANGED_SINCE_U0"


def _group(bundle):
    groups = bundle["optimizer"]["param_groups"]
    assert len(groups) == 1  # the V5 reference builds one AdamW group
    return groups[0]


def positional_restore(bundle):
    """Restore the way PyTorch does: zip saved IDs with live group order.

    Returns the live optimizer's group fields and, for each parameter
    name, the first-moment tensor that landed on that live parameter.
    """
    online, _teacher, predictor, live, _meta = fixture(updates=0)
    live.load_state_dict(bundle["optimizer"])  # restore only; never a step
    named = {f"online.{n}": p for n, p in online.named_parameters()}
    named.update({f"predictor.{n}": p for n, p in predictor.named_parameters()})
    moments = {n: live.state[p]["exp_avg"].clone() for n, p in named.items()
               if p in live.state}
    fields = {k: v for k, v in live.param_groups[0].items() if k != "params"}
    return fields, moments


def _label_moments(bundle):
    """Give every parameter a distinguishable fabricated first moment."""
    for name, desc in bundle["parameter_layout"].items():
        pid = desc["optimizer_param_id"]
        slot = bundle["optimizer"]["state"][pid]
        slot["exp_avg"] = torch.full_like(slot["exp_avg"], float(pid + 1))
    return {name: float(desc["optimizer_param_id"] + 1)
            for name, desc in bundle["parameter_layout"].items()}


# --------------------------------------------------------------------- RED

def _weight_decay_removed(group):
    group["weight_decay"] = 0.0


def _betas_changed(group):
    group["betas"] = (0.5, 0.9)


def _eps_changed(group):
    group["eps"] = 1e-3


def _gradient_ascent(group):
    group["maximize"] = True


@pytest.mark.parametrize("mutation", [
    _weight_decay_removed, _betas_changed, _eps_changed, _gradient_ascent,
], ids=["weight_decay_0p01_to_0", "betas_changed", "eps_changed",
        "maximize_true_gradient_ascent"])
def test_red_u1_adamw_group_field_drift_must_refuse_before_publication(
        tmp_path, mutation):
    root, backup, _ = open_synthetic(tmp_path)
    journal.begin_attempt(root, backup, update=1)
    bundle = fake_bundle(1)
    before = dict(_group(bundle))
    mutation(_group(bundle))
    assert _group(bundle) != before
    raw, digest = state.to_verified_bytes(bundle)  # single snapshot passes
    # A positional restore really does adopt the drifted field.
    fields, _moments = positional_restore(state.read_verified_bytes(
        raw, expected_sha256=digest)[0])
    changed = {k for k in fields if k in before and fields[k] != before[k]
               and k != "lr"}
    assert changed, "the mutation must reach a live optimizer on restore"
    with pytest.raises(bridge.StructuredJournalRefusal,
                       match=f"({CHANGED}|OPTIMIZER_MAXIMIZE_NOT_V5_MINIMIZATION)"):
        submit(root, backup, 1, raw)
    assert not (root / "u00001.state.bin").exists()
    assert not (root / "u00001.telemetry.json").exists()


def test_red_u0_gradient_ascent_adamw_refused_before_run_folder(tmp_path):
    bundle = fake_bundle(0)
    _group(bundle)["maximize"] = True
    raw, _ = state.to_verified_bytes(bundle)
    root, backup = tmp_path / "fake-run", tmp_path / "external-head"
    with pytest.raises(bridge.StructuredJournalRefusal,
                       match="OPTIMIZER_MAXIMIZE_NOT_V5_MINIMIZATION"):
        bridge.open_synthetic_journal(
            root=root, custody=backup, run_id="v5-synthetic-bridge",
            horizon=3, panel_sha256="c" * 64, config_sha256="d" * 64,
            rights_sha256="b" * 64, gene_axis_sha256="a" * 64,
            source_manifest_sha256="f" * 64,
            philox_contract_sha256="e" * 64, keyed_run_seed=73,
            state_bytes=raw, reported_probe=probe(0, raw))
    assert not root.exists()


def test_red_non_scalar_optimizer_flag_is_a_typed_refusal(tmp_path):
    root, backup, _ = open_synthetic(tmp_path)
    journal.begin_attempt(root, backup, update=1)
    bundle = fake_bundle(1)
    _group(bundle)["foreach"] = torch.tensor([1.0])
    raw, _ = state.to_verified_bytes(bundle)
    with pytest.raises(bridge.StructuredJournalRefusal,
                       match="OPTIMIZER_GROUP_FIELD_NOT_PLAIN"):
        submit(root, backup, 1, raw)
    assert not (root / "u00001.state.bin").exists()
