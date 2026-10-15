"""Unified Task 2 execution manifest and population-access authority.

Task 2 is non-authorizing outside its exact manifest/access scope. Current-TD
population authority is never granted by digest strings alone: consumers must
re-resolve the frozen reader-split raw bytes and recompute donors and folds.
Observed access for authoritative policies must come from a harness-owned,
HMAC-attested session registry. Redundant manifest sub-policies are canonical
derivatives of the access policy, and the manifest explicitly binds the missing
normalization/TargetPortfolio/per-unit execution identity surface.
"""
from __future__ import annotations

import csv
import hashlib
import hmac
import io
from collections import Counter
from dataclasses import dataclass
from typing import Callable

from scripts.v5.td_unified.canonical_v1 import canonical_sha256 as canonical_object_sha256

FROZEN_READER_SPLIT_SHA256 = "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511"
# Historical custody annotation. It is intentionally NOT a population-authority
# predicate until Task 2 is given actual registry bytes under a verified binding.
FROZEN_POPULATION_REGISTRY_SHA256 = "50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d"
CURRENT_TD_ASSIGNMENT_LAW = "DONOR_SHA256_ORDER_ROUND_ROBIN_V1"
_FIXTURE_ASSIGNMENT_LAW = "SOURCE_STRATIFIED_HASH_ORDER_ROUND_ROBIN_V1"
_EXPECTED_READER_COUNTS = {"reader_fit": 104, "reader_validation": 22, "reader_oracle": 23}

class ManifestError(ValueError):
    pass

_ALLOWED_PARTITIONS = {"reader_fit", "reader_validation", "reader_oracle"}
_ALLOWED_ACCESS_CLASSES = {
    "METADATA", "PARTITION_IDENTITY", "SUPPORT_ONLY_SUMMARY",
    "BIOLOGICAL_VALUES", "CALIBRATION_STATISTICS",
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
    "normalization_library_contract_sha": "NORMALIZATION_LIBRARY_CONTRACT",
    "target_portfolio_code_identity_sha": "TARGET_PORTFOLIO_CODE_IDENTITY",
    "target_portfolio_policy_sha": "TARGET_PORTFOLIO_POLICY",
    "unit_execution_identity_table_sha": "UNIT_EXECUTION_IDENTITY_TABLE",
}
_MANIFEST_REQUIRED = {"schema", "controller_code_sha", *_MANIFEST_ROLE_BY_FIELD}


def _is_lower_hex(value: object, length: int) -> bool:
    return type(value) is str and len(value) == length and not (set(value) - _HEX)


def verify_raw_file_sha256(claimed_sha: str, raw_bytes: bytes) -> None:
    if not _is_lower_hex(claimed_sha, 64):
        raise ManifestError("raw SHA-256 claim must be lowercase 64-hex")
    if type(raw_bytes) is not bytes:
        raise ManifestError("raw-file identity requires actual bytes")
    if hashlib.sha256(raw_bytes).hexdigest() != claimed_sha:
        raise ManifestError("raw-file SHA-256 digest mismatch")


def verify_git_blob_sha1(claimed_sha: str, raw_bytes: bytes) -> None:
    if not _is_lower_hex(claimed_sha, 40):
        raise ManifestError("Git blob identity must be lowercase 40-hex")
    if type(raw_bytes) is not bytes:
        raise ManifestError("Git blob identity requires actual bytes")
    prefix = f"blob {len(raw_bytes)}\0".encode("ascii")
    if hashlib.sha1(prefix + raw_bytes).hexdigest() != claimed_sha:
        raise ManifestError("Git blob identity mismatch")


@dataclass(frozen=True)
class CrossFitFold:
    fold_index: int
    train_donors: tuple[str, ...]
    held_out_donors: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {"fold_index": self.fold_index, "train_donors": list(self.train_donors), "held_out_donors": list(self.held_out_donors)}


@dataclass(frozen=True)
class PopulationAccessPolicy:
    object_role: str
    policy_schema: str
    population_authority: str
    reader_split_raw_sha256: str | None
    population_registry_sha256: str | None
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
            "population_authority": self.population_authority,
            "reader_split_raw_sha256": self.reader_split_raw_sha256,
            "population_registry_sha256": self.population_registry_sha256,
            "assignment_basis": self.assignment_basis,
            "assignment_basis_sha": self.assignment_basis_sha,
            "fold_count": self.fold_count,
            "crossfit_folds": [f.to_payload() for f in self.crossfit_folds],
            "allowed_outcome_partitions": list(self.allowed_outcome_partitions),
            "protected_partitions": list(self.protected_partitions),
        }

    def canonical_sha256(self) -> str:
        _validate_population_access_policy_structure(self.to_payload())
        return canonical_object_sha256(self.to_payload())


@dataclass(frozen=True)
class ObservedAccess:
    partition: str
    access_class: str
    fold_index: int | None
    phase: str
    donor_ids: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "partition": self.partition, "access_class": self.access_class,
            "fold_index": self.fold_index, "phase": self.phase,
            "donor_ids": list(self.donor_ids),
        }


