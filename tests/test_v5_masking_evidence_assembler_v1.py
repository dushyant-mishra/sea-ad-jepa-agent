import hashlib
from types import SimpleNamespace

import numpy as np
import pytest

from sea_ad_jepa.v5.masking_evidence_assembler_v1 import _matrix_from_donor_rows


def donor_rows(policy="RIDGE8_CONDITIONAL"):
    return [
        {
            "target_col":10,
            "target_id":"q0",
            "method":policy,
            "heldout_donor_scores":((0,0.1),(1,0.2)),
        },
        {
            "target_col":11,
            "target_id":"q1",
            "method":policy,
            "heldout_donor_scores":((0,0.3),(1,0.4)),
        },
    ]


def test_matrix_assembler_requires_complete_unique_target_donor_units():
    order=((10,"q0"),(11,"q1"))
    m=_matrix_from_donor_rows(
        donor_rows(),
        target_order=order,
        donor_count=2,
        policy="RIDGE8_CONDITIONAL",
        donor_field="heldout_donor_scores",
    )
    assert np.array_equal(m,np.array([[0.1,0.2],[0.3,0.4]]))


def test_matrix_assembler_rejects_missing_donor_units():
    bad=donor_rows()
    bad[1]["heldout_donor_scores"]=((0,0.3),)
    with pytest.raises(ValueError, match="incomplete donor matrix"):
        _matrix_from_donor_rows(
            bad,
            target_order=((10,"q0"),(11,"q1")),
            donor_count=2,
            policy="RIDGE8_CONDITIONAL",
            donor_field="heldout_donor_scores",
        )


def test_matrix_assembler_rejects_duplicate_units():
    bad=donor_rows()+[donor_rows()[0]]
    with pytest.raises(ValueError, match="duplicate donor evidence"):
        _matrix_from_donor_rows(
            bad,
            target_order=((10,"q0"),(11,"q1")),
            donor_count=2,
            policy="RIDGE8_CONDITIONAL",
            donor_field="heldout_donor_scores",
        )
