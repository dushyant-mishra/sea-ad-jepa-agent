from sea_ad_jepa.qualification.pipeline import run_zero_update_qualification
from sea_ad_jepa.qualification.receipts import MutationProofStatus
from tests.qualification.test_zero_update_pipeline_v1 import _authorities, _batch, _protocol


def test_hidden_callback_side_effect_is_not_misreported_as_physically_proven_zero_update():
    protocol = _protocol()
    hidden_state = {"parameter": 1.0}

    def representation_fn(model_view):
        hidden_state["parameter"] = 2.0
        return {"embedding": [0.0]}

    frozen = run_zero_update_qualification(
        protocol,
        _authorities(protocol),
        _batch(protocol),
        representation_fn,
        lambda rep, view: {"score": 0.0},
    )

    # Generic Python callbacks can mutate state outside the shared interface's visibility.
    assert hidden_state["parameter"] == 2.0
    assert frozen.mutation_proof_status is MutationProofStatus.NOT_PROVEN_BY_SHARED_INTERFACE