@dataclass(frozen=True)
class ProducerAccessReceipt:
    producer_id: str
    access_policy_sha: str
    access_ledger_sha: str
    observed_access: tuple[ObservedAccess, ...]
    numeric_result_digest: str | None = None
    receipt_schema: str = "PRODUCER_ACCESS_RECEIPT_V1"

    def to_payload(self) -> dict[str, object]:
        out: dict[str, object] = {
            "receipt_schema": self.receipt_schema,
            "producer_id": self.producer_id,
            "access_policy_sha": self.access_policy_sha,
            "access_ledger_sha": self.access_ledger_sha,
            "observed_access": [e.to_payload() for e in self.observed_access],
        }
        if self.numeric_result_digest is not None:
            out["numeric_result_digest"] = self.numeric_result_digest
        return out


@dataclass(frozen=True)
class TDExecutionManifest:
    schema: str
    dependencies: tuple[tuple[str, str], ...]

    def to_payload(self) -> dict[str, object]:
        return {"schema": self.schema, **dict(self.dependencies)}


def _donor_sort_key(donor: str) -> tuple[str, str]:
    return hashlib.sha256(donor.encode()).hexdigest(), donor


def _validate_fit_donors(fit_donors: list[str]) -> None:
    if type(fit_donors) is not list or len(fit_donors) < 5:
        raise ManifestError("fit_donors must contain at least five donors")
    if len(fit_donors) != len(set(fit_donors)):
        raise ManifestError("duplicate fit donor identity")
    if any(type(d) is not str or not d for d in fit_donors):
        raise ManifestError("donor identity must be a non-empty string")


def _build_folds(fit_donors: list[str], *, donor_source: dict[str, str] | None) -> tuple[CrossFitFold, ...]:
    _validate_fit_donors(fit_donors)
    held = [[] for _ in range(5)]
    if donor_source is None:
        for i, donor in enumerate(sorted(fit_donors, key=_donor_sort_key)):
            held[i % 5].append(donor)
    else:
        if type(donor_source) is not dict or set(donor_source) != set(fit_donors):
            raise ManifestError("donor_source must bind exactly the fit donors")
        by_source: dict[str, list[str]] = {}
        for d in fit_donors:
            s = donor_source[d]
            if type(s) is not str or not s:
                raise ManifestError("source identity must be non-empty")
            by_source.setdefault(s, []).append(d)
        offset = 0
        for source in sorted(by_source):
            donors = sorted(by_source[source], key=_donor_sort_key)
            for i, donor in enumerate(donors):
                held[(offset + i) % 5].append(donor)
            offset = (offset + len(donors)) % 5
    all_donors = tuple(sorted(fit_donors, key=_donor_sort_key))
    folds = []
    for k in range(5):
        h = tuple(sorted(held[k], key=_donor_sort_key))
        if not h:
            raise ManifestError("every cross-fit fold must contain at least one held-out donor")
        hs = set(h)
        t = tuple(d for d in all_donors if d not in hs)
        folds.append(CrossFitFold(k, t, h))
    return tuple(folds)


def build_current_td_access_policy(*, fit_donors: list[str], donor_source: dict[str, str]) -> PopulationAccessPolicy:
    _validate_fit_donors(fit_donors)
    if type(donor_source) is not dict or set(donor_source) != set(fit_donors):
        raise ManifestError("donor_source must bind exactly the fit donors")
    basis = {
        "fit_donors": sorted(fit_donors),
        "donor_source": {d: donor_source[d] for d in sorted(fit_donors)},
        "fold_count": 5,
        "assignment_law": _FIXTURE_ASSIGNMENT_LAW,
    }
    p = PopulationAccessPolicy(
        "ACCESS_POLICY", "POPULATION_ACCESS_POLICY_V1", "FIXTURE_UNBOUND", None, None,
        basis, canonical_object_sha256(basis), 5,
        _build_folds(fit_donors, donor_source=donor_source),
        ("reader_fit",), ("reader_validation", "reader_oracle"),
    )
    _validate_population_access_policy_structure(p.to_payload())
    return p


def _parse_frozen_reader_split(reader_split_raw: bytes) -> tuple[list[str], Counter[str]]:
    verify_raw_file_sha256(FROZEN_READER_SPLIT_SHA256, reader_split_raw)
    try:
        text = reader_split_raw.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if reader.fieldnames != ["donor_id", "reader_partition"]:
            raise ManifestError("reader split schema must be exactly donor_id,reader_partition")
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ManifestError("reader split raw bytes are not frozen UTF-8 CSV") from exc
    if len(rows) != 149:
        raise ManifestError("reader split row count must be exactly 149")
    donors = [r.get("donor_id", "") for r in rows]
    if any(not d for d in donors) or len(donors) != len(set(donors)):
        raise ManifestError("reader split donor identities must be non-empty and unique")
    counts = Counter(r.get("reader_partition", "") for r in rows)
    if dict(counts) != _EXPECTED_READER_COUNTS:
        raise ManifestError("reader split partition counts do not match frozen 104/22/23 custody")
    fit = sorted(r["donor_id"] for r in rows if r["reader_partition"] == "reader_fit")
    return fit, counts


