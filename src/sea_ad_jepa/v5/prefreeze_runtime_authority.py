"""Prefreeze-compatible V5 runtime safety core.

This module recovers only the mechanical guarantees from the historical V64
training-authority lineage. It deliberately does not import or recognize the
old E2/target-specific scientific authority graph.

The canonical V3 premise state currently has training and Stage-A execution
turned off, so it cannot issue an authority. Tests may use an explicit
``test_only`` future-state fixture to exercise the mechanics without changing
canonical governance. Production authority issuance is intentionally disabled
until a separate future execution-authority schema is prospectively frozen.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Mapping


GOVERNANCE_SCHEMA = "JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006"
AUTHORITY_SCHEMA = "V5_PREFREEZE_RUNTIME_AUTHORITY_V1"
RECEIPT_SCHEMA = "V5_PREFREEZE_RUNTIME_AUTHORITY_RECEIPT_V1"
COMPLETED_CHECKPOINT_RECEIPT_SCHEMA = "V5_PREFREEZE_COMPLETED_CHECKPOINT_RECEIPT_V1"


class PrefreezeGovernanceError(RuntimeError):
    """Current scientific governance does not permit the requested action."""


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


def _governance_core(state: Mapping[str, Any]) -> dict[str, Any]:
    if state.get("schema") != GOVERNANCE_SCHEMA:
        raise PrefreezeGovernanceError(
            f"governance schema must be {GOVERNANCE_SCHEMA}"
        )
    if state.get("training_authorized") is not True:
        raise PrefreezeGovernanceError("training_authorized=false; runtime authority refused")
    if state.get("stage_a_execution_authorized") is not True:
        raise PrefreezeGovernanceError(
            "stage_a_execution_authorized=false; runtime authority refused"
        )
    # Bind the entire machine-readable governance object, not a hand-picked
    # subset. Any scientific/governance mutation must change the authority
    # digest even though this adapter remains test-only.
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


class CurrentTrainingAuthorityV2:
    """Digest-bound test authority for exercising recovered runtime mechanics.

    This prefreeze adapter cannot issue production authority. A later,
    independently governed execution-authority schema must replace that gap.
    """

    def __init__(
        self,
        *,
        governance_digest: str,
        optimizer_identity: str,
        checkpoint_digest: str,
        test_only: bool,
        authority_digest: str,
    ) -> None:
        self.governance_digest = _sha256(governance_digest, "governance_digest")
        if not isinstance(optimizer_identity, str) or not optimizer_identity.strip():
            raise PrefreezeGovernanceError("optimizer identity must be non-empty")
        self.optimizer_identity = optimizer_identity
        self.checkpoint_digest = _sha256(checkpoint_digest, "checkpoint digest")
        self.test_only = bool(test_only)
        if self.test_only is not True:
            raise PrefreezeGovernanceError(
                "production issuance disabled until separate execution authority exists"
            )
        self.authority_digest = _sha256(authority_digest, "authority_digest")
        self._validate_digest()

    @classmethod
    def issue(
        cls,
        *,
        governance_state: Mapping[str, Any],
        optimizer_identity: str,
        checkpoint_digest: str,
        test_only: bool = False,
    ) -> "CurrentTrainingAuthorityV2":
        core = _governance_core(governance_state)
        if test_only is not True:
            raise PrefreezeGovernanceError(
                "production issuance disabled until separate execution authority exists"
            )
        if not isinstance(optimizer_identity, str) or not optimizer_identity.strip():
            raise PrefreezeGovernanceError("optimizer identity must be non-empty")
        checkpoint_digest = _sha256(checkpoint_digest, "checkpoint digest")
        governance_digest = _digest(core)
        authority_core = {
            "schema": AUTHORITY_SCHEMA,
            "governance_digest": governance_digest,
            "optimizer_identity": optimizer_identity,
            "checkpoint_digest": checkpoint_digest,
            "test_only": True,
        }
        return cls(
            governance_digest=governance_digest,
            optimizer_identity=optimizer_identity,
            checkpoint_digest=checkpoint_digest,
            test_only=True,
            authority_digest=_digest(authority_core),
        )

    def _authority_core(self) -> dict[str, Any]:
        return {
            "schema": AUTHORITY_SCHEMA,
            "governance_digest": self.governance_digest,
            "optimizer_identity": self.optimizer_identity,
            "checkpoint_digest": self.checkpoint_digest,
            "test_only": self.test_only,
        }

    def _validate_digest(self) -> None:
        if self.test_only is not True:
            raise PrefreezeGovernanceError("non-test runtime authority is forbidden")
        if self.authority_digest != _digest(self._authority_core()):
            raise PrefreezeGovernanceError("authority digest mismatch")

    def checkpoint_receipt(self) -> dict[str, Any]:
        """Receipt for the exact starting checkpoint bound to this authority."""
        self._validate_digest()
        core = {
            "schema": RECEIPT_SCHEMA,
            "authority_digest": self.authority_digest,
            "governance_digest": self.governance_digest,
            "optimizer_identity": self.optimizer_identity,
            "checkpoint_digest": self.checkpoint_digest,
            "test_only": True,
        }
        return {**core, "receipt_digest": _digest(core)}

    def completed_checkpoint_receipt(self, checkpoint_digest: str) -> dict[str, Any]:
        """Bind a new post-update checkpoint to its exact starting checkpoint."""
        self._validate_digest()
        checkpoint_digest = _sha256(checkpoint_digest, "checkpoint digest")
        if checkpoint_digest == self.checkpoint_digest:
            raise PrefreezeGovernanceError(
                "completed checkpoint must represent a new post-update state"
            )
        core = {
            "schema": COMPLETED_CHECKPOINT_RECEIPT_SCHEMA,
            "authority_digest": self.authority_digest,
            "governance_digest": self.governance_digest,
            "optimizer_identity": self.optimizer_identity,
            "parent_checkpoint_digest": self.checkpoint_digest,
            "checkpoint_digest": checkpoint_digest,
            "test_only": True,
        }
        return {**core, "receipt_digest": _digest(core)}

    @classmethod
    def verify_completed_checkpoint_receipt(
        cls, receipt: Mapping[str, Any], observed_checkpoint_digest: str
    ) -> dict[str, Any]:
        """Verify exact post-update bytes and their parent-state lineage."""
        if receipt.get("schema") != COMPLETED_CHECKPOINT_RECEIPT_SCHEMA:
            raise PrefreezeGovernanceError("completed checkpoint receipt schema mismatch")
        if receipt.get("test_only") is not True:
            raise PrefreezeGovernanceError(
                "production reload disabled until separate execution authority exists"
            )
        observed = _sha256(observed_checkpoint_digest, "checkpoint digest")
        expected = _sha256(receipt.get("checkpoint_digest"), "checkpoint digest")
        parent = _sha256(
            receipt.get("parent_checkpoint_digest"), "parent checkpoint digest"
        )
        governance_digest = _sha256(
            receipt.get("governance_digest"), "governance_digest"
        )
        optimizer_identity = receipt.get("optimizer_identity")
        if not isinstance(optimizer_identity, str) or not optimizer_identity.strip():
            raise PrefreezeGovernanceError("optimizer identity must be non-empty")
        if observed != expected:
            raise PrefreezeGovernanceError("checkpoint digest mismatch on reload")
        if expected == parent:
            raise PrefreezeGovernanceError(
                "completed checkpoint must represent a new post-update state"
            )

        expected_authority_digest = _digest(
            {
                "schema": AUTHORITY_SCHEMA,
                "governance_digest": governance_digest,
                "optimizer_identity": optimizer_identity,
                "checkpoint_digest": parent,
                "test_only": True,
            }
        )
        authority_digest = _sha256(
            receipt.get("authority_digest"), "authority digest"
        )
        if authority_digest != expected_authority_digest:
            raise PrefreezeGovernanceError("parent authority digest mismatch")

        core = {
            "schema": COMPLETED_CHECKPOINT_RECEIPT_SCHEMA,
            "authority_digest": authority_digest,
            "governance_digest": governance_digest,
            "optimizer_identity": optimizer_identity,
            "parent_checkpoint_digest": parent,
            "checkpoint_digest": expected,
            "test_only": True,
        }
        if receipt.get("receipt_digest") != _digest(core):
            raise PrefreezeGovernanceError("completed checkpoint receipt digest mismatch")
        return core

    @classmethod
    def reload(
        cls, receipt: Mapping[str, Any], observed_checkpoint_digest: str
    ) -> "CurrentTrainingAuthorityV2":
        """Reload the exact starting checkpoint receipt (pre-update path)."""
        if receipt.get("schema") != RECEIPT_SCHEMA:
            raise PrefreezeGovernanceError("runtime receipt schema mismatch")
        if receipt.get("test_only") is not True:
            raise PrefreezeGovernanceError(
                "production reload disabled until separate execution authority exists"
            )
        observed_checkpoint_digest = _sha256(
            observed_checkpoint_digest, "checkpoint digest"
        )
        expected_checkpoint = _sha256(
            receipt.get("checkpoint_digest"), "checkpoint digest"
        )
        if observed_checkpoint_digest != expected_checkpoint:
            raise PrefreezeGovernanceError("checkpoint digest mismatch on reload")
        core = {
            "schema": RECEIPT_SCHEMA,
            "authority_digest": receipt.get("authority_digest"),
            "governance_digest": receipt.get("governance_digest"),
            "optimizer_identity": receipt.get("optimizer_identity"),
            "checkpoint_digest": expected_checkpoint,
            "test_only": True,
        }
        if receipt.get("receipt_digest") != _digest(core):
            raise PrefreezeGovernanceError("runtime receipt digest mismatch")
        return cls(
            governance_digest=receipt.get("governance_digest"),
            optimizer_identity=receipt.get("optimizer_identity"),
            checkpoint_digest=expected_checkpoint,
            test_only=True,
            authority_digest=receipt.get("authority_digest"),
        )


class OptimizerGuardV4:
    """One-shot state machine that proves a step completed before EMA."""

    def __init__(self, authority: CurrentTrainingAuthorityV2) -> None:
        if not isinstance(authority, CurrentTrainingAuthorityV2):
            raise PrefreezeGovernanceError("CurrentTrainingAuthorityV2 required")
        authority._validate_digest()
        self.authority = authority
        self._counter = 0
        self._steps: dict[str, dict[str, Any]] = {}

    def begin_step(self, optimizer_identity: str, checkpoint_digest: str) -> str:
        self.authority._validate_digest()
        if optimizer_identity != self.authority.optimizer_identity:
            raise PrefreezeGovernanceError("optimizer identity mismatch")
        if _sha256(checkpoint_digest, "checkpoint digest") != self.authority.checkpoint_digest:
            raise PrefreezeGovernanceError("checkpoint digest mismatch")
        token = f"step-{self._counter:08d}"
        self._counter += 1
        self._steps[token] = {
            "unscaled": False,
            "gradients_valid": False,
            "step_complete": False,
            "rejected": False,
            "reject_reason": None,
            "ema_consumed": False,
        }
        return token

    def _step(self, token: str) -> dict[str, Any]:
        try:
            return self._steps[token]
        except KeyError as exc:
            raise StepCompletionError("unknown guarded step token") from exc

    def mark_unscaled(self, token: str) -> None:
        step = self._step(token)
        if step["rejected"] or step["step_complete"]:
            raise StepCompletionError("cannot unscale a closed step")
        step["unscaled"] = True

    def mark_gradients_valid(self, token: str) -> None:
        step = self._step(token)
        if not step["unscaled"]:
            raise StepCompletionError("gradients must be unscaled before validation")
        if step["rejected"] or step["step_complete"]:
            raise StepCompletionError("cannot validate gradients on a closed step")
        step["gradients_valid"] = True

    def reject_step(self, token: str, reason: str) -> None:
        step = self._step(token)
        if step["step_complete"]:
            raise StepCompletionError("cannot reject a completed optimizer step")
        step["rejected"] = True
        step["reject_reason"] = str(reason)

    def run_optimizer_step(self, token: str, step_callable: Callable[[], Any]) -> Any:
        step = self._step(token)
        if step["rejected"]:
            raise StepCompletionError("rejected step cannot execute optimizer")
        if not step["unscaled"] or not step["gradients_valid"]:
            raise StepCompletionError(
                "optimizer step requires unscaled and validated gradients"
            )
        if step["step_complete"]:
            raise StepCompletionError("optimizer step already completed")
        if not callable(step_callable):
            raise StepCompletionError("optimizer step callable required")
        try:
            result = step_callable()
        except Exception:
            step["rejected"] = True
            step["reject_reason"] = "optimizer callable raised"
            raise
        step["step_complete"] = True
        return result

    def assert_step_complete(self, token: str) -> bool:
        step = self._step(token)
        if step["rejected"] or not step["step_complete"]:
            raise StepCompletionError("guarded optimizer step did not complete")
        return True

    def authorize_ema(self, token: str) -> bool:
        step = self._step(token)
        if step["ema_consumed"]:
            raise StepCompletionError("EMA authorization already consumed")
        if step["rejected"] or not step["step_complete"]:
            raise StepCompletionError("EMA forbidden before successful optimizer step")
        step["ema_consumed"] = True
        return True
