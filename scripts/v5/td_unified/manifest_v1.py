"""Unified Task 2 execution-manifest and population-access primitives.

This module reuses Task 1 canonical identity. It does not define a second
serializer or authority taxonomy.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Callable

from scripts.v5.td_unified.canonical_v1 import canonical_sha256

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


@dataclass(frozen=True)
class CrossFitFold:
    fold_index: int
    train_donors: tuple[str, ...]
    held_out_donors: tuple[str, ...]


@dataclass(frozen=True)
class PopulationAccessPolicy:
    object_role: str
    policy_schema: str
    fold_count: int
    crossfit_folds: tuple[CrossFitFold, ...]
    allowed_outcome_partitions: tuple[str, ...]
    protected_partitions: tuple[str, ...]


@dataclass(frozen=True)
class ProducerAccessReceipt:
    producer_id: str
    observed_access: tuple[tuple[str, str], ...]
    numeric_result_digest: str | None = None


@dataclass(frozen=True)
class TDExecutionManifest:
    schema: str
    registry_sha: str
    access_policy_sha: str


def _donor_sort_key(donor: str) -> tuple[str, str]:
    return donor, hashlib.sha256(donor.encode("utf-8")).hexdigest()


def build_current_td_access_policy(
    *,
    fit_donors: list[str],
    donor_source: dict[str, str],
) -> PopulationAccessPolicy:
    if not isinstance(fit_donors, list) or not fit_donors:
        raise ManifestError("fit_donors must be a non-empty list")
    if len(fit_donors) != len(set(fit_donors)):
        raise ManifestError("duplicate fit donor identity")
    if set(fit_donors) != set(donor_source):
        raise ManifestError("donor_source must bind exactly the fit donors")
    if any(type(d) is not str or not d for d in fit_donors):
        raise ManifestError("donor identity must be a non-empty string")
    if any(type(s) is not str or not s for s in donor_source.values()):
        raise ManifestError("source identity must be a non-empty string")

    fold_count = 5
    held: list[list[str]] = [[] for _ in range(fold_count)]
    # Deterministic, outcome-blind source-stratified round-robin assignment.
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
        held_set = set(held_out)
        train = tuple(d for d in all_donors if d not in held_set)
        if set(train) & held_set:
            raise ManifestError("donor leakage across train/held-out fold")
        folds.append(CrossFitFold(fold_index, train, held_out))

    flattened = [d for fold in folds for d in fold.held_out_donors]
    if sorted(flattened) != sorted(fit_donors):
        raise ManifestError("every fit donor must appear in exactly one held-out fold")

    return PopulationAccessPolicy(
        object_role="ACCESS_POLICY",
        policy_schema="POPULATION_ACCESS_POLICY_V1",
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
    if not receipt.observed_access:
        raise ManifestError("observed access must be explicitly enumerated")

    for item in receipt.observed_access:
        if type(item) is not tuple or len(item) != 2:
            raise ManifestError("observed access entries must be (partition, access_class)")
        partition, access_class = item
        if partition not in _ALLOWED_PARTITIONS:
            raise ManifestError(f"unknown or forbidden partition: {partition}")
        if access_class not in _ALLOWED_ACCESS_CLASSES:
            raise ManifestError(f"unknown or forbidden access class: {access_class}")
        if partition == "reader_fit":
            continue
        if access_class not in _PROTECTED_ALLOWED:
            raise ManifestError(f"forbidden {partition} access class: {access_class}")


def verify_manifest_dependency(claimed_sha: str, resolved: object, *, expected_role: str) -> None:
    if type(claimed_sha) is not str or len(claimed_sha) != 64 or set(claimed_sha) - _HEX:
        raise ManifestError("dependency identity must be lowercase 64-hex")
    if type(resolved) is not dict:
        raise ManifestError("dependency must resolve to a canonical object")
    if resolved.get("object_role") != expected_role:
        raise ManifestError(f"dependency role mismatch for {expected_role}")
    try:
        actual = canonical_sha256(resolved)
    except Exception as exc:
        raise ManifestError("dependency cannot be canonically verified") from exc
    if actual != claimed_sha:
        raise ManifestError("dependency digest identity mismatch")


def verify_raw_file_sha256(claimed_sha: str, raw_bytes: bytes) -> None:
    if type(claimed_sha) is not str or len(claimed_sha) != 64 or set(claimed_sha) - _HEX:
        raise ManifestError("raw SHA-256 claim must be lowercase 64-hex")
    if type(raw_bytes) is not bytes:
        raise ManifestError("raw-file identity requires actual bytes")
    actual = hashlib.sha256(raw_bytes).hexdigest()
    if actual != claimed_sha:
        raise ManifestError("raw-file SHA-256 digest mismatch")


def validate_manifest(payload: dict[str, object], resolver: Callable[[str], object | None]) -> TDExecutionManifest:
    if type(payload) is not dict:
        raise ManifestError("manifest must be a dict")
    required = {"schema", "registry_sha", "access_policy_sha"}
    if set(payload) != required:
        raise ManifestError("manifest fields do not match TD_EXECUTION_MANIFEST_V1")
    if payload["schema"] != "TD_EXECUTION_MANIFEST_V1":
        raise ManifestError("unknown manifest schema")
    registry_sha = payload["registry_sha"]
    access_policy_sha = payload["access_policy_sha"]
    if type(registry_sha) is not str or len(registry_sha) != 64 or set(registry_sha) - _HEX:
        raise ManifestError("registry identity must be exact lowercase 64-hex, not branch/PR metadata")
    if type(access_policy_sha) is not str or len(access_policy_sha) != 64 or set(access_policy_sha) - _HEX:
        raise ManifestError("access-policy identity must be exact lowercase 64-hex")
    registry = resolver(registry_sha)
    policy = resolver(access_policy_sha)
    if registry is None or policy is None:
        raise ManifestError("manifest dependency unavailable")
    verify_manifest_dependency(registry_sha, registry, expected_role="REGISTRY")
    verify_manifest_dependency(access_policy_sha, policy, expected_role="ACCESS_POLICY")
    return TDExecutionManifest("TD_EXECUTION_MANIFEST_V1", registry_sha, access_policy_sha)
