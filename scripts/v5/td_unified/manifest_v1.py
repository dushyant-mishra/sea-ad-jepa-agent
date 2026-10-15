"""Unified Task 2 execution-manifest and population-access primitives.

This module reuses the independently accepted Task 1 canonical identity. It
never defines a second semantic serializer or authority taxonomy. Current-TD
outcome-bearing access is restricted to deterministic donor-held-out
cross-fitting inside ``reader_fit``; validation/oracle biological values remain
protected.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Callable

from scripts.v5.td_unified.canonical_v1 import canonical_sha256 as canonical_object_sha256

__all__ = [
    "ManifestError",
    "CrossFitFold",
    "PopulationAccessPolicy",
    "ObservedAccess",
    "ProducerAccessReceipt",
    "TDExecutionManifest",
    "build_current_td_access_policy",
    "validate_population_access_policy_payload",
    "validate_producer_access",
    "verify_manifest_dependency",
    "verify_raw_file_sha256",
    "verify_git_blob_sha1",
    "validate_manifest",
]


class ManifestError(ValueError):
    """Fail-closed Task 2 manifest/access error."""


_ALLOWED_PARTITIONS = {"reader_fit", "reader_validation", "reader_oracle"}
_ALLOWED_ACCESS_CLASSES = {
    "METADATA",
    "PARTITION_IDENTITY",
    "SUPPORT_ONLY_SUMMARY",
    "BIOLOGICAL_VALUES",
    "CALIBRATION_STATISTICS",
}
_PROTECTED_ALLOWED = {"PARTITION_IDENTITY"}
_FIT_PHASES = {"TRAIN", "EVAL"}
_HEX = set("0123456789abcdef")

_MANIFEST_ROLE_BY_FIELD = {
    "registry_sha": "REGISTRY",
    "observation_contract_sha": "OBSERVATION_CONTRACT",
    "support_contract_sha": "SUPPORT_CONTRACT",
    "controller_policy_sha": "CONTROLLER_POLICY",
    "candidate_registry_sha": "CANDIDATE_REGISTRY",
    "endpoint_registry_sha": "ENDPOINT_REGISTRY",
    "source_registry_sha": "SOURCE_REGISTRY",
    "qualification_registry_sha": "QUALIFICATION_REGISTRY",
    "population_split_registry_sha": "POPULATION_SPLIT_REGISTRY",
    "access_policy_sha": "ACCESS_POLICY",
    "reader_fit_policy_sha": "READER_FIT_POLICY",
    "reader_validation_policy_sha": "READER_VALIDATION_POLICY",
    "reader_oracle_policy_sha": "READER_ORACLE_POLICY",
    "crossfit_policy_sha": "CROSSFIT_POLICY",
    "protected_partition_policy_sha": "PROTECTED_PARTITION_POLICY",
}
_MANIFEST_REQUIRED = {"schema", "controller_code_sha", *_MANIFEST_ROLE_BY_FIELD}


@dataclass(frozen=True)
class CrossFitFold:
    fold_index: int
    train_donors: tuple[str, ...]
    held_out_donors: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "fold_index": self.fold_index,
            "train_donors": list(self.train_donors),
            "held_out_donors": list(self.held_out_donors),
        }


@dataclass(frozen=True)
class PopulationAccessPolicy:
    object_role: str
    policy_schema: str
    assignment_basis: dict[str, object]
    assignment_basis_sha: str
    fold_count: int
    crossfit_folds: tuple[CrossFitFold, ...]
    allowed_outcome_partitions: tuple[str, ...]
    protected_partitions: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "object_role": self.object_role,
            "policy_schema": self.policy_schema,
            "assignment_basis": self.assignment_basis,
            "assignment_basis_sha": self.assignment_basis_sha,
            "fold_count": self.fold_count,
            "crossfit_folds": [fold.to_payload() for fold in self.crossfit_folds],
            "allowed_outcome_partitions": list(self.allowed_outcome_partitions),
            "protected_partitions": list(self.protected_partitions),
        }

    def canonical_sha256(self) -> str:
        payload = self.to_payload()
        validate_population_access_policy_payload(payload)
        return canonical_object_sha256(payload)


@dataclass(frozen=True)
class ObservedAccess:
    partition: str
    access_class: str
    fold_index: int | None
    phase: str
    donor_ids: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "partition": self.partition,
            "access_class": self.access_class,
            "fold_index": self.fold_index,
            "phase": self.phase,
            "donor_ids": list(self.donor_ids),
        }


@dataclass(frozen=True)
class ProducerAccessReceipt:
    producer_id: str
    access_policy_sha: str
    observed_access: tuple[ObservedAccess, ...]
    numeric_result_digest: str | None = None
    receipt_schema: str = "PRODUCER_ACCESS_RECEIPT_V1"

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "receipt_schema": self.receipt_schema,
            "producer_id": self.producer_id,
            "access_policy_sha": self.access_policy_sha,
            "observed_access": [event.to_payload() for event in self.observed_access],
        }
        if self.numeric_result_digest is not None:
            payload["numeric_result_digest"] = self.numeric_result_digest
        return payload


@dataclass(frozen=True)
class TDExecutionManifest:
    schema: str
    dependencies: tuple[tuple[str, str], ...]

    def to_payload(self) -> dict[str, object]:
        return {"schema": self.schema, **dict(self.dependencies)}


def _is_lower_hex(value: object, length: int) -> bool:
    return type(value) is str and len(value) == length and not (set(value) - _HEX)


def _donor_sort_key(donor: str) -> tuple[str, str]:
    return hashlib.sha256(donor.encode("utf-8")).hexdigest(), donor


def _assignment_basis_payload(fit_donors: list[str], donor_source: dict[str, str]) -> dict[str, object]:
    return {
        "fit_donors": sorted(fit_donors),
        "donor_source": {donor: donor_source[donor] for donor in sorted(fit_donors)},
        "fold_count": 5,
        "assignment_law": "SOURCE_STRATIFIED_HASH_ORDER_ROUND_ROBIN_V1",
    }


def build_current_td_access_policy(
    *,
    fit_donors: list[str],
    donor_source: dict[str, str],
) -> PopulationAccessPolicy:
    if type(fit_donors) is not list or len(fit_donors) < 5:
        raise ManifestError("fit_donors must contain at least five donors")
    if len(fit_donors) != len(set(fit_donors)):
        raise ManifestError("duplicate fit donor identity")
    if type(donor_source) is not dict or set(fit_donors) != set(donor_source):
        raise ManifestError("donor_source must bind exactly the fit donors")
    if any(type(d) is not str or not d for d in fit_donors):
        raise ManifestError("donor identity must be a non-empty string")
    if any(type(s) is not str or not s for s in donor_source.values()):
        raise ManifestError("source identity must be a non-empty string")

    assignment_basis = _assignment_basis_payload(fit_donors, donor_source)
    assignment_basis_sha = canonical_object_sha256(assignment_basis)
    fold_count = 5
    held: list[list[str]] = [[] for _ in range(fold_count)]
    by_source: dict[str, list[str]] = {}
    for donor in fit_donors:
        by_source.setdefault(donor_source[donor], []).append(donor)
    offset = 0
    for source in sorted(by_source):
        donors = sorted(by_source[source], key=_donor_sort_key)
        for index, donor in enumerate(donors):
            held[(offset + index) % fold_count].append(donor)
        offset = (offset + len(donors)) % fold_count

    all_donors = tuple(sorted(fit_donors, key=_donor_sort_key))
    folds: list[CrossFitFold] = []
    for fold_index in range(fold_count):
        held_out = tuple(sorted(held[fold_index], key=_donor_sort_key))
        if not held_out:
            raise ManifestError("every cross-fit fold must contain at least one held-out donor")
        held_set = set(held_out)
        train = tuple(d for d in all_donors if d not in held_set)
        if set(train) & held_set:
            raise ManifestError("donor leakage across train/held-out fold")
        folds.append(CrossFitFold(fold_index, train, held_out))

    policy = PopulationAccessPolicy(
        object_role="ACCESS_POLICY",
        policy_schema="POPULATION_ACCESS_POLICY_V1",
        assignment_basis=assignment_basis,
        assignment_basis_sha=assignment_basis_sha,
        fold_count=fold_count,
        crossfit_folds=tuple(folds),
        allowed_outcome_partitions=("reader_fit",),
        protected_partitions=("reader_validation", "reader_oracle"),
    )
    validate_population_access_policy_payload(policy.to_payload())
    return policy


def validate_population_access_policy_payload(payload: dict[str, object]) -> None:
    if type(payload) is not dict:
        raise ManifestError("population access policy must be a dict")
    required = {
        "object_role",
        "policy_schema",
        "assignment_basis",
        "assignment_basis_sha",
        "fold_count",
        "crossfit_folds",
        "allowed_outcome_partitions",
        "protected_partitions",
    }
    if set(payload) != required:
        raise ManifestError("population access policy fields do not match POPULATION_ACCESS_POLICY_V1")
    if payload["object_role"] != "ACCESS_POLICY" or payload["policy_schema"] != "POPULATION_ACCESS_POLICY_V1":
        raise ManifestError("population access policy role/schema mismatch")
    if payload["fold_count"] != 5:
        raise ManifestError("population access policy fold_count must be 5")
    basis = payload["assignment_basis"]
    if type(basis) is not dict or set(basis) != {"fit_donors", "donor_source", "fold_count", "assignment_law"}:
        raise ManifestError("assignment basis fields are invalid")
    if basis["fold_count"] != 5 or basis["assignment_law"] != "SOURCE_STRATIFIED_HASH_ORDER_ROUND_ROBIN_V1":
        raise ManifestError("assignment basis law is invalid")
    fit_donors = basis["fit_donors"]
    donor_source = basis["donor_source"]
    if type(fit_donors) is not list or len(fit_donors) < 5 or any(type(d) is not str or not d for d in fit_donors):
        raise ManifestError("assignment basis fit donors are invalid")
    if len(fit_donors) != len(set(fit_donors)) or fit_donors != sorted(fit_donors):
        raise ManifestError("assignment basis fit donors must be unique and sorted")
    if type(donor_source) is not dict or set(donor_source) != set(fit_donors):
        raise ManifestError("assignment basis donor_source must bind exactly fit donors")
    if any(type(v) is not str or not v for v in donor_source.values()):
        raise ManifestError("assignment basis source identity is invalid")
    if not _is_lower_hex(payload["assignment_basis_sha"], 64):
        raise ManifestError("assignment basis SHA must be lowercase 64-hex")
    if canonical_object_sha256(basis) != payload["assignment_basis_sha"]:
        raise ManifestError("assignment basis digest mismatch")
    if payload["allowed_outcome_partitions"] != ["reader_fit"]:
        raise ManifestError("only reader_fit may carry current-TD outcomes")
    if payload["protected_partitions"] != ["reader_validation", "reader_oracle"]:
        raise ManifestError("protected partition set mismatch")

    folds = payload["crossfit_folds"]
    if type(folds) is not list or len(folds) != 5:
        raise ManifestError("exactly five cross-fit folds are required")
    seen_indices: set[int] = set()
    seen_held: list[str] = []
    fit_set = set(fit_donors)
    for fold in folds:
        if type(fold) is not dict or set(fold) != {"fold_index", "train_donors", "held_out_donors"}:
            raise ManifestError("cross-fit fold fields are invalid")
        index = fold["fold_index"]
        train = fold["train_donors"]
        held = fold["held_out_donors"]
        if type(index) is not int or index not in range(5) or index in seen_indices:
            raise ManifestError("cross-fit fold indices must be unique 0..4")
        seen_indices.add(index)
        if type(train) is not list or type(held) is not list or not held:
            raise ManifestError("cross-fit donor lists are invalid")
        if len(train) != len(set(train)) or len(held) != len(set(held)):
            raise ManifestError("cross-fit donor lists contain duplicates")
        if set(train) & set(held):
            raise ManifestError("cross-fit train/held donor leakage")
        if set(train) | set(held) != fit_set:
            raise ManifestError("every fold must partition the complete fit-donor set")
        seen_held.extend(held)
    if set(seen_indices) != set(range(5)):
        raise ManifestError("cross-fit fold index coverage is incomplete")
    if sorted(seen_held) != sorted(fit_donors) or len(seen_held) != len(set(seen_held)):
        raise ManifestError("every fit donor must be held out exactly once")


def validate_producer_access(policy: PopulationAccessPolicy, receipt: ProducerAccessReceipt) -> None:
    if not isinstance(policy, PopulationAccessPolicy):
        raise ManifestError("policy must be PopulationAccessPolicy")
    validate_population_access_policy_payload(policy.to_payload())
    if not isinstance(receipt, ProducerAccessReceipt):
        raise ManifestError("receipt must be ProducerAccessReceipt")
    if receipt.receipt_schema != "PRODUCER_ACCESS_RECEIPT_V1":
        raise ManifestError("unknown producer access receipt schema")
    if type(receipt.producer_id) is not str or not receipt.producer_id:
        raise ManifestError("producer_id is required")
    if not _is_lower_hex(receipt.access_policy_sha, 64):
        raise ManifestError("access policy identity must be lowercase 64-hex")
    if receipt.access_policy_sha != policy.canonical_sha256():
        raise ManifestError("access policy identity mismatch")
    if not receipt.observed_access:
        raise ManifestError("observed access must be explicitly enumerated")
    if receipt.numeric_result_digest is not None and not _is_lower_hex(receipt.numeric_result_digest, 64):
        raise ManifestError("numeric result digest must be lowercase 64-hex")

    for event in receipt.observed_access:
        if not isinstance(event, ObservedAccess):
            raise ManifestError("observed access must use structured ObservedAccess events")
        partition = event.partition
        access_class = event.access_class
        if type(partition) is not str or partition not in _ALLOWED_PARTITIONS:
            raise ManifestError(f"unknown or forbidden partition: {partition}")
        if type(access_class) is not str or access_class not in _ALLOWED_ACCESS_CLASSES:
            raise ManifestError(f"unknown or forbidden access class: {access_class}")
        if type(event.donor_ids) is not tuple or len(event.donor_ids) != len(set(event.donor_ids)):
            raise ManifestError("observed donor_ids must be a unique tuple")
        if any(type(d) is not str or not d for d in event.donor_ids):
            raise ManifestError("observed donor identity is invalid")

        if partition != "reader_fit":
            if access_class not in _PROTECTED_ALLOWED:
                raise ManifestError(f"forbidden protected {partition} access class: {access_class}")
            if event.fold_index is not None or event.phase != "CUSTODY" or event.donor_ids:
                raise ManifestError("protected partition identity access must be custody-only and donor-free")
            continue

        if type(event.fold_index) is not int or event.fold_index not in range(policy.fold_count):
            raise ManifestError("reader_fit access must bind a valid fold_index")
        if event.phase not in _FIT_PHASES:
            raise ManifestError("reader_fit access phase must be TRAIN or EVAL")
        if not event.donor_ids:
            raise ManifestError("reader_fit access must enumerate donor_ids")
        fold = policy.crossfit_folds[event.fold_index]
        permitted = set(fold.train_donors if event.phase == "TRAIN" else fold.held_out_donors)
        if not set(event.donor_ids) <= permitted:
            if event.phase == "TRAIN":
                raise ManifestError("held-out donor leakage into TRAIN access")
            raise ManifestError("train donor leakage into EVAL held-out access")


def verify_manifest_dependency(claimed_sha: str, resolved: object, *, expected_role: str) -> None:
    if not _is_lower_hex(claimed_sha, 64):
        raise ManifestError("dependency identity must be lowercase 64-hex")
    if type(resolved) is not dict:
        raise ManifestError("dependency must resolve to a canonical object")
    if resolved.get("object_role") != expected_role:
        raise ManifestError(f"dependency role mismatch for {expected_role}")
    try:
        actual = canonical_object_sha256(resolved)
    except Exception as exc:
        raise ManifestError("dependency cannot be canonically verified") from exc
    if actual != claimed_sha:
        raise ManifestError("dependency digest identity mismatch")


def verify_raw_file_sha256(claimed_sha: str, raw_bytes: bytes) -> None:
    if not _is_lower_hex(claimed_sha, 64):
        raise ManifestError("raw SHA-256 claim must be lowercase 64-hex")
    if type(raw_bytes) is not bytes:
        raise ManifestError("raw-file identity requires actual bytes")
    actual = hashlib.sha256(raw_bytes).hexdigest()
    if actual != claimed_sha:
        raise ManifestError("raw-file SHA-256 digest mismatch")


def verify_git_blob_sha1(claimed_sha: str, raw_bytes: bytes) -> None:
    if not _is_lower_hex(claimed_sha, 40):
        raise ManifestError("Git blob identity must be lowercase 40-hex")
    if type(raw_bytes) is not bytes:
        raise ManifestError("Git blob identity requires actual bytes")
    prefix = f"blob {len(raw_bytes)}\0".encode("ascii")
    actual = hashlib.sha1(prefix + raw_bytes).hexdigest()
    if actual != claimed_sha:
        raise ManifestError("Git blob identity mismatch")


def validate_manifest(payload: dict[str, object], resolver: Callable[[str], object | None]) -> TDExecutionManifest:
    if type(payload) is not dict:
        raise ManifestError("manifest must be a dict")
    if set(payload) != _MANIFEST_REQUIRED:
        raise ManifestError("manifest fields do not match TD_EXECUTION_MANIFEST_V1")
    if payload["schema"] != "TD_EXECUTION_MANIFEST_V1":
        raise ManifestError("unknown manifest schema")

    controller_code_sha = payload["controller_code_sha"]
    if not _is_lower_hex(controller_code_sha, 40):
        raise ManifestError("controller code identity must be exact lowercase 40-hex, not branch/PR metadata")
    controller_code = resolver(controller_code_sha)
    if controller_code is None:
        raise ManifestError("controller code dependency unavailable")
    verify_git_blob_sha1(controller_code_sha, controller_code)

    semantic_shas: list[str] = []
    dependencies: list[tuple[str, str]] = [("controller_code_sha", controller_code_sha)]
    for field, role in _MANIFEST_ROLE_BY_FIELD.items():
        claimed = payload[field]
        if not _is_lower_hex(claimed, 64):
            raise ManifestError(f"{field} must be exact lowercase 64-hex, not branch/PR metadata")
        semantic_shas.append(claimed)
        resolved = resolver(claimed)
        if resolved is None:
            raise ManifestError(f"manifest dependency unavailable: {field}")
        verify_manifest_dependency(claimed, resolved, expected_role=role)
        if field == "access_policy_sha":
            validate_population_access_policy_payload(resolved)
        dependencies.append((field, claimed))
    if len(semantic_shas) != len(set(semantic_shas)):
        raise ManifestError("one semantic identity cannot fill multiple manifest roles")

    return TDExecutionManifest("TD_EXECUTION_MANIFEST_V1", tuple(dependencies))
