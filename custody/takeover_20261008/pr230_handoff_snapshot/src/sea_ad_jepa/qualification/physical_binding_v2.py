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
class PhysicalRowValueBindingV2:
    """One fail-closed proof chain from logical identity to physically consumed values.

    V2 extends the historical row/value binding with donor identity, matrix slot,
    feature-space identity and physical payload location. A joined execution may
    only consume values whose complete chain agrees with the authenticated source.
    """

    expression_row: int
    source_row_index: int
    block_row_index: int
    selected_block_row_index: int
    logical_cell_id: str
    source_cell_id: str
    logical_donor_id: str
    source_donor_id: str
    matrix_slot: str
    authenticated_matrix_slot: str
    feature_space_sha256: str
    authenticated_feature_space_sha256: str
    payload_location: str
    authenticated_payload_location: str
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

        for value, name in (
            (self.logical_cell_id, "logical cell identity"),
            (self.source_cell_id, "source cell identity"),
            (self.logical_donor_id, "logical donor identity"),
            (self.source_donor_id, "source donor identity"),
            (self.matrix_slot, "matrix slot"),
            (self.authenticated_matrix_slot, "authenticated matrix slot"),
            (self.payload_location, "payload location"),
            (self.authenticated_payload_location, "authenticated payload location"),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be explicit")

        if self.source_cell_id != self.logical_cell_id:
            raise ValueError("source cell identity must equal logical cell identity")
        if self.source_donor_id != self.logical_donor_id:
            raise ValueError("source donor identity must equal logical donor identity")
        if self.authenticated_matrix_slot != self.matrix_slot:
            raise ValueError("matrix slot must equal authenticated matrix slot")
        if self.authenticated_payload_location != self.payload_location:
            raise ValueError("payload location must equal authenticated payload location")

        object.__setattr__(
            self,
            "feature_space_sha256",
            _require_sha256(self.feature_space_sha256, "feature_space_sha256"),
        )
        object.__setattr__(
            self,
            "authenticated_feature_space_sha256",
            _require_sha256(
                self.authenticated_feature_space_sha256,
                "authenticated_feature_space_sha256",
            ),
        )
        if self.authenticated_feature_space_sha256 != self.feature_space_sha256:
            raise ValueError("feature space must equal authenticated feature space")

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
