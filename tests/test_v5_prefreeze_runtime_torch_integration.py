import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"
MODULE_PATH = ROOT / "src/sea_ad_jepa/v5/prefreeze_runtime_authority.py"

spec = importlib.util.spec_from_file_location("prefreeze_runtime_authority_torch", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
Authority = module.PrefreezeMechanicalAuthorityV1
Guard = module.PrefreezeOptimizerGuardV1
PrefreezeGovernanceError = module.PrefreezeGovernanceError
StepCompletionError = module.StepCompletionError


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _state():
    return json.loads(STATE_PATH.read_text())


def _guard(param):
    optimizer = torch.optim.SGD([param], lr=0.1)
    authority = Authority.issue(
        governance_state=_state(),
        optimizer_identity="torch.optim.SGD:lr=0.1",
        checkpoint_digest=_sha("checkpoint-A"),
    )
    guard = Guard(authority, optimizer)
    token = guard.begin_step(authority.optimizer_identity, authority.checkpoint_digest)
    return authority, optimizer, guard, token


def test_real_torch_optimizer_step_is_observed_by_bound_hooks():
    param = torch.nn.Parameter(torch.tensor([2.0], dtype=torch.float32))
    _, optimizer, guard, token = _guard(param)
    before = param.detach().clone()

    loss = (param.square()).sum()
    loss.backward()
    guard.mark_unscaled(token)
    guard.mark_gradients_valid(token)
    guard.run_optimizer_step(token)

    assert guard.assert_step_complete(token) is True
    assert not torch.equal(param.detach(), before)
    optimizer.zero_grad(set_to_none=True)


def test_authority_optimizer_identity_cannot_lie_about_real_optimizer_configuration():
    param = torch.nn.Parameter(torch.tensor([2.0], dtype=torch.float32))
    optimizer = torch.optim.SGD([param], lr=0.1)
    authority = Authority.issue(
        governance_state=_state(),
        optimizer_identity="torch.optim.AdamW:lr=0.001",
        checkpoint_digest=_sha("checkpoint-A"),
    )

    with pytest.raises(PrefreezeGovernanceError, match="optimizer.*configuration|optimizer.*identity"):
        Guard(authority, optimizer)


def test_cpu_gradscaler_finite_step_completes_through_guard():
    param = torch.nn.Parameter(torch.tensor([2.0], dtype=torch.float32))
    _, optimizer, guard, token = _guard(param)
    scaler = torch.amp.GradScaler("cpu")
    before = param.detach().clone()

    loss = (param.square()).sum()
    scaler.scale(loss).backward()
    scaler.unscale_(optimizer)
    guard.mark_unscaled(token)
    guard.mark_gradients_valid(token)

    guard.run_scaler_step(token, scaler)
    scaler.update()

    assert guard.assert_step_complete(token) is True
    assert not torch.equal(param.detach(), before)


def test_cpu_gradscaler_nonfinite_skip_cannot_complete_step_or_authorize_ema():
    param = torch.nn.Parameter(torch.tensor([2.0], dtype=torch.float32))
    _, optimizer, guard, token = _guard(param)
    scaler = torch.amp.GradScaler("cpu")
    before = param.detach().clone()

    loss = (param * torch.tensor(float("inf"))).sum()
    scaler.scale(loss).backward()
    scaler.unscale_(optimizer)
    guard.mark_unscaled(token)
    # Deliberately simulate a buggy external validator. The scaler itself must remain an
    # independent physical barrier: if it skips optimizer.step(), EMA still cannot advance.
    guard.mark_gradients_valid(token)

    with pytest.raises(StepCompletionError, match="scaler.*skipped|did not complete"):
        guard.run_scaler_step(token, scaler)
    scaler.update()

    assert torch.equal(param.detach(), before)
    with pytest.raises(StepCompletionError):
        guard.assert_step_complete(token)
    with pytest.raises(StepCompletionError):
        guard.run_ema(token, lambda: None)
