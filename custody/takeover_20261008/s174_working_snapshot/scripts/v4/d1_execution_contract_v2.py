#!/usr/bin/env python3
"""D1 V2 execution-binding resolver.

This module is deliberately additive to the preserved 566079a D1 candidate.
It fixes three authority problems without choosing any future teacher readout:

1. the canonical readout is an immutable external contract, not a dynamic
   resolver-report hash;
2. a healthy checkpoint is valid only under the exact canonical readout
   contract hash;
3. the D1 implementation can become executable when future frozen authorities
   appear, without editing this source after outcomes exist.

No contract/qualification files are created here and absence is never
permission.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

REPO = Path(__file__).resolve().parents[2]
_EXPLICIT = os.environ.get("D1_AUTHORITY_ROOT")
AUTHORITY_ROOTS: tuple[Path, ...] = (
    (Path(_EXPLICIT),)
    if _EXPLICIT
    else (Path("/mnt/d/Jepa project"), Path("D:/Jepa project"), REPO)
)

READOUT_CONTRACT_REL = "docs/agent/D1_CANONICAL_TEACHER_READOUT_CONTRACT_V2.json"
QUALIFICATION_AUTHORITY_REL = "docs/agent/D1_TEACHER_QUALIFICATION_AUTHORITY_V2.json"

STOP_READOUT_CONTRACT_ABSENT = "STOP_D1_V2_CANONICAL_READOUT_CONTRACT_ABSENT"
STOP_READOUT_CONTRACT_INVALID = "STOP_D1_V2_CANONICAL_READOUT_CONTRACT_INVALID"
STOP_READOUT_SOURCE_DRIFT = "STOP_D1_V2_CANONICAL_READOUT_SOURCE_DRIFT"
STOP_QUALIFICATION_ABSENT = "STOP_D1_V2_TEACHER_QUALIFICATION_AUTHORITY_ABSENT"
STOP_QUALIFICATION_INVALID = "STOP_D1_V2_TEACHER_QUALIFICATION_INVALID"
STOP_CHECKPOINT_DRIFT = "STOP_D1_V2_QUALIFIED_CHECKPOINT_DRIFT"
STOP_ADAPTER_INVALID = "STOP_D1_V2_READOUT_ADAPTER_INVALID"
WAIT_HEALTHY_TEACHER = "WAIT_HEALTHY_TRAINED_TEACHER"


@dataclass(frozen=True)
class D1ExecutionBinding:
    readout_contract_path: str
    readout_contract_sha256: str
    readout_contract: Mapping[str, Any]
    qualification_authority_path: str
    qualification_authority_sha256: str
    qualification_authority: Mapping[str, Any]
    checkpoint_path: str
    checkpoint_sha256: str
    adapter_path: str
    adapter_sha256: str
    adapter_function: str
    output_dimension: int
    output_dtype: str
    teacher_role: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "readout_contract_path": self.readout_contract_path,
            "readout_contract_sha256": self.readout_contract_sha256,
            "qualification_authority_path": self.qualification_authority_path,
            "qualification_authority_sha256": self.qualification_authority_sha256,
            "checkpoint_path": self.checkpoint_path,
            "checkpoint_sha256": self.checkpoint_sha256,
            "adapter_path": self.adapter_path,
            "adapter_sha256": self.adapter_sha256,
            "adapter_function": self.adapter_function,
            "output_dimension": self.output_dimension,
            "output_dtype": self.output_dtype,
            "teacher_role": self.teacher_role,
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(c in "0123456789abcdef" for c in text)


def _resolve(relative: str) -> Path | None:
    rel = Path(str(relative))
    if rel.is_absolute():
        return rel if rel.is_file() else None
    for root in AUTHORITY_ROOTS:
        candidate = root / rel
        if candidate.is_file():
            return candidate
    return None


def _load_json(relative: str, absent_terminal: str) -> tuple[Path, dict[str, Any], str]:
    path = _resolve(relative)
    if path is None:
        raise PermissionError(f"{absent_terminal}: {relative}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        raise PermissionError(f"{STOP_READOUT_CONTRACT_INVALID}: {relative}: {error}") from error
    if not isinstance(payload, dict):
        raise PermissionError(f"{STOP_READOUT_CONTRACT_INVALID}: root is not an object")
    return path, payload, _sha256(path)


def validate_readout_contract(payload: Mapping[str, Any], *, file_sha256: str) -> dict[str, Any]:
    if payload.get("schema") != "D1_CANONICAL_TEACHER_READOUT_CONTRACT_V2":
        raise PermissionError(f"{STOP_READOUT_CONTRACT_INVALID}: schema")
    if not str(payload.get("status") or "").startswith("FROZEN_"):
        raise PermissionError(f"{STOP_READOUT_CONTRACT_INVALID}: status must be frozen")
    if not _is_sha256(file_sha256):
        raise PermissionError(f"{STOP_READOUT_CONTRACT_INVALID}: contract file hash")
    required_text = (
        "readout_id", "teacher_role", "model_source_path", "model_source_sha256",
        "adapter_path", "adapter_source_sha256", "adapter_function",
        "checkpoint_schema", "cell_identity_field", "output_dtype",
    )
    for key in required_text:
        if not str(payload.get(key) or ""):
            raise PermissionError(f"{STOP_READOUT_CONTRACT_INVALID}: missing {key}")
    if payload["teacher_role"] != "EMA_TARGET":
        raise PermissionError(
            f"{STOP_READOUT_CONTRACT_INVALID}: teacher_role must be EMA_TARGET")
    if payload["output_dtype"] not in ("float32", "float64"):
        raise PermissionError(
            f"{STOP_READOUT_CONTRACT_INVALID}: output_dtype must be float32/float64")
    dimension = int(payload.get("output_dimension") or 0)
    if dimension <= 0:
        raise PermissionError(f"{STOP_READOUT_CONTRACT_INVALID}: output_dimension")
    if not _is_sha256(payload["model_source_sha256"]):
        raise PermissionError(f"{STOP_READOUT_CONTRACT_INVALID}: model_source_sha256")
    if not _is_sha256(payload["adapter_source_sha256"]):
        raise PermissionError(f"{STOP_READOUT_CONTRACT_INVALID}: adapter_source_sha256")
    if payload.get("readout_operation") is None:
        raise PermissionError(f"{STOP_READOUT_CONTRACT_INVALID}: readout_operation")
    if payload.get("autocast_enabled") not in (True, False):
        raise PermissionError(f"{STOP_READOUT_CONTRACT_INVALID}: autocast_enabled")
    return {
        "readout_contract_sha256": file_sha256,
        "readout_id": str(payload["readout_id"]),
        "output_dimension": dimension,
        "output_dtype": str(payload["output_dtype"]),
        "teacher_role": str(payload["teacher_role"]),
    }


def _verify_source(relative: str, expected: str, label: str) -> Path:
    path = _resolve(relative)
    if path is None:
        raise PermissionError(f"{STOP_READOUT_SOURCE_DRIFT}: {label} absent: {relative}")
    actual = _sha256(path)
    if actual != expected:
        raise PermissionError(
            f"{STOP_READOUT_SOURCE_DRIFT}: {label} {relative} is {actual}, expected {expected}")
    return path


def validate_qualification_authority(
    payload: Mapping[str, Any], *, authority_sha256: str,
    readout_contract_sha256: str, readout_contract: Mapping[str, Any],
) -> dict[str, Any]:
    if payload.get("schema") != "D1_TEACHER_QUALIFICATION_AUTHORITY_V2":
        raise PermissionError(f"{STOP_QUALIFICATION_INVALID}: schema")
    if not str(payload.get("status") or "").startswith("FROZEN_"):
        raise PermissionError(f"{STOP_QUALIFICATION_INVALID}: status must be frozen")
    if not _is_sha256(authority_sha256):
        raise PermissionError(f"{STOP_QUALIFICATION_INVALID}: authority file hash")
    selected = str(payload.get("selected_checkpoint_sha256") or "")
    if not _is_sha256(selected):
        raise PermissionError(f"{STOP_QUALIFICATION_INVALID}: selected checkpoint")
    entries = payload.get("qualified_teachers")
    if not isinstance(entries, list) or not entries:
        raise PermissionError(f"{STOP_QUALIFICATION_INVALID}: qualified_teachers")
    matches = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        digest = str(entry.get("checkpoint_sha256") or "")
        if digest != selected:
            continue
        if str(entry.get("readout_contract_sha256") or "") != readout_contract_sha256:
            raise PermissionError(
                f"{STOP_QUALIFICATION_INVALID}: selected checkpoint is qualified under "
                "a different readout contract")
        if not str(entry.get("review_terminal") or "").startswith("PASS"):
            raise PermissionError(
                f"{STOP_QUALIFICATION_INVALID}: selected checkpoint review did not PASS")
        if str(entry.get("checkpoint_schema") or "") != str(
            readout_contract.get("checkpoint_schema") or ""
        ):
            raise PermissionError(
                f"{STOP_QUALIFICATION_INVALID}: checkpoint schema/readout contract mismatch")
        for key in ("successor_commit", "source_manifest_root"):
            if not _is_sha256(entry.get(key)):
                raise PermissionError(f"{STOP_QUALIFICATION_INVALID}: {key}")
        checkpoint_path = str(entry.get("checkpoint_path") or "")
        if not checkpoint_path:
            raise PermissionError(f"{STOP_QUALIFICATION_INVALID}: checkpoint_path")
        matches.append(entry)
    if len(matches) != 1:
        raise PermissionError(
            f"{STOP_QUALIFICATION_INVALID}: selected checkpoint has {len(matches)} exact entries")
    return {"selected": matches[0], "selected_checkpoint_sha256": selected}


def resolve_execution_binding() -> dict[str, Any]:
    """Resolve the future D1 execution binding, or fail closed without source edits."""
    try:
        contract_path, contract, contract_sha = _load_json(
            READOUT_CONTRACT_REL, STOP_READOUT_CONTRACT_ABSENT)
        validate_readout_contract(contract, file_sha256=contract_sha)
        model_source = _verify_source(
            str(contract["model_source_path"]), str(contract["model_source_sha256"]),
            "model source")
        adapter_source = _verify_source(
            str(contract["adapter_path"]), str(contract["adapter_source_sha256"]),
            "readout adapter")
    except PermissionError as error:
        return {
            "gate_open": False,
            "terminal": WAIT_HEALTHY_TEACHER,
            "reason": str(error),
            "canonical_readout_present": False,
        }

    try:
        qual_path, qualification, qual_sha = _load_json(
            QUALIFICATION_AUTHORITY_REL, STOP_QUALIFICATION_ABSENT)
        qualified = validate_qualification_authority(
            qualification, authority_sha256=qual_sha,
            readout_contract_sha256=contract_sha, readout_contract=contract)
        entry = qualified["selected"]
        checkpoint_path = _resolve(str(entry["checkpoint_path"]))
        if checkpoint_path is None:
            raise PermissionError(
                f"{STOP_CHECKPOINT_DRIFT}: selected checkpoint absent: {entry['checkpoint_path']}")
        actual_checkpoint = _sha256(checkpoint_path)
        if actual_checkpoint != str(entry["checkpoint_sha256"]):
            raise PermissionError(
                f"{STOP_CHECKPOINT_DRIFT}: selected checkpoint is {actual_checkpoint}, "
                f"expected {entry['checkpoint_sha256']}")
    except PermissionError as error:
        return {
            "gate_open": False,
            "terminal": WAIT_HEALTHY_TEACHER,
            "reason": str(error),
            "canonical_readout_present": True,
            "readout_contract_sha256": contract_sha,
        }

    binding = D1ExecutionBinding(
        readout_contract_path=str(contract_path),
        readout_contract_sha256=contract_sha,
        readout_contract=contract,
        qualification_authority_path=str(qual_path),
        qualification_authority_sha256=qual_sha,
        qualification_authority=qualification,
        checkpoint_path=str(checkpoint_path),
        checkpoint_sha256=str(entry["checkpoint_sha256"]),
        adapter_path=str(adapter_source),
        adapter_sha256=str(contract["adapter_source_sha256"]),
        adapter_function=str(contract["adapter_function"]),
        output_dimension=int(contract["output_dimension"]),
        output_dtype=str(contract["output_dtype"]),
        teacher_role=str(contract["teacher_role"]),
    )
    return {
        "gate_open": True,
        "terminal": "PASS_D1_V2_EXECUTION_BINDING",
        "binding": binding,
        "binding_summary": binding.as_dict(),
        "model_source_verified_path": str(model_source),
    }


def load_readout_adapter(binding: D1ExecutionBinding) -> Callable[..., Any]:
    """Load only the exact source-bound adapter named by the canonical contract."""
    path = Path(binding.adapter_path)
    if not path.is_file() or _sha256(path) != binding.adapter_sha256:
        raise PermissionError(f"{STOP_ADAPTER_INVALID}: adapter source drift")
    spec = importlib.util.spec_from_file_location("d1_v2_frozen_readout_adapter", path)
    if spec is None or spec.loader is None:
        raise PermissionError(f"{STOP_ADAPTER_INVALID}: cannot import adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    function = getattr(module, binding.adapter_function, None)
    if not callable(function):
        raise PermissionError(
            f"{STOP_ADAPTER_INVALID}: {binding.adapter_function} is not callable")
    return function


def build_state_batch_iterator(binding: D1ExecutionBinding, **kwargs: Any) -> Any:
    """Instantiate the frozen adapter.

    The adapter interface is prospectively fixed to return an iterable yielding
    dictionaries with exactly:
      canonical_cell_id: 1-D string-like sequence
      states:            (n, output_dimension) numeric array

    Population/row-count validation belongs to the archive writer, not the
    adapter, so a buggy adapter cannot self-certify completeness.
    """
    factory = load_readout_adapter(binding)
    iterator = factory(
        checkpoint_path=binding.checkpoint_path,
        readout_contract=dict(binding.readout_contract),
        **kwargs,
    )
    if iterator is None or not hasattr(iterator, "__iter__"):
        raise PermissionError(f"{STOP_ADAPTER_INVALID}: adapter returned no iterable")
    return iterator
