"""Immutable intrinsic-cell data passed read-only to context modules."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import torch


def tensor_sha256(value: torch.Tensor) -> str:
    array = value.detach().cpu().contiguous().numpy()
    return hashlib.sha256(array.tobytes()).hexdigest()


@dataclass(frozen=True)
class IntrinsicCellPackage:
    molecular_ledger: torch.Tensor
    global_state: torch.Tensor
    biological_belief: torch.Tensor
    measurement_context: torch.Tensor
    domain_support: torch.Tensor

    def detached(self) -> "IntrinsicCellPackage":
        return IntrinsicCellPackage(*(value.detach() for value in self.tensors()))

    def tensors(self) -> tuple[torch.Tensor, ...]:
        return (
            self.molecular_ledger,
            self.global_state,
            self.biological_belief,
            self.measurement_context,
            self.domain_support,
        )

    def hashes(self) -> tuple[str, ...]:
        return tuple(tensor_sha256(value) for value in self.tensors())
