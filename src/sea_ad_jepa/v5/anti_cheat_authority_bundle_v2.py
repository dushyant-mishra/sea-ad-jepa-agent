"""Current-V5 anti-cheat authority successor.

V1 bound static guard authorities but did not require executed evidence that the
masking qualification or remaining-RNA necessity actually passed. V2 keeps V1
untouched for provenance and adds hash-bound, live, EXECUTED_PASS evidence for
both scientific anti-shortcut gates. It cannot authorize training.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping


def _id(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value.strip()


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
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    ).hexdigest()


def _live_digest(obj: Any, name: str) -> str:
    if getattr(obj, "training_authorized", False) is not False:
        raise ValueError(f"{name} unexpectedly authorizes training")
    obj.validate()
    return _sha(obj.canonical_digest(), f"{name} canonical digest")


@dataclass(frozen=True)
class AntiCheatAuthorityBundleV2:
    authority_id: str
    target_identity_gate_authority_sha256: str
    masking_authority_sha256: str
    masking_qualification_execution_authority_sha256: str
    remaining_rna_execution_authority_sha256: str
    measurement_robustness_authority_sha256: str
    observation_gradient_firewall_authority_sha256: str
    critical_test_authority_sha256: str
    training_authorized: bool = False

    def validate(self) -> None:
        _id(self.authority_id, "authority_id")
        fields = (
            "target_identity_gate_authority_sha256",
            "masking_authority_sha256",
            "masking_qualification_execution_authority_sha256",
            "remaining_rna_execution_authority_sha256",
            "measurement_robustness_authority_sha256",
            "observation_gradient_firewall_authority_sha256",
            "critical_test_authority_sha256",
        )
        roots = [_sha(getattr(self, name), name) for name in fields]
        if len(set(roots)) != len(roots):
            raise ValueError("anti-cheat authority role roots must be distinct")
        if self.training_authorized is not False:
            raise ValueError("anti-cheat bundle cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_ANTI_CHEAT_AUTHORITY_BUNDLE_V2",
                **asdict(self),
                "training_authorized": False,
            }
        )

    def bind_execution_evidence(
        self,
        *,
        masking_qualification_execution: Any,
        remaining_rna_execution: Any,
    ) -> None:
        self.validate()
        observed_masking = _live_digest(masking_qualification_execution, "masking qualification execution")
        if observed_masking != self.masking_qualification_execution_authority_sha256:
            raise ValueError("masking qualification execution authority root mismatch")
        if getattr(masking_qualification_execution, "passed", False) is not True:
            raise ValueError("masking qualification execution must be EXECUTED_PASS")

        observed_rna = _live_digest(remaining_rna_execution, "remaining-RNA execution")
        if observed_rna != self.remaining_rna_execution_authority_sha256:
            raise ValueError("remaining-RNA execution authority root mismatch")
        if getattr(remaining_rna_execution, "passed", False) is not True:
            raise ValueError("remaining-RNA execution must be EXECUTED_PASS")
