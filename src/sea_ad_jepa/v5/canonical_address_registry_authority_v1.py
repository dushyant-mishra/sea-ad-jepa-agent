"""Canonical target-address registry authority.

Declares WHICH artifact is the canonical molecular-address registry for the current
FULL104 population, and separates it from the three artifacts it is routinely confused
with. It binds content and invariants, never a filesystem location, and it cannot
authorize training.

Deliberately NOT in scope: model width, depth, geometry, mask fraction, optimizer, EMA
timescale, seed, proposal law. Those belong to other authorities.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any, Mapping, Tuple

CANONICAL_ADDRESS_REGISTRY_ROW_COUNT = 41238

# The only registry columns a model-facing provider may receive. Address identity may
# key a shared trainable query mechanism; it must not become an imported biological memory.
MODEL_FACING_FIELDS: Tuple[str, ...] = ("molecular_address_index", "molecular_address_id")

PROVENANCE_ONLY_FIELDS: Tuple[str, ...] = (
    "identity_class",
    "current_ensembl_gene_id",
    "legacy_source_exact_id",
    "source_native_anchor",
    "identity_authority",
    "identity_evidence",
    "measurement_support_provenance",
    "registry_semantic_hash",
)

# Registry columns that are biological annotation or source-identity/frequency derived,
# plus the per-cell identity columns that MATERIALIZATION_CONTRACT.json declares to be
# audit metadata rather than model input.
PROHIBITED_FIELDS: Tuple[str, ...] = (
    "symbol",
    "biotype",
    "contributing_source_feature_count",
    "contributing_source_families",
    "contributing_source_dataset_ids",
    "canonical_cell_id",
    "selection_row",
    "donor_id",
    "expression_row",
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _nonempty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value.strip()


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class CanonicalAddressRegistryAuthorityV1:
    """Binds the canonical address registry by content, invariants and provenance."""

    authority_id: str
    registry_sha256: str
    registry_row_count: int
    full104_block_manifest_sha256: str
    observation_state_sha256: str
    recovery_provenance: str
    # Informative only. A drive letter is not authority; it is excluded from identity.
    informative_path: str = ""
    ordering_invariant: str = (
        "molecular_address_index is contiguous 0..N-1 and strictly increasing in file order"
    )
    identifier_invariant: str = "molecular_address_id is unique across all rows"
    training_authorized: bool = False

    @property
    def model_facing_fields(self) -> Tuple[str, ...]:
        return MODEL_FACING_FIELDS

    @property
    def provenance_only_fields(self) -> Tuple[str, ...]:
        return PROVENANCE_ONLY_FIELDS

    @property
    def prohibited_fields(self) -> Tuple[str, ...]:
        return PROHIBITED_FIELDS

    def validate(self) -> None:
        _nonempty(self.authority_id, "authority_id")
        _nonempty(self.recovery_provenance, "recovery_provenance")
        _sha(self.registry_sha256, "registry_sha256")
        _sha(self.full104_block_manifest_sha256, "full104_block_manifest_sha256")
        _sha(self.observation_state_sha256, "observation_state_sha256")
        _nonempty(self.ordering_invariant, "ordering_invariant")
        _nonempty(self.identifier_invariant, "identifier_invariant")

        if self.registry_row_count != CANONICAL_ADDRESS_REGISTRY_ROW_COUNT:
            raise ValueError(
                f"registry_row_count must be {CANONICAL_ADDRESS_REGISTRY_ROW_COUNT}, "
                f"got {self.registry_row_count}"
            )

        # Role-splicing defence. These are three DISTINCT artifacts. Historical records
        # have already conflated the registry with the observation state under a single
        # field name; that must fail here rather than propagate into a provider.
        if self.registry_sha256 == self.observation_state_sha256:
            raise ValueError(
                "registry_sha256 and observation_state_sha256 must identify distinct artifacts"
            )
        if self.registry_sha256 == self.full104_block_manifest_sha256:
            raise ValueError(
                "registry_sha256 and full104_block_manifest_sha256 must identify distinct artifacts"
            )
        if self.observation_state_sha256 == self.full104_block_manifest_sha256:
            raise ValueError(
                "observation_state_sha256 and full104_block_manifest_sha256 must identify "
                "distinct artifacts"
            )

        if self.training_authorized is not False:
            raise ValueError("canonical address-registry authority cannot authorize training")

    def verify_artifact(self, *, sha256: str, row_count: int, ordered: bool, unique: bool) -> bool:
        """Portable fail-closed check that another machine holds the same registry.

        Identity is content plus invariants. Path is never consulted.
        """
        self.validate()
        return bool(
            sha256 == self.registry_sha256
            and row_count == self.registry_row_count
            and ordered is True
            and unique is True
        )

    def canonical_digest(self) -> str:
        self.validate()
        payload = {k: v for k, v in asdict(self).items() if k != "informative_path"}
        return _canonical_sha(
            {
                "schema": "V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_V1",
                **payload,
                "model_facing_fields": list(MODEL_FACING_FIELDS),
                "provenance_only_fields": list(PROVENANCE_ONLY_FIELDS),
                "prohibited_fields": list(PROHIBITED_FIELDS),
                "training_authorized": False,
            }
        )
