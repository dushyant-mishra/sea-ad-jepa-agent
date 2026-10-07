import pytest

from sea_ad_jepa.qualification import v77_join
from sea_ad_jepa.qualification.receipts import QSafetyExecutionProofStatus
from sea_ad_jepa.qualification.v77_join import (
    PhysicalRowValueBindingV1,
    build_learnable_model_context,
)


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


def test_raw_source_and_operator_identity_do_not_reach_learnable_context():
    context = build_learnable_model_context(
        model_inputs={"student_expression": [[1.0, 0.0]], "measurement_mask": [[True, True]]},
        lawful_operator_context={
            "source_index": [4],
            "operator_index": [11],
            "visible_library_size": [37.0],
            "n_measured": [2],
        },
    )
    assert set(context.operator_context) == {"visible_library_size", "n_measured"}
    assert "source_index" not in context.operator_context
    assert "operator_index" not in context.operator_context


def test_unreviewed_measurement_identity_proxy_fails_closed():
    with pytest.raises(ValueError, match="unreviewed|operator context"):
        build_learnable_model_context(
            model_inputs={"student_expression": [[1.0]]},
            lawful_operator_context={
                "source_index": [4],
                "operator_index": [11],
                "visible_library_size": [37.0],
                "n_measured": [1],
                "dataset_embedding": [99],
            },
        )


def test_policy_only_q_safety_cannot_count_as_executed_joined_proof():
    gate = getattr(v77_join, "require_executed_q_safety", None)
    assert callable(gate), "V77 join has no execution-bound q-safety gate"
    with pytest.raises(ValueError, match="executed|q-safety"):
        gate(QSafetyExecutionProofStatus.POLICY_ONLY_NOT_EXECUTION_PROVEN)


def test_executed_status_enum_alone_cannot_mint_q_safety_proof():
    with pytest.raises(ValueError, match="typed|proof"):
        v77_join.require_executed_q_safety(
            QSafetyExecutionProofStatus.PROVEN_BY_BOUND_ADAPTER_RUNTIME
        )
