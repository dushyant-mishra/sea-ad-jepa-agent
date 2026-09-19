"""Explicit final current-V5 training authority.

This is the only current V5 schema allowed to carry training_authorized=True.
It may be issued only after exact closure V2, preexecution V2, receipt V2,
critical-test execution and runtime-source roots agree.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from .current_authority_roots_v2 import CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V2, CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2
from .current_teacher_target_receipt_v2 import validate_current_teacher_target_receipt_v2
from .current_trainer_preexecution_contract_v2 import CurrentTrainerPreexecutionAuthorityV2

ISSUANCE_POLICY_ID = "CURRENT_V5_ALL_GATES_PASS_BEFORE_TRAINING_V1"
CURRENT_CHAIN_STATUS_ID = (
    "STALE_RELATIVE_TO_CURRENT_MASKING_V3_V4_AND_OPEN_F13_F14_F15_V1"
)
STOP_STALE_TRAINING_CHAIN = "STOP_V5_CURRENT_TRAINING_AUTHORITY_V1_STALE_CHAIN"


def assert_current_training_authority_v1_issuance_open() -> None:
    """Fail closed while the V1/V2 final closure graph is stale.

    Current masking qualification uses newer V3/V4 authorities and F13/F14/F15
    remain open.  Historical V1 training-authority objects remain readable for
    provenance, but they cannot issue or arm a new optimizer step.
    """

    raise RuntimeError(
        f"{STOP_STALE_TRAINING_CHAIN}: {CURRENT_CHAIN_STATUS_ID}"
    )


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _live_digest(obj: Any, name: str) -> str:
    if getattr(obj, "training_authorized", False) is not False:
        raise ValueError(f"{name} unexpectedly authorizes training")
    obj.validate()
    return _sha(obj.canonical_digest(), f"{name} canonical digest")


@dataclass(frozen=True)
class CurrentTrainingAuthorityV1:
    authority_id: str
    closure_v2_sha256: str
    preexecution_authority_sha256: str
    receipt_v2_sha256: str
    target_package_root: str
    critical_test_authority_sha256: str
    runtime_source_authority_sha256: str
    issuance_policy_id: str
    issuance_proof_sha256: str
    training_authorized: bool = True

    def _proof_payload(self) -> dict[str, Any]:
        return {
            "schema": "V5_CURRENT_TRAINING_AUTHORITY_V1",
            "authority_id": self.authority_id,
            "closure_v2_sha256": _sha(self.closure_v2_sha256, "closure_v2_sha256"),
            "preexecution_authority_sha256": _sha(self.preexecution_authority_sha256, "preexecution_authority_sha256"),
            "receipt_v2_sha256": _sha(self.receipt_v2_sha256, "receipt_v2_sha256"),
            "target_package_root": _sha(self.target_package_root, "target_package_root"),
            "critical_test_authority_sha256": _sha(self.critical_test_authority_sha256, "critical_test_authority_sha256"),
            "runtime_source_authority_sha256": _sha(self.runtime_source_authority_sha256, "runtime_source_authority_sha256"),
            "issuance_policy_id": self.issuance_policy_id,
            "training_authorized": True,
        }

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        if self.issuance_policy_id != ISSUANCE_POLICY_ID:
            raise ValueError("issuance_policy_id mismatch")
        if self.training_authorized is not True:
            raise ValueError("final training authority must explicitly authorize training")
        proof = _sha(self.issuance_proof_sha256, "issuance_proof_sha256")
        if proof != _digest(self._proof_payload()):
            raise ValueError("issuance proof mismatch")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({**self._proof_payload(), "issuance_proof_sha256": self.issuance_proof_sha256})


def issue_training_authority_v1(*, closure_v2: Mapping[str, Any], preexecution: CurrentTrainerPreexecutionAuthorityV2, receipt_v2: Mapping[str, Any], expected_target_package_root: str, critical_test: Any, runtime_source: Any) -> CurrentTrainingAuthorityV1:
    assert_current_training_authority_v1_issuance_open()
    if not isinstance(closure_v2, Mapping) or closure_v2.get("schema") != "V5_CURRENT_AUTHORITY_CLOSURE_V2":
        raise ValueError("closure_v2 schema mismatch")
    if closure_v2.get("training_authorized") is not False:
        raise ValueError("closure_v2 must not itself authorize training")
    roots = closure_v2.get("authority_roots")
    if not isinstance(roots, Mapping) or tuple(roots) != CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2:
        raise ValueError("closure_v2 roots mismatch")
    closure_digest = _sha(closure_v2.get("closure_digest"), "closure_digest")
    preexecution.bind_closure_v2(closure_v2)
    pre_digest = preexecution.canonical_digest()
    receipt_roots = dict(roots)
    receipt_roots["preexecution_authority_sha256"] = pre_digest
    if tuple(receipt_roots) != CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V2:
        raise RuntimeError("internal receipt root order mismatch")
    verified_receipt = validate_current_teacher_target_receipt_v2(
        receipt_v2,
        expected_target_package_root=expected_target_package_root,
        expected_authority_roots=receipt_roots,
        expected_closure_v2_sha256=closure_digest,
    )
    critical = _live_digest(critical_test, "critical test")
    runtime = _live_digest(runtime_source, "runtime source")
    if critical != roots["critical_test_authority_sha256"]:
        raise ValueError("critical-test authority root mismatch")
    if runtime != roots["runtime_source_authority_sha256"]:
        raise ValueError("runtime-source authority root mismatch")
    core = {
        "schema": "V5_CURRENT_TRAINING_AUTHORITY_V1",
        "authority_id": "V5_CURRENT_TRAINING_AUTHORITY_V1",
        "closure_v2_sha256": closure_digest,
        "preexecution_authority_sha256": pre_digest,
        "receipt_v2_sha256": verified_receipt["receipt_digest"],
        "target_package_root": verified_receipt["target_package_root"],
        "critical_test_authority_sha256": critical,
        "runtime_source_authority_sha256": runtime,
        "issuance_policy_id": ISSUANCE_POLICY_ID,
        "training_authorized": True,
    }
    authority = CurrentTrainingAuthorityV1(
        authority_id=core["authority_id"],
        closure_v2_sha256=closure_digest,
        preexecution_authority_sha256=pre_digest,
        receipt_v2_sha256=verified_receipt["receipt_digest"],
        target_package_root=verified_receipt["target_package_root"],
        critical_test_authority_sha256=critical,
        runtime_source_authority_sha256=runtime,
        issuance_policy_id=ISSUANCE_POLICY_ID,
        issuance_proof_sha256=_digest(core),
        training_authorized=True,
    )
    authority.validate()
    return authority
