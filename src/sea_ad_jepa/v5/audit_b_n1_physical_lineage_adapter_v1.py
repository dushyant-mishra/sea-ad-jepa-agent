"""Corrected-source PHYSICAL N1 lineage adapter.

The synthetic counterpart (`audit_b_n1_synthetic_lineage_adapter_v1`) proves the
crash-safe mechanics. This module is its physical sibling: it authenticates real
FULL104 bytes before any molecular data is opened, and it is deliberately unable
to authorize a real N1 run on its own.

What it binds, and why each is by BYTES rather than by declaration
------------------------------------------------------------------
* the **corrected** derivative ``4b15ee52…`` — not the quarantined original;
* the frozen pass1 ``37f79e49…`` as a **whole-file** digest (PR #76), because the
  split receipt pins that value and the earlier code read pass1 without checking it;
* the reviewed V2 receipts and the PR #69 per-member manifest;
* donor registry, donor→source, fold, strict-core and frozen-target vectors, each
  by an **order-sensitive** digest, because a permutation preserving 41/17/46 or
  28/26/25/25 is invisible to a count check.

Relationship to the PR #62 binder
---------------------------------
`audit_b_n1_physical_binding_v1` pins ``f77dff47…``, the quarantined artifact. It
stays useful precisely as a **negative regression control** — it must keep
rejecting the corrected derivative and keep binding the original — and it is not
used here as a positive authenticator.

What this module does NOT do
----------------------------
It opens no molecular data, selects no target, draws no mask, computes no burden
or precision, and issues no execution authority. Passing every gate here means the
inputs are authenticated; it does not mean N1 may run.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

# ---- frozen roots, all authenticated by bytes -------------------------------
CORRECTED_DERIVATIVE_SHA256 = "4b15ee5238c6e48d931329d222a9488a7b4f122c58767b6615a0b480afc4800b"
CORRECTED_DERIVATIVE_BYTES = 363_053_057
QUARANTINED_ORIGINAL_SHA256 = "f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae"
FROZEN_PASS1_SHA256 = "37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1"
SPLIT_CANONICAL_SHA256 = "5d616c9c509d8224d15d6e8c163ca38b4b5140a44fdab4c2fa00efad7a8f01e4"
FULL104_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
SPLIT_FILE_SHA256 = "56f045d7dc80fde7e30c97632c1d109286e4b8f9f033b77476521c2822980585"
ARRAY_MANIFEST_FILE_SHA256 = "9517b95446013c7f803df0b63b662d24f2e1df81f0b4917a2af41dae1df2b1ee"
V2_PREFLIGHT_FILE_SHA256 = "28dc18d2c7f9876c6b93cce318ecc0bb6fac42068e819b9047099a63eeaad91c"
PHYSICAL_INPUT_ROOTS = {
    "corrected_derivative": CORRECTED_DERIVATIVE_SHA256,
    "pass1_whole_file": FROZEN_PASS1_SHA256,
    "full104_level4_manifest": FULL104_MANIFEST_SHA256,
    "split_receipt": SPLIT_FILE_SHA256,
    "per_member_manifest": ARRAY_MANIFEST_FILE_SHA256,
    "v2_preflight_receipt": V2_PREFLIGHT_FILE_SHA256,
}
PROTECTED_RECEIPT_KEYS = frozenset({
    "schema", "mode", "task", "context_digest", "code_sha256", "inputs",
    "identity_digests", "parameters", "n1_execution_authorized", "audit_b_n1",
    "masks_executed", "burden_calculated", "precision_calculated",
    "training_authorized", "receipt_sha256",
})

SOURCE_NAMES = ("HVS", "NPH52", "SEA_AD")
EXPECTED_SOURCE_COUNTS = (41, 17, 46)
EXPECTED_FOLD_COUNTS = (28, 26, 25, 25)
N_DONORS = 104
CORE_SIZE = 17_186
N_CELLS = 4_553_407
N_MEMBERS = 35

#: Digests that may never satisfy a physical role, whatever the file is called.
QUARANTINED = {
    QUARANTINED_ORIGINAL_SHA256:
        "original FULL104 sufficient statistics: transposed source encoding, "
        "src_of_cell disagrees with donor_src[cell_donor] for 4,354,689 cells",
}

#: Historical smaller-run donor counts that must never satisfy a FULL104 role.
FORBIDDEN_HISTORICAL_DONOR_COUNTS = (6, 42, 48)


class ExecutionMode(Enum):
    """Shared vocabulary with the perturbation lane's execution authority."""
    SYNTHETIC_TEST = "SYNTHETIC_TEST"
    PHYSICAL_QUALIFICATION = "PHYSICAL_QUALIFICATION"
    PRODUCTION = "PRODUCTION"


