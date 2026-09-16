"""V5_SHARED_ADDRESS_QUERY_PROVIDER_V1 -- structural Stage-A provider.

One shared trainable projection over a deterministic k-of-m code of lawful canonical
address identity. Trainable parameters are m*d + d: a function of capacity and width,
NOT of the 41,238 registry rows. Every address reuses the same projection, so no address
owns an independently trainable vector.

What this module deliberately does NOT decide: production width, depth, transformer
geometry, mask fraction, optimizer, schedule, EMA timescale, proposal law, seed. All are
constructor arguments supplied by later authorities. There is no production default here.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterator, Sequence, Tuple

import torch
from torch import nn

from .address_identity_encoding_v1 import (
    AddressIdentityEncodingV1,
    reject_forbidden_inputs,
    trainable_parameter_count,
)

PROVIDER_ID = "V5_SHARED_ADDRESS_QUERY_PROVIDER_V1"


class SharedAddressQueryProviderV1(nn.Module):
    """Shared function of canonical address identity. No per-address free vector."""

    def __init__(
        self,
        *,
        registry_authority_sha256: str,
        n_buckets: int,
        n_hashes: int,
        query_width: int,
        init_seed: int,
    ) -> None:
        super().__init__()
        if not isinstance(registry_authority_sha256, str) or len(registry_authority_sha256) != 64:
            raise ValueError("registry_authority_sha256 must be a SHA-256 digest")
        if not isinstance(query_width, int) or query_width < 1:
            raise ValueError("query_width must be a positive int supplied by geometry authority")
        if not isinstance(init_seed, int):
            raise ValueError("init_seed must be supplied explicitly by the runtime authority")

        self.encoding = AddressIdentityEncodingV1(n_buckets=n_buckets, n_hashes=n_hashes)
        self.query_width = int(query_width)
        self.init_seed = int(init_seed)
        # Registry binding and encoding identity travel with the checkpoint.
        self.register_buffer(
            "_registry_authority",
            torch.tensor(bytearray.fromhex(registry_authority_sha256), dtype=torch.uint8),
            persistent=True,
        )

        generator = torch.Generator().manual_seed(self.init_seed)
        scale = (1.0 / max(n_buckets, 1)) ** 0.5
        self.projection = nn.Parameter(
            torch.empty(n_buckets, self.query_width).uniform_(-scale, scale, generator=generator)
        )
        self.bias = nn.Parameter(torch.zeros(self.query_width))

    # ---------------------------------------------------------------- identity
    @property
    def registry_authority_sha256(self) -> str:
        return bytes(self._registry_authority.tolist()).hex()

    def named_trainable_parameters(self) -> Iterator[Tuple[str, nn.Parameter]]:
        for name, param in self.named_parameters():
            if param.requires_grad:
                yield name, param

    def trainable_parameter_count(self) -> int:
        return sum(p.numel() for _, p in self.named_trainable_parameters())

    def expected_trainable_parameter_count(self) -> int:
        return trainable_parameter_count(
            n_buckets=self.encoding.n_buckets, query_width=self.query_width
        )

    # ---------------------------------------------------------------- forward
    def forward(self, molecular_address_ids: Sequence[str], **forbidden: Any) -> torch.Tensor:
        """Map lawful canonical identity to a query. Privileged kwargs fail closed."""
        reject_forbidden_inputs(**forbidden)
        codes = self.encoding.encode(molecular_address_ids)
        buckets = torch.tensor([c[0] for c in codes], dtype=torch.long)
        signs = torch.tensor([c[1] for c in codes], dtype=self.projection.dtype)
        gathered = self.projection[buckets]              # [B, k, d] -- shared rows
        return (gathered * signs.unsqueeze(-1)).sum(dim=1) + self.bias

    # ---------------------------------------------------------------- replay
    def replay_state(self) -> Dict[str, Any]:
        return {
            "provider_id": PROVIDER_ID,
            "registry_authority_sha256": self.registry_authority_sha256,
            "encoding_fingerprint": self.encoding.replay_fingerprint(),
            "n_buckets": self.encoding.n_buckets,
            "n_hashes": self.encoding.n_hashes,
            "query_width": self.query_width,
            "init_seed": self.init_seed,
        }

    def query_artifact_sha256(self) -> str:
        """Binds the provider implementation/configuration needed to reproduce
        address -> query behaviour. Deliberately excludes learned weights (those are
        checkpoint state) and excludes any later model-geometry decision."""
        return hashlib.sha256(
            json.dumps(self.replay_state(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    @classmethod
    def from_replay_state(cls, state: Dict[str, Any]) -> "SharedAddressQueryProviderV1":
        if state.get("provider_id") != PROVIDER_ID:
            raise ValueError("replay state is not for this provider")
        for key in ("registry_authority_sha256", "n_buckets", "n_hashes", "query_width",
                    "init_seed", "encoding_fingerprint"):
            if key not in state:
                raise ValueError(f"replay state missing required key: {key}")
        provider = cls(
            registry_authority_sha256=state["registry_authority_sha256"],
            n_buckets=state["n_buckets"],
            n_hashes=state["n_hashes"],
            query_width=state["query_width"],
            init_seed=state["init_seed"],
        )
        if provider.encoding.replay_fingerprint() != state["encoding_fingerprint"]:
            raise ValueError("encoding fingerprint mismatch on replay")
        return provider
