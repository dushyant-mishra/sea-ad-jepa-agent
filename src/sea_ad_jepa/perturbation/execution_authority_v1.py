"""Execution-mode authority and input authentication for perturbation ETL.

This is the gate the physical entry points call. It is code, not configuration:
a mode is a value that must be passed, every physical input must be authenticated
against an expected digest, and there is no fallback path anywhere in the module.

Three modes, no automatic transition between them
-------------------------------------------------
``SYNTHETIC_TEST``
    Disposable fixtures and engineering tests. May never emit a qualification
    receipt and may never read a path registered as physical authority.
``PHYSICAL_QUALIFICATION``
    Authenticated real data, for explicitly permitted qualification tasks. Emits
    qualification receipts. May not emit production authority.
``PRODUCTION``
    Requires a separately reviewed execution authorization that this module does
    not issue and cannot synthesize.

Design rules that the adversarial suite exercises
-------------------------------------------------
* a missing or unreadable physical input raises; it is never replaced by a
  synthetic fixture, a historical smaller-run artifact, a zero array or a default;
* an input is authenticated by the digest of its **bytes**, so two files with
  identical decoded arrays but different containers are different inputs;
* identity vectors (donor, source, fold, feature order, target order) are
  authenticated by an **order-sensitive** digest, so a permutation that preserves
  counts is rejected;
* a resumable checkpoint carries a context digest; a checkpoint rehashed under a
  different context is rejected even though its own hash is internally valid;
* an unmeasured feature is represented by a mask, never by a zero;
* a parameter with no authenticated source stays ``UNRESOLVED``. It is never
  borrowed from a previous experiment.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np


class ExecutionMode(Enum):
    SYNTHETIC_TEST = "SYNTHETIC_TEST"
    PHYSICAL_QUALIFICATION = "PHYSICAL_QUALIFICATION"
    PRODUCTION = "PRODUCTION"


class ExecutionAuthorityError(RuntimeError):
    """Raised whenever a gate fails. Never caught inside this module."""


UNRESOLVED = "UNRESOLVED"

#: Artifacts that must never be read as current production input. Quarantined or
#: superseded lineage is listed by digest, so renaming the file does not help.
QUARANTINED_DIGESTS = {
    "f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae":
        "FULL104 original sufficient-statistics artifact: transposed source encoding",
}

#: Historical smaller-run fixtures that must never satisfy a physical role.
FORBIDDEN_HISTORICAL_DONOR_COUNTS = (6, 42, 48)

# Reviewed fixed source roots from the physically authenticated September-23
# GSE301119 source manifest. Callers cannot change these by passing a different
# 'expected_sha256' for the same role. Other studies must add a separately
# reviewed/versioned authority rather than self-attest new physical roots.
REVIEWED_SOURCE_ROOTS = {
    "GSE301119_CRISPRa_SOURCE": (
        "2f700baff2390e257a7ae1b301204bceb5feeb823671c21f10fd3f1038450829",
        345798341,
    ),
    "GSE301119_CRISPRi_SOURCE": (
        "fc2584fad6327defb32b939c94e89fa174d3287399ab66e91b6189569b108eb3",
        406836813,
    ),
}
# Fixed physical tasks; adding new studies requires explicit source review.
# The raw-pseudobulk extraction and parity checker digests come from the
# independently reviewed PR81 GSE301119 physical evidence manifest.
REVIEWED_QUALIFICATION_TASKS = {
    "GSE301119_RAW_PSEUDOBULK_QUALIFICATION": {
        "roles": frozenset(REVIEWED_SOURCE_ROOTS),
        "code_sha256": "260c7a3609f3fe987bb3c90755cc9369fd25c8d14941d996d6bcdee52c634fdb",
    },
    "GSE301119_COUNT_READER_PARITY": {
        "roles": frozenset(REVIEWED_SOURCE_ROOTS),
        "code_sha256": "7c2f9fd98e8cc40aaef1c9ca982a4a591b449e3fe6a820f1e1d5c7adaaffca4d",
    },
}
RESERVED_RECEIPT_FIELDS = frozenset({
    "schema", "mode", "task", "context_digest", "code_sha256",
    "inputs", "identity_digests", "parameters", "receipt_sha256",
    "authorization_receipt_sha256",
})


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def order_digest(values: Iterable[Any]) -> str:
    """Order-sensitive digest of an identity vector.

    Deliberately not a multiset digest: a permutation that preserves counts must
    produce a different value, because that is exactly the substitution the
    aggregate-count checks cannot see.
    """
    payload = json.dumps([str(v) for v in values], ensure_ascii=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b"ORDERED|" + payload).hexdigest()


def canonical_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False)
                          .encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuthenticatedInput:
    role: str
    path: str
    sha256: str
    bytes_: int


@dataclass
class ExecutionContext:
    """Immutable execution identity. Every output must carry its digest."""

    mode: ExecutionMode
    task: str
    code_sha256: str
    code_path: str | None = None
    inputs: list[AuthenticatedInput] = field(default_factory=list)
    identity_digests: dict[str, str] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    authorization_receipt_sha256: str | None = None

    def require_no_unresolved_parameters(self) -> None:
        bad = sorted(k for k, v in self.parameters.items() if v == UNRESOLVED)
        if bad:
            raise ExecutionAuthorityError(
                f"parameters without an authenticated source must stay unresolved and "
                f"cannot be borrowed from a previous experiment: {bad}")

    def digest(self) -> str:
        return canonical_digest({
            "mode": self.mode.value,
            "task": self.task,
            "code_sha256": self.code_sha256,
            "inputs": [{"role": i.role, "sha256": i.sha256, "bytes": i.bytes_}
                       for i in sorted(self.inputs, key=lambda x: x.role)],
            "identity_digests": self.identity_digests,
            "parameters": {k: str(v) for k, v in sorted(self.parameters.items())},
            "authorization_receipt_sha256": self.authorization_receipt_sha256 or "",
        })


def authenticate_physical_input(*, role: str, path: Path | str, expected_sha256: str,
                                mode: ExecutionMode,
                                expected_bytes: int | None = None) -> AuthenticatedInput:
    """Authenticate one physical input. Fails closed; never substitutes."""
    if mode is ExecutionMode.SYNTHETIC_TEST:
        raise ExecutionAuthorityError(
            f"SYNTHETIC_TEST may not authenticate physical input {role!r}; "
            "synthetic fixtures must never stand in for authenticated data")
    if mode is ExecutionMode.PRODUCTION:
        raise ExecutionAuthorityError(
            "PRODUCTION is CLOSED until an independently verified, task-specific "
            "authorization verifier has been implemented and reviewed")
    p = Path(path)
    if not p.is_file():
        raise ExecutionAuthorityError(
            f"required physical input {role!r} is missing at {p}. Execution stops; "
            "no synthetic, historical, zero-filled or default substitute is permitted")
    if not (isinstance(expected_sha256, str) and len(expected_sha256) == 64):
        raise ExecutionAuthorityError(
            f"{role!r} has no authenticated expected digest; the value must stay "
            "UNRESOLVED rather than being supplied by the caller")
    observed = sha256_file(p)
    if observed in QUARANTINED_DIGESTS:
        raise ExecutionAuthorityError(
            f"{role!r} resolves to a QUARANTINED artifact: {QUARANTINED_DIGESTS[observed]}")
    if role in REVIEWED_SOURCE_ROOTS:
        frozen_sha, frozen_size = REVIEWED_SOURCE_ROOTS[role]
        if expected_sha256 != frozen_sha:
            raise ExecutionAuthorityError(
                f"{role!r} caller-supplied expected digest disagrees with "
                "the independently reviewed source root")
        if expected_bytes is not None and expected_bytes != frozen_size:
            raise ExecutionAuthorityError(
                f"{role!r} caller-supplied expected size disagrees with "
                "the independently reviewed source root")
        expected_bytes = frozen_size
    if observed != expected_sha256:
        raise ExecutionAuthorityError(
            f"{role!r} digest mismatch: observed {observed}, expected {expected_sha256}. "
            "A file whose decoded arrays look correct is still a different input if its "
            "bytes differ")
    size = p.stat().st_size
    if expected_bytes is not None and size != expected_bytes:
        raise ExecutionAuthorityError(
            f"{role!r} byte size {size} != expected {expected_bytes}")
    return AuthenticatedInput(role=role, path=str(p), sha256=observed, bytes_=size)


def require_identity_order(*, name: str, observed: Iterable[Any],
                           expected_digest: str) -> str:
    """Authenticate an identity vector by ORDER, not by counts."""
    values = list(observed)
    got = order_digest(values)
    if got != expected_digest:
        raise ExecutionAuthorityError(
            f"{name} order digest mismatch: observed {got}, expected {expected_digest}. "
            "Aggregate counts are preserved by permutations and cannot authenticate an "
            "identity vector")
    return got


def reject_historical_donor_fixture(n_donors: int) -> None:
    if n_donors in FORBIDDEN_HISTORICAL_DONOR_COUNTS:
        raise ExecutionAuthorityError(
            f"donor count {n_donors} matches a historical smaller-run fixture "
            f"{FORBIDDEN_HISTORICAL_DONOR_COUNTS}; historical artifacts may be studied "
            "but must not enter a physical run")


def require_measurement_mask(*, values: np.ndarray, measured: np.ndarray,
                             name: str) -> None:
    """An unmeasured feature must be masked, never written as a zero."""
    values = np.asarray(values)
    measured = np.asarray(measured, dtype=bool)
    if values.shape != measured.shape:
        raise ExecutionAuthorityError(f"{name}: mask does not align the values")
    unmeasured = ~measured
    if unmeasured.any():
        finite_zeros = np.isfinite(values[unmeasured])
        if finite_zeros.any():
            raise ExecutionAuthorityError(
                f"{name}: {int(finite_zeros.sum())} structurally unmeasured features "
                "carry a finite value. An unmeasured feature is unknown, not zero")


def require_no_synthetic_provenance(records: Iterable[Mapping[str, Any]],
                                    *, name: str) -> None:
    """Reject synthetic rows inserted into an otherwise physical intermediate."""
    bad = [i for i, r in enumerate(records)
           if str(r.get("provenance", "")).upper() != "PHYSICAL"]
    if bad:
        raise ExecutionAuthorityError(
            f"{name}: {len(bad)} record(s) are not marked PHYSICAL provenance "
            f"(first at index {bad[0]}); synthetic observations may not enter a "
            "physical intermediate")


def open_checkpoint(*, path: Path | str, context: ExecutionContext) -> dict:
    """Load a checkpoint only if it was written under this exact context."""
    p = Path(path)
    if not p.is_file():
        raise ExecutionAuthorityError(f"checkpoint missing: {p}")
    payload = json.loads(p.read_text(encoding="utf-8"))
    stored = payload.get("context_digest")
    declared = payload.get("self_digest")
    recomputed = canonical_digest({k: v for k, v in payload.items()
                                   if k != "self_digest"})
    if declared != recomputed:
        raise ExecutionAuthorityError("checkpoint self digest does not verify")
    if stored != context.digest():
        raise ExecutionAuthorityError(
            "checkpoint was written under a different execution context. A validly "
            "rehashed checkpoint from another run is still the wrong checkpoint")
    return payload


def write_checkpoint(*, path: Path | str, context: ExecutionContext,
                     state: Mapping[str, Any]) -> str:
    payload = {"schema": "PERTURBATION_CHECKPOINT_V1",
               "context_digest": context.digest(),
               "mode": context.mode.value,
               "state": dict(state)}
    payload["self_digest"] = canonical_digest(payload)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    stage = p.with_suffix(p.suffix + ".stage")
    stage.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    stage.replace(p)
    return payload["self_digest"]


def emit_qualification_receipt(*, path: Path | str, context: ExecutionContext,
                               body: Mapping[str, Any]) -> str:
    """Write a new, immutable qualification receipt from reviewed physical roots.

    An arbitrary caller-provided digest cannot certify a physical sample.
    Existing generic roles without reviewed roots are not eligible for a
    qualification receipt. In particular, a self-attested authorization hash
    cannot enable PRODUCTION.
    """
    if context.mode is ExecutionMode.SYNTHETIC_TEST:
        raise ExecutionAuthorityError(
            "a synthetic test may not emit a qualification receipt; passing an "
            "engineering test is not physical evidence")
    if context.mode is ExecutionMode.PRODUCTION:
        raise ExecutionAuthorityError(
            "PRODUCTION is CLOSED until a separate reviewed authorization verifier "
            "exists; a caller-supplied SHA-256 is not authorization")
    context.require_no_unresolved_parameters()
    if not isinstance(body, Mapping):
        raise ExecutionAuthorityError("receipt body must be a mapping")
    collisions = RESERVED_RECEIPT_FIELDS.intersection(body)
    if collisions:
        raise ExecutionAuthorityError(
            f"receipt body attempts to override protected provenance: {sorted(collisions)}")
    if not context.inputs:
        raise ExecutionAuthorityError(
            "qualification receipt requires independently reviewed physical inputs")
    reviewed_task = REVIEWED_QUALIFICATION_TASKS.get(context.task)
    if reviewed_task is None:
        raise ExecutionAuthorityError(
            "task lacks a separately reviewed physical qualification contract")
    if context.code_sha256 != reviewed_task["code_sha256"]:
        raise ExecutionAuthorityError(
            "script digest differs from the reviewed task-specific code root")
    if context.code_path is None or not Path(context.code_path).is_file():
        raise ExecutionAuthorityError(
            "reviewed script file missing; a caller-supplied script SHA is not evidence")
    if sha256_file(Path(context.code_path)) != reviewed_task["code_sha256"]:
        raise ExecutionAuthorityError(
            "actual script bytes differ from the reviewed task-specific code root")
    roles = [item.role for item in context.inputs]
    if set(roles) != reviewed_task["roles"]:
        raise ExecutionAuthorityError(
            "physical input roles differ from the reviewed task-specific roles")
    if len(roles) != len(set(roles)):
        raise ExecutionAuthorityError("duplicate physical input roles in qualification context")
    unreviewed = sorted(set(roles) - set(REVIEWED_SOURCE_ROOTS))
    if unreviewed:
        raise ExecutionAuthorityError(
            f"qualification receipt contains roles without reviewed source roots: {unreviewed}")
    if not isinstance(context.code_sha256, str) or len(context.code_sha256) != 64:
        raise ExecutionAuthorityError("code identity must be a SHA-256")
    checked_inputs = []
    for item in context.inputs:
        expected_sha, expected_size = REVIEWED_SOURCE_ROOTS[item.role]
        if item.sha256 != expected_sha or item.bytes_ != expected_size:
            raise ExecutionAuthorityError(
                f"{item.role!r} does not match frozen input SHA and byte size")
        observed = authenticate_physical_input(
            role=item.role, path=item.path,
            expected_sha256=expected_sha, expected_bytes=expected_size,
            mode=ExecutionMode.PHYSICAL_QUALIFICATION,
        )
        checked_inputs.append(observed)
    payload = {
        "schema": "PERTURBATION_QUALIFICATION_RECEIPT_V2",
        "mode": context.mode.value,
        "task": context.task,
        "context_digest": context.digest(),
        "code_sha256": context.code_sha256,
        "inputs": [
            {"role": i.role, "path": i.path, "sha256": i.sha256, "bytes": i.bytes_}
            for i in sorted(checked_inputs, key=lambda x: x.role)
        ],
        "identity_digests": dict(context.identity_digests),
        "parameters": {k: str(v) for k, v in context.parameters.items()},
        "evidence": dict(body),
        "production_execution_authorized": False,
        "training_authorized": False,
    }
    payload["receipt_sha256"] = canonical_digest(payload)
    p = Path(path)
    # No replace/overwrite: a receipt is a one-time statement about one
    # immutable execution. Reissues require a distinct path and version.
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, indent=2) + "\n")
        handle.flush()
    return payload["receipt_sha256"]