def build_current_td_access_policy_from_reader_split(*, reader_split_raw: bytes) -> PopulationAccessPolicy:
    if type(reader_split_raw) is not bytes:
        raise ManifestError("reader split authority requires actual raw bytes")
    fit, _ = _parse_frozen_reader_split(reader_split_raw)
    basis = {
        "fit_donors": fit,
        "fold_count": 5,
        "assignment_law": CURRENT_TD_ASSIGNMENT_LAW,
        "reader_split_raw_sha256": FROZEN_READER_SPLIT_SHA256,
        "population_registry_sha256": FROZEN_POPULATION_REGISTRY_SHA256,
    }
    p = PopulationAccessPolicy(
        "ACCESS_POLICY", "POPULATION_ACCESS_POLICY_V1", "AUTHENTICATED_READER_SPLIT",
        FROZEN_READER_SPLIT_SHA256, FROZEN_POPULATION_REGISTRY_SHA256,
        basis, canonical_object_sha256(basis), 5, _build_folds(fit, donor_source=None),
        ("reader_fit",), ("reader_validation", "reader_oracle"),
    )
    resolver = {FROZEN_READER_SPLIT_SHA256: reader_split_raw}.get
    validate_population_access_policy_payload(p.to_payload(), raw_resolver=resolver)
    require_current_td_population_authority(p, raw_resolver=resolver)
    return p


def _validate_population_access_policy_structure(payload: dict[str, object]) -> None:
    if type(payload) is not dict:
        raise ManifestError("population access policy must be a dict")
    required = {
        "object_role", "policy_schema", "population_authority", "reader_split_raw_sha256",
        "population_registry_sha256", "assignment_basis", "assignment_basis_sha", "fold_count",
        "crossfit_folds", "allowed_outcome_partitions", "protected_partitions",
    }
    if set(payload) != required:
        raise ManifestError("population access policy fields do not match POPULATION_ACCESS_POLICY_V1")
    if payload["object_role"] != "ACCESS_POLICY" or payload["policy_schema"] != "POPULATION_ACCESS_POLICY_V1":
        raise ManifestError("population access policy role/schema mismatch")
    if payload["fold_count"] != 5 or payload["allowed_outcome_partitions"] != ["reader_fit"]:
        raise ManifestError("population access policy fold/outcome law mismatch")
    if payload["protected_partitions"] != ["reader_validation", "reader_oracle"]:
        raise ManifestError("protected partition set mismatch")
    basis = payload["assignment_basis"]
    if type(basis) is not dict:
        raise ManifestError("assignment basis must be a dict")
    authority = payload["population_authority"]
    if authority == "FIXTURE_UNBOUND":
        expected = {"fit_donors", "donor_source", "fold_count", "assignment_law"}
        if set(basis) != expected or basis.get("assignment_law") != _FIXTURE_ASSIGNMENT_LAW:
            raise ManifestError("fixture assignment basis invalid")
        if payload["reader_split_raw_sha256"] is not None or payload["population_registry_sha256"] is not None:
            raise ManifestError("fixture policy cannot claim frozen identities")
        donor_source = basis.get("donor_source")
    elif authority == "AUTHENTICATED_READER_SPLIT":
        expected = {"fit_donors", "fold_count", "assignment_law", "reader_split_raw_sha256", "population_registry_sha256"}
        if set(basis) != expected or basis.get("assignment_law") != CURRENT_TD_ASSIGNMENT_LAW:
            raise ManifestError("authenticated assignment basis invalid")
        if not _is_lower_hex(payload["reader_split_raw_sha256"], 64):
            raise ManifestError("authenticated reader split identity invalid")
        if not _is_lower_hex(payload["population_registry_sha256"], 64):
            raise ManifestError("population registry custody annotation must be 64-hex")
        donor_source = None
    else:
        raise ManifestError("unknown population authority class")
    donors = basis.get("fit_donors")
    if type(donors) is not list or any(type(d) is not str or not d for d in donors):
        raise ManifestError("assignment basis fit donors invalid")
    if donors != sorted(donors) or len(donors) != len(set(donors)):
        raise ManifestError("assignment basis fit donors must be unique and sorted")
    if basis.get("fold_count") != 5:
        raise ManifestError("assignment basis fold_count must be 5")
    if authority == "FIXTURE_UNBOUND":
        if type(donor_source) is not dict or set(donor_source) != set(donors):
            raise ManifestError("fixture donor_source must bind exactly fit donors")
    else:
        if len(donors) != 104:
            raise ManifestError("authenticated policy must bind exactly 104 fit donors")
        if basis.get("reader_split_raw_sha256") != payload["reader_split_raw_sha256"]:
            raise ManifestError("assignment basis reader split mismatch")
        if basis.get("population_registry_sha256") != payload["population_registry_sha256"]:
            raise ManifestError("assignment basis population registry annotation mismatch")
    if not _is_lower_hex(payload["assignment_basis_sha"], 64) or canonical_object_sha256(basis) != payload["assignment_basis_sha"]:
        raise ManifestError("assignment basis digest mismatch")
    folds = payload["crossfit_folds"]
    if type(folds) is not list or len(folds) != 5:
        raise ManifestError("exactly five cross-fit folds required")
    fitset = set(donors); seen_idx = set(); seen_held: list[str] = []
    for fold in folds:
        if type(fold) is not dict or set(fold) != {"fold_index", "train_donors", "held_out_donors"}:
            raise ManifestError("cross-fit fold fields invalid")
        idx = fold["fold_index"]; train = fold["train_donors"]; held = fold["held_out_donors"]
        if type(idx) is not int or idx not in range(5) or idx in seen_idx:
            raise ManifestError("cross-fit fold index invalid")
        seen_idx.add(idx)
        if type(train) is not list or type(held) is not list or not held:
            raise ManifestError("cross-fit donor lists invalid")
        if len(train) != len(set(train)) or len(held) != len(set(held)) or set(train) & set(held):
            raise ManifestError("cross-fit donor leakage or duplication")
        if set(train) | set(held) != fitset:
            raise ManifestError("every fold must partition the complete fit set")
        seen_held.extend(held)
    if sorted(seen_held) != sorted(donors) or len(seen_held) != len(set(seen_held)):
        raise ManifestError("every fit donor must be held out exactly once")


