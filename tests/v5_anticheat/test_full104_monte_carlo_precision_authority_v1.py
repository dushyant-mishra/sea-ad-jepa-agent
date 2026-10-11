import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5_anticheat" / "derive_monte_carlo_precision_authority_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("full104_mc_precision_v1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_distribution_free_replicates_are_derived_from_declared_error_budget():
    m = load_module()
    rec = m.derive_precision_authority(
        metric_lower=-1.0,
        metric_upper=1.0,
        half_width=0.05,
        familywise_alpha=0.05,
        n_endpoints=20,
    )
    assert rec["replicates"] > 0
    assert rec["replicates"] == m.hoeffding_replicates(-1.0, 1.0, 0.05, 0.05 / 20)
    assert rec["replicate_count_source"] == "PROSPECTIVE_ERROR_BUDGET__NOT_HISTORICAL_CONSTANT"
    assert rec["training_authorized"] is False


def test_tighter_precision_requires_more_replicates():
    m = load_module()
    loose = m.hoeffding_replicates(0.0, 1.0, 0.10, 0.01)
    tight = m.hoeffding_replicates(0.0, 1.0, 0.05, 0.01)
    assert tight > loose


def test_more_endpoints_increases_familywise_replicate_requirement():
    m = load_module()
    a = m.derive_precision_authority(0.0, 1.0, 0.05, 0.05, 5)
    b = m.derive_precision_authority(0.0, 1.0, 0.05, 0.05, 50)
    assert b["replicates"] > a["replicates"]


@pytest.mark.parametrize(
    "args",
    [
        (0.0, 0.0, 0.05, 0.01),
        (1.0, 0.0, 0.05, 0.01),
        (0.0, 1.0, 0.0, 0.01),
        (0.0, 1.0, -0.1, 0.01),
        (0.0, 1.0, 0.05, 0.0),
        (0.0, 1.0, 0.05, 1.0),
    ],
)
def test_invalid_precision_contract_fails_closed(args):
    m = load_module()
    with pytest.raises(ValueError):
        m.hoeffding_replicates(*args)


def test_authority_rejects_nonpositive_endpoint_count():
    m = load_module()
    with pytest.raises(ValueError, match="n_endpoints"):
        m.derive_precision_authority(0.0, 1.0, 0.05, 0.05, 0)