class PhysicalLineageError(RuntimeError):
    """Every gate failure. Never caught inside this module."""


UNRESOLVED = "UNRESOLVED"


def sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def order_digest(values: Iterable[Any]) -> str:
    payload = json.dumps([str(v) for v in values], ensure_ascii=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b"ORDERED|" + payload).hexdigest()


def canonical_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False)
                          .encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PhysicalInput:
    role: str
    path: str
    sha256: str
    bytes_: int


def authenticate_file(*, role: str, path: Path | str, expected_sha256: str,
                      mode: ExecutionMode, expected_bytes: int | None = None) -> PhysicalInput:
    """Authenticate one real file. Fails closed; substitutes nothing, ever."""
    if mode is ExecutionMode.SYNTHETIC_TEST:
        raise PhysicalLineageError(
            f"SYNTHETIC_TEST may not authenticate physical input {role!r}; a synthetic "
            "fixture must never satisfy a physical requirement")
    p = Path(path)
    if not p.is_file():
        raise PhysicalLineageError(
            f"required physical input {role!r} is missing at {p}. Execution stops; no "
            "synthetic fixture, historical smaller run, zero array or default is used")
    if not (isinstance(expected_sha256, str) and len(expected_sha256) == 64
            and expected_sha256 == expected_sha256.lower()):
        raise PhysicalLineageError(
            f"{role!r} has no authenticated expected digest; it must stay UNRESOLVED "
            "rather than be supplied by the caller")
    observed = sha256_file(p)
    if observed in QUARANTINED:
        raise PhysicalLineageError(
            f"{role!r} resolves to a QUARANTINED artifact: {QUARANTINED[observed]}")
    if observed != expected_sha256:
        raise PhysicalLineageError(
            f"{role!r} byte digest mismatch: observed {observed}, expected "
            f"{expected_sha256}. Identical decoded arrays in a different container are "
            "still a different input")
    size = p.stat().st_size
    if expected_bytes is not None and size != expected_bytes:
        raise PhysicalLineageError(f"{role!r} size {size} != expected {expected_bytes}")
    return PhysicalInput(role=role, path=str(p), sha256=observed, bytes_=size)


def require_order(*, name: str, observed: Iterable[Any], expected_digest: str) -> str:
    got = order_digest(observed)
    if got != expected_digest:
        raise PhysicalLineageError(
            f"{name} order digest mismatch: observed {got}, expected {expected_digest}. "
            "Aggregate counts are permutation-invariant and cannot authenticate order")
    return got


def reject_historical_donor_count(n: int) -> None:
    if n in FORBIDDEN_HISTORICAL_DONOR_COUNTS:
        raise PhysicalLineageError(
            f"donor count {n} matches a historical smaller-run fixture "
            f"{FORBIDDEN_HISTORICAL_DONOR_COUNTS}; historical artifacts stay available "
            "for comparison but must not become production inputs")
    if n != N_DONORS:
        raise PhysicalLineageError(f"FULL104 requires {N_DONORS} donors, found {n}")


@dataclass
class PhysicalExecutionContext:
    """Immutable execution identity. Every journal unit must carry its digest."""

    mode: ExecutionMode
    task: str
    code_sha256: str
    inputs: list[PhysicalInput] = field(default_factory=list)
    identity_digests: dict[str, str] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    execution_authorization_sha256: str | None = None
    n1_execution_authorized: bool = False

    def require_resolved(self) -> None:
        bad = sorted(k for k, v in self.parameters.items() if v == UNRESOLVED)
        if bad:
            raise PhysicalLineageError(
                f"parameters lacking an authenticated authority must remain unresolved "
                f"and may not be borrowed from a previous experiment: {bad}")

    def digest(self) -> str:
        return canonical_digest({
            "mode": self.mode.value,
            "task": self.task,
            "code_sha256": self.code_sha256,
            "inputs": [{"role": i.role, "sha256": i.sha256, "bytes": i.bytes_}
                       for i in sorted(self.inputs, key=lambda x: x.role)],
            "identity_digests": dict(sorted(self.identity_digests.items())),
            "parameters": {k: str(v) for k, v in sorted(self.parameters.items())},
            "execution_authorization_sha256": self.execution_authorization_sha256 or "",
            "n1_execution_authorized": bool(self.n1_execution_authorized),
        })


