import pytest

from sea_ad_jepa.qualification.v77_join import PhysicalRowValueBindingV1


def _valid_binding(**overrides):
    values = dict(
        expression_row=91,
        source_row_index=91,
        block_row_index=3,
        selected_block_row_index=3,
        logical_cell_id="cell-91",
        source_cell_id="cell-91",
        payload_sha256="a" * 64,
        authenticated_values_sha256="b" * 64,
        consumed_values_sha256="b" * 64,
    )
    values.update(overrides)
    return PhysicalRowValueBindingV1(**values)


def test_physical_row_value_binding_accepts_one_inseparable_chain():
    binding = _valid_binding()
    assert binding.expression_row == 91
    assert binding.consumed_values_sha256 == binding.authenticated_values_sha256


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"source_row_index": 7}, "source row"),
        ({"selected_block_row_index": 4}, "block row"),
        ({"source_cell_id": "cell-7"}, "cell identity"),
        ({"consumed_values_sha256": "c" * 64}, "consumed values"),
    ],
)
def test_physical_row_value_binding_rejects_historical_substitutions(overrides, message):
    with pytest.raises(ValueError, match=message):
        _valid_binding(**overrides)
