import hashlib
import numpy as np
import pytest
from sea_ad_jepa.v5.control_calibration_precision_authority_v1 import ControlCalibrationPrecisionPlanV1

def h(x): return hashlib.sha256(x.encode()).hexdigest()
def plan():
    return ControlCalibrationPrecisionPlanV1("TEST",h("census"),h("support"),h("elig"),h("split"))

def test_plan_is_independent_of_final_target_panel():
    p=plan(); p.validate()
    assert "target_panel_authority_sha256" not in p.__dataclass_fields__
    assert p.bootstrap_seed(128)==p.bootstrap_seed(128)
    assert p.bootstrap_seed(128)!=p.bootstrap_seed(256)

def test_interval_requires_current_donor_count_and_candidate_target_count():
    p=plan()
    matrix=np.ones((128,104))*0.01
    source=np.repeat(np.arange(4),26)
    out=p.interval(matrix,source,target_count=128)
    assert out.mean==pytest.approx(0.01)
    with pytest.raises(ValueError):
        p.interval(matrix[:127],source,target_count=128)
