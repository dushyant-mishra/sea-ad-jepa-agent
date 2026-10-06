import pytest

from sea_ad_jepa.qualification.pipeline import ZeroUpdateViolation, run_zero_update_qualification
from tests.qualification.test_zero_update_pipeline_v1 import _authorities, _batch, _protocol


def test_hidden_callback_side_effect_cannot_pass_zero_update_runner():
    protocol = _protocol()
    hidden_state = {"parameter": 1.0}

    def representation_fn(model_view):
        hidden_state["parameter"] = 2.0
        return {"embedding": [0.0]}

    with pytest.raises(ZeroUpdateViolation, match="physical mutation"):
        run_zero_update_qualification(
            protocol,
            _authorities(protocol),
            _batch(protocol),
            representation_fn,
            lambda rep, view: {"score": 0.0},
        )

    assert hidden_state["parameter"] == 1.0
