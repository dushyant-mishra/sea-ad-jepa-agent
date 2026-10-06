"""Non-authorizing V5 runtime mechanics bound to the V3 prefreeze state.

This module selectively recovers mechanical safety ideas from the historical
V64 training-authority / optimizer-guard lineage while deliberately refusing
its scientific authority graph.  It is a rehearsal surface, not a training
authority: the canonical V3 governance state must remain OFF/SEALED/PROTECTED.

The optimizer guard is installed on the optimizer object itself and observes
that object's pre/post step hooks.  It does not trust a caller-supplied step
counter or a caller assertion that a step occurred.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


GOVERNANCE_SCHEMA = "JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006"
AUTHORITY_SCHEMA = "V5_PREFREEZE_MECHANICAL_AUTHORITY_V1"
START_RECEIPT_SCHEMA = "V5_PREFREEZE_START_CHECKPOINT_RECEIPT_V1"
COMPLETED_RECEIPT_SCHEMA = "V5_PREFREEZE_COMPLETED_CHECKPOINT_RECEIPT_V1"
STEP_TOKEN_KWARG = "v5_prefreeze_guard_step_token"


class PrefreezeGovernanceError(RuntimeError):
    """The current prefreeze governance does not permit the requested action."""


class StepCompletionError(RuntimeError):
    """A guarded optimizer/EMA transition is incomplete or invalid."""


def _digest(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise PrefreezeGovernanceError(f"{name} must be lowercase SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise PrefreezeGovernanceError(f"{name} must be lowercase SHA-256") from exc
    return value


def _nonempty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PrefreezeGovernanceError(f"{name} must be non-empty")
    return value.strip()


def _canonical_prefreeze_governance(state: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(state, Mapping):
        raise PrefreezeGovernanceError("governance state must be a mapping")
    if state.get("schema") != GOVERNANCE_SCHEMA:
        raise PrefreezeGovernanceError(f"governance schema must be {GOVERNANCE_SCHEMA}")
    required = {
        "role": "PROSPECTIVE_SCIENTIFIC_GOVERNANCE__PREFREEZE_ONLY",
        "training_authorized": False,
        "multimodal_training_authorized": False,
        "stage_a_execution_authorized": False,
        "stage4_authorized": False,
        "five_hundred_k_authorized": False,
        "optimizer_updates_during_target_discrimination": 0,
        "ema_updates_during_target_discrimination": 0,
        "test_state": "SEALED",
        "morabito_state": "PROTECTED",
        "production_target_winner": None,
        "representation_winner": None,
        "selected_estimand": "UNSET_REQUIRES_APPROVAL",
        "deciding_numeric_thresholds": "UNSET_REQUIRES_APPROVAL",
    }
    for key, expected in required.items():
        if state.get(key) != expected:
            raise PrefreezeGovernanceError(
                f"prefreeze mechanical authority requires {key}={expected!r}"
            )
    try:
        return json.loads(
            json.dumps(
                dict(state),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
        )
    except (TypeError, ValueError) as exc:
        raise PrefreezeGovernanceError("governance state must be canonical JSON") from exc


class PrefreezeMechanicalAuthorityV1:
    """Digest-bound rehearsal authority that cannot authorize execution."""

    def __init__(
        self,
        *,
        governance_digest: str,
        optimizer_identity: str,
        checkpoint_digest: str,
        authority_digest: str,
    ) -> None:
        self.governance_digest = _sha256(governance_digest, "governance_digest")
        self.optimizer_identity = _nonempty(optimizer_identity, "optimizer identity")
        self.checkpoint_digest = _sha256(checkpoint_digest, "checkpoint digest")
        self.authority_digest = _sha256(authority_digest, "authority digest")
        self.rehearsal_only = True
        self.training_authorized = False
        self.execution_authorized = False
        self._validate_digest()

    @classmethod
    def issue(
        cls,
        *,
        governance_state: Mapping[str, Any],
        optimizer_identity: str,
        checkpoint_digest: str,
    ) -> "PrefreezeMechanicalAuthorityV1":
        core = _canonical_prefreeze_governance(governance_state)
        optimizer_identity = _nonempty(optimizer_identity, "optimizer identity")
        checkpoint_digest = _sha256(checkpoint_digest, "checkpoint digest")
        governance_digest = _digest(core)
        authority_core = {
            "schema": AUTHORITY_SCHEMA,
            "governance_digest": governance_digest,
            "optimizer_identity": optimizer_identity,
            "checkpoint_digest": checkpoint_digest,
            "rehearsal_only": True,
            "training_authorized": False,
            "execution_authorized": False,
        }
        return cls(
            governance_digest=governance_digest,
            optimizer_identity=optimizer_identity,
            checkpoint_digest=checkpoint_digest,
            authority_digest=_digest(authority_core),
        )

    def _core(self) -> dict[str, Any]:
        return {
            "schema": AUTHORITY_SCHEMA,
            "governance_digest": self.governance_digest,
            "optimizer_identity": self.optimizer_identity,
            "checkpoint_digest": self.checkpoint_digest,
            "rehearsal_only": True,
            "training_authorized": False,
            "execution_authorized": False,
        }

    def _validate_digest(self) -> None:
        if self.rehearsal_only is not True:
            raise PrefreezeGovernanceError("prefreeze authority must remain rehearsal-only")
        if self.training_authorized or self.execution_authorized:
            raise PrefreezeGovernanceError("prefreeze authority cannot authorize execution")
        if self.authority_digest != _digest(self._core()):
            raise PrefreezeGovernanceError("authority digest mismatch")

    def start_checkpoint_receipt(self) -> dict[str, Any]:
        self._validate_digest()
        core = {
            "schema": START_RECEIPT_SCHEMA,
            "authority_digest": self.authority_digest,
            "governance_digest": self.governance_digest,
            "optimizer_identity": self.optimizer_identity,
            "checkpoint_digest": self.checkpoint_digest,
            "rehearsal_only": True,
            "training_authorized": False,
            "execution_authorized": False,
        }
        return {**core, "receipt_digest": _digest(core)}

    @classmethod
    def reload_start_checkpoint(
        cls, receipt: Mapping[str, Any], observed_checkpoint_digest: str
    ) -> "PrefreezeMechanicalAuthorityV1":
        if receipt.get("schema") != START_RECEIPT_SCHEMA:
            raise PrefreezeGovernanceError("start checkpoint receipt schema mismatch")
        if receipt.get("rehearsal_only") is not True:
            raise PrefreezeGovernanceError("non-rehearsal reload is forbidden")
        if receipt.get("training_authorized") is not False or receipt.get("execution_authorized") is not False:
            raise PrefreezeGovernanceError("prefreeze receipt cannot authorize execution")
        observed = _sha256(observed_checkpoint_digest, "checkpoint digest")
        expected = _sha256(receipt.get("checkpoint_digest"), "checkpoint digest")
        if observed != expected:
            raise PrefreezeGovernanceError("checkpoint digest mismatch on reload")
        core = {
            "schema": START_RECEIPT_SCHEMA,
            "authority_digest": receipt.get("authority_digest"),
            "governance_digest": receipt.get("governance_digest"),
            "optimizer_identity": receipt.get("optimizer_identity"),
            "checkpoint_digest": expected,
            "rehearsal_only": True,
            "training_authorized": False,
            "execution_authorized": False,
        }
        if receipt.get("receipt_digest") != _digest(core):
            raise PrefreezeGovernanceError("start checkpoint receipt digest mismatch")
        return cls(
            governance_digest=receipt.get("governance_digest"),
            optimizer_identity=receipt.get("optimizer_identity"),
            checkpoint_digest=expected,
            authority_digest=receipt.get("authority_digest"),
        )

    @classmethod
    def verify_completed_checkpoint_receipt(
        cls, receipt: Mapping[str, Any], observed_checkpoint_digest: str
    ) -> dict[str, Any]:
        if receipt.get("schema") != COMPLETED_RECEIPT_SCHEMA:
            raise PrefreezeGovernanceError("completed checkpoint receipt schema mismatch")
        if receipt.get("rehearsal_only") is not True:
            raise PrefreezeGovernanceError("non-rehearsal completed receipt is forbidden")
        if receipt.get("training_authorized") is not False or receipt.get("execution_authorized") is not False:
            raise PrefreezeGovernanceError("prefreeze receipt cannot authorize execution")
        observed = _sha256(observed_checkpoint_digest, "checkpoint digest")
        expected = _sha256(receipt.get("checkpoint_digest"), "checkpoint digest")
        parent = _sha256(receipt.get("parent_checkpoint_digest"), "parent checkpoint digest")
        if observed != expected:
            raise PrefreezeGovernanceError("checkpoint digest mismatch on reload")
        if expected == parent:
            raise PrefreezeGovernanceError("completed checkpoint must be a new state")
        core = {
            "schema": COMPLETED_RECEIPT_SCHEMA,
            "authority_digest": _sha256(receipt.get("authority_digest"), "authority digest"),
            "governance_digest": _sha256(receipt.get("governance_digest"), "governance digest"),
            "optimizer_identity": _nonempty(receipt.get("optimizer_identity"), "optimizer identity"),
            "parent_checkpoint_digest": parent,
            "checkpoint_digest": expected,
            "guarded_step_token": _nonempty(receipt.get("guarded_step_token"), "guarded step token"),
            "rehearsal_only": True,
            "training_authorized": False,
            "execution_authorized": False,
        }
        if receipt.get("receipt_digest") != _digest(core):
            raise PrefreezeGovernanceError("completed checkpoint receipt digest mismatch")
        expected_authority = _digest(
            {
                "schema": AUTHORITY_SCHEMA,
                "governance_digest": core["governance_digest"],
                "optimizer_identity": core["optimizer_identity"],
                "checkpoint_digest": parent,
                "rehearsal_only": True,
                "training_authorized": False,
                "execution_authorized": False,
            }
        )
        if core["authority_digest"] != expected_authority:
            raise PrefreezeGovernanceError("parent authority digest mismatch")
        return core


class PrefreezeOptimizerGuardV1:
    """Optimizer-bound one-shot guard mirroring the historical V4 hook pattern."""

    def __init__(self, authority: PrefreezeMechanicalAuthorityV1, optimizer: Any) -> None:
        if not isinstance(authority, PrefreezeMechanicalAuthorityV1):
            raise PrefreezeGovernanceError("PrefreezeMechanicalAuthorityV1 required")
        authority._validate_digest()
        for name in ("step", "register_step_pre_hook", "register_step_post_hook"):
            if not callable(getattr(optimizer, name, None)):
                raise PrefreezeGovernanceError(f"optimizer must provide {name}()")
        self.authority = authority
        self.optimizer = optimizer
        self._counter = 0
        self._steps: dict[str, dict[str, Any]] = {}
        self._armed: str | None = None
        self._consumed: str | None = None
        self._closed = False
        self._pre_handle = optimizer.register_step_pre_hook(self._pre_step)
        self._post_handle = optimizer.register_step_post_hook(self._post_step)

    def _ensure_open(self) -> None:
        if self._closed:
            raise StepCompletionError("optimizer guard is closed")
        self.authority._validate_digest()

    def begin_step(self, optimizer_identity: str, checkpoint_digest: str) -> str:
        self._ensure_open()
        if optimizer_identity != self.authority.optimizer_identity:
            raise PrefreezeGovernanceError("optimizer identity mismatch")
        if _sha256(checkpoint_digest, "checkpoint digest") != self.authority.checkpoint_digest:
            raise PrefreezeGovernanceError("checkpoint digest mismatch")
        if self._armed is not None or self._consumed is not None:
            raise StepCompletionError("prior optimizer authorization is still active")
        token = f"prefreeze-step-{self._counter:08d}"
        self._counter += 1
        self._steps[token] = {
            "unscaled": False,
            "gradients_valid": False,
            "optimizer_completed": False,
            "ema_completed": False,
            "rejected": False,
            "ema_consumed": False,
        }
        self._armed = token
        return token

    def _step_state(self, token: str) -> dict[str, Any]:
        try:
            return self._steps[token]
        except KeyError as exc:
            raise StepCompletionError("unknown guarded step token") from exc

    def mark_unscaled(self, token: str) -> None:
        step = self._step_state(token)
        if step["rejected"] or step["optimizer_completed"]:
            raise StepCompletionError("cannot unscale a closed step")
        step["unscaled"] = True

    def mark_gradients_valid(self, token: str) -> None:
        step = self._step_state(token)
        if not step["unscaled"]:
            raise StepCompletionError("gradients must be unscaled before validation")
        if step["rejected"] or step["optimizer_completed"]:
            raise StepCompletionError("cannot validate gradients on a closed step")
        step["gradients_valid"] = True

    def reject_step(self, token: str, reason: str) -> None:
        step = self._step_state(token)
        if step["optimizer_completed"]:
            raise StepCompletionError("cannot reject a completed optimizer step")
        step["rejected"] = True
        step["reject_reason"] = str(reason)
        if self._armed == token:
            self._armed = None

    def _pre_step(self, optimizer: Any, args: tuple[Any, ...], kwargs: dict[str, Any]):
        self._ensure_open()
        if optimizer is not self.optimizer:
            raise StepCompletionError("optimizer identity object mismatch")
        token = kwargs.pop(STEP_TOKEN_KWARG, None)
        if self._armed is None or token != self._armed:
            expected = self._armed
            self._armed = None
            raise StepCompletionError(
                f"optimizer step not armed for supplied token; expected={expected!r} observed={token!r}"
            )
        step = self._step_state(token)
        if step["rejected"] or not step["unscaled"] or not step["gradients_valid"]:
            self._armed = None
            raise StepCompletionError("optimizer step requires unscaled validated gradients")
        if self._consumed is not None:
            self._armed = None
            raise StepCompletionError("optimizer authorization replay")
        self._consumed = token
        return args, kwargs

    def _post_step(self, optimizer: Any, args: tuple[Any, ...], kwargs: dict[str, Any]):
        self._ensure_open()
        if optimizer is not self.optimizer or self._consumed is None:
            self._armed = None
            raise StepCompletionError("optimizer post-step lacks consumed authorization")
        token = self._consumed
        step = self._step_state(token)
        step["optimizer_completed"] = True
        self._armed = None

    def run_optimizer_step(self, token: str) -> Any:
        step = self._step_state(token)
        if step["rejected"]:
            raise StepCompletionError("rejected step cannot execute optimizer")
        if not step["unscaled"] or not step["gradients_valid"]:
            raise StepCompletionError("optimizer step requires unscaled validated gradients")
        try:
            result = self.optimizer.step(**{STEP_TOKEN_KWARG: token})
        except Exception:
            step["rejected"] = True
            self._armed = None
            self._consumed = None
            raise
        if self._consumed != token or not step["optimizer_completed"]:
            step["rejected"] = True
            self._armed = None
            self._consumed = None
            raise StepCompletionError("guarded optimizer step did not complete")
        self._consumed = None
        return result

    def assert_step_complete(self, token: str) -> bool:
        step = self._step_state(token)
        if step["rejected"] or not step["optimizer_completed"]:
            raise StepCompletionError("guarded optimizer step did not complete")
        return True

    def run_ema(self, token: str, ema_callable: Any) -> Any:
        step = self._step_state(token)
        self.assert_step_complete(token)
        if step["ema_consumed"]:
            raise StepCompletionError("EMA authorization already consumed")
        if not callable(ema_callable):
            raise StepCompletionError("EMA callback is required")
        step["ema_consumed"] = True
        try:
            result = ema_callable()
        except Exception:
            step["rejected"] = True
            raise
        step["ema_completed"] = True
        return result

    def completed_checkpoint_receipt(self, token: str, checkpoint_digest: str) -> dict[str, Any]:
        step = self._step_state(token)
        self.assert_step_complete(token)
        if step["rejected"] or not step["ema_completed"]:
            raise StepCompletionError("completed checkpoint requires successful EMA")
        checkpoint_digest = _sha256(checkpoint_digest, "checkpoint digest")
        if checkpoint_digest == self.authority.checkpoint_digest:
            raise PrefreezeGovernanceError("completed checkpoint must be a new state")
        core = {
            "schema": COMPLETED_RECEIPT_SCHEMA,
            "authority_digest": self.authority.authority_digest,
            "governance_digest": self.authority.governance_digest,
            "optimizer_identity": self.authority.optimizer_identity,
            "parent_checkpoint_digest": self.authority.checkpoint_digest,
            "checkpoint_digest": checkpoint_digest,
            "guarded_step_token": token,
            "rehearsal_only": True,
            "training_authorized": False,
            "execution_authorized": False,
        }
        return {**core, "receipt_digest": _digest(core)}

    def close(self) -> None:
        if not self._closed:
            self._pre_handle.remove()
            self._post_handle.remove()
            self._armed = None
            self._consumed = None
            self._closed = True