def authenticate_corrected_inputs(
    *, mode: ExecutionMode, derivative: Path | str, pass1: Path | str,
    split_receipt: Path | str, level4_manifest: Path | str,
    array_manifest: Path | str, preflight_receipt: Path | str,
) -> list[PhysicalInput]:
    """Authenticate the corrected FULL104 chain by bytes, in one place."""
    inputs = [
        authenticate_file(role="corrected_derivative", path=derivative,
                          expected_sha256=CORRECTED_DERIVATIVE_SHA256, mode=mode,
                          expected_bytes=CORRECTED_DERIVATIVE_BYTES),
        # PR #76 whole-file gate: the split receipt pins this value.
        authenticate_file(role="pass1_whole_file", path=pass1,
                          expected_sha256=FROZEN_PASS1_SHA256, mode=mode),
    ]
    man = Path(level4_manifest)
    inputs.append(authenticate_file(role="full104_level4_manifest", path=man,
                                    expected_sha256=FULL104_MANIFEST_SHA256, mode=mode))
    # Freeze the whole receipt files, not just their self-declared canonical
    # fields; otherwise a forged/resealed JSON can mimic a reviewed receipt.
    for role, file_path in (
        ("split_receipt", split_receipt),
        ("per_member_manifest", array_manifest),
        ("v2_preflight_receipt", preflight_receipt),
    ):
        inputs.append(authenticate_file(
            role=role, path=file_path, expected_sha256=PHYSICAL_INPUT_ROOTS[role],
            mode=mode,
        ))
    split = json.loads(Path(split_receipt).read_text(encoding="utf-8"))
    if split.get("receipt_sha256") != SPLIT_CANONICAL_SHA256:
        raise PhysicalLineageError("split receipt carries the wrong frozen canonical digest")
    if split.get("pass1_npz_sha256") != FROZEN_PASS1_SHA256:
        raise PhysicalLineageError(
            "split receipt pins a different pass1 whole-file digest than the one supplied")
    am = json.loads(Path(array_manifest).read_text(encoding="utf-8"))
    if am.get("derivative_sha256") != CORRECTED_DERIVATIVE_SHA256:
        raise PhysicalLineageError("per-member manifest binds a different derivative")
    if am.get("members_total") != N_MEMBERS or am.get("members_changed") != 2:
        raise PhysicalLineageError(
            f"per-member manifest census drift: {am.get('members_total')} members, "
            f"{am.get('members_changed')} changed")
    pf = json.loads(Path(preflight_receipt).read_text(encoding="utf-8"))
    if pf.get("derivative_sha256") != CORRECTED_DERIVATIVE_SHA256:
        raise PhysicalLineageError("preflight receipt binds a different derivative")
    if pf.get("source_invariant_violations") != 0:
        raise PhysicalLineageError("preflight receipt reports source-invariant violations")
    return inputs


def preflight_corrected_derivative(*, derivative: Path | str, pass1: Path | str,
                                   mode: ExecutionMode) -> dict[str, str]:
    """Read-only structural preflight. Opens no molecular outcome."""
    if mode is ExecutionMode.SYNTHETIC_TEST:
        raise PhysicalLineageError("SYNTHETIC_TEST may not preflight physical data")
    z = np.load(Path(derivative), allow_pickle=True)
    core = np.asarray(z["core"], dtype=np.int64)
    duniq = [str(x) for x in z["duniq"]]
    donor_src = np.asarray(z["donor_src"], dtype=np.int64)
    src_of_cell = np.asarray(z["src_of_cell"], dtype=np.int64)
    names = [str(x) for x in z["source_names"]]

    if tuple(names) != SOURCE_NAMES:
        raise PhysicalLineageError(f"source names are not the corrected order: {names}")
    reject_historical_donor_count(len(duniq))
    if duniq != sorted(set(duniq)):
        raise PhysicalLineageError("donor registry is not a sorted unique list")
    if core.size != CORE_SIZE or not np.all(np.diff(core) > 0):
        raise PhysicalLineageError("strict-core order invalid")
    if tuple(int(x) for x in np.bincount(donor_src, minlength=3)) != EXPECTED_SOURCE_COUNTS:
        raise PhysicalLineageError("donor/source census is not 41/17/46")

    p1 = np.load(Path(pass1), allow_pickle=True)
    cell_donor = np.asarray(p1["cell_donor"], dtype=np.int64)
    if cell_donor.size != N_CELLS:
        raise PhysicalLineageError("pass1 cell_donor length mismatch")
    if src_of_cell.size != N_CELLS or src_of_cell.dtype != np.int64:
        raise PhysicalLineageError("src_of_cell must be exact int64 over all cells")
    bad = int(np.count_nonzero(src_of_cell != donor_src[cell_donor]))
    if bad:
        raise PhysicalLineageError(
            f"corrected source invariant violated for {bad} cells; this artifact is not "
            "the corrected derivative")
    return {
        "donor_order": order_digest(duniq),
        "donor_source_order": order_digest(donor_src.tolist()),
        "strict_core_order": order_digest(core.tolist()),
        "src_of_cell_digest": hashlib.sha256(src_of_cell.tobytes()).hexdigest(),
    }


