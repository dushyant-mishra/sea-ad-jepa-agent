"""Deterministic, torch-free encoding of lawful canonical address identity.

This is the lawfulness-critical half of V5_SHARED_ADDRESS_QUERY_PROVIDER_V1 and is kept
free of any tensor framework so that the structural properties -- determinism, replay,
field safety, sharing -- can be verified without an autograd runtime.

Input is restricted BY CONSTRUCTION to the two fields the canonical address-registry
authority marks model-facing: molecular_address_index and molecular_address_id. There is
no parameter through which symbol, biotype, ontology, coordinates, graph structure,
source, operator, donor, visibility, depth, detection, expression statistics, support
frequency or target values could enter.

Capacity (n_buckets), fan-out (n_hashes) and width are NOT chosen here. They are supplied
by the eventual model-geometry authority. Nothing in this module has a production default.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable, Sequence, Tuple

ENCODING_NAMESPACE = "JEPA_V5_SHARED_ADDRESS_QUERY_IDENTITY_ENCODING_V1"

# Anything the provider must never receive. Presence of any of these in a call is a
# structural violation, not a style problem.
FORBIDDEN_PROVIDER_INPUT_FIELDS: Tuple[str, ...] = (
    "symbol", "biotype", "current_ensembl_gene_id", "legacy_source_exact_id",
    "source_native_anchor", "identity_class", "identity_authority", "identity_evidence",
    "measurement_support_provenance", "registry_semantic_hash",
    "contributing_source_feature_count", "contributing_source_families",
    "contributing_source_dataset_ids",
    "ontology", "graph", "graph_neighborhood", "chromosome", "chromosomal_coordinate",
    "coordinate", "gene_set", "annotation",
    "source", "operator", "operator_index", "donor", "donor_id", "dataset", "dataset_id",
    "canonical_cell_id", "selection_row", "expression_row",
    "visibility", "depth", "q_depth", "q_detect", "detection", "detected_genes",
    "expression", "expression_mean", "expression_variance", "support_frequency",
    "target", "target_value", "target_rank", "target_support", "hidden_target",
)


class ForbiddenProviderInputError(ValueError):
    """Raised when a caller tries to hand the provider privileged information."""


def reject_forbidden_inputs(**kwargs: object) -> None:
    """Fail closed on any privileged keyword, rather than relying on convention."""
    bad = sorted(k for k in kwargs if k.lower() in FORBIDDEN_PROVIDER_INPUT_FIELDS)
    if bad:
        raise ForbiddenProviderInputError(
            f"forbidden provider input field(s): {bad}; the provider may receive only "
            f"molecular_address_index and molecular_address_id"
        )


@dataclass(frozen=True)
class AddressIdentityEncodingV1:
    """k-of-m sparse code over canonical identity. No trainable state lives here."""

    n_buckets: int
    n_hashes: int

    def __post_init__(self) -> None:
        if not isinstance(self.n_buckets, int) or self.n_buckets < 2:
            raise ValueError("n_buckets must be an int >= 2")
        if not isinstance(self.n_hashes, int) or self.n_hashes < 1:
            raise ValueError("n_hashes must be an int >= 1")
        if self.n_hashes > self.n_buckets:
            raise ValueError("n_hashes must not exceed n_buckets")

    def buckets_for(self, molecular_address_id: str) -> Tuple[int, ...]:
        """Deterministic bucket indices for one canonical address id."""
        if not isinstance(molecular_address_id, str) or not molecular_address_id.strip():
            raise ValueError("molecular_address_id must be a nonempty string")
        out = []
        for j in range(self.n_hashes):
            digest = hashlib.sha256(
                f"{ENCODING_NAMESPACE}|{j}|{molecular_address_id}".encode("utf-8")
            ).digest()
            out.append(int.from_bytes(digest[:8], "big") % self.n_buckets)
        return tuple(out)

    def signs_for(self, molecular_address_id: str) -> Tuple[int, ...]:
        """Deterministic +-1 signs, so distinct ids colliding in a bucket do not simply add."""
        out = []
        for j in range(self.n_hashes):
            digest = hashlib.sha256(
                f"{ENCODING_NAMESPACE}|sign|{j}|{molecular_address_id}".encode("utf-8")
            ).digest()
            out.append(1 if digest[0] & 1 else -1)
        return tuple(out)

    def encode(self, molecular_address_ids: Sequence[str]) -> Tuple[Tuple[Tuple[int, ...],
                                                                          Tuple[int, ...]], ...]:
        return tuple(
            (self.buckets_for(a), self.signs_for(a)) for a in molecular_address_ids
        )

    def replay_fingerprint(self) -> str:
        """Identity of the encoding itself, for checkpoint/replay binding."""
        return hashlib.sha256(
            f"{ENCODING_NAMESPACE}|n_buckets={self.n_buckets}|n_hashes={self.n_hashes}"
            .encode("utf-8")
        ).hexdigest()


def trainable_parameter_count(*, n_buckets: int, query_width: int) -> int:
    """Shared projection only: m*d + d. Deliberately independent of the address count."""
    return n_buckets * query_width + query_width


def is_per_address_memorization(*, trainable_parameters: int, n_addresses: int,
                                query_width: int) -> bool:
    """True when the parameter budget is large enough to hold a free vector per address.

    This is the qualification test for check 1. An unrestricted nn.Embedding(N, d) has
    exactly N*d trainable parameters and fails here; a shared projection does not.
    """
    if n_addresses <= 0 or query_width <= 0:
        raise ValueError("n_addresses and query_width must be positive")
    return trainable_parameters >= n_addresses * query_width
