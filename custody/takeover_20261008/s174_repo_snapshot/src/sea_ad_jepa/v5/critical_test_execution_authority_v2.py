from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence


def _sha(v: object, name: str) -> str:
    if not isinstance(v, str) or len(v) != 64 or v != v.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(v, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return v


def _id(v: object, name: str) -> str:
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{name} must be nonempty")
    return v.strip()


def _digest(p: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(p, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    ).hexdigest()


@dataclass(frozen=True)
class CriticalTestExecutionReceiptV1:
    test_id: str
    provider_id: str
    provider_run_id: str
    provider_run_locator: str
    test_source_sha256: str
    command_sha256: str
    stdout_sha256: str
    stderr_sha256: str
    artifact_manifest_sha256: str
    provider_attestation_sha256: str
    exit_code: int
    passed: bool

    def _payload(self) -> dict[str, Any]:
        if isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int) or self.exit_code != 0:
            raise ValueError("critical test receipt must have exit_code == 0")
        if self.passed is not True:
            raise ValueError("critical test receipt must be passed=True")
        return {
            "schema": "V5_CRITICAL_TEST_EXECUTION_RECEIPT_V1",
            "test_id": _id(self.test_id, "test_id"),
            "provider_id": _id(self.provider_id, "provider_id"),
            "provider_run_id": _id(self.provider_run_id, "provider_run_id"),
            "provider_run_locator": _id(self.provider_run_locator, "provider_run_locator"),
            "test_source_sha256": _sha(self.test_source_sha256, "test_source_sha256"),
            "command_sha256": _sha(self.command_sha256, "command_sha256"),
            "stdout_sha256": _sha(self.stdout_sha256, "stdout_sha256"),
            "stderr_sha256": _sha(self.stderr_sha256, "stderr_sha256"),
            "artifact_manifest_sha256": _sha(self.artifact_manifest_sha256, "artifact_manifest_sha256"),
            "provider_attestation_sha256": _sha(self.provider_attestation_sha256, "provider_attestation_sha256"),
            "exit_code": 0,
            "passed": True,
        }

    def validate(self) -> None:
        self._payload()

    def canonical_digest(self) -> str:
        return _digest(self._payload())


@dataclass(frozen=True)
class CriticalTestExecutionAuthorityV2:
    authority_id: str
    required_test_ids: Sequence[str]
    test_suite_source_sha256: str
    receipt_by_test: Mapping[str, CriticalTestExecutionReceiptV1]
    training_authorized: bool = False

    def _payload(self) -> dict[str, Any]:
        if self.training_authorized is not False:
            raise ValueError("critical-test authority cannot authorize training")
        if (
            not isinstance(self.required_test_ids, Sequence)
            or isinstance(self.required_test_ids, (str, bytes))
            or not self.required_test_ids
        ):
            raise ValueError("required_test_ids must be a nonempty sequence")
        required = tuple(sorted(_id(x, "required_test_id") for x in self.required_test_ids))
        if len(set(required)) != len(required):
            raise ValueError("required_test_ids must be unique")
        if not isinstance(self.receipt_by_test, Mapping) or set(self.receipt_by_test) != set(required):
            raise ValueError("receipt_by_test must exactly match required_test_ids")
        suite = _sha(self.test_suite_source_sha256, "test_suite_source_sha256")
        receipts: dict[str, str] = {}
        for test_id in required:
            receipt = self.receipt_by_test[test_id]
            if not isinstance(receipt, CriticalTestExecutionReceiptV1):
                raise ValueError(f"receipt for {test_id} must use CriticalTestExecutionReceiptV1")
            receipt.validate()
            if receipt.test_id != test_id:
                raise ValueError(f"receipt test_id mismatch for {test_id}")
            if receipt.test_source_sha256 != suite:
                raise ValueError(f"receipt test-source root mismatch for {test_id}")
            receipts[test_id] = receipt.canonical_digest()
        return {
            "schema": "V5_CRITICAL_TEST_EXECUTION_AUTHORITY_V2",
            "authority_id": _id(self.authority_id, "authority_id"),
            "required_test_ids": list(required),
            "test_suite_source_sha256": suite,
            "execution_receipt_sha256_by_test": receipts,
            "training_authorized": False,
        }

    def validate(self) -> None:
        self._payload()

    def canonical_digest(self) -> str:
        return _digest(self._payload())