def build_context(*, mode: ExecutionMode, task: str, code_sha256: str,
                  inputs: list[PhysicalInput], identity_digests: Mapping[str, str],
                  parameters: Mapping[str, Any]) -> PhysicalExecutionContext:
    ctx = PhysicalExecutionContext(
        mode=mode, task=task, code_sha256=code_sha256, inputs=list(inputs),
        identity_digests=dict(identity_digests), parameters=dict(parameters))
    ctx.require_resolved()
    if any(i.sha256 == QUARANTINED_ORIGINAL_SHA256 for i in ctx.inputs):
        raise PhysicalLineageError("a quarantined artifact reached the execution context")
    return ctx


def require_n1_execution_authority(ctx: PhysicalExecutionContext) -> None:
    """FAIL CLOSED: this qualification module cannot verify a production grant.

    A caller-supplied 64-character hash and mutable Boolean are not a reviewed
    authorization. A separate future executor must implement an independently
    anchored, versioned authorization verifier; do not silently add a success
    path to this preflight module.
    """
    raise PhysicalLineageError(
        "STOP_N1_NOT_AUTHORIZED: no reviewed execution authorization verifier "
        "exists in this adapter; PRODUCTION mode, a claimed SHA and a Boolean "
        "cannot unlock molecular N1"
    )


def emit_adapter_qualification_receipt(*, path: Path | str,
                                       ctx: PhysicalExecutionContext,
                                       body: Mapping[str, Any]) -> str:
    """Issue only immutable V2 physical *qualification*, never N1 authority."""
    if ctx.mode is not ExecutionMode.PHYSICAL_QUALIFICATION:
        raise PhysicalLineageError(
            "only PHYSICAL_QUALIFICATION can issue the non-authoritative "
            "adapter receipt; synthetic or PRODUCTION mode is forbidden")
    ctx.require_resolved()
    if not isinstance(body, Mapping):
        raise PhysicalLineageError("qualification evidence body must be a mapping")
    overlap = PROTECTED_RECEIPT_KEYS.intersection(body)
    if overlap:
        raise PhysicalLineageError(
            f"qualification body attempts to override protected fields: {sorted(overlap)}")
    if body.get("terminal") != "PHYSICAL_ADAPTER_QUALIFIED_FOR_INDEPENDENT_REVIEW":
        raise PhysicalLineageError(
            "receipt requires the explicit, non-authoritative physical-review terminal")
    roles = [x.role for x in ctx.inputs]
    if len(roles) != len(set(roles)) or set(roles) != set(PHYSICAL_INPUT_ROOTS):
        raise PhysicalLineageError(
            "physical qualification requires all six distinct, independently pinned roles")
    if ctx.n1_execution_authorized or ctx.execution_authorization_sha256:
        raise PhysicalLineageError(
            "adapter preflight cannot carry claimed production execution authority")
    if ctx.code_sha256 != sha256_file(Path(__file__)):
        raise PhysicalLineageError(
            "adapter implementation code root does not match actual loaded source bytes")
    # TOCTOU reduction: recompute each physical digest at publication, rather
    # than trusting PhysicalInput dataclass fields captured earlier.
    for item in ctx.inputs:
        expected = PHYSICAL_INPUT_ROOTS[item.role]
        if item.sha256 != expected:
            raise PhysicalLineageError(
                f"{item.role} digest differs from independently reviewed frozen root")
        authenticate_file(
            role=item.role, path=item.path, expected_sha256=expected,
            expected_bytes=item.bytes_, mode=ExecutionMode.PHYSICAL_QUALIFICATION,
        )
    payload = {
        "schema": "AUDIT_B_N1_PHYSICAL_ADAPTER_QUALIFICATION_V2",
        "mode": ctx.mode.value,
        "task": ctx.task,
        "context_digest": ctx.digest(),
        "code_sha256": ctx.code_sha256,
        "inputs": [
            {"role": i.role, "path": i.path, "sha256": i.sha256, "bytes": i.bytes_}
            for i in sorted(ctx.inputs, key=lambda x: x.role)
        ],
        "identity_digests": dict(ctx.identity_digests),
        "parameters": {k: str(v) for k, v in ctx.parameters.items()},
        "n1_execution_authorized": False,
        "audit_b_n1": "UNOPENED",
        "masks_executed": "NONE",
        "burden_calculated": False,
        "precision_calculated": False,
        "training_authorized": False,
        "evidence": dict(body),
    }
    payload["receipt_sha256"] = canonical_digest(payload)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation: do not silently overwrite historical V1 receipts.
    with p.open("x", encoding="utf-8") as out:
        out.write(json.dumps(payload, sort_keys=True, indent=2) + "\n")
        out.flush()
    return payload["receipt_sha256"]
