"""Current-V5 preexecution authority bound to the explicit V2 root graph."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from .current_authority_roots_v2 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _closure_digest(closure: Mapping[str, Any]) -> str:
    if not isinstance(closure, Mapping):
        raise ValueError("closure_v2 must be a mapping")
    if closure.get("schema") != "V5_CURRENT_AUTHORITY_CLOSURE_V2":
        raise ValueError("closure_v2 schema mismatch")
    if closure.get("training_authorized") is not False:
        raise ValueError("closure_v2 cannot authorize training")
    roots = closure.get("authority_roots")
    if not isinstance(roots, Mapping) or tuple(roots) != CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2:
        raise ValueError("closure_v2 roots must exactly match current V2 upstream roots")
    normalized = {name: _sha(roots[name], name) for name in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2}
    core = {"schema": "V5_CURRENT_AUTHORITY_CLOSURE_V2", "authority_roots": normalized, "training_authorized": False}
    observed = _sha(closure.get("closure_digest"), "closure_digest")
    expected = _digest(core)
    if observed != expected:
        raise ValueError("closure_v2 digest mismatch")
    return observed


@dataclass(frozen=True)
class CurrentTrainerPreexecutionAuthorityV2:
    authority_roots: Mapping[str, str]
    closure_v2_sha256: str
    protected_registry_authority_sha256: str
    critical_test_authority_sha256: str
    relational_training_active: bool
    optimizer_started: bool
    training_authorized: bool = False

    def normalized_roots(self) -> dict[str, str]:
        if not isinstance(self.authority_roots, Mapping) or tuple(self.authority_roots) != CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2:
            raise ValueError("authority_roots must exactly match current V2 upstream roots")
        return {name: _sha(self.authority_roots[name], name) for name in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2}

    def validate(self) -> None:
        roots = self.normalized_roots()
        _sha(self.closure_v2_sha256, "closure_v2_sha256")
        protected = _sha(self.protected_registry_authority_sha256, "protected_registry_authority_sha256")
        critical = _sha(self.critical_test_authority_sha256, "critical_test_authority_sha256")
        if protected != roots["protected_registry_authority_sha256"]:
            raise ValueError("protected registry root mismatch")
        if critical != roots["critical_test_authority_sha256"]:
            raise ValueError("critical test root mismatch")
        if self.relational_training_active is not False:
            raise ValueError("relational training must remain inactive before final training authority")
        if self.optimizer_started is not False:
            raise ValueError("optimizer must not be started before preexecution closure")
        if self.training_authorized is not False:
            raise ValueError("preexecution authority cannot authorize training")

    def bind_closure_v2(self, closure_v2: Mapping[str, Any]) -> str:
        self.validate()
        digest = _closure_digest(closure_v2)
        if digest != self.closure_v2_sha256:
            raise ValueError("closure_v2 digest does not match preexecution authority")
        if dict(closure_v2["authority_roots"]) != self.normalized_roots():
            raise ValueError("closure_v2 roots do not match preexecution authority roots")
        return digest

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_CURRENT_TRAINER_PREEXECUTION_AUTHORITY_V2",
                "authority_roots": self.normalized_roots(),
                "closure_v2_sha256": self.closure_v2_sha256,
                "protected_registry_authority_sha256": self.protected_registry_authority_sha256,
                "critical_test_authority_sha256": self.critical_test_authority_sha256,
                "relational_training_active": False,
                "optimizer_started": False,
                "training_authorized": False,
            }
        )
