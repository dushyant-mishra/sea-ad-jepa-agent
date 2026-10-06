"""Non-authorizing V5 runtime rehearsal mechanics bound to V3 prefreeze governance.

Only mechanical ideas are recovered from V64. No historical target/E2 authority
is imported. The canonical V3 state must remain OFF/SEALED/PROTECTED. This
surface permits exactly one guarded rehearsal update and can never authorize
Stage A or training.
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

EXPECTED_TOP_LEVEL_FIELDS = {
    "schema", "role", "training_authorized", "multimodal_training_authorized",
    "stage_a_execution_authorized", "stage4_authorized", "five_hundred_k_authorized",
    "optimizer_updates_during_target_discrimination", "ema_updates_during_target_discrimination",
    "test_state", "morabito_state", "production_target_winner", "representation_winner",
    "selected_estimand", "deciding_numeric_thresholds", "representation_families",
    "recoverability_semantics", "transport_axes", "observation_operator",
    "representation_stability", "uncertainty_axes", "ood_axes", "estimand_candidates",
    "hierarchical_tempering_parameter", "claim_ladder", "stage_a_maximum_claim",
    "stage_a_verdicts", "diagnostic_readout_firewall", "external_asset_rules", "source_documents",
}
EXPECTED_NESTED_FIELDS = {
    "recoverability_semantics": {
        "target_object_recoverability", "biological_truth_recoverability", "automatic_equivalence_forbidden",
    },
    "observation_operator": {
        "form", "allowed_descriptor_classes", "forbidden_free_shortcuts",
        "technology_invariance_is_not_blanket_requirement",
    },
    "representation_stability": {
        "primary_resampling_unit", "required_diagnostics", "statuses",
        "coordinate_claim_allowed_when_subspace_only", "alignment_fit_partition",
        "alignment_freeze_before_held_donor_evaluation", "held_out_donors_may_influence_alignment",
    },
    "uncertainty_axes": {
        "biological_evidence_convergence", "measurement_depth_convergence", "must_remain_separate",
    },
    "biological_evidence_convergence": {
        "purpose", "operator_class", "count_depth_thinning_forbidden", "exact_fractions",
    },
    "measurement_depth_convergence": {
        "purpose", "operator_class", "information_universe_fixed", "exact_fractions",
    },
    "diagnostic_readout_firewall": {
        "fit_partition", "freeze_before_held_donor_evaluation",
        "held_out_units_may_influence_fit", "authorizes_jepa_training",
    },
    "external_asset_rules": {
        "external_not_equal_independent", "access_not_equal_exposure",
        "same_nucleus_pairing_not_equal_separate_nucleus_evidence",
        "cell_count_cannot_substitute_for_donor_count",
        "observational_multimodal_support_is_not_causal",
        "protected_assets_forbidden_for_target_selection", "unknown_fields_fail_closed",
    },
}
START_RECEIPT_FIELDS = {
    "schema", "authority_digest", "governance_digest", "optimizer_identity",
    "checkpoint_digest", "rehearsal_only", "training_authorized",
    "execution_authorized", "receipt_digest",
}
COMPLETED_RECEIPT_FIELDS = {
    "schema", "authority_digest", "governance_digest", "optimizer_identity",
    "parent_checkpoint_digest", "checkpoint_digest", "guarded_step_token",
    "rehearsal_only", "training_authorized", "execution_authorized", "receipt_digest",
}


class PrefreezeGovernanceError(RuntimeError):
    pass


class StepCompletionError(RuntimeError):
    pass


def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


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


def _exact_fields(value: object, expected: set[str], label: str, *, governance: bool = True) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PrefreezeGovernanceError(f"{label} must be an object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        prefix = "governance " if governance else ""
        details = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if unknown:
            details.append("unknown=" + ",".join(unknown))
        raise PrefreezeGovernanceError(f"{prefix}{label} fields mismatch: {'; '.join(details)}")
    return value


def _canonical_prefreeze_governance(state: Mapping[str, Any]) -> dict[str, Any]:
    state = _exact_fields(state, EXPECTED_TOP_LEVEL_FIELDS, "contract")
    for key in (
        "recoverability_semantics", "observation_operator", "representation_stability",
        "uncertainty_axes", "diagnostic_readout_firewall", "external_asset_rules",
    ):
        _exact_fields(state.get(key), EXPECTED_NESTED_FIELDS[key], key)
    uncertainty = state["uncertainty_axes"]
    for key in ("biological_evidence_convergence", "measurement_depth_convergence"):
        _exact_fields(uncertainty.get(key), EXPECTED_NESTED_FIELDS[key], key)
    if state.get("schema") != GOVERNANCE_SCHEMA:
        raise PrefreezeGovernanceError(f"governance schema must be {GOVERNANCE_SCHEMA}")
    frozen = {
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
    for key, expected in frozen.items():
        if state.get(key) != expected:
            raise PrefreezeGovernanceError(f"prefreeze mechanical authority requires {key}={expected!r}")
    try:
        return json.loads(json.dumps(dict(state), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise PrefreezeGovernanceError("governance state must be canonical JSON") from exc


def _current_governance_digest(state: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    canonical = _canonical_prefreeze_governance(state)
    return canonical, _digest(canonical)


class PrefreezeMechanicalAuthorityV1:
    """Digest-bound, rehearsal-only authority. It never grants execution."""

    def __init__(self, *, governance_state: Mapping[str, Any], optimizer_identity: str,
                 checkpoint_digest: str, authority_digest: str) -> None:
        canonical, governance_digest = _current_governance_digest(governance_state)
        self.governance_state = canonical
        self.governance_digest = governance_digest
        self.optimizer_identity = _nonempty(optimizer_identity, "optimizer identity")
        self.checkpoint_digest = _sha256(checkpoint_digest, "checkpoint digest")
        self.authority_digest = _sha256(authority_digest, "authority digest")
        self.rehearsal_only = True
        self.training_authorized = False
        self.execution_authorized = False
        self._validate_digest()

    @classmethod
    def issue(cls, *, governance_state: Mapping[str, Any], optimizer_identity: str,
              checkpoint_digest: str) -> "PrefreezeMechanicalAuthorityV1":
        canonical, governance_digest = _current_governance_digest(governance_state)
        optimizer_identity = _nonempty(optimizer_identity, "optimizer identity")
        checkpoint_digest = _sha256(checkpoint_digest, "checkpoint digest")
        core = {
            "schema": AUTHORITY_SCHEMA, "governance_digest": governance_digest,
            "optimizer_identity": optimizer_identity, "checkpoint_digest": checkpoint_digest,
            "rehearsal_only": True, "training_authorized": False, "execution_authorized": False,
        }
        return cls(governance_state=canonical, optimizer_identity=optimizer_identity,
                   checkpoint_digest=checkpoint_digest, authority_digest=_digest(core))

    def _core(self) -> dict[str, Any]:
        return {
            "schema": AUTHORITY_SCHEMA, "governance_digest": self.governance_digest,
            "optimizer_identity": self.optimizer_identity, "checkpoint_digest": self.checkpoint_digest,
            "rehearsal_only": True, "training_authorized": False, "execution_authorized": False,
        }

    def _validate_digest(self) -> None:
        if self.rehearsal_only is not True or self.training_authorized or self.execution_authorized:
            raise PrefreezeGovernanceError("prefreeze authority cannot authorize execution")
        _, current = _current_governance_digest(self.governance_state)
        if current != self.governance_digest:
            raise PrefreezeGovernanceError("authority current governance digest mismatch")
        if self.authority_digest != _digest(self._core()):
            raise PrefreezeGovernanceError("authority digest mismatch")

    def start_checkpoint_receipt(self) -> dict[str, Any]:
        self._validate_digest()
        core = {
            "schema": START_RECEIPT_SCHEMA, "authority_digest": self.authority_digest,
            "governance_digest": self.governance_digest, "optimizer_identity": self.optimizer_identity,
            "checkpoint_digest": self.checkpoint_digest, "rehearsal_only": True,
            "training_authorized": False, "execution_authorized": False,
        }
        return {**core, "receipt_digest": _digest(core)}

    @classmethod
    def reload_start_checkpoint(cls, receipt: Mapping[str, Any], observed_checkpoint_digest: str,
                                *, governance_state: Mapping[str, Any]) -> "PrefreezeMechanicalAuthorityV1":
        _exact_fields(receipt, START_RECEIPT_FIELDS, "start checkpoint receipt", governance=False)
        if receipt.get("schema") != START_RECEIPT_SCHEMA:
            raise PrefreezeGovernanceError("start checkpoint receipt schema mismatch")
        canonical, current_governance_digest = _current_governance_digest(governance_state)
        receipt_governance = _sha256(receipt.get("governance_digest"), "governance digest")
        if receipt_governance != current_governance_digest:
            raise PrefreezeGovernanceError("start checkpoint current governance digest mismatch")
        if receipt.get("rehearsal_only") is not True or receipt.get("training_authorized") is not False or receipt.get("execution_authorized") is not False:
            raise PrefreezeGovernanceError("prefreeze receipt cannot authorize execution")
        observed = _sha256(observed_checkpoint_digest, "checkpoint digest")
        expected = _sha256(receipt.get("checkpoint_digest"), "checkpoint digest")
        if observed != expected:
            raise PrefreezeGovernanceError("checkpoint digest mismatch on reload")
        core = {k: receipt[k] for k in START_RECEIPT_FIELDS if k != "receipt_digest"}
        if receipt["receipt_digest"] != _digest(core):
            raise PrefreezeGovernanceError("start checkpoint receipt digest mismatch")
        return cls(governance_state=canonical, optimizer_identity=receipt["optimizer_identity"],
                   checkpoint_digest=expected, authority_digest=receipt["authority_digest"])

    @classmethod
    def verify_completed_checkpoint_receipt(cls, receipt: Mapping[str, Any], observed_checkpoint_digest: str,
                                            *, governance_state: Mapping[str, Any]) -> dict[str, Any]:
        _exact_fields(receipt, COMPLETED_RECEIPT_FIELDS, "completed checkpoint receipt", governance=False)
        if receipt.get("schema") != COMPLETED_RECEIPT_SCHEMA:
            raise PrefreezeGovernanceError("completed checkpoint receipt schema mismatch")
        _, current_governance_digest = _current_governance_digest(governance_state)
        governance_digest = _sha256(receipt.get("governance_digest"), "governance digest")
        if governance_digest != current_governance_digest:
            raise PrefreezeGovernanceError("completed checkpoint current governance digest mismatch")
        if receipt.get("rehearsal_only") is not True or receipt.get("training_authorized") is not False or receipt.get("execution_authorized") is not False:
            raise PrefreezeGovernanceError("prefreeze receipt cannot authorize execution")
        observed = _sha256(observed_checkpoint_digest, "checkpoint digest")
        expected = _sha256(receipt.get("checkpoint_digest"), "checkpoint digest")
        parent = _sha256(receipt.get("parent_checkpoint_digest"), "parent checkpoint digest")
        if observed != expected:
            raise PrefreezeGovernanceError("checkpoint digest mismatch on reload")
        if expected == parent:
            raise PrefreezeGovernanceError("completed checkpoint must be a new state")
        core = {k: receipt[k] for k in COMPLETED_RECEIPT_FIELDS if k != "receipt_digest"}
        core["authority_digest"] = _sha256(core["authority_digest"], "authority digest")
        core["optimizer_identity"] = _nonempty(core["optimizer_identity"], "optimizer identity")
        core["guarded_step_token"] = _nonempty(core["guarded_step_token"], "guarded step token")
        if receipt["receipt_digest"] != _digest(core):
            raise PrefreezeGovernanceError("completed checkpoint receipt digest mismatch")
        expected_authority = _digest({
            "schema": AUTHORITY_SCHEMA, "governance_digest": governance_digest,
            "optimizer_identity": core["optimizer_identity"], "checkpoint_digest": parent,
            "rehearsal_only": True, "training_authorized": False, "execution_authorized": False,
        })
        if core["authority_digest"] != expected_authority:
            raise PrefreezeGovernanceError("parent authority digest mismatch")
        return core


class PrefreezeOptimizerGuardV1:
    """Optimizer-bound, exactly-one-update guard using optimizer pre/post hooks."""

    def __init__(self, authority: PrefreezeMechanicalAuthorityV1, optimizer: Any) -> None:
        if not isinstance(authority, PrefreezeMechanicalAuthorityV1):
            raise PrefreezeGovernanceError("PrefreezeMechanicalAuthorityV1 required")
        authority._validate_digest()
        for name in ("step", "register_step_pre_hook", "register_step_post_hook"):
            if not callable(getattr(optimizer, name, None)):
                raise PrefreezeGovernanceError(f"optimizer must provide {name}()")
        if getattr(optimizer, "_v5_prefreeze_optimizer_guard_v1", None) is not None:
            raise PrefreezeGovernanceError("optimizer already has a prefreeze guard")
        self.authority, self.optimizer = authority, optimizer
        self._counter = 0
        self._steps: dict[str, dict[str, Any]] = {}
        self._armed: str | None = None
        self._consumed: str | None = None
        self._pending_ema: str | None = None
        self._poisoned = False
        self._closed = False
        self._pre_handle = optimizer.register_step_pre_hook(self._pre_step)
        self._post_handle = optimizer.register_step_post_hook(self._post_step)
        setattr(optimizer, "_v5_prefreeze_optimizer_guard_v1", self)

    def _ensure_open(self) -> None:
        if self._closed:
            raise StepCompletionError("optimizer guard is closed")
        if self._poisoned:
            raise StepCompletionError("optimizer guard is poisoned after ambiguous failure")
        self.authority._validate_digest()

    def begin_step(self, optimizer_identity: str, checkpoint_digest: str) -> str:
        self._ensure_open()
        if self._counter != 0:
            raise StepCompletionError("prefreeze guard permits exactly one optimizer update")
        if optimizer_identity != self.authority.optimizer_identity:
            raise PrefreezeGovernanceError("optimizer identity mismatch")
        if _sha256(checkpoint_digest, "checkpoint digest") != self.authority.checkpoint_digest:
            raise PrefreezeGovernanceError("checkpoint digest mismatch")
        token = "prefreeze-step-00000000"
        self._counter = 1
        self._steps[token] = {
            "unscaled": False, "gradients_valid": False, "optimizer_completed": False,
            "ema_completed": False, "rejected": False, "ema_consumed": False,
            "checkpoint_emitted": False,
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
        token = kwargs.pop(STEP_TOKEN_KWARG, None)
        if optimizer is not self.optimizer or self._armed is None or token != self._armed:
            expected = self._armed
            self._armed = None
            raise StepCompletionError(f"optimizer step not armed for supplied token; expected={expected!r} observed={token!r}")
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
            self._poisoned = True
            raise StepCompletionError("optimizer post-step lacks consumed authorization")
        token = self._consumed
        self._step_state(token)["optimizer_completed"] = True
        self._armed = None
        self._pending_ema = token

    def run_optimizer_step(self, token: str) -> Any:
        step = self._step_state(token)
        if step["rejected"] or not step["unscaled"] or not step["gradients_valid"]:
            raise StepCompletionError("optimizer step requires unscaled validated gradients")
        try:
            result = self.optimizer.step(**{STEP_TOKEN_KWARG: token})
        except Exception:
            step["rejected"] = True
            self._armed = self._consumed = None
            self._poisoned = True
            raise
        if self._consumed != token or not step["optimizer_completed"]:
            step["rejected"] = True
            self._armed = self._consumed = None
            self._poisoned = True
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
        if self._pending_ema != token:
            raise StepCompletionError("EMA token does not match pending optimizer step")
        if not callable(ema_callable):
            raise StepCompletionError("EMA callback is required")
        step["ema_consumed"] = True
        try:
            result = ema_callable()
        except Exception:
            step["rejected"] = True
            self._poisoned = True
            raise
        step["ema_completed"] = True
        self._pending_ema = None
        return result

    def completed_checkpoint_receipt(self, token: str, checkpoint_digest: str) -> dict[str, Any]:
        step = self._step_state(token)
        if step["checkpoint_emitted"]:
            raise StepCompletionError("completed checkpoint receipt already emitted")
        if step["rejected"] or not step["ema_completed"]:
            raise StepCompletionError("completed checkpoint requires successful EMA")
        self.assert_step_complete(token)
        checkpoint_digest = _sha256(checkpoint_digest, "checkpoint digest")
        if checkpoint_digest == self.authority.checkpoint_digest:
            raise PrefreezeGovernanceError("completed checkpoint must be a new state")
        core = {
            "schema": COMPLETED_RECEIPT_SCHEMA, "authority_digest": self.authority.authority_digest,
            "governance_digest": self.authority.governance_digest,
            "optimizer_identity": self.authority.optimizer_identity,
            "parent_checkpoint_digest": self.authority.checkpoint_digest,
            "checkpoint_digest": checkpoint_digest, "guarded_step_token": token,
            "rehearsal_only": True, "training_authorized": False, "execution_authorized": False,
        }
        step["checkpoint_emitted"] = True
        return {**core, "receipt_digest": _digest(core)}

    def close(self) -> None:
        if not self._closed:
            self._pre_handle.remove()
            self._post_handle.remove()
            if getattr(self.optimizer, "_v5_prefreeze_optimizer_guard_v1", None) is self:
                delattr(self.optimizer, "_v5_prefreeze_optimizer_guard_v1")
            self._armed = self._consumed = self._pending_ema = None
            self._closed = True