def _resolve_reader_split(raw_resolver: Callable[[str], object | None] | None, claimed_sha: str) -> bytes:
    if raw_resolver is None:
        raise ManifestError("current-TD population authority requires raw reader-split resolver")
    raw = raw_resolver(claimed_sha)
    if type(raw) is not bytes:
        raise ManifestError("current-TD reader split raw bytes unavailable")
    verify_raw_file_sha256(claimed_sha, raw)
    return raw


def _enforce_authoritative_population_payload(payload: dict[str, object], raw_resolver: Callable[[str], object | None]) -> None:
    claimed = payload["reader_split_raw_sha256"]
    if claimed != FROZEN_READER_SPLIT_SHA256:
        raise ManifestError("current-TD reader split identity mismatch")
    raw = _resolve_reader_split(raw_resolver, claimed)
    fit, _ = _parse_frozen_reader_split(raw)
    basis = payload["assignment_basis"]
    if basis["fit_donors"] != fit:
        raise ManifestError("current-TD donor set does not match frozen reader split bytes")
    expected_folds = [f.to_payload() for f in _build_folds(fit, donor_source=None)]
    if payload["crossfit_folds"] != expected_folds:
        raise ManifestError("current-TD folds do not match DONOR_SHA256_ORDER_ROUND_ROBIN_V1")
    if basis["assignment_law"] != CURRENT_TD_ASSIGNMENT_LAW:
        raise ManifestError("current-TD assignment law mismatch")


def validate_population_access_policy_payload(payload: dict[str, object], *, raw_resolver: Callable[[str], object | None] | None = None) -> None:
    _validate_population_access_policy_structure(payload)
    if payload["population_authority"] == "AUTHENTICATED_READER_SPLIT":
        _enforce_authoritative_population_payload(payload, raw_resolver)


def _policy_from_payload(payload: dict[str, object]) -> PopulationAccessPolicy:
    return PopulationAccessPolicy(
        payload["object_role"], payload["policy_schema"], payload["population_authority"],
        payload["reader_split_raw_sha256"], payload["population_registry_sha256"], payload["assignment_basis"],
        payload["assignment_basis_sha"], payload["fold_count"],
        tuple(CrossFitFold(f["fold_index"], tuple(f["train_donors"]), tuple(f["held_out_donors"])) for f in payload["crossfit_folds"]),
        tuple(payload["allowed_outcome_partitions"]), tuple(payload["protected_partitions"]),
    )


def require_current_td_population_authority(policy: PopulationAccessPolicy, *, raw_resolver: Callable[[str], object | None] | None = None) -> None:
    if not isinstance(policy, PopulationAccessPolicy):
        raise ManifestError("current-TD authority requires PopulationAccessPolicy")
    if policy.population_authority != "AUTHENTICATED_READER_SPLIT":
        raise ManifestError("current-TD authoritative population requires authenticated reader split")
    validate_population_access_policy_payload(policy.to_payload(), raw_resolver=raw_resolver)


def validate_manifest_population_binding(*, access_policy: dict[str, object], population_split_registry: dict[str, object], raw_resolver: Callable[[str], object | None] | None = None) -> None:
    validate_population_access_policy_payload(access_policy, raw_resolver=raw_resolver)
    if access_policy["population_authority"] != "AUTHENTICATED_READER_SPLIT":
        raise ManifestError("manifest population authority requires authenticated reader split")
    if type(population_split_registry) is not dict or population_split_registry.get("object_role") != "POPULATION_SPLIT_REGISTRY":
        raise ManifestError("population split registry role mismatch")
    if population_split_registry.get("reader_split_raw_sha256") != access_policy["reader_split_raw_sha256"]:
        raise ManifestError("population split registry reader split mismatch")
    # Registry digest is custody annotation only; require consistency, not authority.
    if population_split_registry.get("population_registry_sha256") != access_policy["population_registry_sha256"]:
        raise ManifestError("population registry custody annotation mismatch")


