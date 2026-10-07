from __future__ import annotations

from dataclasses import dataclass
import string


def _require_sha256(value: str, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in string.hexdigits for ch in value)
    ):
        raise ValueError(f"{name} must be a 64-character hexadecimal digest")
    return value.lower()


@dataclass(frozen=True)
class PhysicalRowValueBindingV1:
    """Fail-closed coupling of logical row identity to the values physically consumed.

    Source-global row identity, block-local selection, logical/source cell identity,
    authenticated payload identity, and consumed values are one proof chain.
    """

    expression_row: int
    source_row_index: int
    block_row_index: int
    selected_block_row_index: int
    logical_cell_id: str
    source_cell_id: str
    payload_sha256: str
    authenticated_values_sha256: str
    consumed_values_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.expression_row, int) or self.expression_row < 0:
            raise ValueError("expression row must be a non-negative integer")
        if not isinstance(self.source_row_index, int) or self.source_row_index < 0:
            raise ValueError("source row must be a non-negative integer")
        if self.source_row_index != self.expression_row:
            raise ValueError("source row must equal expression row")

        if not isinstance(self.block_row_index, int) or self.block_row_index < 0:
            raise ValueError("block row must be a non-negative integer")
        if not isinstance(self.selected_block_row_index, int) or self.selected_block_row_index < 0:
            raise ValueError("selected block row must be a non-negative integer")
        if self.selected_block_row_index != self.block_row_index:
            raise ValueError("selected block row must equal validated block row")

        if not isinstance(self.logical_cell_id, str) or not self.logical_cell_id:
            raise ValueError("logical cell identity must be explicit")
        if not isinstance(self.source_cell_id, str) or not self.source_cell_id:
            raise ValueError("source cell identity must be explicit")
        if self.source_cell_id != self.logical_cell_id:
            raise ValueError("source cell identity must equal logical cell identity")

        object.__setattr__(self, "payload_sha256", _require_sha256(self.payload_sha256, "payload_sha256"))
        object.__setattr__(
            self,
            "authenticated_values_sha256",
            _require_sha256(self.authenticated_values_sha256, "authenticated_values_sha256"),
        )
        object.__setattr__(
            self,
            "consumed_values_sha256",
            _require_sha256(self.consumed_values_sha256, "consumed_values_sha256"),
        )
        if self.consumed_values_sha256 != self.authenticated_values_sha256:
            raise ValueError("consumed values must equal authenticated values")
