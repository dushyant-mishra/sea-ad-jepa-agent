import pytest

from sea_ad_jepa.qualification.pipeline import run_zero_update_qualification
from sea_ad_jepa.qualification.receipts import DataKind
from tests.qualification.test_zero_update_pipeline_v1 import _authorities, _batch, _protocol


def test_synthetic_scope_authority_cannot_execute_real_rna_batch():
    protocol = _protocol()
    called = {"representation": False}

    with pytest.raises(ValueError, match="scope"):
        run_zero_update_qualification(
            protocol,
            _authorities(protocol, evaluation_authorized=True),
            _batch(protocol, data_kind=DataKind.REAL_RNA),
            lambda view: called.__setitem__("representation", True),
            lambda rep, view: {"score": 0.0},
        )

    assert called["representation"] is False