def _validate_observed_event(policy: PopulationAccessPolicy, event: ObservedAccess) -> None:
    if not isinstance(event, ObservedAccess):
        raise ManifestError("observed access must use structured events")
    if event.partition not in _ALLOWED_PARTITIONS or event.access_class not in _ALLOWED_ACCESS_CLASSES:
        raise ManifestError("unknown or forbidden partition/access class")
    if type(event.donor_ids) is not tuple or len(event.donor_ids) != len(set(event.donor_ids)):
        raise ManifestError("observed donor_ids must be a unique tuple")
    if event.partition != "reader_fit":
        if event.access_class not in _PROTECTED_ALLOWED:
            raise ManifestError(f"forbidden protected {event.partition} access class")
        if event.fold_index is not None or event.phase != "CUSTODY" or event.donor_ids:
            raise ManifestError("protected partition identity access must be custody-only and donor-free")
        return
    if type(event.fold_index) is not int or event.fold_index not in range(policy.fold_count):
        raise ManifestError("reader_fit access must bind a valid fold")
    if event.phase not in _FIT_PHASES or not event.donor_ids:
        raise ManifestError("reader_fit access must bind TRAIN/EVAL and donor ids")
    fold = policy.crossfit_folds[event.fold_index]
    permitted = set(fold.train_donors if event.phase == "TRAIN" else fold.held_out_donors)
    if not set(event.donor_ids) <= permitted:
        raise ManifestError("held-out/train donor leakage across cross-fit phase")


def _fixture_ledger_payload(*, producer_id: str, access_policy_sha: str, events: tuple[ObservedAccess, ...]) -> dict[str, object]:
    return {"object_role": "OBSERVED_ACCESS_LEDGER", "ledger_schema": "OBSERVED_ACCESS_LEDGER_V1", "producer_id": producer_id, "access_policy_sha": access_policy_sha, "observed_access": [e.to_payload() for e in events]}


class PopulationAccessSession:
    def __init__(self, *, policy: PopulationAccessPolicy, producer_id: str, reader_fit_values: dict[str, object], _harness_registry=None, _session_id: str | None = None) -> None:
        if not isinstance(policy, PopulationAccessPolicy):
            raise ManifestError("session policy must be PopulationAccessPolicy")
        _validate_population_access_policy_structure(policy.to_payload())
        if type(producer_id) is not str or not producer_id:
            raise ManifestError("producer_id is required")
        if type(reader_fit_values) is not dict or set(reader_fit_values) != set(policy.assignment_basis["fit_donors"]):
            raise ManifestError("reader_fit_values must bind exactly policy fit donors")
        self._policy = policy; self._producer_id = producer_id; self._reader_fit_values = dict(reader_fit_values)
        self._events: list[ObservedAccess] = []; self._invalid_reason = None; self._finalized = False
        self._harness_registry = _harness_registry; self._session_id = _session_id

    def _ensure_open(self) -> None:
        if self._finalized:
            raise ManifestError("access session already finalized")
        if self._invalid_reason is not None:
            raise ManifestError(f"access session invalidated by forbidden access: {self._invalid_reason}")

    def read_fit(self, fold_index: int, phase: str, donor_ids: tuple[str, ...], access_class: str) -> tuple[object, ...]:
        self._ensure_open(); event = ObservedAccess("reader_fit", access_class, fold_index, phase, donor_ids)
        try:
            _validate_observed_event(self._policy, event)
            values = tuple(self._reader_fit_values[d] for d in donor_ids)
        except (ManifestError, KeyError) as exc:
            self._invalid_reason = str(exc)
            if isinstance(exc, ManifestError): raise
            raise ManifestError("requested donor is not available in reader_fit gateway") from exc
        self._events.append(event); return values

    def observe_protected_partition_identity(self, partition: str) -> None:
        self._ensure_open(); event = ObservedAccess(partition, "PARTITION_IDENTITY", None, "CUSTODY", ())
        try: _validate_observed_event(self._policy, event)
        except ManifestError as exc: self._invalid_reason = str(exc); raise
        self._events.append(event)

    def finalize(self, numeric_result_digest: str | None = None) -> tuple[ProducerAccessReceipt, dict[str, object]]:
        self._ensure_open()
        if not self._events: raise ManifestError("access session cannot finalize without observed access")
        if numeric_result_digest is not None and not _is_lower_hex(numeric_result_digest, 64):
            raise ManifestError("numeric result digest must be lowercase 64-hex")
        events = tuple(self._events); policy_sha = self._policy.canonical_sha256()
        if self._harness_registry is not None:
            receipt, ledger = self._harness_registry._finalize_session(self._session_id, self._producer_id, policy_sha, events, numeric_result_digest)
        else:
            ledger = _fixture_ledger_payload(producer_id=self._producer_id, access_policy_sha=policy_sha, events=events)
            receipt = ProducerAccessReceipt(self._producer_id, policy_sha, canonical_object_sha256(ledger), events, numeric_result_digest)
        self._finalized = True
        return receipt, ledger


