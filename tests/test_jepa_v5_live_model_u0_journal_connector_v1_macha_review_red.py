"""Macha independent review of Sol #590 (a3a59eb9) and #591 (ff1141fe).

RED 1 (#590): the connector authenticates the 35 executed files under
repo_root, but records whatever ``sea_ad_jepa`` Python actually imported.
A second copy with an edited forward and identical initialization is
recorded as ACTUAL_ORIGINAL_V5 U0.
RED 2 (#591): the durable original_v5_u0_only policy is opt-in. Authentic
original V5 U0 bytes open in the legacy lane without it, and a fabricated
u1 then commits as UPDATE_COMMITTED.

Only initialized CPU modules, manually assigned (fabricated) Adam slots and
fake journal bytes. The imported autouse fixture makes any optimizer step,
backward, autograd.grad or guarded/reference update raise; the child
process installs the same patches. No forward, EMA, GPU or real RNA.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import torch

from scripts.v5 import jepa_synth2048_attempt_journal_v2 as journal
from scripts.v5 import jepa_v5_full_state_readonly_audit_v1 as state
from scripts.v5 import jepa_v5_live_model_u0_journal_connector_v1 as live
from scripts.v5 import jepa_v5_structured_journal_preflight_v1 as bridge
from tests.test_jepa_v5_live_model_u0_journal_connector_v1 import (  # noqa: F401
    ROOT, capture, caller_reported_probe,
    forbid_all_actual_training_mutations_in_this_module, public_contract, real_v5,
)

CHILD = r'''
import sys
from pathlib import Path
from unittest.mock import patch
src, root, fit = sys.argv[1:4]
sys.path[:0] = [src, root]
import torch
boom = AssertionError("REAL_OPTIMIZER_BACKWARD_EMA_EXECUTION_FORBIDDEN")
for owner, name in ((torch.optim.Optimizer, "step"), (torch.optim.AdamW, "step"),
                    (torch.Tensor, "backward"), (torch.autograd, "backward"),
                    (torch.autograd, "grad")):
    patch.object(owner, name, side_effect=boom).start()
from sea_ad_jepa.v5 import inactive_update_reference as ref
from scripts.v5 import jepa_v5_live_model_u0_journal_connector_v1 as live
from scripts.v5 import jepa_v5_pipeline_identity_contract_v1 as pic
doc = pic.load_contract(Path(root) / pic.CONTRACT_PATH)
modules = ref.build_reference_modules(**live.CONFIG)
print("LOADED_FROM", Path(ref.__file__).resolve())
try:
    snap = live.capture_real_v5_u0(modules=modules, repo_root=Path(root),
                                   public_fit_zip=Path(fit),
                                   expected_contract=doc, run_id="import-check")
    print("CAPTURED_AS_AUTHENTIC", snap.snapshot_sha256)
except live.LiveV5JournalRefusal as exc:
    print("REFUSED", exc)
'''


def _capture_in_child(src: Path) -> str:
    done = subprocess.run(
        [sys.executable, "-I", "-c", CHILD, str(src), str(ROOT),
         os.environ["JEPA_PUBLIC_DEV_FIT_ZIP"]],
        capture_output=True, text=True, timeout=300, check=False)
    assert done.returncode == 0, done.stderr[-1500:]
    return done.stdout


def test_control_verified_tree_import_is_captured(public_contract):
    out = _capture_in_child(ROOT / "src")
    assert f"LOADED_FROM {(ROOT / 'src').resolve()}" in out
    assert "CAPTURED_AS_AUTHENTIC" in out


def test_red_590_substituted_import_is_not_recorded_as_original(tmp_path, public_contract):
    shutil.copytree(ROOT / "src" / "sea_ad_jepa", tmp_path / "src" / "sea_ad_jepa")
    edited = tmp_path / "src/sea_ad_jepa/v5/keyed_dropout_prototype_v2.py"
    edited.write_text(edited.read_text(encoding="utf-8") +
                      "\n# substituted behaviour, identical initialization\n"
                      "KeyedIPBEncoderV2Reference.forward = lambda self, *a, **k: None\n",
                      encoding="utf-8")
    out = _capture_in_child(tmp_path / "src")
    assert f"LOADED_FROM {(tmp_path / 'src').resolve()}" in out
    assert "REFUSED" in out and "LOADED_V5_MODULE_NOT_FROM_VERIFIED_TREE" in out, out


def _fabricated_u1(modules, metadata) -> bytes:
    """Hand-assigned Adam slots: the fabrication the journal must not accept."""
    for group in modules.optimizer.param_groups:
        for parameter in group["params"]:
            modules.optimizer.state[parameter] = {
                "step": torch.tensor(1.0),
                "exp_avg": torch.zeros_like(parameter),
                "exp_avg_sq": torch.ones_like(parameter),
            }
    meta = dict(metadata, completed_updates=1, ema_updates=1, presentations_seen=8)
    bundle = state.capture_readonly_bundle(
        online=modules.online, teacher=modules.teacher,
        predictor=modules.predictor, optimizer=modules.optimizer, metadata=meta)
    return state.to_verified_bytes(bundle)[0]


def test_red_591_authentic_u0_cannot_open_the_legacy_fake_update_lane(
        tmp_path, public_contract):
    modules = real_v5()
    snap = capture(modules, public_contract)
    b = live._dev_journal_bindings(public_contract)
    root, custody = tmp_path / "downgraded", tmp_path / "outside"
    try:
        bridge.open_synthetic_journal(   # require_original_v5 left at its default
            root=root, custody=custody, run_id=snap.run_id, horizon=2,
            panel_sha256=b["panel_sha256"], config_sha256=b["config_sha256"],
            rights_sha256=b["rights_sha256"], gene_axis_sha256=b["gene_axis_sha256"],
            source_manifest_sha256=b["source_manifest_sha256"],
            philox_contract_sha256=b["philox_contract_sha256"],
            keyed_run_seed=b["keyed_run_seed"], state_bytes=snap.state_bytes,
            reported_probe=caller_reported_probe(snap))
    except bridge.StructuredJournalRefusal as exc:
        assert "ORIGINAL_V5_STRUCTURE_REQUIRES_U0_ONLY_LANE" in str(exc)
        assert not root.exists()
        return
    lock = json.loads((root / "run.lock.json").read_text(encoding="utf-8"))
    assert "original_v5_u0_only" not in lock
    journal.begin_attempt(root, custody, update=1)
    raw = _fabricated_u1(modules, snap.metadata)
    probe = dict(caller_reported_probe(snap), state_update=1,
                 state_payload_sha256=sha256(raw).hexdigest())
    out = bridge.commit_synthetic_preflight(
        root=root, custody=custody, update=1, state_bytes=raw, reported_probe=probe,
        expected_gene_axis_sha256=b["gene_axis_sha256"],
        expected_source_manifest_sha256=b["source_manifest_sha256"],
        expected_philox_contract_sha256=b["philox_contract_sha256"],
        expected_keyed_run_seed=b["keyed_run_seed"])
    pytest.fail("DOWNGRADE: authentic original V5 U0 opened without the U0-only "
                "lock and a fabricated u1 became " + out["journal"]["status"])


def test_control_connector_u0_journal_remains_forensically_inspectable(
        tmp_path, public_contract):
    modules = real_v5()
    snap = capture(modules, public_contract)
    root, custody = tmp_path / "original", tmp_path / "outside"
    live.record_real_v5_u0_to_journal(
        snapshot=snap, modules=modules, repo_root=ROOT,
        public_fit_zip=Path(os.environ["JEPA_PUBLIC_DEV_FIT_ZIP"]),
        expected_contract=public_contract, journal_root=root,
        external_custody=custody, horizon=2,
        caller_reported_probe=caller_reported_probe(snap))
    b = live._dev_journal_bindings(public_contract)
    seen = bridge.inspect_stored_structured_snapshot(
        root=root, custody=custody, update=0,
        expected_gene_axis_sha256=b["gene_axis_sha256"],
        expected_source_manifest_sha256=b["source_manifest_sha256"],
        expected_philox_contract_sha256=b["philox_contract_sha256"],
        expected_keyed_run_seed=b["keyed_run_seed"])
    assert seen["state"]["snapshot_sha256"] == snap.snapshot_sha256
    assert seen["resume_authorized"] is False
