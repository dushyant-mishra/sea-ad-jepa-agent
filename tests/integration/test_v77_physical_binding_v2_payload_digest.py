from dataclasses import fields

import pytest

from sea_ad_jepa.qualification.physical_binding_v2 import PhysicalRowValueBindingV2


def _binding_kwargs():
    return dict(
        expression_row=91,
        source_row_index=91,
        block_row_index=3,
        selected_block_row_index=3,
        logical_cell_id="cell-91",
        source_cell_id="cell-91",
        logical_donor_id="donor-7",
        source_donor_id="donor-7",
        matrix_slot="layers/UMIs",
        authenticated_matrix_slot="layers/UMIs",
        feature_space_sha256="d" * 64,
        authenticated_feature_space_sha256="d" * 64,
        payload_location="shard-0042:row-3",
        authenticated_payload_location="shard-0042:row-3",
        payload_sha256="a" * 64,
        authenticated_values_sha256="b" * 64,
        consumed_values_sha256="b" * 64,
    )


def test_v2_requires_authenticated_payload_digest_and_rejects_substitution():
    field_names = {field.name for field in fields(PhysicalRowValueBindingV2)}
    assert "authenticated_payload_sha256" in field_names, (
        "V2 claims to bind the authenticated payload digest, but carries no authenticated digest to compare against"
    )

    values = _binding_kwargs()
    values["authenticated_payload_sha256"] = "c" * 64
    with pytest.raises(ValueError, match="payload.*digest|digest.*payload"):
        PhysicalRowValueBindingV2(**values)
