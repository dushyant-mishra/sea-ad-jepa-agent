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
    "ProducerAccessReceipt",
    "TDExecutionManifest",
    "build_current_td_access_policy",
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
_PROTECTED_ALLOWED = {"METADATA", "PARTITION_IDENTITY"}
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
    assignment_basis_sha: str
    fold_count: int
    crossfit_folds: tuple[CrossFitFold, ...]
    allowed_outcome_partitions: tuple[str, ...]
    protected_partitions: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "object_role": self.object_role,
            "policy_schema": self.policy_schema,
            "assignment_basis_sha": self.assignment_basis_sha,
            "fold_count": self.fold_count,
            "crossfit_folds": [fold.to_payload() for fold in self.crossfit_folds],
            "allowed_outcome_partitions": list(self.allowed_outcome_partitions),
            "protected_partitions": list(self.protected_partitions),
        }

    def canonical_sha256(self) -> str:
        return canonical_object_sha256(self.to_payload())


@dataclass(frozen=True)
class ProducerAccessReceipt:
    producer_id: str
    access_policy_sha: str
    observed_access: tuple[tuple[str, str], ...]
    numeric_result_digest: str | None = None


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

    assignment_basis_sha = canonical_object_sha256(_assignment_basis_payload(fit_donors, donor_source))
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

    flattened = [d for fold in folds for d in fold.held_out_donors]
    if sorted(flattened) != sorted(fit_donors) or len(flattened) != len(set(flattened)):
        raise ManifestError("every fit donor must appear in exactly one held-out fold")

    return PopulationAccessPolicy(
        object_role="ACCESS_POLICY",
        policy_schema="POPULATION_ACCESS_POLICY_V1",
        assignment_basis_sha=assignment_basis_sha,
        fold_count=fold_count,
        crossfit_folds=tuple(folds),
        allowed_outcome_partitions=("reader_fit",),
        protected_partitions=("reader_validation", "reader_oracle"),
    )


def validate_producer_access(policy: PopulationAccessPolicy, receipt: ProducerAccessReceipt) -> None:
    if not isinstance(policy, PopulationAccessPolicy):
        raise ManifestError("policy must be PopulationAccessPolicy")
    if not isinstance(receipt, ProducerAccessReceipt):
        raise ManifestError("receipt must be ProducerAccessReceipt")
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

    for item in receipt.observed_access:
        if type(item) is not tuple or len(item) != 2:
            raise ManifestError("observed access entries must be (partition, access_class)")
        partition, access_class = item
        if type(partition) is not str or partition not in _ALLOWED_PARTITIONS:
            raise ManifestError(f"unknown or forbidden partition: {partition}")
        if type(access_class) is not str or access_class not in _ALLOWED_ACCESS_CLASSES:
            raise ManifestError(f"unknown or forbidden access class: {access_class}")
        if partition == "reader_fit":
            continue
        if access_class not in _PROTECTED_ALLOWED:
            raise ManifestError(f"forbidden {partition} access class: {access_class}")


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
        dependencies.append((field, claimed))
    if len(semantic_shas) != len(set(semantic_shas)):
        raise ManifestError("one semantic identity cannot fill multiple manifest roles")

    return TDExecutionManifest("TD_EXECUTION_MANIFEST_V1", tuple(dependencies))
