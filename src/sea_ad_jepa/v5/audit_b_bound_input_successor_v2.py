"""Versioned successor binding for a Phase-IV bound input that legitimately moved.

Why this exists
---------------
``AUDIT_B_FROZEN_TARGET_SAMPLE.json`` records the SHA-256 of every file whose
change would alter what the frozen Audit-B target sample means. If one of those
files changes, the runtime preflight refuses to start and the regression suite
fails. That refusal is the integrity signal working, and the correct response is
never to edit the recorded digest: a frozen record must keep saying what it said.

The lawful response, named by the freeze's own failure message, is to **re-freeze
as a successor and explain the change**. This module is that successor mechanism.

What a successor may and may not do
-----------------------------------
A successor record is a narrow, pinned waiver for ONE exact transition of ONE
bound input. It is deliberately harder to satisfy than the original digest check:

* it may cover only roles that have ACTUALLY drifted - listing an unchanged role
  is rejected, so a blanket pre-authorization cannot be written in advance;
* ``from_sha256`` must equal the digest the parent freeze recorded and
  ``to_sha256`` must equal the digest observed right now, so the waiver expires
  the moment the file moves again;
* the parent freeze must still be byte-identical and must still carry the pinned
  Phase-IV freeze digest, so the original record cannot be quietly rewritten;
* the record's own canonical digest must equal a constant pinned in this module,
  so the JSON cannot be edited without a reviewed code change;
* only ``LEGITIMATE_VERSION_CHANGE`` continues a binding. ``UNINTENDED_MODIFICATION``
  and ``SEMANTIC_CHANGE`` are recordable but NON-AUTHORIZING: they are refusals
  with an explanation attached, not permissions;
* it must attest that the frozen SAMPLE ITSELF is unchanged - re-derived from the
  same salt and the same target universe - because a re-rolled sample is the
  precise attack a freeze exists to prevent;
* it must name an executed equivalence receipt, bound by digest, and that receipt
  must report bitwise equality.

A successor authorizes nothing else. It does not authorize Audit-B execution, it
does not resolve a precision scope, it does not open any terminal masking
outcome, and it does not authorize training.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .audit_b_execution_contract_v1 import PHASE_IV_SAMPLE_FREEZE_DIGEST

SCHEMA = "V5_AUDIT_B_BOUND_INPUT_SUCCESSOR_V2"

#: The only classification that continues a binding. The other two are recorded
#: for honesty and explicitly refuse.
AUTHORIZING_CLASSIFICATION = "LEGITIMATE_VERSION_CHANGE"
NON_AUTHORIZING_CLASSIFICATIONS = ("UNINTENDED_MODIFICATION", "SEMANTIC_CHANGE")
VALID_CLASSIFICATIONS = (AUTHORIZING_CLASSIFICATION,) + NON_AUTHORIZING_CLASSIFICATIONS

#: Canonical digest of the reviewed successor record. Pinned here for the same
#: reason PHASE_IV_SAMPLE_FREEZE_DIGEST is pinned: the JSON alone cannot grant
#: itself authority.
AUDIT_B_BOUND_INPUT_SUCCESSOR_V2_DIGEST = (
    "e62f261d746dbe4b6623c38f18f9f061df2892227932d7d5924c001de2e0e2e6"
)

REPO_ROOT = Path(__file__).resolve().parents[3]

SUCCESSOR_RECORD_PATH = REPO_ROOT / (
    "analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/"
    "AUDIT_B_BOUND_INPUT_SUCCESSOR_V2.json"
)

_REQUIRED_BINDING_FIELDS = (
    "path",
    "from_sha256",
    "to_sha256",
    "classification",
    "rationale",
    "source_commit",
    "source_pull_request",
    "equivalence_receipt_path",
    "equivalence_receipt_sha256",
)


def sha256_file(path: str | Path) -> str:
    target = Path(path)
    if not target.is_file():
        raise ValueError(f"required file is missing: {target}")
    digest = hashlib.sha256()
    with target.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_digest(payload: Mapping[str, Any]) -> str:
    """Digest over everything that carries authority, excluding the digest field."""
    material = json.dumps(
        {
            "schema": payload["schema"],
            "parent_freeze_digest": payload["parent_freeze_digest"],
            "parent_freeze_artifact_sha256": payload["parent_freeze_artifact_sha256"],
            "parent_freeze_path": payload["parent_freeze_path"],
            "sample_identity": payload["sample_identity"],
            "superseded_bindings": payload["superseded_bindings"],
            "unchanged_bindings": payload["unchanged_bindings"],
            "required_execution_mode": payload["required_execution_mode"],
            "frozen_before_any_burden_was_computed": payload[
                "frozen_before_any_burden_was_computed"
            ],
            "execution_authorized": payload["execution_authorized"],
            "terminal_masking_outcomes_inspected": payload[
                "terminal_masking_outcomes_inspected"
            ],
            "training_authorized": payload["training_authorized"],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value)
    )


def load_successor(
    path: str | Path,
    *,
    repo_root: str | Path,
    require_pinned_digest: bool = True,
) -> dict[str, Any]:
    """Validate a successor record. Raises rather than returning a partial result."""
    record_path = Path(path)
    if not record_path.is_file():
        raise ValueError(f"bound-input successor record is missing: {record_path}")
    payload = json.loads(record_path.read_text(encoding="utf-8"))

    if payload.get("schema") != SCHEMA:
        raise ValueError("bound-input successor schema mismatch")

    for flag, message in (
        ("execution_authorized", "successor record unexpectedly authorizes execution"),
        (
            "terminal_masking_outcomes_inspected",
            "successor record indicates terminal masking outcomes were inspected",
        ),
        ("training_authorized", "successor record unexpectedly authorizes training"),
    ):
        if payload.get(flag) is not False:
            raise ValueError(message)
    if payload.get("frozen_before_any_burden_was_computed") is not True:
        raise ValueError(
            "successor record does not attest that it precedes any burden computation"
        )

    observed = canonical_digest(payload)
    if payload.get("successor_digest") != observed:
        raise ValueError("bound-input successor internal digest mismatch")
    if require_pinned_digest and observed != AUDIT_B_BOUND_INPUT_SUCCESSOR_V2_DIGEST:
        raise ValueError(
            "runtime uses a different bound-input successor record: "
            f"expected {AUDIT_B_BOUND_INPUT_SUCCESSOR_V2_DIGEST}, observed {observed}"
        )

    if payload.get("parent_freeze_digest") != PHASE_IV_SAMPLE_FREEZE_DIGEST:
        raise ValueError("successor record does not descend from the pinned Phase-IV freeze")

    root = Path(repo_root).resolve()
    parent_rel = payload.get("parent_freeze_path")
    if not isinstance(parent_rel, str) or not parent_rel or Path(parent_rel).is_absolute():
        raise ValueError("successor parent_freeze_path must be a relative repo path")
    parent_path = (root / parent_rel).resolve()
    try:
        parent_path.relative_to(root)
    except ValueError as exc:
        raise ValueError("successor parent_freeze_path escapes repo_root") from exc
    parent_actual = sha256_file(parent_path)
    if parent_actual != payload.get("parent_freeze_artifact_sha256"):
        raise ValueError(
            "the parent Phase-IV freeze artifact has been modified: "
            f"expected {payload.get('parent_freeze_artifact_sha256')}, observed {parent_actual}"
        )

    identity = payload.get("sample_identity")
    if not isinstance(identity, dict):
        raise ValueError("successor record is missing its sample-identity attestation")
    if identity.get("sample_is_unchanged") is not True:
        raise ValueError("successor record does not attest an unchanged target sample")
    if identity.get("rederived_from_parent_salt_and_universe") is not True:
        raise ValueError(
            "successor record did not re-derive the sample from the parent salt and universe"
        )
    if identity.get("parent_samples_digest") != identity.get("rederived_samples_digest"):
        raise ValueError(
            "the re-derived target sample does not match the parent sample; "
            "the sample was re-rolled and no successor can rescue it"
        )
    if not _is_sha256(identity.get("parent_samples_digest")):
        raise ValueError("successor sample-identity digest is malformed")

    superseded = payload.get("superseded_bindings")
    if not isinstance(superseded, dict) or not superseded:
        raise ValueError("successor record must supersede at least one binding")
    for role, rec in superseded.items():
        if not isinstance(rec, dict):
            raise ValueError(f"successor binding {role} is malformed")
        missing = [f for f in _REQUIRED_BINDING_FIELDS if f not in rec]
        if missing:
            raise ValueError(f"successor binding {role} is missing fields: {missing}")
        if not _is_sha256(rec["from_sha256"]) or not _is_sha256(rec["to_sha256"]):
            raise ValueError(f"successor binding {role} has a malformed digest")
        if rec["from_sha256"] == rec["to_sha256"]:
            raise ValueError(
                f"successor binding {role} supersedes a digest with itself; "
                "a successor may only record an actual change"
            )
        if rec["classification"] not in VALID_CLASSIFICATIONS:
            raise ValueError(
                f"successor binding {role} has an unknown classification "
                f"{rec['classification']!r}"
            )
        if not isinstance(rec["rationale"], str) or len(rec["rationale"].strip()) < 40:
            raise ValueError(
                f"successor binding {role} needs a written rationale, not a label"
            )
        if not _is_sha256(rec["equivalence_receipt_sha256"]):
            raise ValueError(f"successor binding {role} has a malformed receipt digest")
        receipt_rel = rec["equivalence_receipt_path"]
        if not isinstance(receipt_rel, str) or Path(receipt_rel).is_absolute():
            raise ValueError(
                f"successor binding {role} receipt must use a relative repo path"
            )
        receipt_path = (root / receipt_rel).resolve()
        try:
            receipt_path.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"successor binding {role} receipt escapes repo_root") from exc
        receipt_actual = sha256_file(receipt_path)
        if receipt_actual != rec["equivalence_receipt_sha256"]:
            raise ValueError(
                f"successor binding {role} equivalence receipt drifted: "
                f"expected {rec['equivalence_receipt_sha256']}, observed {receipt_actual}"
            )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("equivalent") is not True:
            raise ValueError(
                f"successor binding {role} cites an equivalence receipt that did not pass"
            )
        if receipt.get("frozen_planner_sha256") != rec["from_sha256"]:
            raise ValueError(
                f"successor binding {role} receipt does not compare the recorded old bytes"
            )
        if receipt.get("successor_planner_sha256") != rec["to_sha256"]:
            raise ValueError(
                f"successor binding {role} receipt does not compare the observed new bytes"
            )

    unchanged = payload.get("unchanged_bindings")
    if not isinstance(unchanged, dict):
        raise ValueError("successor record must list the bindings it does not supersede")
    overlap = sorted(set(unchanged) & set(superseded))
    if overlap:
        raise ValueError(
            f"successor record lists {overlap} as both superseded and unchanged"
        )

    mode = payload.get("required_execution_mode")
    if not isinstance(mode, dict) or not mode:
        raise ValueError(
            "successor record must pin the execution mode of the superseded planner"
        )

    return payload


def resolve_drift(
    role: str,
    *,
    recorded: str,
    observed: str,
    successor: Mapping[str, Any] | None,
) -> None:
    """Permit one drifted bound input, or raise with the reason it is not permitted.

    ``successor`` of ``None`` means no waiver was offered, which is the
    fail-closed default. This function never returns a boolean: a caller cannot
    accidentally ignore its verdict.
    """
    if successor is None:
        raise ValueError(
            f"Phase-IV bound input drift for {role}: "
            f"expected {recorded}, observed {observed}"
        )
    superseded = successor.get("superseded_bindings", {})
    rec = superseded.get(role)
    if rec is None:
        raise ValueError(
            f"Phase-IV bound input drift for {role}: expected {recorded}, "
            f"observed {observed}; the successor record does not cover this role"
        )
    if rec["from_sha256"] != recorded:
        raise ValueError(
            f"successor binding {role} supersedes {rec['from_sha256']} but the frozen "
            f"record says {recorded}"
        )
    if rec["to_sha256"] != observed:
        raise ValueError(
            f"successor binding {role} authorizes {rec['to_sha256']} but the checkout "
            f"contains {observed}"
        )
    if rec["classification"] != AUTHORIZING_CLASSIFICATION:
        raise ValueError(
            f"successor binding {role} is classified {rec['classification']}, which "
            "records the change but does not continue the binding"
        )


def assert_no_uncovered_supersessions(
    *,
    successor: Mapping[str, Any] | None,
    drifted_roles: Mapping[str, tuple[str, str]],
) -> None:
    """Reject a successor that waives a role which did not actually drift.

    Without this, a successor could be written ahead of time to pre-authorize a
    future edit. A waiver must always be a response to an observed change.
    """
    if successor is None:
        return
    declared = set(successor.get("superseded_bindings", {}))
    unnecessary = sorted(declared - set(drifted_roles))
    if unnecessary:
        raise ValueError(
            "successor record supersedes bindings that did not drift: "
            f"{unnecessary}; a successor may not pre-authorize a future change"
        )