class HarnessAccessRegistry:
    """Harness-owned issuance and immutable attested ledger store."""
    def __init__(self, *, attestation_key: bytes) -> None:
        if type(attestation_key) is not bytes or len(attestation_key) < 16:
            raise ManifestError("harness attestation key must be at least 16 bytes")
        self.__key = attestation_key
        self.__issued: dict[str, tuple[str, str]] = {}
        self.__ledgers: dict[str, dict[str, object]] = {}
        self.__counter = 0

    def issue_session(self, *, policy: PopulationAccessPolicy, producer_id: str, reader_fit_values: dict[str, object]) -> PopulationAccessSession:
        self.__counter += 1
        seed = f"{self.__counter}\0{producer_id}\0{policy.canonical_sha256()}".encode()
        session_id = hmac.new(self.__key, seed, hashlib.sha256).hexdigest()
        self.__issued[session_id] = (producer_id, policy.canonical_sha256())
        return PopulationAccessSession(policy=policy, producer_id=producer_id, reader_fit_values=reader_fit_values, _harness_registry=self, _session_id=session_id)

    def _finalize_session(self, session_id: str | None, producer_id: str, policy_sha: str, events: tuple[ObservedAccess, ...], numeric_result_digest: str | None):
        if type(session_id) is not str or self.__issued.get(session_id) != (producer_id, policy_sha):
            raise ManifestError("session was not issued by this harness registry")
        unsigned = {
            "object_role": "OBSERVED_ACCESS_LEDGER",
            "ledger_schema": "OBSERVED_ACCESS_LEDGER_V2_HARNESS_ATTESTED",
            "session_id": session_id,
            "producer_id": producer_id,
            "access_policy_sha": policy_sha,
            "observed_access": [e.to_payload() for e in events],
        }
        attestation = hmac.new(self.__key, canonical_object_sha256(unsigned).encode(), hashlib.sha256).hexdigest()
        ledger = {**unsigned, "harness_attestation": attestation}
        ledger_sha = canonical_object_sha256(ledger)
        self.__ledgers[ledger_sha] = ledger
        del self.__issued[session_id]
        return ProducerAccessReceipt(producer_id, policy_sha, ledger_sha, events, numeric_result_digest), ledger

    def resolve_attested_ledger(self, ledger_sha: str) -> dict[str, object] | None:
        ledger = self.__ledgers.get(ledger_sha)
        if ledger is None: return None
        if canonical_object_sha256(ledger) != ledger_sha: return None
        unsigned = dict(ledger); att = unsigned.pop("harness_attestation", None)
        if type(att) is not str: return None
        expected = hmac.new(self.__key, canonical_object_sha256(unsigned).encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(att, expected): return None
        return dict(ledger)


def validate_producer_access(policy: PopulationAccessPolicy, receipt: ProducerAccessReceipt, *, ledger_resolver: Callable[[str], object | None] | None = None, session_registry: HarnessAccessRegistry | None = None) -> None:
    if not isinstance(policy, PopulationAccessPolicy) or not isinstance(receipt, ProducerAccessReceipt):
        raise ManifestError("policy/receipt type mismatch")
    _validate_population_access_policy_structure(policy.to_payload())
    if receipt.receipt_schema != "PRODUCER_ACCESS_RECEIPT_V1" or not receipt.observed_access:
        raise ManifestError("invalid producer access receipt")
    if receipt.access_policy_sha != policy.canonical_sha256():
        raise ManifestError("access policy identity mismatch")
    if not _is_lower_hex(receipt.access_ledger_sha, 64):
        raise ManifestError("observed access ledger identity invalid")
    if policy.population_authority == "AUTHENTICATED_READER_SPLIT":
        if not isinstance(session_registry, HarnessAccessRegistry):
            raise ManifestError("authoritative access requires harness-issued session registry")
        ledger = session_registry.resolve_attested_ledger(receipt.access_ledger_sha)
        expected_schema = "OBSERVED_ACCESS_LEDGER_V2_HARNESS_ATTESTED"
        required = {"object_role", "ledger_schema", "session_id", "producer_id", "access_policy_sha", "observed_access", "harness_attestation"}
    else:
        if ledger_resolver is None:
            raise ManifestError("fixture observed access ledger resolver required")
        ledger = ledger_resolver(receipt.access_ledger_sha)
        expected_schema = "OBSERVED_ACCESS_LEDGER_V1"
        required = {"object_role", "ledger_schema", "producer_id", "access_policy_sha", "observed_access"}
    if type(ledger) is not dict or set(ledger) != required:
        raise ManifestError("observed access ledger unavailable or fields invalid")
    if ledger["object_role"] != "OBSERVED_ACCESS_LEDGER" or ledger["ledger_schema"] != expected_schema:
        raise ManifestError("observed access ledger schema mismatch")
    if ledger["producer_id"] != receipt.producer_id or ledger["access_policy_sha"] != receipt.access_policy_sha:
        raise ManifestError("observed access ledger producer/policy mismatch")
    if canonical_object_sha256(ledger) != receipt.access_ledger_sha:
        raise ManifestError("observed access ledger digest mismatch")
    if ledger["observed_access"] != [e.to_payload() for e in receipt.observed_access]:
        raise ManifestError("observed access ledger events mismatch")
    for event in receipt.observed_access: _validate_observed_event(policy, event)


def derive_crossfit_policy_payload(policy: PopulationAccessPolicy) -> dict[str, object]:
    return {
        "object_role": "CROSSFIT_POLICY", "policy_schema": "CROSSFIT_POLICY_V1",
        "assignment_law": policy.assignment_basis["assignment_law"], "fold_count": policy.fold_count,
        "crossfit_folds_sha": canonical_object_sha256([f.to_payload() for f in policy.crossfit_folds]),
    }


def derive_protected_partition_policy_payload(policy: PopulationAccessPolicy) -> dict[str, object]:
    return {
        "object_role": "PROTECTED_PARTITION_POLICY", "policy_schema": "PROTECTED_PARTITION_POLICY_V1",
        "reader_validation_access_classes": ["PARTITION_IDENTITY"],
        "reader_oracle_access_classes": ["PARTITION_IDENTITY"],
    }


def derive_reader_partition_policy_payload(policy: PopulationAccessPolicy, partition: str) -> dict[str, object]:
    role = {"reader_fit": "READER_FIT_POLICY", "reader_validation": "READER_VALIDATION_POLICY", "reader_oracle": "READER_ORACLE_POLICY"}.get(partition)
    if role is None: raise ManifestError("unknown reader partition policy")
    if partition == "reader_fit":
        return {"object_role": role, "policy_schema": "READER_PARTITION_POLICY_V1", "partition": partition, "access_classes": sorted(_ALLOWED_ACCESS_CLASSES), "use": "CROSSFIT_ONLY"}
    return {"object_role": role, "policy_schema": "READER_PARTITION_POLICY_V1", "partition": partition, "access_classes": ["PARTITION_IDENTITY"], "use": "CUSTODY_ONLY"}


def validate_manifest_subpolicy_consistency(*, access_policy: dict[str, object], crossfit_policy: dict[str, object], protected_partition_policy: dict[str, object], reader_fit_policy: dict[str, object], reader_validation_policy: dict[str, object], reader_oracle_policy: dict[str, object], raw_resolver: Callable[[str], object | None] | None = None) -> None:
    validate_population_access_policy_payload(access_policy, raw_resolver=raw_resolver)
    p = _policy_from_payload(access_policy)
    expected = {
        "crossfit": derive_crossfit_policy_payload(p),
        "protected": derive_protected_partition_policy_payload(p),
        "fit": derive_reader_partition_policy_payload(p, "reader_fit"),
        "validation": derive_reader_partition_policy_payload(p, "reader_validation"),
        "oracle": derive_reader_partition_policy_payload(p, "reader_oracle"),
    }
    actual = {"crossfit": crossfit_policy, "protected": protected_partition_policy, "fit": reader_fit_policy, "validation": reader_validation_policy, "oracle": reader_oracle_policy}
    for name in expected:
        if actual[name] != expected[name]:
            raise ManifestError(f"manifest sub-policy inconsistent with access policy: {name}")


def verify_manifest_dependency(claimed_sha: str, resolved: object, *, expected_role: str) -> None:
    if not _is_lower_hex(claimed_sha, 64) or type(resolved) is not dict:
        raise ManifestError("dependency identity/object invalid")
    if resolved.get("object_role") != expected_role:
        raise ManifestError(f"dependency role mismatch for {expected_role}")
    try: actual = canonical_object_sha256(resolved)
    except Exception as exc: raise ManifestError("dependency cannot be canonically verified") from exc
    if actual != claimed_sha: raise ManifestError("dependency digest identity mismatch")


def _resolve_semantic_identity(sha: object, resolver, expected_role: str) -> dict[str, object]:
    if not _is_lower_hex(sha, 64): raise ManifestError("nested semantic identity must be 64-hex")
    obj = resolver(sha)
    verify_manifest_dependency(sha, obj, expected_role=expected_role)
    return obj


def validate_normalization_library_contract(obj: dict[str, object], resolver) -> None:
    if set(obj) != {"object_role", "contract_schema", "normalization_contract_sha", "library_contract_sha"} or obj.get("contract_schema") != "NORMALIZATION_LIBRARY_CONTRACT_IDENTITY_V1":
        raise ManifestError("normalization/library contract identity object invalid")
    _resolve_semantic_identity(obj["normalization_contract_sha"], resolver, "NORMALIZATION_CONTRACT")
    _resolve_semantic_identity(obj["library_contract_sha"], resolver, "LIBRARY_CONTRACT")


def validate_target_portfolio_code_identity(obj: dict[str, object], resolver) -> None:
    if set(obj) != {"object_role", "identity_schema", "git_blob_sha1"} or obj.get("identity_schema") != "GIT_BLOB_IDENTITY_V1":
        raise ManifestError("TargetPortfolio code identity object invalid")
    sha = obj["git_blob_sha1"]
    raw = resolver(sha)
    if raw is None: raise ManifestError("TargetPortfolio code bytes unavailable")
    verify_git_blob_sha1(sha, raw)


def validate_target_portfolio_policy(obj: dict[str, object], resolver) -> None:
    if set(obj) != {"object_role", "policy_schema", "policy_contract_sha"} or obj.get("policy_schema") != "TARGET_PORTFOLIO_POLICY_IDENTITY_V1":
        raise ManifestError("TargetPortfolio policy identity object invalid")
    _resolve_semantic_identity(obj["policy_contract_sha"], resolver, "TARGET_PORTFOLIO_POLICY_CONTRACT")


def validate_unit_execution_identity_table(obj: dict[str, object], resolver: Callable[[str], object | None] | None = None) -> None:
    if set(obj) != {"object_role", "table_schema", "units"} or obj.get("table_schema") != "UNIT_EXECUTION_IDENTITY_TABLE_V1":
        raise ManifestError("unit execution identity table invalid")
    units = obj.get("units")
    if type(units) is not list or not units: raise ManifestError("unit execution identity table must be non-empty")
    expected = {"unit_id", "producer_code_sha1", "executor_code_sha1", "producer_policy_sha", "executor_policy_sha", "schema_sha", "metric_sha", "reference_producer_sha", "falsifier_sha"}
    ids = []
    for row in units:
        if type(row) is not dict or set(row) != expected: raise ManifestError("unit execution identity row invalid")
        uid = row["unit_id"]
        if type(uid) is not str or not uid: raise ManifestError("unit_id invalid")
        ids.append(uid)
        for field in ("producer_code_sha1", "executor_code_sha1"):
            if not _is_lower_hex(row[field], 40): raise ManifestError("unit code identity invalid")
            if resolver is not None:
                raw = resolver(row[field]);
                if raw is None: raise ManifestError("unit code bytes unavailable")
                verify_git_blob_sha1(row[field], raw)
        roles = {
            "producer_policy_sha": "PRODUCER_POLICY", "executor_policy_sha": "EXECUTOR_POLICY",
            "schema_sha": "UNIT_SCHEMA", "metric_sha": "METRIC_DEFINITION",
            "reference_producer_sha": "REFERENCE_PRODUCER", "falsifier_sha": "FALSIFIER_CONTROL",
        }
        for field, role in roles.items():
            if not _is_lower_hex(row[field], 64): raise ManifestError("unit semantic identity invalid")
            if resolver is not None: _resolve_semantic_identity(row[field], resolver, role)
    if len(ids) != len(set(ids)): raise ManifestError("duplicate unit_id in execution identity table")


def validate_manifest(payload: dict[str, object], resolver: Callable[[str], object | None], *, raw_resolver: Callable[[str], object | None] | None = None) -> TDExecutionManifest:
    if type(payload) is not dict or set(payload) != _MANIFEST_REQUIRED or payload.get("schema") != "TD_EXECUTION_MANIFEST_V1":
        raise ManifestError("manifest fields/schema do not match TD_EXECUTION_MANIFEST_V1")
    code_sha = payload["controller_code_sha"]
    if not _is_lower_hex(code_sha, 40): raise ManifestError("controller code identity must be exact 40-hex")
    code = resolver(code_sha)
    if code is None: raise ManifestError("controller code dependency unavailable")
    verify_git_blob_sha1(code_sha, code)
    semantic_shas = []; deps = [("controller_code_sha", code_sha)]; resolved: dict[str, dict[str, object]] = {}
    for field, role in _MANIFEST_ROLE_BY_FIELD.items():
        sha = payload[field]
        if not _is_lower_hex(sha, 64): raise ManifestError(f"{field} must be exact 64-hex")
        obj = resolver(sha)
        if obj is None: raise ManifestError(f"manifest dependency unavailable: {field}")
        verify_manifest_dependency(sha, obj, expected_role=role)
        semantic_shas.append(sha); resolved[field] = obj; deps.append((field, sha))
    if len(semantic_shas) != len(set(semantic_shas)):
        raise ManifestError("one semantic identity cannot fill multiple manifest roles")
    validate_manifest_population_binding(access_policy=resolved["access_policy_sha"], population_split_registry=resolved["population_split_registry_sha"], raw_resolver=raw_resolver)
    validate_manifest_subpolicy_consistency(
        access_policy=resolved["access_policy_sha"],
        crossfit_policy=resolved["crossfit_policy_sha"], protected_partition_policy=resolved["protected_partition_policy_sha"],
        reader_fit_policy=resolved["reader_fit_policy_sha"], reader_validation_policy=resolved["reader_validation_policy_sha"], reader_oracle_policy=resolved["reader_oracle_policy_sha"],
        raw_resolver=raw_resolver,
    )
    validate_normalization_library_contract(resolved["normalization_library_contract_sha"], resolver)
    validate_target_portfolio_code_identity(resolved["target_portfolio_code_identity_sha"], resolver)
    validate_target_portfolio_policy(resolved["target_portfolio_policy_sha"], resolver)
    validate_unit_execution_identity_table(resolved["unit_execution_identity_table_sha"], resolver)
    return TDExecutionManifest("TD_EXECUTION_MANIFEST_V1", tuple(deps))


__all__ = [name for name in globals() if not name.startswith("_")]